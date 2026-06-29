"""Per-project metadata helpers — project kind detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import PROJECT_PATH

PROJECT_KINDS = {"obsidian-vault", "python-repo", "mixed"}


def project_kind(project_root: Path | None = None) -> str:
    """Return the project kind from .gaijinn/project.json."""
    root = (project_root or Path.cwd()).resolve()
    payload = _load_project_payload(root)
    kind = str(payload.get("project_kind", "")).strip().lower()
    if kind in PROJECT_KINDS:
        return kind
    extra = payload.get("extra")
    if isinstance(extra, dict):
        nested = str(extra.get("project_kind", "")).strip().lower()
        if nested in PROJECT_KINDS:
            return nested
    if (root / "10_Operations" / "knowledge-linter.py").is_file():
        return "obsidian-vault"
    return "python-repo"


def is_obsidian_vault(project_root: Path) -> bool:
    """True when project_root is an Obsidian vault."""
    return (project_root.resolve() / "10_Operations" / "knowledge-linter.py").is_file()


def vault_linter_script(project_root: Path) -> Path | None:
    root = project_root.resolve()
    script = root / "10_Operations" / "knowledge-linter.py"
    return script if script.is_file() else None


def _load_project_payload(project_root: Path) -> dict[str, Any]:
    path = project_root / PROJECT_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload
