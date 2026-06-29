"""Tests for multi-phase advance_phase re-blueprint (GAIJINN-ENG-104)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aoc_supervisor.orchestrate_session import OrchestrateSessionStore


@pytest.fixture
def store(tmp_path: Path) -> OrchestrateSessionStore:
    return OrchestrateSessionStore(tmp_path)


def _seed_awaiting_next_phase(
    store: OrchestrateSessionStore,
    *,
    session_id: str = "aabbccddeeff",
    phases: list[str] | None = None,
    loaded_context: dict[str, dict[str, str]] | None = None,
    work_stream_titles: tuple[str, ...] = ("Service API layer", "Core project scaffold"),
) -> Path:
    phases = phases or ["backend", "frontend"]
    session_root = store.sessions_dir / session_id
    gaijinn_dir = session_root / ".gaijinn"
    gaijinn_dir.mkdir(parents=True, exist_ok=True)
    (session_root / "src").mkdir(parents=True, exist_ok=True)
    (gaijinn_dir / "intent.txt").write_text("Build a REST API backend service\n", encoding="utf-8")
    blueprint = {
        "schema_version": 1,
        "project_goal": "Build a REST API backend service",
        "blueprint_mode": "intent",
        "work_stream_titles": list(work_stream_titles),
        "work_units": [
            {"id": f"WU-{index:03d}", "title": title, "allowed_paths": [f"src/{index}/"]}
            for index, title in enumerate(work_stream_titles, start=1)
        ],
    }
    (gaijinn_dir / "blueprint.json").write_text(json.dumps(blueprint, indent=2) + "\n", encoding="utf-8")
    meta = {
        "session_id": session_id,
        "owner_user_id": "terminal-user",
        "intent": "Build a REST API backend service",
        "phase": "awaiting_next_phase",
        "phases": phases,
        "current_phase": phases[0],
        "pipeline_plan": {
            "phases": phases,
            "current_index": 0,
            "current_phase": phases[0],
            "completed_phases": [phases[0]],
        },
        "loaded_context": loaded_context or {},
        "blueprint_mode": "intent",
        "work_stream_titles": list(work_stream_titles),
        "work_units": len(work_stream_titles),
        "swarm_rationale": "demo",
        "workers_ready": 2,
        "selected_swarm": 2,
    }
    (gaijinn_dir / "session.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    workers_dir = gaijinn_dir / "workers"
    workers_dir.mkdir(parents=True, exist_ok=True)
    (workers_dir / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "worker_count": 2, "worker_details": [{}, {}]}),
        encoding="utf-8",
    )
    store._active[session_id] = session_root
    return session_root


def test_advance_without_merge_fails(store: OrchestrateSessionStore) -> None:
    snapshot = store.prepare("Terminal smoke test project", phases=["backend", "frontend"])
    with pytest.raises(ValueError, match="current phase must be merged before advancing"):
        store.advance_phase(snapshot.session_id)


def test_advance_backend_to_frontend_reblueprints_with_loaded_context(
    store: OrchestrateSessionStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "aabbccddeeff"
    session_root = _seed_awaiting_next_phase(store, session_id=session_id)
    phase_one_titles = ("Service API layer", "Core project scaffold")
    phase_two_titles = ("Desktop UI", "Editor UI and theming")

    def fake_pipeline(
        project_root: Path,
        intent: str,
        *,
        command_timeout: int | None = None,
        use_intent_blueprint: bool = False,
        loaded_context: dict | None = None,
    ) -> tuple[int, int, tuple[str, ...], str, tuple[str, ...]]:
        assert project_root == session_root
        assert "frontend UI integrating with backend context" in intent
        assert loaded_context is not None
        assert "backend" in loaded_context
        assert loaded_context["backend"]["prior_session_id"] == session_id
        blueprint = {
            "schema_version": 1,
            "project_goal": intent,
            "blueprint_mode": "intent",
            "loaded_context": loaded_context,
            "work_stream_titles": list(phase_two_titles),
            "work_units": [
                {"id": f"WU-{index:03d}", "title": title, "allowed_paths": [f"src/ui/{index}/"]}
                for index, title in enumerate(phase_two_titles, start=1)
            ],
        }
        blueprint_path = project_root / ".gaijinn" / "blueprint.json"
        blueprint_path.write_text(json.dumps(blueprint, indent=2) + "\n", encoding="utf-8")
        return len(phase_two_titles), 0, phase_two_titles, "intent", phase_two_titles

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_blueprint_pipeline", fake_pipeline)

    advanced = store.advance_phase(session_id)
    public = advanced.to_public_dict()
    meta = json.loads((session_root / ".gaijinn" / "session.json").read_text(encoding="utf-8"))
    blueprint = json.loads((session_root / ".gaijinn" / "blueprint.json").read_text(encoding="utf-8"))

    assert advanced.phase == "awaiting_swarm"
    assert advanced.current_phase == "frontend"
    assert advanced.workers_ready == 0
    assert advanced.work_stream_titles == phase_two_titles
    assert phase_two_titles != phase_one_titles
    assert public["pipeline_plan"]["current_index"] == 1
    assert "blueprint stub" not in (public.get("message") or "").lower()
    assert "blueprint ready" in (public.get("message") or "").lower()
    assert meta["loaded_context"]["backend"]["prior_session_id"] == session_id
    assert blueprint.get("loaded_context", {}).get("backend", {}).get("prior_session_id") == session_id
    assert not (session_root / ".gaijinn" / "workers").exists()


def test_advance_backend_testing_requires_loaded_frontend(store: OrchestrateSessionStore) -> None:
    session_id = "bbccddeeff00"
    _seed_awaiting_next_phase(store, session_id=session_id, phases=["backend", "testing"], loaded_context={})
    with pytest.raises(ValueError, match="requires loaded context first: frontend"):
        store.advance_phase(session_id)


def test_advance_phase_message_never_contains_stub(
    store: OrchestrateSessionStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "ccddeeff0011"
    session_root = _seed_awaiting_next_phase(
        store,
        session_id=session_id,
        phases=["backend", "frontend", "testing"],
    )

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
        return 1, 0, titles, "intent", titles

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_blueprint_pipeline", fake_pipeline)

    advanced = store.advance_phase(session_id)
    assert "stub" not in (advanced.to_public_dict().get("message") or "").lower()

    meta_path = session_root / ".gaijinn" / "session.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["phase"] = "awaiting_next_phase"
    meta["current_phase"] = "frontend"
    meta["pipeline_plan"]["current_index"] = 1
    meta["pipeline_plan"]["completed_phases"] = ["backend", "frontend"]
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    testing = store.advance_phase(session_id)
    assert testing.current_phase == "testing"
    assert "stub" not in (testing.to_public_dict().get("message") or "").lower()
