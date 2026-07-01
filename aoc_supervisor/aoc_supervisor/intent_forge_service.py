"""Intent Forge session orchestration service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aoc_supervisor.blueprint_compiler import (
    ValidationResult,
    compile_executable_projection,
    compile_rich_artifact,
    validate_blueprint_state,
)
from aoc_supervisor.conflict_resolver import detect_contradictions, merge_contradictions, resolution_options
from aoc_supervisor.intent_blueprint import detect_intent_streams
from aoc_supervisor.intent_blueprint_state import (
    bump_blueprint_version,
    new_blueprint_state,
    new_element_id,
    new_question_id,
    new_session_id,
    public_session_view,
)
from aoc_supervisor.intent_forge_events import build_intent_event
from aoc_supervisor.intent_session_store import (
    IdempotencyReplayError,
    IntentForgeSessionStore,
)
from aoc_supervisor.question_policy import apply_intake_prompt, build_next_question, should_stop_questioning
from aoc_supervisor.telemetry_policy import export_optional_telemetry, normalize_consent
from aoc_supervisor.teleology_artifact import write_teleology_artifact


class IntentForgeService:
    def __init__(self, host_root: Path) -> None:
        self.store = IntentForgeSessionStore(host_root)
        self._sequence: dict[str, int] = {}

    def _next_sequence(self, session_id: str) -> int:
        value = self._sequence.get(session_id, -1) + 1
        self._sequence[session_id] = value
        return value

    def _emit(self, session_id: str, event_type: str, state: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        event = build_intent_event(
            session_id=session_id,
            event_type=event_type,
            data=data,
            sequence=self._next_sequence(session_id),
            blueprint_version=int(state.get("blueprint_version", 0)),
        )
        self.store.append_event(session_id, event)
        return event

    def _invalidate_question_dependents(self, state: dict[str, Any], question_id: str) -> None:
        graph = state.setdefault("blueprint_graph", {"version": 0, "nodes": [], "edges": []})
        stale_ids: set[str] = set()
        for req in state.get("confirmed_requirements", []):
            if not isinstance(req, dict):
                continue
            if str(req.get("source_question_id", "")) == question_id and not req.get("stale"):
                req["stale"] = True
                req_id = str(req.get("id", ""))
                if req_id:
                    stale_ids.add(req_id)
        if not isinstance(graph, dict):
            return
        for node in graph.get("nodes", []):
            if isinstance(node, dict) and str(node.get("id", "")) in stale_ids:
                node["stale"] = True
        for edge in graph.get("edges", []):
            if not isinstance(edge, dict):
                continue
            if str(edge.get("source", "")) in stale_ids:
                target = str(edge.get("target", ""))
                if target:
                    stale_ids.add(target)
        for node in graph.get("nodes", []):
            if isinstance(node, dict) and str(node.get("id", "")) in stale_ids:
                node["stale"] = True

    def _apply_answer_to_state(
        self,
        state: dict[str, Any],
        *,
        question_id: str,
        answer: str,
        domain: str,
        conflict_resolution: bool = False,
    ) -> None:
        from aoc_supervisor.adaptive_question_engine import get_default_engine
        from aoc_supervisor.reasoning_provider import ProviderFailureError

        current_q = state.get("current_question") or {}
        entry = {
            "question_id": question_id,
            "text": current_q.get("text", "") if isinstance(current_q, dict) else "",
            "answer": answer.strip(),
            "domain": domain,
            "timestamp": state.get("updated_at"),
        }
        state.setdefault("questions_and_answers", []).append(entry)

        # C03: evidence reanalysis — run provider.analyze() before selecting next question.
        # Set ANALYZING during reanalysis so it appears in the analysis snapshot.
        prev_status = state.get("session_status", "")
        state["session_status"] = "ANALYZING"

        _claim_ids: list[str] = []

        try:
            engine = get_default_engine()
            result = engine.analyze(state, mutate_state=True)
            output = result.output

            # Mark any previously raw-appended requirements for this question as stale
            for req in state.get("confirmed_requirements", []):
                if (
                    isinstance(req, dict)
                    and not req.get("stale")
                    and str(req.get("source_question_id", "")) == question_id
                ):
                    req["stale"] = True

            # Merge extracted claims from analysis output (facts, inferences, assumptions)
            # into confirmed_requirements instead of the old raw-append approach.
            for claim_list in (output.facts, output.inferences, output.assumptions):
                for claim in claim_list:
                    if not isinstance(claim, dict):
                        continue
                    text = str(claim.get("text", "")).strip()
                    if not text:
                        continue
                    rid = new_element_id("REQ")
                    state.setdefault("confirmed_requirements", []).append(
                        {
                            "id": rid,
                            "text": text,
                            "source_question_id": question_id,
                            "confidence": float(claim.get("confidence", 0.8)),
                            "domain": claim.get("domain", domain),
                        }
                    )
                    _claim_ids.append(rid)

        except ProviderFailureError:
            # Analysis unavailable — fall through to raw-append fallback
            pass

        if not _claim_ids:
            # Fallback: raw-append raw answer if analysis produced no claims or failed
            rid = new_element_id("REQ")
            state.setdefault("confirmed_requirements", []).append(
                {
                    "id": rid,
                    "text": answer.strip(),
                    "source_question_id": question_id,
                    "confidence": 1.0,
                    "domain": domain,
                }
            )
            _claim_ids.append(rid)

        state["session_status"] = prev_status

        coverage = state.setdefault("domain_coverage", {})
        if isinstance(coverage, dict):
            coverage.setdefault(domain, {"addressed": True, "na": False})
            coverage[domain]["addressed"] = True
        confidence = state.setdefault("confidence_by_domain", {})
        if isinstance(confidence, dict):
            confidence[domain] = min(1.0, float(confidence.get(domain, 0.0)) + 0.2)
        graph = state.setdefault("blueprint_graph", {"version": 0, "nodes": [], "edges": []})
        if isinstance(graph, dict):
            graph.setdefault("nodes", []).append(
                {
                    "id": _claim_ids[0],
                    "label": answer.strip()[:80],
                    "kind": "requirement",
                    "domain": domain,
                    "confidence": confidence.get(domain, 0.8) if isinstance(confidence, dict) else 0.8,
                }
            )
        if conflict_resolution:
            contradictions = state.get("contradictions", [])
            active = next(
                (item for item in contradictions if isinstance(item, dict) and not item.get("resolved")),
                None,
            )
            for contradiction in state.get("contradictions", []):
                if isinstance(contradiction, dict):
                    contradiction["resolved"] = True
                    contradiction["resolution_text"] = answer.strip()
            if isinstance(active, dict):
                for element_id in (active.get("element_a_id"), active.get("element_b_id")):
                    eid = str(element_id or "")
                    if not eid:
                        continue
                    for req in state.get("confirmed_requirements", []):
                        if isinstance(req, dict) and str(req.get("id", "")) == eid:
                            req["stale"] = True
                    for dec in state.get("decisions", []):
                        if isinstance(dec, dict) and str(dec.get("id", "")) == eid:
                            dec["superseded"] = True
                    graph = state.setdefault("blueprint_graph", {"version": 0, "nodes": [], "edges": []})
                    if isinstance(graph, dict):
                        for node in graph.get("nodes", []):
                            if isinstance(node, dict) and str(node.get("id", "")) == eid:
                                node["stale"] = True
        lowered = answer.strip().lower()
        if domain == "testing_acceptance" and "validation window" in lowered:
            state.setdefault("decisions", []).append(
                {
                    "id": new_element_id("DEC"),
                    "text": answer.strip(),
                    "rationale": "acceptance_policy",
                }
            )
        state["current_question"] = None

    def _seed_free_tier(self, state: dict[str, Any]) -> None:
        intent = str(state.get("original_prompt", "")).strip()
        streams = detect_intent_streams(intent)
        state.setdefault("inferred_requirements", [])
        for stream in streams[:6]:
            state["inferred_requirements"].append(
                {
                    "id": new_element_id("REQ"),
                    "text": stream.title,
                    "confidence": 0.55,
                    "basis": "keyword_stream_detection",
                }
            )
        state.setdefault("assumptions", []).append(
            {
                "id": new_element_id("ASSUME"),
                "text": "Free-tier blueprint inferred without follow-up questions.",
                "risk_if_wrong": "medium",
            }
        )
        state.setdefault("risks", []).append(
            {
                "id": new_element_id("RISK"),
                "text": "Unverified assumptions remain until a paid adaptive session is run.",
                "severity": "medium",
            }
        )
        for domain, meta in state.get("domain_coverage", {}).items():
            if isinstance(meta, dict):
                meta["addressed"] = True
        confidence = state.setdefault("confidence_by_domain", {})
        if isinstance(confidence, dict):
            for domain in confidence:
                confidence[domain] = 0.9
        artifact = compile_rich_artifact(state, provisional=True)
        state["artifact"] = artifact
        state["executable_projection"] = compile_executable_projection(state)
        state["session_status"] = "FINALIZED"
        state["finalized_at"] = state.get("updated_at")

    def create_session(
        self,
        *,
        user_id: str,
        prompt: str,
        tier: str = "paid",
        telemetry_consent: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session_id = new_session_id()
        state = new_blueprint_state(
            session_id=session_id,
            user_id=user_id,
            tier=tier,
            original_prompt=prompt,
            session_status="CREATED",
        )
        state["telemetry_consent"] = normalize_consent(telemetry_consent)
        self.store.create(state)
        self._emit(session_id, "intent.session.created", state, {"tier": tier})
        if tier == "free":
            bump_blueprint_version(state)
            self._seed_free_tier(state)
            self.store.save(session_id, state)
            self._emit(session_id, "blueprint.finalized", state, {"provisional": True})
            return public_session_view(state)
        apply_intake_prompt(state)
        state["session_status"] = "QUESTIONING"
        question = build_next_question(state)
        state["current_question"] = question
        if question is None and state.get("analysis_recovery"):
            state["session_status"] = "ANALYSIS_BLOCKED"
        bump_blueprint_version(state)
        self.store.save(session_id, state)
        if question:
            self._emit(
                session_id,
                "intent.question.presented",
                state,
                {"question_id": question["question_id"], "domain": question["domain"], "text": question["text"]},
            )
        return public_session_view(state)

    def get_session(self, session_id: str) -> dict[str, Any]:
        return public_session_view(self.store.load(session_id))

    def submit_answer(
        self,
        session_id: str,
        *,
        question_id: str,
        answer: str,
        idempotency_key: str,
        expected_blueprint_version: int,
        action: str = "answer",
    ) -> dict[str, Any]:
        with self.store.session_lock(session_id):
            state = self.store.load(session_id)
            try:
                self.store.claim_idempotency(state, idempotency_key)
            except IdempotencyReplayError:
                return public_session_view(state)
            status = str(state.get("session_status", ""))
            if status not in {"QUESTIONING", "CONFLICT_RESOLUTION"}:
                raise ValueError(f"cannot submit answer while session is {status}")
            current = state.get("current_question") or {}
            current_qid = str(current.get("question_id", "")).strip() if isinstance(current, dict) else ""
            submitted_qid = question_id.strip()
            if not current_qid:
                raise ValueError("cannot submit answer without a current_question")
            if submitted_qid and submitted_qid != current_qid:
                raise ValueError("question_id does not match current_question")
            question_id = current_qid
            domain = str(current.get("domain", "functional_requirements"))
            if action == "skip" and status == "QUESTIONING":
                coverage = state.setdefault("domain_coverage", {})
                if isinstance(coverage, dict):
                    coverage.setdefault(domain, {"addressed": True, "na": False})
                    coverage[domain]["addressed"] = True
                state["current_question"] = None
            else:
                self._apply_answer_to_state(
                    state,
                    question_id=question_id,
                    answer=answer,
                    domain=domain,
                    conflict_resolution=status == "CONFLICT_RESOLUTION",
                )
            bump_blueprint_version(state)
            merge_contradictions(state, detect_contradictions(state))
            unresolved = [c for c in state.get("contradictions", []) if isinstance(c, dict) and not c.get("resolved")]
            if unresolved:
                state["session_status"] = "CONFLICT_RESOLUTION"
                primary = unresolved[0]
                state["current_question"] = {
                    "question_id": question_id,
                    "domain": "conflict_resolution",
                    "text": f"Resolve contradiction {primary.get('id')}: {primary.get('description')}",
                    "options": resolution_options(primary, state),
                }
                self.store.save(session_id, state, expected_version=expected_blueprint_version)
                self._emit(
                    session_id,
                    "blueprint.contradiction.detected",
                    state,
                    {"contradiction_id": primary.get("id")},
                )
                return public_session_view(state)
            if should_stop_questioning(state):
                state["session_status"] = "VALIDATING"
            else:
                next_question = build_next_question(state)
                state["current_question"] = next_question
                if next_question is None and state.get("analysis_recovery"):
                    state["session_status"] = "ANALYSIS_BLOCKED"
                else:
                    state["session_status"] = "QUESTIONING"
            self.store.save(session_id, state, expected_version=expected_blueprint_version)
            self._emit(session_id, "intent.answer.recorded", state, {"question_id": question_id, "action": action})
            if state.get("current_question"):
                q = state["current_question"]
                self._emit(
                    session_id,
                    "intent.question.presented",
                    state,
                    {"question_id": q["question_id"], "domain": q.get("domain"), "text": q.get("text")},
                )
            return public_session_view(state)

    def revise_answer(
        self,
        session_id: str,
        *,
        question_id: str,
        answer: str,
        idempotency_key: str,
        expected_blueprint_version: int,
    ) -> dict[str, Any]:
        with self.store.session_lock(session_id):
            state = self.store.load(session_id)
            try:
                self.store.claim_idempotency(state, idempotency_key)
            except IdempotencyReplayError:
                return public_session_view(state)
            status = str(state.get("session_status", ""))
            if status not in {"QUESTIONING", "PAUSED", "VALIDATING", "FINAL_CONFIRMATION"}:
                raise ValueError(f"cannot revise while session is {status}")
            original = next(
                (
                    entry
                    for entry in state.get("questions_and_answers", [])
                    if isinstance(entry, dict)
                    and str(entry.get("question_id", "")) == question_id
                    and not entry.get("superseded_by")
                ),
                None,
            )
            if original is None:
                raise ValueError(f"question_id not found or already superseded: {question_id}")
            revision_id = new_question_id()
            original["superseded_by"] = revision_id
            domain = str(original.get("domain", "functional_requirements"))
            self._invalidate_question_dependents(state, question_id)
            state.setdefault("questions_and_answers", []).append(
                {
                    "question_id": revision_id,
                    "revises": question_id,
                    "text": original.get("text", ""),
                    "answer": answer.strip(),
                    "domain": domain,
                    "timestamp": state.get("updated_at"),
                }
            )
            self._apply_answer_to_state(
                state,
                question_id=revision_id,
                answer=answer,
                domain=domain,
            )
            bump_blueprint_version(state)
            merge_contradictions(state, detect_contradictions(state))
            unresolved = [c for c in state.get("contradictions", []) if isinstance(c, dict) and not c.get("resolved")]
            if unresolved:
                state["session_status"] = "CONFLICT_RESOLUTION"
                primary = unresolved[0]
                state["current_question"] = {
                    "question_id": revision_id,
                    "domain": "conflict_resolution",
                    "text": f"Resolve contradiction {primary.get('id')}: {primary.get('description')}",
                    "options": resolution_options(primary, state),
                }
            elif should_stop_questioning(state):
                state["session_status"] = "VALIDATING"
                state["current_question"] = None
            else:
                next_question = build_next_question(state)
                state["current_question"] = next_question
                if next_question is None and state.get("analysis_recovery"):
                    state["session_status"] = "ANALYSIS_BLOCKED"
                else:
                    state["session_status"] = "QUESTIONING"
            self.store.save(session_id, state, expected_version=expected_blueprint_version)
            self._emit(
                session_id,
                "intent.answer.revised",
                state,
                {"question_id": question_id, "revision_id": revision_id},
            )
            telemetry = export_optional_telemetry(state)
            if telemetry:
                self._emit(session_id, "intent.telemetry.aggregate", state, telemetry)
            return public_session_view(state)

    def pause(self, session_id: str, *, idempotency_key: str, expected_blueprint_version: int) -> dict[str, Any]:
        with self.store.session_lock(session_id):
            state = self.store.load(session_id)
            try:
                self.store.claim_idempotency(state, idempotency_key)
            except IdempotencyReplayError:
                return public_session_view(state)
            status = str(state.get("session_status", ""))
            if status in {"FINAL_CONFIRMATION", "FINALIZING", "FINALIZED", "HANDED_OFF"}:
                raise ValueError(f"cannot pause while session is {status}")
            state["session_status"] = "PAUSED"
            bump_blueprint_version(state)
            self.store.save(session_id, state, expected_version=expected_blueprint_version)
            self._emit(session_id, "intent.session.paused", state, {})
            return public_session_view(state)

    def resume(self, session_id: str, *, idempotency_key: str, expected_blueprint_version: int) -> dict[str, Any]:
        with self.store.session_lock(session_id):
            state = self.store.load(session_id)
            try:
                self.store.claim_idempotency(state, idempotency_key)
            except IdempotencyReplayError:
                return public_session_view(state)
            status = str(state.get("session_status", ""))
            if status in {"FINAL_CONFIRMATION", "FINALIZING", "FINALIZED", "HANDED_OFF"}:
                raise ValueError(f"cannot resume while session is {status}")
            unresolved = [c for c in state.get("contradictions", []) if isinstance(c, dict) and not c.get("resolved")]
            if status == "ANALYSIS_BLOCKED":
                state["session_status"] = "QUESTIONING"
                next_question = build_next_question(state)
                state["current_question"] = next_question
                if next_question is None and state.get("analysis_recovery"):
                    state["session_status"] = "ANALYSIS_BLOCKED"
            elif unresolved:
                state["session_status"] = "CONFLICT_RESOLUTION"
            else:
                state["session_status"] = "QUESTIONING"
                if not state.get("current_question"):
                    next_question = build_next_question(state)
                    state["current_question"] = next_question
                    if next_question is None and state.get("analysis_recovery"):
                        state["session_status"] = "ANALYSIS_BLOCKED"
            bump_blueprint_version(state)
            self.store.save(session_id, state, expected_version=expected_blueprint_version)
            self._emit(session_id, "intent.session.resumed", state, {})
            return public_session_view(state)

    def _get_structural_errors(self, state: dict[str, Any]) -> list[str]:
        structural_errors: list[str] = []
        contradictions = [c for c in state.get("contradictions", []) if isinstance(c, dict) and not c.get("resolved")]
        if contradictions:
            structural_errors.append(f"{len(contradictions)} unresolved contradictions remain")
        stale_nodes = [
            n for n in state.get("blueprint_graph", {}).get("nodes", []) if isinstance(n, dict) and n.get("stale")
        ]
        if stale_nodes:
            structural_errors.append(f"{len(stale_nodes)} stale graph nodes remain")
        return structural_errors

    def _block_finalize(
        self,
        session_id: str,
        state: dict[str, Any],
        expected_version: int,
        items: list[str],
        text: str,
    ) -> dict[str, Any]:
        state["session_status"] = "QUESTIONING"
        state["current_question"] = {
            "question_id": "finalize_blocked",
            "text": text,
            "domain": "validation",
            "blocking_items": items,
        }
        bump_blueprint_version(state)
        self.store.save(session_id, state, expected_version=expected_version)
        return public_session_view(state)

    def finalize(
        self,
        session_id: str,
        *,
        idempotency_key: str,
        expected_blueprint_version: int,
        force: bool = False,
    ) -> dict[str, Any]:
        with self.store.session_lock(session_id):
            state = self.store.load(session_id)
            try:
                self.store.claim_idempotency(state, idempotency_key)
            except IdempotencyReplayError:
                return public_session_view(state)

            overridden_blockers: list[str] = []
            if force:
                strict_validation = validate_blueprint_state(state, finalize=True)
                overridden_blockers = list(strict_validation.blocking_items)
                structural_errors = self._get_structural_errors(state)
                if structural_errors:
                    return self._block_finalize(
                        session_id,
                        state,
                        expected_blueprint_version,
                        structural_errors,
                        "Structural issues prevent finalization even with force.",
                    )
                for item in state.get("unresolved_items", []):
                    if isinstance(item, dict) and item.get("blocking"):
                        item["blocking"] = False

            validation = validate_blueprint_state(state, finalize=not force)
            if not validation.ok:
                if not force:
                    state["session_status"] = "QUESTIONING"
                    state["current_question"] = build_next_question(state) or {
                        "question_id": "finalize_blocked",
                        "text": "Resolve blocking validation items before finalizing.",
                        "domain": "validation",
                        "blocking_items": validation.blocking_items,
                    }
                    bump_blueprint_version(state)
                    self.store.save(session_id, state, expected_version=expected_blueprint_version)
                    return public_session_view(state)

                return self._block_finalize(
                    session_id,
                    state,
                    expected_blueprint_version,
                    validation.blocking_items,
                    "Validation issues prevent finalization even with force.",
                )

            state["session_status"] = "FINAL_CONFIRMATION"
            if force:
                state["forced_finalization"] = {
                    "forced": True,
                    "overridden_blockers": overridden_blockers,
                    "timestamp": state.get("updated_at"),
                }
            bump_blueprint_version(state)
            self.store.save(session_id, state, expected_version=expected_blueprint_version)
            self._emit(session_id, "blueprint.validation.completed", state, {"ok": validation.ok, "forced": force})
            return public_session_view(state)

    def confirm_handoff(
        self,
        session_id: str,
        *,
        idempotency_key: str,
        expected_blueprint_version: int,
        confirmation: str = "",
    ) -> dict[str, Any]:
        with self.store.session_lock(session_id):
            state = self.store.load(session_id)
            try:
                self.store.claim_idempotency(state, idempotency_key)
            except IdempotencyReplayError:
                return public_session_view(state)
            if confirmation.strip():
                state.setdefault("decisions", []).append(
                    {
                        "id": new_element_id("DEC"),
                        "text": confirmation.strip(),
                        "rationale": "final_confirmation",
                    }
                )
            forced = state.get("forced_finalization", {}) if isinstance(state.get("forced_finalization"), dict) else {}
            validation = validate_blueprint_state(state, finalize=not forced.get("forced"))
            if not validation.ok:
                state["session_status"] = "QUESTIONING"
                bump_blueprint_version(state)
                self.store.save(session_id, state, expected_version=expected_blueprint_version)
                raise ValueError("; ".join(validation.blocking_items))
            state["session_status"] = "FINALIZING"
            artifact = compile_rich_artifact(state, provisional=False)
            executable = compile_executable_projection(state)
            state["artifact"] = artifact
            state["executable_projection"] = executable
            # C22: emit canonical teleology.json alongside the compiled blueprint
            write_teleology_artifact(self.store.host_root, state)
            state["session_status"] = "FINALIZED"
            state["finalized_at"] = state.get("updated_at")
            bump_blueprint_version(state)
            self.store.save(session_id, state, expected_version=expected_blueprint_version)
            self._emit(session_id, "blueprint.finalized", state, {"artifact_version": artifact.get("schema_version")})
            return public_session_view(state)

    def accept_handoff(
        self,
        session_id: str,
        *,
        idempotency_key: str,
        expected_blueprint_version: int,
    ) -> dict[str, Any]:
        with self.store.session_lock(session_id):
            state = self.store.load(session_id)
            try:
                self.store.claim_idempotency(state, idempotency_key)
            except IdempotencyReplayError:
                return public_session_view(state)
            if state.get("session_status") != "FINALIZED":
                raise ValueError("session must be FINALIZED before handoff")
            state["session_status"] = "HANDED_OFF"
            state["handed_off_at"] = state.get("updated_at")
            bump_blueprint_version(state)
            self.store.save(session_id, state, expected_version=expected_blueprint_version)
            self._emit(session_id, "blueprint.handoff.accepted", state, {})
            return public_session_view(state)

    def validation_result(self, session_id: str) -> ValidationResult:
        return validate_blueprint_state(self.store.load(session_id), finalize=True)
