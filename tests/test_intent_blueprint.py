"""Intent-driven blueprint for greenfield orchestrate sessions."""

from __future__ import annotations

from pathlib import Path

import pytest
from aoc_supervisor.intent_blueprint import (
    build_intent_blueprint,
    detect_intent_streams,
    is_greenfield_intent,
    swarm_rationale,
    swarm_warning,
    write_intent_blueprint,
)

PKM_INTENT = (
    "Build a local-first personal knowledge manager for Linux that indexes PDFs, "
    "Markdown files, and audio transcripts, supports semantic search, and exposes "
    "a desktop UI. Must be offline-only and privacy-preserving."
)
TIC_TAC_TOE_INTENT = "Build a tic-tac-toe game with a CLI interface and unit tests."


def test_is_greenfield_intent() -> None:
    assert is_greenfield_intent(PKM_INTENT)
    assert not is_greenfield_intent("fix typo in readme")


def test_pkm_decomposition_yields_distinct_streams() -> None:
    streams = detect_intent_streams(PKM_INTENT)
    titles = {stream.title for stream in streams}
    assert "Document indexing" in titles
    assert "Semantic search" in titles
    assert "Desktop UI" in titles
    assert "Audio transcript ingestion" in titles
    assert "Privacy and offline security" in titles
    assert len(streams) >= 6


def test_pkm_blueprint_uses_intent_goal_not_template_scan() -> None:
    blueprint = build_intent_blueprint(PKM_INTENT)
    assert blueprint["blueprint_mode"] == "intent"
    assert blueprint["project_goal"] == PKM_INTENT
    assert len(blueprint["work_units"]) >= 6
    paths = {unit["allowed_paths"][0] for unit in blueprint["work_units"]}
    assert "src/indexing/" in paths
    assert "src/search/" in paths
    assert "tiny_service/" not in str(paths)


def test_tictactoe_decomposition() -> None:
    streams = detect_intent_streams(TIC_TAC_TOE_INTENT)
    keys = {stream.key for stream in streams}
    assert {"game_logic", "cli", "tests"} <= keys


def test_tictactoe_blueprint() -> None:
    blueprint = build_intent_blueprint(TIC_TAC_TOE_INTENT)
    by_title = {unit["title"]: unit for unit in blueprint["work_units"]}

    assert by_title["Game rules and state"]["allowed_paths"] == ["src/game/"]
    assert by_title["CLI tooling"]["allowed_paths"] == ["src/cli/"]
    assert by_title["Test suite and harness"]["allowed_paths"] == ["tests/"]


def test_swarm_rationale_lists_streams() -> None:
    streams = detect_intent_streams(PKM_INTENT)
    text = swarm_rationale(streams, recommended=7)
    assert "Recommended: 7 agents based on" in text
    assert "indexing" in text.lower() or "document indexing" in text.lower()


def test_swarm_warning_when_oversubscribed() -> None:
    assert swarm_warning(16, 7) == "Only 7 agents can receive work. 9 would be idle."
    assert swarm_warning(3, 7) is None


def test_mock_grid_idle_command_does_not_fake_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAIJINN_MOCK_GRID", "1")
    from aoc_supervisor.api import _spawn_worker_command

    cmd = _spawn_worker_command(
        worker_name="worker-004",
        worker_dir=Path("."),
        full_prompt="",
        model="test",
        has_assigned_work=False,
    )
    script = cmd[-1]
    assert "standby — no work assigned" in script
    assert "build PASS" not in script


EDITOR_INTENT = "Build a test editor in Rust and Go, styled for developers who work at a dark, elegant workstation."


def test_editor_intent_decomposition_for_dogfood() -> None:
    streams = detect_intent_streams(EDITOR_INTENT)
    titles = {stream.title for stream in streams}
    assert "Test editor core" in titles
    assert "Rust engine layer" in titles
    assert "Go services bridge" in titles
    assert "Editor UI and theming" in titles
    assert "Test suite and harness" in titles


def test_write_intent_blueprint_persists_files(tmp_path: Path) -> None:
    project = tmp_path / "session"
    project.mkdir()
    (project / ".gaijinn").mkdir()
    payload = write_intent_blueprint(project, PKM_INTENT)
    assert (project / ".gaijinn" / "blueprint.json").exists()
    assert (project / ".gaijinn" / "blueprint.md").exists()
    assert payload["work_stream_titles"]
