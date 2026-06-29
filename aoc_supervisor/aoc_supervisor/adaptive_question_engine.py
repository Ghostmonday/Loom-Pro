"""Whole-state adaptive question engine for Perfect SPEC interrogation."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any

from aoc_supervisor.intent_blueprint_state import new_element_id
from aoc_supervisor.reasoning_provider import (
    ProviderFailureError,
    ReasoningProvider,
    create_reasoning_provider,
    sanitize_provider_text,
)
from aoc_supervisor.reasoning_schema import (
    POLICY_VERSION,
    AnalysisOutput,
    AnalysisReceipt,
    NextAction,
    PolicyValidationError,
    SchemaValidationError,
    analysis_output_to_dict,
    enforce_analysis_policy,
    parse_analysis_output,
    receipt_to_dict,
)

try:
    from aoc_supervisor.evidence_state import build_analysis_snapshot as _external_build_snapshot
    from aoc_supervisor.evidence_state import compute_state_digest as _external_compute_digest
except ImportError:  # pragma: no cover - Subagent A integration path
    _external_build_snapshot = None
    _external_compute_digest = None

try:
    from aoc_supervisor.analysis_receipts import append_analysis_receipt as _external_append_receipt
except ImportError:  # pragma: no cover - Subagent A integration path
    _external_append_receipt = None

MAX_AUTO_RESOLUTION_PASSES = 8


@dataclass(frozen=True)
class EngineResult:
    output: AnalysisOutput
    snapshot: dict[str, Any]
    receipt: AnalysisReceipt
    compatibility_question: dict[str, Any] | None = None


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def compute_state_digest(snapshot: dict[str, Any]) -> str:
    if _external_compute_digest is not None:
        return _external_compute_digest(snapshot)
    digest = hashlib.sha256(_canonical_json(snapshot).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _active_answers(state: dict[str, Any]) -> list[dict[str, Any]]:
    active: list[dict[str, Any]] = []
    for entry in state.get("questions_and_answers", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("superseded_by"):
            continue
        active.append(dict(entry))
    return active


def _superseded_answers(state: dict[str, Any]) -> list[dict[str, Any]]:
    superseded: list[dict[str, Any]] = []
    for entry in state.get("questions_and_answers", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("superseded_by"):
            superseded.append(dict(entry))
    return superseded


def build_analysis_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical whole-state analysis input."""
    if _external_build_snapshot is not None:
        return _external_build_snapshot(state)

    analysis_revision = int(state.get("analysis_revision", 0)) + 1
    evidence_revision = int(state.get("evidence_revision", state.get("blueprint_version", 0)))
    snapshot: dict[str, Any] = {
        "session_id": state.get("session_id"),
        "original_intent": str(state.get("original_prompt", "")).strip(),
        "analysis_revision": analysis_revision,
        "evidence_revision": evidence_revision,
        "active_answers": _active_answers(state),
        "superseded_answers": _superseded_answers(state),
        "confirmed_requirements": list(state.get("confirmed_requirements", [])),
        "inferred_requirements": list(state.get("inferred_requirements", [])),
        "assumptions": list(state.get("assumptions", [])),
        "constraints": list(state.get("constraints", [])),
        "non_goals": list(state.get("non_goals", [])),
        "decisions": list(state.get("decisions", [])),
        "contradictions": list(state.get("contradictions", [])),
        "unresolved_items": list(state.get("unresolved_items", [])),
        "deferred_items": list(state.get("deferred_items", [])),
        "risks": list(state.get("risks", [])),
        "acceptance_criteria": list(state.get("acceptance_criteria", [])),
        "blueprint_graph": state.get("blueprint_graph", {}),
        "domain_coverage": state.get("domain_coverage", {}),
        "confidence_by_domain": state.get("confidence_by_domain", {}),
        "project_evidence": list(state.get("project_evidence", [])),
        "document_evidence": list(state.get("document_evidence", [])),
        "research_evidence": list(state.get("research_evidence", [])),
        "environment_evidence": list(state.get("environment_evidence", [])),
        "analysis_receipts": list(state.get("analysis_receipts", [])),
        "ergonomics_requirements": list(state.get("ergonomics_requirements", [])),
        "accessibility_requirements": list(state.get("accessibility_requirements", [])),
        "voice_requirements": list(state.get("voice_requirements", [])),
        "automation_boundaries": list(state.get("automation_boundaries", [])),
        "model_metadata": dict(state.get("model_metadata", {})),
    }
    snapshot["state_digest"] = compute_state_digest(snapshot)
    return snapshot


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _build_receipt(
    *,
    snapshot: dict[str, Any],
    output: AnalysisOutput,
    provider: ReasoningProvider,
) -> AnalysisReceipt:
    return AnalysisReceipt(
        input_digest=str(snapshot.get("state_digest", "")),
        output_digest=f"sha256:{hashlib.sha256(_canonical_json(analysis_output_to_dict(output)).encode()).hexdigest()}",
        provider_id=getattr(provider, "provider_id", "unknown"),
        model_id=getattr(provider, "model_id", "unknown"),
        policy_version=POLICY_VERSION,
        timestamp=_now_iso(),
        analysis_revision=output.analysis_revision,
        evidence_revision=output.evidence_revision,
        next_action=output.next_action,
        rationale=output.readiness.reason,
    )


