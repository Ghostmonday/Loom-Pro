#!/usr/bin/env python3
"""Composer 2.5 heartbeat — AFK daemon uses this to detect idle vs working."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEARTBEAT = ROOT / ".gaijinn" / "composer-heartbeat.json"
IDLE_SEC = int(__import__("os").environ.get("COMPOSER_IDLE_SEC", "90"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load() -> dict:
    if not HEARTBEAT.exists():
        return {"status": "unknown", "last_ack_at": None, "idle_seconds": 999999}
    try:
        return json.loads(HEARTBEAT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "unknown", "last_ack_at": None, "idle_seconds": 999999}


def idle_seconds(data: dict) -> float:
    raw = data.get("last_ack_at")
    if not raw:
        return float("inf")
    try:
        then = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).total_seconds()
    except ValueError:
        return float("inf")


def is_idle() -> bool:
    data = load()
    if data.get("status") == "working":
        return idle_seconds(data) > IDLE_SEC * 2
    return idle_seconds(data) > IDLE_SEC


def touch(*, status: str = "working", note: str = "", council_seq: int | None = None) -> None:
    data = load()
    data.update(
        {
            "status": status,
            "last_ack_at": _now(),
            "note": note,
            "runtime": "composer-2.5-grok-build-beta",
        }
    )
    if council_seq is not None:
        data["last_council_seq"] = council_seq
    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def mark_idle(note: str = "simulated idle for demo") -> None:
    stale = datetime.now(timezone.utc).timestamp() - IDLE_SEC - 30
    data = {
        "status": "idle",
        "last_ack_at": datetime.fromtimestamp(stale, tz=timezone.utc).isoformat(),
        "note": note,
        "runtime": "composer-2.5-grok-build-beta",
    }
    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Composer heartbeat for AFK idle detection")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="Print idle/working status")
    sub.add_parser("touch", help="Mark working now")
    p_idle = sub.add_parser("mark-idle", help="Mark stale idle (demo)")
    p_idle.add_argument("--note", default="simulated idle")
    args = parser.parse_args()

    if args.cmd == "status":
        data = load()
        secs = idle_seconds(data)
        idle = is_idle()
        print(json.dumps({"idle": idle, "idle_seconds": round(secs, 1), **data}, indent=2))
        return 0
    if args.cmd == "touch":
        touch(note="manual touch")
        print(f"heartbeat → working @ {HEARTBEAT}")
        return 0
    if args.cmd == "mark-idle":
        mark_idle(note=args.note)
        print(f"heartbeat → idle (stale) @ {HEARTBEAT}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
