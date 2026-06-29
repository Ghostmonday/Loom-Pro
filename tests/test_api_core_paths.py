"""Behavioral coverage for api.py core HTTP paths (GAIJINN-COV-001)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from aoc_supervisor.adaptive_question_engine import set_default_provider
from aoc_supervisor.intent_forge_service import IntentForgeService
from aoc_supervisor.orchestrate_session import OrchestrateSessionStore, SessionSnapshot
from aoc_supervisor.ui_intent import UiIntentDriver
from fastapi.testclient import TestClient

from tests.fixtures.fake_reasoning_provider import ScriptedFakeReasoningProvider, divergence_script


def _headers(*, user_id: str = "alice") -> dict[str, str]:
    return {"X-User-Id": user_id, "Content-Type": "application/json"}


def _spawn_headers(*, user_id: str = "alice", idempotency_key: str = "core-spawn-key") -> dict[str, str]:
    return {"X-User-Id": user_id, "X-Idempotency-Key": idempotency_key}


@pytest.fixture
def forge_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Intent Forge API client with isolated storage and deterministic reasoning."""
    import aoc_supervisor.api as api

    monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
    monkeypatch.setenv("GAIJINN_FAKE_REASONING", "1")
    monkeypatch.setenv("GAIJINN_ALLOW_INSECURE_LOCAL", "1")
    monkeypatch.setattr(api, "ROOT_DIR", tmp_path)
    api._intent_forge_service = IntentForgeService(tmp_path)
    with TestClient(api.app) as client:
        set_default_provider(ScriptedFakeReasoningProvider(script=divergence_script()))
        yield client, api._intent_forge_service


# ── Orchestrate prepare ─────────────────────────────────────────────────────


def test_prepare_greenfield_returns_public_stats(mock_grid_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /orchestrate/prepare succeeds for greenfield intent and hides raw blueprint."""
    client, _workers, _tmp, _store = mock_grid_client
    calls: list[tuple[str, ...]] = []

    def fake_run(project_root: Path, *args: str, **_kwargs) -> None:
        calls.append(args)
        if args and args[0] == "plan":
            blueprint = {
                "schema_version": 1,
                "blueprint_mode": "graph",
                "work_stream_titles": ["Game board", "Game rules"],
                "work_units": [
                    {"id": "WU-001", "title": "Game board", "allowed_paths": ["src/board/"]},
                    {"id": "WU-002", "title": "Game rules", "allowed_paths": ["src/rules/"]},
                ],
            }
            blueprint_path = project_root / ".gaijinn" / "blueprint.json"
            blueprint_path.parent.mkdir(parents=True, exist_ok=True)
            blueprint_path.write_text(json.dumps(blueprint, indent=2) + "\n", encoding="utf-8")

    import aoc_supervisor.api as api
    monkeypatch.setitem(api._session_store.advance_phase.__globals__, "_run_gaijinn", fake_run)

    response = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": "Build a tic-tac-toe game with local multiplayer"},
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert payload["work_units"] >= 1
    assert payload["phase"] == "awaiting_swarm"
    assert payload.get("executable_projection") is None
    assert "blueprint.json" not in json.dumps(payload)
    assert any(call and call[0] == "plan" for call in calls)


def test_prepare_rejects_intent_forge_before_handoff(forge_client) -> None:
    """Intent-forge handoff guard: prepare returns 409 until session is HANDED_OFF."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a markdown note CLI", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    assert created["session_status"] == "QUESTIONING"

    blocked = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": created["original_prompt"], "intent_forge_session_id": sid},
        headers=_headers(),
    )
    assert blocked.status_code == 409
    assert "HANDED_OFF" in blocked.json()["detail"]