def _append_receipt(state: dict[str, Any], receipt: AnalysisReceipt) -> None:
    import uuid

    dct = receipt_to_dict(receipt)
    dct.setdefault("receipt_id", f"rcpt_{uuid.uuid4().hex[:12]}")
    dct.setdefault("status", "completed")
    dct.setdefault("readiness_score", 0.0)
    dct.setdefault("ready_to_finalize", False)
    if _external_append_receipt is not None:
        _external_append_receipt(state, dct)
        return
    state.setdefault("analysis_receipts", []).append(dct)


def _persist_analysis(state: dict[str, Any], result: EngineResult) -> None:
    output_dict = analysis_output_to_dict(result.output)
    state["latest_analysis"] = output_dict
    state["analysis_revision"] = result.output.analysis_revision
    state["evidence_revision"] = result.output.evidence_revision
    state.pop("analysis_recovery", None)
    _append_receipt(state, result.receipt)

    from aoc_supervisor.conflict_resolver import merge_contradictions

    merge_contradictions(state, list(result.output.contradictions))


def _record_provider_failure(state: dict[str, Any], error: ProviderFailureError) -> None:
    state["analysis_recovery"] = {
        "code": error.code,
        "message": error.message,
        "retryable": error.retryable,
        "policy_version": POLICY_VERSION,
        "timestamp": _now_iso(),
    }


def _apply_auto_resolution(state: dict[str, Any], resolution: dict[str, Any]) -> None:
    method = str(resolution.get("method") or resolution.get("resolution_method") or "").upper()
    target = str(resolution.get("decision_target", "")).strip()
    text = sanitize_provider_text(str(resolution.get("text", "")).strip())
    domain = str(resolution.get("domain", "functional_requirements")).strip() or "functional_requirements"

    if method == NextAction.NOT_APPLICABLE:
        coverage = state.setdefault("domain_coverage", {})
        if isinstance(coverage, dict):
            meta = coverage.setdefault(domain, {"addressed": False, "na": False})
            if isinstance(meta, dict):
                meta["na"] = True
                meta["addressed"] = True
        return

    if method in {NextAction.DERIVE, NextAction.DEFAULT, NextAction.RESEARCH, NextAction.DEFER}:
        req_id = new_element_id("REQ")
        target_bucket = "confirmed_requirements" if method == NextAction.DERIVE else "inferred_requirements"
        state.setdefault(target_bucket, []).append(
            {
                "id": req_id,
                "text": text,
                "source_question_id": None,
                "confidence": 0.8 if method == NextAction.DERIVE else 0.7,
                "domain": domain,
                "decision_target": target,
                "resolution_method": method,
            }
        )
        state.setdefault("decisions", []).append(
            {
                "id": new_element_id("DEC"),
                "decision_target": target,
                "text": text,
                "method": method,
                "reversible": bool(resolution.get("reversible", True)),
            }
        )
        coverage = state.setdefault("domain_coverage", {})
        if isinstance(coverage, dict):
            meta = coverage.setdefault(domain, {"addressed": False, "na": False})
            if isinstance(meta, dict):
                meta["addressed"] = True
        confidence = state.setdefault("confidence_by_domain", {})
        if isinstance(confidence, dict):
            confidence[domain] = max(float(confidence.get(domain, 0.0)), 0.75)


