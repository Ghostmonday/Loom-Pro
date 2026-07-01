"""Claims Ledger projection tests."""

from __future__ import annotations

from aoc_supervisor.blueprint_compiler import compile_executable_projection, compile_rich_artifact
from aoc_supervisor.claims_ledger import build_claim_ledger
from aoc_supervisor.intent_blueprint_state import new_blueprint_state, public_session_view


def _state() -> dict:
    return new_blueprint_state(
        session_id="sess-claims",
        user_id="alice",
        tier="paid",
        original_prompt="Build a local-first research notebook.",
        session_status="VALIDATING",
    )


def test_claim_ledger_is_deterministic_across_evidence_order() -> None:
    first = _state()
    first["confirmed_requirements"] = [
        {"id": "REQ-2", "text": "Support offline search.", "domain": "functional_requirements"},
        {"id": "REQ-1", "text": "Encrypt local notes.", "domain": "security_privacy"},
    ]

    second = _state()
    second["confirmed_requirements"] = list(reversed(first["confirmed_requirements"]))

    left = build_claim_ledger(first)
    right = build_claim_ledger(second)

    assert left["ledger_digest"] == right["ledger_digest"]
    assert [claim["text"] for claim in left["claims"]] == [claim["text"] for claim in right["claims"]]


def test_superseded_answers_are_blocked_not_promoted() -> None:
    state = _state()
    state["questions_and_answers"] = [
        {
            "question_id": "q-old",
            "text": "Which auth mode?",
            "answer": "Password login.",
            "domain": "authz",
            "superseded_by": "q-new",
        },
        {
            "question_id": "q-new",
            "text": "Which auth mode?",
            "answer": "Passkeys only.",
            "domain": "authz",
        },
    ]

    ledger = build_claim_ledger(state)
    promoted = {claim["text"] for claim in ledger["promoted_claims"]}
    blocked = {claim["text"] for claim in ledger["blocked_claims"]}

    assert "Passkeys only." in promoted
    assert "Password login." in blocked
    assert "Password login." not in promoted


def test_explicit_incompatible_claims_block_promotion() -> None:
    state = _state()
    state["constraints"] = [
        {
            "id": "C-1",
            "text": "Runtime must be offline.",
            "domain": "infrastructure",
            "metadata": {
                "claim_subject": "runtime",
                "claim_predicate": "network_mode",
                "claim_object": "offline",
            },
        },
        {
            "id": "C-2",
            "text": "Runtime must require cloud sync.",
            "domain": "infrastructure",
            "metadata": {
                "claim_subject": "runtime",
                "claim_predicate": "network_mode",
                "claim_object": "cloud_sync",
            },
        },
    ]

    ledger = build_claim_ledger(state)

    assert ledger["contradiction_count"] == 1
    assert ledger["promoted_count"] == 1  # original prompt remains promoted
    assert {claim["text"] for claim in ledger["blocked_claims"]} == {
        "Runtime must be offline.",
        "Runtime must require cloud sync.",
    }
    assert ledger["promotion_gates"]["blueprint_influence_available"] is False


def test_compile_rich_artifact_includes_claims_ledger() -> None:
    state = _state()
    state["acceptance_criteria"] = [{"id": "AC-1", "text": "Search works while offline."}]

    artifact = compile_rich_artifact(state)
    ledger = artifact["claims_ledger"]

    assert ledger["claim_count"] >= 2
    assert any(claim["kind"] == "acceptance_criterion" for claim in ledger["claims"])
    assert ledger["ledger_digest"].startswith("sha256:")


def test_public_session_view_exposes_computed_claims_ledger() -> None:
    state = _state()
    state["confirmed_requirements"] = [
        {"id": "REQ-1", "text": "Support local-only mode.", "domain": "security_privacy"}
    ]
    state["processed_idempotency_keys"] = ["secret-internal-key"]

    public = public_session_view(state)

    assert "processed_idempotency_keys" not in public
    assert public["claims_ledger"]["promoted_count"] >= 2
    assert any(claim["text"] == "Support local-only mode." for claim in public["claims_ledger"]["claims"])


def test_promoted_claims_feed_projection_descriptions() -> None:
    state = _state()
    state["confirmed_requirements"] = [
        {
            "id": "REQ-api",
            "text": "Expose a local API for notebook search.",
            "domain": "infrastructure",
        }
    ]
    state["domain_coverage"]["infrastructure"]["addressed"] = True

    projection = compile_executable_projection(state)
    descriptions = " ".join(unit["description"] for unit in projection["work_units"])

    assert projection["projection_mode"] == "intent_forge"
    assert "Expose a local API for notebook search." in descriptions
