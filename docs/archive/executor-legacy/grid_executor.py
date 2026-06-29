"""Grid execution backends — Codex codes the work units from blueprinted isolation."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from .constants import GROK_BINARY, HERMES_BINARY
from .hermes_spawn import build_hermes_argv
from .project_profile import DEEPSEEK_DEFAULT_MODEL, load_executor_profile

CODEX_BINARY = "codex"
DEFAULT_GRID_EXECUTOR = "auto"
VALID_GRID_EXECUTORS = frozenset({"auto", "codex", "grok", "deepseek", "hermes"})


def resolve_grid_executor(requested: str | None = None) -> str:
    """Pick codex, grok, or deepseek for sprint execution (auto prefers codex)."""
    normalized = (requested or DEFAULT_GRID_EXECUTOR).strip().lower()
    if normalized not in VALID_GRID_EXECUTORS:
        raise ValueError(f"executor must be one of: {', '.join(sorted(VALID_GRID_EXECUTORS))}")
    if normalized == "hermes":
        if not shutil.which(HERMES_BINARY):
            raise RuntimeError("hermes executable not found on PATH")
        return "hermes"
    if normalized in {"codex", "deepseek"}:
        if not shutil.which(CODEX_BINARY):
            raise RuntimeError("codex executable not found on PATH (required for codex/deepseek)")
        return normalized
    if normalized == "grok":
        if not shutil.which(GROK_BINARY):
            raise RuntimeError("grok executable not found on PATH")
        return "grok"
    if shutil.which(HERMES_BINARY):
        return "hermes"
    if shutil.which(CODEX_BINARY):
        return "codex"
    if shutil.which(GROK_BINARY):
        return "grok"
    raise RuntimeError("no grid executor found — install hermes, codex, or grok on PATH")


def session_root_from_worker_dir(worker_dir: Path) -> Path:
    """Session/repo root containing .gaijinn/workers/<cell> (read-only context)."""
    workers_dir = worker_dir.resolve()
    if workers_dir.parent.name == "workers" and workers_dir.parent.parent.name == ".gaijinn":
        return workers_dir.parent.parent.parent
    return workers_dir


def execution_cwd_for_worker(worker_dir: Path) -> Path:
    """Writable checkout root — executors must run here, not the shared session tree."""
    return worker_dir.resolve()


def project_root_from_worker_dir(worker_dir: Path) -> Path:
    """Backward-compatible alias for session root (profile loading, not executor cwd)."""
    return session_root_from_worker_dir(worker_dir)


def build_spawn_command(
    *,
    worker_name: str,
    worker_dir: Path,
    full_prompt: str,
    model: str,
    executor: str,
    has_assigned_work: bool = True,
    mock_grid: bool = False,
) -> list[str]:
    """Build subprocess argv for a worker cell (Codex codes by default)."""
    if mock_grid:
        if not has_assigned_work:
            script = f"echo '[{worker_name}] standby — no work assigned';"
            return ["bash", "-c", script]
        script = (
            f"echo '=== MOCK GRID: {worker_name} ==='; "
            "for step in 1 2 3 4 5; do "
            f'echo "[{worker_name}] working step $step"; '
            "sleep 0.4; "
            "done; "
            f"echo '[{worker_name}] build PASS';"
        )
        return ["bash", "-c", script]

    resolved = resolve_grid_executor(executor)
    exec_cwd = execution_cwd_for_worker(worker_dir)
    if resolved == "codex":
        last_message = worker_dir / "codex-last-message.txt"
        return [
            CODEX_BINARY,
            "exec",
            "-C",
            str(exec_cwd),
            "-s",
            "workspace-write",
            "--output-last-message",
            str(last_message),
            full_prompt,
        ]

    if resolved == "deepseek":
        session_root = session_root_from_worker_dir(worker_dir)
        last_message = worker_dir / "codex-last-message.txt"
        spawn_model = (model or DEEPSEEK_DEFAULT_MODEL).strip()
        if spawn_model.startswith("grok-"):
            spawn_model = DEEPSEEK_DEFAULT_MODEL
        profile = (
            os.environ.get("GAIJINN_CODEX_PROFILE", "").strip()
            or load_executor_profile(session_root).get("codex_profile", "").strip()
        )
        cmd = [
            CODEX_BINARY,
            "exec",
            "-C",
            str(exec_cwd),
            "-s",
            "workspace-write",
        ]
        if profile:
            cmd.extend(["--profile", profile])
        cmd.extend(
            [
                "-m",
                spawn_model,
                "--output-last-message",
                str(last_message),
                full_prompt,
            ]
        )
        return cmd

    if resolved == "hermes":
        session_root = session_root_from_worker_dir(worker_dir)
        return build_hermes_argv(
            full_prompt,
            project_root=session_root,
            model=model,
            yolo=True,
            cwd=exec_cwd,
        )

    return [
        GROK_BINARY,
        "-p",
        full_prompt,
        "--model",
        model,
        "--always-approve",
        "--output-format",
        "plain",
        "--cwd",
        str(exec_cwd),
    ]