def _apply_resolutions(state: dict[str, Any], output: AnalysisOutput) -> bool:
    changed = False
    for resolution in output.resolved_without_user:
        if not isinstance(resolution, dict):
            continue
        _apply_auto_resolution(state, resolution)
        res_copy = dict(resolution)
        if "resolution_method" not in res_copy and "method" in res_copy:
            res_copy["resolution_method"] = res_copy["method"]
        state.setdefault("resolved_without_user", []).append(res_copy)
        changed = True
    return changed


def _compatibility_question(output: AnalysisOutput) -> dict[str, Any] | None:
    if output.next_action not in {NextAction.ASK, NextAction.CONFIRM}:
        return None
    question = output.next_question
    if question is None:
        return None
    impact = "high" if question.risk_if_wrong in {"high", "medium"} else "medium"
    return {
        "question_id": question.question_id,
        "domain": question.domain or question.decision_target,
        "decision_target": question.decision_target,
        "text": sanitize_provider_text(question.text),
        "why_it_matters": sanitize_provider_text(question.why_it_matters),
        "impact_hint": impact,
        "recommended_default": question.recommended_default,
        "evidence_used": list(question.evidence_used),
        "alternatives_considered": list(question.alternatives_considered),
        "answer_mode": question.answer_mode,
        "next_action": output.next_action,
        "risk_if_wrong": question.risk_if_wrong,
    }


