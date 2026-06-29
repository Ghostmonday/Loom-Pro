"""Architectural Complexity Index (ACI) — pricing inputs from Gaijinn artifacts.

Customer-facing output uses integrity_score and tier only.
Internal metrics (shadow bridges, kappa) feed the index but are not exposed via API.
"""

from __future__ import annotations

import json
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_METRICS_PATH = Path(".gaijinn/metrics_manifest.json")
DEFAULT_BLUEPRINT_PATH = Path(".gaijinn/blueprint.json")

TIER_NAMES = ("starter", "team", "professional", "enterprise")


@dataclass(frozen=True)
class ComplexitySnapshot:
    """Deterministic pricing inputs derived from analyze + plan artifacts."""

    node_count: int
    isolation_signals: int  # internal: shadow bridge count
    flagged_files: int  # internal: rejected node count
    assignment_count: int  # internal: work unit count
    high_risk_assignments: int
    mean_severity: float  # internal: mean |kappa| for negative edges
    worker_count: int

    @property
    def integrity_score(self) -> int:
        """Customer-visible complexity index (rounded integer)."""
        node_count = float(self.node_count)
        if not math.isfinite(node_count) or node_count < 0:
            raise ValueError("node_count must be finite and non-negative")

        raw = (
            10.0 * math.log1p(node_count)
            + 25.0 * self.isolation_signals
            + 15.0 * self.assignment_count
            + 20.0 * self.high_risk_assignments
            + 50.0 * self.mean_severity
            + 5.0 * self.flagged_files
            + 8.0 * self.worker_count
        )
        return max(0, int(round(raw)))


def compute_complexity_index(snapshot: ComplexitySnapshot) -> int:
    """Return the customer-visible Architectural Complexity Index (ACI)."""
    return snapshot.integrity_score


def tier_for_score(score: int, thresholds: tuple[int, int, int] = (200, 800, 2500)) -> str:
    if score < thresholds[0]:
        return TIER_NAMES[0]
    if score < thresholds[1]:
        return TIER_NAMES[1]
    if score < thresholds[2]:
        return TIER_NAMES[2]
    return TIER_NAMES[3]


def build_snapshot(
    *,
    metrics_path: str | Path = DEFAULT_METRICS_PATH,
    blueprint_path: str | Path = DEFAULT_BLUEPRINT_PATH,
    worker_count: int = 1,
) -> ComplexitySnapshot:
    """Build a snapshot from on-disk Gaijinn artifacts."""
    metrics = _load_metrics(metrics_path)
    blueprint = _load_blueprint(blueprint_path)
    return ComplexitySnapshot(
        node_count=metrics["node_count"],
        isolation_signals=metrics["isolation_signals"],
        flagged_files=metrics["flagged_files"],
        assignment_count=blueprint["assignment_count"],
        high_risk_assignments=blueprint["high_risk_assignments"],
        mean_severity=metrics["mean_severity"],
        worker_count=max(1, worker_count),
    )


def build_snapshot_from_payload(
    payload: Mapping[str, Any],
    *,
    worker_count: int = 1,
) -> ComplexitySnapshot:
    """Build a snapshot from an API/analyze JSON payload."""
    gravity_meta = payload.get("gravity_meta", {}) if isinstance(payload.get("gravity_meta"), Mapping) else {}
    curvature_meta = payload.get("curvature_meta", {}) if isinstance(payload.get("curvature_meta"), Mapping) else {}

    gravity_nodes = gravity_meta.get("nodes", {})
    if isinstance(gravity_nodes, Mapping) and gravity_nodes:
        node_count = len(gravity_nodes)
    else:
        nodes = payload.get("nodes", [])
        node_count = len(nodes) if isinstance(nodes, list) else 0

    rejected = gravity_meta.get("rejected_nodes", [])
    flagged_files = len(rejected) if isinstance(rejected, list) else 0
    isolation_signals = int(curvature_meta.get("shadow_bridge_count", 0) or 0)

    mean_severity = _mean_negative_kappa(curvature_meta.get("edges", {}))

    blueprint = payload.get("blueprint", {})
    if not isinstance(blueprint, Mapping):
        blueprint = {}
    units = blueprint.get("work_units", [])
    assignment_count = len(units) if isinstance(units, list) else int(payload.get("assignment_count", 1) or 1)
    high_risk = 0
    if isinstance(units, list):
        for unit in units:
            if isinstance(unit, Mapping) and str(unit.get("estimated_risk", "low")).lower() == "high":
                high_risk += 1

    return ComplexitySnapshot(
        node_count=node_count,
        isolation_signals=isolation_signals,
        flagged_files=flagged_files,
        assignment_count=max(1, assignment_count),
        high_risk_assignments=high_risk,
        mean_severity=mean_severity,
        worker_count=max(1, worker_count),
    )


