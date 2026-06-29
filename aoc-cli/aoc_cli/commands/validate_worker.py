"""validate-worker command — run merge-pipeline validation gates per worker."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

import typer

from ..errors import GaijinnError, MergeValidationError
from ..helpers import _require_project_state, render_error
from ..helpers.council import load_messages
from ..helpers.handoff import evaluate_handoff_transaction_integrity, handoff_gate_for_worker
from ..helpers.merge import (
    COLLECTED_PATH,
    VALIDATED_PATH,
    acceptance_checks_for_worker,
    changed_files,
    deleted_files,
    detect_trespasses,
    invariant_violations,
    load_blueprint_optional,
    load_worker_giv,
    load_worker_manifest,
    output_log_path,
    pytest_targets_for_worker,
    resolve_base_ref,
    run_acceptance_check,
    scan_denied_command_violations,
    sibling_dependency_deferral,
    utc_now,
    worker_details_map,
    write_merge_json,
)


def _load_collected(project_root: Path) -> dict[str, Any]:
    path = project_root / COLLECTED_PATH
    if not path.exists():
        raise MergeValidationError(
            "collected worker state missing",
            cause=f"expected artifact at {path}",
            fix_command="gaijinn collect",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MergeValidationError(
            "collected.json is invalid JSON",
            cause=str(exc),
            fix_command="gaijinn collect",
        ) from exc
    if not isinstance(payload, dict):
        raise MergeValidationError("collected.json must contain a JSON object", fix_command="gaijinn collect")
    return payload


def _localized_test_env(worker_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["GAIJINN_PROJECT_ROOT"] = str(worker_dir.resolve())
    return env


def _matched_sibling_path(path: str, sibling_paths: set[str]) -> str | None:
    normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
    for sibling in sorted(sibling_paths):
        rule = PurePosixPath(sibling.replace("\\", "/")).as_posix().rstrip("/")
        if normalized == rule or normalized.startswith(f"{rule}/"):
            return sibling
    return None


def _validate_single_worker(
    worker_id: str,
    worker_dir: Path,
    project_root: Path,
    base_ref: str,
    manifest_detail: dict[str, Any] | None,
    manifest_details: dict[str, dict[str, Any]],
    blueprint: Any,
) -> dict[str, Any]:
    if not worker_dir.is_dir():
        raise MergeValidationError(
            f"worker directory missing for {worker_id}",
            cause=f"expected directory at {worker_dir}",
            fix_command="gaijinn run-grid --workers 2 --force",
        )

    giv = load_worker_giv(worker_dir)
    changed = changed_files(
        worker_dir,
        base_ref,
        baseline_dir=project_root,
        scope_paths=giv.allowed_paths,
    )
    trespasses = detect_trespasses(changed, giv)
    path_gate = {"passed": not trespasses, "trespasses": trespasses}
    sibling_paths = set(giv.sibling_denied_paths)
    scope_violations = [
        f"{path} (OWNED BY SIBLING WORKER: {_matched_sibling_path(path, sibling_paths)})"
        if _matched_sibling_path(path, sibling_paths)
        else path
        for path in trespasses
    ]
    scope_gate = {"passed": not scope_violations, "violations": scope_violations}

    log_text = (
        output_log_path(worker_dir).read_text(encoding="utf-8", errors="replace")
        if output_log_path(worker_dir).exists()
        else ""
    )
    denied_violations = scan_denied_command_violations(log_text, giv.denied_commands)
    denied_gate = {"passed": not denied_violations, "violations": denied_violations}

    checks = acceptance_checks_for_worker(
        worker_dir,
        manifest_detail,
        blueprint,
        project_root=project_root,
    )
    scoped_pytest_targets = pytest_targets_for_worker(worker_dir, giv.allowed_paths, changed)
    defer_tests, awaiting_units, awaiting_workers = sibling_dependency_deferral(
        worker_id,
        manifest_detail,
        manifest_details,
        blueprint,
    )
    mock_grid = os.environ.get("GAIJINN_MOCK_GRID", "").strip().lower() in {"1", "true", "yes", "on"}
    mock_completed = mock_grid and "build PASS" in log_text
    test_outputs: list[str] = []
    test_exit = 0
    tests_ran = False
    if mock_completed and not defer_tests:
        tests_gate = {
            "passed": True,
            "deferred": False,
            "reason": "mock_grid_build_pass",
            "exit_code": 0,
            "output_truncated": "",
            "ran": False,
        }
    elif mock_completed or defer_tests:
        tests_gate = {
            "passed": True,
            "deferred": True,
            "reason": "awaiting_sibling_merge",
            "awaiting_units": awaiting_units,
            "awaiting_workers": awaiting_workers,
            "exit_code": 0,
            "output_truncated": "",
            "ran": False,
        }
    elif not mock_completed:
        runnable = {"pytest", "ruff", "vault_linter"}
        for check in checks:
            if check == "unresolved_domain":
                test_exit = max(test_exit, 1)
                test_outputs.append("=== unresolved_domain ===\nwork_unit.domain is missing or unsupported")
                tests_ran = True
                continue
            if check not in runnable:
                continue
            if check == "pytest" and not scoped_pytest_targets and "vault_linter" in checks:
                continue
            tests_ran = True
            exit_code, output = run_acceptance_check(
                worker_dir,
                check,
                env=_localized_test_env(worker_dir),
                toolchain_root=project_root,
                pytest_targets=scoped_pytest_targets if check == "pytest" else None,
            )
            test_exit = max(test_exit, exit_code)
            if output.strip():
                test_outputs.append(f"=== {check} ===\n{output.strip()}")
        tests_gate = {
            "passed": test_exit == 0,
            "exit_code": test_exit,
            "output_truncated": "\n\n".join(test_outputs)[:4000] if test_outputs else "",
            "ran": tests_ran,
        }

    inv_violations = invariant_violations(changed, giv, deleted_files=deleted_files(worker_dir, base_ref))
    invariants_gate = {"passed": not inv_violations, "violations": inv_violations}

    handoff_gate = handoff_gate_for_worker(
        worker_id,
        log_text,
        trespasses,
        sibling_paths,
        blueprint,
    )

    passed = all(
        gate["passed"]
        for gate in (
            path_gate,
            scope_gate,
            denied_gate,
            handoff_gate,
            tests_gate if tests_ran else {"passed": True},
            invariants_gate,
        )
    )
    return {
        "validated_at": utc_now(),
        "passed": passed,
        "gates": {
            "path_allowlist": path_gate,
            "scope_isolation": scope_gate,
            "denied_commands": denied_gate,
            "handoff_protocol": handoff_gate,
            "tests": tests_gate,
            "invariants": invariants_gate,
        },
    }


def validate_worker_cmd(worker_id: str | None = None, workers_dir: Path | None = None) -> None:
    """Validate one or all collected workers and write .gaijinn/merge/validated.json."""
    try:
        state = _require_project_state()
        project_root = state.project_root
        workers_path = workers_dir or state.workers_path
        collected = _load_collected(project_root)
        base_ref = str(collected.get("base_ref") or resolve_base_ref(project_root, "main"))
        manifest = load_worker_manifest(workers_path)
        details = worker_details_map(manifest)
        blueprint = load_blueprint_optional(project_root)

        collected_workers = collected.get("workers", {})
        if not isinstance(collected_workers, dict) or not collected_workers:
            raise MergeValidationError(
                "collected.json contains no workers",
                fix_command="gaijinn collect",
            )

        targets = [worker_id] if worker_id else sorted(collected_workers)
        if worker_id and worker_id not in collected_workers:
            raise MergeValidationError(
                f"worker {worker_id} was not collected",
                cause="run collect before validating a single worker",
                fix_command="gaijinn collect",
            )

        results: dict[str, Any] = {}
        for target in targets:
            results[target] = _validate_single_worker(
                target,
                workers_path / target,
                project_root,
                base_ref,
                details.get(target),
                details,
                blueprint,
            )

        handoff_integrity = evaluate_handoff_transaction_integrity(
            project_root=project_root,
            workers_path=workers_path,
            manifest_details=details,
            base_ref=base_ref,
            council_messages=[message.to_dict() for message in load_messages(project_root)],
        )
        for entry in results.values():
            if isinstance(entry, dict):
                entry["handoff_integrity"] = handoff_integrity
                if not handoff_integrity.get("transaction_bus_synchronized", True):
                    entry["passed"] = False
                    gates = entry.setdefault("gates", {})
                    if isinstance(gates, dict):
                        gates["handoff_bus"] = {
                            "passed": False,
                            "pending_tickets": handoff_integrity.get("pending_tickets", []),
                        }

        write_merge_json(project_root / VALIDATED_PATH, results)
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc

    passed = sum(1 for item in results.values() if item.get("passed"))
    typer.echo(f"Validated {len(results)} worker(s); {passed} passed → {VALIDATED_PATH.as_posix()}")
