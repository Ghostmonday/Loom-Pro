"""gaijinn council — shared multi-agent conversation bridge."""

from __future__ import annotations

import time

import typer

from ..errors import GaijinnError
from ..helpers import _require_project_state, render_error
from ..helpers.council import (
    _format_display_ts,
    append_message,
    ensure_council,
    load_messages,
    machine_council_address,
    rebuild_council_markdown,
    render_council_markdown,
)


def council_say_cmd(
    message: str,
    author: str,
    author_id: str | None,
    role: str,
    global_council: bool,
) -> None:
    """Append a message to the shared council thread."""
    try:
        if not global_council:
            _require_project_state()
        msg = append_message(
            message,
            author=author,
            author_id=author_id,
            role=role,
            global_council=global_council,
        )
        path = machine_council_address() if global_council else str(ensure_council(global_council=False))
        typer.echo(f"Posted [{msg.seq}] as {msg.author_id} → {path}")
    except (GaijinnError, ValueError) as exc:
        raise typer.BadParameter(render_error(exc) if isinstance(exc, GaijinnError) else str(exc)) from exc


def council_show_cmd(json_output: bool, tail: int, global_council: bool) -> None:
    """Print the council thread."""
    try:
        if not global_council:
            _require_project_state()
        ensure_council(global_council=global_council)
        if json_output:
            import json

            entries = load_messages(global_council=global_council)
            if tail > 0:
                entries = entries[-tail:]
            typer.echo(json.dumps([entry.to_dict() for entry in entries], indent=2, sort_keys=True))
            return

        if tail > 0:
            entries = load_messages(global_council=global_council)
            for entry in entries[-tail:]:
                typer.echo(
                    f"[{entry.seq}] {entry.author_id} ({entry.author}) · {_format_display_ts(entry.ts)}: {entry.text}"
                )
            return

        typer.echo(render_council_markdown(global_council=global_council))
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc


def council_watch_cmd(poll_interval: float) -> None:
    """Watch council.md and print new messages (for humans monitoring the thread)."""
    try:
        _require_project_state()
        ensure_council()
        seen = len(load_messages())
        typer.echo(f"Watching {machine_council_address()} (poll {poll_interval}s). Ctrl+C to stop.")
        while True:
            time.sleep(poll_interval)
            entries = load_messages()
            if len(entries) > seen:
                for entry in entries[seen:]:
                    typer.echo(f"[{entry.seq}] {entry.author_id}: {entry.text}")
                seen = len(entries)
    except KeyboardInterrupt:
        typer.echo("Stopped.")
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc


def council_init_cmd() -> None:
    """Create or refresh the council bridge files."""
    try:
        _require_project_state()
        path = ensure_council()
        typer.echo(f"Council ready at {path}")
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc


def council_rebuild_cmd(global_council: bool) -> None:
    """Regenerate council.md from council.jsonl (fixes display formatting)."""
    try:
        if not global_council:
            _require_project_state()
        path = rebuild_council_markdown(global_council=global_council)
        typer.echo(f"Rebuilt council markdown → {path}")
    except (GaijinnError, ValueError) as exc:
        raise typer.BadParameter(render_error(exc) if isinstance(exc, GaijinnError) else str(exc)) from exc
