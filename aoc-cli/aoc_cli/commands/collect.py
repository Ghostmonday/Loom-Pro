"""collect command — gather worker execution state for the merge pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from ..errors import CollectError, GaijinnError
from ..helpers import _require_project_state, render_error
from ..helpers.handoff import sync_handoff_queue_at_collect
from ..helpers.merge import (
    COLLECTED_PATH,
    classify_worker_status,
    detect_trespasses,
    diff_summary,
    intent_hash,
    load_worker_giv,
    load_worker_manifest,
    resolve_base_branch,
    resolve_base_ref,
    utc_now,
    worker_details_map,
    write_merge_json,
)
from ..helpers.merge import changed_files as worker_changed_files


def collect_cmd(workers_dir: Path | None = None) -> None:
    """Collect worker state and write .gaijinn/merge/collected.json."""
    try:
        state = _require_project_state()
        workers_path = workers_dir or state.workers_path
        manifest = load_worker_manifest(workers_path)
        details = worker_details_map(manifest)
        worker_ids = manifest.get("workers", [])
        if not isinstance(worker_ids, list) or not worker_ids:
            raise CollectError(
                "worker manifest contains no workers",
                fix_command="gaijinn run-grid --workers 2",
            )

        project_root = state.project_root
        base_branch = resolve_base_branch(project_root)
        base_ref = resolve_base_ref(project_root, base_branch)

        workers_payload: dict[str, Any] = {}
        for worker_id in worker_ids:
            worker_name = str(worker_id)
            worker_dir = workers_path / worker_name
            if not worker_dir.is_dir():
                raise CollectError(
                    f"worker directory missing for {worker_name}",
                    cause=f"expected directory at {worker_dir}",
                    fix_command="gaijinn run-grid --workers 2 --force",
                )

            giv = load_worker_giv(worker_dir)
            detail = details.get(worker_name)
            status = classify_worker_status(
                worker_dir,
                giv,
                base_ref,
                detail,
                baseline_dir=project_root,
            )
            changed = worker_changed_files(
                worker_dir,
                base_ref,
                baseline_dir=project_root,
                scope_paths=giv.allowed_paths,
            )
            trespasses = detect_trespasses(changed, giv) if changed else []

            entry: dict[str, Any] = {
                "status": status,
                "allowed_paths": list(giv.allowed_paths),
                "intent_hash": intent_hash(worker_dir),
                "trespasses": trespasses,
            }
            if status in {"completed", "dirty"} and changed:
                entry["diff_summary"] = diff_summary(
                    worker_dir,
                    base_ref,
                    baseline_dir=project_root,
                    scope_paths=giv.allowed_paths,
                )
            if changed:
                entry["changed_files"] = changed
            workers_payload[worker_name] = entry

        payload = {
            "schema_version": 1,
            "collected_at": utc_now(),
            "base_branch": base_branch,
            "base_ref": base_ref,
            "workers": workers_payload,
        }
        write_merge_json(project_root / COLLECTED_PATH, payload)
        handoff_queue = sync_handoff_queue_at_collect(
            project_root=project_root,
            workers_path=workers_path,
            manifest_details=details,
            base_ref=base_ref,
        )
    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc

    completed = sum(1 for item in workers_payload.values() if item.get("status") == "completed")
    typer.echo(f"Collected {len(workers_payload)} worker(s); {completed} completed → {COLLECTED_PATH.as_posix()}")
    pending = handoff_queue.get("pending_tickets", [])
    dropped_scaffold = int(handoff_queue.get("dropped_scaffold_tickets", 0) or 0)
    if pending or handoff_queue.get("receipts_emitted") or dropped_scaffold:
        typer.echo(
            "Handoff queue: "
            f"{handoff_queue.get('handoff_tickets_resolved', 0)}/"
            f"{handoff_queue.get('handoff_tickets_raised', 0)} resolved; "
            f"{len(pending)} pending" + (f"; {dropped_scaffold} scaffold dropped" if dropped_scaffold else "")
        )
