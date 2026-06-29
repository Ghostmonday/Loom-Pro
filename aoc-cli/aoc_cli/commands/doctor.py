"""doctor command implementation."""

from __future__ import annotations

import json
import shutil

import typer

from ..helpers import _doctor_diagnostics, _overall_diagnostic_status, _render_diagnostics
from ..helpers.constants import GROK_BINARY, UI_CONTRACT_PATH


def _terminal_bridge_diagnostics() -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    grok_path = shutil.which(GROK_BINARY)
    if grok_path:
        diagnostics.append(
            {
                "name": "terminal:grok",
                "status": "pass",
                "hard_failure": False,
                "detail": f"Grok Build CLI found at {grok_path}",
            }
        )
    else:
        diagnostics.append(
            {
                "name": "terminal:grok",
                "status": "warn",
                "hard_failure": False,
                "detail": "Grok Build CLI not found on PATH; grid-spawn requires `grok`",
            }
        )

    if UI_CONTRACT_PATH.exists():
        diagnostics.append(
            {
                "name": "ui:contract",
                "status": "pass",
                "hard_failure": False,
                "detail": f"UI intent contract present at {UI_CONTRACT_PATH}",
            }
        )
    else:
        diagnostics.append(
            {
                "name": "ui:contract",
                "status": "warn",
                "hard_failure": False,
                "detail": f"UI intent contract not found at {UI_CONTRACT_PATH}",
            }
        )
    return diagnostics


def doctor_cmd(json_output: bool, strict: bool) -> None:
    """Check the local Gaijinn installation and project artifacts."""
    diagnostics = _doctor_diagnostics() + _terminal_bridge_diagnostics()
    payload = {
        "schema_version": 1,
        "status": _overall_diagnostic_status(diagnostics),
        "diagnostics": diagnostics,
    }
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True))
    else:
        _render_diagnostics(diagnostics)
    if strict and payload["status"] == "fail":
        raise typer.Exit(code=2)
