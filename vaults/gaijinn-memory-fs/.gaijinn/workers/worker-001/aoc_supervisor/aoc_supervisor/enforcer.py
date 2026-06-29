"""Structural safety validation for Gaijinn supervisor artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StructuralGravityViolation(RuntimeError):
    """Raised when generated telemetry violates structural safety constraints."""


def validate_system_state(manifest_path: str | Path = ".gaijinn/metrics_manifest.json") -> bool:
    """Validate the generated metrics manifest.

    The enforcer treats a missing manifest as an unverified state, malformed JSON
    as a structural crash, and any explicit tripped/unsafe/rejected marker as a
    blocked system state.
    """
    path = Path(manifest_path)
    if not path.exists():
        return False

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StructuralGravityViolation(f"invalid metrics manifest: {path}") from exc

    if not isinstance(payload, dict):
        raise StructuralGravityViolation("metrics manifest must be a JSON object")

    return not _contains_trip_marker(payload)


def shadow_bridge_summary(manifest_path: str | Path = ".gaijinn/metrics_manifest.json") -> dict[str, Any]:
    """Return shadow-bridge and rejection counts from a metrics manifest."""
    path = Path(manifest_path)
    if not path.exists():
        return {
            "exists": False,
            "shadow_bridge_count": 0,
            "rejected_node_count": 0,
            "rejected_nodes": [],
            "automatic_rejection": False,
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StructuralGravityViolation(f"invalid metrics manifest: {path}") from exc

    if not isinstance(payload, dict):
        raise StructuralGravityViolation("metrics manifest must be a JSON object")

    gravity_meta = payload.get("gravity_meta", {})
    curvature_meta = payload.get("curvature_meta", {})
    rejected = sorted(str(item) for item in gravity_meta.get("rejected_nodes", []))
    return {
        "exists": True,
        "shadow_bridge_count": int(curvature_meta.get("shadow_bridge_count", 0) or 0),
        "rejected_node_count": len(rejected),
        "rejected_nodes": rejected,
        "automatic_rejection": bool(gravity_meta.get("automatic_rejection", False)),
    }


def validate_grid_readiness(
    manifest_path: str | Path = ".gaijinn/metrics_manifest.json",
    workers_path: str | Path = ".gaijinn/workers",
) -> dict[str, Any]:
    """Check whether the project is ready for an atomic Grok Build grid sprint."""
    metrics = shadow_bridge_summary(manifest_path)
    workers_dir = Path(workers_path)
    manifest_file = workers_dir / "manifest.json"
    worker_dirs = sorted(path for path in workers_dir.glob("worker-*") if path.is_dir())
    output_logs = [path / "output.log" for path in worker_dirs]
    blocked_reasons: list[str] = []
    if not metrics["exists"]:
        blocked_reasons.append("metrics manifest missing")
    if metrics["automatic_rejection"]:
        blocked_reasons.append("automatic rejection tripped")
    if metrics["rejected_node_count"] > 0:
        blocked_reasons.append(f"{metrics['rejected_node_count']} rejected node(s)")
    if metrics["shadow_bridge_count"] > 0:
        blocked_reasons.append(f"{metrics['shadow_bridge_count']} shadow bridge(s)")
    if not manifest_file.exists():
        blocked_reasons.append("worker manifest missing")
    if not worker_dirs:
        blocked_reasons.append("no worker directories")

    from aoc_cli.helpers.stealth import sanitize_blocked_reasons

    return {
        "ready": not blocked_reasons,
        "blocked_reasons": sanitize_blocked_reasons(blocked_reasons),
        "worker_count": len(worker_dirs),
        "manifest_exists": manifest_file.exists(),
        "output_logs_present": sum(log.exists() for log in output_logs),
        "atomic_sprint": True,
        "cancel_supported": False,
        **metrics,
    }


def _contains_trip_marker(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key in {"tripped", "unsafe", "rejected", "automatic_rejection"} and bool(item):
                return True
            if normalized_key in {"status", "state"} and str(item).upper() in {"TRIPPED", "CRASHED", "UNSAFE"}:
                return True
            if _contains_trip_marker(item):
                return True
    elif isinstance(value, list):
        return any(_contains_trip_marker(item) for item in value)
    return False
