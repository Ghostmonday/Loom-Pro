"""Upstream CI merge gate — workspace isolation + transaction bus synchronization."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aoc_cli.helpers.constants import WORKERS_DIR
from aoc_cli.helpers.handoff import load_handoff_queue
from aoc_cli.helpers.merge import (
    COLLECTED_PATH,
    INTEGRATION_BRANCH,
    VALIDATED_PATH,
    _load_merge_artifact,
    changed_files,
    detect_trespasses,
    load_blueprint_optional,
    load_worker_giv,
    merge_pipeline_status,
    resolve_base_ref,
)

VICTORY_LAP_FALLBACK = Path("/tmp/gaijinn-victory-lap-gateway")


class PreflightResolutionError(FileNotFoundError):
    """Raised when no project root can be resolved for a preflight session."""


@dataclass(frozen=True)
class PreflightResult:
    allow_merge: bool
    session_id: str
    worker_id: str
    target_branch: str
    status_code: str
    trespass_violations: list[str]
    pending_tickets_count: int
    metrics: dict[str, Any]
    project_path: str
    rejection_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allow_merge": self.allow_merge,
            "session_id": self.session_id,
            "worker_id": self.worker_id,
            "target_branch": self.target_branch,
            "status_code": self.status_code,
            "trespass_violations": self.trespass_violations,
            "pending_tickets_count": self.pending_tickets_count,
            "metrics": self.metrics,
            "project_path": self.project_path,
            "rejection_reasons": self.rejection_reasons,
        }


def resolve_preflight_project_root(
    session_id: str,
    *,
    project_path: str | None = None,
    session_roots: dict[str, Path] | None = None,
) -> Path:
    """Resolve the project root for a preflight check."""
    if project_path:
        resolved = Path(project_path).expanduser().resolve()
        if resolved.is_dir():
            return resolved
        raise PreflightResolutionError(f"project_path does not exist: {resolved}")

    if session_roots and session_id in session_roots:
        return session_roots[session_id].resolve()

    override = os.environ.get("GAIJINN_PROJECT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    if VICTORY_LAP_FALLBACK.is_dir():
        return VICTORY_LAP_FALLBACK.resolve()

    raise PreflightResolutionError(
        f"unable to resolve project root for session {session_id!r}; "
        "provide project_path or set GAIJINN_PROJECT_ROOT",
    )


def verify_workspace_isolation_gate(project_root: Path, worker_id: str) -> list[str]:
    """Evaluate path allowlist / scope isolation for one worker."""
    validated = _load_merge_artifact(project_root, VALIDATED_PATH) or {}
    worker_record = validated.get(worker_id)
    if isinstance(worker_record, dict):
        gates = worker_record.get("gates", {})
        if isinstance(gates, dict):
            violations: list[str] = []
            path_gate = gates.get("path_allowlist", {})
            if isinstance(path_gate, dict):
                violations.extend(str(path) for path in path_gate.get("trespasses", []) if path)
            scope_gate = gates.get("scope_isolation", {})
            if isinstance(scope_gate, dict):
                violations.extend(str(path) for path in scope_gate.get("violations", []) if path)
            return sorted(set(violations))

    workers_path = project_root / WORKERS_DIR
    worker_dir = workers_path / worker_id
    if not worker_dir.is_dir():
        return []

    collected = _load_merge_artifact(project_root, COLLECTED_PATH) or {}
    base_ref = str(collected.get("base_ref") or resolve_base_ref(project_root, "main"))
    giv = load_worker_giv(worker_dir)
    return detect_trespasses(changed_files(worker_dir, base_ref), giv)


def _pending_ticket_count(project_root: Path, worker_id: str) -> tuple[int, bool]:
    queue = load_handoff_queue(project_root)
    pending = queue.get("pending_tickets", [])
    pending_count = len(pending) if isinstance(pending, list) else 0
    bus_synced = bool(queue.get("transaction_bus_synchronized", True))

    validated = _load_merge_artifact(project_root, VALIDATED_PATH) or {}
    worker_record = validated.get(worker_id)
    if isinstance(worker_record, dict):
        integrity = worker_record.get("handoff_integrity", {})
        if isinstance(integrity, dict):
            if "transaction_bus_synchronized" in integrity:
                bus_synced = bus_synced and bool(integrity["transaction_bus_synchronized"])
            worker_pending = integrity.get("pending_tickets", [])
            if isinstance(worker_pending, list) and worker_pending:
                pending_count = max(pending_count, len(worker_pending))

    return pending_count, bus_synced


def run_preflight_check(
    *,
    session_id: str,
    worker_id: str,
    target_branch: str = INTEGRATION_BRANCH,
    project_path: str | None = None,
    session_roots: dict[str, Path] | None = None,
) -> PreflightResult:
    """Run the upstream merge gate against merge-pipeline artifacts."""
    project_root = resolve_preflight_project_root(
        session_id,
        project_path=project_path,
        session_roots=session_roots,
    )
    worker_id = worker_id.strip()
    if not worker_id:
        raise ValueError("worker_id is required")

    trespass_violations = verify_workspace_isolation_gate(project_root, worker_id)
    pending_count, bus_synced = _pending_ticket_count(project_root, worker_id)

    rejection_reasons: list[str] = []
    if trespass_violations:
        rejection_reasons.append("workspace_isolation_violation")
    if not bus_synced:
        rejection_reasons.append("transaction_bus_not_synchronized")
    if pending_count > 0:
        rejection_reasons.append("pending_handoff_tickets")

    validated = _load_merge_artifact(project_root, VALIDATED_PATH) or {}
    worker_record = validated.get(worker_id)
    worker_passed: bool | None = None
    if isinstance(worker_record, dict):
        worker_passed = bool(worker_record.get("passed", False))
        if worker_passed is False:
            rejection_reasons.append("worker_validation_failed")

    violations_detected = bool(trespass_violations)
    unresolved_transactions = not bus_synced or pending_count > 0
    validation_blocked = worker_passed is False
    allow_merge = not violations_detected and not unresolved_transactions and not validation_blocked

    blueprint = load_blueprint_optional(project_root)
    pipeline = merge_pipeline_status(project_root)

    return PreflightResult(
        allow_merge=allow_merge,
        session_id=session_id,
        worker_id=worker_id,
        target_branch=target_branch,
        status_code="PREFLIGHT_CLEARED" if allow_merge else "PREFLIGHT_REJECTED",
        trespass_violations=trespass_violations,
        pending_tickets_count=pending_count,
        metrics={
            "bus_synchronized_state": bus_synced,
            "total_violations_logged": len(trespass_violations),
            "worker_validation_passed": worker_passed,
            "blueprint_loaded": blueprint is not None,
            "blueprint_work_units": len(blueprint.work_units) if blueprint else 0,
            "merge_pipeline_phase": pipeline.get("phase"),
            "structural_score": pipeline.get("structural_score"),
        },
        project_path=str(project_root),
        rejection_reasons=rejection_reasons,
    )


def load_validated_worker_record(project_root: Path, worker_id: str) -> dict[str, Any] | None:
    """Load one worker record from validated.json (test helper / diagnostics)."""
    path = project_root / VALIDATED_PATH
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    record = payload.get(worker_id)
    return record if isinstance(record, dict) else None
