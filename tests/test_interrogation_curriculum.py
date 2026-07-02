"""World-class interrogation curriculum contract.

Covers the 2026-07 upgrade: complete domain curriculum, tiered coaching
order, answer-quality credit, weak-answer follow-ups, the two-strike
rescue draft, and — the point of it all — an honest, force-free path to
FINALIZE with the deterministic provider.
"""

from __future__ import annotations

from typing import Any

from aoc_supervisor.adaptive_question_engine import AdaptiveQuestionEngine
from aoc_supervisor.answer_quality import (
    RICH_CREDIT,
    SOLID_CREDIT,
    WEAK_CREDIT,
    credit_confidence,
    score_answer,
)
from aoc_supervisor.intent_blueprint_state import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    REQUIRED_DOMAINS,
)
from aoc_supervisor.question_policy import apply_intake_prompt
from aoc_supervisor.reasoning_provider import (
    _GAP_SPECS,
    DeterministicFakeReasoningProvider,
    _identify_uncertainties,
)

API_PROMPT = (
    "Build a small internal service with a REST API that receives webhook "
    "events for our team, verifies signatures, stores them in Postgres, and "
    "exposes a paginated read endpoint for auditors."
)


def _fresh_state(prompt: str = API_PROMPT) -> dict[str, Any]:
    state: dict[str, Any] = {
        "session_id": "curriculum-test",
        "original_prompt": prompt,
        "blueprint_version": 0,
        "questions_and_answers": [],
        "confirmed_requirements": [],
        "domain_coverage": {},
        "confidence_by_domain": {},
    }
    apply_intake_prompt(state)
    return state


def _rich_answer(domain: str) -> str:
    return (
        f"For {domain}: the service must never drop a verified event; p95 stays "
        f"under 300ms; core entities are webhook_event, receipt, and audit_log "
        f"linked by event_id, with 3 retries before dead-lettering."
    )


class TestCurriculumCompleteness:
    def test_every_required_domain_is_askable(self) -> None:
        spec_domains = {spec["domain"] for spec in _GAP_SPECS}
        missing = set(REQUIRED_DOMAINS) - spec_domains - {"product_scope"}
        assert not missing, f"domains with no question spec: {sorted(missing)}"

    def test_every_spec_is_fully_authored(self) -> None:
        for spec in _GAP_SPECS:
            target = spec["decision_target"]
            assert spec.get("template"), f"{target}: missing question template"
            assert spec.get("why"), f"{target}: missing why-it-matters"
            assert spec.get("follow_up"), f"{target}: missing follow-up"
            assert isinstance(spec.get("tier"), int), f"{target}: missing tier"

    def test_ask_domains_have_no_default_and_high_risk(self) -> None:
        # The dreamer's own voice: these must be asked, never auto-drafted.
        must_ask = {"target_users", "data_model", "business_rules", "authz", "security_privacy"}
        for spec in _GAP_SPECS:
            if spec["domain"] in must_ask:
                assert spec["default"] is None, f"{spec['domain']} must not be defaultable"
                assert float(spec["risk"]) >= 0.85, f"{spec['domain']} must sit in the ASK band"


class TestTieredOrdering:
    def test_fresh_session_leads_with_discovery(self) -> None:
        state = _fresh_state()
        snapshot = {
            "original_intent": API_PROMPT,
            "active_answers": [],
            "domain_coverage": state["domain_coverage"],
            "confidence_by_domain": state["confidence_by_domain"],
        }
        candidates = _identify_uncertainties(snapshot)
        assert candidates, "fresh session must have open questions"
        assert candidates[0]["tier"] == 0, "interview must open with discovery"
        tiers = [c["tier"] for c in candidates]
        assert tiers == sorted(tiers), "candidates must be presented foundations-first"

    def test_ordering_is_deterministic(self) -> None:
        snapshot = {
            "original_intent": API_PROMPT,
            "active_answers": [],
            "domain_coverage": {},
            "confidence_by_domain": {},
        }
        first = [c["decision_target"] for c in _identify_uncertainties(snapshot)]
        second = [c["decision_target"] for c in _identify_uncertainties(snapshot)]
        assert first == second


class TestAnswerQuality:
    def test_deflections_earn_weak_credit(self) -> None:
        for text in ("idk", "whatever you think", "  ", "yes", "no idea, sorry"):
            assert score_answer(text) == WEAK_CREDIT, f"deflection not caught: {text!r}"

    def test_substantive_answer_clears_threshold_in_one_pass(self) -> None:
        answer = "Auditors read events through a paginated endpoint sorted by arrival."
        assert score_answer(answer) >= SOLID_CREDIT
        assert credit_confidence(0.0, answer) >= DEFAULT_CONFIDENCE_THRESHOLD

    def test_specific_answer_earns_rich_credit(self) -> None:
        assert score_answer(_rich_answer("data_model")) == RICH_CREDIT

    def test_weak_answer_never_lowers_confidence(self) -> None:
        assert credit_confidence(0.7, "idk") >= 0.7


