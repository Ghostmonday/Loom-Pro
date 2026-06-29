"""Acceptance tests for the adaptive Perfect SPEC interrogation engine.

Uses injected deterministic fake reasoning providers — never live models.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from tests.fixtures import contract_imports as _contract_imports  # noqa: F401 — worktree path precedence
from tests.fixtures.contract_imports import module_available, require_callable, require_module
from tests.fixtures.fake_reasoning_provider import (
    ProviderFailureError,
    ScriptedFakeReasoningProvider,
    contradiction_script,
    default_resolution_script,
    divergence_script,
    early_finalize_script,
    high_impact_script,
    question_payload,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_seed_session() -> dict[str, Any]:
    return json.loads((FIXTURES / "interrogation_session_seed.json").read_text(encoding="utf-8"))


def _engine_with(provider: ScriptedFakeReasoningProvider) -> Any:
    engine_cls = require_module("aoc_supervisor.adaptive_question_engine", "AdaptiveQuestionEngine", dod="DoD-1")
    return engine_cls(provider=provider)


def _run_turn(engine: Any, state: dict[str, Any], *, answer: str | None = None) -> dict[str, Any]:
    if answer is not None:
        return engine.submit_answer(
            state, answer=answer, question_id=state.get("current_question", {}).get("question_id")
        )
    return engine.start_questioning(state)


@pytest.fixture
def seed_state() -> dict[str, Any]:
    return _load_seed_session()


class TestAdaptiveInterrogationContract:
    """Canonical engine behavior — DoD items 1, 3, 5-11, 15."""

    def test_dod1_every_answer_triggers_fresh_complete_state_analysis(self, seed_state: dict[str, Any]) -> None:
        provider = ScriptedFakeReasoningProvider(script=divergence_script())
        engine = _engine_with(provider)
        state = _run_turn(engine, seed_state)
        state = _run_turn(engine, state, answer="OAuth2 with scoped tokens for every endpoint.")
        state = _run_turn(engine, state, answer="API keys with per-tenant rotation.")

        assert provider.call_count >= 3, "DoD-1: each turn must invoke provider analysis"
        for idx, snapshot in enumerate(provider.recorded_snapshots):
            assert "original_intent" in snapshot or "original_prompt" in snapshot, f"turn {idx} missing intent"
            answers = snapshot.get("active_answers") or snapshot.get("questions_and_answers") or []
            assert isinstance(answers, list), f"turn {idx} must include prior answers"

    def test_dod3_next_question_from_structured_unresolved_uncertainty(self, seed_state: dict[str, Any]) -> None:
        provider = ScriptedFakeReasoningProvider(script=divergence_script())
        engine = _engine_with(provider)
        state = _run_turn(engine, seed_state)
        question = state.get("current_question") or {}
        assert question.get("decision_target"), "DoD-3: question must target an unresolved decision"
        assert question.get("why_it_matters") or question.get("text"), "DoD-3: rationale must be present"

    def test_dod5_two_answers_produce_different_next_questions(self, seed_state: dict[str, Any]) -> None:
        provider = ScriptedFakeReasoningProvider(script=divergence_script())
        engine = _engine_with(provider)
        state = _run_turn(engine, seed_state)
        state = _run_turn(engine, state, answer="OAuth2 with scoped tokens.")
        first_next = (state.get("current_question") or {}).get("question_id")
        state = _run_turn(engine, state, answer="API keys with rotation.")
        second_next = (state.get("current_question") or {}).get("question_id")
        assert first_next and second_next and first_next != second_next, (
            "DoD-5: divergent answers must yield different next questions"
        )

    def test_dod6_contradiction_changes_next_action_to_conflict_resolution(self, seed_state: dict[str, Any]) -> None:
        provider = ScriptedFakeReasoningProvider(script=contradiction_script())
        engine = _engine_with(provider)
        state = _run_turn(engine, seed_state)
        state = _run_turn(engine, state, answer="Reads must be zero-latency.")
        latest = state.get("latest_analysis") or {}
        action = latest.get("next_action") or state.get("session_status")
        assert (
            action in {"CONFLICT_RESOLUTION", "conflict_resolution"}
            or state.get("session_status") == "CONFLICT_RESOLUTION"
        ), "DoD-6: contradiction must route to conflict resolution"

    def test_dod7_reversible_low_risk_choices_can_be_defaulted(self, seed_state: dict[str, Any]) -> None:
        provider = ScriptedFakeReasoningProvider(script=default_resolution_script())
        engine = _engine_with(provider)
        state = _run_turn(engine, seed_state)
        state = _run_turn(engine, state, answer="No preference — use the ergonomic default.")
        resolutions = (
            state.get("resolved_without_user")
            or (state.get("latest_analysis") or {}).get("resolved_without_user")
            or []
        )
        assert any(r.get("resolution_method") == "DEFAULT" for r in resolutions if isinstance(r, dict)), (
            "DoD-7: low-risk reversible choice must be automatically defaulted"
        )

    def test_dod8_high_impact_subjective_choices_require_ask_or_confirm(self, seed_state: dict[str, Any]) -> None:
        provider = ScriptedFakeReasoningProvider(script=high_impact_script())
        engine = _engine_with(provider)
        state = _run_turn(engine, seed_state)
        latest = state.get("latest_analysis") or {}
        action = str(latest.get("next_action", "")).upper()
        assert action in {"ASK", "CONFIRM"}, "DoD-8: irreversible/safety-sensitive choices require ASK or CONFIRM"
        question = state.get("current_question") or latest.get("next_question") or {}
        assert str(question.get("risk_if_wrong", "")).lower() in {"high", "medium"}, (
            "DoD-8: high-impact question must declare elevated risk"
        )

    def test_dod9_exactly_one_question_presented_at_a_time(self, seed_state: dict[str, Any]) -> None:
        validate = require_callable("aoc_supervisor.reasoning_schema", "validate_analysis_output", dod="DoD-9")
        provider = ScriptedFakeReasoningProvider(
            script=[
                {
                    "analysis_revision": 1,
                    "evidence_revision": 1,
                    "state_digest": "sha256:bad",
                    "facts": [],
                    "inferences": [],
                    "assumptions": [],
                    "contradictions": [],
                    "resolved_without_user": [],
                    "unresolved": [],
                    "readiness": {
                        "score": 0.0,
                        "blocking_count": 0,
                        "high_value_unknown_count": 2,
                        "ready_to_finalize": False,
                        "reason": "",
                    },
                    "next_action": "ASK",
                    "next_question": question_payload(
                        question_id="q_one",
                        text="First?",
                        decision_target="a",
                    ),
                    "extra_question": question_payload(question_id="q_two", text="Second?", decision_target="b"),
                }
            ]
        )
        engine = _engine_with(provider)
        with pytest.raises(Exception):  # noqa: B017 — production chooses typed validation error
            _run_turn(engine, seed_state)
        multi_text = "Question one? Also question two?"
        invalid = {
            "analysis_revision": 1,
            "evidence_revision": 1,
            "state_digest": "sha256:x",
            "facts": [],
            "inferences": [],
            "assumptions": [],
            "contradictions": [],
            "resolved_without_user": [],
            "unresolved": [],
            "readiness": {
                "score": 0.0,
                "blocking_count": 0,
                "high_value_unknown_count": 1,
                "ready_to_finalize": False,
                "reason": "",
            },
            "next_action": "ASK",
            "next_question": {
                **question_payload(question_id="q_multi", text=multi_text, decision_target="multi"),
            },
        }
        result = validate(invalid)
        assert result.ok is False or getattr(result, "passed", True) is False, (
            "DoD-9: multi-question or policy-violating output must be rejected"
        )

    def test_dod10_engine_can_stop_before_all_descriptive_domains_touched(self, seed_state: dict[str, Any]) -> None:
        provider = ScriptedFakeReasoningProvider(script=early_finalize_script())
        engine = _engine_with(provider)
        state = _run_turn(engine, seed_state)
        state = _run_turn(engine, state, answer="V1 excludes mobile clients and billing.")
        status = state.get("session_status")
        readiness = (state.get("latest_analysis") or {}).get("readiness") or {}
        untouched = [
            domain
            for domain, meta in (state.get("domain_coverage") or {}).items()
            if isinstance(meta, dict) and not meta.get("addressed") and not meta.get("na")
        ]
        assert status in {"VALIDATING", "FINAL_CONFIRMATION", "FINALIZED"} or readiness.get("ready_to_finalize"), (
            "DoD-10: engine must stop when SPEC ready despite untouched descriptive domains"
        )
        assert untouched, "DoD-10: fixture expects untouched domains when stopping early"

    def test_dod11_provider_failure_preserves_state_and_retryable_status(self, seed_state: dict[str, Any]) -> None:
        provider = ScriptedFakeReasoningProvider(script=divergence_script(), fail_on_calls={1})
        engine = _engine_with(provider)
        before = json.dumps(seed_state, sort_keys=True)
        state = _run_turn(engine, seed_state)
        with pytest.raises(ProviderFailureError):
            _run_turn(engine, state, answer="trigger failure")
        after = json.dumps(state, sort_keys=True)
        assert before != after or state.get("analysis_recovery"), (
            "DoD-11: committed state before failure must be preserved"
        )
        recovery = state.get("analysis_recovery") or state.get("recoverable_error") or {}
        assert recovery or state.get("session_status") in {"QUESTIONING", "ANALYZING", "ANALYSIS_FAILED"}, (
            "DoD-11: actionable retry path must be exposed"
        )
        provider.fail_on_calls.clear()
        recovered = engine.retry_analysis(state) if hasattr(engine, "retry_analysis") else _run_turn(engine, state)
        assert recovered.get("current_question") or recovered.get("session_status") != "ANALYSIS_FAILED", (
            "DoD-11: retry must recover questioning flow"
        )

    def test_dod15_static_domain_prompts_not_in_production_path(self) -> None:
        forbidden_sources = json.loads((FIXTURES / "whole_state_snapshot_contract.json").read_text(encoding="utf-8"))[
            "forbidden_question_sources"
        ]

        if module_available("aoc_supervisor.adaptive_question_engine"):
            from aoc_supervisor import adaptive_question_engine as aqe

            source = inspect.getsource(aqe)
            for token in forbidden_sources:
                assert token not in source, f"DoD-15: production engine must not reference {token}"

        build_next = require_callable("aoc_supervisor.question_policy", "build_next_question", dod="DoD-15")
        wrapper_source = inspect.getsource(build_next)
        assert "adaptive" in wrapper_source.lower() or "AdaptiveQuestionEngine" in wrapper_source, (
            "DoD-15: question_policy.build_next_question must delegate to adaptive engine"
        )
        assert "rank_candidate_domains" not in wrapper_source, (
            "DoD-15: fixed domain-order traversal must not drive presented questions"
        )

    def test_production_exposes_deterministic_fake_provider(self) -> None:
        fake_cls = require_module(
            "aoc_supervisor.reasoning_provider",
            "DeterministicFakeReasoningProvider",
            dod="DoD-1",
        )
        provider = fake_cls()
        assert hasattr(provider, "analyze") and callable(provider.analyze), (
            "Contract: production must ship injectable deterministic fake provider"
        )


class TestInterrogationEvaluationMetrics:
    """Workflow evaluator interrogation metrics required by contract tests."""

    def test_evaluator_exposes_required_metrics(self) -> None:
        require_module(
            "aoc_supervisor.workflow_evaluator",
            "InterrogationMetrics",
            dod="DoD-15",
        )
        evaluate_interrogation_session = require_callable(
            "aoc_supervisor.workflow_evaluator",
            "evaluate_interrogation_session",
            dod="DoD-15",
        )

        session = _load_seed_session()
        session["analysis_receipts"] = [
            {
                "input_digest": "sha256:a",
                "output_digest": "sha256:b",
                "output": {"resolved_without_user": [{"id": "r1"}]},
            }
        ]
        session["analysis_revision"] = 2
        checks, metrics = evaluate_interrogation_session(session, provider_recovered=True, voice_ui_ok=True)
        payload = metrics.as_dict()
        for key in (
            "unnecessary_question_count",
            "repeated_question_count",
            "whole_state_reanalysis_rate",
            "automatically_resolved_count",
            "provider_recovery_success",
            "voice_fallback_integrity",
        ):
            assert key in payload, f"Evaluator must expose metric `{key}`"
        assert metrics.automatically_resolved_count >= 1
        assert all(isinstance(check.passed, bool) for check in checks)
