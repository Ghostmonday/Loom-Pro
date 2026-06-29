"""loom hermes — Hermes chat session from the terminal (council-backed)."""

from __future__ import annotations

import os
import shutil
import subprocess

import typer

from ..errors import GaijinnError
from ..helpers import _require_project_state, render_error
from ..helpers.council import ensure_council, machine_council_address


def _hermes_binary() -> str:
    path = shutil.which("hermes")
    if path is None:
        raise typer.BadParameter(
            "hermes executable not found on PATH.\nInstall Hermes Agent or add it to PATH, then retry."
        )
    return path


def _hermes_argv(hermes: str, prompt: str, *, model: str = "") -> list[str]:
    argv = [hermes, "-z", prompt]
    if model:
        return [hermes, "-m", model, "-z", prompt]
    return argv


def _council_prompt(user_message: str) -> str:
    ensure_council(global_council=True)
    council_path = machine_council_address()
    return (
        f"Read the file {council_path} for multi-agent context (Gaijinn Council).\n"
        f"User message from Gaijinn terminal: {user_message}\n"
        "Reply concisely. Then run:\n"
        'gaijinn council say --global --as hermes --id hermes "one-line summary of your reply"'
    )


def hermes_cmd(
    message: str | None,
    interactive: bool,
    global_council: bool,
) -> None:
    """Open a Hermes chat session from the Gaijinn terminal."""
    try:
        if not global_council:
            _require_project_state()
        hermes = _hermes_binary()
        ensure_council(global_council=global_council)
        council_path = machine_council_address()

        hermes_model = os.environ.get("HERMES_DEFAULT_MODEL", "").strip()

        if message:
            prompt = _council_prompt(message.strip())
            typer.echo(f"⌁ Hermes session · council: {council_path}")
            result = subprocess.run(_hermes_argv(hermes, prompt, model=hermes_model), check=False)
            if result.returncode != 0:
                raise typer.Exit(code=result.returncode)
            return

        if interactive:
            typer.echo(f"⌁ Hermes interactive · council: {council_path}")
            typer.echo(
                "Council protocol: read council.md before replies; "
                'post with `gaijinn council say --global --as hermes "..."`'
            )
            os.execvp(hermes, [hermes, "chat"])  # noqa: S606

        # Default: one-shot council status
        prompt = _council_prompt("Read the machine council and give a one-sentence status.")
        typer.echo(f"⌁ Hermes session · council: {council_path}")
        result = subprocess.run(_hermes_argv(hermes, prompt, model=hermes_model), check=False)
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)

    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc
