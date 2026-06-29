"""Status, diagnostics, and rendering helpers for Gaijinn CLI commands."""

from __future__ import annotations

import importlib
import math
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import typer

from ..blueprint import Blueprint
from ..errors import GaijinnError, render_error
from ..giv import GIV
from ..gravity import GRAVITY_HARD_FLOOR
from ..state import StateError, ensure_state, write_state
from .constants import (
    AGENT_FILE_PATHS,
    BLUEPRINT_JSON_PATH,
    BLUEPRINT_TEMPLATE_PATH,
    DEFAULT_GRAPH_PATH,
    DEFAULT_METRICS_PATH,
    GAIJINN_AGENT_BLOCK_BEGIN,
    GAIJINN_AGENT_BLOCK_END,
    GAIJINN_DIR,
    GIV_PATH,
    INTENT_PATH,
    LICENSE_PATH,
    PROJECT_PATH,
    WORKERS_DIR,
)
from .git import _git_clean
from .io import _load_json_artifact, _optional_project_state, _summary_list
from .workers import _worker_count

# ── Status helpers ─────────────────────────────────────────────────────


def _stealth_enabled() -> bool:
    from .stealth import stealth_mode

    # Stealth is the default product mode. Set GAIJINN_OPERATOR=1 for internal math tables.
    if os.environ.get("GAIJINN_STEALTH", "").strip().lower() in {"0", "false", "no", "off"}:
        return False
    if os.environ.get("GAIJINN_STEALTH", "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return stealth_mode()


def _integrity_score(
    metrics: Mapping[str, Any],
    *,
    worker_count: int = 1,
    assignment_count: int = 1,
    high_risk_assignments: int = 0,
) -> int:
    """Customer-visible complexity index derived from internal preflight metrics."""
    node_count = int(metrics.get("node_count", 0) or 0)
    isolation_signals = int(metrics.get("shadow_bridge_count", 0) or 0)
    flagged_files = int(metrics.get("rejected_nodes", 0) or 0)
    mean_severity = float(metrics.get("mean_severity", 0.0) or 0.0)
    raw = (
        10.0 * math.log1p(node_count)
        + 25.0 * isolation_signals
        + 15.0 * assignment_count
        + 20.0 * high_risk_assignments
        + 50.0 * mean_severity
        + 5.0 * flagged_files
        + 8.0 * max(1, worker_count)
    )
    return max(0, int(round(raw)))


def _preflight_status(metrics: Mapping[str, Any]) -> str:
    if int(metrics.get("rejected_nodes", 0) or 0) > 0 or int(metrics.get("shadow_bridge_count", 0) or 0) > 0:
        return "review"
    return "ready"


def _status_metrics_extended(metrics_path: Path) -> dict[str, Any]:
    base = _status_metrics(metrics_path)
    if not metrics_path.exists():
        return {**base, "node_count": 0, "mean_severity": 0.0}
    try:
        metrics = _load_json_artifact(metrics_path, "metrics JSON", "gaijinn analyze")
    except GaijinnError:
        return {**base, "node_count": 0, "mean_severity": 0.0}
    gravity_meta = metrics.get("gravity_meta", {})
    curvature_meta = metrics.get("curvature_meta", {})
    nodes = gravity_meta.get("nodes", {})
    node_count = len(nodes) if isinstance(nodes, Mapping) else 0
    edges = curvature_meta.get("edges", {})
    mean_severity = 0.0
    if isinstance(edges, Mapping):
        negative_values: list[float] = []
        for edge in edges.values():
            if not isinstance(edge, Mapping):
                continue
            kappa = edge.get("kappa", edge.get("curvature", 0.0))
            try:
                value = float(kappa)
            except (TypeError, ValueError):
                continue
            if value < 0.0:
                negative_values.append(abs(value))
        if negative_values:
            mean_severity = sum(negative_values) / len(negative_values)
    return {**base, "node_count": node_count, "mean_severity": mean_severity}


def _manifest_assignment_stats() -> tuple[int, int]:
    if not BLUEPRINT_JSON_PATH.exists():
        return (1, 0)
    try:
        payload = _load_json_artifact(BLUEPRINT_JSON_PATH, "build manifest JSON", "gaijinn plan --workers 2")
    except GaijinnError:
        return (1, 0)
    units = payload.get("work_units", [])
    if not isinstance(units, list):
        return (1, 0)
    high_risk = sum(
        1 for unit in units if isinstance(unit, Mapping) and str(unit.get("estimated_risk", "low")).lower() == "high"
    )
    return (max(1, len(units)), high_risk)


def _status_payload() -> dict[str, Any]:
    state_error = None
    project_state = None
    if PROJECT_PATH.exists():
        try:
            project_state = ensure_state(Path.cwd())
        except StateError as exc:
            state_error = render_error(exc)

    graph_path = project_state.graph_path if project_state else DEFAULT_GRAPH_PATH
    metrics_path = project_state.metrics_path if project_state else DEFAULT_METRICS_PATH
    intent_path = project_state.intent_path if project_state else INTENT_PATH
    workers_path = project_state.workers_path if project_state else WORKERS_DIR
    metrics = _status_metrics_extended(metrics_path)
    worker_manifest = _worker_manifest_status(workers_path)
    assignment_count, high_risk_assignments = _manifest_assignment_stats()
    worker_count = int(worker_manifest.get("count", 1) or 1)
    integrity_score = _integrity_score(
        metrics,
        worker_count=worker_count,
        assignment_count=assignment_count,
        high_risk_assignments=high_risk_assignments,
    )
    preflight_status = _preflight_status(metrics)
    artifacts = {
        "initialized": GAIJINN_DIR.exists() and PROJECT_PATH.exists() and state_error is None,
        "activation": _activation_status(project_state),
        "graph": graph_path.exists(),
        "metrics": metrics_path.exists(),
        "blueprint": BLUEPRINT_JSON_PATH.exists() and BLUEPRINT_TEMPLATE_PATH.exists(),
        "giv": GIV_PATH.exists(),
        "worker_grid": worker_manifest,
        "intent": intent_path.exists(),
    }
    missing_required = not all(
        bool(artifacts[key]) for key in ("initialized", "graph", "metrics", "blueprint", "giv", "intent")
    )
    degraded = (
        missing_required or bool(state_error) or metrics["rejected_nodes"] > 0 or metrics["shadow_bridge_count"] > 0
    )
    tripped = PROJECT_PATH.exists() and state_error is not None
    payload = {
        "schema_version": 1,
        "state": "tripped" if tripped else "degraded" if degraded else "ready",
        **artifacts,
        "shadow_bridge_count": metrics["shadow_bridge_count"],
        "rejected_nodes": metrics["rejected_node_ids"],
        "rejected_node_count": metrics["rejected_nodes"],
        "integrity_score": integrity_score,
        "preflight_status": preflight_status,
        "next_recommended_command": _next_command(artifacts),
    }
    if state_error:
        payload["project_error"] = state_error
    payload["merge_pipeline"] = _merge_pipeline_status_payload()
    if _stealth_enabled():
        payload = _stealth_status_payload(payload)
    return payload


def _merge_pipeline_status_payload() -> dict[str, Any]:
    from .merge import merge_pipeline_status

    return merge_pipeline_status(Path.cwd())


def _stealth_status_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a customer-safe status payload without internal terminology."""
    worker_grid = payload.get("worker_grid", {})
    stealth = {
        "schema_version": payload.get("schema_version", 1),
        "state": payload.get("state"),
        "initialized": payload.get("initialized"),
        "activation": payload.get("activation"),
        "graph": payload.get("graph"),
        "metrics": payload.get("metrics"),
        "manifest": payload.get("blueprint"),
        "scope_lock": payload.get("giv"),
        "worker_grid": worker_grid,
        "intent": payload.get("intent"),
        "integrity_score": payload.get("integrity_score"),
        "preflight_status": payload.get("preflight_status"),
        "preflight_flags": payload.get("rejected_nodes", []),
        "preflight_flag_count": payload.get("rejected_node_count", 0),
        "next_recommended_command": payload.get("next_recommended_command"),
    }
    if "project_error" in payload:
        stealth["project_error"] = payload["project_error"]
    if "terminal_bridge" in payload:
        stealth["terminal_bridge"] = payload["terminal_bridge"]
    if "merge_pipeline" in payload:
        stealth["merge_pipeline"] = payload["merge_pipeline"]
    return stealth


def _status_metrics(metrics_path: Path) -> dict[str, Any]:
    if not metrics_path.exists():
        return {"shadow_bridge_count": 0, "rejected_nodes": 0, "rejected_node_ids": []}
    try:
        metrics = _load_json_artifact(metrics_path, "metrics JSON", "gaijinn analyze")
    except GaijinnError:
        return {"shadow_bridge_count": 0, "rejected_nodes": 0, "rejected_node_ids": []}
    gravity_meta = metrics.get("gravity_meta", {})
    curvature_meta = metrics.get("curvature_meta", {})
    rejected = sorted(str(item) for item in gravity_meta.get("rejected_nodes", []))
    return {
        "shadow_bridge_count": int(curvature_meta.get("shadow_bridge_count", 0) or 0),
        "rejected_nodes": len(rejected),
        "rejected_node_ids": rejected,
    }


def _worker_manifest_status(workers_path: Path) -> dict[str, Any]:
    manifest_path = workers_path / "manifest.json"
    count = _worker_count(workers_path)
    if not manifest_path.exists():
        return {"exists": count > 0, "count": count, "mode": None}
    try:
        manifest = _load_json_artifact(manifest_path, "worker manifest", "gaijinn run-grid --workers 2")
    except GaijinnError:
        return {"exists": count > 0, "count": count, "mode": "invalid"}
    return {
        "exists": True,
        "count": int(manifest.get("worker_count", count) or count),
        "mode": manifest.get("mode"),
    }


def _activation_status(project_state: Any) -> str:
    if LICENSE_PATH.exists():
        return "active"
    if project_state is not None:
        return project_state.activation_status
    return "inactive"


def _next_command(artifacts: Mapping[str, Any]) -> str:
    if not artifacts["initialized"]:
        return 'gaijinn init "PROJECT PROMPT"'
    if not artifacts["giv"] or not artifacts["intent"]:
        return "gaijinn compile-prompt"
    if not artifacts["graph"]:
        return "gaijinn scan ."
    if not artifacts["metrics"]:
        return "gaijinn analyze"
    if not artifacts["blueprint"]:
        return "gaijinn plan --workers 2"
    worker_grid = artifacts["worker_grid"]
    if isinstance(worker_grid, Mapping) and not worker_grid.get("exists"):
        return "gaijinn run-grid --workers 2"
    return "gaijinn monitor"


def _render_status(payload: Mapping[str, Any]) -> None:
    typer.echo("Gaijinn status")
    for key in (
        "state",
        "initialized",
        "activation",
        "graph",
        "metrics",
        "manifest",
        "scope_lock",
    ):
        source_key = key
        if key == "manifest":
            source_key = "blueprint" if "blueprint" in payload else "manifest"
        elif key == "scope_lock":
            source_key = "giv" if "giv" in payload else "scope_lock"
        typer.echo(f"{key}: {payload[source_key]}")
    worker_grid = payload["worker_grid"]
    typer.echo(f"worker_grid: {worker_grid.get('count', 0)} ({worker_grid.get('mode') or 'none'})")
    typer.echo(f"workers: {worker_grid.get('count', 0)}")
    typer.echo(f"integrity_score: {payload.get('integrity_score', 0)}")
    typer.echo(f"preflight_status: {payload.get('preflight_status', 'review')}")
    preflight_flags = payload.get("preflight_flags", payload.get("rejected_nodes", []))
    typer.echo(f"preflight_flags: {_summary_list(preflight_flags)}")
    typer.echo(f"next_recommended_command: {payload['next_recommended_command']}")
    if "project_error" in payload:
        typer.echo(f"project_error: {payload['project_error']}")


# ── Analyze helpers ────────────────────────────────────────────────────


def _update_project_metrics_path(output: Path) -> None:
    state = _optional_project_state()
    if state is None:
        return

    relative_output = _relative_to_cwd(output)
    if relative_output is None or not _is_gaijinn_relative_path(relative_output):
        return
    if relative_output == state.metrics_path:
        return

    write_state(replace(state, metrics_path=relative_output))


def _relative_to_cwd(path: Path) -> Path | None:
    if not path.is_absolute():
        return path
    try:
        return path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        return None


def _is_gaijinn_relative_path(path: Path) -> bool:
    return not path.is_absolute() and bool(path.parts) and path.parts[0] == GAIJINN_DIR.name


def _normalize_graph_data(graph_data: dict[str, Any]) -> dict[str, Any]:
    if "nodes" in graph_data or "edges" in graph_data:
        return graph_data

    interaction_graph = graph_data.get("interaction_graph")
    if not isinstance(interaction_graph, list):
        return graph_data

    nodes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str]] = set()
    states: dict[str, list[str]] = {}

    for raw_node in interaction_graph:
        if not isinstance(raw_node, Mapping):
            continue

        intent = raw_node.get("agent_intent") or raw_node.get("intent") or raw_node.get("id")
        if intent is None:
            continue

        node_id = str(intent)
        prior_state = raw_node.get("valid_prior_state")
        resulting_state = raw_node.get("resulting_state")
        nodes[node_id] = {
            "id": node_id,
            "capability_level": _capability_score(raw_node.get("capability_level")),
            "side_effect_score": _side_effect_score(raw_node.get("side_effects")),
        }

        if prior_state is not None:
            states.setdefault(str(prior_state), []).append(node_id)
        if resulting_state is not None:
            states.setdefault(str(resulting_state), [])

    for raw_node in interaction_graph:
        if not isinstance(raw_node, Mapping):
            continue

        intent = raw_node.get("agent_intent") or raw_node.get("intent") or raw_node.get("id")
        resulting_state = raw_node.get("resulting_state")
        if intent is None or resulting_state is None:
            continue

        for target in states.get(str(resulting_state), []):
            if target != str(intent):
                edges.add((str(intent), target))

    return {"nodes": list(nodes.values()), "edges": sorted(edges)}


def _capability_score(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return _clamp(float(value))

    text = str(value).strip().upper()
    if text.startswith("LEVEL_"):
        try:
            return _clamp(int(text.removeprefix("LEVEL_")) / 5)
        except ValueError:
            return 0.0

    try:
        return _clamp(float(text))
    except ValueError:
        return 0.0


def _side_effect_score(value: Any) -> float:
    if isinstance(value, list):
        return _clamp(len(value) / 5)
    if value:
        return 0.2
    return 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _validate_graph_for_analysis(graph_data: Mapping[str, Any], source: Path) -> None:
    nodes = graph_data.get("nodes")
    if not isinstance(nodes, list):
        raise typer.BadParameter(f"graph JSON at {source} must contain a `nodes` array")
    if not nodes:
        raise typer.BadParameter(
            f"graph JSON at {source} contains no nodes; run `gaijinn scan .` on a non-empty project"
        )


def _analysis_summary(metrics: Mapping[str, Any], graph: Path, output: Path) -> dict[str, Any]:
    gravity_meta = metrics.get("gravity_meta", {})
    curvature_meta = metrics.get("curvature_meta", {})
    rejected_nodes = sorted(str(node) for node in gravity_meta.get("rejected_nodes", []))
    shadow_bridge_edges = sorted(
        str(edge)
        for edge, edge_meta in curvature_meta.get("edges", {}).items()
        if isinstance(edge_meta, Mapping) and edge_meta.get("is_shadow_bridge")
    )
    reflective_meta = metrics.get("reflective_meta", {})
    topo = reflective_meta.get("topological_inference", {}) if isinstance(reflective_meta, Mapping) else {}
    state_path = reflective_meta.get("state_path_chaining", {}) if isinstance(reflective_meta, Mapping) else {}
    boundary = reflective_meta.get("topological_boundary_scan", {}) if isinstance(reflective_meta, Mapping) else {}
    type_flow = reflective_meta.get("type_flow_analysis", {}) if isinstance(reflective_meta, Mapping) else {}
    symmetry = reflective_meta.get("curvature_measurement", {}) if isinstance(reflective_meta, Mapping) else {}
    return {
        "schema_version": 1,
        "graph": graph.as_posix(),
        "metrics": output.as_posix(),
        "node_count": len(gravity_meta.get("nodes", {})),
        "edge_count": len(curvature_meta.get("edges", {})),
        "automatic_rejection": bool(gravity_meta.get("automatic_rejection")),
        "rejection_count": len(rejected_nodes),
        "rejected_nodes": rejected_nodes,
        "shadow_bridge_count": int(curvature_meta.get("shadow_bridge_count", 0)),
        "shadow_bridges": shadow_bridge_edges,
        "layer2_intent_nodes": int(reflective_meta.get("intent_node_count", 0) or 0),
        "lifecycle_chain_count": len(state_path.get("lifecycle_chains", [])),
        "disconnected_gap_count": int(topo.get("gap_count", 0) or 0),
        "capability_ceiling_count": int(boundary.get("ceiling_count", 0) or 0),
        "type_flow_puncture_count": int(type_flow.get("puncture_count", 0) or 0),
        "symmetry_shadowbridge_count": int(symmetry.get("shadowbridge_count", 0) or 0),
        "inferred_path": metrics.get("inferred_path"),
    }


def _render_analysis(metrics: dict[str, Any], graph: Path, output: Path) -> None:
    if _stealth_enabled():
        _render_analysis_stealth(metrics, graph, output)
        return

    try:
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
    except ImportError:
        typer.echo(f"analyzed graph: {graph}")
        typer.echo(f"metrics artifact: {output}")
        return

    console = Console()
    gravity_meta = metrics.get("gravity_meta", {})
    curvature_meta = metrics.get("curvature_meta", {})

    gravity_table = Table(box=box.SQUARE, show_lines=True, expand=True)
    gravity_table.add_column("Node", style="bold white")
    gravity_table.add_column("Gravity", justify="right")
    gravity_table.add_column("In", justify="right")
    gravity_table.add_column("Out", justify="right")
    gravity_table.add_column("Verdict", justify="center")

    nodes = gravity_meta.get("nodes", {})
    for node, node_meta in sorted(nodes.items(), key=lambda item: item[1]["gravity"]):
        gravity = float(node_meta["gravity"])
        verdict = "[red]REJECT[/red]" if gravity < GRAVITY_HARD_FLOOR else "[green]PASS[/green]"
        gravity_table.add_row(
            str(node),
            f"{gravity:.4f}",
            f"{float(node_meta['in_degree']):.4f}",
            f"{float(node_meta['out_degree']):.4f}",
            verdict,
        )

    curvature_table = Table(box=box.SQUARE, show_lines=True, expand=True)
    curvature_table.add_column("Edge", style="bold white")
    curvature_table.add_column("Curvature", justify="right")
    curvature_table.add_column("W1", justify="right")
    curvature_table.add_column("Fragility", justify="center")

    edges = curvature_meta.get("edges", {})
    for edge, edge_meta in sorted(edges.items(), key=lambda item: item[0]):
        curvature = float(edge_meta["curvature"])
        fragility = "[red]SHADOW BRIDGE[/red]" if edge_meta.get("is_shadow_bridge") else "[green]stable[/green]"
        curvature_table.add_row(
            str(edge),
            f"{curvature:.4f}",
            f"{float(edge_meta['wasserstein_1']):.4f}",
            fragility,
        )

    reflective_meta = metrics.get("reflective_meta", {})
    lifecycle_count = 0
    gap_count = 0
    ceiling_count = 0
    type_flow_count = 0
    symmetry_shadow_count = 0
    if isinstance(reflective_meta, Mapping):
        topo = reflective_meta.get("topological_inference", {})
        state_path = reflective_meta.get("state_path_chaining", {})
        boundary = reflective_meta.get("topological_boundary_scan", {})
        type_flow = reflective_meta.get("type_flow_analysis", {})
        symmetry = reflective_meta.get("curvature_measurement", {})
        if isinstance(topo, Mapping):
            gap_count = int(topo.get("gap_count", 0) or 0)
        if isinstance(state_path, Mapping):
            lifecycle_count = len(state_path.get("lifecycle_chains", []))
        if isinstance(boundary, Mapping):
            ceiling_count = int(boundary.get("ceiling_count", 0) or 0)
        if isinstance(type_flow, Mapping):
            type_flow_count = int(type_flow.get("puncture_count", 0) or 0)
        if isinstance(symmetry, Mapping):
            symmetry_shadow_count = int(symmetry.get("shadowbridge_count", 0) or 0)

    summary = (
        f"graph: {graph}\n"
        f"artifact: {output}\n"
        f"hard floor: {GRAVITY_HARD_FLOOR:.2f}\n"
        f"automatic rejection: {gravity_meta.get('automatic_rejection', False)}\n"
        f"shadow bridges: {curvature_meta.get('shadow_bridge_count', 0)}\n"
        f"layer 2 intent nodes: {_reflective_intent_count(reflective_meta)}\n"
        f"lifecycle chains: {lifecycle_count}\n"
        f"disconnected gaps (DFS): {gap_count}\n"
        f"capability ceilings: {ceiling_count}\n"
        f"type-flow punctures: {type_flow_count}\n"
        f"symmetry shadowbridges: {symmetry_shadow_count}\n"
        f"inferred: {metrics.get('inferred_path', 'n/a')}"
    )
    console.print(Panel(summary, title="[bold]GAIJINN ANALYZE[/bold]", border_style="white", box=box.SQUARE))
    console.print(Panel(gravity_table, title="[bold]STRUCTURAL GRAVITY[/bold]", border_style="white", box=box.SQUARE))
    console.print(
        Panel(curvature_table, title="[bold]OLLIVIER-RICCI CURVATURE[/bold]", border_style="white", box=box.SQUARE)
    )
    if isinstance(reflective_meta, Mapping) and int(reflective_meta.get("intent_node_count", 0) or 0) > 0:
        console.print(
            Panel(
                _reflective_summary_text(reflective_meta),
                title="[bold]LAYER 2 REFLECTIVE (INFERRED)[/bold]",
                border_style="white",
                box=box.SQUARE,
            )
        )


def _reflective_intent_count(reflective_meta: Any) -> int:
    if not isinstance(reflective_meta, Mapping):
        return 0
    return int(reflective_meta.get("intent_node_count", 0) or 0)


def _reflective_summary_text(reflective_meta: Mapping[str, Any]) -> str:
    topo = reflective_meta.get("topological_inference", {})
    state_path = reflective_meta.get("state_path_chaining", {})
    boundary = reflective_meta.get("topological_boundary_scan", {})
    type_flow = reflective_meta.get("type_flow_analysis", {})
    symmetry = reflective_meta.get("curvature_measurement", {})
    lines = [
        f"intent nodes: {reflective_meta.get('intent_node_count', 0)}",
        f"state-path edges: {len(state_path.get('edges', [])) if isinstance(state_path, Mapping) else 0}",
        f"lifecycle chains: {len(state_path.get('lifecycle_chains', [])) if isinstance(state_path, Mapping) else 0}",
        f"disconnected gaps: {topo.get('gap_count', 0) if isinstance(topo, Mapping) else 0}",
        f"capability ceilings: {boundary.get('ceiling_count', 0) if isinstance(boundary, Mapping) else 0}",
        f"type-flow punctures: {type_flow.get('puncture_count', 0) if isinstance(type_flow, Mapping) else 0}",
        f"symmetry shadowbridges: {symmetry.get('shadowbridge_count', 0) if isinstance(symmetry, Mapping) else 0}",
    ]
    if isinstance(topo, Mapping):
        for gap in topo.get("disconnected_lifecycle_gaps", [])[:3]:
            if isinstance(gap, Mapping):
                lines.append(f"  gap: {gap.get('from_state')} -/-> {gap.get('to_state')}")
    if isinstance(state_path, Mapping):
        for chain in state_path.get("lifecycle_chains", [])[:3]:
            if isinstance(chain, Mapping):
                lines.append(f"  chain: {' -> '.join(chain.get('steps', []))}")
    if isinstance(boundary, Mapping):
        for ceiling in boundary.get("capability_ceilings", [])[:3]:
            if isinstance(ceiling, Mapping):
                lines.append(f"  ceiling: {ceiling.get('terminal_state')} — {ceiling.get('description')}")
    if isinstance(symmetry, Mapping):
        for bridge in symmetry.get("shadowbridges", [])[:3]:
            if isinstance(bridge, Mapping):
                lines.append(f"  shadowbridge: {bridge.get('agent_intent')} — {bridge.get('description')}")
    return "\n".join(lines)


def _render_analysis_stealth(metrics: dict[str, Any], graph: Path, output: Path) -> None:
    from .stealth import customer_preflight_from_metrics

    extended = _status_metrics_extended(output)
    assignment_count, high_risk_assignments = _manifest_assignment_stats()
    integrity_score = _integrity_score(
        extended,
        assignment_count=assignment_count,
        high_risk_assignments=high_risk_assignments,
    )
    preflight = customer_preflight_from_metrics(metrics)
    typer.echo("Gaijinn integrity preflight")
    typer.echo(f"  graph: {graph}")
    typer.echo(f"  integrity_score: {integrity_score}")
    typer.echo(f"  preflight_status: {preflight['preflight_status']}")
    typer.echo(f"  coupling_reviews: {preflight['coupling_review_count']}")
    typer.echo(f"  flagged_files: {preflight['preflight_flag_count']}")
    typer.echo(f"  artifact: {output}")
    typer.echo("  (Set GAIJINN_OPERATOR=1 for internal engineering view.)")


def _echo_analyze_next_steps(summary: Mapping[str, Any]) -> None:
    typer.echo("Next suggested commands:")
    rejection_count = int(summary.get("rejection_count", summary.get("preflight_flag_count", 0)) or 0)
    coupling_count = int(summary.get("shadow_bridge_count", summary.get("coupling_review_count", 0)) or 0)
    if rejection_count > 0 or coupling_count > 0:
        if _stealth_enabled():
            steps = [
                "Review preflight flags and coupling reviews, then rerun `gaijinn analyze`.",
                "Resolve integrity issues before `gaijinn plan` and deploy.",
            ]
        else:
            steps = [
                "Review rejected nodes and Shadow Bridges in the metrics artifact.",
                "Adjust the graph or implementation plan, then rerun `gaijinn analyze`.",
            ]
    else:
        steps = [
            "gaijinn compile-prompt && gaijinn plan --workers 2",
            "gaijinn run-grid --workers 2",
        ]
    for index, command in enumerate(steps, start=1):
        typer.echo(f"{index}. {command}")


# ── Init helpers ───────────────────────────────────────────────────────


def _parse_capabilities(prompt: str) -> list[str]:
    lowered = prompt.lower()
    keyword_map = {
        "api": "api",
        "auth": "auth",
        "database": "database",
        "postgres": "database",
        "sqlite": "database",
        "mysql": "database",
        "frontend": "frontend",
        "react": "frontend",
        "vue": "frontend",
        "svelte": "frontend",
        "test": "testing",
        "jwt": "auth",
        "cli": "cli",
        "worker": "workers",
        "queue": "queues",
    }
    capabilities = sorted({capability for keyword, capability in keyword_map.items() if keyword in lowered})
    return capabilities or ["general"]


def _blueprint_seed(project_prompt: str) -> str:
    return (
        "# Generate Loom Blueprint\n\n"
        "## Project Prompt\n\n"
        f"{project_prompt}\n\n"
        "## Output Contract\n\n"
        "Write the final implementation blueprint to `.gaijinn/blueprint.md`.\n"
        "Keep work units deterministic, dependency-mapped, and safe for isolated workers.\n"
    )


def _blueprint_template(project_prompt: str) -> str:
    return (
        "# Gaijinn Blueprint\n\n"
        "## Project Prompt\n\n"
        f"{project_prompt}\n\n"
        "## Objective\n\n"
        "- Define the production outcome in concrete terms.\n\n"
        "## Work Units\n\n"
        "1. Describe the first isolated worker task, its inputs, and expected artifact.\n"
        "2. Describe the next task after dependencies are satisfied.\n\n"
        "## Dependencies\n\n"
        "- List ordering constraints between work units.\n\n"
        "## Validation\n\n"
        "- List the commands or checks that prove the work is complete.\n"
    )


def _write_agent_files_block(project_prompt: str) -> None:
    block = _agent_files_block(project_prompt)
    for path in AGENT_FILE_PATHS:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        path.write_text(_replace_delimited_block(existing, block), encoding="utf-8")


def _agent_files_block(project_prompt: str) -> str:
    return (
        f"{GAIJINN_AGENT_BLOCK_BEGIN}\n"
        "# Gaijinn Project Guidance\n\n"
        f"- Project prompt: {project_prompt}\n"
        "- Keep generated Gaijinn artifacts under `.gaijinn/`.\n"
        "- Run `gaijinn compile-prompt` after changing `.gaijinn/project.json`.\n"
        "- Run `gaijinn scan .` before graph analysis when source files change.\n"
        "- Run `gaijinn analyze` before creating worker directories.\n"
        "- Run `gaijinn run-grid --workers 2` to create isolated worker handoffs.\n"
        "- **Council (required):** Read `.gaijinn/bridge/council.md` before acting. "
        'Post replies with `gaijinn council say --as cursor "..."` (user: `--as user`). '
        "One shared thread — never ask the human to relay messages between agents.\n"
        "- **Hermes:** `gaijinn hermes` or `gaijinn hermes -i` from terminal (council-backed).\n"
        f"{GAIJINN_AGENT_BLOCK_END}\n"
    )


def _replace_delimited_block(existing: str, block: str) -> str:
    start = existing.find(GAIJINN_AGENT_BLOCK_BEGIN)
    end = existing.find(GAIJINN_AGENT_BLOCK_END)
    if start != -1 and end != -1 and end >= start:
        end += len(GAIJINN_AGENT_BLOCK_END)
        while end < len(existing) and existing[end] in "\r\n":
            end += 1
        prefix = existing[:start].rstrip()
        suffix = existing[end:].lstrip()
        pieces = [piece for piece in (prefix, block.rstrip(), suffix) if piece]
        return "\n\n".join(pieces) + "\n"

    prefix = existing.rstrip()
    if not prefix:
        return block
    return f"{prefix}\n\n{block}"


def _echo_init_next_steps(blueprint_template: bool) -> None:
    if blueprint_template:
        typer.echo(f"Before running the commands, edit {BLUEPRINT_TEMPLATE_PATH}.")
    typer.echo("Next suggested commands:")
    steps = [
        "loom compile-prompt",
        "loom scan .",
        "loom analyze",
        "loom plan --workers 2",
        "loom run-grid --workers 2",
    ]
    for index, command in enumerate(steps, start=1):
        typer.echo(f"{index}. {command}")


# ── Compile-prompt helpers ─────────────────────────────────────────────


def _giv_from_profile(profile: Any) -> GIV:
    allowed_paths = tuple(profile.recommended_paths) or (".")
    invariants = (
        "deterministic output",
        "preserve existing project.json compatibility",
        "write generated Loom artifacts under .gaijinn/",
    )
    return GIV(
        worker_id="project",
        allowed_paths=allowed_paths,
        capabilities=tuple(profile.capabilities),
        prohibitions=tuple(profile.prohibitions),
        invariants=invariants,
    )


def _compile_prompt_summary(giv: GIV, profile: Any) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "giv": GIV_PATH.as_posix(),
        "intent": INTENT_PATH.as_posix(),
        "work_domains": list(profile.capabilities),
        "allowed_paths": list(giv.allowed_paths),
        "prohibitions": list(giv.prohibitions),
        "risk_flags": list(profile.risk_flags),
    }


def _intent_text(project_prompt: str, giv: GIV) -> str:
    return f"# Gaijinn Intent Constraints\n\n## Project Prompt\n\n{project_prompt}\n\n{giv.render_intent()}"


def _render_compile_prompt_summary(summary: Mapping[str, Any]) -> None:
    typer.echo(f"Compiled GIV intent to {summary['giv']} and {summary['intent']}")
    typer.echo(f"work domains: {_summary_list(summary['work_domains'])}")
    typer.echo(f"allowed paths: {_summary_list(summary['allowed_paths'])}")
    typer.echo(f"prohibitions: {_summary_list(summary['prohibitions'])}")
    typer.echo(f"risk flags: {_summary_list(summary['risk_flags'])}")


# ── Plan helpers ───────────────────────────────────────────────────────


def _risk_rank(risk: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}[risk]


def _render_plan_summary(blueprint: Blueprint, workers: int) -> None:
    typer.echo(f"Wrote blueprint JSON to {BLUEPRINT_JSON_PATH}")
    typer.echo(f"Wrote blueprint Markdown to {BLUEPRINT_TEMPLATE_PATH}")
    typer.echo(f"work_units: {len(blueprint.work_units)}")
    typer.echo(f"intended_workers: {workers}")
    typer.echo(f"highest_risk: {_highest_risk(blueprint)}")
    typer.echo(f"shadow_bridge_units: {_shadow_bridge_unit_count(blueprint)}")


def _highest_risk(blueprint: Blueprint) -> str:
    risks = [unit.estimated_risk for unit in blueprint.work_units]
    return max(risks, key=_risk_rank) if risks else "low"


def _shadow_bridge_unit_count(blueprint: Blueprint) -> int:
    markers = ("Dark Bridge atomic block", "Consolidate coupling review block", "Shadow Bridge")
    return sum(1 for unit in blueprint.work_units if any(marker in unit.title for marker in markers))


# ── Doctor helpers ─────────────────────────────────────────────────────


def _doctor_diagnostics() -> list[dict[str, Any]]:
    diagnostics = [
        _check_python_version(),
        *_check_package_imports(),
        *_check_dependency_imports(),
        _check_git(),
        _check_gaijinn_writable(),
        *_check_artifacts(),
    ]
    return diagnostics


def _diagnostic(name: str, status: str, detail: str, *, hard_failure: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "hard_failure": bool(hard_failure),
        "detail": detail,
    }


def _overall_diagnostic_status(diagnostics: list[dict[str, Any]]) -> str:
    if any(item["status"] == "fail" and item["hard_failure"] for item in diagnostics):
        return "fail"
    if any(item["status"] in {"fail", "warn"} for item in diagnostics):
        return "warn"
    return "pass"


def _check_python_version() -> dict[str, Any]:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return _diagnostic("python", "pass", f"Python {version}")


def _check_package_imports() -> list[dict[str, Any]]:
    modules = ("aoc_cli", "aoc_cli.cli", "aoc_supervisor")
    results = []
    for module in modules:
        try:
            importlib.import_module(module)
        except Exception as exc:
            results.append(
                _diagnostic(
                    f"import:{module}",
                    "fail",
                    f"cannot import {module}: {exc}",
                    hard_failure=True,
                )
            )
        else:
            results.append(_diagnostic(f"import:{module}", "pass", f"{module} importable"))
    return results


def _check_dependency_imports() -> list[dict[str, Any]]:
    dependencies = {
        "networkx": "networkx",
        "numpy": "numpy",
        "POT": "ot",
        "rich": "rich",
        "typer": "typer",
    }
    results = []
    for label, module in dependencies.items():
        try:
            importlib.import_module(module)
        except Exception as exc:
            results.append(
                _diagnostic(
                    f"dependency:{label}",
                    "fail",
                    f"cannot import {module}: {exc}",
                    hard_failure=True,
                )
            )
        else:
            results.append(_diagnostic(f"dependency:{label}", "pass", f"{module} importable"))
    return results


def _check_git() -> dict[str, Any]:
    if shutil.which("git") is None:
        return _diagnostic(
            "git",
            "warn",
            "git executable not found; run-grid will use copy mode outside git worktrees.",
        )
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return _diagnostic("git", "warn", "git is installed, but this directory is not a git worktree.")
    clean_detail = "clean" if _git_clean() else "dirty"
    return _diagnostic("git", "pass", f"inside git worktree ({clean_detail})")


def _check_gaijinn_writable() -> dict[str, Any]:
    try:
        GAIJINN_DIR.mkdir(parents=True, exist_ok=True)
        probe = GAIJINN_DIR / ".doctor-write-test"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        return _diagnostic(
            ".gaijinn writable",
            "fail",
            f"cannot write to {GAIJINN_DIR}: {exc}",
            hard_failure=True,
        )
    return _diagnostic(".gaijinn writable", "pass", f"{GAIJINN_DIR} is writable")


def _check_artifacts() -> list[dict[str, Any]]:
    checks = [
        ("project", PROJECT_PATH, _validate_project_artifact, 'run `gaijinn init "PROJECT PROMPT"`'),
        ("graph", DEFAULT_GRAPH_PATH, _validate_graph_artifact, "run `gaijinn scan .`"),
        ("metrics", DEFAULT_METRICS_PATH, _validate_metrics_artifact, "run `gaijinn analyze`"),
        ("giv", GIV_PATH, _validate_giv_artifact, "run `gaijinn compile-prompt`"),
        ("blueprint", BLUEPRINT_JSON_PATH, _validate_blueprint_artifact, "run `gaijinn plan --workers 2`"),
        (
            "worker manifest",
            WORKERS_DIR / "manifest.json",
            _validate_worker_manifest_artifact,
            "run `gaijinn run-grid --workers 2`",
        ),
    ]
    diagnostics = []
    for name, path, validator, missing_detail in checks:
        if not path.exists():
            diagnostics.append(_diagnostic(f"artifact:{name}", "warn", f"{path} is missing; {missing_detail}."))
            continue
        try:
            validator(path)
        except Exception as exc:
            diagnostics.append(
                _diagnostic(
                    f"artifact:{name}",
                    "fail",
                    f"{path} is invalid: {exc}",
                    hard_failure=True,
                )
            )
        else:
            diagnostics.append(_diagnostic(f"artifact:{name}", "pass", f"{path} is valid"))
    return diagnostics


def _validate_project_artifact(path: Path) -> None:
    if path != PROJECT_PATH:
        raise ValueError(f"expected {PROJECT_PATH}")
    ensure_state(Path.cwd())


def _validate_graph_artifact(path: Path) -> None:
    payload = _load_json_artifact(path, "graph JSON", "gaijinn scan .")
    normalized = _normalize_graph_data(payload)
    _validate_graph_for_analysis(normalized, path)


def _validate_metrics_artifact(path: Path) -> None:
    payload = _load_json_artifact(path, "metrics JSON", "gaijinn analyze")
    if not isinstance(payload.get("gravity_meta"), Mapping):
        raise ValueError("missing gravity_meta object")
    if not isinstance(payload.get("curvature_meta"), Mapping):
        raise ValueError("missing curvature_meta object")
    reflective_meta = payload.get("reflective_meta")
    if reflective_meta is not None and not isinstance(reflective_meta, Mapping):
        raise ValueError("reflective_meta must be an object when present")


def _validate_giv_artifact(path: Path) -> None:
    payload = _load_json_artifact(path, "GIV profile", "gaijinn compile-prompt")
    GIV.from_dict(payload)


def _validate_blueprint_artifact(path: Path) -> None:
    payload = _load_json_artifact(path, "blueprint JSON", "gaijinn plan --workers 2")
    Blueprint.from_dict(payload)


def _validate_worker_manifest_artifact(path: Path) -> None:
    payload = _load_json_artifact(path, "worker manifest", "gaijinn run-grid --workers 2")
    worker_count = payload.get("worker_count")
    workers = payload.get("workers")
    if not isinstance(worker_count, int) or worker_count < 1:
        raise ValueError("worker_count must be a positive integer")
    if not isinstance(workers, list) or len(workers) != worker_count:
        raise ValueError("workers must list exactly worker_count entries")


def _render_diagnostics(diagnostics: list[dict[str, Any]]) -> None:
    headers = ("STATUS", "CHECK", "DETAIL")
    rows = [
        (
            str(item["status"]).upper(),
            str(item["name"]),
            str(item["detail"]),
        )
        for item in diagnostics
    ]
    status_width = max(len(headers[0]), *(len(row[0]) for row in rows))
    name_width = max(len(headers[1]), *(len(row[1]) for row in rows))
    typer.echo(f"{headers[0]:<{status_width}}  {headers[1]:<{name_width}}  {headers[2]}")
    typer.echo(f"{'-' * status_width}  {'-' * name_width}  {'-' * len(headers[2])}")
    for status, name, detail in rows:
        typer.echo(f"{status:<{status_width}}  {name:<{name_width}}  {detail}")


# ── Monitor helpers ────────────────────────────────────────────────────


def _load_validate_system_state() -> Callable[[], Any]:
    _ensure_supervisor_package_path()
    candidates = (
        "aoc_supervisor",
        "aoc_supervisor.enforcer",
        "aoc_supervisor.supervisor",
        "aoc_supervisor.daemon",
        "aoc_supervisor.runtime",
    )

    for module_name in candidates:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue

        validator = getattr(module, "validate_system_state", None)
        if callable(validator):
            return validator

    raise typer.BadParameter("validate_system_state() was not found in the aoc_supervisor package")


def _ensure_supervisor_package_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    supervisor_root = repo_root / "aoc_supervisor"
    if supervisor_root.is_dir():
        supervisor_path = str(supervisor_root)
        if supervisor_path not in sys.path:
            sys.path.insert(0, supervisor_path)


def _file_signature(path: Path) -> tuple[int, int, int] | None:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return (stat.st_mtime_ns, stat.st_size, stat.st_ino)


def _run_validation(validate_system_state: Callable[[], Any]) -> None:
    try:
        result = validate_system_state()
    except Exception as exc:  # pragma: no cover - status boundary.
        _echo_status(f"validation failed: {exc}", err=True)
        return

    status = getattr(result, "status", None)
    if status is None and isinstance(result, Mapping):
        status = result.get("status")
    if status is None:
        status = "ok" if result is None or result is True else str(result)

    _echo_status(f"validation status: {status}")


def _echo_status(message: str, *, err: bool = False) -> None:
    typer.echo(f"[gaijinn monitor] {message}", err=err)