def test_prepare_rejects_intent_forge_owner_mismatch(forge_client) -> None:
    """Intent-forge owner guard: mismatched principal cannot drive prepare."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a team wiki", "tier": "free"},
        headers=_headers(user_id="alice"),
    ).json()
    sid = created["session_id"]
    version = created["blueprint_version"]
    confirmed = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/handoff",
        json={
            "action": "confirm",
            "confirmation": "Proceed",
            "idempotency_key": "handoff-confirm-owner",
            "expected_blueprint_version": version,
        },
        headers=_headers(user_id="alice"),
    )
    assert confirmed.status_code == 200
    version = confirmed.json()["blueprint_version"]
    accepted = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/handoff",
        json={
            "action": "accept",
            "idempotency_key": "handoff-accept-owner",
            "expected_blueprint_version": version,
        },
        headers=_headers(user_id="alice"),
    )
    assert accepted.status_code == 200
    assert accepted.json()["session_status"] == "HANDED_OFF"

    denied = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": created["original_prompt"], "intent_forge_session_id": sid},
        headers=_headers(user_id="bob"),
    )
    assert denied.status_code == 403
    assert "access denied" in denied.json()["detail"].lower()


# ── Orchestrate swarm ───────────────────────────────────────────────────────


def test_swarm_rejects_missing_session_id(mock_grid_client) -> None:
    """POST /orchestrate/swarm requires session_id."""
    client, _workers, _tmp, _store = mock_grid_client
    response = client.post(
        "/api/v1/orchestrate/swarm",
        json={"workers": 2},
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "session_id is required"


@pytest.mark.parametrize("workers", [0, -1, "two"])
def test_swarm_rejects_invalid_workers(mock_grid_client, workers: object) -> None:
    """POST /orchestrate/swarm rejects non-positive worker counts."""
    client, _workers, _tmp, store = mock_grid_client
    snapshot = store.prepare("Terminal smoke test project", owner_user_id="terminal-user")
    response = client.post(
        "/api/v1/orchestrate/swarm",
        json={"session_id": snapshot.session_id, "workers": workers},
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "workers must be a positive integer"


# ── Orchestrate advance-phase ───────────────────────────────────────────────


def test_advance_phase_rejects_unmerged_session(mock_grid_client) -> None:
    """POST /orchestrate/advance-phase blocks until the current phase has merged."""
    client, _workers, _tmp, store = mock_grid_client
    snapshot = store.prepare(
        "Terminal smoke test project",
        phases=["backend", "frontend"],
        owner_user_id="terminal-user",
    )
    assert snapshot.phase == "awaiting_swarm"

    response = client.post(
        "/api/v1/orchestrate/advance-phase",
        json={"session_id": snapshot.session_id},
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 400
    assert "merged" in response.json()["detail"].lower()


def test_advance_phase_success_reblueprints_next_phase(mock_grid_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /orchestrate/advance-phase re-blueprints the next phase via mocked pipeline."""
    client, _workers, _tmp, store = mock_grid_client
    session_id = "aabbccddeeff"
    session_root = store.sessions_dir / session_id
    gaijinn_dir = session_root / ".gaijinn"
    gaijinn_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "session_id": session_id,
        "owner_user_id": "terminal-user",
        "intent": "Build a REST API backend service",
        "phase": "awaiting_next_phase",
        "phases": ["backend", "frontend"],
        "current_phase": "backend",
        "pipeline_plan": {
            "phases": ["backend", "frontend"],
            "current_index": 0,
            "current_phase": "backend",
            "completed_phases": ["backend"],
        },
        "loaded_context": {},
        "blueprint_mode": "intent",
        "work_stream_titles": ["Service API layer"],
        "swarm_rationale": "demo",
    }
    (gaijinn_dir / "session.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    store._active[session_id] = session_root

    def fake_pipeline(
        project_root: Path,
        intent: str,
        *,
        command_timeout: int | None = None,
        use_intent_blueprint: bool = False,
        loaded_context: dict | None = None,
    ) -> tuple[int, int, tuple[str, ...], str, tuple[str, ...]]:
        titles = ("Desktop UI",)
        blueprint = {
            "schema_version": 1,
            "project_goal": intent,
            "blueprint_mode": "intent",
            "work_stream_titles": list(titles),
            "work_units": [{"id": "WU-001", "title": titles[0], "allowed_paths": ["src/ui/"]}],
        }
        (project_root / ".gaijinn" / "blueprint.json").write_text(
            json.dumps(blueprint, indent=2) + "\n",
            encoding="utf-8",
        )
        assert loaded_context is not None
        assert loaded_context["backend"]["prior_session_id"] == session_id
        return 1, 0, titles, "intent", titles

    import aoc_supervisor.api as api
    monkeypatch.setitem(api._session_store.advance_phase.__globals__, "_run_blueprint_pipeline", fake_pipeline)

    response = client.post(
        "/api/v1/orchestrate/advance-phase",
        json={"session_id": session_id},
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] == "awaiting_swarm"
    assert payload["current_phase"] == "frontend"
    assert payload["workers_ready"] == 0
    assert "blueprint stub" not in (payload.get("message") or "").lower()


# ── Intent Forge API ──────────────────────────────────────────────────────────


def test_intent_forge_revise_answer(forge_client) -> None:
    """POST /intent-forge/sessions/{id}/revise supersedes a prior answer."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a task tracker", "tier": "paid"},
        headers=_headers(),
    ).json()
    qid = created["current_question"]["question_id"]
    answered = client.post(
        f"/api/v1/intent-forge/sessions/{created['session_id']}/answers",
        json={
            "question_id": qid,
            "answer": "V1 covers task creation only.",
            "idempotency_key": "core-revise-answer",
            "expected_blueprint_version": created["blueprint_version"],
        },
        headers=_headers(),
    ).json()
    revised = client.post(
        f"/api/v1/intent-forge/sessions/{created['session_id']}/revise",
        json={
            "question_id": qid,
            "answer": "V1 covers task creation and assignment.",
            "idempotency_key": "core-revise-submit",
            "expected_blueprint_version": answered["blueprint_version"],
        },
        headers=_headers(),
    )
    assert revised.status_code == 200
    superseded = [
        entry
        for entry in revised.json().get("questions_and_answers", [])
        if entry.get("question_id") == qid and entry.get("superseded_by")
    ]
    assert superseded


def test_intent_forge_create_and_answer_with_scripted_provider(forge_client) -> None:
    """Intent Forge session create + answer advances questioning with injected provider."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a secure API gateway with OAuth2", "tier": "paid"},
        headers=_headers(),
    )
    assert created.status_code == 200
    session = created.json()
    assert session["session_status"] == "QUESTIONING"
    assert session["current_question"]["question_id"]

    answered = client.post(
        f"/api/v1/intent-forge/sessions/{session['session_id']}/answers",
        json={
            "question_id": session["current_question"]["question_id"],
            "answer": "OAuth2 with scoped tokens for every endpoint.",
            "idempotency_key": "core-answer-001",
            "expected_blueprint_version": session["blueprint_version"],
        },
        headers=_headers(),
    )
    assert answered.status_code == 200
    body = answered.json()
    assert body["blueprint_version"] > session["blueprint_version"]
    assert body["session_status"] in {"QUESTIONING", "VALIDATING", "CONFLICT_RESOLUTION"}


