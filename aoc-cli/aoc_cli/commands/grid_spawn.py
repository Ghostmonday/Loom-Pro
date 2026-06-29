"""grid-spawn command — spool Codex agents from blueprinted worker handoffs.

Reads .gaijinn/workers/manifest.json + per-worker giv.json and WORK_UNIT.md,
spawns Codex per cell, captures output (atomic sprint, no cancel).
"""

from __future__ import annotations

import json
import os
import shutil  # noqa: F401 — patched by tests for spawn timeout handling
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import typer

from ..errors import GridSpawnError, SprintError
from ..helpers import GaijinnError, _require_project_state, render_error
from ..helpers.constants import (
    DEFAULT_GRID_MODEL,
    OUTPUT_LOG_FILENAME,
)
from ..helpers.council import council_excerpt_for_prompt, publish_handoff_tickets_from_log
from ..helpers.handoff import (
    build_sibling_handoff_map,
    format_handoff_protocol_block,
    format_pending_handoffs_ingest_block,
    load_handoff_queue,
    pending_tickets_for_worker,
)
from ..helpers.merge import load_blueprint_optional
from ..helpers.scan import validate_grid_readiness

CODEX_BINARY = "codex"


def _grid_mode(n: int) -> tuple[str, int, int]:
    """Return (layout_mode, cols, rows) based on agent count.

    Perfect squares → grid layout. Non-perfect squares → list view.
    """
    if n == 4:
        return ("2x2", 2, 2)
    if n == 9:
        return ("3x3", 3, 3)
    if n == 16:
        return ("4x4", 4, 4)
    return ("list", 1, n)


def _read_manifest(state: Any) -> dict[str, Any]:
    """Read the worker manifest."""
    manifest_path = state.workers_path / "manifest.json"
    if not manifest_path.exists():
        raise GridSpawnError(
            f"Worker manifest not found at {manifest_path}.",
            cause="run-grid has not created worker handoffs yet",
            fix_command="gaijinn run-grid --workers N",
        )
    with manifest_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_worker_giv(worker_dir: Path) -> dict[str, Any]:
    """Read the per-worker GIV contract."""
    giv_path = worker_dir / "giv.json"
    if not giv_path.exists():
        return {}
    with giv_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_worker_metadata(worker_dir: Path) -> dict[str, Any]:
    """Read per-worker metadata if present."""
    metadata_path = worker_dir / "metadata.json"
    if not metadata_path.exists():
        return {}
    with metadata_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_worker_work_unit(worker_dir: Path) -> str:
    """Read the per-worker work unit/task description."""
    work_unit_path = worker_dir / "WORK_UNIT.md"
    intent_path = worker_dir / "WORKER_INTENT.txt"

    if work_unit_path.exists():
        return work_unit_path.read_text(encoding="utf-8")
    if intent_path.exists():
        return intent_path.read_text(encoding="utf-8")
    return "Implement the assigned changes within the locked scope."


