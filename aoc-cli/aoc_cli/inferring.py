"""Layer 2 Reflective inference — converts Layer 1 Intent Nodes into emergent rules.

GAIJINN BLUEPRINT — Inferring Process (Layer 1 → Layer 2)
---------------------------------------------------------
Non-sentient engineering pipelines (no LLM reasoning):

1. Topological Inference — DFS reachability on state transition graph
2. Topological Boundary Scans — terminal states with no recovery path
3. Type-Flow Analysis — AST taint tracking (source → sink punctures)
4. Curvature Measurement — parameter symmetry anomalies (cluster backup)

Entry: infer_reflective_layer(interaction_graph) after scan produces Layer 1 nodes.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

INFERRING_SCHEMA_VERSION = 1


def infer_reflective_layer(interaction_graph: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Run all three inferring passes and return the Layer 2 reflective artifact."""
    nodes = [_normalize_intent_node(raw) for raw in interaction_graph if isinstance(raw, Mapping)]
    state_edges = _state_path_chaining_edges(nodes)
    state_graph = _build_state_transition_graph(nodes)
    lifecycle = _compile_lifecycle_chains(nodes, state_edges)
    contracts = _dependency_contracts(nodes, state_edges)
    disconnected_gaps = _disconnected_lifecycle_gaps(nodes, state_graph)
    ceilings = _topological_boundary_scan(nodes, state_edges)
    type_flow_bridges = _type_flow_shadowbridges(nodes)
    symmetry_bridges = _curvature_measurement(nodes)
    shadowbridges = _merge_shadowbridges(type_flow_bridges, symmetry_bridges)

    return {
        "schema_version": INFERRING_SCHEMA_VERSION,
        "layer": "reflective",
        "intent_node_count": len(nodes),
        "topological_inference": {
            "state_graph": state_graph,
            "state_path_edges": state_edges,
            "lifecycle_chains": lifecycle,
            "dependency_contracts": contracts,
            "disconnected_lifecycle_gaps": disconnected_gaps,
            "gap_count": len(disconnected_gaps),
        },
        "state_path_chaining": {
            "edges": state_edges,
            "lifecycle_chains": lifecycle,
            "dependency_contracts": contracts,
        },
        "topological_boundary_scan": {
            "capability_ceilings": ceilings,
            "ceiling_count": len(ceilings),
        },
        "type_flow_analysis": {
            "shadowbridges": type_flow_bridges,
            "shadowbridge_count": len(type_flow_bridges),
            "puncture_count": len(type_flow_bridges),
        },
        "curvature_measurement": {
            "shadowbridges": symmetry_bridges,
            "shadowbridge_count": len(symmetry_bridges),
        },
        "shadowbridge_count": len(shadowbridges),
        "shadowbridges": shadowbridges,
    }


def _normalize_intent_node(raw: Mapping[str, Any]) -> dict[str, Any]:
    intent = raw.get("agent_intent") or raw.get("intent") or raw.get("id")
    if intent is None:
        raise ValueError(f"intent node lacks agent_intent/intent/id: {raw!r}")

    prior = raw.get("valid_prior_state")
    resulting = raw.get("resulting_state")
    context_params = _normalize_param_list(raw.get("context_params"))
    query_params = _normalize_param_list(raw.get("query_params"))
    cluster = raw.get("resource_cluster")
    if cluster is None:
        cluster = _infer_resource_cluster(str(intent), raw.get("http_path"), raw.get("http_method"))

    return {
        "agent_intent": str(intent),
        "valid_prior_state": None if prior is None else str(prior),
        "resulting_state": None if resulting is None else str(resulting),
        "http_method": raw.get("http_method"),
        "http_path": raw.get("http_path"),
        "side_effects": _normalize_param_list(raw.get("side_effects")),
        "guard_conditions": _normalize_param_list(raw.get("guard_conditions")),
        "context_params": context_params,
        "query_params": query_params,
        "resource_cluster": str(cluster) if cluster else None,
        "capability_level": _coerce_float(raw.get("capability_level"), default=0.0),
        "side_effect_score": _coerce_float(raw.get("side_effect_score"), default=0.0),
        "source_file": raw.get("source_file"),
    }


