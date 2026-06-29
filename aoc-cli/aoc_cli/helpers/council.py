"""Gaijinn Council — shared multi-party thread for humans and agents.

Canonical human-readable file: ``.gaijinn/bridge/council.md``
Append-only log: ``.gaijinn/bridge/council.jsonl``

Every AI in the stack reads ``council.md``; no human relay required.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .constants import BLUEPRINT_JSON_PATH, GAIJINN_DIR, INTENT_PATH

BRIDGE_DIR = GAIJINN_DIR / "bridge"
COUNCIL_JSONL = BRIDGE_DIR / "council.jsonl"
COUNCIL_MD = BRIDGE_DIR / "council.md"
COUNCIL_META = BRIDGE_DIR / "meta.json"

VALID_AUTHORS = frozenset({"user", "cursor", "grok", "gaijinn", "deepseek", "hermes", "other"})

GLOBAL_GAIJINN_DIR = Path.home() / ".gaijinn"
GLOBAL_COUNCIL_MD = GLOBAL_GAIJINN_DIR / "bridge" / "council.md"
DEFAULT_COUNCIL_TZ = "America/Los_Angeles"


@dataclass(frozen=True)
class CouncilMessage:
    seq: int
    ts: str
    author: str
    author_id: str
    role: str
    text: str
    message_type: str = ""
    payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "seq": self.seq,
            "ts": self.ts,
            "author": self.author,
            "author_id": self.author_id,
            "role": self.role,
            "text": self.text,
        }
        if self.message_type:
            data["type"] = self.message_type
        if self.payload:
            data["payload"] = self.payload
        return data

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CouncilMessage:
        extra_payload = payload.get("payload")
        return cls(
            seq=int(payload["seq"]),
            ts=str(payload["ts"]),
            author=str(payload["author"]),
            author_id=str(payload.get("author_id", payload["author"])),
            role=str(payload.get("role", "participant")),
            text=str(payload["text"]),
            message_type=str(payload.get("type", payload.get("message_type", ""))),
            payload=dict(extra_payload) if isinstance(extra_payload, dict) else None,
        )


def council_paths(project_root: Path | None = None, *, global_council: bool = False) -> dict[str, Path]:
    if global_council:
        root = Path.home()
        bridge = GLOBAL_GAIJINN_DIR / "bridge"
        return {
            "bridge": bridge,
            "jsonl": bridge / "council.jsonl",
            "md": GLOBAL_COUNCIL_MD,
            "meta": bridge / "meta.json",
        }
    root = (project_root or Path.cwd()).resolve()
    bridge = root / BRIDGE_DIR
    return {
        "bridge": bridge,
        "jsonl": root / COUNCIL_JSONL,
        "md": root / COUNCIL_MD,
        "meta": root / COUNCIL_META,
    }


def default_author_id(author: str) -> str:
    env_key = f"GAIJINN_COUNCIL_{author.upper()}_ID"
    return os.environ.get(env_key) or os.environ.get("GAIJINN_COUNCIL_AUTHOR_ID") or author


def machine_council_address() -> str:
    """Absolute path every local agent (Cursor, Hermes, Grok) should read."""
    return str(GLOBAL_COUNCIL_MD.resolve())


def ensure_council(
    project_root: Path | None = None,
    *,
    project_prompt: str | None = None,
    global_council: bool = False,
) -> Path:
    """Create bridge artifacts if missing. Returns path to council.md."""
    paths = council_paths(project_root, global_council=global_council)
    paths["bridge"].mkdir(parents=True, exist_ok=True)

    prompt = project_prompt
    gaijinn_dir = paths["md"].parent.parent
    if prompt is None and not global_council and (gaijinn_dir / "project.json").exists():
        try:
            project = json.loads((gaijinn_dir / "project.json").read_text(encoding="utf-8"))
            prompt = str(project.get("project_prompt", ""))
        except (OSError, json.JSONDecodeError):
            prompt = ""

    if not paths["meta"].exists():
        paths["meta"].write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "purpose": "Gaijinn Council — intent map thread for all agents",
                    "read_path": str(COUNCIL_MD),
                    "append_command": 'gaijinn council say --as <author> "message"',
                    "display_timezone": _council_timezone_name(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    if not paths["jsonl"].exists():
        bootstrap = CouncilMessage(
            seq=1,
            ts=_now_iso(),
            author="gaijinn",
            author_id="council-bridge",
            role="system",
            text=(
                "Council initialized. MACHINE ADDRESS for all local agents (Cursor, Hermes, Grok): "
                f"{paths['md'].resolve()}. Read before acting; append via gaijinn council say. No human relay."
            ),
        )
        _append_line(paths["jsonl"], bootstrap)
        _render_markdown(paths, [bootstrap], project_prompt=prompt or "")
    return paths["md"]


def append_message(
    text: str,
    *,
    author: str = "user",
    author_id: str | None = None,
    role: str = "participant",
    message_type: str = "",
    payload: Mapping[str, Any] | None = None,
    project_root: Path | None = None,
    global_council: bool = False,
) -> CouncilMessage:
    """Append a message and regenerate council.md."""
    text = text.strip()
    if not text:
        raise ValueError("message must not be empty")

    author = author.strip().lower()
    if author not in VALID_AUTHORS:
        raise ValueError(f"author must be one of: {', '.join(sorted(VALID_AUTHORS))}")

    paths = council_paths(project_root, global_council=global_council)
    ensure_council(project_root, global_council=global_council)

    entries = load_messages(project_root, global_council=global_council)
    msg = CouncilMessage(
        seq=len(entries) + 1,
        ts=_now_iso(),
        author=author,
        author_id=(author_id or default_author_id(author)).strip(),
        role=role.strip() or "participant",
        text=text,
        message_type=message_type.strip(),
        payload=dict(payload) if payload is not None else None,
    )
    _append_line(paths["jsonl"], msg)
    entries.append(msg)

    prompt = "" if global_council else _read_project_prompt(paths["md"].parent.parent)
    _render_markdown(paths, entries, project_prompt=prompt)
    return msg


def load_messages(project_root: Path | None = None, *, global_council: bool = False) -> list[CouncilMessage]:
    paths = council_paths(project_root, global_council=global_council)
    if not paths["jsonl"].exists():
        return []

    entries: list[CouncilMessage] = []
    for line in paths["jsonl"].read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            entries.append(CouncilMessage.from_dict(payload))
    return entries


def render_council_markdown(project_root: Path | None = None, *, global_council: bool = False) -> str:
    paths = council_paths(project_root, global_council=global_council)
    if not paths["jsonl"].exists():
        ensure_council(project_root, global_council=global_council)
    entries = load_messages(project_root, global_council=global_council)
    prompt = "" if global_council else _read_project_prompt(paths["md"].parent.parent)
    root = Path.home() if global_council else (project_root or Path.cwd()).resolve()
    return _build_markdown(entries, project_prompt=prompt, project_root=root)


def append_handoff_receipt(
    ticket: Any,
    *,
    project_root: Path | None = None,
    global_council: bool = False,
    resolved_by_worker_id: str | None = None,
) -> CouncilMessage:
    """Publish a handoff transaction receipt when a target worker resolves a ticket."""
    from ..giv import HandoffTicket

    if not isinstance(ticket, HandoffTicket):
        raise TypeError("ticket must be a HandoffTicket")

    resolver = resolved_by_worker_id or "unknown"
    text = (
        f"**[HANDOFF_TRANSACTION_RECEIPT]** Ticket `{ticket.ticket_id}` resolved by `{resolver}` "
        f"for `{ticket.target_work_unit_id}` (`{ticket.target_file}`)."
    )
    return append_message(
        text,
        author="gaijinn",
        author_id=f"merge-governance/{resolver}",
        role="executor",
        message_type="HANDOFF_TRANSACTION_RECEIPT",
        payload={
            "ticket_id": ticket.ticket_id,
            "source_worker_id": ticket.source_worker_id,
            "target_work_unit_id": ticket.target_work_unit_id,
            "target_file": ticket.target_file,
            "resolved_by_worker_id": resolver,
        },
        project_root=project_root,
        global_council=global_council,
    )


def append_handoff_transaction(
    ticket: Any,
    *,
    project_root: Path | None = None,
    global_council: bool = False,
) -> CouncilMessage:
    """Publish a handoff transaction request to the council bus."""
    from ..giv import HandoffTicket

    if not isinstance(ticket, HandoffTicket):
        raise TypeError("ticket must be a HandoffTicket")

    text = (
        f"**[HANDOFF_TRANSACTION_ALERT]** Ticket `{ticket.ticket_id}` raised against "
        f"`{ticket.target_work_unit_id}`.\n"
        f"Requires structural modification in closed file `{ticket.target_file}`:\n"
        f"```\n{ticket.required_mutation_context}\n```"
    )
    return append_message(
        text,
        author="gaijinn",
        author_id=f"merge-governance/{ticket.source_worker_id}",
        role="executor",
        message_type="HANDOFF_TRANSACTION_REQUEST",
        payload=ticket.to_dict(),
        project_root=project_root,
        global_council=global_council,
    )


def publish_handoff_tickets_from_log(
    worker_id: str,
    log_text: str,
    blueprint: Any,
    *,
    project_root: Path | None = None,
    global_council: bool = False,
) -> list[Any]:
    """Parse worker output.log and append handoff transactions to council.

    Scaffold placeholders and off-blueprint targets are dropped before publish
    (see handoff.parse_handoff_tickets_from_log).
    """
    from .handoff import parse_handoff_tickets_from_log

    published: list[Any] = []
    for ticket in parse_handoff_tickets_from_log(worker_id, log_text, blueprint):
        append_handoff_transaction(
            ticket,
            project_root=project_root,
            global_council=global_council,
        )
        published.append(ticket)
    return published


def council_excerpt_for_prompt(project_root: Path | None = None, *, max_messages: int = 12) -> str:
    """Compact block injected into worker spawn prompts."""
    entries = load_messages(project_root)
    if not entries:
        return "(Council thread empty — read .gaijinn/bridge/council.md when available.)"

    tail = entries[-max_messages:]
    lines = ["=== GAIJINN COUNCIL (shared intent map thread) ==="]
    for msg in tail:
        lines.append(f"[{msg.seq}] {msg.author_id} ({msg.author}): {msg.text}")
    lines.append(f"Full thread: {(project_root or Path.cwd()).resolve() / COUNCIL_MD}")
    lines.append('Append material updates: gaijinn council say --as <you> "..."')
    return "\n".join(lines)


def _append_line(jsonl_path: Path, msg: CouncilMessage) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(msg.to_dict(), sort_keys=True) + "\n"
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _render_markdown(
    paths: dict[str, Path],
    entries: list[CouncilMessage],
    *,
    project_prompt: str,
) -> None:
    body = _build_markdown(entries, project_prompt=project_prompt, project_root=paths["md"].parent.parent.parent)
    fd, tmp = tempfile.mkstemp(prefix="council.", suffix=".md", dir=str(paths["bridge"]), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, paths["md"])
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _build_markdown(
    entries: list[CouncilMessage],
    *,
    project_prompt: str,
    project_root: Path | None,
) -> str:
    root = (project_root or Path.cwd()).resolve()
    blueprint_note = ""
    if (root / BLUEPRINT_JSON_PATH).exists():
        blueprint_note = (
            f"- Build manifest: `{BLUEPRINT_JSON_PATH}` (Gaijinn Blueprint / intent map of the environment)\n"
        )
    if (root / INTENT_PATH).exists():
        blueprint_note += f"- Scope lock intent: `{INTENT_PATH}`\n"

    lines = [
        "# Gaijinn Council",
        "",
        "> **One shared thread.** Every human and every agent reads this file before acting. ",
        '> Append via `gaijinn council say --as <author> "message"` — no copy-paste relay between AIs.',
        "",
        "## Protocol",
        "",
        "1. **Read** this file (` .gaijinn/bridge/council.md `) at session start and before substantive replies.",
        '2. **Post** after decisions, questions, or handoffs: `gaijinn council say --as cursor "..."`',
        "3. **User** posts as `--as user` (default). Grok cells as `--as grok --id worker-001`.",
        "4. The **Gaijinn Blueprint** is the intent map of the environment agents work in — discuss it here.",
        "",
        "## Environment",
        "",
    ]
    if project_prompt:
        lines.append(f"**Project prompt:** {project_prompt}")
        lines.append("")
    if blueprint_note:
        lines.extend([blueprint_note.rstrip(), ""])

    tz_name = _council_timezone_name()
    lines.extend(
        [
            f"**Last updated:** {_format_display_ts(_now_iso())}",
            f"**Display timezone:** {tz_name}",
            f"**Messages:** {len(entries)}",
            "",
            "---",
            "",
            "## Thread",
            "",
        ]
    )

    if not entries:
        lines.append('_No messages yet. Start with `gaijinn council say "hello council"`_')
        lines.append("")
    else:
        for msg in entries:
            lines.extend(
                [
                    f"### [{msg.seq}] {msg.author_id} · `{msg.author}` · {_format_display_ts(msg.ts)}",
                    "",
                    msg.text,
                    "",
                ]
            )

    lines.extend(
        [
            "---",
            "",
            "_Auto-generated from `.gaijinn/bridge/council.jsonl` — do not edit by hand; use `gaijinn council say`._",
            "",
        ]
    )
    return "\n".join(lines)


def _read_project_prompt(gaijinn_dir: Path) -> str:
    project_path = gaijinn_dir / "project.json"
    if not project_path.exists():
        return ""
    try:
        payload = json.loads(project_path.read_text(encoding="utf-8"))
        return str(payload.get("project_prompt", ""))
    except (OSError, json.JSONDecodeError):
        return ""


def _council_timezone_name() -> str:
    return os.environ.get("GAIJINN_COUNCIL_TZ", DEFAULT_COUNCIL_TZ).strip() or DEFAULT_COUNCIL_TZ


def _council_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(_council_timezone_name())
    except Exception:
        return ZoneInfo(DEFAULT_COUNCIL_TZ)


def _parse_utc_timestamp(iso_utc: str) -> datetime:
    raw = iso_utc.strip()
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_display_ts(iso_utc: str) -> str:
    """Show Amir-local time first, UTC canonical in parentheses."""
    try:
        utc_dt = _parse_utc_timestamp(iso_utc)
    except ValueError:
        return iso_utc
    local_dt = utc_dt.astimezone(_council_timezone())
    utc_label = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    local_label = local_dt.strftime("%a %b %d, %I:%M %p %Z")
    return f"{local_label} (UTC {utc_label})"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rebuild_council_markdown(
    project_root: Path | None = None,
    *,
    global_council: bool = False,
) -> Path:
    """Regenerate council.md from council.jsonl without appending a message."""
    paths = council_paths(project_root, global_council=global_council)
    ensure_council(project_root, global_council=global_council)
    entries = load_messages(project_root, global_council=global_council)
    prompt = "" if global_council else _read_project_prompt(paths["md"].parent.parent)
    _render_markdown(paths, entries, project_prompt=prompt)
    return paths["md"]
