"""run-grid command implementation."""

from __future__ import annotations

from pathlib import Path

import typer

from ..errors import SafetyError
from ..helpers import (
    BLUEPRINT_JSON_PATH,
    GIV_PATH,
    GaijinnError,
    _assign_work_units,
    _copy_worker_tree,
    _create_worktree,
    _load_blueprint_optional,
    _load_giv,
    _prepare_workers_root,
    _project_work_unit,
    _require_file,
    _require_project_state,
    _validate_work_unit_paths,
    _worker_giv,
    _worker_metadata,
    _worker_mode,
    _write_json,
    _write_worker_artifacts,
    render_error,
)
from ..moat_authority import load_latest_decision, refuse_worker_assignment


def _assert_scoped_work_units(work_units) -> None:
    for unit in work_units:
        paths = tuple(unit.allowed_paths)
        if not paths or any(str(path).strip() in {"", "."} for path in paths):
            raise SafetyError(
                "worker scope is empty or root-only",
                cause=f"{unit.id} allowed_paths={list(paths)!r}",
                fix_command="gaijinn plan --workers 2",
            )


def run_grid_cmd(workers: int, force: bool, bootstrap_single_worker: bool = False) -> None:
    """Create isolated worker directories under .gaijinn/workers/."""
    if workers < 1:
        raise typer.BadParameter("--workers must be at least 1")
    state = _require_project_state()
    decision = load_latest_decision()
    if decision is not None:
        refuse_worker_assignment(decision)
    try:
        _require_file(state.intent_path, "compiled intent", "gaijinn compile-prompt")
        _require_file(GIV_PATH, "GIV profile", "gaijinn compile-prompt")
        giv = _load_giv(GIV_PATH)
        blueprint = _load_blueprint_optional(BLUEPRINT_JSON_PATH)
        if blueprint is None:
            if not (bootstrap_single_worker and workers == 1):
                raise SafetyError(
                    "blueprint.json is required before run-grid",
                    cause="multi-worker grids must fail closed without explicit scoped work units",
                    fix_command="gaijinn scan . && gaijinn analyze && gaijinn plan --workers 2",
                )
            work_units = (_project_work_unit(giv),)
        else:
            work_units = blueprint.work_units
            if not work_units:
                raise SafetyError(
                    "blueprint has zero work units",
                    cause=(
                        "gaijinn plan produced work_units=[] — vault straddle, empty graph, "
                        "or all units filtered by completion-ledger.json"
                    ),
                    fix_command="gaijinn scan . && gaijinn analyze && gaijinn plan --workers 2",
                )
        if workers > 1:
            _assert_scoped_work_units(work_units)
        _validate_work_unit_paths(work_units)
        assignments = _assign_work_units(work_units, workers)
        mode, clean_git = _worker_mode()
        _prepare_workers_root(state.workers_path, workers, force)
        worker_entries = []
        for index in range(1, workers + 1):
            worker_name = f"worker-{index:03d}"
            worker_dir = state.workers_path / worker_name
            branch = f"gaijinn/worker-{index}"
            if mode == "git-worktree":
                _create_worktree(worker_dir, branch)
            else:
                _copy_worker_tree(Path.cwd(), worker_dir)
            assigned_units = assignments[index]
            worker_giv = _worker_giv(giv, worker_name, assigned_units, assignments)
            metadata = _worker_metadata(
                worker_name,
                index,
                mode,
                branch if mode == "git-worktree" else None,
                clean_git,
                assigned_units,
            )
            _write_worker_artifacts(worker_dir, worker_name, worker_giv, assigned_units, metadata)
            worker_entries.append(metadata)

        manifest = {
            "schema_version": 1,
            "mode": mode,
            "git_clean": clean_git,
            "worker_count": workers,
            "workers": [entry["worker_id"] for entry in worker_entries],
            "worker_details": worker_entries,
            "sprint": {
                "atomic": True,
                "cancel_supported": False,
                "ready_for_grid_spawn": True,
                "next_command": f"gaijinn grid-spawn --workers {workers}",
            },
        }
        _write_json(state.workers_path / "manifest.json", manifest)
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc
    typer.echo(f"Created {workers} worker directories under {state.workers_path} using {mode}")
