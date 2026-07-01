"""Canonical Intent Forge blueprint session state (v2.1)."""

from __future__ import annotations

import time
import uuid
from copy import deepcopy
from typing import Any

INTENT_FORGE_SCHEMA_VERSION = 1

SESSION_STATUSES = frozenset(
    {
        "CREATED",
        "ANALYZING",
        "ANALYSIS_BLOCKED",
        "QUESTIONING",
        "PAUSED",
        "CONFLICT_RESOLUTION",
        "VALIDATING",
        "FINAL_CONFIRMATION",
        "FINALIZING",
        "FINALIZED",
        "HANDED_OFF",
        "ABANDONED",
    }
)

# Descriptive coverage telemetry only; MUST NOT control questioning order.
REQUIRED_DOMAINS: tuple[str, ...] = (
    "product_scope",
    "target_users",
    "user_journeys",
    "functional_requirements",
    "non_functional_requirements",
    "interface_behavior",
    "data_model",
    "business_rules",
    "authz",
    "security_privacy",
    "error_handling",
    "infrastructure",
    "performance",
    "observability",
    "testing_acceptance",
    "risks_assumptions",
)

DEFAULT_CONFIDENCE_THRESHOLD = 0.65


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def new_question_id() -> str:
    return f"q_{uuid.uuid4().hex[:10]}"


def new_element_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


def empty_domain_coverage() -> dict[str, dict[str, Any]]:
    return {domain: {"addressed": False, "na": False} for domain in REQUIRED_DOMAINS}


def empty_confidence_by_domain() -> dict[str, float]:
    return {domain: 0.0 for domain in REQUIRED_DOMAINS}


def empty_confidence_threshold() -> dict[str, float]:
    return {domain: DEFAULT_CONFIDENCE_THRESHOLD for domain in REQUIRED_DOMAINS}


def new_blueprint_state(
    *,
    session_id: str,
    user_id: str,
    tier: str,
    original_prompt: str,
    session_status: str = "CREATED",
) -> dict[str, Any]:
    now = _now_iso()
    return {
        "schema_version": INTENT_FORGE_SCHEMA_VERSION,
        "session_id": session_id,
        "user_id": user_id,
        "tier": tier,
        "session_status": session_status,
        "original_prompt": original_prompt,
        "questions_and_answers": [],
        "confirmed_requirements": [],
        "inferred_requirements": [],
        "constraints": [],
        "decisions": [],
        "assumptions": [],
        "non_goals": [],
        "deferred_items": [],
        "unresolved_items": [],
        "contradictions": [],
        "risks": [],
        "domain_coverage": empty_domain_coverage(),
        "confidence_by_domain": empty_confidence_by_domain(),
        "confidence_threshold": empty_confidence_threshold(),
        "acceptance_criteria": [],
        "blueprint_graph": {"version": 0, "nodes": [], "edges": []},
        "blueprint_version": 0,
        "orchestrator_policy_version": "1.0.0",
        "model_metadata": {},
        "telemetry_consent": {"operational": True, "analytics": False, "training": False},
        "processed_idempotency_keys": [],
        "current_question": None,
        "evidence_revision": 0,
        "analysis_revision": 0,
        "analysis_receipts": [],
        "project_evidence": [],
        "document_evidence": [],
        "research_evidence": [],
        "environment_evidence": [],
        "latest_analysis": None,
        "ergonomics_requirements": [],
        "automation_boundaries": [],
        "accessibility_requirements": [],
        "voice_requirements": [],
        "created_at": now,
        "updated_at": now,
        "finalized_at": None,
        "handed_off_at": None,
        "artifact": None,
        "executable_projection": None,
    }


def bump_blueprint_version(state: dict[str, Any]) -> int:
    version = int(state.get("blueprint_version", 0)) + 1
    state["blueprint_version"] = version
    graph = state.setdefault("blueprint_graph", {"version": 0, "nodes": [], "edges": []})
    if isinstance(graph, dict):
        graph["version"] = version
    state["updated_at"] = _now_iso()
    return version


def normalize_blueprint_state(state: dict[str, Any]) -> dict[str, Any]:
    """Ensure evidence-aware fields exist for legacy serialized sessions."""
    from aoc_supervisor.evidence_state import normalize_session_state

    return normalize_session_state(state)


def public_session_view(state: dict[str, Any]) -> dict[str, Any]:
    """Safe API projection without internal idempotency bookkeeping."""
    from aoc_supervisor.claims_ledger import build_claim_ledger

    payload = deepcopy(normalize_blueprint_state(state))
    payload.pop("processed_idempotency_keys", None)
    payload["claims_ledger"] = build_claim_ledger(payload)
    return payload


def assert_status(state: dict[str, Any], *allowed: str) -> None:
    status = str(state.get("session_status", ""))
    if status not in allowed:
        raise ValueError(f"session status {status} not in {allowed}")
