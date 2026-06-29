"""status command implementation."""

from __future__ import annotations

import json
import shutil

import typer

from ..helpers import _render_status, _status_payload
from ..helpers.constants import GROK_BINARY
from ..helpers.scan import validate_grid_readiness


def status_cmd(json_output: bool, strict: bool) -> None:
    """Summarize current .gaijinn project state."""
    payload = _status_payload()
    grid_readiness = validate_grid_readiness()
    payload["terminal_bridge"] = {
        "grok_available": shutil.which(GROK_BINARY) is not None,
        "grid_spawn_ready": grid_readiness["ready"],
        "blocked_reasons": grid_readiness["blocked_reasons"],
        "atomic_sprint": grid_readiness["atomic_sprint"],
        "cancel_supported": grid_readiness["cancel_supported"],
        "output_logs_present": grid_readiness["output_logs_present"],
    }
    if grid_readiness["ready"] and payload["state"] == "ready":
        payload["next_recommended_command"] = "gaijinn grid-spawn --workers 2"
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True))
    else:
        _render_status(payload)
        bridge = payload["terminal_bridge"]
        typer.echo(f"terminal_bridge.grok_available: {bridge['grok_available']}")
        typer.echo(f"terminal_bridge.grid_spawn_ready: {bridge['grid_spawn_ready']}")
        if bridge["blocked_reasons"]:
            typer.echo(f"terminal_bridge.blocked: {', '.join(bridge['blocked_reasons'])}")
    merge_pipeline = payload.get("merge_pipeline", {})
    if strict and payload["state"] in {"degraded", "tripped"}:
        raise typer.Exit(code=2)
    if strict and (int(merge_pipeline.get("blocked", 0) or 0) > 0 or int(merge_pipeline.get("conflicted", 0) or 0) > 0):
        raise typer.Exit(code=2)
