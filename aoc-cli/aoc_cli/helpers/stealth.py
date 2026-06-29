"""Customer-facing stealth layer — hide proprietary math from operators."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any


def operator_mode() -> bool:
    """Internal dev mode: full gravity/curvature artifacts and terminology."""
    return os.environ.get("GAIJINN_OPERATOR", "").strip().lower() in {"1", "true", "yes", "on"}


def stealth_mode() -> bool:
    """Default product mode: customer-safe surfaces only."""
    return not operator_mode()


def stealth_coupling_label() -> str:
    return "coupling review" if stealth_mode() else "shadow bridge"


def sanitize_blocked_reason(reason: str) -> str:
    """Rewrite internal preflight blockers for customer-visible output."""
    if not stealth_mode():
        return reason
    text = reason
    shadow_replacements = (
        (r"shadow bridge\(s\)", "coupling review(s)"),
        (r"shadow bridges", "coupling reviews"),
        (r"shadow bridge", "coupling review"),
    )
    for pattern, new in shadow_replacements:
        text = re.sub(pattern, new, text, flags=re.IGNORECASE)
    replacements = (
        ("automatic rejection", "integrity floor"),
        ("rejected node", "flagged file"),
        ("rejected nodes", "flagged files"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def sanitize_blocked_reasons(reasons: list[str]) -> list[str]:
    return [sanitize_blocked_reason(item) for item in reasons]


def dark_bridge_internal_log(source: str, target: str) -> str:
    """Operator-facing serialization event when a Dark Bridge forces co-location."""
    return f"DARK BRIDGE SEVERITY CRITICAL: Forced serialization of Node {source} and Node {target}."


def dark_bridge_user_log() -> str:
    """Customer-facing pipeline stabilization message."""
    return "Optimizing pipeline: Consolidating local coupling reviews for execution stabilization."


def dark_bridge_blueprint_assumption(serialization_count: int) -> str:
    if serialization_count <= 0:
        return ""
    if stealth_mode():
        return dark_bridge_user_log()
    return f"{serialization_count} Dark Bridge edge(s) forced atomic work-unit binding."


def customer_preflight_from_metrics(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Map internal metrics manifest fields to customer-safe preflight summary."""
    gravity_meta = metrics.get("gravity_meta", {})
    curvature_meta = metrics.get("curvature_meta", {})
    if not isinstance(gravity_meta, Mapping):
        gravity_meta = {}
    if not isinstance(curvature_meta, Mapping):
        curvature_meta = {}

    rejected = sorted(str(item) for item in gravity_meta.get("rejected_nodes", []))
    coupling_count = int(curvature_meta.get("shadow_bridge_count", 0) or 0)
    automatic_rejection = bool(gravity_meta.get("automatic_rejection", False))

    status = "review" if automatic_rejection or rejected or coupling_count > 0 else "ready"

    nodes = gravity_meta.get("nodes", {})
    node_count = len(nodes) if isinstance(nodes, Mapping) else 0

    return {
        "preflight_status": status,
        "integrity_floor_tripped": automatic_rejection,
        "preflight_flag_count": len(rejected),
        "preflight_flags": rejected,
        "coupling_review_count": coupling_count,
        "scope_nodes": node_count,
    }


def customer_analysis_summary(
    metrics: Mapping[str, Any],
    *,
    graph: str,
    artifact: str,
    integrity_score: int,
) -> dict[str, Any]:
    """JSON summary for `gaijinn analyze --json` in stealth mode."""
    preflight = customer_preflight_from_metrics(metrics)
    return {
        "schema_version": 1,
        "graph": graph,
        "artifact": artifact,
        "integrity_score": integrity_score,
        **preflight,
    }


def sanitize_analyze_api_response(
    *,
    status: str,
    automatic_rejection: bool,
    shadow_bridge_count: int,
    rejected_nodes: list[str] | None = None,
    integrity_score: int | None = None,
) -> dict[str, Any]:
    """Customer-safe POST /api/v1/analyze response."""
    payload: dict[str, Any] = {
        "status": status,
        "preflight_status": "review" if status in {"TRIPPED", "DEGRADED"} else "ready",
        "integrity_floor_tripped": automatic_rejection,
        "coupling_review_count": shadow_bridge_count,
    }
    if rejected_nodes is not None:
        payload["preflight_flags"] = rejected_nodes
        payload["preflight_flag_count"] = len(rejected_nodes)
    if integrity_score is not None:
        payload["integrity_score"] = integrity_score
    return payload