def _normalize_param_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _coerce_float(value: Any, *, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _infer_resource_cluster(intent: str, http_path: Any, http_method: Any) -> str | None:
    if isinstance(http_path, str) and http_path:
        segments = [segment for segment in http_path.strip("/").split("/") if segment and not segment.startswith("{")]
        if segments:
            return segments[-1].replace("-", "_")
    for suffix in ("_create", "_activate", "_trigger", "_cancel", "_delete", "_update", "_get", "_list"):
        if intent.endswith(suffix):
            return intent[: -len(suffix)]
    return None


def _state_path_chaining_edges(nodes: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Pass 1a: draw directed edges where A.resulting_state == B.valid_prior_state."""
    by_prior: dict[str, list[str]] = defaultdict(list)
    for node in nodes:
        prior = node.get("valid_prior_state")
        if prior is not None:
            by_prior[str(prior)].append(str(node["agent_intent"]))

    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for node in nodes:
        source = str(node["agent_intent"])
        resulting = node.get("resulting_state")
        if resulting is None:
            continue
        for target in by_prior.get(str(resulting), []):
            if target == source:
                continue
            key = (source, target)
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "via_state": str(resulting),
                }
            )
    return sorted(edges, key=lambda item: (item["source"], item["target"]))


def _compile_lifecycle_chains(
    nodes: Sequence[Mapping[str, Any]],
    state_edges: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    """Pass 1b: trace state-path edges from entry nodes to compile lifecycle chains."""
    if not nodes:
        return []

    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in state_edges:
        adjacency[edge["source"]].append(edge["target"])

    entry_nodes = sorted(str(node["agent_intent"]) for node in nodes if node.get("valid_prior_state") is None)
    if not entry_nodes:
        entry_nodes = sorted(str(node["agent_intent"]) for node in nodes)

    chains: list[dict[str, Any]] = []
    seen_signatures: set[tuple[str, ...]] = set()

    for entry in entry_nodes:
        path = [entry]
        visited = {entry}
        current = entry
        while True:
            successors = [target for target in adjacency.get(current, []) if target not in visited]
            if not successors:
                break
            if len(successors) > 1:
                for branch in successors:
                    branch_path = path + [branch]
                    signature = tuple(branch_path)
                    if signature not in seen_signatures:
                        seen_signatures.add(signature)
                        chains.append(_chain_record(branch_path, nodes))
                break
            current = successors[0]
            path.append(current)
            visited.add(current)

        signature = tuple(path)
        if signature not in seen_signatures:
            seen_signatures.add(signature)
            chains.append(_chain_record(path, nodes))

    return sorted(chains, key=lambda item: (item["entry"], item["terminal"], len(item["steps"])))


def _chain_record(path: list[str], nodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    node_by_intent = {str(node["agent_intent"]): node for node in nodes}
    states = []
    for intent in path:
        node = node_by_intent.get(intent, {})
        states.append(
            {
                "intent": intent,
                "valid_prior_state": node.get("valid_prior_state"),
                "resulting_state": node.get("resulting_state"),
            }
        )
    return {
        "entry": path[0],
        "terminal": path[-1],
        "steps": path,
        "states": states,
        "length": len(path),
    }


def _dependency_contracts(
    nodes: Sequence[Mapping[str, Any]],
    state_edges: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Pass 1c: each state edge implies a dependency contract before transition."""
    node_by_intent = {str(node["agent_intent"]): node for node in nodes}
    contracts: list[dict[str, str]] = []
    for edge in state_edges:
        target = node_by_intent.get(edge["target"], {})
        required_state = target.get("valid_prior_state") or edge.get("via_state", "")
        contract = {
            "intent": edge["target"],
            "requires_prior_state": str(required_state),
            "requires_node": edge["source"],
            "via_state": str(edge.get("via_state", "")),
        }
        side_effects = target.get("side_effects") or ()
        if side_effects:
            contract["requires_side_effects"] = ", ".join(side_effects)
        contracts.append(contract)
    return sorted(contracts, key=lambda item: (item["intent"], item["requires_node"]))


def _topological_boundary_scan(
    nodes: Sequence[Mapping[str, Any]],
    state_edges: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    """Pass 2: find terminal states with no recovery path → capability ceilings."""
    resulting_states = {str(node["resulting_state"]) for node in nodes if node.get("resulting_state")}
    prior_states = {str(node["valid_prior_state"]) for node in nodes if node.get("valid_prior_state")}
    terminal_states = sorted(resulting_states - prior_states)

    transitions: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        prior = node.get("valid_prior_state")
        resulting = node.get("resulting_state")
        if prior is not None and resulting is not None:
            transitions[str(prior)].add(str(resulting))

    ceilings: list[dict[str, Any]] = []
    for terminal in terminal_states:
        outgoing = sorted(transitions.get(terminal, ()))
        recovery_targets = _recovery_targets_for_terminal(terminal, nodes)
        missing_recoveries: list[dict[str, str]] = []

        for target_prior, target_result in recovery_targets:
            has_path = any(
                node.get("valid_prior_state") == target_prior and node.get("resulting_state") == target_result
                for node in nodes
            )
            if not has_path:
                missing_recoveries.append(
                    {
                        "required_prior_state": target_prior,
                        "missing_resulting_state": target_result,
                    }
                )

        if missing_recoveries or not outgoing:
            ceilings.append(
                {
                    "terminal_state": terminal,
                    "outgoing_states": outgoing,
                    "missing_recoveries": missing_recoveries,
                    "description": _ceiling_description(terminal, missing_recoveries, outgoing),
                }
            )

    return sorted(ceilings, key=lambda item: item["terminal_state"])


def _recovery_targets_for_terminal(
    terminal: str,
    nodes: Sequence[Mapping[str, Any]],
) -> list[tuple[str | None, str]]:
    """Infer plausible recovery transitions from non-terminal entry states."""
    if terminal.endswith("_failed"):
        prefix = terminal[: -len("_failed")]
        return [(terminal, f"{prefix}_pending"), (terminal, f"{prefix}_active")]
    if terminal.endswith("_cancelled"):
        prefix = terminal[: -len("_cancelled")]
        return [(terminal, f"{prefix}_pending"), (terminal, f"{prefix}_active")]
    entry_states = sorted(
        {
            str(node["resulting_state"])
            for node in nodes
            if node.get("valid_prior_state") is None and node.get("resulting_state")
        }
    )
    return [(terminal, state) for state in entry_states]


def _ceiling_description(
    terminal: str,
    missing_recoveries: Sequence[Mapping[str, str]],
    outgoing: Sequence[str],
) -> str:
    if missing_recoveries:
        first = missing_recoveries[0]
        return (
            f"No transition from {terminal} to {first['missing_resulting_state']}; "
            "retry requires starting a new lifecycle chain."
        )
    if not outgoing:
        return f"Terminal state {terminal} has no outgoing transitions."
    return f"State {terminal} only transitions to {', '.join(outgoing)}."


def _curvature_measurement(nodes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Pass 3: detect parameter symmetry breaks within resource clusters → shadowbridges."""
    clusters: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for node in nodes:
        cluster = node.get("resource_cluster")
        if cluster:
            clusters[str(cluster)].append(node)

    anomalies: list[dict[str, Any]] = []
    for cluster, members in sorted(clusters.items()):
        if len(members) < 2:
            continue

        context_sets = [frozenset(node.get("context_params") or ()) for node in members]
        query_sets = [frozenset(node.get("query_params") or ()) for node in members]
        expected_context = _majority_frozenset(context_sets)
        expected_query = _majority_frozenset(query_sets)

        for node in members:
            context = frozenset(node.get("context_params") or ())
            query = frozenset(node.get("query_params") or ())
            missing_context = sorted(expected_context - context)
            missing_query = sorted(expected_query - query)
            if not missing_context and not missing_query:
                continue

            symmetry_score = (
                1.0
                - (
                    (len(missing_context) / max(len(expected_context), 1))
                    + (len(missing_query) / max(len(expected_query), 1))
                )
                / 2.0
            )
            anomalies.append(
                {
                    "agent_intent": str(node["agent_intent"]),
                    "resource_cluster": cluster,
                    "expected_context_params": sorted(expected_context),
                    "expected_query_params": sorted(expected_query),
                    "actual_context_params": sorted(context),
                    "actual_query_params": sorted(query),
                    "missing_context_params": missing_context,
                    "missing_query_params": missing_query,
                    "curvature_anomaly": round(symmetry_score, 4),
                    "is_shadowbridge": bool(missing_context or missing_query),
                    "description": _shadowbridge_description(
                        str(node["agent_intent"]),
                        cluster,
                        missing_context,
                        missing_query,
                    ),
                }
            )

    return sorted(anomalies, key=lambda item: (item["resource_cluster"], item["agent_intent"]))


def _majority_frozenset(values: Sequence[frozenset[str]]) -> frozenset[str]:
    if not values:
        return frozenset()
    counts: dict[frozenset[str], int] = defaultdict(int)
    for value in values:
        counts[value] += 1
    return max(counts, key=lambda key: (counts[key], -len(key), sorted(key)))


def _shadowbridge_description(
    intent: str,
    cluster: str,
    missing_context: Sequence[str],
    missing_query: Sequence[str],
) -> str:
    parts: list[str] = []
    if missing_context:
        parts.append(f"missing context params {list(missing_context)}")
    if missing_query:
        parts.append(f"missing query params {list(missing_query)}")
    detail = " and ".join(parts)
    return f"{intent} breaks {cluster} cluster symmetry ({detail})."


def _build_state_transition_graph(nodes: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    """Directed state graph: prior_state → resulting_state per intent node."""
    adjacency: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        prior = node.get("valid_prior_state")
        resulting = node.get("resulting_state")
        if resulting is None:
            continue
        source_state = "__start__" if prior is None else str(prior)
        adjacency[source_state].add(str(resulting))
    return {state: sorted(targets) for state, targets in sorted(adjacency.items())}


def _dfs_reachable(state_graph: Mapping[str, Sequence[str]], start: str) -> set[str]:
    """Depth-first reachability from a state in the transition graph."""
    visited: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        for neighbor in state_graph.get(current, ()):
            if neighbor not in visited:
                stack.append(neighbor)
    return visited


def _state_resource_prefix(state: str) -> str:
    for suffix in (
        "_created",
        "_active",
        "_running",
        "_pending",
        "_failed",
        "_cancelled",
        "_deleted",
        "_completed",
        "_updated",
    ):
        if state.endswith(suffix):
            return state[: -len(suffix)]
    return state


def _disconnected_lifecycle_gaps(
    nodes: Sequence[Mapping[str, Any]],
    state_graph: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Prove absence of paths between expected state pairs (graph reachability)."""
    resulting_states = sorted({str(node["resulting_state"]) for node in nodes if node.get("resulting_state")})
    required_states = sorted({str(node["valid_prior_state"]) for node in nodes if node.get("valid_prior_state")})
    gaps: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for from_state in resulting_states:
        reachable = _dfs_reachable(state_graph, from_state)
        for to_state in required_states:
            if from_state == to_state or to_state in reachable:
                continue
            if _state_resource_prefix(from_state) != _state_resource_prefix(to_state):
                continue
            key = (from_state, to_state)
            if key in seen:
                continue
            seen.add(key)
            gaps.append(
                {
                    "from_state": from_state,
                    "to_state": to_state,
                    "resource_prefix": _state_resource_prefix(from_state),
                    "reachable_states": sorted(reachable),
                    "description": (
                        f"No path from {from_state} to {to_state}; "
                        "disconnected lifecycle chain (DFS reachability proof)."
                    ),
                }
            )
    return sorted(gaps, key=lambda item: (item["from_state"], item["to_state"]))


def _type_flow_shadowbridges(nodes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Flag intent nodes whose AST dataflow shows source→sink punctures."""
    bridges: list[dict[str, Any]] = []
    for node in nodes:
        dataflow = node.get("dataflow")
        if not isinstance(dataflow, Mapping):
            continue
        punctures = dataflow.get("dataflow_punctures", [])
        if not punctures:
            continue
        bridges.append(
            {
                "agent_intent": str(node["agent_intent"]),
                "resource_cluster": node.get("resource_cluster"),
                "detection": "type_flow_taint",
                "taint_sources": list(dataflow.get("taint_sources", [])),
                "mutation_sinks": list(dataflow.get("mutation_sinks", [])),
                "dataflow_punctures": list(punctures),
                "is_shadowbridge": True,
                "description": punctures[0].get("description", "Data-flow puncture detected."),
            }
        )
    return sorted(bridges, key=lambda item: str(item["agent_intent"]))


def _merge_shadowbridges(
    type_flow: Sequence[Mapping[str, Any]],
    symmetry: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for bridge in (*type_flow, *symmetry):
        intent = str(bridge.get("agent_intent", ""))
        if not intent:
            continue
        existing = merged.get(intent)
        if existing is None:
            merged[intent] = dict(bridge)
            continue
        existing["is_shadowbridge"] = True
        if bridge.get("detection") == "type_flow_taint":
            existing["type_flow"] = dict(bridge)
        else:
            existing["symmetry"] = dict(bridge)
    return [merged[key] for key in sorted(merged)]