class AdaptiveQuestionEngine:
    """Analyze complete evidence and select exactly one next action."""

    def __init__(self, provider: ReasoningProvider | None = None) -> None:
        self.provider: ReasoningProvider = provider if provider is not None else create_reasoning_provider()

    def start_questioning(self, state: dict[str, Any]) -> dict[str, Any]:
        question = self.select_next(state)
        state["current_question"] = question
        if question:
            state["session_status"] = question.get("next_action", "ASK")
        else:
            state["session_status"] = "FINALIZED"
        return state

    def submit_answer(
        self,
        state: dict[str, Any],
        *,
        answer: str,
        question_id: str,
    ) -> dict[str, Any]:
        current = state.get("current_question") or {}
        domain = str(current.get("domain") or "functional_requirements")

        conflict_resolution = state.get("session_status") == "CONFLICT_RESOLUTION"

        entry = {
            "question_id": question_id,
            "text": current.get("text", ""),
            "answer": answer.strip(),
            "domain": domain,
            "timestamp": state.get("updated_at"),
        }
        state.setdefault("questions_and_answers", []).append(entry)

        req_id = new_element_id("REQ")
        state.setdefault("confirmed_requirements", []).append(
            {
                "id": req_id,
                "text": answer.strip(),
                "source_question_id": question_id,
                "confidence": 1.0,
                "domain": domain,
            }
        )

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
                    "id": req_id,
                    "label": answer.strip()[:80],
                    "kind": "requirement",
                    "domain": domain,
                    "confidence": confidence.get(domain, 0.8) if isinstance(confidence, dict) else 0.8,
                }
            )

        if conflict_resolution:
            for contradiction in state.get("contradictions", []):
                if isinstance(contradiction, dict):
                    contradiction["resolved"] = True
                    contradiction["resolution_text"] = answer.strip()

        state["current_question"] = None
        state["session_status"] = "QUESTIONING"

        latest = state.get("latest_analysis")
        ready = False
        if isinstance(latest, dict):
            readiness = latest.get("readiness", {})
            if isinstance(readiness, dict) and readiness.get("ready_to_finalize"):
                ready = True

        if ready:
            state["session_status"] = "VALIDATING"
        else:
            question = self.select_next(state)
            state["current_question"] = question
            if question:
                state["session_status"] = question.get("next_action", "ASK")
            else:
                state["session_status"] = "VALIDATING"

        return state

    def revise_answer(
        self,
        state: dict[str, Any],
        *,
        question_id: str,
        answer: str,
    ) -> dict[str, Any]:
        qas = state.setdefault("questions_and_answers", [])
        old_qa = None
        for item in qas:
            if isinstance(item, dict) and item.get("question_id") == question_id:
                old_qa = item
                break

        if old_qa is None:
            raise ValueError(f"Answer with question_id {question_id} not found")

        import uuid

        new_q_id = f"{question_id}_rev_{uuid.uuid4().hex[:6]}"
        old_qa["superseded_by"] = new_q_id

        new_qa = {
            "question_id": new_q_id,
            "revises": question_id,
            "text": old_qa.get("text", ""),
            "answer": answer.strip(),
            "domain": old_qa.get("domain", "functional_requirements"),
            "timestamp": _now_iso(),
        }
        qas.append(new_qa)

        for req in state.setdefault("confirmed_requirements", []):
            if isinstance(req, dict) and req.get("source_question_id") == question_id:
                req["stale"] = True

        question = self.select_next(state)
        state["current_question"] = question
        if question:
            state["session_status"] = question.get("next_action", "ASK")
        else:
            state["session_status"] = "VALIDATING"

        return state

    def analyze(self, state: dict[str, Any], *, mutate_state: bool = True) -> EngineResult:
        snapshot = build_analysis_snapshot(state)
        try:
            raw = self.provider.analyze(snapshot)
        except ProviderFailureError:
            if mutate_state:
                raise
            raise
        except Exception as exc:
            failure = ProviderFailureError(
                code="provider_exception",
                message=str(exc),
                retryable=True,
            )
            if mutate_state:
                _record_provider_failure(state, failure)
            raise failure from exc

        try:
            output = parse_analysis_output(raw)
            if output.state_digest and output.state_digest != snapshot.get("state_digest"):
                raise PolicyValidationError(["state_digest mismatch between snapshot and provider output"])
            output = enforce_analysis_policy(output, snapshot)
        except (SchemaValidationError, PolicyValidationError) as exc:
            failure = ProviderFailureError(
                code="invalid_provider_output",
                message=str(exc),
                retryable=True,
            )
            if mutate_state:
                _record_provider_failure(state, failure)
            raise failure from exc

        receipt = _build_receipt(snapshot=snapshot, output=output, provider=self.provider)
        result = EngineResult(
            output=output,
            snapshot=snapshot,
            receipt=receipt,
            compatibility_question=_compatibility_question(output),
        )
        if mutate_state:
            _persist_analysis(state, result)
        return result

    def select_next(self, state: dict[str, Any]) -> dict[str, Any] | None:
        """Return one compatibility question or None when questioning should stop."""
        passes = 0
        while passes < MAX_AUTO_RESOLUTION_PASSES:
            passes += 1
            result = self.analyze(state, mutate_state=True)

            action = result.output.next_action
            if action == NextAction.FINALIZE:
                return None
            if action == NextAction.CONFLICT_RESOLUTION:
                return None
            if action in {NextAction.ASK, NextAction.CONFIRM}:
                return result.compatibility_question
            if _apply_resolutions(state, result.output):
                continue
            return None
        return None

    def should_stop(self, state: dict[str, Any]) -> bool:
        latest = state.get("latest_analysis")
        if isinstance(latest, dict):
            readiness = latest.get("readiness", {})
            if isinstance(readiness, dict) and readiness.get("ready_to_finalize"):
                return True
            if str(latest.get("next_action", "")).upper() == NextAction.FINALIZE:
                return True
        unresolved = [
            item for item in state.get("contradictions", []) if isinstance(item, dict) and not item.get("resolved")
        ]
        if unresolved:
            return False
        blocking = [
            item for item in state.get("unresolved_items", []) if isinstance(item, dict) and item.get("blocking")
        ]
        if blocking:
            return False
        try:
            result = self.analyze(state, mutate_state=False)
        except ProviderFailureError:
            return False
        return result.output.next_action == NextAction.FINALIZE or result.output.readiness.ready_to_finalize


_DEFAULT_ENGINE = AdaptiveQuestionEngine()


def get_default_engine() -> AdaptiveQuestionEngine:
    return _DEFAULT_ENGINE


def set_default_provider(provider: ReasoningProvider) -> None:
    global _DEFAULT_ENGINE
    _DEFAULT_ENGINE = AdaptiveQuestionEngine(provider=provider)


def get_analysis_recovery(state: dict[str, Any]) -> dict[str, Any] | None:
    recovery = state.get("analysis_recovery")
    return dict(recovery) if isinstance(recovery, dict) else None
