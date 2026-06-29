"""compile-prompt command implementation."""

from __future__ import annotations

import json

import typer

from ..helpers import (
    GIV_PATH,
    INTENT_PATH,
    PROJECT_PATH,
    _compile_prompt_summary,
    _ensure_gaijinn_dir,
    _giv_from_profile,
    _intent_text,
    _load_project,
    _render_compile_prompt_summary,
    _require_text,
)
from ..moat import parse_prompt


def compile_prompt_cmd(json_output: bool) -> None:
    """Compile project.json into .gaijinn/intent.txt."""
    project = _load_project()
    prompt = _require_text(project, "project_prompt", PROJECT_PATH)
    profile = parse_prompt(prompt)
    declared = project.get("capabilities")
    if not profile.capabilities and isinstance(declared, list):
        fallback = sorted(str(item).strip() for item in declared if isinstance(item, str) and str(item).strip())
        if fallback:
            profile.capabilities = fallback
    giv = _giv_from_profile(profile)
    summary = _compile_prompt_summary(giv, profile)

    _ensure_gaijinn_dir()
    GIV_PATH.write_text(giv.to_json(), encoding="utf-8")
    INTENT_PATH.write_text(_intent_text(prompt, giv), encoding="utf-8")
    if json_output:
        typer.echo(json.dumps(summary, sort_keys=True))
    else:
        _render_compile_prompt_summary(summary)
