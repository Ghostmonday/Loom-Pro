"""Python 3.10-compatible reasoning schema enum behavior tests."""

from __future__ import annotations

from aoc_supervisor.reasoning_schema import (
    AnalysisOutput,
    AnswerMode,
    NextAction,
    NextQuestion,
    Readiness,
    RiskLevel,
    analysis_output_to_dict,
    parse_analysis_output,
    validate_analysis_output,
)


def _valid_ask_payload() -> dict[str, object]:
    return {
        "analysis_revision": 1,
        "evidence_revision": 1,
        "state_digest": "sha256:abc",
        "facts": [],
        "inferences": [],
        "assumptions": [],
        "contradictions": [],
        "resolved_without_user": [],
        "unresolved": [],
        "readiness": {
            "score": 0.25,
            "blocking_count": 1,
            "high_value_unknown_count": 1,
            "ready_to_finalize": False,
            "reason": "needs one answer",
        },
        "next_action": "ASK",
        "next_question": {
            "question_id": "q_runtime",
            "text": "Which runtime should be supported?",
            "decision_target": "runtime",
            "why_it_matters": "CI matrix compatibility depends on this.",
            "evidence_used": ["pyproject requires >=3.10"],
            "alternatives_considered": ["drop 3.10", "keep 3.10"],
            "recommended_default": "keep 3.10",
            "risk_if_wrong": "medium",
            "answer_mode": "choice",
            "domain": "ci",
        },
    }


def test_reasoning_enums_are_string_values_for_serialization() -> None:
    output = AnalysisOutput(
        analysis_revision=1,
        evidence_revision=1,
        state_digest="sha256:abc",
        facts=({"next_action": NextAction.ASK},),
        inferences=(),
        assumptions=(),
        contradictions=(),
        resolved_without_user=(),
        unresolved=(),
        readiness=Readiness(
            score=0.25,
            blocking_count=1,
            high_value_unknown_count=1,
            ready_to_finalize=False,
            reason="needs one answer",
        ),
        next_action=NextAction.ASK,
        next_question=NextQuestion(
            question_id="q_runtime",
            text="Which runtime should be supported?",
            decision_target="runtime",
            why_it_matters="CI matrix compatibility depends on this.",
            evidence_used=("pyproject requires >=3.10",),
            alternatives_considered=("drop 3.10", "keep 3.10"),
            recommended_default="keep 3.10",
            risk_if_wrong=RiskLevel.MEDIUM,
            answer_mode=AnswerMode.CHOICE,
            domain="ci",
        ),
    )

    encoded = analysis_output_to_dict(output)

    assert encoded["next_action"] == "ASK"
    assert encoded["facts"] == [{"next_action": "ASK"}]
    assert encoded["next_question"]["risk_if_wrong"] == "medium"
    assert encoded["next_question"]["answer_mode"] == "choice"


def test_reasoning_enums_keep_string_equality_behavior() -> None:
    assert NextAction.ASK == "ASK"
    assert RiskLevel.LOW == "low"
    assert AnswerMode.FREEFORM == "freeform"
    assert str(NextAction.CONFIRM) == "CONFIRM"
    assert {NextAction.ASK, NextAction.CONFIRM} == {"ASK", "CONFIRM"}


def test_reasoning_schema_validation_accepts_string_enum_values() -> None:
    payload = _valid_ask_payload()

    parsed = parse_analysis_output(payload)
    result = validate_analysis_output(payload)

    assert parsed.next_action == NextAction.ASK
    assert parsed.next_question is not None
    assert parsed.next_question.risk_if_wrong == RiskLevel.MEDIUM
    assert parsed.next_question.answer_mode == AnswerMode.CHOICE
    assert result.ok
    assert result.passed
