"""init command implementation."""

from __future__ import annotations

from pathlib import Path

import typer

from ..helpers import (
    BLUEPRINT_SEED_PATH,
    BLUEPRINT_TEMPLATE_PATH,
    DEFAULT_GRAPH_PATH,
    DEFAULT_METRICS_PATH,
    GAIJINN_DIR,
    INTENT_PATH,
    LICENSE_PATH,
    PROJECT_PATH,
    WORKERS_DIR,
    _blueprint_seed,
    _blueprint_template,
    _echo_init_next_steps,
    _ensure_gaijinn_dir,
    _parse_capabilities,
    _write_agent_files_block,
)
from ..helpers.council import ensure_council
from ..state import new_state, write_state


def init_cmd(project_prompt: str, force: bool, blueprint_template: bool, agent_files: bool) -> None:
    """Initialize .gaijinn project state and blueprint seed files."""
    project_prompt = project_prompt.strip()
    if not project_prompt:
        raise typer.BadParameter("PROJECT PROMPT must not be empty")
    if PROJECT_PATH.exists() and not force:
        typer.echo(
            f"Error: {PROJECT_PATH} already exists; use --force to overwrite project state.",
            err=True,
        )
        raise typer.Exit(code=1)

    _ensure_gaijinn_dir()
    ensure_council(project_prompt=project_prompt)
    project_extra = {
        "project_prompt": project_prompt,
        "capabilities": _parse_capabilities(project_prompt),
        "artifacts": {
            "blueprint_seed": str(BLUEPRINT_SEED_PATH),
            "graph": str(DEFAULT_GRAPH_PATH),
            "metrics": str(DEFAULT_METRICS_PATH),
            "intent": str(INTENT_PATH),
            "workers": str(WORKERS_DIR),
            "blueprint_template": str(BLUEPRINT_TEMPLATE_PATH),
        },
    }
    write_state(
        new_state(
            Path.cwd(),
            project_prompt,
            activation_status="active" if LICENSE_PATH.exists() else "inactive",
            extra=project_extra,
        )
    )
    BLUEPRINT_SEED_PATH.write_text(_blueprint_seed(project_prompt), encoding="utf-8")
    if blueprint_template:
        BLUEPRINT_TEMPLATE_PATH.write_text(_blueprint_template(project_prompt), encoding="utf-8")
    if agent_files:
        _write_agent_files_block(project_prompt)
    typer.echo(f"Initialized Loom project in {GAIJINN_DIR}")
    if blueprint_template:
        typer.echo(f"Wrote blueprint template to {BLUEPRINT_TEMPLATE_PATH}")
    if agent_files:
        typer.echo("Updated agent guidance in CLAUDE.md and .cursorrules")
    _echo_init_next_steps(blueprint_template)
