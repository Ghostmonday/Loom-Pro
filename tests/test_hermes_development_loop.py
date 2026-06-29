"""Tests for Hermes development loop."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "hermes_development_loop",
    ROOT / "scripts" / "dev" / "hermes_development_loop.py",
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["hermes_development_loop"] = _mod
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

_decide_action = _mod._decide_action
_blueprint_worker_target = _mod._blueprint_worker_target
_council_control_state = _mod._council_control_state


def test_decide_action_run_grid_when_no_workers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "VAULT", tmp_path)
    monkeypatch.setattr(_mod, "_spawn_in_progress", lambda: False)
    monkeypatch.setattr(_mod, "_worker_count", lambda: 0)
    monkeypatch.setattr(_mod, "_blueprint_worker_target", lambda: 5)
    state = {"layer1_at": "2026-06-17T12:00:00+00:00"}
    assert _decide_action(state) == "run_grid"


def test_decide_action_merge_when_terminal(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "_spawn_in_progress", lambda: False)
    monkeypatch.setattr(_mod, "_sprint_terminal", lambda: True)
    monkeypatch.setattr(_mod, "_worker_statuses", lambda: {"worker-001": "completed"})
    state = {"last_sprint_completed_at": "t1"}
    assert _decide_action(state) == "merge"


def test_decide_action_linter_after_merge(tmp_path: Path, monkeypatch) -> None:
    merge_dir = tmp_path / ".gaijinn" / "merge"
    merge_dir.mkdir(parents=True)
    (merge_dir / "governance.json").write_text(
        json.dumps({"structural_score": {"merged_workers": 2, "convergence": 0.9}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "VAULT", tmp_path)
    monkeypatch.setattr(_mod, "_spawn_in_progress", lambda: False)
    monkeypatch.setattr(_mod, "_sprint_terminal", lambda: True)
    monkeypatch.setattr(_mod, "_worker_statuses", lambda: {"worker-001": "completed"})
    state = {"last_sprint_completed_at": "t1", "last_merge_at": "t1"}
    assert _decide_action(state) == "linter"


def test_decide_action_plan_next_when_only_already_merged_and_backlog(tmp_path: Path, monkeypatch) -> None:
    merge_dir = tmp_path / ".gaijinn" / "merge"
    merge_dir.mkdir(parents=True)
    (merge_dir / "governance.json").write_text(
        json.dumps(
            {
                "structural_score": {
                    "merged_workers": 0,
                    "already_merged_workers": 2,
                    "ledger_entries_written": 0,
                    "convergence": 0.8,
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / ".gaijinn" / "blueprint.json").write_text(
        json.dumps({"work_units": [{"id": "WU-a"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "VAULT", tmp_path)
    monkeypatch.setattr(_mod, "_spawn_in_progress", lambda: False)
    monkeypatch.setattr(_mod, "_sprint_terminal", lambda: True)
    monkeypatch.setattr(_mod, "_worker_statuses", lambda: {"worker-001": "completed"})

    state = {"last_sprint_completed_at": "t1", "last_merge_at": "t1"}

    assert _decide_action(state) == "plan_next_sprint"


def test_council_control_go_after_stop(tmp_path: Path, monkeypatch) -> None:
    bridge = tmp_path / ".gaijinn" / "bridge"
    bridge.mkdir(parents=True)
    rows = [
        {"seq": 11, "author": "user", "text": "STOP — USER HALT"},
        {"seq": 26, "author": "user", "text": "AUTHORIZED: 16-agent LEARN SPRINT"},
    ]
    (bridge / "council.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "VAULT", tmp_path)
    assert _council_control_state() == "go"


def test_blueprint_worker_target_reads_vault_blueprint(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    gaijinn = vault / ".gaijinn"
    gaijinn.mkdir()
    (gaijinn / "blueprint.json").write_text(
        json.dumps({"work_units": [{"id": "WU-001"}, {"id": "WU-002"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "VAULT", vault)
    assert _blueprint_worker_target() == 2
