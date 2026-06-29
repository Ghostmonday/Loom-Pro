"""I/O and project-state helpers for Gaijinn CLI commands."""

from __future__ import annotations

import importlib
import json
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import typer

from ..blueprint import Blueprint, BlueprintValidationError
from ..errors import GaijinnError, PrerequisiteError, ValidationError, render_error
from ..giv import GIV, GIVValidationError
from ..state import StateError, ensure_state, state_payload
from .constants import DEFAULT_GRAPH_PATH, DEFAULT_METRICS_PATH, GAIJINN_DIR, PROJECT_PATH

# ── State migration bridge ──────────────────────────────────────────────


def migrate_persisted_state_paths() -> None:
    """Mirror .gaijinn/ → .loom/ and ~/.gaijinn/ → ~/.loom/ for backward compat.

    Runs once per session on first access. Harmless no-op when already migrated.
    """
    # 1. Project-level state
    old_local = Path(".gaijinn")
    new_local = Path(".loom")
    if old_local.is_dir() and not new_local.exists():
        try:
            shutil.copytree(old_local, new_local, dirs_exist_ok=True)
            (new_local / "migration.receipt").write_text(
                "MIGRATION_PASS_01: SUCCESS\n", encoding="utf-8"
            )
        except OSError:
            pass  # Graceful fallback — read-only fs or test mock

    # 2. Global-level user state
    old_global = Path.home() / ".gaijinn"
    new_global = Path.home() / ".loom"
    if old_global.is_dir() and not new_global.exists():
        try:
            shutil.copytree(old_global, new_global, dirs_exist_ok=True)
        except OSError:
            pass


# ── I/O helpers ────────────────────────────────────────────────────────

# Run state migration once at import time so existing .gaijinn/ data is
# available under .loom/ without waiting for a specific CLI command.
migrate_persisted_state_paths()


def _ensure_gaijinn_dir() -> None:
    GAIJINN_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json_artifact(path: Path, artifact_name: str, fix_command: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PrerequisiteError(
            f"missing {artifact_name} at {path}",
            fix_command=fix_command,
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"invalid JSON in {path}",
            cause=f"line {exc.lineno}, column {exc.colno}: {exc.msg}",
            fix_command=fix_command,
        ) from exc
    except OSError as exc:
        raise ValidationError(f"cannot read {artifact_name} at {path}", cause=str(exc)) from exc

    if not isinstance(payload, dict):
        raise ValidationError(f"{artifact_name} at {path} must contain an object")
    schema_version = payload.get("schema_version", 1)
    if schema_version != 1:
        raise ValidationError(
            f"unsupported {artifact_name} schema_version",
            cause=f"expected 1; found {schema_version!r}",
            fix_command=fix_command,
        )
    return payload


def _require_file(path: Path, name: str, fix_command: str) -> None:
    if not path.exists():
        raise PrerequisiteError(f"missing {name} at {path}", fix_command=fix_command)


def _read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _preview_license_key(license_key: str) -> str:
    if len(license_key) <= 8:
        return "*" * len(license_key)
    return f"{license_key[:4]}...{license_key[-4:]}"


def _package_version() -> str:
    try:
        package = importlib.import_module("aoc_cli")
        version = getattr(package, "__version__", None)
        if isinstance(version, str) and version:
            return version
    except Exception:  # noqa: S110
        pass
    try:
        from importlib.metadata import version as metadata_version

        return metadata_version("gaijinn")
    except Exception:
        return "unknown"


def _summary_list(values: Any) -> str:
    items = [str(value) for value in values if str(value).strip()]
    return ", ".join(items) if items else "none"


# ── State / project helpers ────────────────────────────────────────────


def _load_project() -> dict[str, Any]:
    return state_payload(_require_project_state())


def _require_text(payload: Mapping[str, Any], key: str, source: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise typer.BadParameter(f"{source} must contain a non-empty `{key}` string")
    return value.strip()


def _require_project_state():
    try:
        return ensure_state(Path.cwd())
    except StateError as exc:
        raise typer.BadParameter(render_error(exc)) from exc


def _optional_project_state():
    if not PROJECT_PATH.exists():
        return None
    return _require_project_state()


# ── Graph / metrics / GIV loaders ──────────────────────────────────────


def _project_analysis_paths(graph: Path, output: Path) -> tuple[Path, Path]:
    state = _optional_project_state()
    if state is None:
        return graph, output
    if graph == DEFAULT_GRAPH_PATH:
        graph = state.graph_path
    if output == DEFAULT_METRICS_PATH:
        output = state.metrics_path
    return graph, output


def _load_graph(path: Path) -> dict[str, Any]:
    try:
        return _load_json_artifact(path, "graph JSON", "gaijinn scan .")
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc


def _load_metrics(path: Path) -> dict[str, Any]:
    try:
        return _load_json_artifact(path, "metrics JSON", "gaijinn analyze")
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc


def _load_giv(path: Path) -> GIV:
    try:
        payload = _load_json_artifact(path, "GIV profile", "gaijinn compile-prompt")
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc
    try:
        return GIV.from_dict(payload)
    except GIVValidationError as exc:
        raise typer.BadParameter(f"invalid GIV profile at {path}: {exc}") from exc


def _load_blueprint_optional(path: Path) -> Blueprint | None:
    if not path.exists():
        return None
    payload = _load_json_artifact(path, "blueprint JSON", "gaijinn plan --workers 2")
    try:
        return Blueprint.from_dict(payload)
    except BlueprintValidationError as exc:
        raise ValidationError(
            f"invalid blueprint JSON at {path}",
            cause=str(exc),
            fix_command="gaijinn plan --workers 2",
        ) from exc
