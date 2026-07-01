from unittest.mock import MagicMock, patch

import pytest
from aoc_supervisor.adaptive_question_engine import EngineResult
from aoc_supervisor.intent_blueprint_state import new_blueprint_state, new_question_id
from aoc_supervisor.intent_forge_service import IntentForgeService
from aoc_supervisor.reasoning_schema import AnalysisOutput, Readiness


@pytest.fixture
def service(tmp_path):
    return IntentForgeService(tmp_path)


@pytest.fixture
def initial_state():
    return new_blueprint_state(session_id="session-123", user_id="user-456", tier="paid", original_prompt="Test prompt")


def mock_output(facts=None, inferences=None, assumptions=None):
    return AnalysisOutput(
        analysis_revision=1,
        evidence_revision=1,
        state_digest="digest",
        facts=tuple(facts or []),
        inferences=tuple(inferences or []),
        assumptions=tuple(assumptions or []),
        contradictions=(),
        resolved_without_user=(),
        unresolved=(),
        readiness=Readiness(
            score=0.5, blocking_count=0, high_value_unknown_count=0, ready_to_finalize=False, reason=""
        ),
        next_action="ASK",
        next_question=None,
    )


def test_apply_answer_normal_analysis(service, initial_state):
    question_id = new_question_id()
    initial_state["current_question"] = {"text": "What is your name?", "question_id": question_id}

    output = mock_output(
        facts=[{"text": "Name is Alice", "confidence": 0.9, "domain": "identity"}],
        inferences=[{"text": "Likely a human", "confidence": 0.8}],
        assumptions=[{"text": "Speaks English", "confidence": 0.7}],
    )

    result = MagicMock(spec=EngineResult)
    result.output = output

    with patch("aoc_supervisor.adaptive_question_engine.AdaptiveQuestionEngine.analyze", return_value=result):
        service._apply_answer_to_state(
            initial_state, question_id=question_id, answer="My name is Alice", domain="identity"
        )

    # Check Q&A recording
    assert len(initial_state["questions_and_answers"]) == 1
    assert initial_state["questions_and_answers"][0]["answer"] == "My name is Alice"

    # Check claims merging
    reqs = initial_state["confirmed_requirements"]
    assert len(reqs) == 3
    texts = [r["text"] for r in reqs]
    assert "Name is Alice" in texts
    assert "Likely a human" in texts
    assert "Speaks English" in texts
    for r in reqs:
        assert r["source_question_id"] == question_id
        assert "id" in r

    # Check domain coverage
    assert initial_state["domain_coverage"]["identity"]["addressed"] is True
    assert initial_state["confidence_by_domain"]["identity"] > 0

    # Check graph
    nodes = initial_state["blueprint_graph"]["nodes"]
    assert len(nodes) == 1
    assert nodes[0]["label"] == "My name is Alice"

    # Check current_question cleared
    assert initial_state["current_question"] is None


def test_apply_answer_marks_old_reqs_stale(service, initial_state):
    question_id = "q-old"
    initial_state["confirmed_requirements"].append(
        {"id": "REQ-OLD", "text": "Old requirement", "source_question_id": question_id, "stale": False}
    )

    output = mock_output()
    result = MagicMock(spec=EngineResult)
    result.output = output

    with patch("aoc_supervisor.adaptive_question_engine.AdaptiveQuestionEngine.analyze", return_value=result):
        service._apply_answer_to_state(initial_state, question_id=question_id, answer="New answer", domain="identity")

    # Old requirement should be stale
    assert initial_state["confirmed_requirements"][0]["stale"] is True
    # New requirement should be added (fallback because output was empty)
    assert len(initial_state["confirmed_requirements"]) == 2
    assert initial_state["confirmed_requirements"][1]["text"] == "New answer"


def test_apply_answer_fallback_on_failure(service, initial_state):
    question_id = new_question_id()

    from aoc_supervisor.reasoning_provider import ProviderFailureError

    with patch(
        "aoc_supervisor.adaptive_question_engine.AdaptiveQuestionEngine.analyze",
        side_effect=ProviderFailureError(code="test", message="test"),
    ):
        service._apply_answer_to_state(
            initial_state, question_id=question_id, answer="Fallback answer", domain="identity"
        )

    # Should fallback to raw answer
    reqs = initial_state["confirmed_requirements"]
    assert len(reqs) == 1
    assert reqs[0]["text"] == "Fallback answer"
    assert reqs[0]["confidence"] == 1.0


def test_apply_answer_conflict_resolution(service, initial_state):
    question_id = new_question_id()
    eid_a = "REQ-A"
    eid_b = "DEC-B"
    initial_state["confirmed_requirements"].append({"id": eid_a, "text": "A", "stale": False})
    initial_state["decisions"].append({"id": eid_b, "text": "B", "superseded": False})
    initial_state["contradictions"].append({"element_a_id": eid_a, "element_b_id": eid_b, "resolved": False})
    initial_state["blueprint_graph"]["nodes"].append({"id": eid_a, "label": "A", "stale": False})

    output = mock_output()
    result = MagicMock(spec=EngineResult)
    result.output = output

    with patch("aoc_supervisor.adaptive_question_engine.AdaptiveQuestionEngine.analyze", return_value=result):
        service._apply_answer_to_state(
            initial_state, question_id=question_id, answer="Resolved!", domain="identity", conflict_resolution=True
        )

    assert initial_state["contradictions"][0]["resolved"] is True
    assert initial_state["contradictions"][0]["resolution_text"] == "Resolved!"
    assert initial_state["confirmed_requirements"][0]["stale"] is True
    assert initial_state["decisions"][0]["superseded"] is True
    assert initial_state["blueprint_graph"]["nodes"][0]["stale"] is True


def test_apply_answer_acceptance_decision(service, initial_state):
    question_id = new_question_id()

    output = mock_output()
    result = MagicMock(spec=EngineResult)
    result.output = output

    with patch("aoc_supervisor.adaptive_question_engine.AdaptiveQuestionEngine.analyze", return_value=result):
        service._apply_answer_to_state(
            initial_state,
            question_id=question_id,
            answer="This is a validation window requirement",
            domain="testing_acceptance",
        )

    assert len(initial_state["decisions"]) == 1
    assert initial_state["decisions"][0]["rationale"] == "acceptance_policy"
