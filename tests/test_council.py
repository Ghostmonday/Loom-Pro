from __future__ import annotations

import json
from pathlib import Path

from aoc_cli.cli import app
from aoc_cli.helpers import council as council_helpers
from aoc_cli.helpers.council import _format_display_ts
from typer.testing import CliRunner

runner = CliRunner()


def test_council_init_and_say(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--force", "--no-agent-files", "Council test project"], color=False)

    council_md = Path(".gaijinn/bridge/council.md")
    assert council_md.exists()

    result = runner.invoke(
        app,
        ["council", "say", "--as", "user", "--id", "Amir", "Hello council"],
        color=False,
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        ["council", "say", "--as", "cursor", "--id", "composer", "I read the thread"],
        color=False,
    )
    assert result.exit_code == 0, result.output

    md = council_md.read_text(encoding="utf-8")
    assert "Hello council" in md
    assert "I read the thread" in md
    assert "Gaijinn Blueprint" in md or "intent map" in md.lower()

    lines = Path(".gaijinn/bridge/council.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 3
    last = json.loads(lines[-1])
    assert last["author"] == "cursor"
    assert "PDT" in md or "PST" in md or "UTC" in md


def test_council_display_timestamp_includes_local_and_utc(monkeypatch) -> None:
    monkeypatch.setenv("GAIJINN_COUNCIL_TZ", "America/Los_Angeles")
    label = _format_display_ts("2026-06-16T01:11:39Z")
    assert "UTC 2026-06-16T01:11:39Z" in label
    assert "Jun 15" in label
    assert "PM PDT" in label


def test_council_rebuild_global(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    global_gaijinn_dir = tmp_path / ".home" / ".gaijinn"
    monkeypatch.setattr(council_helpers, "GLOBAL_GAIJINN_DIR", global_gaijinn_dir)
    monkeypatch.setattr(council_helpers, "GLOBAL_COUNCIL_MD", global_gaijinn_dir / "bridge" / "council.md")
    runner.invoke(app, ["council", "say", "--global", "--as", "cursor", "rebuild test"], color=False)
    result = runner.invoke(app, ["council", "rebuild", "--global"], color=False)
    assert result.exit_code == 0, result.output
    assert "Rebuilt council markdown" in result.output
