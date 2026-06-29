"""analyze command implementation."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import typer

from ..blueprint_compiler import compile_inferred_json
from ..errors import GaijinnError
from ..gravity import compute_gravity_and_curvature
from ..helpers import (
    _analysis_summary,
    _echo_analyze_next_steps,
    _load_graph,
    _normalize_graph_data,
    _project_analysis_paths,
    _render_analysis,
    _update_project_metrics_path,
    _validate_graph_for_analysis,
)
from ..helpers.constants import GROK_BINARY, INFERRED_JSON_PATH, PROJECT_PATH
from ..helpers.diagnostics import (
    _integrity_score,
    _manifest_assignment_stats,
    _status_metrics_extended,
    _stealth_enabled,
)
from ..helpers.io import _load_json_artifact
from ..helpers.scan import validate_grid_readiness
from ..helpers.stealth import customer_analysis_summary, sanitize_blocked_reasons
from ..inferring import infer_reflective_layer
from ..moat_authority import (
    build_static_scopes,
    evaluate_boundary,
    ingest_raw_semantic_proposal,
    load_overrides,
)


def analyze_cmd(
    graph: Path,
    output: Path,
    json_output: bool,
    fail_on_rejection: bool,
    fail_on_shadow_bridge: bool,
) -> None:
    """Run mathematical graph analysis and write the metrics manifest."""
    graph, output = _project_analysis_paths(graph, output)
    graph_data = _load_graph(graph)
    normalized_graph = _normalize_graph_data(graph_data)
    _validate_graph_for_analysis(normalized_graph, graph)
    try:
        metrics = compute_gravity_and_curvature(normalized_graph)
    except (TypeError, ValueError) as exc:
        raise typer.BadParameter(f"cannot analyze {graph}: {exc}") from exc
    metrics["schema_version"] = 1
    interaction_graph = graph_data.get("interaction_graph")
    if isinstance(interaction_graph, list) and interaction_graph:
        metrics["reflective_meta"] = infer_reflective_layer(interaction_graph)
    else:
        metrics["reflective_meta"] = _empty_reflective_meta()

    project_prompt = _load_project_prompt()
    if project_prompt and isinstance(interaction_graph, list):
        compile_inferred_json(
            project_prompt=project_prompt,
            interaction_graph=interaction_graph,
            reflective_meta=metrics["reflective_meta"],
            output_path=INFERRED_JSON_PATH,
        )
        raw = ingest_raw_semantic_proposal(None, interaction_graph)

        # P2: Feed reflective dark-bridge edges into the boundary check
        edges_by_source = {}
        for edge_payload in metrics.get("curvature_meta", {}).get("edges", {}).values():
            src = edge_payload.get("source")
            if src:
                edges_by_source.setdefault(src, []).append(edge_payload)

        for node in interaction_graph:
            node_key = node.get("agent_intent") or node.get("intent") or node.get("id")
            if node_key:
                node["edges"] = edges_by_source.get(str(node_key), [])

        # P3: Use a unique session id for authority decisions
        session_id = uuid.uuid4().hex[:12]

        evaluate_boundary(
            raw_proposals=raw,
            canonical_graph=interaction_graph,
            static_scopes_by_node=build_static_scopes(interaction_graph),
            session_id=session_id,
            overrides=load_overrides(),
        )
        metrics["inferred_path"] = INFERRED_JSON_PATH.as_posix()

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _update_project_metrics_path(output)

    summary = _analysis_summary(metrics, graph, output)
    grid_readiness = validate_grid_readiness(output)
    if json_output:
        if _stealth_enabled():
            extended = _status_metrics_extended(output)
            assignment_count, high_risk_assignments = _manifest_assignment_stats()
            public_summary = customer_analysis_summary(
                metrics,
                graph=graph.as_posix(),
                artifact=output.as_posix(),
                integrity_score=_integrity_score(
                    extended,
                    assignment_count=assignment_count,
                    high_risk_assignments=high_risk_assignments,
                ),
            )
            typer.echo(json.dumps(public_summary, sort_keys=True))
        else:
            typer.echo(json.dumps(summary, sort_keys=True))
    else:
        _render_analysis(metrics, graph, output)
        if _stealth_enabled():
            extended = _status_metrics_extended(output)
            assignment_count, high_risk_assignments = _manifest_assignment_stats()
            next_summary = customer_analysis_summary(
                metrics,
                graph=graph.as_posix(),
                artifact=output.as_posix(),
                integrity_score=_integrity_score(
                    extended,
                    assignment_count=assignment_count,
                    high_risk_assignments=high_risk_assignments,
                ),
            )
        else:
            next_summary = summary
        _echo_analyze_next_steps(next_summary)
        _echo_terminal_bridge_readiness(grid_readiness)

    rejection_count = summary["rejection_count"]
    coupling_count = summary["shadow_bridge_count"]
    if fail_on_rejection and rejection_count > 0:
        raise typer.Exit(code=2)
    if fail_on_shadow_bridge and coupling_count > 0:
        raise typer.Exit(code=3)


def _empty_reflective_meta() -> dict[str, object]:
    return {
        "schema_version": 1,
        "layer": "reflective",
        "intent_node_count": 0,
        "topological_inference": {
            "state_graph": {},
            "state_path_edges": [],
            "lifecycle_chains": [],
            "dependency_contracts": [],
            "disconnected_lifecycle_gaps": [],
            "gap_count": 0,
        },
        "state_path_chaining": {"edges": [], "lifecycle_chains": [], "dependency_contracts": []},
        "topological_boundary_scan": {"capability_ceilings": [], "ceiling_count": 0},
        "type_flow_analysis": {"shadowbridges": [], "shadowbridge_count": 0, "puncture_count": 0},
        "curvature_measurement": {"shadowbridges": [], "shadowbridge_count": 0},
        "shadowbridge_count": 0,
        "shadowbridges": [],
    }


def _load_project_prompt() -> str:
    if not PROJECT_PATH.exists():
        return ""
    try:
        payload = _load_json_artifact(PROJECT_PATH, "project.json", 'gaijinn init "PROJECT PROMPT"')
    except GaijinnError:
        return ""
    prompt = payload.get("project_prompt", "")
    return str(prompt).strip()


def _echo_terminal_bridge_readiness(grid_readiness: dict[str, object]) -> None:
    typer.echo("Deploy readiness:")
    typer.echo(f"  grid_spawn_ready: {grid_readiness['ready']}")
    typer.echo(f"  grok_available: {shutil.which(GROK_BINARY) is not None}")
    if grid_readiness["blocked_reasons"]:
        reasons = sanitize_blocked_reasons([str(item) for item in grid_readiness["blocked_reasons"]])
        typer.echo(f"  blocked: {', '.join(reasons)}")
    if grid_readiness["shadow_bridge_count"] == 0 and grid_readiness["rejected_node_count"] == 0:
        typer.echo("Next deploy command:")
        typer.echo("  gaijinn run-grid --workers 2 && gaijinn grid-spawn --workers 2")
