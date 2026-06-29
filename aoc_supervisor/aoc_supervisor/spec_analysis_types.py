"""Typed structures for Perfect SPEC whole-state analysis input and output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

# Claim classifications used when reclassifying session knowledge.
CLAIM_CLASSIFICATIONS: frozenset[str] = frozenset(
    {
        "confirmed",
        "inferred",
        "assumed",
        "contradicted",
        "unresolved",
        "deferred",
        "non_goal",
        "constraint",
        "decision",
        "risk",
        "acceptance_criterion",
    }
)

# Resolution methods considered before asking the user.
RESOLUTION_METHODS: frozenset[str] = frozenset(
    {
        "DERIVE",
        "RESEARCH",
        "DEFAULT",
        "CONFIRM",
        "ASK",
        "DEFER",
        "NOT_APPLICABLE",
    }
)

# Structured next actions returned by the reasoning engine.
NEXT_ACTIONS: frozenset[str] = frozenset(
    {
        *RESOLUTION_METHODS,
        "CONFLICT_RESOLUTION",
        "FINALIZE",
    }
)

RISK_LEVELS: frozenset[str] = frozenset({"low", "medium", "high", "critical"})
ANSWER_MODES: frozenset[str] = frozenset({"freeform", "single_choice", "multi_choice", "confirm"})
EVIDENCE_SOURCE_KINDS: frozenset[str] = frozenset(
    {
        "user_answer",
        "user_intent",
        "repository",
        "document",
        "research",
        "environment",
        "derived",
        "defaulted",
        "voice_transcript",
        "system",
    }
)


class EvidenceProvenance(TypedDict, total=False):
    """Concise provenance for an evidence item; no hidden chain-of-thought."""

    source_kind: str
    source_id: str
    source_label: str
    captured_at: str
    derivation_method: str
    provider_id: str
    model_id: str
    input_mode: str


class EvidenceItem(TypedDict, total=False):
    """Normalized evidence unit referenced by analysis output."""

    evidence_id: str
    text: str
    classification: str
    confidence: float
    provenance: EvidenceProvenance
    domain: str
    stale: bool
    superseded_by: str
    metadata: dict[str, Any]


class ConfidenceRecord(TypedDict, total=False):
    """Domain or claim confidence with explicit basis."""

    target_id: str
    domain: str
    score: float
    basis: str
    threshold: float
    above_threshold: bool


class UnresolvedUncertainty(TypedDict, total=False):
    """Remaining user-dependent or high-value unknown."""

    uncertainty_id: str
    text: str
    decision_target: str
    classification: str
    blocking: bool
    risk_if_wrong: str
    recommended_resolution: str
    evidence_refs: list[str]
    rationale: str


class ResolvedWithoutUser(TypedDict, total=False):
    """Gap closed without user burden."""

    resolution_id: str
    text: str
    method: str
    decision_target: str
    confidence: float
    evidence_refs: list[str]
    rationale: str
    reversible: bool


class ContradictionRecord(TypedDict, total=False):
    """Structured contradiction surfaced during analysis."""

    contradiction_id: str
    element_a_id: str
    element_b_id: str
    description: str
    blocking: bool
    resolved: bool
    resolution_text: str


class ReadinessSnapshot(TypedDict, total=False):
    """SPEC readiness telemetry; not a domain checklist."""

    score: float
    blocking_count: int
    high_value_unknown_count: int
    ready_to_finalize: bool
    reason: str


class NextQuestion(TypedDict, total=False):
    """At most one generated question per analysis pass."""

    question_id: str
    text: str
    decision_target: str
    why_it_matters: str
    evidence_used: list[str]
    alternatives_considered: list[str]
    recommended_default: str | None
    risk_if_wrong: str
    answer_mode: str
    domain: str


class AnalysisOutput(TypedDict, total=False):
    """Validated reasoning-engine response before session mutation."""

    analysis_revision: int
    evidence_revision: int
    state_digest: str
    facts: list[dict[str, Any]]
    inferences: list[dict[str, Any]]
    assumptions: list[dict[str, Any]]
    contradictions: list[dict[str, Any]]
    resolved_without_user: list[dict[str, Any]]
    unresolved: list[dict[str, Any]]
    readiness: ReadinessSnapshot
    next_action: str
    next_question: NextQuestion | None


class AnalysisSnapshot(TypedDict, total=False):
    """Deterministic whole-state input passed to the reasoning engine."""

    snapshot_version: int
    session_id: str
    schema_version: int
    evidence_revision: int
    analysis_revision: int
    state_digest: str
    original_intent: str
    session_status: str
    questions_and_answers: dict[str, list[dict[str, Any]]]
    confirmed_requirements: list[dict[str, Any]]
    inferred_requirements: list[dict[str, Any]]
    constraints: list[dict[str, Any]]
    assumptions: list[dict[str, Any]]
    non_goals: list[dict[str, Any]]
    deferred_items: list[dict[str, Any]]
    unresolved_items: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    contradictions: list[dict[str, Any]]
    risks: list[dict[str, Any]]
    acceptance_criteria: list[dict[str, Any]]
    blueprint_graph: dict[str, Any]
    domain_coverage: dict[str, dict[str, Any]]
    confidence_by_domain: dict[str, float]
    confidence_threshold: dict[str, float]
    project_evidence: list[dict[str, Any]]
    document_evidence: list[dict[str, Any]]
    research_evidence: list[dict[str, Any]]
    environment_evidence: list[dict[str, Any]]
    prior_analysis_receipts: list[dict[str, Any]]
    ergonomics_requirements: list[dict[str, Any]]
    automation_boundaries: list[dict[str, Any]]
    accessibility_requirements: list[dict[str, Any]]
    voice_requirements: list[dict[str, Any]]
    model_metadata: dict[str, Any]
    orchestrator_policy_version: str
    current_question: dict[str, Any] | None
    blueprint_version: int


@dataclass
class AnalysisValidationResult:
    """Outcome of validating structured analysis output."""

    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def is_valid_digest(value: Any) -> bool:
    text = str(value or "")
    if not text.startswith("sha256:"):
        return False
    hex_part = text[7:]
    return len(hex_part) == 64 and all(ch in "0123456789abcdef" for ch in hex_part)


def coerce_readiness(payload: Any) -> ReadinessSnapshot | None:
    if not isinstance(payload, dict):
        return None
    return {
        "score": float(payload.get("score", 0.0)),
        "blocking_count": int(payload.get("blocking_count", 0)),
        "high_value_unknown_count": int(payload.get("high_value_unknown_count", 0)),
        "ready_to_finalize": bool(payload.get("ready_to_finalize", False)),
        "reason": str(payload.get("reason", "")),
    }


NextAction = Literal[
    "DERIVE",
    "RESEARCH",
    "DEFAULT",
    "CONFIRM",
    "ASK",
    "DEFER",
    "NOT_APPLICABLE",
    "CONFLICT_RESOLUTION",
    "FINALIZE",
]
