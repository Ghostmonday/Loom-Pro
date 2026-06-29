"""Orchestrate session store — intent → blueprint → swarm."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aoc_supervisor.orchestrate_session import (
    DESIGN_COMMAND_TIMEOUT_DEFAULT,
    OrchestrateSessionStore,
    _pythonpath_env,
    _recommend_swarm,
    design_command_timeout,
)

PKM_INTENT = (
    "Build a local-first personal knowledge manager for Linux that indexes PDFs, "
    "Markdown files, and audio transcripts, supports semantic search, and exposes "
    "a desktop UI. Must be offline-only and privacy-preserving."
)


@pytest.fixture
def store(tmp_path: Path) -> OrchestrateSessionStore:
    return OrchestrateSessionStore(tmp_path)


def test_recommend_swarm_scales_with_work_units(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assert _recommend_swarm(1) == 1
    assert _recommend_swarm(3) == 3
    assert _recommend_swarm(12) >= 4

    monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / ".venv"))
    monkeypatch.setenv("PYTHON", "python-from-session")
    monkeypatch.setenv("PYTHONPATH", "relative-path")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("aoc_supervisor.orchestrate_session._repo_venv_python", lambda: None)

    env = _pythonpath_env()

    assert "VIRTUAL_ENV" not in env
    assert "PYTHON" not in env
    for item in env["PYTHONPATH"].split(":"):
        assert Path(item).is_absolute()


def test_prepare_and_assign_swarm(store: OrchestrateSessionStore) -> None:
    snapshot = store.prepare("Terminal smoke test project")
    assert snapshot.work_units >= 1
    assert snapshot.phase == "awaiting_swarm"

    armed = store.assign_swarm(snapshot.session_id, 2)
    assert armed.workers_ready == 2
    assert armed.phase == "ready_to_deploy"
    assert (store.workers_dir(snapshot.session_id) / "worker-001").exists()


def _loaded_context_for(tmp_path: Path, phases: list[str]) -> dict[str, dict[str, str]]:
    backend = tmp_path / "loaded-backend"
    frontend = tmp_path / "loaded-frontend"
    backend.mkdir(exist_ok=True)
    frontend.mkdir(exist_ok=True)
    selected = set(phases)
    context: dict[str, dict[str, str]] = {}
    if selected == {"testing"} or selected == {"frontend", "testing"}:
        context["backend"] = {"project_path": str(backend)}
    if selected == {"testing"} or selected == {"backend", "testing"}:
        context["frontend"] = {"project_path": str(frontend)}
    return context


@pytest.mark.parametrize(
    "phases",
    [
        ["backend"],
        ["frontend"],
        ["testing"],
        ["backend", "frontend"],
        ["backend", "testing"],
        ["frontend", "testing"],
        ["backend", "frontend", "testing"],
    ],
)
def test_prepare_persists_phase_presets(store: OrchestrateSessionStore, tmp_path: Path, phases: list[str]) -> None:
    snapshot = store.prepare(
        "Terminal smoke test project", phases=phases, loaded_context=_loaded_context_for(tmp_path, phases)
    )
    meta = json.loads((snapshot.project_root / ".gaijinn" / "session.json").read_text(encoding="utf-8"))
    assert meta["phases"] == phases
    assert meta["current_phase"] == phases[0]
    assert meta["pipeline_plan"]["phases"] == phases
    assert meta["pipeline_plan"]["current_index"] == 0
    public = snapshot.to_public_dict()
    assert public["phases"] == phases
    assert public["current_phase"] == phases[0]
    assert public["phase_count"] == len(phases)
    assert public["pipeline_plan"]["phases"] == phases


def test_prepare_normalizes_phase_order(store: OrchestrateSessionStore) -> None:
    frontend = store.host_root / "loaded-frontend"
    frontend.mkdir()
    snapshot = store.prepare(
        "Terminal smoke test project",
        phases=["testing", "backend"],
        loaded_context={"frontend": {"project_path": str(frontend)}},
    )
    assert snapshot.to_public_dict()["phases"] == ["backend", "testing"]


def test_prepare_rejects_missing_loaded_context(store: OrchestrateSessionStore) -> None:
    with pytest.raises(ValueError, match="requires loaded context first: frontend"):
        store.prepare("Terminal smoke test project", phases=["backend", "testing"])


def test_frontend_only_warns_without_loaded_backend(store: OrchestrateSessionStore) -> None:
    snapshot = store.prepare("Terminal smoke test project", phases=["frontend"])
    assert "backend context is recommended" in snapshot.to_public_dict()["phase_warning"]


def test_backend_only_single_phase_no_advance_needed(store: OrchestrateSessionStore) -> None:
    snapshot = store.prepare("Terminal smoke test project", phases=["backend"])
    meta_path = snapshot.project_root / ".gaijinn" / "session.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["phase"] = "merge_complete"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no remaining phases"):
        store.advance_phase(snapshot.session_id)


def test_full_stack_advances_backend_frontend_testing(
    store: OrchestrateSessionStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = store.prepare("Terminal smoke test project", phases=["backend", "frontend", "testing"])
    meta_path = snapshot.project_root / ".gaijinn" / "session.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    def fake_pipeline(
        _project_root: Path,
        intent: str,
        *,
        command_timeout: int | None = None,
        use_intent_blueprint: bool = False,
        loaded_context: dict | None = None,
    ) -> tuple[int, int, tuple[str, ...], str, tuple[str, ...]]:
        if "frontend UI" in intent:
            titles = ("Desktop UI",)
        elif "acceptance tests" in intent:
            titles = ("Test suite and harness",)
        else:
            titles = ("Core project scaffold",)
        return len(titles), 0, titles, "graph", titles

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_blueprint_pipeline", fake_pipeline)

    meta["phase"] = "awaiting_next_phase"
    meta["pipeline_plan"]["completed_phases"] = ["backend"]
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    frontend = store.advance_phase(snapshot.session_id)
    assert frontend.phase == "awaiting_swarm"
    assert frontend.current_phase == "frontend"
    assert frontend.workers_ready == 0
    assert frontend.to_public_dict()["pipeline_plan"]["current_index"] == 1
    assert "blueprint stub" not in (frontend.to_public_dict().get("message") or "").lower()

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["phase"] = "awaiting_next_phase"
    meta["pipeline_plan"]["completed_phases"] = ["backend", "frontend"]
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    testing = store.advance_phase(snapshot.session_id)
    assert testing.current_phase == "testing"
    assert testing.to_public_dict()["pipeline_plan"]["current_index"] == 2
    assert "blueprint stub" not in (testing.to_public_dict().get("message") or "").lower()


def test_testing_only_starts_on_testing_phase(store: OrchestrateSessionStore, tmp_path: Path) -> None:
    snapshot = store.prepare(
        "Terminal smoke test project",
        phases=["testing"],
        loaded_context=_loaded_context_for(tmp_path, ["testing"]),
    )
    assert snapshot.current_phase == "testing"
    assert snapshot.to_public_dict()["pipeline_plan"]["current_phase"] == "testing"


def test_backend_testing_advances_once(
    store: OrchestrateSessionStore,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = store.prepare(
        "Terminal smoke test project",
        phases=["backend", "testing"],
        loaded_context=_loaded_context_for(tmp_path, ["backend", "testing"]),
    )
    meta_path = snapshot.project_root / ".gaijinn" / "session.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["phase"] = "awaiting_next_phase"
    meta["pipeline_plan"]["completed_phases"] = ["backend"]
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        "aoc_supervisor.orchestrate_session._run_blueprint_pipeline",
        lambda *_args, **_kwargs: (1, 0, ("Test suite and harness",), "graph", ("Test suite and harness",)),
    )

    advanced = store.advance_phase(snapshot.session_id)
    assert advanced.current_phase == "testing"
    assert advanced.phase == "awaiting_swarm"
    assert advanced.workers_ready == 0
    assert advanced.to_public_dict()["pipeline_plan"]["phases"] == ["backend", "testing"]


def test_recommend_swarm_intent_mode_matches_work_units() -> None:
    assert _recommend_swarm(7, intent_mode=True) == 7
    assert _recommend_swarm(3, intent_mode=True) == 3


def test_suggest_swarm_intent_mode_skips_tiny_ladder() -> None:
    from aoc_supervisor.orchestrate_session import _suggest_swarm

    options = _suggest_swarm(7, intent_mode=True)
    assert options == [3, 7, 9]
    assert 1 not in options
    assert 2 not in options


def test_pkm_prepare_uses_gravity_plan(store: OrchestrateSessionStore, monkeypatch) -> None:
    monkeypatch.delenv("GAIJINN_KEYWORD_GREENFIELD", raising=False)
    snapshot = store.prepare(PKM_INTENT)
    assert snapshot.blueprint_mode == "graph"
    assert snapshot.work_units >= 1
    assert "indexing" in snapshot.swarm_rationale.lower() or "document" in snapshot.swarm_rationale.lower()
    public = snapshot.to_public_dict()
    assert public["recommended_swarm"] >= 1
    assert public["max_productive_swarm"] == snapshot.work_units
    assert len(public["work_stream_titles"]) >= 1

    armed = store.assign_swarm(snapshot.session_id, 16)
    assert armed.swarm_warning is not None
    assert armed.idle_agents == 16 - snapshot.work_units


def test_design_command_timeout_defaults_to_one_hour() -> None:
    assert design_command_timeout(None) == DESIGN_COMMAND_TIMEOUT_DEFAULT
    assert DESIGN_COMMAND_TIMEOUT_DEFAULT == 3600


def test_design_command_timeout_clamps_request(monkeypatch) -> None:
    monkeypatch.delenv("GAIJINN_DESIGN_TIMEOUT", raising=False)
    assert design_command_timeout(7200) == 7200
    assert design_command_timeout(30) == 60
    assert design_command_timeout(99_999) == 14_400


def test_prepare_passes_layer1_timeout_to_gaijinn(store: OrchestrateSessionStore, monkeypatch) -> None:
    seen: list[int] = []

    def fake_run(_root: Path, *_args: str, timeout: int | None = None, **_kwargs) -> None:
        seen.append(design_command_timeout(timeout))

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_gaijinn", fake_run)
    monkeypatch.setattr(
        "aoc_supervisor.orchestrate_session._read_blueprint_stats",
        lambda _root: (3, 0, ("Core",), "graph"),
    )

    store.prepare("fix typo in readme", layer1_timeout=5400)
    assert seen
    assert all(timeout == 5400 for timeout in seen)


def test_slim_prepare_writes_executable_blueprint_without_gaijinn_commands(
    store: OrchestrateSessionStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blueprint = {
        "schema_version": 1,
        "blueprint_mode": "intent",
        "projection_mode": "intent_forge",
        "work_stream_titles": ["API", "Tests"],
        "work_units": [
            {"id": "WU-001", "title": "API", "estimated_risk": "high", "allowed_paths": ["src/api.py"]},
            {"id": "WU-002", "title": "Tests", "estimated_risk": "low", "allowed_paths": ["tests/test_api.py"]},
        ],
    }
    commands: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        "aoc_supervisor.orchestrate_session._run_gaijinn",
        lambda _root, *args, **_kwargs: commands.append(args),
    )

    snapshot = store.prepare("Build an API", executable_blueprint=blueprint)

    assert commands == []
    assert snapshot.work_units == 2
    assert snapshot.high_risk_units == 1
    assert snapshot.work_stream_titles == ("API", "Tests")
    assert snapshot.to_public_dict()["recommended_swarm"] == 2
    persisted = json.loads((snapshot.project_root / ".gaijinn" / "blueprint.json").read_text(encoding="utf-8"))
    assert persisted == blueprint


def test_slim_prepare_reports_loom_synthesis_projection_mode(
    store: OrchestrateSessionStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blueprint = {
        "schema_version": 1,
        "blueprint_mode": "intent",
        "projection_mode": "loom_synthesis",
        "work_stream_titles": ["Synthesized architecture"],
        "work_units": [
            {
                "id": "WU-001",
                "title": "Synthesized architecture",
                "estimated_risk": "low",
                "allowed_paths": ["src/architecture.py"],
            }
        ],
    }
    monkeypatch.setattr(
        "aoc_supervisor.orchestrate_session._run_gaijinn",
        lambda *_args, **_kwargs: pytest.fail("slim prepare must not run Gaijinn commands"),
    )

    snapshot = store.prepare("Build the synthesized architecture", executable_blueprint=blueprint)

    assert snapshot.blueprint_mode == "loom_synthesis"
    assert snapshot.work_units == 1
    meta = json.loads((snapshot.project_root / ".gaijinn" / "session.json").read_text(encoding="utf-8"))
    assert meta["blueprint_mode"] == "loom_synthesis"
