"""audit command — zero-mutation structural readiness evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from ..errors import GaijinnError
from ..helpers import render_error
from ..helpers.audit import (
    AUDIT_REPORT_PATH,
    print_brutalist_report,
    run_structural_audit,
    write_audit_report,
)


def audit_cmd(
    target_dir: Path,
    *,
    json_only: bool = False,
    report_path: Path | None = None,
    write_report: bool = True,
) -> None:
    """Evaluate repository readiness for multi-agent parallel execution without mutating code."""
    try:
        root = target_dir.resolve()
        if not root.is_dir():
            raise GaijinnError(
                "audit target is not a directory",
                cause=str(root),
                fix_command=f"gaijinn audit {target_dir}",
            )
        if not (root / ".git").exists():
            raise GaijinnError(
                "audit target is not a git repository",
                cause=f"expected .git at {root / '.git'}",
                fix_command="git init && gaijinn audit .",
            )

        payload = run_structural_audit(root)
        destination = report_path or (root / AUDIT_REPORT_PATH)
        if write_report:
            write_audit_report(root, payload, destination)

        if json_only:
            typer.echo(json.dumps(payload, indent=2, sort_keys=True))
            return

        print_brutalist_report(payload)
        if write_report:
            typer.echo(f"Audit report → {destination.as_posix()}")
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc
