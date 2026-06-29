"""Whole-state evidence model and deterministic analysis snapshot builder."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

from aoc_supervisor.analysis_receipts import summarize_receipts_for_snapshot
from aoc_supervisor.intent_blueprint_state import REQUIRED_DOMAINS
from aoc_supervisor.spec_analysis_types import (
    ANSWER_MODES,
    CLAIM_CLASSIFICATIONS,
    NEXT_ACTIONS,
    RESOLUTION_METHODS,
    RISK_LEVELS,
    AnalysisValidationResult,
    coerce_readiness,
    is_valid_digest,
)

ANALYSIS_SNAPSHOT_VERSION = 1

# Public constant for downstream policy wiring.
POLICY_VERSION_FIELD = "orchestrator_policy_version"


def empty_project_evidence() -> list[dict[str, Any]]:
    return []


def empty_document_evidence() -> list[dict[str, Any]]:
    return []


def empty_research_evidence() -> list[dict[str, Any]]:
    return []


def empty_environment_evidence() -> list[dict[str, Any]]:
    return []


def empty_analysis_receipts() -> list[dict[str, Any]]:
    return []


def empty_requirement_dimension_list() -> list[dict[str, Any]]:
    return []


def default_latest_analysis() -> dict[str, Any] | None:
    return None


def normalize_session_state(state: dict[str, Any]) -> dict[str, Any]:
    """Apply backward-compatible defaults for evidence-aware session fields."""
    state.setdefault("evidence_revision", 0)
    state.setdefault("analysis_revision", 0)
    state.setdefault("analysis_receipts", empty_analysis_receipts())
    state.setdefault("project_evidence", empty_project_evidence())
    state.setdefault("document_evidence", empty_document_evidence())
    state.setdefault("research_evidence", empty_research_evidence())
    state.setdefault("environment_evidence", empty_environment_evidence())
    state.setdefault("latest_analysis", default_latest_analysis())
    state.setdefault("ergonomics_requirements", empty_requirement_dimension_list())
    state.setdefault("automation_boundaries", empty_requirement_dimension_list())
    state.setdefault("accessibility_requirements", empty_requirement_dimension_list())
    state.setdefault("voice_requirements", empty_requirement_dimension_list())

    for collection_name in (
        "analysis_receipts",
        "project_evidence",
        "document_evidence",
        "research_evidence",
        "environment_evidence",
        "ergonomics_requirements",
        "automation_boundaries",
        "accessibility_requirements",
        "voice_requirements",
    ):
        value = state.get(collection_name)
        if not isinstance(value, list):
            state[collection_name] = []

    for numeric_field in ("evidence_revision", "analysis_revision"):
        try:
            state[numeric_field] = max(0, int(state.get(numeric_field, 0)))
        except (TypeError, ValueError):
            state[numeric_field] = 0

    latest = state.get("latest_analysis")
    if latest is not None and not isinstance(latest, dict):
        state["latest_analysis"] = None

    return state


def bump_evidence_revision(state: dict[str, Any]) -> int:
    normalize_session_state(state)
    revision = int(state.get("evidence_revision", 0)) + 1
    state["evidence_revision"] = revision
    return revision


def bump_analysis_revision(state: dict[str, Any]) -> int:
    normalize_session_state(state)
    revision = int(state.get("analysis_revision", 0)) + 1
    state["analysis_revision"] = revision
    return revision


def partition_questions_and_answers(
    entries: list[Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split active and superseded answers for auditable whole-state analysis."""
    active: list[dict[str, Any]] = []
    superseded: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        normalized = deepcopy(entry)
        if normalized.get("superseded_by"):
            superseded.append(normalized)
        else:
            active.append(normalized)
    return active, superseded


