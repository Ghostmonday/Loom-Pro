"""AI-driven UI smoke tests via loom-ui-intent-map.json (mirror driver; no browser)."""

from __future__ import annotations

import json
from pathlib import Path

from aoc_supervisor.repo_paths import PLACEHOLDER_HTML_PATH
from aoc_supervisor.ui_intent import UiIntentDriver, load_ui_intent_map


def test_unified_shell_serves_sandbox() -> None:
    assert PLACEHOLDER_HTML_PATH.exists()
    html = PLACEHOLDER_HTML_PATH.read_text(encoding="utf-8")
    assert "Loom Blueprint Workbench" in html
    assert "shell.js" in html  # unified shell JS registered


def test_ui_intent_map_v2_phases() -> None:
    catalog = load_ui_intent_map()
    assert catalog["schema_version"] == 5
    assert "state_machine" in catalog
    assert "optimization_goal" in catalog
    assert "intent_forge" in catalog
    assert catalog["intent_forge"]["api_prefix"] == "/api/v1/intent-forge"
    assert "HANDED_OFF" in catalog["intent_forge"]["states"]
    assert catalog["phases"][:4] == ["awaiting_intent", "blueprinting", "awaiting_swarm", "sprinting"]
    assert catalog["elements"]["controls.auto_approve"]["user_visible"] is False
    assert catalog["_ai_blueprint"]["layers"]["terminal_ui"]["status"] == "contract_only"
    scenario_ids = {s["id"] for s in catalog["smoke_scenarios"]}
    assert "flow.intent_swarm_deploy_mock" in scenario_ids
    assert "flow.intent_forge_free_provisional" in scenario_ids


def test_handoff_chat_submit_intent_contract_postconditions() -> None:
    catalog = load_ui_intent_map()
    action = catalog["actions"]["chat.submit_intent"]
    prepare_body = catalog["actions"]["orchestrate.prepare"]["api"]["body"]
    assert action["preconditions"] == ["forge_session_id present from query or sessionStorage handoff"]
    assert "raw chat.submit_intent blocked before POST when forge_session_id missing" in action["postconditions"]
    assert "orchestrate.prepare body.intent_forge_session_id == forge_session_id" in action["postconditions"]
    assert prepare_body["intent_forge_session_id"] == "string"


def test_handoff_prepare_rejects_raw_chat_submit_without_forge_session(mock_grid_client, monkeypatch) -> None:
    client, _workers, _tmp, _store = mock_grid_client
    monkeypatch.setenv("GAIJINN_ALLOW_RAW_INTENT_PREPARE", "")
    response = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": "Build a tic-tac-toe game", "phases": ["backend"]},
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 409
    assert "intent_forge_session_id" in response.json()["detail"]


def test_prepare_returns_session_stats(mock_grid_client) -> None:
    client, _workers, _tmp, _store = mock_grid_client
    driver = UiIntentDriver(client)
    prep = driver.prepare("Build a tic-tac-toe game")
    assert prep.session_id
    assert prep.work_units >= 1
    assert prep.suggested_swarm
    assert prep.recommended_swarm >= 1
    assert prep.phases == ["backend"]
    assert prep.current_phase == "backend"
    assert prep.phase_count == 1


def test_prepare_rejects_invalid_phases(mock_grid_client) -> None:
    client, _workers, _tmp, _store = mock_grid_client
    invalid_payloads = [
        {"intent": "Build a tic-tac-toe game", "phases": []},
        {"intent": "Build a tic-tac-toe game", "phases": ["backend", "docs"]},
        {"intent": "Build a tic-tac-toe game", "phases": "backend"},
    ]
    for payload in invalid_payloads:
        response = client.post("/api/v1/orchestrate/prepare", json=payload, headers={"X-User-Id": "terminal-user"})
        assert response.status_code == 400


def test_prepare_normalizes_phase_order_api(mock_grid_client) -> None:
    client, _workers, _tmp, _store = mock_grid_client
    response = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": "Build a tic-tac-toe game", "phases": ["frontend", "backend"]},
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phases"] == ["backend", "frontend"]
    assert data["current_phase"] == "backend"
    assert data["phase_count"] == 2


def test_prepare_rejects_frontend_testing_without_loaded_backend(mock_grid_client) -> None:
    client, _workers, _tmp, _store = mock_grid_client
    response = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": "Build a tic-tac-toe game", "phases": ["testing", "frontend"]},
        headers={"X-User-Id": "terminal-user"},
    )
    assert response.status_code == 400
    assert "loaded context" in response.json()["detail"].lower()