def test_intent_forge_answer_returns_409_on_version_conflict(forge_client) -> None:
    """Intent Forge answer endpoint surfaces optimistic-lock conflicts as HTTP 409."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build inventory tracking", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    response = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/answers",
        json={
            "question_id": created["current_question"]["question_id"],
            "answer": "FIFO costing with nightly reconciliation.",
            "idempotency_key": "core-conflict-001",
            "expected_blueprint_version": 0,
        },
        headers=_headers(),
    )
    assert response.status_code == 409
    assert "version" in response.json()["detail"].lower()


def test_intent_forge_get_returns_session_for_owner(forge_client) -> None:
    """GET /intent-forge/sessions/{id} returns the public session view for the owner."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a recipe manager", "tier": "paid"},
        headers=_headers(user_id="alice"),
    ).json()
    fetched = client.get(
        f"/api/v1/intent-forge/sessions/{created['session_id']}",
        headers=_headers(user_id="alice"),
    )
    assert fetched.status_code == 200
    assert fetched.json()["session_id"] == created["session_id"]


def test_intent_forge_get_returns_403_for_owner_mismatch(forge_client) -> None:
    """Intent Forge GET enforces per-session ownership."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a photo gallery", "tier": "paid"},
        headers=_headers(user_id="alice"),
    ).json()
    denied = client.get(
        f"/api/v1/intent-forge/sessions/{created['session_id']}",
        headers=_headers(user_id="bob"),
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "session access denied"


# ── Grid spawn ───────────────────────────────────────────────────────────────


def test_grid_spawn_mock_grid_path_succeeds(mock_grid_client) -> None:
    """POST /grid/spawn uses mock executor path and returns spawned sprint metadata."""
    client, _workers, tmp_path, store = mock_grid_client
    snapshot = store.prepare("Terminal smoke test project", owner_user_id="terminal-user")
    armed = store.assign_swarm(snapshot.session_id, 1)

    purchase = client.post(
        "/api/v1/blueprint/purchase",
        json={"workers": 1, "nodes": [{"id": "a"}]},
        headers={"X-User-Id": "terminal-user"},
    ).json()

    response = client.post(
        "/api/v1/grid/spawn",
        json={
            "workers": 1,
            "sprint_token": purchase["sprint_token"],
            "session_id": armed.session_id,
            "task": "Terminal smoke test project",
        },
        headers=_spawn_headers(user_id="terminal-user", idempotency_key="core-mock-spawn"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "spawned"
    assert payload["sprint_id"]
    assert payload["count"] == 1
    session_workers = tmp_path / ".gaijinn" / "sessions" / armed.session_id / ".gaijinn" / "workers"
    log_text = (session_workers / "worker-001" / "output.log").read_text(encoding="utf-8")
    assert "Executor: mock" in log_text


def test_grid_spawn_missing_executor_returns_503(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-mock spawn fails with 503 before charging when no executor is available."""
    import aoc_supervisor.api as api
    import aoc_supervisor.billing as billing
    from aoc_supervisor.billing import LocalFileLedgerStorageProvider, clear_sprint_tokens

    monkeypatch.delenv("GAIJINN_MOCK_GRID", raising=False)
    monkeypatch.setenv("GAIJINN_ALLOW_INSECURE_LOCAL", "1")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
    lock_path = tmp_path / ".aoc" / "billing" / "accounts.lock"
    provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)
    provider.write_ledger({"alice": {"balance": "100.00", "status": "active"}})

    workers_dir = tmp_path / ".gaijinn" / "workers"
    workers_dir.mkdir(parents=True)
    (workers_dir / "manifest.json").write_text(
        json.dumps({"worker_details": [{"worker_id": "worker-001", "status": "created"}]}),
        encoding="utf-8",
    )
    (workers_dir / "worker-001").mkdir()
    (workers_dir / "worker-001" / "output.log").write_text("", encoding="utf-8")

    clear_sprint_tokens()
    with (
        patch.object(api, "DEFAULT_LEDGER_STORAGE", provider),
        patch.object(api, "ROOT_DIR", tmp_path),
        patch.object(api, "WORKERS_DIR", workers_dir),
        patch.object(api, "SCRATCH_DIR", tmp_path / ".gaijinn" / "scratch"),
        TestClient(api.app) as client,
    ):
        purchase = client.post(
            "/api/v1/blueprint/purchase",
            json={"workers": 1, "nodes": [{"id": "a"}]},
            headers={"X-User-Id": "alice"},
        ).json()
        balance_after_purchase = provider.read_ledger()["alice"]["balance"]
        sprint_token = purchase["sprint_token"]

        response = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": sprint_token},
            headers=_spawn_headers(idempotency_key="core-no-executor"),
        )

    assert response.status_code == 503
    assert "GAIJINN_MOCK_GRID" in response.json()["detail"]
    assert provider.read_ledger()["alice"]["balance"] == balance_after_purchase
    with billing._SPRINT_TOKEN_LOCK:
        assert billing._SPRINT_TOKENS[sprint_token]["used"] is False