def _normalize_evidence_item(item: Any, *, default_classification: str, source_kind: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    text = str(item.get("text", "")).strip()
    if not text:
        return None
    confidence_raw = item.get("confidence", 0.0)
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    classification = str(item.get("classification", default_classification)).strip() or default_classification
    if classification not in CLAIM_CLASSIFICATIONS:
        classification = default_classification
    provenance = item.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {
            "source_kind": source_kind,
            "source_id": str(item.get("id", item.get("evidence_id", ""))),
            "source_label": source_kind,
        }
    return {
        "evidence_id": str(item.get("evidence_id", item.get("id", ""))),
        "text": text,
        "classification": classification,
        "confidence": confidence,
        "provenance": provenance,
        "domain": str(item.get("domain", "")),
        "stale": bool(item.get("stale", False)),
        "superseded_by": str(item.get("superseded_by", "")),
        "metadata": item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
    }


def collect_evidence_items(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten structured session collections into normalized evidence items."""
    normalize_session_state(state)
    items: list[dict[str, Any]] = []

    intent = str(state.get("original_prompt", "")).strip()
    if intent:
        items.append(
            {
                "evidence_id": "intent:original_prompt",
                "text": intent,
                "classification": "confirmed",
                "confidence": 1.0,
                "provenance": {
                    "source_kind": "user_intent",
                    "source_id": "original_prompt",
                    "source_label": "original_intent",
                },
                "domain": "product_scope",
                "stale": False,
                "superseded_by": "",
                "metadata": {},
            }
        )

    active_answers, superseded_answers = partition_questions_and_answers(state.get("questions_and_answers", []))
    for entry in active_answers:
        answer = str(entry.get("answer", "")).strip()
        if not answer:
            continue
        items.append(
            {
                "evidence_id": f"answer:{entry.get('question_id', '')}",
                "text": answer,
                "classification": "confirmed",
                "confidence": 1.0,
                "provenance": {
                    "source_kind": "user_answer",
                    "source_id": str(entry.get("question_id", "")),
                    "source_label": str(entry.get("text", ""))[:120],
                    "input_mode": str(entry.get("input_mode", "typed")),
                },
                "domain": str(entry.get("domain", "")),
                "stale": False,
                "superseded_by": "",
                "metadata": {"active": True},
            }
        )
    for entry in superseded_answers:
        answer = str(entry.get("answer", "")).strip()
        if not answer:
            continue
        items.append(
            {
                "evidence_id": f"answer:{entry.get('question_id', '')}",
                "text": answer,
                "classification": "confirmed",
                "confidence": 0.0,
                "provenance": {
                    "source_kind": "user_answer",
                    "source_id": str(entry.get("question_id", "")),
                    "source_label": str(entry.get("text", ""))[:120],
                    "input_mode": str(entry.get("input_mode", "typed")),
                },
                "domain": str(entry.get("domain", "")),
                "stale": True,
                "superseded_by": str(entry.get("superseded_by", "")),
                "metadata": {"active": False},
            }
        )

    collection_map = {
        "confirmed_requirements": ("confirmed", "user_answer"),
        "inferred_requirements": ("inferred", "derived"),
        "assumptions": ("assumed", "system"),
        "constraints": ("constraint", "system"),
        "non_goals": ("non_goal", "system"),
        "deferred_items": ("deferred", "system"),
        "unresolved_items": ("unresolved", "system"),
        "decisions": ("decision", "user_answer"),
        "risks": ("risk", "system"),
        "acceptance_criteria": ("acceptance_criterion", "system"),
        "project_evidence": ("confirmed", "repository"),
        "document_evidence": ("confirmed", "document"),
        "research_evidence": ("inferred", "research"),
        "environment_evidence": ("confirmed", "environment"),
        "ergonomics_requirements": ("constraint", "system"),
        "automation_boundaries": ("constraint", "system"),
        "accessibility_requirements": ("constraint", "system"),
        "voice_requirements": ("constraint", "system"),
    }
    for collection_name, (classification, source_kind) in collection_map.items():
        for raw in state.get(collection_name, []):
            normalized = _normalize_evidence_item(
                raw,
                default_classification=classification,
                source_kind=source_kind,
            )
            if normalized is not None:
                items.append(normalized)
    return items


def compute_canonical_digest(payload: Any) -> str:
    """Return a stable sha256 digest from canonical JSON serialization."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_analysis_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    """Build a complete deterministic analysis input from the entire session state."""
    normalize_session_state(state)
    active_answers, superseded_answers = partition_questions_and_answers(state.get("questions_and_answers", []))

    confirmed_requirements = [
        deepcopy(item)
        for item in state.get("confirmed_requirements", [])
        if isinstance(item, dict) and not item.get("stale")
    ]
    stale_requirements = [
        deepcopy(item)
        for item in state.get("confirmed_requirements", [])
        if isinstance(item, dict) and item.get("stale")
    ]

    contradictions = [deepcopy(item) for item in state.get("contradictions", []) if isinstance(item, dict)]
    decisions = [
        deepcopy(item) for item in state.get("decisions", []) if isinstance(item, dict) and not item.get("superseded")
    ]
    superseded_decisions = [
        deepcopy(item) for item in state.get("decisions", []) if isinstance(item, dict) and item.get("superseded")
    ]

    snapshot_without_digest: dict[str, Any] = {
        "snapshot_version": ANALYSIS_SNAPSHOT_VERSION,
        "session_id": str(state.get("session_id", "")),
        "schema_version": int(state.get("schema_version", 1)),
        "evidence_revision": int(state.get("evidence_revision", 0)),
        "analysis_revision": int(state.get("analysis_revision", 0)),
        "original_intent": str(state.get("original_prompt", "")),
        "session_status": str(state.get("session_status", "")),
        "blueprint_version": int(state.get("blueprint_version", 0)),
        "questions_and_answers": {
            "active": active_answers,
            "superseded": superseded_answers,
        },
        "confirmed_requirements": confirmed_requirements,
        "stale_requirements": stale_requirements,
        "inferred_requirements": [
            deepcopy(item) for item in state.get("inferred_requirements", []) if isinstance(item, dict)
        ],
        "constraints": [deepcopy(item) for item in state.get("constraints", []) if isinstance(item, dict)],
        "assumptions": [deepcopy(item) for item in state.get("assumptions", []) if isinstance(item, dict)],
        "non_goals": [deepcopy(item) for item in state.get("non_goals", []) if isinstance(item, dict)],
        "deferred_items": [deepcopy(item) for item in state.get("deferred_items", []) if isinstance(item, dict)],
        "unresolved_items": [deepcopy(item) for item in state.get("unresolved_items", []) if isinstance(item, dict)],
        "decisions": decisions,
        "superseded_decisions": superseded_decisions,
        "contradictions": contradictions,
        "risks": [deepcopy(item) for item in state.get("risks", []) if isinstance(item, dict)],
        "acceptance_criteria": [
            deepcopy(item) for item in state.get("acceptance_criteria", []) if isinstance(item, dict)
        ],
        "blueprint_graph": deepcopy(state.get("blueprint_graph", {"version": 0, "nodes": [], "edges": []})),
        "domain_coverage": deepcopy(state.get("domain_coverage", {})),
        "confidence_by_domain": deepcopy(state.get("confidence_by_domain", {})),
        "confidence_threshold": deepcopy(state.get("confidence_threshold", {})),
        "project_evidence": deepcopy(state.get("project_evidence", [])),
        "document_evidence": deepcopy(state.get("document_evidence", [])),
        "research_evidence": deepcopy(state.get("research_evidence", [])),
        "environment_evidence": deepcopy(state.get("environment_evidence", [])),
        "prior_analysis_receipts": summarize_receipts_for_snapshot(state.get("analysis_receipts", [])),
        "ergonomics_requirements": deepcopy(state.get("ergonomics_requirements", [])),
        "automation_boundaries": deepcopy(state.get("automation_boundaries", [])),
        "accessibility_requirements": deepcopy(state.get("accessibility_requirements", [])),
        "voice_requirements": deepcopy(state.get("voice_requirements", [])),
        "evidence_items": collect_evidence_items(state),
        "required_domains": list(REQUIRED_DOMAINS),
        "model_metadata": deepcopy(state.get("model_metadata", {})),
        "orchestrator_policy_version": str(state.get("orchestrator_policy_version", "1.0.0")),
        "current_question": deepcopy(state.get("current_question")),
        "latest_analysis": deepcopy(state.get("latest_analysis")),
        "active_answers": active_answers,
        "superseded_answers": superseded_answers,
        "analysis_receipts": deepcopy(state.get("analysis_receipts", [])),
    }

    digest = compute_canonical_digest(snapshot_without_digest)
    snapshot = {**snapshot_without_digest, "state_digest": digest, "digest": digest}
    return snapshot


def _validate_claim_list(
    items: Any,
    *,
    field_name: str,
    errors: list[str],
    require_text: bool = True,
) -> None:
    if not isinstance(items, list):
        errors.append(f"{field_name} must be a list")
        return
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{field_name}[{index}] must be an object")
            continue
        if require_text and not str(item.get("text", "")).strip():
            errors.append(f"{field_name}[{index}] missing text")
        classification = str(item.get("classification", "")).strip()
        if classification and classification not in CLAIM_CLASSIFICATIONS:
            errors.append(f"{field_name}[{index}] has invalid classification: {classification}")


def _validate_next_question(question: Any, *, errors: list[str]) -> None:
    if question is None:
        return
    if not isinstance(question, dict):
        errors.append("next_question must be an object or null")
        return
    for field_name in ("question_id", "text", "decision_target"):
        if not str(question.get(field_name, "")).strip():
            errors.append(f"next_question missing {field_name}")
    evidence_used = question.get("evidence_used", [])
    if not isinstance(evidence_used, list):
        errors.append("next_question.evidence_used must be a list")
    elif not evidence_used:
        errors.append("next_question must cite evidence_used")
    risk = str(question.get("risk_if_wrong", "low"))
    if risk not in RISK_LEVELS:
        errors.append(f"next_question.risk_if_wrong invalid: {risk}")
    answer_mode = str(question.get("answer_mode", "freeform"))
    if answer_mode not in ANSWER_MODES:
        errors.append(f"next_question.answer_mode invalid: {answer_mode}")
    text = str(question.get("text", ""))
    if text.count("?") > 1 or re.search(r"\b(and|also)\b.+\?", text, flags=re.IGNORECASE):
        errors.append("next_question must ask one decision at a time")


def _validate_resolved_without_user(items: Any, *, errors: list[str]) -> None:
    if not isinstance(items, list):
        errors.append("resolved_without_user must be a list")
        return
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"resolved_without_user[{index}] must be an object")
            continue
        method = str(item.get("method", "")).strip()
        if method not in RESOLUTION_METHODS:
            errors.append(f"resolved_without_user[{index}] has invalid method: {method}")


def _validate_unresolved(items: Any, *, errors: list[str]) -> None:
    if not isinstance(items, list):
        errors.append("unresolved must be a list")
        return
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"unresolved[{index}] must be an object")
            continue
        if not str(item.get("text", "")).strip():
            errors.append(f"unresolved[{index}] missing text")
        method = str(item.get("recommended_resolution", "ASK")).strip() or "ASK"
        if method not in NEXT_ACTIONS:
            errors.append(f"unresolved[{index}] has invalid recommended_resolution: {method}")


def validate_analysis_output(
    output: Any,
    *,
    expected_state_digest: str | None = None,
    known_evidence_ids: set[str] | None = None,
    known_decision_targets: set[str] | None = None,
) -> AnalysisValidationResult:
    """Reject malformed, multi-question, or policy-violating analysis output."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(output, dict):
        return AnalysisValidationResult(ok=False, errors=["analysis output must be an object"])

    for hidden in ("chain_of_thought", "raw_model_output", "private_reasoning"):
        if hidden in output:
            errors.append(f"analysis output must not contain hidden field: {hidden}")

    for field_name in ("analysis_revision", "evidence_revision"):
        try:
            value = int(output.get(field_name, -1))
        except (TypeError, ValueError):
            errors.append(f"{field_name} must be an integer")
            continue
        if value < 0:
            errors.append(f"{field_name} must be non-negative")

    state_digest = str(output.get("state_digest", ""))
    if not is_valid_digest(state_digest):
        errors.append("state_digest must be sha256:<64 hex chars>")
    elif expected_state_digest and state_digest != expected_state_digest:
        errors.append("state_digest does not match analysis snapshot")

    _validate_claim_list(output.get("facts", []), field_name="facts", errors=errors)
    _validate_claim_list(output.get("inferences", []), field_name="inferences", errors=errors)
    _validate_claim_list(output.get("assumptions", []), field_name="assumptions", errors=errors)
    _validate_claim_list(
        output.get("contradictions", []),
        field_name="contradictions",
        errors=errors,
        require_text=False,
    )
    _validate_resolved_without_user(output.get("resolved_without_user", []), errors=errors)
    _validate_unresolved(output.get("unresolved", []), errors=errors)

    readiness = coerce_readiness(output.get("readiness"))
    if readiness is None:
        errors.append("readiness must be an object")
    else:
        score = readiness.get("score", 0.0)
        if not 0.0 <= float(score) <= 1.0:
            errors.append("readiness.score must be between 0 and 1")

    next_action = str(output.get("next_action", "")).strip()
    if next_action not in NEXT_ACTIONS:
        errors.append(f"next_action invalid: {next_action}")

    next_question = output.get("next_question")
    if next_action == "ASK":
        if next_question is None:
            errors.append("next_question is required when next_action is ASK")
        else:
            _validate_next_question(next_question, errors=errors)
    elif next_action == "CONFIRM":
        if next_question is None:
            errors.append("next_question is required when next_action is CONFIRM")
        else:
            _validate_next_question(next_question, errors=errors)
    elif next_question is not None:
        errors.append("next_question must be null unless next_action is ASK or CONFIRM")

    if isinstance(next_question, dict) and known_evidence_ids is not None:
        for evidence_id in next_question.get("evidence_used", []):
            if str(evidence_id) and str(evidence_id) not in known_evidence_ids:
                warnings.append(f"next_question cites unknown evidence id: {evidence_id}")

    if isinstance(next_question, dict) and known_decision_targets is not None:
        target = str(next_question.get("decision_target", "")).strip()
        if target and target in known_decision_targets:
            errors.append(f"next_question repeats known decision target: {target}")

    return AnalysisValidationResult(ok=not errors, errors=errors, warnings=warnings)


def known_decision_targets_from_snapshot(snapshot: dict[str, Any]) -> set[str]:
    """Collect decision targets already resolved in the current snapshot."""
    targets: set[str] = set()
    for collection_name in ("facts", "resolved_without_user"):
        for item in snapshot.get(collection_name, []):
            if isinstance(item, dict):
                target = str(item.get("decision_target", "")).strip()
                if target:
                    targets.add(target)
    for item in snapshot.get("evidence_items", []):
        if isinstance(item, dict) and not item.get("stale"):
            target = str(item.get("metadata", {}).get("decision_target", "")).strip()
            if target:
                targets.add(target)
    for answer in snapshot.get("questions_and_answers", {}).get("active", []):
        if isinstance(answer, dict):
            target = str(answer.get("decision_target", answer.get("domain", ""))).strip()
            if target:
                targets.add(target)
    return targets


def known_evidence_ids_from_snapshot(snapshot: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for item in snapshot.get("evidence_items", []):
        if isinstance(item, dict):
            evidence_id = str(item.get("evidence_id", "")).strip()
            if evidence_id:
                ids.add(evidence_id)
    return ids


def validate_analysis_output_for_snapshot(
    output: Any,
    snapshot: dict[str, Any],
) -> AnalysisValidationResult:
    """Validate analysis output against a built snapshot."""
    return validate_analysis_output(
        output,
        expected_state_digest=str(snapshot.get("state_digest", "")),
        known_evidence_ids=known_evidence_ids_from_snapshot(snapshot),
        known_decision_targets=known_decision_targets_from_snapshot(snapshot),
    )


def _self_check() -> None:
    """Narrow module-level invariant checks for local verification."""
    from aoc_supervisor.intent_blueprint_state import new_blueprint_state, new_session_id

    state = new_blueprint_state(
        session_id=new_session_id(),
        user_id="self-check",
        tier="paid",
        original_prompt="Build a local filesystem analytics tool.",
    )
    snapshot_a = build_analysis_snapshot(state)
    snapshot_b = build_analysis_snapshot(state)
    if snapshot_a["state_digest"] != snapshot_b["state_digest"]:
        raise RuntimeError("snapshot digest must be stable for unchanged state")

    state["project_evidence"] = [{"id": "repo-1", "text": "Python service in monorepo", "confidence": 0.9}]
    revised = build_analysis_snapshot(state)
    if revised["state_digest"] == snapshot_a["state_digest"]:
        raise RuntimeError("snapshot digest must change when evidence changes")

    valid_output = {
        "analysis_revision": 1,
        "evidence_revision": 1,
        "state_digest": revised["state_digest"],
        "facts": [],
        "inferences": [],
        "assumptions": [],
        "contradictions": [],
        "resolved_without_user": [],
        "unresolved": [],
        "readiness": {
            "score": 0.2,
            "blocking_count": 1,
            "high_value_unknown_count": 1,
            "ready_to_finalize": False,
            "reason": "missing deployment target",
        },
        "next_action": "ASK",
        "next_question": {
            "question_id": "q_test",
            "text": "What deployment environment should V1 target?",
            "decision_target": "deployment_environment",
            "why_it_matters": "Hosting constraints affect architecture.",
            "evidence_used": ["intent:original_prompt"],
            "alternatives_considered": ["DERIVE", "DEFAULT"],
            "recommended_default": None,
            "risk_if_wrong": "medium",
            "answer_mode": "freeform",
        },
    }
    result = validate_analysis_output_for_snapshot(valid_output, revised)
    if not result.ok:
        raise RuntimeError(f"expected valid analysis output: {result.errors}")

    invalid = dict(valid_output)
    invalid["next_question"] = {
        **valid_output["next_question"],
        "text": "What is the goal and who are the users?",
        "evidence_used": [],
    }
    bad = validate_analysis_output_for_snapshot(invalid, revised)
    if bad.ok:
        raise RuntimeError("expected invalid analysis output to be rejected")


if __name__ == "__main__":
    _self_check()
    print("evidence_state self-check passed")