def _write_manifest_atomic(manifest_path: Path, payload: dict[str, Any]) -> None:
    """Atomically write a worker manifest."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{manifest_path.name}.",
        suffix=".tmp",
        dir=str(manifest_path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, manifest_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _build_task_prompt(
    worker_name: str,
    work_unit_text: str,
    giv: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    *,
    blueprint: Any = None,
    project_root: Path | None = None,
) -> str:
    """Build the Grok Build prompt from assigned task + scope lock constraints."""
    metadata = metadata or {}
    allowed = giv.get("allowed_paths", [])
    denied = giv.get("denied_paths", [])
    sibling_denied = set(giv.get("sibling_denied_paths", []))
    sibling_handoff_map = build_sibling_handoff_map(sorted(sibling_denied), blueprint)
    structural_tokens = giv.get("structural_tokens", {})
    assigned_units = metadata.get("assigned_work_units", [])
    token_names = []
    if structural_tokens.get("scope_strict", True):
        token_names.append("SCOPE_STRICT")
    if structural_tokens.get("no_sibling_trespass", True):
        token_names.append("NO_SIBLING_TRESPASS")
    if structural_tokens.get("handoff_only", True):
        token_names.append("HANDOFF_ONLY")

    lines = [
        "You are a Gaijinn-governed subagent. Execute the assigned task exactly.",
        "",
        "=== SCOPE LAW ===",
        f"WORKER ID: {worker_name}",
        f"ASSIGNED WORK UNITS: {', '.join(assigned_units) if assigned_units else 'none'}",
        f"GAIJINN_TOKENS: {', '.join(token_names)}",
        "",
        "ALLOWED WRITE PATHS:",
        *([f"- {path}" for path in allowed] if allowed else ["- none"]),
        "",
        "PROHIBITED WRITE PATHS:",
        *(
            [f"- {path}{' (OWNED BY SIBLING WORKER)' if path in sibling_denied else ''}" for path in denied]
            if denied
            else ["- none"]
        ),
        "",
        "OPERATIONAL INVARIANTS:",
        "- Do not edit prohibited paths.",
        "- If a sibling-owned path is required, emit a HANDOFF ticket (see protocol below).",
        "- Do not run denied commands.",
        "",
        "CONVERGENCE CHECK:",
        "- Any git diff outside the allowlist fails validation.",
        "",
        format_handoff_protocol_block(worker_name, allowed, sibling_handoff_map),
    ]

    if project_root is not None:
        queue = load_handoff_queue(project_root)
        pending = pending_tickets_for_worker(
            worker_name,
            assigned_units,
            queue.get("pending_tickets", []),
        )
        ingest_block = format_pending_handoffs_ingest_block(pending)
        if ingest_block:
            lines.extend(["", ingest_block])

    lines.extend(
        [
            "",
            "=== ASSIGNED TASK ===",
            work_unit_text.strip(),
            "",
            council_excerpt_for_prompt(),
            "",
            "=== EXECUTION RULES ===",
            "- Run to completion. Do not stop until the assigned task is finished.",
            "- Verify your changes compile/build before reporting done.",
            "- Report errors honestly in the output.",
            "- Post material updates to the council thread when done (see path above).",
        ]
    )

    return "\n".join(lines)


def _spawn_worker(
    worker_name: str,
    worker_dir: Path,
    task_prompt: str,
    model: str = DEFAULT_GRID_MODEL,
) -> subprocess.Popen:
    """Spawn Codex for a single worker cell."""
    log_path = worker_dir / OUTPUT_LOG_FILENAME
    last_message = worker_dir / "codex-last-message.txt"
    cmd: list[str] = [
        CODEX_BINARY,
        "exec",
        "-C",
        str(worker_dir.resolve()),
        "-s",
        "workspace-write",
        "--output-last-message",
        str(last_message),
        task_prompt,
    ]

    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"=== LOOM GRID SPAWN: {worker_name} ===\n")
        log_file.write(f"Executor: codex\n")
        log_file.write(f"Model: {model}\n")
        log_file.write(f"CWD: {worker_dir}\n")
        log_file.write(f"Started: {time.ctime()}\n")
        log_file.write(f"Command: {' '.join(cmd)}\n")
        log_file.write("=" * 60 + "\n\n")
        log_file.flush()

        return subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(worker_dir.resolve()),
        )


def _ensure_grid_spawn_prerequisites(state: Any, workers: int) -> dict[str, Any]:
    from ..helpers.stealth import operator_mode

    readiness = validate_grid_readiness(state.metrics_path, state.workers_path)
    if not readiness["ready"]:
        if operator_mode():
            typer.echo(
                f"  operator bypass: grid readiness gate skipped ({', '.join(readiness['blocked_reasons'])})",
                err=True,
            )
        else:
            reasons = ", ".join(readiness["blocked_reasons"])
            raise GridSpawnError(
                f"Grid spawn blocked: {reasons}",
                cause="metrics or worker handoffs are not sprint-ready",
                fix_command="gaijinn analyze && gaijinn run-grid --workers 2",
            )
    manifest = _read_manifest(state)
    registered_workers = manifest.get("worker_details", manifest.get("workers", []))
    if len(registered_workers) != workers:
        raise GridSpawnError(
            f"Manifest has {len(registered_workers)} workers but --workers={workers} specified.",
            fix_command=f"gaijinn run-grid --workers {workers}",
        )
    missing = [
        f"worker-{i:03d}" for i in range(1, workers + 1) if not (state.workers_path / f"worker-{i:03d}").is_dir()
    ]
    if missing:
        raise GridSpawnError(
            f"Manifest expects {workers} workers but missing worker director{'y' if len(missing) == 1 else 'ies'}: "
            f"{', '.join(missing)}.",
            cause="worker handoff directories are incomplete",
            fix_command=f"gaijinn run-grid --workers {workers} --force",
        )
    if not shutil.which(CODEX_BINARY):
        raise GridSpawnError(
            f"`{CODEX_BINARY}` not found on PATH",
            cause="Codex CLI is required for grid execution",
            fix_command="install `codex` and ensure it's on PATH",
        )
    return manifest


def grid_spawn_cmd(
    workers: int = typer.Option(
        ...,
        "--workers",
        "-w",
        min=1,
        help="Number of workers to spawn (must match run-grid count).",
    ),
    model: str = typer.Option(
        DEFAULT_GRID_MODEL,
        "--model",
        "-m",
        help="Codex model to use for all agents.",
    ),
    timeout: int = typer.Option(
        3600,
        "--timeout",
        min=1,
        help="Seconds to wait for each worker before killing it.",
    ),
) -> None:
    """Spawn Codex agents for each worker cell and run to completion.

    This is an ATOMIC sprint — once started, it cannot be cancelled.
    All agents use the SAME model for consistent manifest interpretation.
    """
    try:
        state = _require_project_state()
        _ensure_grid_spawn_prerequisites(state, workers)
        manifest_path = state.workers_path / "manifest.json"
        project_root = getattr(state, "project_root", Path.cwd())
        blueprint = load_blueprint_optional(project_root)

        layout_mode, cols, rows = _grid_mode(workers)
        typer.echo(f"Grid layout: {layout_mode} ({cols}×{rows})")
        typer.echo(f"Executor: codex")
        typer.echo(f"Model: {model}")
        typer.echo(f"Spawning {workers} agent{'s' if workers > 1 else ''} — atomic sprint, no cancel.")
        typer.echo("")

        processes: list[dict[str, Any]] = []
        for i in range(1, workers + 1):
            worker_name = f"worker-{i:03d}"
            worker_dir = state.workers_path / worker_name

            giv = _read_worker_giv(worker_dir)
            metadata = _read_worker_metadata(worker_dir)
            work_unit_text = _read_worker_work_unit(worker_dir)
            task_prompt = _build_task_prompt(
                worker_name,
                work_unit_text,
                giv,
                metadata,
                blueprint=blueprint,
                project_root=project_root,
            )

            from ..state import transition_worker_state
            transition_worker_state(manifest_path, worker_name, "executing")

            typer.echo(f"  ▶  Spawning {worker_name}...")
            proc = _spawn_worker(worker_name, worker_dir, task_prompt, model)

            processes.append(
                {
                    "name": worker_name,
                    "dir": worker_dir,
                    "proc": proc,
                    "started": time.time(),
                }
            )

        if not processes:
            raise SprintError(
                "No workers spawned.",
                cause="worker directories were missing",
                fix_command="gaijinn run-grid --workers 2",
            )

        typer.echo("")
        typer.echo(f"All {len(processes)} agent{'s' if len(processes) > 1 else ''} spawned.")
        typer.echo("Waiting for completion (atomic sprint — no cancel)...")
        typer.echo("")

        completed = 0
        failed = 0
        for entry in processes:
            proc = entry["proc"]
            timed_out = False
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.kill()
                proc.wait()
            elapsed = time.time() - entry["started"]

            if timed_out:
                typer.echo(f"  ✘  {entry['name']}: TIMED OUT after {timeout}s")
                failed += 1
            elif proc.returncode == 0:
                typer.echo(f"  ✔  {entry['name']}: completed in {elapsed:.1f}s")
                completed += 1
            else:
                typer.echo(f"  ✘  {entry['name']}: FAILED (exit {proc.returncode}) in {elapsed:.1f}s")
                failed += 1

            try:
                new_status = "timed_out" if timed_out else "completed" if proc.returncode == 0 else "failed"
                transition_worker_state(manifest_path, entry["name"], new_status)

                with manifest_path.open("r", encoding="utf-8") as mf:
                    current = json.load(mf)
                for detail in current.get("worker_details", []):
                    if detail.get("worker_id") == entry["name"]:
                        detail["elapsed_seconds"] = round(elapsed, 1)
                        break
                current["sprint"] = {
                    "atomic": True,
                    "cancel_supported": False,
                    "executor": "codex",
                    "model": model,
                    "completed": completed + failed,
                    "failed": failed,
                    "timeout_seconds": timeout,
                }
                _write_manifest_atomic(manifest_path, current)
            except Exception as exc:
                typer.echo(f"Warning: failed to update worker manifest at {manifest_path}: {exc}")

        typer.echo("")
        typer.echo(f"Sprint complete: {completed} passed, {failed} failed, {len(processes)} total")

        handoff_count = 0
        for entry in processes:
            log_path = entry["dir"] / OUTPUT_LOG_FILENAME
            if not log_path.exists():
                continue
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            published = publish_handoff_tickets_from_log(
                entry["name"],
                log_text,
                blueprint,
                project_root=project_root,
            )
            handoff_count += len(published)
        if handoff_count:
            typer.echo(f"Handoff bus: {handoff_count} transaction(s) published to council")

        if failed > 0:
            raise SprintError(
                f"{failed} worker(s) failed during the atomic sprint",
                cause="one or more Grok Build subprocesses exited non-zero",
            )

    except GaijinnError as exc:
        raise typer.BadParameter(render_error(exc)) from exc
