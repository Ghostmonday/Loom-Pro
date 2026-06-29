"""Typed schemas and validation for adaptive SPEC interrogation analysis output."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, is_dataclass

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return self.value


from typing import Any

POLICY_VERSION = "2.0.0-adaptive"

_QUESTION_MARKERS = re.compile(r"\?|^(?:what|who|how|when|where|why|which|should|can|do|does|is|are)\b", re.I)


class NextAction(StrEnum):
    DERIVE = "DERIVE"
    RESEARCH = "RESEARCH"
    DEFAULT = "DEFAULT"
    CONFIRM = "CONFIRM"
    ASK = "ASK"
    DEFER = "DEFER"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONFLICT_RESOLUTION = "CONFLICT_RESOLUTION"
    FINALIZE = "FINALIZE"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnswerMode(StrEnum):
    FREEFORM = "freeform"
    CHOICE = "choice"
    CONFIRM = "confirm"


NON_QUESTION_ACTIONS = frozenset(
    {
        NextAction.DERIVE,
        NextAction.RESEARCH,
        NextAction.DEFAULT,
        NextAction.DEFER,
        NextAction.NOT_APPLICABLE,
        NextAction.CONFLICT_RESOLUTION,
        NextAction.FINALIZE,
    }
)

QUESTION_ACTIONS = frozenset({NextAction.ASK, NextAction.CONFIRM})


@dataclass(frozen=True)
class Readiness:
    score: float
    blocking_count: int
    high_value_unknown_count: int
    ready_to_finalize: bool
    reason: str


@dataclass(frozen=True)
class NextQuestion:
    question_id: str
    text: str
    decision_target: str
    why_it_matters: str
    evidence_used: tuple[str, ...]
    alternatives_considered: tuple[str, ...]
    recommended_default: str | None
    risk_if_wrong: str
    answer_mode: str
    domain: str | None = None


@dataclass(frozen=True)
class AnalysisOutput:
    analysis_revision: int
    evidence_revision: int
    state_digest: str
    facts: tuple[dict[str, Any], ...]
    inferences: tuple[dict[str, Any], ...]
    assumptions: tuple[dict[str, Any], ...]
    contradictions: tuple[dict[str, Any], ...]
    resolved_without_user: tuple[dict[str, Any], ...]
    unresolved: tuple[dict[str, Any], ...]
    readiness: Readiness
    next_action: str
    next_question: NextQuestion | None


class SchemaValidationError(ValueError):
    """Raised when provider output fails structural schema validation."""


class PolicyValidationError(ValueError):
    """Raised when provider output violates interrogation policy."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__("; ".join(violations))


