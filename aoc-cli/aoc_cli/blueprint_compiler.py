"""Stage 1 Blueprint Compiler — synthesizes Layer 0/1/2 artifacts.

Pipeline:
  User prompt + scan graph  →  inferred.json (Layer 2 workflows)
  reflective_meta           →  lifecycle chains partitioned for workers
  MOAT profile              →  Layer 0 invariants embedded in inferred.json
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .moat import parse_prompt

INFERRED_SCHEMA_VERSION = 1


def compile_inferred_json(
    *,
    project_prompt: str,
    interaction_graph: Sequence[Mapping[str, Any]],
    reflective_meta: Mapping[str, Any],
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Compile Layer 2 inferred workflows from reflective analysis."""
    moat = parse_prompt(project_prompt)
    workflows = _workflows_from_reflective(reflective_meta, interaction_graph)
    payload = {
        "schema_version": INFERRED_SCHEMA_VERSION,
        "layer": 2,
        "project_prompt": project_prompt,
        "layer0": {
            "functional_domains": moat.capabilities or ["general"],
            "invariants": list(moat.prohibitions),
            "risk_flags": list(moat.risk_flags),
        },
        "workflows": workflows,
        "workflow_count": len(workflows),
        "disconnected_gaps": _gap_records(reflective_meta),
        "shadowbridges": _shadowbridge_records(reflective_meta),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _workflows_from_reflective(
    reflective_meta: Mapping[str, Any],
    interaction_graph: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    state_path = reflective_meta.get("state_path_chaining", {})
    chains = state_path.get("lifecycle_chains", []) if isinstance(state_path, Mapping) else []
    node_by_intent = {
        str(node.get("agent_intent") or node.get("intent") or ""): node
        for node in interaction_graph
        if isinstance(node, Mapping)
    }
    workflows: list[dict[str, Any]] = []
    for index, chain in enumerate(chains, start=1):
        if not isinstance(chain, Mapping):
            continue
        steps = [str(step) for step in chain.get("steps", [])]
        if not steps:
            continue
        clusters = sorted(
            {
                str(node_by_intent[step].get("resource_cluster"))
                for step in steps
                if step in node_by_intent and node_by_intent[step].get("resource_cluster")
            }
        )
        name = clusters[0] if clusters else steps[0]
        workflows.append(
            {
                "id": f"wf-{index:03d}",
                "name": name,
                "description": f"Lifecycle chain: {' → '.join(steps)}",
                "steps": steps,
                "entry": chain.get("entry"),
                "terminal": chain.get("terminal"),
                "resource_clusters": clusters,
                "allowed_paths": _paths_for_steps(steps, node_by_intent),
            }
        )
    return workflows


def _paths_for_steps(steps: Sequence[str], node_by_intent: Mapping[str, Mapping[str, Any]]) -> list[str]:
    paths: set[str] = set()
    for step in steps:
        node = node_by_intent.get(step)
        if not isinstance(node, Mapping):
            continue
        source_file = node.get("source_file")
        if isinstance(source_file, str) and source_file:
            parent = str(Path(source_file).parent)
            paths.add(parent if parent != "." else source_file)
    return sorted(paths) or ["."]


def _gap_records(reflective_meta: Mapping[str, Any]) -> list[dict[str, Any]]:
    topo = reflective_meta.get("topological_inference", {})
    if isinstance(topo, Mapping):
        gaps = topo.get("disconnected_lifecycle_gaps", [])
        return [gap for gap in gaps if isinstance(gap, Mapping)]
    return []


def _shadowbridge_records(reflective_meta: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key in ("curvature_measurement", "type_flow_analysis"):
        section = reflective_meta.get(key, {})
        if not isinstance(section, Mapping):
            continue
        for bridge in section.get("shadowbridges", []):
            if isinstance(bridge, Mapping):
                records.append(dict(bridge))
    return records
