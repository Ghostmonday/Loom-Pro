#!/usr/bin/env python3
"""Bridge Hermes cron pings → Composer actions via council.jsonl.

Hermes posts ``@composer`` or ``ACTION:<name>`` to council; cron runs this watcher.
It records pending work in ``.gaijinn/composer-watcher-inbox.md`` and optionally
executes safe automation scripts, then acknowledges on council.

Usage:
  python scripts/dev/council_composer_watcher.py
  python scripts/dev/council_composer_watcher.py --dry-run
  GAIJINN_PROJECT_ROOT=vaults/gaijinn-memory-fs python scripts/dev/council_composer_watcher.py
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "aoc-cli"))

from aoc_cli.helpers.council import append_message, council_paths  # noqa: E402

STATE_PATH = ROOT / ".gaijinn" / "composer-watcher-state.json"
INBOX_PATH = ROOT / ".gaijinn" / "composer-watcher-inbox.md"
LOG_PATH = ROOT / ".gaijinn" / "composer-watcher.log"

COMPOSER_AUTHORS = frozenset({"cursor", "composer"})
TRIGGER_RE = re.compile(r"@composer\b", re.IGNORECASE)
ACTION_RE = re.compile(r"\bACTION:\s*([a-z][a-z0-9_.-]*)", re.IGNORECASE)

ACTIONS: dict[str, tuple[str, list[str]]] = {
    "ping": ("Acknowledge Hermes ping; refresh inbox", []),
    "digest": ("Summarize new council messages into inbox", []),
    "loop": ("Run memory↔execution loop check", ["bash", "scripts/dev/memory-execution-loop.sh"]),
    "equivalence": (
        "Weekly GUI equivalence smoke",
        ["bash", "scripts/dev/gui-equivalence-weekly.sh"],
    ),
    "sprint.status": (
        "Check LEARN sprint log tail",
        ["bash", "-c", "tail -30 /tmp/gaijinn-learn-sprint-16.log 2>/dev/null || echo '(no sprint log)'"],
    ),
    "health": (
        "Vault Command Bridge health",
        [
            "bash",
            "-c",
            "curl -sf http://127.0.0.1:8082/api/v1/health | python3 -m json.tool || echo 'vault serve down'",
        ],
    ),
    "pipeline": (
        "Hermes development loop (one vault pipeline step)",
        ["bash", "scripts/dev/hermes-development-loop.sh"],
    ),
    "improve": (
        "Hermes development loop (alias for pipeline)",
        ["bash", "scripts/dev/hermes-development-loop.sh"],
    ),
    "deploy": (
        "Hermes development loop with force unlock",
        ["bash", "scripts/dev/hermes-development-loop.sh", "--force"],
    ),
    "lint": (
        "Vault knowledge linter",
        [
            "bash",
            "-c",
            "cd vaults/gaijinn-memory-fs && python3 10_Operations/knowledge-linter.py --check",
        ],
    ),
    "merge": (
        "Post-sprint collect → validate → merge",
        [
            "bash",
            "-c",
            (
                "cd vaults/gaijinn-memory-fs && "
                "export GAIJINN_PROJECT_ROOT=. "
                'PYTHONPATH="${PWD}/../../aoc-cli:${PWD}/../../aoc_supervisor" '
                "GAIJINN_OPERATOR=1 && "
                "gaijinn collect && gaijinn validate-worker && gaijinn merge-grid --strategy sequential"
            ),
        ],
    ),
    "v1.lead": (
        "V1 program lead — refresh sprint board + test snapshot for Composer",
        [
            "bash",
            "-c",
            (
                'cd "$PWD" && '
                "mkdir -p .gaijinn && "
                "echo '# V1 Sprint Board (auto)' > .gaijinn/v1-sprint-board.md && "
                "date -u +'Updated: %Y-%m-%dT%H:%M:%SZ' >> .gaijinn/v1-sprint-board.md && "
                "echo '' >> .gaijinn/v1-sprint-board.md && "
                "git status -sb | head -5 >> .gaijinn/v1-sprint-board.md && "
                "echo '' >> .gaijinn/v1-sprint-board.md && "
                "test -f .gaijinn/hermes-loop-state.json && "
                "python3 -c \"import json; s=json.load(open('.gaijinn/hermes-loop-state.json')); "
                "print('hermes:', s.get('phase'), 'convergence:', s.get('convergence'))\" "
                ">> .gaijinn/v1-sprint-board.md 2>/dev/null || true && "
                "echo '' >> .gaijinn/v1-sprint-board.md && "
                "(.venv/bin/python -m pytest -q --tb=no 2>&1 | tail -5 || true) >> .gaijinn/v1-sprint-board.md"
            ),
        ],
    ),
    "v1.status": (
        "V1 status snapshot — print sprint board",
        [
            "bash",
            "-c",
            (
                "test -f .gaijinn/v1-sprint-board.md && cat .gaijinn/v1-sprint-board.md "
                "|| echo 'no v1 board — run ACTION:v1.lead first'"
            ),
        ],
    ),
}


@dataclass(frozen=True)
class CouncilPing:
    council_id: str
    jsonl: Path
    seq: int
    ts: str
    author: str
    author_id: str
    text: str
    actions: tuple[str, ...]


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"councils": {}, "version": 1}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"councils": {}, "version": 1}


def _save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _append_log(line: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} {line}\n")


def _parse_actions(text: str) -> tuple[str, ...]:
    found = [match.group(1).lower() for match in ACTION_RE.finditer(text)]
    if found:
        return tuple(dict.fromkeys(found))
    if TRIGGER_RE.search(text):
        return ("ping",)
    return ()


def _discover_councils(extra_roots: list[Path]) -> list[tuple[str, Path]]:
    councils: list[tuple[str, Path]] = []
    seen: set[Path] = set()

    global_jsonl = Path.home() / ".gaijinn" / "bridge" / "council.jsonl"
    if global_jsonl.exists():
        seen.add(global_jsonl.resolve())
        councils.append(("global", global_jsonl.resolve()))

    candidates = [
        ROOT,
        ROOT / "vaults" / "gaijinn-memory-fs",
        *extra_roots,
    ]
    project_root = os.environ.get("GAIJINN_PROJECT_ROOT", "").strip()
    if project_root:
        candidates.insert(0, Path(project_root).resolve())

    for base in candidates:
        base = base.resolve()
        paths = council_paths(base)
        jsonl = paths["jsonl"]
        if jsonl in seen or not jsonl.exists():
            continue
        seen.add(jsonl)
        council_id = str(base.relative_to(ROOT)) if base != ROOT else "platform"
        councils.append((council_id, jsonl))
    return councils


def _read_pings(council_id: str, jsonl: Path, after_seq: int) -> list[CouncilPing]:
    pings: list[CouncilPing] = []
    for line in jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        seq = int(payload.get("seq", 0))
        if seq <= after_seq:
            continue
        author = str(payload.get("author", "")).lower()
        if author in COMPOSER_AUTHORS:
            continue
        text = str(payload.get("text", ""))
        actions = _parse_actions(text)
        if not actions:
            continue
        pings.append(
            CouncilPing(
                council_id=council_id,
                jsonl=jsonl,
                seq=seq,
                ts=str(payload.get("ts", "")),
                author=author,
                author_id=str(payload.get("author_id", author)),
                text=text,
                actions=actions,
            )
        )
    return pings


def _run_action(action: str, *, dry_run: bool) -> tuple[bool, str]:
    if action not in ACTIONS:
        return False, f"unknown action {action!r} (known: {', '.join(sorted(ACTIONS))})"
    _desc, cmd = ACTIONS[action]
    if not cmd:
        return True, f"{action}: inbox only"
    if dry_run:
        return True, f"dry-run: would run {' '.join(cmd)}"
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    output = (proc.stdout or proc.stderr or "").strip()
    if len(output) > 4000:
        output = output[:4000] + "\n…(truncated)"
    ok = proc.returncode == 0
    return ok, output or f"exit {proc.returncode}"


def _write_inbox(pings: list[CouncilPing], results: list[dict[str, Any]]) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Composer Watcher Inbox",
        "",
        f"Updated: {now}",
        "",
        "Hermes/cron pings land here. Open Cursor Composer and act on pending items.",
        "",
        "## Pending pings",
        "",
    ]
    if not pings:
        lines.append("_No new @composer pings since last run._")
    else:
        for ping in pings:
            lines.append(f"### [{ping.council_id}] seq {ping.seq} — {ping.author_id} ({ping.ts})")
            lines.append("")
            lines.append(ping.text.strip())
            lines.append("")
            lines.append(f"Suggested actions: `{', '.join(ping.actions)}`")
            lines.append("")

    lines.extend(["## Automation results", ""])
    if not results:
        lines.append("_No automation executed this run._")
    else:
        for item in results:
            status = "OK" if item["ok"] else "FAIL"
            lines.append(f"- **{status}** `{item['action']}` @ {item['council_id']} seq {item['seq']}")
            if item.get("detail"):
                lines.append("  ```")
                lines.append(item["detail"])
                lines.append("  ```")
    lines.append("")
    lines.append("---")
    lines.append("Cron: `bash scripts/dev/council-composer-watcher.sh`")
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INBOX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _notify(summary: str) -> None:
    if os.environ.get("GAIJINN_WATCHER_NOTIFY", "1").strip().lower() in {"0", "false", "no"}:
        return
    with contextlib.suppress(FileNotFoundError):
        subprocess.run(
            ["notify-send", "Gaijinn Composer", summary, "-u", "normal", "-t", "8000"],
            check=False,
            capture_output=True,
        )


def _acknowledge(ping: CouncilPing, summary: str, *, dry_run: bool) -> None:
    if dry_run:
        return
    project_root = ping.jsonl.parent.parent.parent
    text = f"Watcher [auto]: processed seq {ping.seq} — {summary}"
    append_message(
        text,
        author="cursor",
        author_id="composer-watcher",
        role="system",
        project_root=project_root,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Council → Composer watcher")
    parser.add_argument("--dry-run", action="store_true", help="Do not mutate state or council")
    parser.add_argument("--council", action="append", default=[], help="Extra project root to watch")
    args = parser.parse_args()

    extra = [Path(p).resolve() for p in args.council]
    state = _load_state()
    councils_state: dict[str, Any] = dict(state.get("councils") or {})

    all_pings: list[CouncilPing] = []
    for council_id, jsonl in _discover_councils(extra):
        after_seq = int((councils_state.get(council_id) or {}).get("last_seq", 0))
        pings = _read_pings(council_id, jsonl, after_seq)
        all_pings.extend(pings)

    if not all_pings:
        _write_inbox([], [])
        print("composer-watcher: no new pings")
        return 0

    results: list[dict[str, Any]] = []
    max_seq: dict[str, int] = {}

    for ping in all_pings:
        max_seq[ping.council_id] = max(max_seq.get(ping.council_id, 0), ping.seq)
        for action in ping.actions:
            ok, detail = _run_action(action, dry_run=args.dry_run)
            results.append(
                {
                    "council_id": ping.council_id,
                    "seq": ping.seq,
                    "action": action,
                    "ok": ok,
                    "detail": detail,
                }
            )
            _append_log(f"{'OK' if ok else 'FAIL'} {ping.council_id} seq={ping.seq} action={action}")

    _write_inbox(all_pings, results)

    if not args.dry_run:
        for council_id, seq in max_seq.items():
            councils_state[council_id] = {"last_seq": seq, "last_run": datetime.now(timezone.utc).isoformat()}
        state["councils"] = councils_state
        _save_state(state)
        summary = f"{len(all_pings)} ping(s), {len(results)} action(s)"
        _notify(summary)
        for ping in all_pings:
            actions = ", ".join(ping.actions)
            _acknowledge(ping, f"ran [{actions}]", dry_run=False)

    print(f"composer-watcher: processed {len(all_pings)} ping(s), inbox → {INBOX_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
