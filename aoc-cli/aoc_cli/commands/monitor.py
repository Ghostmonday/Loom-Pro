"""monitor command implementation."""

from __future__ import annotations

import time
from pathlib import Path

import typer

from ..helpers import (
    _echo_status,
    _file_signature,
    _load_validate_system_state,
    _run_validation,
)
from ..helpers.constants import OUTPUT_LOG_FILENAME, WORKERS_DIR
from ..helpers.scan import shadow_bridge_summary


def _worker_output_status() -> str:
    worker_dirs = sorted(path for path in WORKERS_DIR.glob("worker-*") if path.is_dir())
    if not worker_dirs:
        return "no worker directories"
    logs = [path / OUTPUT_LOG_FILENAME for path in worker_dirs]
    present = sum(log.exists() for log in logs)
    return f"{present}/{len(logs)} worker output logs present"


def monitor_cmd(manifest: Path, poll_interval: float) -> None:
    """Watch metrics manifest writes and validate supervisor state."""
    validate_system_state = _load_validate_system_state()
    last_signature: tuple[int, int, int] | None = None

    _echo_status(f"monitoring {manifest}")
    _echo_status(f"terminal bridge: {_worker_output_status()}")
    try:
        while True:
            signature = _file_signature(manifest)
            if signature is not None and signature != last_signature:
                last_signature = signature
                _run_validation(validate_system_state)
                summary = shadow_bridge_summary(manifest)
                _echo_status(
                    "metrics update: "
                    f"shadow_bridges={summary['shadow_bridge_count']} "
                    f"rejected={summary['rejected_node_count']}"
                )
                _echo_status(f"terminal bridge: {_worker_output_status()}")
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        last_signature = None
        raise typer.Exit(code=0)
    finally:
        last_signature = None
