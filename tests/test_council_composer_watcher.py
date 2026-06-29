"""Tests for council → Composer watcher."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "council_composer_watcher",
    ROOT / "scripts" / "dev" / "council_composer_watcher.py",
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["council_composer_watcher"] = _mod
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

ACTION_RE = _mod.ACTION_RE
TRIGGER_RE = _mod.TRIGGER_RE
_parse_actions = _mod._parse_actions
_read_pings = _mod._read_pings


def test_trigger_detects_hermes_ping() -> None:
    text = "@composer — ping. Ready for your next move."
    assert TRIGGER_RE.search(text)
    assert _parse_actions(text) == ("ping",)


def test_action_directive_parsed() -> None:
    text = "@composer ACTION:loop ACTION:health — check gates"
    assert _parse_actions(text) == ("loop", "health")
    assert ACTION_RE.findall(text)


def test_read_pings_skips_composer_echo(tmp_path: Path) -> None:
    jsonl = tmp_path / "council.jsonl"
    rows = [
        {"seq": 1, "author": "hermes", "author_id": "hermes", "text": "@composer ping", "ts": "t1"},
        {"seq": 2, "author": "cursor", "author_id": "composer", "text": "done", "ts": "t2"},
    ]
    jsonl.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    pings = _read_pings("test", jsonl, after_seq=0)
    assert len(pings) == 1
    assert pings[0].seq == 1
    assert pings[0].actions == ("ping",)