def test_full_flow_intent_swarm_deploy_mock(mock_grid_client) -> None:
    client, _workers, tmp_path, _store = mock_grid_client
    driver = UiIntentDriver(client)
    observation, assertions = driver.run_and_verify_scenario("flow.intent_swarm_deploy_mock")
    assert observation.status == "completed"
    assert observation.prepare is not None
    assert observation.prepare.work_units >= 1
    assert all(item.passed for item in assertions)
    session_workers = tmp_path / ".gaijinn" / "sessions" / observation.session_id / ".gaijinn" / "workers"
    assert (session_workers / "worker-001" / "output.log").exists()
    assert (session_workers / "worker-002" / "output.log").exists()


def test_grid_view_consistency_scenario(mock_grid_client) -> None:
    client, _workers, _tmp, _store = mock_grid_client
    driver = UiIntentDriver(client)
    observation, assertions = driver.run_and_verify_scenario("grid.view_consistency", workers=3)
    assert observation.sprint_id
    assert all(item.passed for item in assertions)


def test_session_spawn_grid_status_lists_all_workers(mock_grid_client) -> None:
    client, _workers, _tmp, _store = mock_grid_client
    driver = UiIntentDriver(client)
    prep = driver.prepare("Build a tic-tac-toe game")
    driver.assign_swarm(3)
    purchase = driver.purchase(3, assignment_count=max(prep.work_units, 3))
    spawn = driver.spawn(
        workers=3,
        sprint_token=purchase["sprint_token"],
        task="Build a tic-tac-toe game",
        session_id=prep.session_id,
    )
    observation = driver.wait_for_sprint_terminal(str(spawn["sprint_id"]), workers=3, timeout_s=90)
    status = driver.grid_status(str(spawn["sprint_id"]))
    worker_names = [w["name"] for w in status.get("workers", [])]
    assert len(worker_names) >= 3
    assert "worker-003" in worker_names
    assert observation.status == "completed"


def test_command_engine_intent_map_loads() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "ui" / "command-engine-ui-intent-map.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["surface"] == "command-engine"
    assert "intake.begin" in payload["elements"]


def test_vault_intent_map_extends_terminal() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "vaults" / "gaijinn-memory-fs" / "ui" / "vault-ui-intent-map.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["project_kind"] == "obsidian-vault"
    assert "governance" in payload


def test_advance_phase_api_reblueprints_without_stub(mock_grid_client, monkeypatch) -> None:
    client, _workers, _tmp, store = mock_grid_client
    session_id = "ddeeff001122"
    session_root = store.sessions_dir / session_id
    gaijinn_dir = session_root / ".gaijinn"
    gaijinn_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "session_id": session_id,
        "owner_user_id": "terminal-user",
        "intent": "Build a tic-tac-toe game",
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
        "work_stream_titles": ["Game rules and state"],
        "swarm_rationale": "demo",
    }
    (gaijinn_dir / "session.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    store._active[session_id] = session_root

    import aoc_supervisor.api as api

    monkeypatch.setitem(
        api._session_store.advance_phase.__globals__,
        "_run_blueprint_pipeline",
        lambda *_args, **_kwargs: (1, 0, ("Desktop UI",), "intent", ("Desktop UI",)),
    )

    driver = UiIntentDriver(client)
    data = driver.advance_phase(session_id)
    assert data["phase"] == "awaiting_swarm"
    assert data["current_phase"] == "frontend"
    assert data["workers_ready"] == 0
    assert "blueprint stub" not in (data.get("message") or "").lower()
    assert data["loaded_context"]["backend"]["prior_session_id"] == session_id


def test_grid_status_includes_worker_assignment_metadata(mock_grid_client) -> None:
    client, _workers, _tmp, _store = mock_grid_client
    driver = UiIntentDriver(client)
    purchase = driver.purchase(2)
    spawn = driver.spawn(workers=2, sprint_token=purchase["sprint_token"], task="smoke")
    status = driver.grid_status(str(spawn["sprint_id"]))
    workers = status.get("workers") or []
    assert len(workers) >= 2
    first = workers[0]
    assert "assigned_work_units" in first
    assert "spawned" in first
    assert "has_output" in first
    assert first["assigned_work_units"] == ["WU-001"]
