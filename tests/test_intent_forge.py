"""Intent Forge session lifecycle tests."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from aoc_supervisor.intent_forge_service import IntentForgeService
from aoc_supervisor.intent_session_store import VersionConflictError
from aoc_supervisor.telemetry_policy import export_optional_telemetry
from fastapi.testclient import TestClient

from tests.fixtures import contract_imports as _contract_imports  # noqa: F401 — worktree path precedence
from tests.fixtures.contract_imports import module_available, require_callable, require_module
from tests.fixtures.fake_reasoning_provider import ScriptedFakeReasoningProvider, divergence_script


@pytest.fixture
def forge_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import aoc_supervisor.api as api

    monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
    monkeypatch.setenv("GAIJINN_FAKE_REASONING", "1")
    monkeypatch.setattr(api, "ROOT_DIR", tmp_path)
    api._intent_forge_service = IntentForgeService(tmp_path)
    with TestClient(api.app) as client:
        yield client, api._intent_forge_service


def _headers() -> dict[str, str]:
    return {"X-User-Id": "alice", "Content-Type": "application/json"}


def test_free_tier_provisional_artifact(forge_env) -> None:
    client, _service = forge_env
    res = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a personal knowledge vault with search", "tier": "free"},
        headers=_headers(),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["tier"] == "free"
    assert data["session_status"] == "FINALIZED"
    assert data["artifact"]["provisional"] is True
    assert data["inferred_requirements"]


def test_paid_session_presents_question(forge_env) -> None:
    client, _service = forge_env
    res = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a team task board with roles and audit logs", "tier": "paid"},
        headers=_headers(),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["session_status"] == "QUESTIONING"
    assert data["current_question"]["question_id"]


def test_intake_prompt_seeds_product_scope_without_reasking(forge_env) -> None:
    client, _service = forge_env
    prompt = "Analyze my filesystem and SSD for actionable statistics on this machine"
    data = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": prompt, "tier": "paid"},
        headers=_headers(),
    ).json()
    assert data["session_status"] == "QUESTIONING"
    assert data["current_question"]["domain"] != "product_scope"
    seeded = [entry for entry in data.get("questions_and_answers", []) if entry.get("source") == "intake_prompt"]
    assert seeded and seeded[0]["answer"] == prompt
    assert any(req.get("text") == prompt for req in data.get("confirmed_requirements", []))
    assert "filesystem" in data["current_question"]["text"].lower() or "ssd" in data["current_question"]["text"].lower()


def test_filesystem_prompt_deprioritizes_authz(forge_env) -> None:
    client, _service = forge_env
    data = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Scan my SSD and report disk health statistics", "tier": "paid"},
        headers=_headers(),
    ).json()
    assert data["domain_coverage"]["authz"]["na"] is True
    assert data["current_question"]["domain"] == "functional_requirements"


def test_duplicate_answer_idempotency(forge_env) -> None:
    client, service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a secure API gateway", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    qid = created["current_question"]["question_id"]
    body = {
        "question_id": qid,
        "answer": "Use OAuth2 with role-based scopes for every endpoint.",
        "idempotency_key": "answer-once-001",
        "expected_blueprint_version": created["blueprint_version"],
    }
    first = client.post(f"/api/v1/intent-forge/sessions/{sid}/answers", json=body, headers=_headers())
    second = client.post(f"/api/v1/intent-forge/sessions/{sid}/answers", json=body, headers=_headers())
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["blueprint_version"] == first.json()["blueprint_version"]


def test_version_conflict_rejected(forge_env) -> None:
    client, service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build inventory tracking", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    with pytest.raises(VersionConflictError):
        service.submit_answer(
            sid,
            question_id=created["current_question"]["question_id"],
            answer="FIFO costing with nightly reconciliation.",
            idempotency_key="conflict-key-001",
            expected_blueprint_version=0,
        )


def test_finalize_now_allows_unresolved(forge_env) -> None:
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a chat app", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    res = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/finalize",
        json={
            "idempotency_key": "finalize-now-001",
            "expected_blueprint_version": created["blueprint_version"],
            "force": True,
        },
        headers=_headers(),
    )
    assert res.status_code == 200
    assert res.json()["session_status"] == "FINAL_CONFIRMATION"


def test_handoff_to_command_engine_url(forge_env) -> None:
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a note-taking CLI with markdown export", "tier": "free"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    version = created["blueprint_version"]
    confirmed = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/handoff",
        json={
            "action": "confirm",
            "confirmation": "Proceed",
            "idempotency_key": "handoff-confirm-001",
            "expected_blueprint_version": version,
        },
        headers=_headers(),
    )
    assert confirmed.status_code == 200
    version = confirmed.json()["blueprint_version"]
    accepted = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/handoff",
        json={
            "action": "accept",
            "idempotency_key": "handoff-accept-001",
            "expected_blueprint_version": version,
        },
        headers=_headers(),
    )
    assert accepted.status_code == 200
    assert accepted.json()["session_status"] == "HANDED_OFF"
    assert "command-engine" in accepted.json()["command_engine_url"]


def test_intent_forge_ui_route_served(forge_env) -> None:
    client, _service = forge_env
    res = client.get("/")
    assert res.status_code == 200
    assert "Blueprint" in res.text


def _answer(client, session: dict, answer: str, *, key: str, action: str = "answer") -> dict:
    q = session.get("current_question") or {}
    res = client.post(
        f"/api/v1/intent-forge/sessions/{session['session_id']}/answers",
        json={
            "question_id": q.get("question_id", ""),
            "answer": answer,
            "action": action,
            "idempotency_key": key,
            "expected_blueprint_version": session["blueprint_version"],
        },
        headers=_headers(),
    )
    assert res.status_code == 200
    return res.json()


def _handoff_free(client, session: dict) -> dict:
    version = session["blueprint_version"]
    confirmed = client.post(
        f"/api/v1/intent-forge/sessions/{session['session_id']}/handoff",
        json={
            "action": "confirm",
            "confirmation": "Proceed",
            "idempotency_key": f"handoff-confirm-{version}",
            "expected_blueprint_version": version,
        },
        headers=_headers(),
    )
    assert confirmed.status_code == 200
    version = confirmed.json()["blueprint_version"]
    accepted = client.post(
        f"/api/v1/intent-forge/sessions/{session['session_id']}/handoff",
        json={
            "action": "accept",
            "idempotency_key": f"handoff-accept-{version}",
            "expected_blueprint_version": version,
        },
        headers=_headers(),
    )
    assert accepted.status_code == 200
    return accepted.json()


def test_pause_resume_after_server_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import aoc_supervisor.api as api

    monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
    monkeypatch.setattr(api, "ROOT_DIR", tmp_path)
    api._intent_forge_service = IntentForgeService(tmp_path)
    with TestClient(api.app) as client:
        created = client.post(
            "/api/v1/intent-forge/sessions",
            json={"prompt": "Build a CRM with audit logs", "tier": "paid"},
            headers=_headers(),
        ).json()
        paused = client.post(
            f"/api/v1/intent-forge/sessions/{created['session_id']}/pause",
            json={
                "idempotency_key": "pause-restart-001",
                "expected_blueprint_version": created["blueprint_version"],
            },
            headers=_headers(),
        )
        assert paused.status_code == 200
        assert paused.json()["session_status"] == "PAUSED"
        sid = created["session_id"]
        version = paused.json()["blueprint_version"]

    api._intent_forge_service = IntentForgeService(tmp_path)
    with TestClient(api.app) as client:
        resumed = client.post(
            f"/api/v1/intent-forge/sessions/{sid}/resume",
            json={"idempotency_key": "resume-restart-001", "expected_blueprint_version": version},
            headers=_headers(),
        )
        assert resumed.status_code == 200
        assert resumed.json()["session_status"] == "QUESTIONING"


def test_revision_invalidates_dependent_nodes(forge_env) -> None:
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a task tracker", "tier": "paid"},
        headers=_headers(),
    ).json()
    answered = _answer(client, created, "V1 covers task creation and assignment only.", key="answer-scope-001")
    original_qid = (created["current_question"] or {})["question_id"]
    revised = client.post(
        f"/api/v1/intent-forge/sessions/{answered['session_id']}/revise",
        json={
            "question_id": original_qid,
            "answer": "V1 covers task creation, assignment, and weekly reporting.",
            "idempotency_key": "revise-scope-001",
            "expected_blueprint_version": answered["blueprint_version"],
        },
        headers=_headers(),
    )
    assert revised.status_code == 200
    stale = [req for req in revised.json().get("confirmed_requirements", []) if req.get("stale")]
    fresh = [
        req
        for req in revised.json().get("confirmed_requirements", [])
        if not req.get("stale") and "weekly reporting" in str(req.get("text", ""))
    ]
    assert stale
    assert fresh


def test_conflict_detection_and_resolution(forge_env) -> None:
    client, _service = forge_env
    session = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a realtime analytics platform", "tier": "paid"},
        headers=_headers(),
    ).json()
    while session.get("current_question"):
        domain = session["current_question"]["domain"]
        if domain == "functional_requirements":
            session = _answer(
                client,
                session,
                "Reads must provide zero-latency responses for dashboards.",
                key="answer-functional-conflict",
            )
            break
        session = _answer(client, session, f"Cover {domain} in V1.", key=f"answer-{domain}")
    while session.get("current_question") and session["session_status"] == "QUESTIONING":
        domain = session["current_question"]["domain"]
        if domain == "testing_acceptance":
            session = _answer(
                client,
                session,
                "All writes must pass through a validation window before commit.",
                key="answer-testing-conflict",
            )
            break
        session = _answer(client, session, f"Cover {domain} in V1.", key=f"answer2-{domain}")
    assert session["session_status"] == "CONFLICT_RESOLUTION"
    resolved = _answer(
        client,
        session,
        "Use zero-latency reads and async validation window for writes only.",
        key="resolve-conflict-001",
    )
    assert resolved["session_status"] in {"QUESTIONING", "VALIDATING", "FINAL_CONFIRMATION"}


def test_validation_failure_returns_to_questioning(forge_env) -> None:
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a photo gallery", "tier": "paid"},
        headers=_headers(),
    ).json()
    blocked = client.post(
        f"/api/v1/intent-forge/sessions/{created['session_id']}/finalize",
        json={
            "idempotency_key": "finalize-blocked-001",
            "expected_blueprint_version": created["blueprint_version"],
            "force": False,
        },
        headers=_headers(),
    )
    assert blocked.status_code == 200
    assert blocked.json()["session_status"] == "QUESTIONING"


def test_handoff_prepare_flow(forge_env) -> None:
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a markdown note CLI", "tier": "free"},
        headers=_headers(),
    ).json()
    handed = _handoff_free(client, created)
    sid = handed["session_id"]
    prepare = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": created["original_prompt"], "intent_forge_session_id": sid},
        headers=_headers(),
    )
    assert prepare.status_code == 200
    payload = prepare.json()
    assert payload["session_id"] == sid
    assert payload["work_units"] >= 1
    assert payload.get("executable_projection") is None


def test_telemetry_declined_path(forge_env) -> None:
    client, service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={
            "prompt": "Build a habit tracker",
            "tier": "paid",
            "telemetry_consent": {"operational": True, "analytics": False, "training": False},
        },
        headers=_headers(),
    ).json()
    assert created["telemetry_consent"]["analytics"] is False
    state = service.store.load(created["session_id"])
    assert export_optional_telemetry(state) is None


def test_websocket_replay_and_snapshot(forge_env, tmp_path: Path) -> None:
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a recipe manager", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    with client.websocket_connect(f"/ws/intent-forge?session_id={sid}&last_sequence=-1&blueprint_version=0") as ws:
        first = ws.receive_json()
        assert first["event_type"] == "intent.session.created"
        second = ws.receive_json()
        assert second["event_type"] == "intent.question.presented"
        snapshot = ws.receive_json()
        assert snapshot["event_type"] == "session.snapshot"
        assert snapshot["data"]["replay"] is True
    events_path = tmp_path / ".gaijinn" / "intent-forge" / "sessions" / sid / "events.jsonl"
    lines = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(event["event_type"] == "intent.session.created" for event in lines)


class TestPerfectSpecLifecycleContract:
    """Service-level assertions for canonical DoD items 1, 14, and 15."""

    def test_dod14_resume_revise_and_supersede_audit_trail(self, forge_env) -> None:
        client, _service = forge_env
        created = client.post(
            "/api/v1/intent-forge/sessions",
            json={"prompt": "Build a CRM with audit logs", "tier": "paid"},
            headers=_headers(),
        ).json()
        sid = created["session_id"]
        answered = _answer(client, created, "V1 covers contacts and notes only.", key="lifecycle-answer-001")
        original_qid = (created["current_question"] or {})["question_id"]
        revised = client.post(
            f"/api/v1/intent-forge/sessions/{sid}/revise",
            json={
                "question_id": original_qid,
                "answer": "V1 covers contacts, notes, and weekly reporting.",
                "idempotency_key": "lifecycle-revise-001",
                "expected_blueprint_version": answered["blueprint_version"],
            },
            headers=_headers(),
        ).json()
        superseded = [
            entry for entry in revised.get("questions_and_answers", []) if entry.get("question_id") == original_qid
        ]
        active = [entry for entry in revised.get("questions_and_answers", []) if not entry.get("superseded_by")]
        assert superseded and superseded[0].get("superseded_by"), "DoD-14: superseded answers remain auditable"
        assert any("weekly reporting" in str(entry.get("answer", "")) for entry in active), (
            "DoD-14: revised answer becomes current truth"
        )

        paused = client.post(
            f"/api/v1/intent-forge/sessions/{sid}/pause",
            json={"idempotency_key": "lifecycle-pause-001", "expected_blueprint_version": revised["blueprint_version"]},
            headers=_headers(),
        ).json()
        assert paused["session_status"] == "PAUSED"
        resumed = client.post(
            f"/api/v1/intent-forge/sessions/{sid}/resume",
            json={"idempotency_key": "lifecycle-resume-001", "expected_blueprint_version": paused["blueprint_version"]},
            headers=_headers(),
        ).json()
        assert resumed["session_status"] in {"QUESTIONING", "CONFLICT_RESOLUTION"}
        assert resumed.get("current_question") or resumed.get("session_status") == "CONFLICT_RESOLUTION", (
            "DoD-14: resume restores committed questioning state"
        )

    def test_dod15_service_must_not_present_domain_prompt_queue(self, forge_env) -> None:
        from aoc_supervisor import question_policy

        source = inspect.getsource(question_policy.build_next_question)
        if module_available("aoc_supervisor.adaptive_question_engine"):
            assert "rank_candidate_domains" not in source, (
                "DoD-15: service path must not traverse fixed domain order for questions"
            )
        else:
            pytest.fail("DoD-15: adaptive_question_engine required before static prompt traversal can be removed")

    def test_dod1_paid_session_records_analysis_receipt_per_answer(
        self, forge_env, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        if not module_available("aoc_supervisor.adaptive_question_engine"):
            pytest.fail("DoD-1: adaptive_question_engine must integrate with IntentForgeService")

        require_module(
            "aoc_supervisor.reasoning_provider",
            "DeterministicFakeReasoningProvider",
            dod="DoD-1",
        )
        client, service = forge_env
        with patch.object(
            service,
            "_reasoning_provider",
            ScriptedFakeReasoningProvider(script=divergence_script()),
            create=True,
        ):
            created = client.post(
                "/api/v1/intent-forge/sessions",
                json={"prompt": "Build a secure API gateway with OAuth2", "tier": "paid"},
                headers=_headers(),
            ).json()
            before = len(created.get("analysis_receipts") or [])
            answered = _answer(
                client,
                created,
                "OAuth2 with scoped tokens for every endpoint.",
                key="analysis-receipt-001",
            )
            after = len(answered.get("analysis_receipts") or [])
            assert after > before or int(answered.get("analysis_revision") or 0) > int(
                created.get("analysis_revision") or 0
            ), "DoD-1: each answer must trigger a fresh analysis receipt/revision"

    def test_interrogation_metrics_available_for_session(self, forge_env) -> None:
        evaluate_interrogation_session = require_callable(
            "aoc_supervisor.workflow_evaluator",
            "evaluate_interrogation_session",
            dod="DoD-15",
        )

        client, _service = forge_env
        created = client.post(
            "/api/v1/intent-forge/sessions",
            json={"prompt": "Build inventory tracking with nightly reconciliation", "tier": "paid"},
            headers=_headers(),
        ).json()
        _checks, metrics = evaluate_interrogation_session(created)
        assert metrics.whole_state_reanalysis_rate >= 0.0
        assert metrics.voice_fallback_integrity is True


# ─────────────────────────────────────────────
# IF-HARDEN-001: ANALYSIS_BLOCKED state (Defect A)
# ─────────────────────────────────────────────


def _raise_provider_failure(*args, **kwargs):
    """Simulate provider failure by raising ProviderFailureError."""
    from aoc_supervisor.reasoning_provider import ProviderFailureError

    raise ProviderFailureError(
        code="provider_unavailable",
        message="Simulated provider failure for testing.",
        retryable=True,
    )


def _blocked_next_question(state):
    """Simulate question policy handling a provider outage."""
    state["analysis_recovery"] = {
        "code": "provider_unavailable",
        "message": "Simulated provider failure for testing.",
        "retryable": True,
    }
    return None


def _working_select_next(state, *, engine=None):
    """Simulate successful provider: return a question."""
    return {
        "question_id": "q_test_recovered",
        "domain": "functional_requirements",
        "decision_target": "functional_scope",
        "text": "Test recovered question?",
        "why_it_matters": "Testing recovery.",
        "impact_hint": "medium",
        "alternatives_considered": ["ASK"],
        "answer_mode": "freeform",
        "next_action": "ASK",
        "risk_if_wrong": "medium",
    }


def test_provider_failure_sets_analysis_blocked(forge_env) -> None:
    """Paid session with unavailable provider → ANALYSIS_BLOCKED, current_question=None."""
    client, service = forge_env
    with patch.dict(service.create_session.__globals__, {"build_next_question": _blocked_next_question}):
        created = client.post(
            "/api/v1/intent-forge/sessions",
            json={"prompt": "Build a team dashboard", "tier": "paid"},
            headers=_headers(),
        ).json()
    assert created["session_status"] == "ANALYSIS_BLOCKED", (
        f"expected ANALYSIS_BLOCKED, got {created['session_status']}"
    )
    assert created["current_question"] is None
    assert created.get("analysis_recovery") is not None
    assert created["analysis_recovery"]["retryable"] is True


def test_resume_stays_analysis_blocked_while_provider_fails(forge_env) -> None:
    """Resume while provider remains unavailable → remains ANALYSIS_BLOCKED."""
    client, service = forge_env
    with patch.dict(service.create_session.__globals__, {"build_next_question": _blocked_next_question}):
        created = client.post(
            "/api/v1/intent-forge/sessions",
            json={"prompt": "Build a habit tracker", "tier": "paid"},
            headers=_headers(),
        ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    with patch.dict(service.resume.__globals__, {"build_next_question": _blocked_next_question}):
        resumed = client.post(
            f"/api/v1/intent-forge/sessions/{sid}/resume",
            json={"idempotency_key": "resume-blocked-001", "expected_blueprint_version": bv},
            headers=_headers(),
        ).json()
    assert resumed["session_status"] == "ANALYSIS_BLOCKED"
    assert resumed["current_question"] is None


def test_resume_recovering_provider_returns_to_questioning(forge_env) -> None:
    """Resume after provider recovers → QUESTIONING with a valid current_question."""
    client, _service = forge_env
    with patch(
        "aoc_supervisor.adaptive_question_engine.AdaptiveQuestionEngine.select_next",
        side_effect=_raise_provider_failure,
    ):
        created = client.post(
            "/api/v1/intent-forge/sessions",
            json={"prompt": "Build a weather API", "tier": "paid"},
            headers=_headers(),
        ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    with patch(
        "aoc_supervisor.adaptive_question_engine.AdaptiveQuestionEngine.select_next",
        return_value=_working_select_next({}),
    ):
        resumed = client.post(
            f"/api/v1/intent-forge/sessions/{sid}/resume",
            json={"idempotency_key": "resume-recovered-001", "expected_blueprint_version": bv},
            headers=_headers(),
        ).json()
    assert resumed["session_status"] == "QUESTIONING"
    assert resumed["current_question"] is not None


def test_no_questioning_without_current_question(forge_env) -> None:
    """Invariant: no public session may be QUESTIONING with current_question=None."""
    client, _service = forge_env
    with patch(
        "aoc_supervisor.adaptive_question_engine.AdaptiveQuestionEngine.select_next",
        side_effect=_raise_provider_failure,
    ):
        created = client.post(
            "/api/v1/intent-forge/sessions",
            json={"prompt": "Build a blog engine", "tier": "paid"},
            headers=_headers(),
        ).json()
    if created["session_status"] == "QUESTIONING":
        assert created["current_question"] is not None
    assert created["session_status"] in {"QUESTIONING", "ANALYSIS_BLOCKED"}
    if created["session_status"] == "ANALYSIS_BLOCKED":
        assert created["current_question"] is None


# ─────────────────────────────────────────────
# IF-HARDEN-001: Idempotency hardening (Defect B)
# ─────────────────────────────────────────────


def test_duplicate_finalize_idempotent(forge_env) -> None:
    """Duplicate finalize: no HTTP 500, no blueprint_version increase, stable state."""
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a file organizer", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    req = {
        "idempotency_key": "dup-finalize-001",
        "expected_blueprint_version": bv,
        "force": False,
    }
    first = client.post(f"/api/v1/intent-forge/sessions/{sid}/finalize", json=req, headers=_headers())
    second = client.post(f"/api/v1/intent-forge/sessions/{sid}/finalize", json=req, headers=_headers())
    assert first.status_code == 200
    assert second.status_code == 200, f"duplicate finalize returned {second.status_code}, expected 200"
    assert second.json()["blueprint_version"] == first.json()["blueprint_version"]
    assert second.json()["session_status"] == first.json()["session_status"]


def test_duplicate_handoff_confirm_idempotent(forge_env) -> None:
    """Duplicate handoff confirm: no duplicate transition, no HTTP 500."""
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a timer app", "tier": "free"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    req = {
        "action": "confirm",
        "confirmation": "Proceed",
        "idempotency_key": "dup-confirm-001",
        "expected_blueprint_version": bv,
    }
    first = client.post(f"/api/v1/intent-forge/sessions/{sid}/handoff", json=req, headers=_headers())
    assert first.status_code == 200
    bv_after = first.json()["blueprint_version"]
    second = client.post(f"/api/v1/intent-forge/sessions/{sid}/handoff", json=req, headers=_headers())
    assert second.status_code == 200, f"duplicate handoff confirm returned {second.status_code}, expected 200"
    assert second.json()["blueprint_version"] == bv_after
    assert second.json()["session_status"] == first.json()["session_status"]


def test_duplicate_handoff_accept_idempotent(forge_env) -> None:
    """Duplicate handoff accept: no duplicate transition, no HTTP 500."""
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a todo CLI", "tier": "free"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    confirm_req = {
        "action": "confirm",
        "confirmation": "Proceed",
        "idempotency_key": "dup-accept-confirm-001",
        "expected_blueprint_version": bv,
    }
    confirmed = client.post(f"/api/v1/intent-forge/sessions/{sid}/handoff", json=confirm_req, headers=_headers())
    assert confirmed.status_code == 200
    bv_after = confirmed.json()["blueprint_version"]

    accept_req = {
        "action": "accept",
        "idempotency_key": "dup-accept-001",
        "expected_blueprint_version": bv_after,
    }
    first = client.post(f"/api/v1/intent-forge/sessions/{sid}/handoff", json=accept_req, headers=_headers())
    assert first.status_code == 200
    assert first.json()["session_status"] == "HANDED_OFF"
    bv_final = first.json()["blueprint_version"]

    second = client.post(f"/api/v1/intent-forge/sessions/{sid}/handoff", json=accept_req, headers=_headers())
    assert second.status_code == 200, f"duplicate accept returned {second.status_code}, expected 200"
    assert second.json()["blueprint_version"] == bv_final
    assert second.json()["session_status"] == "HANDED_OFF"


def test_duplicate_pause_idempotent(forge_env) -> None:
    """Duplicate pause: no HTTP 500, stable state."""
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a timer app", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    req = {
        "idempotency_key": "dup-pause-001",
        "expected_blueprint_version": bv,
    }
    first = client.post(f"/api/v1/intent-forge/sessions/{sid}/pause", json=req, headers=_headers())
    assert first.status_code == 200
    bv_after = first.json()["blueprint_version"]
    second = client.post(f"/api/v1/intent-forge/sessions/{sid}/pause", json=req, headers=_headers())
    assert second.status_code == 200, f"duplicate pause returned {second.status_code}"
    assert second.json()["blueprint_version"] == bv_after


def test_duplicate_resume_idempotent(forge_env) -> None:
    """Duplicate resume: no HTTP 500, stable state."""
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a notebook sync tool", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    pause_req = {
        "idempotency_key": "dup-resume-pause-001",
        "expected_blueprint_version": bv,
    }
    paused = client.post(f"/api/v1/intent-forge/sessions/{sid}/pause", json=pause_req, headers=_headers())
    assert paused.status_code == 200
    bv_after = paused.json()["blueprint_version"]

    resume_req = {
        "idempotency_key": "dup-resume-001",
        "expected_blueprint_version": bv_after,
    }
    first = client.post(f"/api/v1/intent-forge/sessions/{sid}/resume", json=resume_req, headers=_headers())
    assert first.status_code == 200
    bv_final = first.json()["blueprint_version"]
    second = client.post(f"/api/v1/intent-forge/sessions/{sid}/resume", json=resume_req, headers=_headers())
    assert second.status_code == 200, f"duplicate resume returned {second.status_code}"
    assert second.json()["blueprint_version"] == bv_final


# ─────────────────────────────────────────────
# IF-HARDEN-001: Forced finalization (Defect C)
# ─────────────────────────────────────────────


def test_forced_finalization_metadata_persisted(forge_env) -> None:
    """Force-finalize an incomplete session and verify forced_finalization metadata."""
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a photo gallery app", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    forced = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/finalize",
        json={
            "idempotency_key": "force-meta-001",
            "expected_blueprint_version": bv,
            "force": True,
        },
        headers=_headers(),
    )
    assert forced.status_code == 200
    assert forced.json()["session_status"] == "FINAL_CONFIRMATION"
    meta = forced.json().get("forced_finalization")
    assert meta is not None, "forced_finalization metadata must be present"
    assert meta.get("forced") is True
    assert isinstance(meta.get("overridden_blockers"), list)
    assert len(meta["overridden_blockers"]) > 0


def test_forced_finalize_then_handoff_succeeds(forge_env) -> None:
    """Force-finalized session → handoff confirm → FINALIZED with non-null artifact/projection."""
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a markdown editor", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    forced = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/finalize",
        json={
            "idempotency_key": "force-handoff-001",
            "expected_blueprint_version": bv,
            "force": True,
        },
        headers=_headers(),
    )
    assert forced.status_code == 200
    assert forced.json()["session_status"] == "FINAL_CONFIRMATION"
    bv_after = forced.json()["blueprint_version"]

    confirmed = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/handoff",
        json={
            "action": "confirm",
            "confirmation": "Proceed with known gaps",
            "idempotency_key": "force-handoff-confirm-001",
            "expected_blueprint_version": bv_after,
        },
        headers=_headers(),
    )
    assert confirmed.status_code == 200, f"handoff confirm after force failed: {confirmed.json()}"
    assert confirmed.json()["session_status"] == "FINALIZED"
    assert confirmed.json().get("artifact") is not None
    assert confirmed.json().get("executable_projection") is not None
    # Forced finalization metadata must survive in public view
    assert confirmed.json().get("forced_finalization") is not None


def test_forced_finalize_full_lifecycle(forge_env) -> None:
    """Force-finalized session → confirm → accept → HANDED_OFF."""
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a habit tracker", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]
    forced = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/finalize",
        json={
            "idempotency_key": "force-lifecycle-001",
            "expected_blueprint_version": bv,
            "force": True,
        },
        headers=_headers(),
    )
    assert forced.json()["session_status"] == "FINAL_CONFIRMATION"
    bv = forced.json()["blueprint_version"]

    confirmed = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/handoff",
        json={
            "action": "confirm",
            "confirmation": "Accept gaps",
            "idempotency_key": "force-lifecycle-confirm-001",
            "expected_blueprint_version": bv,
        },
        headers=_headers(),
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["session_status"] == "FINALIZED"
    bv = confirmed.json()["blueprint_version"]

    accepted = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/handoff",
        json={
            "action": "accept",
            "idempotency_key": "force-lifecycle-accept-001",
            "expected_blueprint_version": bv,
        },
        headers=_headers(),
    )
    assert accepted.status_code == 200
    assert accepted.json()["session_status"] == "HANDED_OFF"


def test_force_does_not_bypass_structural_corruption(forge_env) -> None:
    """Structurally corrupted blueprint (contradictions) must still block even with force."""
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a voting app", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]

    # Inject an unresolved contradiction directly into store to simulate corruption
    service = _service
    state = service.store.load(sid)
    state.setdefault("contradictions", []).append(
        {
            "id": "CORRUPT-001",
            "description": "Simulated structural corruption",
            "element_a_id": "REQ-A",
            "element_b_id": "REQ-B",
            "resolved": False,
        }
    )
    state["blueprint_version"] = bv + 1
    service.store.save(sid, state)
    bv += 1

    forced = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/finalize",
        json={
            "idempotency_key": "force-corrupt-001",
            "expected_blueprint_version": bv,
            "force": True,
        },
        headers=_headers(),
    )
    # With force=True, contradictions should still block
    assert forced.json()["session_status"] != "FINAL_CONFIRMATION", f"structural corruption bypassed: {forced.json()}"


def test_rejected_force_preserves_unresolved_blockers(forge_env) -> None:
    """Rejected force-finalize attempts must not clear unresolved item blockers."""
    client, service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a release approval workflow", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]

    state = service.store.load(sid)
    blocker_id = "BLOCKER-PRESERVE-001"
    state.setdefault("unresolved_items", []).append(
        {
            "id": blocker_id,
            "description": "Needs explicit audit policy decision.",
            "blocking": True,
        }
    )
    state.setdefault("contradictions", []).append(
        {
            "id": "CORRUPT-PRESERVE-001",
            "description": "Simulated structural corruption",
            "element_a_id": "REQ-A",
            "element_b_id": "REQ-B",
            "resolved": False,
        }
    )
    state["blueprint_version"] = bv + 1
    service.store.save(sid, state)
    bv += 1

    forced = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/finalize",
        json={
            "idempotency_key": "force-preserve-blocker-001",
            "expected_blueprint_version": bv,
            "force": True,
        },
        headers=_headers(),
    )
    assert forced.json()["session_status"] != "FINAL_CONFIRMATION"

    persisted = service.store.load(sid)
    blocker = next(item for item in persisted["unresolved_items"] if item.get("id") == blocker_id)
    assert blocker["blocking"] is True


def test_force_does_not_bypass_stale_graph_nodes(forge_env) -> None:
    """Stale dependency graph nodes must still block even with force."""
    client, service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a permissions dashboard", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    bv = created["blueprint_version"]

    state = service.store.load(sid)
    graph = state.setdefault("blueprint_graph", {"version": bv, "nodes": [], "edges": []})
    graph.setdefault("nodes", []).append(
        {
            "id": "REQ-STALE-001",
            "type": "requirement",
            "label": "Stale requirement",
            "stale": True,
        }
    )
    state["blueprint_version"] = bv + 1
    service.store.save(sid, state)
    bv += 1

    forced = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/finalize",
        json={
            "idempotency_key": "force-stale-node-001",
            "expected_blueprint_version": bv,
            "force": True,
        },
        headers=_headers(),
    )
    body = forced.json()
    assert body["session_status"] != "FINAL_CONFIRMATION", f"stale graph node bypassed: {body}"
    assert "stale graph nodes remain" in body["current_question"]["blocking_items"][0]
