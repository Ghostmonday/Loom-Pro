"""Tests for prompt_coverage — internal dev helper (NOT a user-facing quality gate).

Uses the STREAM_SPECS-backed implementation that maps prompt keywords
to expected workstreams and compares against blueprint work units.
"""

from __future__ import annotations

from typing import Any

from aoc_supervisor.prompt_coverage import (
    blueprint_coverage,
    explicit_requirements,
)


class TestExplicitRequirements:
    def test_tic_tac_toe(self) -> None:
        reqs = explicit_requirements("Build a tic-tac-toe game with a CLI")
        assert "foundation" in reqs
        assert "game_logic" in reqs
        assert "cli" in reqs

    def test_test_editor(self) -> None:
        reqs = explicit_requirements(
            "Build a test editor in Rust and Go, styled for developers who work at a dark, elegant workstation."
        )
        assert "foundation" in reqs
        assert "editor_core" in reqs
        assert "rust_core" in reqs
        assert "go_bridge" in reqs
        assert "editor_ui" in reqs
        assert "tests" in reqs

    def test_todo_cli(self) -> None:
        reqs = explicit_requirements("Create a todo CLI application with storage")
        assert "foundation" in reqs
        assert "storage" in reqs
        assert "cli" in reqs

    def test_empty_intent(self) -> None:
        assert explicit_requirements("") == []
        assert explicit_requirements("   ") == []


class TestBlueprintCoverage:
    TICTACTOE_BP: dict[str, Any] = {
        "work_units": [
            {"title": "Core project scaffold", "allowed_paths": ["src/core/"]},
            {"title": "Game rules and state", "allowed_paths": ["src/game/"]},
            {"title": "CLI tooling", "allowed_paths": ["src/cli/"]},
            {"title": "Test suite and harness", "allowed_paths": ["tests/"]},
        ],
    }

    EDITOR_BP: dict[str, Any] = {
        "work_units": [
            {"title": "Core project scaffold", "allowed_paths": ["src/core/"]},
            {"title": "Test editor core", "allowed_paths": ["src/editor/"]},
            {"title": "Rust engine layer", "allowed_paths": ["crates/editor-core/"]},
            {"title": "Go services bridge", "allowed_paths": ["services/bridge/"]},
            {"title": "Editor UI and theming", "allowed_paths": ["src/ui/editor/"]},
            {"title": "Test suite and harness", "allowed_paths": ["tests/"]},
        ],
    }

    def test_tic_tac_toe_full_coverage(self) -> None:
        result = blueprint_coverage("Build a tic-tac-toe game with a CLI", self.TICTACTOE_BP)
        assert "foundation" in result["covered"]
        assert "game_logic" in result["covered"]
        assert "cli" in result["covered"]
        assert result["missing"] == []

    def test_partial_coverage(self) -> None:
        bp = {"work_units": [{"title": "Core project scaffold", "allowed_paths": ["src/core/"]}]}
        result = blueprint_coverage("Build a tic-tac-toe game", bp)
        assert "foundation" in result["covered"]
        assert "game_logic" in result["missing"]

    def test_test_editor_coverage(self) -> None:
        result = blueprint_coverage(
            "Build a test editor in Rust and Go, styled for developers who work at a dark, elegant workstation.",
            self.EDITOR_BP,
        )
        assert set(result["covered"]) == {"foundation", "editor_core", "rust_core", "go_bridge", "editor_ui", "tests"}

    def test_empty_blueprint(self) -> None:
        result = blueprint_coverage("Build a tic-tac-toe game", {"work_units": []})
        assert result["covered"] == []
        assert len(result["missing"]) > 0
