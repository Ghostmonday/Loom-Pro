"""Greenfield orchestrate prepare — gravity/curvature blueprint path (ENG-103)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aoc_supervisor.orchestrate_session import OrchestrateSessionStore

PKM_INTENT = (
    "Build a local-first personal knowledge manager for Linux that indexes PDFs, "
    "Markdown files, and audio transcripts, supports semantic search, and exposes "
    "a desktop UI. Must be offline-only and privacy-preserving."
)


@pytest.fixture
def store(tmp_path: Path) -> OrchestrateSessionStore:
    return OrchestrateSessionStore(tmp_path)


def test_greenfield_pkm_uses_gaijinn_plan(store: OrchestrateSessionStore, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAIJINN_KEYWORD_GREENFIELD", raising=False)
    calls: list[tuple[str, ...]] = []

    def fake_run(_root: Path, *args: str, **_kwargs) -> None:
        calls.append(args)

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_gaijinn", fake_run)

    snapshot = store.prepare(PKM_INTENT)
    assert snapshot.blueprint_mode == "graph"
    assert ("plan", "--workers", "4") in calls
    assert not any(call and call[0] == "intent_blueprint" for call in calls)


def test_greenfield_pkm_plan_writes_gravity_blueprint(
    store: OrchestrateSessionStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GAIJINN_KEYWORD_GREENFIELD", raising=False)

    snapshot = store.prepare(PKM_INTENT)
    blueprint_path = snapshot.project_root / ".gaijinn" / "blueprint.json"
    assert blueprint_path.exists()
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    assert blueprint.get("blueprint_mode", "graph") == "graph"
    assert snapshot.work_units >= 1
    assert snapshot.work_units == len(blueprint.get("work_units", []))
    assumptions = " ".join(blueprint.get("assumptions", []))
    assert "graph" in assumptions.lower() or "scanned" in assumptions.lower()


def test_keyword_greenfield_fallback_uses_intent_blueprint(
    store: OrchestrateSessionStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GAIJINN_KEYWORD_GREENFIELD", "1")
    calls: list[tuple[str, ...]] = []

    def fake_run(_root: Path, *args: str, **_kwargs) -> None:
        calls.append(args)

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_gaijinn", fake_run)

    snapshot = store.prepare(PKM_INTENT)
    assert snapshot.blueprint_mode == "intent"
    assert snapshot.work_units >= 6
    assert ("plan", "--workers", "4") not in calls
    blueprint = json.loads((snapshot.project_root / ".gaijinn" / "blueprint.json").read_text(encoding="utf-8"))
    assert blueprint["blueprint_mode"] == "intent"


def test_brownfield_still_uses_plan(store: OrchestrateSessionStore, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAIJINN_KEYWORD_GREENFIELD", raising=False)
    calls: list[tuple[str, ...]] = []

    def fake_run(_root: Path, *args: str, **_kwargs) -> None:
        calls.append(args)

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_gaijinn", fake_run)
    monkeypatch.setattr(
        "aoc_supervisor.orchestrate_session._read_blueprint_stats",
        lambda _root: (2, 0, ("Patch readme",), "graph"),
    )

    snapshot = store.prepare("fix typo in readme")
    assert snapshot.blueprint_mode == "graph"
    assert ("plan", "--workers", "4") in calls