def test_orchestrate_swarm_success_arms_workers(mock_grid_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /orchestrate/swarm materializes workers for a prepared session."""
    client, _workers, _tmp, store = mock_grid_client

    def fake_run(project_root: Path, *args: str, **_kwargs) -> None:
        if args and args[0] == "plan":
            blueprint = {
                "schema_version": 1,
                "blueprint_mode": "graph",
                "work_units": [{"id": "WU-001", "title": "Core module", "allowed_paths": ["src/"]}],
            }
            path = project_root / ".gaijinn" / "blueprint.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(blueprint), encoding="utf-8")
        if args and args[0] == "run-grid":
            workers_dir = project_root / ".gaijinn" / "workers"
            workers_dir.mkdir(parents=True, exist_ok=True)
            (workers_dir / "manifest.json").write_text(
                json.dumps({"schema_version": 1, "worker_count": 1, "worker_details": [{"worker_id": "worker-001"}]}),
                encoding="utf-8",
            )
            (workers_dir / "worker-001").mkdir(exist_ok=True)

    import aoc_supervisor.api as api
    monkeypatch.setitem(api._session_store.advance_phase.__globals__, "_run_gaijinn", fake_run)

    prepared = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": "Build a tic-tac-toe game"},
        headers={"X-User-Id": "terminal-user"},
    ).json()
    response = client.post(
        "/api/v1/orchestrate/swarm",
        json={"session_id": prepared["session_id"], "workers": 1},
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workers_ready"] == 1
    assert payload["phase"] == "ready_to_deploy"


def test_orchestrate_session_get_returns_public_snapshot(mock_grid_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /orchestrate/session/{id} returns stealth session stats for the owner."""
    client, _workers, _tmp, _store = mock_grid_client

    def fake_run(project_root: Path, *args: str, **_kwargs) -> None:
        if args and args[0] == "plan":
            blueprint = {
                "schema_version": 1,
                "blueprint_mode": "graph",
                "work_units": [{"id": "WU-001", "title": "Rules engine", "allowed_paths": ["src/rules/"]}],
            }
            (project_root / ".gaijinn").mkdir(parents=True, exist_ok=True)
            (project_root / ".gaijinn" / "blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")

    import aoc_supervisor.api as api
    monkeypatch.setitem(api._session_store.advance_phase.__globals__, "_run_gaijinn", fake_run)
    prepared = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": "Build a notes app"},
        headers={"X-User-Id": "terminal-user"},
    ).json()

    response = client.get(
        f"/api/v1/orchestrate/session/{prepared['session_id']}",
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == prepared["session_id"]
    assert payload["work_units"] == 1
    assert "blueprint.json" not in json.dumps(payload)


def test_prepare_after_intent_forge_handoff_succeeds(forge_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """HANDED_OFF intent-forge sessions can seed orchestrate prepare."""
    client, _service = forge_client

    def fake_run(project_root: Path, *args: str, **_kwargs) -> None:
        if args and args[0] == "plan":
            blueprint = {
                "schema_version": 1,
                "blueprint_mode": "graph",
                "work_units": [{"id": "WU-001", "title": "CLI export", "allowed_paths": ["src/"]}],
            }
            (project_root / ".gaijinn").mkdir(parents=True, exist_ok=True)
            (project_root / ".gaijinn" / "blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")

    import aoc_supervisor.api as api
    monkeypatch.setitem(api._session_store.advance_phase.__globals__, "_run_gaijinn", fake_run)

    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a markdown note CLI", "tier": "free"},
        headers=_headers(),
    ).json()
    version = created["blueprint_version"]
    confirmed = client.post(
        f"/api/v1/intent-forge/sessions/{created['session_id']}/handoff",
        json={
            "action": "confirm",
            "confirmation": "Proceed",
            "idempotency_key": "core-handoff-confirm",
            "expected_blueprint_version": version,
        },
        headers=_headers(),
    )
    assert confirmed.status_code == 200
    version = confirmed.json()["blueprint_version"]
    accepted = client.post(
        f"/api/v1/intent-forge/sessions/{created['session_id']}/handoff",
        json={
            "action": "accept",
            "idempotency_key": "core-handoff-accept",
            "expected_blueprint_version": version,
        },
        headers=_headers(),
    )
    assert accepted.status_code == 200
    assert accepted.json()["session_status"] == "HANDED_OFF"

    prepare = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": created["original_prompt"], "intent_forge_session_id": created["session_id"]},
        headers=_headers(),
    )
    assert prepare.status_code == 200
    payload = prepare.json()
    assert payload["session_id"] == created["session_id"]
    assert payload["work_units"] >= 1


