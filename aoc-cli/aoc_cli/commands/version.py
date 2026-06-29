"""version command implementation."""

from __future__ import annotations

import json

import typer

from ..helpers import _package_version


def version_cmd(json_output: bool) -> None:
    """Print the installed Loom version."""
    version = _package_version()
    if json_output:
        typer.echo(json.dumps({"schema_version": 1, "version": version}, sort_keys=True))
    else:
        typer.echo(version)