class TestFollowUpAndRescue:
    def _snapshot_with_answers(self, domain: str, answers: list[str]) -> dict[str, Any]:
        confident = {
            spec["domain"]: 0.9 for spec in _GAP_SPECS if spec["domain"] != domain
        }
        return {
            "original_intent": API_PROMPT,
            "active_answers": [
                {"question_id": f"q{i}", "domain": domain, "answer": text}
                for i, text in enumerate(answers)
            ],
            "domain_coverage": {domain: {"addressed": True, "na": False}},
            "confidence_by_domain": {**confident, domain: WEAK_CREDIT},
        }

    def test_one_weak_answer_earns_a_sharper_follow_up(self) -> None:
        snapshot = self._snapshot_with_answers("data_model", ["idk"])
        candidates = _identify_uncertainties(snapshot)
        assert candidates, "weak answer must resurface the domain"
        follow = candidates[0]
        assert follow["source"] == "follow_up"
        assert follow["decision_target"].endswith("::followup")
        assert 'you said "idk"' in follow["text"].lower()
        assert follow["default"] is None, "follow-ups must be asked, not defaulted"

    def test_two_weak_answers_trigger_the_rescue_draft(self) -> None:
        snapshot = self._snapshot_with_answers("data_model", ["idk", "still not sure"])
        candidates = _identify_uncertainties(snapshot)
        rescue = candidates[0]
        assert rescue["source"] == "rescue"
        assert rescue["default"], "rescue must carry a concrete reversible draft"
        assert rescue["risk"] < 0.8, "rescue must route through the auto-DEFAULT path"

    def test_rescue_resolves_without_asking_again(self) -> None:
        snapshot = self._snapshot_with_answers("data_model", ["idk", "still not sure"])
        snapshot.update({"analysis_revision": 1, "evidence_revision": 1, "state_digest": ""})
        output = DeterministicFakeReasoningProvider().analyze(snapshot)
        assert output["next_action"] == "DEFAULT"
        assert output["resolved_without_user"], "rescue must produce an auto-resolution"

    def test_well_answered_domain_is_never_nagged(self) -> None:
        snapshot = self._snapshot_with_answers("data_model", [_rich_answer("data_model")])
        snapshot["confidence_by_domain"]["data_model"] = RICH_CREDIT
        targets = [c["decision_target"] for c in _identify_uncertainties(snapshot)]
        assert not any("core_entities" in t for t in targets)


class TestHonestFinalizePath:
    """The point of it all: a thought-through idea finalizes without force."""

    def test_full_lifecycle_reaches_finalize_without_force(self) -> None:
        engine = AdaptiveQuestionEngine(provider=DeterministicFakeReasoningProvider())
        state = _fresh_state()
        state = engine.start_questioning(state)

        asked: list[str] = []
        for _ in range(40):
            question = state.get("current_question")
            if not question:
                break
            asked.append(str(question.get("domain")))
            state = engine.submit_answer(
                state,
                answer=_rich_answer(str(question.get("domain"))),
                question_id=question.get("question_id", ""),
            )

        assert state.get("current_question") is None, "interview must complete"
        readiness = (state.get("latest_analysis") or {}).get("readiness") or {}
        assert readiness.get("ready_to_finalize") is True, (
            f"idea must be finalize-ready after honest answers; asked={asked}"
        )

        coverage = state.get("domain_coverage") or {}
        confidence = state.get("confidence_by_domain") or {}
        for domain in REQUIRED_DOMAINS:
            meta = coverage.get(domain, {})
            if isinstance(meta, dict) and meta.get("na"):
                continue
            addressed = isinstance(meta, dict) and meta.get("addressed")
            confident = float(confidence.get(domain, 0.0)) >= DEFAULT_CONFIDENCE_THRESHOLD
            assert addressed and confident, (
                f"{domain}: addressed={addressed} confidence={confidence.get(domain)}"
            )

    def test_interview_is_bounded_and_humane(self) -> None:
        """A dreamer answering thoughtfully faces a focused interview, not a census."""
        engine = AdaptiveQuestionEngine(provider=DeterministicFakeReasoningProvider())
        state = _fresh_state()
        state = engine.start_questioning(state)
        count = 0
        for _ in range(40):
            question = state.get("current_question")
            if not question:
                break
            count += 1
            state = engine.submit_answer(
                state,
                answer=_rich_answer(str(question.get("domain"))),
                question_id=question.get("question_id", ""),
            )
        assert 1 <= count <= 12, f"expected a focused interview, got {count} questions"