def _require_str(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_list(value: Any, *, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise SchemaValidationError(f"{field_name} must be a list")
    return value


def _parse_readiness(raw: Any) -> Readiness:
    if not isinstance(raw, dict):
        raise SchemaValidationError("readiness must be an object")
    try:
        score = float(raw.get("score", 0.0))
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError("readiness.score must be numeric") from exc
    try:
        blocking_count = int(raw.get("blocking_count", 0))
        high_value_unknown_count = int(raw.get("high_value_unknown_count", 0))
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError("readiness counts must be integers") from exc
    ready = bool(raw.get("ready_to_finalize", False))
    reason = str(raw.get("reason", "")).strip()
    return Readiness(
        score=score,
        blocking_count=blocking_count,
        high_value_unknown_count=high_value_unknown_count,
        ready_to_finalize=ready,
        reason=reason,
    )


def _parse_next_question(raw: Any) -> NextQuestion | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise SchemaValidationError("next_question must be an object or null")
    evidence_used = _require_list(raw.get("evidence_used", []), field_name="next_question.evidence_used")
    alternatives = _require_list(
        raw.get("alternatives_considered", []),
        field_name="next_question.alternatives_considered",
    )
    return NextQuestion(
        question_id=_require_str(raw.get("question_id", ""), field_name="next_question.question_id"),
        text=_require_str(raw.get("text", ""), field_name="next_question.text"),
        decision_target=_require_str(raw.get("decision_target", ""), field_name="next_question.decision_target"),
        why_it_matters=str(raw.get("why_it_matters", "")).strip(),
        evidence_used=tuple(str(item).strip() for item in evidence_used if str(item).strip()),
        alternatives_considered=tuple(str(item).strip() for item in alternatives if str(item).strip()),
        recommended_default=(
            str(raw.get("recommended_default")).strip() if raw.get("recommended_default") not in (None, "") else None
        ),
        risk_if_wrong=str(raw.get("risk_if_wrong", RiskLevel.LOW)).strip().lower() or RiskLevel.LOW,
        answer_mode=str(raw.get("answer_mode", AnswerMode.FREEFORM)).strip().lower() or AnswerMode.FREEFORM,
        domain=str(raw.get("domain", "")).strip() or None,
    )


def _parse_record_list(raw: Any, *, field_name: str) -> tuple[dict[str, Any], ...]:
    items = _require_list(raw, field_name=field_name)
    parsed: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise SchemaValidationError(f"{field_name}[{idx}] must be an object")
        parsed.append(dict(item))
    return tuple(parsed)


def parse_analysis_output(raw: dict[str, Any]) -> AnalysisOutput:
    """Parse and structurally validate provider output."""
    if not isinstance(raw, dict):
        raise SchemaValidationError("analysis output must be an object")
    allowed_keys = {
        "analysis_revision",
        "evidence_revision",
        "state_digest",
        "facts",
        "inferences",
        "assumptions",
        "contradictions",
        "resolved_without_user",
        "unresolved",
        "readiness",
        "next_action",
        "next_question",
    }
    extra = set(raw.keys()) - allowed_keys
    if extra:
        raise SchemaValidationError(f"extra keys not allowed in analysis output: {', '.join(sorted(extra))}")
    try:
        analysis_revision = int(raw.get("analysis_revision", 0))
        evidence_revision = int(raw.get("evidence_revision", 0))
    except (TypeError, ValueError) as exc:
        raise SchemaValidationError("analysis_revision and evidence_revision must be integers") from exc
    next_action = _require_str(raw.get("next_action", ""), field_name="next_action").upper()
    if next_action not in {action.value for action in NextAction}:
        raise SchemaValidationError(f"unsupported next_action: {next_action}")
    next_question = _parse_next_question(raw.get("next_question"))
    if next_action in NON_QUESTION_ACTIONS and next_question is not None:
        raise SchemaValidationError("next_question must be null for non-question actions")
    if next_action in QUESTION_ACTIONS and next_question is None:
        raise SchemaValidationError("next_question is required for ASK and CONFIRM actions")
    return AnalysisOutput(
        analysis_revision=analysis_revision,
        evidence_revision=evidence_revision,
        state_digest=_require_str(raw.get("state_digest", ""), field_name="state_digest"),
        facts=_parse_record_list(raw.get("facts", []), field_name="facts"),
        inferences=_parse_record_list(raw.get("inferences", []), field_name="inferences"),
        assumptions=_parse_record_list(raw.get("assumptions", []), field_name="assumptions"),
        contradictions=_parse_record_list(raw.get("contradictions", []), field_name="contradictions"),
        resolved_without_user=_parse_record_list(
            raw.get("resolved_without_user", []),
            field_name="resolved_without_user",
        ),
        unresolved=_parse_record_list(raw.get("unresolved", []), field_name="unresolved"),
        readiness=_parse_readiness(raw.get("readiness", {})),
        next_action=next_action,
        next_question=next_question,
    )


def _count_questions(text: str) -> int:
    parts = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text.strip()) if segment.strip()]
    if not parts:
        return 0
    return sum(1 for part in parts if _QUESTION_MARKERS.search(part))


def _answered_targets(snapshot: dict[str, Any]) -> set[str]:
    targets: set[str] = set()
    for entry in snapshot.get("active_answers", []):
        if not isinstance(entry, dict):
            continue
        value = str(entry.get("decision_target", "")).strip().lower()
        if value:
            targets.add(value)
        answer = str(entry.get("answer", "")).strip().lower()
        if answer:
            targets.add(f"answer:{answer[:120]}")
    for decision in snapshot.get("decisions", []):
        if not isinstance(decision, dict):
            continue
        target = str(decision.get("decision_target", decision.get("id", ""))).strip().lower()
        if target:
            targets.add(target)
    return targets


def _known_evidence_text(snapshot: dict[str, Any]) -> set[str]:
    corpus: set[str] = set()
    for key in (
        "original_intent",
        "active_answers",
        "confirmed_requirements",
        "inferred_requirements",
        "assumptions",
        "decisions",
        "project_evidence",
        "document_evidence",
        "research_evidence",
        "environment_evidence",
    ):
        value = snapshot.get(key)
        if isinstance(value, str) and value.strip():
            corpus.add(value.strip().lower())
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    fields = ("answer",) if key == "active_answers" else ("text", "answer", "summary", "content")
                    for field_name in fields:
                        text = str(item.get(field_name, "")).strip().lower()
                        if text:
                            corpus.add(text)
                elif isinstance(item, str) and item.strip():
                    corpus.add(item.strip().lower())
    return corpus