def test_grid_merge_status_for_prepared_session(mock_grid_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /grid/merge/status reports pipeline state without mutating the session."""
    client, _workers, _tmp, _store = mock_grid_client

    def fake_run(project_root: Path, *args: str, **_kwargs) -> None:
        if args and args[0] == "plan":
            blueprint = {
                "schema_version": 1,
                "blueprint_mode": "graph",
                "work_units": [{"id": "WU-001", "title": "Worker task", "allowed_paths": ["src/"]}],
            }
            (project_root / ".gaijinn").mkdir(parents=True, exist_ok=True)
            (project_root / ".gaijinn" / "blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")

    import aoc_supervisor.api as api
    monkeypatch.setitem(api._session_store.advance_phase.__globals__, "_run_gaijinn", fake_run)
    prepared = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": "Terminal smoke test project"},
        headers={"X-User-Id": "terminal-user"},
    ).json()

    response = client.get(f"/api/v1/grid/merge/status?session_id={prepared['session_id']}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == prepared["session_id"]
    assert payload["phase"] == "awaiting_swarm"
    assert "merge_pipeline" in payload


def test_quote_returns_integrity_pricing(mock_grid_client) -> None:
    """POST /quote returns deploy and sprint fees without charging the ledger."""
    client, _workers, tmp_path, _store = mock_grid_client
    import aoc_supervisor.api as api
    from aoc_supervisor.billing import LocalFileLedgerStorageProvider

    ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
    provider = LocalFileLedgerStorageProvider(ledger_path, tmp_path / ".aoc" / "billing" / "accounts.lock")
    provider.write_ledger({"terminal-user": {"balance": "100.00", "status": "active"}})
    with patch.object(api, "DEFAULT_LEDGER_STORAGE", provider):
        starting = provider.read_ledger()["terminal-user"]["balance"]
        response = client.post(
            "/api/v1/quote",
            json={"workers": 2, "nodes": [{"id": "a"}, {"id": "b"}], "curvature_meta": {"shadow_bridge_count": 0}},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["deploy_fee"] > 0
    assert payload["sprint_fee"] > 0
    assert provider.read_ledger()["terminal-user"]["balance"] == starting


def test_council_show_returns_markdown(mock_grid_client) -> None:
    """GET /council/show exposes the shared council thread for the terminal."""
    client, _workers, _tmp, _store = mock_grid_client
    response = client.get("/api/v1/council/show")
    assert response.status_code == 200
    payload = response.json()
    assert "markdown" in payload
    assert "path" in payload


def test_full_mock_grid_sprint_flow_completes(mock_grid_client) -> None:
    """End-to-end orchestrate prepare → swarm → spawn completes under mock grid."""
    client, _workers, tmp_path, _store = mock_grid_client
    driver = UiIntentDriver(client)
    observation = driver.run_smoke_scenario("flow.intent_swarm_deploy_mock")
    assert observation.status == "completed"
    assert observation.prepare is not None
    assert observation.prepare.work_units >= 1
    session_workers = tmp_path / ".gaijinn" / "sessions" / observation.session_id / ".gaijinn" / "workers"
    assert (session_workers / "worker-001" / "output.log").exists()


def test_mock_sprint_merge_deliverable_and_report(mock_grid_client) -> None:
    """POST /grid/merge plus deliverable/report/diff endpoints after a mock sprint."""
    client, _workers, _tmp, _store = mock_grid_client
    driver = UiIntentDriver(client)
    observation = driver.run_smoke_scenario("flow.intent_swarm_deploy_mock")
    assert observation.status == "completed"
    assert observation.merge is not None
    pipeline = observation.merge["merge_pipeline"]
    assert pipeline["phase"] == "completed"
    assert pipeline["merged"] >= 1

    status = client.get(f"/api/v1/grid/merge/status?session_id={observation.session_id}")
    assert status.status_code == 200
    assert status.json()["merge_pipeline"]["phase"] == "completed"

    deliverable = client.get(f"/api/v1/grid/deliverable?session_id={observation.session_id}")
    assert deliverable.status_code == 200
    assert deliverable.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(deliverable.content)) as archive:
        names = set(archive.namelist())
    assert ".gaijinn/session.json" in names

    report = client.get(f"/api/v1/grid/merge/report?session_id={observation.session_id}")
    assert report.status_code == 200
    assert report.json()["report"]["summary"]["merged"] >= 1

    diff = client.get(f"/api/v1/grid/diff?session_id={observation.session_id}")
    assert diff.status_code == 200
    assert "available" in diff.json()


def test_analyze_post_rejects_non_object_manifest(mock_grid_client) -> None:
    """POST /analyze returns 422 when the metrics manifest is not a JSON object."""
    client, _workers, _tmp, _store = mock_grid_client
    response = client.post("/api/v1/analyze", json=[{"node": "a"}])
    assert response.status_code == 422
    assert "violating_nodes" in response.json()["detail"]


def test_analyze_post_returns_stealth_response(mock_grid_client) -> None:
    """POST /analyze validates payload and returns sanitized structural status."""
    client, _workers, _tmp, _store = mock_grid_client
    response = client.post(
        "/api/v1/analyze",
        json={
            "status": "SUCCESS",
            "gravity_meta": {"rejected_nodes": [], "nodes": {"src/main.py": {"gravity": 0.9}}},
            "curvature_meta": {"shadow_bridge_count": 0, "edges": {}},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["billing"]["charged"] is False
    assert "curvature" not in json.dumps(payload)


def test_moat_parse_returns_operation_profile(mock_grid_client) -> None:
    """POST /moat/parse maps prompts to deterministic operation profiles."""
    client, _workers, _tmp, _store = mock_grid_client
    response = client.post(
        "/api/v1/moat/parse",
        json={"prompt": "scan the repository for structural drift"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "prohibitions" in payload
    assert payload["prohibitions"]


def test_project_telemetry_endpoint(mock_grid_client) -> None:
    """GET /project/telemetry exposes stealth governance summary for the host project."""
    client, _workers, tmp_path, _store = mock_grid_client
    metrics = {
        "status": "SUCCESS",
        "gravity_meta": {
            "nodes": {"src/app.py": {"gravity": 0.8, "automatic_rejection": False}},
            "rejected_nodes": [],
            "hard_floor": 0.2,
        },
        "curvature_meta": {"edges": {}, "shadow_bridge_count": 0},
    }
    gaijinn_dir = tmp_path / ".gaijinn"
    gaijinn_dir.mkdir(parents=True, exist_ok=True)
    (gaijinn_dir / "metrics_manifest.json").write_text(json.dumps(metrics), encoding="utf-8")

    telemetry = client.get("/api/v1/project/telemetry")
    assert telemetry.status_code == 200
    body = telemetry.json()
    assert "topology_preview" in body
    assert body["node_count"] >= 0

    analyze = client.get("/api/v1/analyze")
    assert analyze.status_code == 200
    assert analyze.json().get("node_count") is not None


def test_intent_forge_pause_and_resume(forge_client) -> None:
    """Intent Forge pause/resume endpoints preserve questioning state across calls."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a CRM with audit logs", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    paused = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/pause",
        json={
            "idempotency_key": "core-pause-001",
            "expected_blueprint_version": created["blueprint_version"],
        },
        headers=_headers(),
    )
    assert paused.status_code == 200
    assert paused.json()["session_status"] == "PAUSED"
    resumed = client.post(
        f"/api/v1/intent-forge/sessions/{sid}/resume",
        json={
            "idempotency_key": "core-resume-001",
            "expected_blueprint_version": paused.json()["blueprint_version"],
        },
        headers=_headers(),
    )
    assert resumed.status_code == 200
    assert resumed.json()["session_status"] == "QUESTIONING"