def customer_receipt(snapshot: ComplexitySnapshot, *, worker_count: int | None = None) -> dict[str, Any]:
    """Customer-safe deploy receipt (no internal terminology)."""
    workers = worker_count if worker_count is not None else snapshot.worker_count
    score = snapshot.integrity_score
    return {
        "integrity_score": score,
        "tier": tier_for_score(score),
        "agent_slots": workers,
        "assignments": snapshot.assignment_count,
        "preflight_status": "ready" if snapshot.flagged_files == 0 and snapshot.isolation_signals == 0 else "review",
    }


def _load_metrics(path: str | Path) -> dict[str, Any]:
    metrics_path = Path(path)
    if not metrics_path.exists():
        return {"node_count": 0, "isolation_signals": 0, "flagged_files": 0, "mean_severity": 0.0}

    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    gravity_meta = payload.get("gravity_meta", {})
    curvature_meta = payload.get("curvature_meta", {})

    nodes = gravity_meta.get("nodes", {})
    node_count = len(nodes) if isinstance(nodes, Mapping) else 0
    rejected = gravity_meta.get("rejected_nodes", [])
    flagged_files = len(rejected) if isinstance(rejected, list) else 0
    isolation_signals = int(curvature_meta.get("shadow_bridge_count", 0) or 0)
    mean_severity = _mean_negative_kappa(curvature_meta.get("edges", {}))

    return {
        "node_count": node_count,
        "isolation_signals": isolation_signals,
        "flagged_files": flagged_files,
        "mean_severity": mean_severity,
    }


def _load_blueprint(path: str | Path) -> dict[str, int]:
    blueprint_path = Path(path)
    if not blueprint_path.exists():
        return {"assignment_count": 1, "high_risk_assignments": 0}

    payload = json.loads(blueprint_path.read_text(encoding="utf-8"))
    units = payload.get("work_units", [])
    if not isinstance(units, list):
        return {"assignment_count": 1, "high_risk_assignments": 0}

    high_risk = sum(
        1 for unit in units if isinstance(unit, Mapping) and str(unit.get("estimated_risk", "low")).lower() == "high"
    )
    return {"assignment_count": max(1, len(units)), "high_risk_assignments": high_risk}


def _mean_negative_kappa(edges: Any) -> float:
    if not isinstance(edges, Mapping):
        return 0.0
    values: list[float] = []
    for edge in edges.values():
        if not isinstance(edge, Mapping):
            continue
        kappa = edge.get("kappa", edge.get("curvature", 0.0))
        try:
            k = float(kappa)
        except (TypeError, ValueError):
            continue
        if k < 0.0:
            values.append(abs(k))
    if not values:
        return 0.0
    return sum(values) / len(values)


def max_active_workers() -> int:
    return int(os.environ.get("GAIJINN_MAX_ACTIVE_WORKERS", "32"))


def max_concurrent_sprints() -> int:
    return int(os.environ.get("GAIJINN_MAX_CONCURRENT_SPRINTS", "8"))


def max_spawn_timeout() -> int:
    return int(os.environ.get("GAIJINN_MAX_SPAWN_TIMEOUT", "7200"))


def max_workers_per_session() -> int:
    return int(os.environ.get("GAIJINN_MAX_WORKERS_PER_SESSION", "16"))
