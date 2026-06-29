"""Loom Intent Mapping contract tests — validate specs another AI will implement against."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
UI_DIR = REPO_ROOT / "ui"

LOOM_MAPS = (
    "loom-system-intent-map.json",
    "loom-pipeline-intent-map.json",
    "loom-intent-forge-intent-map.json",
)

REQUIRED_LOOM_TICKETS = (
    "LOOM-201",
    "LOOM-203",
    "LOOM-209",
)

PIPELINE_ACTIONS = (
    "intake.start_session",
    "question.submit_answer",
    "handoff.confirm",
    "handoff.accept",
    "teleology.deliberate",
    "blueprint.synthesize",
    "orchestrate.prepare",
    "deploy.sprint",
)


def _load(name: str) -> dict:
    return json.loads((UI_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", LOOM_MAPS)
def test_loom_maps_are_valid_json(name: str) -> None:
    payload = _load(name)
    assert payload.get("system") == "loom" or name == "loom-pipeline-intent-map.json"
    assert "description" in payload


def test_loom_system_declares_canonical_journey() -> None:
    system = _load("loom-system-intent-map.json")
    journey = system["canonical_user_journey"]["narrative"]
    assert "Vision" in journey[0]
    assert "Teleology" in journey[2]
    assert "Blueprint" in journey[3]


def test_loom_system_lists_implementation_tickets() -> None:
    tickets = _load("loom-system-intent-map.json")["_ai_blueprint"]["implementation_tickets"]
    ids = {item["id"] for item in tickets}
    for required in REQUIRED_LOOM_TICKETS:
        assert required in ids


def test_loom_pipeline_declares_full_action_chain() -> None:
    actions = _load("loom-pipeline-intent-map.json")["actions"]
    for action_id in PIPELINE_ACTIONS:
        assert action_id in actions, f"missing pipeline action {action_id}"


def test_loom_pipeline_synthesis_not_implemented_yet() -> None:
    synthesis = _load("loom-pipeline-intent-map.json")["actions"]["blueprint.synthesize"]
    assert synthesis["status"] == "not_implemented"
    assert synthesis["algorithm_binding"]["ticket"] == "LOOM-203"


def test_loom_pipeline_full_scenario_is_shipped() -> None:
    scenarios = {s["id"]: s for s in _load("loom-pipeline-intent-map.json")["smoke_scenarios"]}
    full = scenarios["flow.loom_full_pipeline_mock"]
    assert full["implementation_status"].startswith("shipped")
    assert "teleology.deliberate" in json.dumps(full["steps"])
    assert "blueprint.synthesize" in json.dumps(full["steps"])


def test_loom_intent_forge_blocks_raw_prepare() -> None:
    invariants = _load("loom-intent-forge-intent-map.json")["invariants"]
    assert any("no_prepare_here" in item["id"] for item in invariants)


def test_loom_c01_prepare_gate(mock_grid_client, monkeypatch: pytest.MonkeyPatch) -> None:
    client, _workers, _tmp, store = mock_grid_client
    payload = {"intent": "Build an app", "phases": ["backend"]}
    headers = {"X-User-Id": "terminal-user"}

    class _Prepared:
        def to_public_dict(self) -> dict:
            return {"session_id": "loom-c01", "work_units": 1}

    monkeypatch.setattr(store, "prepare", lambda *_args, **_kwargs: _Prepared())
    monkeypatch.setenv("GAIJINN_ALLOW_RAW_INTENT_PREPARE", "")
    rejected = client.post("/api/v1/orchestrate/prepare", json=payload, headers=headers)
    assert rejected.status_code == 409
    assert "Loom prepare gate" in rejected.json()["detail"]

    monkeypatch.setenv("GAIJINN_ALLOW_RAW_INTENT_PREPARE", "1")
    allowed = client.post("/api/v1/orchestrate/prepare", json=payload, headers=headers)
    assert allowed.status_code == 200


def test_loom_maps_served_under_contracts_route() -> None:
    from aoc_supervisor.routers.static_ui import _CONTRACT_PATHS

    for name in LOOM_MAPS:
        assert name in _CONTRACT_PATHS
        assert _CONTRACT_PATHS[name].exists()


def test_loom_codex_slices_declared_and_docs_exist() -> None:
    system = _load("loom-system-intent-map.json")
    slices = system["_ai_blueprint"]["codex_slices"]
    assert len(slices) == 21
    master = REPO_ROOT / "docs" / "codex-tasks" / "loom" / "MASTER-loom-codex.md"
    assert master.exists()
    for item in slices:
        doc = REPO_ROOT / item["doc"]
        assert doc.exists(), f"missing codex task {item['id']}: {doc}"


def test_loom_codex_wave_1_parallel_disjoint() -> None:
    system = _load("loom-system-intent-map.json")
    wave1 = set(system["_ai_blueprint"]["codex_parallel_wave_1"])
    slices = {s["id"]: s for s in system["_ai_blueprint"]["codex_slices"]}
    assert wave1 <= set(slices)
    assert len(wave1) == 5
    deferred = system["_ai_blueprint"].get("codex_ui_slices_deferred", [])
    assert "C12" in deferred
    assert "C17" in deferred