def test_grid_status_reports_sprint_progress(mock_grid_client) -> None:
    """GET /grid/status returns worker rows and sprint aggregate state."""
    client, _workers, _tmp, _store = mock_grid_client
    driver = UiIntentDriver(client)
    purchase = driver.purchase(2)
    spawn = driver.spawn(workers=2, sprint_token=purchase["sprint_token"], task="status smoke")
    status = client.get(f"/api/v1/grid/status?sprint_id={spawn['sprint_id']}")
    assert status.status_code == 200
    payload = status.json()
    assert payload["total"] >= 2
    assert payload["sprint"]["sprint_id"] == spawn["sprint_id"]
    assert "assigned_work_units" in payload["workers"][0]


def test_grid_stream_reads_worker_log(mock_grid_client) -> None:
    """GET /grid/stream/{cell} streams existing worker output.log contents."""
    client, workers_dir, _tmp, _store = mock_grid_client
    driver = UiIntentDriver(client)
    purchase = driver.purchase(1)
    driver.spawn(workers=1, sprint_token=purchase["sprint_token"], task="stream smoke")
    with client.stream("GET", "/api/v1/grid/stream/worker-001") as response:
        assert response.status_code == 200
        lines = [line for line in response.iter_lines() if line]
        if lines:
            assert any("GAIJINN GRID SPAWN" in line for line in lines)


