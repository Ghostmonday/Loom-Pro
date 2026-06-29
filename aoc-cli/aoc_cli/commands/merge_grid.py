"""merge-grid command — sequentially merge validated workers into an integration branch."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import typer

from ..blueprint import stable_work_unit_id
from ..errors import ConflictError, GaijinnError, MergeError, MergeValidationError
from ..helpers import _require_project_state, render_error
from ..helpers.merge import (
    COLLECTED_PATH,
    INTEGRATION_BRANCH,
    REPORT_PATH,
    VALIDATED_PATH,
    apply_copy_mode_worker_changes,
    checkout_integration_branch,
    completion_ledger_entries_by_wu,
    compute_merge_structural_score,
    content_hash_for_allowed_paths,
    ensure_worker_branch_committed,
    ledger_entry_matches_current_root,
    load_blueprint_optional,
    load_worker_manifest,
    merge_worker_branch,
    parse_conflict_files_from_error,
    record_merge_governance_history,
    resolve_base_branch,
    resolve_base_ref,
    revert_last_merge,
    run_post_merge_checks,
    upsert_completion_ledger_entries,
    utc_now,
    worker_details_map,
    worker_merge_order,
    write_merge_governance,
    write_merge_json,
)

MergeStrategy = Callable[..., dict[str, Any]]


def _load_validated(project_root: Path) -> dict[str, Any]:
    path = project_root / VALIDATED_PATH
    if not path.exists():
        raise MergeValidationError(
            "validated worker state missing",
            cause=f"expected artifact at {path}",
            fix_command="gaijinn validate-worker",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MergeValidationError(
            "validated.json is invalid JSON",
            cause=str(exc),
            fix_command="gaijinn validate-worker",
        ) from exc
    if not isinstance(payload, dict):
        raise MergeValidationError("validated.json must contain a JSON object", fix_command="gaijinn validate-worker")
    return payload


def _load_collected(project_root: Path) -> dict[str, Any]:
    path = project_root / COLLECTED_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _assigned_units(detail: dict[str, Any], blueprint: Any) -> list[Any]:
    if blueprint is None:
        return []
    assigned = detail.get("assigned_work_units", [])
    if not isinstance(assigned, list):
        return []
    unit_map = {unit.id: unit for unit in blueprint.work_units}
    return [unit_map[str(unit_id)] for unit_id in assigned if str(unit_id) in unit_map]


def _ledger_entries_for_units(project_root: Path, worker_id: str, units: list[Any]) -> list[dict[str, Any]]:
    merged_at = utc_now()
    return [
        {
            "wu_id": stable_work_unit_id(unit.allowed_paths, unit.acceptance_checks),
            "content_hash": content_hash_for_allowed_paths(project_root, unit.allowed_paths),
            "merged_at": merged_at,
            "worker_id": worker_id,
            "allowed_paths": list(unit.allowed_paths),
            "acceptance_checks": list(unit.acceptance_checks),
        }
        for unit in units
    ]


def _units_already_merged(project_root: Path, units: list[Any]) -> bool:
    if not units:
        return False
    ledger = completion_ledger_entries_by_wu(project_root)
    for unit in units:
        stable_id = stable_work_unit_id(unit.allowed_paths, unit.acceptance_checks)
        entry = ledger.get(stable_id)
        if not entry or not ledger_entry_matches_current_root(project_root, entry, unit.allowed_paths):
            return False
    return True


def _sequential_merge(
    *,
    project_root: Path,
    workers_path: Path,
    validated: dict[str, Any],
    base_branch: str,
    base_ref: str,
    dry_run: bool,
    skip_tests: bool,
) -> dict[str, Any]:
    manifest = load_worker_manifest(workers_path)
    details = worker_details_map(manifest)
    blueprint = load_blueprint_optional(project_root)
    collected = _load_collected(project_root)
    collected_workers = collected.get("workers", {})
    if not isinstance(collected_workers, dict):
        collected_workers = {}

    passing = sorted(worker_id for worker_id, result in validated.items() if result.get("passed") is True or dry_run)
    order = worker_merge_order(passing, details, blueprint)

    if not dry_run:
        checkout_integration_branch(project_root, base_ref, dry_run=False)

    worker_results: dict[str, Any] = {}
    merged_sequence: list[str] = []
    merged_count = 0
    already_merged_count = 0
    blocked_count = 0
    conflicted_count = 0
    ledger_entries_written = 0

    for worker_id in order:
        detail = details.get(worker_id, {})
        branch = detail.get("branch")
        worker_dir = workers_path / worker_id
        assigned_units = _assigned_units(detail, blueprint)
        manifest_path = workers_path / "manifest.json"

        if dry_run:
            from ..state import transition_worker_state
            transition_worker_state(manifest_path, worker_id, "merged")
            worker_results[worker_id] = {"status": "merged", "merge_commit": "dry-run", "dry_run": True}
            merged_sequence.append(worker_id)
            merged_count += 1
            continue

        if not branch:
            worker_collected = collected_workers.get(worker_id, {})
            changed = worker_collected.get("changed_files", []) if isinstance(worker_collected, dict) else []
            if not isinstance(changed, list) or not changed:
                if _units_already_merged(project_root, assigned_units):
                    from ..state import transition_worker_state
                    transition_worker_state(manifest_path, worker_id, "already_merged")
                    worker_results[worker_id] = {
                        "status": "already_merged",
                        "reason": "copy-mode worker has no delta and assigned work units match completion ledger",
                        "work_units": [unit.id for unit in assigned_units],
                    }
                    already_merged_count += 1
                    continue
                from ..state import transition_worker_state
                transition_worker_state(manifest_path, worker_id, "blocked")
                worker_results[worker_id] = {
                    "status": "blocked",
                    "reason": "worker has no git branch (copy mode) and no collected file changes",
                }
                blocked_count += 1
                continue
            applied = apply_copy_mode_worker_changes(worker_dir, project_root, changed)
            if not applied:
                from ..state import transition_worker_state
                transition_worker_state(manifest_path, worker_id, "blocked")
                worker_results[worker_id] = {
                    "status": "blocked",
                    "reason": "copy-mode merge found no applicable file changes",
                }
                blocked_count += 1
                continue
            from ..state import transition_worker_state
            transition_worker_state(manifest_path, worker_id, "merged")
            worker_results[worker_id] = {
                "status": "merged",
                "merge_commit": "copy-mode",
                "applied_files": applied,
            }
            ledger_entries_written += upsert_completion_ledger_entries(
                project_root,
                _ledger_entries_for_units(project_root, worker_id, assigned_units),
            )
            merged_sequence.append(worker_id)
            merged_count += 1
            continue

        ensure_worker_branch_committed(worker_dir, str(branch))
        try:
            success, commit, _conflicts = merge_worker_branch(project_root, str(branch), dry_run=False)
        except ConflictError as exc:
            from ..state import transition_worker_state
            transition_worker_state(manifest_path, worker_id, "conflicted")
            worker_results[worker_id] = {
                "status": "conflicted",
                "conflict_files": parse_conflict_files_from_error(exc),
            }
            conflicted_count += 1
            continue

        if not success:
            from ..state import transition_worker_state
            transition_worker_state(manifest_path, worker_id, "blocked")
            worker_results[worker_id] = {"status": "blocked", "reason": "merge failed"}
            blocked_count += 1
            continue

        if not skip_tests:
            tests_ok, _output = run_post_merge_checks(project_root)
            if not tests_ok:
                revert_last_merge(project_root)
                from ..state import transition_worker_state
                transition_worker_state(manifest_path, worker_id, "blocked")
                worker_results[worker_id] = {"status": "blocked", "reason": "tests failed after merge"}
                blocked_count += 1
                continue

        from ..state import transition_worker_state
        transition_worker_state(manifest_path, worker_id, "merged")
        worker_results[worker_id] = {"status": "merged", "merge_commit": commit}
        ledger_entries_written += upsert_completion_ledger_entries(
            project_root,
            _ledger_entries_for_units(project_root, worker_id, assigned_units),
        )
        merged_sequence.append(worker_id)
        merged_count += 1

    return {
        "integration_branch": INTEGRATION_BRANCH,
        "base_ref": base_branch,
        "completed_at": utc_now(),
        "strategy": "sequential",
        "dry_run": dry_run,
        "merge_order": merged_sequence,
        "workers": worker_results,
        "summary": {
            "merged": merged_count,
            "already_merged": already_merged_count,
            "blocked": blocked_count,
            "conflicted": conflicted_count,
            "total": len(order),
            "ledger_entries_written": ledger_entries_written,
        },
    }


_STRATEGIES: dict[str, MergeStrategy] = {
    "sequential": _sequential_merge,
}


def merge_grid_cmd(
    strategy: str = "sequential",
    base_branch: str | None = None,
    skip_tests: bool = False,
    dry_run: bool = False,
) -> None:
    """Merge validated worker branches into gaijinn/integration."""
    try:
        if strategy not in _STRATEGIES:
            raise MergeError(
                f"unsupported merge strategy {strategy!r}",
                cause=f"supported strategies: {', '.join(sorted(_STRATEGIES))}",
                fix_command="gaijinn merge-grid --strategy sequential",
            )

        state = _require_project_state()
        project_root = state.project_root
        validated = _load_validated(project_root)
        resolved_base_branch = base_branch or resolve_base_branch(project_root)
        base_ref = resolve_base_ref(project_root, resolved_base_branch)

        report = _STRATEGIES[strategy](
            project_root=project_root,
            workers_path=state.workers_path,
            validated=validated,
            base_branch=resolved_base_branch,
            base_ref=base_ref,
            dry_run=dry_run,
            skip_tests=skip_tests,
        )
        write_merge_json(project_root / REPORT_PATH, report)
        score = compute_merge_structural_score(project_root)
        write_merge_governance(project_root, score)
        record_merge_governance_history(project_root, score)
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc

    summary = report["summary"]
    typer.echo(
        "Merge complete: "
        f"{summary['merged']} merged, {summary['blocked']} blocked, {summary['conflicted']} conflicted "
        f"→ {REPORT_PATH.as_posix()}"
    )