def validate_analysis_policy(output: AnalysisOutput, snapshot: dict[str, Any]) -> list[str]:
    """Reject policy-violating provider output before mutating session state."""
    violations: list[str] = []
    answered = _answered_targets(snapshot)
    known = _known_evidence_text(snapshot)

    if output.next_action in QUESTION_ACTIONS:
        question = output.next_question
        if question is None:
            violations.append("ASK/CONFIRM requires next_question")
            return violations
        if _count_questions(question.text) > 1:
            violations.append("question text must ask exactly one decision at a time")
        target = question.decision_target.strip().lower()
        if target in answered:
            violations.append(f"decision_target already answered: {question.decision_target}")
        if not question.evidence_used:
            violations.append("ASK/CONFIRM questions must cite evidence_used")
        normalized_question = question.text.strip().lower()
        if normalized_question in known:
            violations.append("question text duplicates known evidence")

    if output.next_action == NextAction.DEFAULT:
        unsafe = [
            item
            for item in output.resolved_without_user
            if isinstance(item, dict)
            and str(item.get("method", "")).upper() == NextAction.DEFAULT
            and str(item.get("risk_if_wrong", RiskLevel.LOW)).lower() in {RiskLevel.HIGH, RiskLevel.MEDIUM}
            and not item.get("reversible", True)
        ]
        if unsafe:
            violations.append("unsafe irreversible DEFAULT resolution for high-impact uncertainty")

    if output.next_action == NextAction.FINALIZE and not output.readiness.ready_to_finalize:
        violations.append("FINALIZE requires readiness.ready_to_finalize")

    if output.next_action == NextAction.CONFLICT_RESOLUTION:
        unresolved_snap = [
            item for item in snapshot.get("contradictions", []) if isinstance(item, dict) and not item.get("resolved")
        ]
        unresolved_out = [item for item in output.contradictions if isinstance(item, dict) and not item.get("resolved")]
        if not unresolved_snap and not unresolved_out:
            violations.append("CONFLICT_RESOLUTION requires unresolved contradictions in evidence")

    return violations


def enforce_analysis_policy(output: AnalysisOutput, snapshot: dict[str, Any]) -> AnalysisOutput:
    violations = validate_analysis_policy(output, snapshot)
    if violations:
        raise PolicyValidationError(violations)
    return output


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, StrEnum):
        return value.value
    return value


def analysis_output_to_dict(output: AnalysisOutput) -> dict[str, Any]:
    return _to_jsonable(output)


@dataclass(frozen=True)
class AnalysisReceipt:
    input_digest: str
    output_digest: str
    provider_id: str
    model_id: str
    policy_version: str
    timestamp: str
    analysis_revision: int
    evidence_revision: int
    next_action: str
    rationale: str = field(default="")


def receipt_to_dict(receipt: AnalysisReceipt) -> dict[str, Any]:
    return asdict(receipt)


@dataclass
class ValidationResult:
    ok: bool
    passed: bool
    error: str | None = None


def validate_analysis_output(raw: dict[str, Any]) -> ValidationResult:
    try:
        output = parse_analysis_output(raw)
        violations = validate_analysis_policy(output, {})
        if violations:
            return ValidationResult(ok=False, passed=False, error="; ".join(violations))
        return ValidationResult(ok=True, passed=True)
    except Exception as exc:
        return ValidationResult(ok=False, passed=False, error=str(exc))


def validate_question_against_evidence(
    question: dict[str, Any] | NextQuestion,
    snapshot: dict[str, Any],
    known_intent: str | None = None,
) -> ValidationResult:
    if isinstance(question, dict):
        try:
            q_obj = _parse_next_question(question)
            if q_obj is None:
                return ValidationResult(ok=False, passed=False, error="Invalid question format")
        except Exception as exc:
            return ValidationResult(ok=False, passed=False, error=str(exc))
    else:
        q_obj = question

    violations: list[str] = []
    answered = _answered_targets(snapshot)
    known = _known_evidence_text(snapshot)
    if known_intent:
        known.add(known_intent.strip().lower())

    target = q_obj.decision_target.strip().lower()
    if target in answered:
        violations.append(f"decision_target already answered: {q_obj.decision_target}")

    text = q_obj.text.strip().lower()
    if text in known:
        violations.append("question text duplicates known evidence")

    # DoD-4: questions must not demand facts already present in evidence
    asks_known_scope = "what product" in text or "what application" in text or "what do you want to build" in text
    if known_intent and target == "product_scope" and asks_known_scope:
        violations.append("Question demands product scope which is already defined in known intent")

    if violations:
        return ValidationResult(ok=False, passed=False, error="; ".join(violations))
    return ValidationResult(ok=True, passed=True)