def test_grid_logs_returns_worker_output(mock_grid_client) -> None:
    """GET /grid/logs surfaces worker output logs after mock spawn."""
    client, workers_dir, _tmp, _store = mock_grid_client
    driver = UiIntentDriver(client)
    purchase = driver.purchase(1)
    driver.spawn(workers=1, sprint_token=purchase["sprint_token"], task="logs smoke")
    logs = client.get("/api/v1/grid/logs")
    assert logs.status_code == 200
    payload = logs.json()["logs"]
    assert "worker-001" in payload
    assert "GAIJINN GRID SPAWN" in payload["worker-001"]


def test_council_say_and_ledger(mock_grid_client) -> None:
    """Council say + ledger endpoints append and tail shared bridge messages."""
    client, _workers, tmp_path, _store = mock_grid_client
    bridge = tmp_path / ".gaijinn" / "bridge"
    bridge.mkdir(parents=True, exist_ok=True)
    (bridge / "council.jsonl").write_text("", encoding="utf-8")
    (bridge / "council.md").write_text("# Council\n", encoding="utf-8")

    said = client.post("/api/v1/council/say", json={"text": "Ship the API slice", "author": "user"})
    assert said.status_code == 200
    assert said.json()["posted"] is True

    ledger = client.get("/api/v1/council/ledger?tail=5")
    assert ledger.status_code == 200
    rows = ledger.json()["rows"]
    assert rows and "Ship the API slice" in rows[-1]["msg"]


def test_preflight_merge_check_returns_structured_gate(mock_grid_client) -> None:
    """POST /preflight evaluates merge readiness for a worker/session pair."""
    client, _workers, _tmp, store = mock_grid_client
    snapshot = store.prepare("Terminal smoke test project", owner_user_id="terminal-user")
    armed = store.assign_swarm(snapshot.session_id, 1)
    response = client.post(
        "/api/v1/preflight",
        json={
            "session_id": armed.session_id,
            "worker_id": "worker-001",
            "target_branch": "gaijinn/integration",
        },
    )
    assert response.status_code in {200, 422}
    payload = response.json()
    assert "allow_merge" in payload
    assert payload["session_id"] == armed.session_id


