"""Whole-state evidence and analysis snapshot contract tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from tests.fixtures import contract_imports as _contract_imports  # noqa: F401 — worktree path precedence
from tests.fixtures.contract_imports import require_callable, require_module
from tests.fixtures.fake_reasoning_provider import ScriptedFakeReasoningProvider, divergence_script, snapshot_digest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_seed_session() -> dict[str, Any]:
    return json.loads((FIXTURES / "interrogation_session_seed.json").read_text(encoding="utf-8"))


def _snapshot_builder():
    return require_callable("aoc_supervisor.evidence_state", "build_analysis_snapshot", dod="DoD-2")


def _engine(provider: ScriptedFakeReasoningProvider) -> Any:
    engine_cls = require_module("aoc_supervisor.adaptive_question_engine", "AdaptiveQuestionEngine", dod="DoD-1")
    return engine_cls(provider=provider)


class TestWholeStateEvidenceContract:
    """DoD items 2, 4, plus revision/supersede audit requirements."""

    def test_dod2_analysis_input_includes_prior_answers_and_evidence(self) -> None:
        build_snapshot = _snapshot_builder()
        state = _load_seed_session()
        state["questions_and_answers"].append(
            {
                "question_id": "q_prior",
                "text": "How should rate limits behave?",
                "answer": "1000 requests/minute per API key.",
                "domain": "functional_requirements",
            }
        )
        snapshot = build_snapshot(state)
        contract = json.loads((FIXTURES / "whole_state_snapshot_contract.json").read_text(encoding="utf-8"))
        for key in contract["required_top_level_keys"]:
            assert key in snapshot, f"DoD-2: snapshot missing required key `{key}`"

        active = snapshot.get("active_answers") or []
        assert any("rate limits" in str(a.get("answer", "")).lower() for a in active if isinstance(a, dict)), (
            "DoD-2: prior answers must be present in analysis input"
        )
        evidence = snapshot.get("project_evidence") or []
        assert evidence, "DoD-2: authorized evidence sources must be included"

    def test_dod2_snapshot_digest_is_stable_for_identical_state(self) -> None:
        build_snapshot = _snapshot_builder()
        state = _load_seed_session()
        first = build_snapshot(state)
        second = build_snapshot(copy.deepcopy(state))
        digest_a = first.get("digest") or snapshot_digest(first)
        digest_b = second.get("digest") or snapshot_digest(second)
        assert digest_a == digest_b, "DoD-2: identical complete state must produce identical digest"

    def test_dod4_known_facts_are_not_re_asked(self) -> None:
        validate_question = require_callable(
            "aoc_supervisor.reasoning_schema",
            "validate_question_against_evidence",
            dod="DoD-4",
        )
        state = _load_seed_session()
        known = state["original_prompt"]
        candidate = {
            "question_id": "q_bad",
            "text": "What product do you want to build?",
            "decision_target": "product_scope",
            "why_it_matters": "Scope",
            "evidence_used": [],
            "alternatives_considered": [],
            "recommended_default": None,
            "risk_if_wrong": "low",
            "answer_mode": "freeform",
        }
        snapshot = _snapshot_builder()(state)
        result = validate_question(candidate, snapshot=snapshot, known_intent=known)
        assert result.ok is False or getattr(result, "passed", True) is False, (
            "DoD-4: questions must not demand facts already present in evidence"
        )

    def test_provider_receives_complete_state_on_every_turn(self) -> None:
        provider = ScriptedFakeReasoningProvider(script=divergence_script())
        engine = _engine(provider)
        state = _load_seed_session()
        engine.start_questioning(state)
        engine.submit_answer(
            state,
            answer="OAuth2 with scoped tokens.",
            question_id=state.get("current_question", {}).get("question_id"),
        )

        assert len(provider.recorded_snapshots) >= 2
        later = provider.recorded_snapshots[-1]
        answers = later.get("active_answers") or later.get("questions_and_answers") or []
        assert len(answers) >= 2, "Every turn must send complete prior answer history"
        assert later.get("project_evidence") or later.get("original_intent") or later.get("original_prompt"), (
            "Every turn must send evidence and original intent"
        )

    def test_revision_invalidates_dependent_analysis_and_triggers_reanalysis(self) -> None:
        provider = ScriptedFakeReasoningProvider(script=divergence_script())
        engine = _engine(provider)
        state = _load_seed_session()
        state = engine.start_questioning(state)
        state = engine.submit_answer(
            state,
            answer="V1 covers task creation only.",
            question_id=state.get("current_question", {}).get("question_id"),
        )
        receipts_before = len(state.get("analysis_receipts") or [])
        revision = engine.revise_answer(
            state,
            question_id=(state.get("questions_and_answers") or [{}])[0].get("question_id", "q_intake"),
            answer="V1 covers task creation and weekly reporting.",
        )
        receipts_after = len(revision.get("analysis_receipts") or [])
        stale = [r for r in revision.get("confirmed_requirements", []) if r.get("stale")]
        assert receipts_after > receipts_before or provider.call_count >= 3, (
            "Revision must trigger complete reanalysis with new receipt"
        )
        assert stale, "Revision must invalidate dependent extracted facts"

    def test_superseded_answers_remain_auditable_but_not_current_truth(self) -> None:
        build_snapshot = _snapshot_builder()
        state = _load_seed_session()
        original = {
            "question_id": "q_scope",
            "text": "What is in scope?",
            "answer": "API gateway only.",
            "domain": "product_scope",
        }
        revised = {
            "question_id": "q_scope_rev",
            "revises": "q_scope",
            "text": "What is in scope?",
            "answer": "API gateway and admin console.",
            "domain": "product_scope",
        }
        original["superseded_by"] = "q_scope_rev"
        state["questions_and_answers"] = [original, revised]
        snapshot = build_snapshot(state)

        active = {a.get("question_id") for a in snapshot.get("active_answers", []) if isinstance(a, dict)}
        superseded = snapshot.get("superseded_answers") or []
        assert "q_scope_rev" in active or any("admin console" in str(a.get("answer", "")) for a in active), (
            "Current truth must reflect revised answer"
        )
        assert any(s.get("question_id") == "q_scope" for s in superseded if isinstance(s, dict)), (
            "Superseded answers must remain auditable"
        )
        assert not any(
            a.get("answer") == "API gateway only." for a in snapshot.get("active_answers", []) if isinstance(a, dict)
        ), "Superseded answer text must not be treated as current truth"

    def test_analysis_receipt_persists_provenance_without_chain_of_thought(self) -> None:
        persist_receipt = require_callable("aoc_supervisor.analysis_receipts", "persist_analysis_receipt", dod="DoD-2")
        state = _load_seed_session()
        output = {
            "analysis_revision": 1,
            "evidence_revision": 1,
            "state_digest": "sha256:abc",
            "facts": [{"text": "OAuth2 required", "provenance": ["original_prompt"]}],
            "inferences": [],
            "assumptions": [],
            "contradictions": [],
            "resolved_without_user": [],
            "unresolved": [],
            "readiness": {
                "score": 0.1,
                "blocking_count": 1,
                "high_value_unknown_count": 1,
                "ready_to_finalize": False,
                "reason": "",
            },
            "next_action": "ASK",
            "next_question": {
                "question_id": "q1",
                "text": "Rate limit model?",
                "decision_target": "rate_limits",
                "why_it_matters": "Prevents abuse",
                "evidence_used": ["original_prompt"],
                "alternatives_considered": [],
                "recommended_default": None,
                "risk_if_wrong": "medium",
                "answer_mode": "freeform",
            },
        }
        receipt = persist_receipt(
            state, snapshot_digest="sha256:abc", output=output, provider_id="fake-deterministic-v1"
        )
        serialized = json.dumps(receipt, default=str)
        assert "chain_of_thought" not in serialized.lower()
        assert receipt.get("input_digest") and receipt.get("output_digest"), (
            "Receipt must capture input/output digests for auditability"
        )
