"""Git worktree and mode-detection helpers for Gaijinn CLI commands."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _worker_mode() -> tuple[str, bool | None]:
    if not _inside_git_work_tree():
        return "copy", None
    clean = _git_clean()
    return ("git-worktree", True) if clean else ("copy", False)


def _inside_git_work_tree() -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _git_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == ""