def test_blueprint_deliberate_streams_prepare_stages(mock_grid_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /blueprint/deliberate SSE emits teleology phases from prepare callbacks."""
    client, _workers, _tmp, store = mock_grid_client
    session_id = "delibsession01"

    def fake_prepare(
        self: OrchestrateSessionStore,
        intent: str,
        phases: object = None,
        loaded_context: object = None,
        *,
        on_step: object = None,
        layer1_timeout: int | None = None,
        **kwargs: object,
    ) -> SessionSnapshot:
        session_root = self.sessions_dir / session_id
        gaijinn_dir = session_root / ".gaijinn"
        gaijinn_dir.mkdir(parents=True, exist_ok=True)
        blueprint = {
            "schema_version": 1,
            "blueprint_mode": "graph",
            "work_units": [{"id": "WU-001", "title": "Core", "allowed_paths": ["src/"]}],
            "gateways": ["handoff:api"],
        }
        (gaijinn_dir / "blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")
        (gaijinn_dir / "intent.txt").write_text(intent + "\n", encoding="utf-8")
        for step in (
            "session_seed",
            "init_start",
            "init_complete",
            "scan_start",
            "scan_complete",
            "analyze_start",
            "analyze_complete",
            "compile_prompt_start",
            "compile_prompt_complete",
            "plan_start",
            "plan_complete",
        ):
            if on_step is not None:
                on_step(step, {"session_root": str(session_root)})
        self._active[session_id] = session_root
        return SessionSnapshot(
            session_id=session_id,
            intent=intent,
            project_root=session_root,
            work_units=1,
            high_risk_units=0,
            workers_ready=0,
            phase="awaiting_swarm",
        )

    monkeypatch.setattr(OrchestrateSessionStore, "prepare", fake_prepare)

    with client.stream(
        "GET",
        "/api/v1/blueprint/deliberate",
        params={"intent": "Build a notes app", "stream_format": "canonical"},
    ) as response:
        assert response.status_code == 200
        events: list[str] = []
        for line in response.iter_lines():
            if line:
                events.append(line)
            if len(events) >= 6:
                break
    joined = "\n".join(events)
    assert joined.startswith("data:")
    assert "delibsession01" in joined or "sequence" in joined


def test_websocket_intent_forge_replay_events(forge_client) -> None:
    """WebSocket /ws/intent-forge replays canonical session events for a session."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a recipe manager", "tier": "paid"},
        headers=_headers(),
    ).json()
    sid = created["session_id"]
    with client.websocket_connect(f"/ws/intent-forge?session_id={sid}&last_sequence=-1&blueprint_version=0") as ws:
        first = ws.receive_json()
        assert first["event_type"] == "intent.session.created"
        snapshot = ws.receive_json()
        while snapshot.get("event_type") != "session.snapshot":
            snapshot = ws.receive_json()
        assert snapshot["data"]["replay"] is True


def test_intent_forge_finalize_force(forge_client) -> None:
    """POST /intent-forge/sessions/{id}/finalize can force completion while questioning."""
    client, _service = forge_client
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a chat app", "tier": "paid"},
        headers=_headers(),
    ).json()
    finalized = client.post(
        f"/api/v1/intent-forge/sessions/{created['session_id']}/finalize",
        json={
            "idempotency_key": "core-finalize-force",
            "expected_blueprint_version": created["blueprint_version"],
            "force": True,
        },
        headers=_headers(),
    )
    assert finalized.status_code == 200
    assert finalized.json()["session_status"] == "FINAL_CONFIRMATION"


def test_blueprint_purchase_returns_sprint_token(mock_grid_client) -> None:
    """POST /blueprint/purchase charges deploy fee and returns an entitlement token."""
    client, _workers, tmp_path, _store = mock_grid_client
    import aoc_supervisor.api as api
    from aoc_supervisor.billing import LocalFileLedgerStorageProvider

    ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
    provider = LocalFileLedgerStorageProvider(ledger_path, tmp_path / ".aoc" / "billing" / "accounts.lock")
    provider.write_ledger({"terminal-user": {"balance": "100.00", "status": "active"}})
    body = {"workers": 1, "nodes": [{"id": "a"}], "curvature_meta": {"shadow_bridge_count": 0}}
    with patch.object(api, "DEFAULT_LEDGER_STORAGE", provider):
        before = float(provider.read_ledger()["terminal-user"]["balance"])
        response = client.post("/api/v1/blueprint/purchase", json=body, headers={"X-User-Id": "terminal-user"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["sprint_token"]
    after = float(provider.read_ledger()["terminal-user"]["balance"])
    assert after < before


# ── API key middleware ────────────────────────────────────────────────────────


def test_health_is_public_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/v1/health remains reachable when mutating routes require API keys."""
    import aoc_supervisor.api as api

    monkeypatch.delenv("GAIJINN_ALLOW_INSECURE_LOCAL", raising=False)
    monkeypatch.setenv("GAIJINN_API_KEY", "super-secret-key")
    with TestClient(api.app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert "active_sprints" in body
    assert "blocked" in body


def test_mutating_route_rejects_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Protected POST routes reject requests without a valid API key."""
    import aoc_supervisor.api as api

    monkeypatch.delenv("GAIJINN_ALLOW_INSECURE_LOCAL", raising=False)
    monkeypatch.setenv("GAIJINN_API_KEY", "super-secret-key")
    with TestClient(api.app) as client:
        response = client.post("/api/v1/orchestrate/prepare", json={"intent": "demo"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"
