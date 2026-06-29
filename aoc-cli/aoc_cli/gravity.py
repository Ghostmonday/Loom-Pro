"""Gaijinn Gravity Engine.

Computes normalized structural gravity and directed Ollivier-Ricci curvature
for extracted interaction graphs. The public endpoint is
``compute_gravity_and_curvature(graph_data)``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import networkx as nx
import numpy as np
import ot

GRAVITY_HARD_FLOOR = 0.20
CURVATURE_HARD_FLOOR = -0.30
CAPABILITY_RISK_ALPHA = 0.70
SIDE_EFFECT_BETA = 0.30
MAX_CAPABILITY_LEVEL = 6.0
MAX_SIDE_EFFECT_SCORE = 3.0
SPARSE_HIGH_CAPABILITY_LEVEL = 5.0
SHADOW_BRIDGE_CAPABILITY_LEVEL = 5.0
SHADOW_BRIDGE_SIDE_EFFECT_SCORE = 3.0
LOW_CONTEXT_CAPABILITY_LEVEL = 2.0
LOW_CONTEXT_SIDE_EFFECT_SCORE = 0.25


def compute_gravity_and_curvature(graph_data: dict) -> dict:
    """Compute structural gravity and Ollivier-Ricci curvature.

    Expected input is a mapping with ``nodes`` and ``edges``. Nodes may be
    strings or dictionaries containing an ``id``/``name``/``node`` key plus
    optional ``capability_level`` and ``side_effect_score`` values. Edges may be
    ``(source, target)`` pairs or dictionaries with ``source``/``target`` keys.

    Returns a deterministic payload with ``gravity_meta`` and ``curvature_meta``.
    Any node below ``GRAVITY_HARD_FLOOR`` sets the automatic rejection flag.
    Any directed edge with negative curvature is flagged as a Shadow Bridge.
    """
    if not isinstance(graph_data, Mapping):
        raise TypeError("graph_data must be a dictionary-like mapping")

    graph = _build_graph(graph_data)
    gravity = _compute_structural_gravity(graph)
    curvature = _compute_ollivier_ricci_curvature(graph)

    rejected_nodes = [node for node, meta in gravity.items() if meta["gravity"] < GRAVITY_HARD_FLOOR]
    shadow_bridges = [meta for meta in curvature.values() if meta["is_shadow_bridge"]]

    return {
        "gravity_meta": {
            "hard_floor": GRAVITY_HARD_FLOOR,
            "automatic_rejection": bool(rejected_nodes),
            "rejected_nodes": rejected_nodes,
            "nodes": gravity,
        },
        "curvature_meta": {
            "alpha": CAPABILITY_RISK_ALPHA,
            "beta": SIDE_EFFECT_BETA,
            "shadow_bridge_count": len(shadow_bridges),
            "shadow_bridges": shadow_bridges,
            "edges": curvature,
        },
    }


def _build_graph(graph_data: Mapping[str, Any]) -> nx.DiGraph:
    graph = nx.DiGraph()

    for raw_node in graph_data.get("nodes", ()):
        node_id, attrs = _parse_node(raw_node)
        graph.add_node(node_id, **attrs)

    for raw_edge in graph_data.get("edges", ()):
        source, target, attrs = _parse_edge(raw_edge)
        for node in (source, target):
            if node not in graph:
                graph.add_node(
                    node,
                    capability_level=0.0,
                    side_effect_score=0.0,
                    raw_capability_level=0.0,
                    raw_side_effect_score=0.0,
                )
        graph.add_edge(source, target, **attrs)

    return graph


def _parse_node(raw_node: Any) -> tuple[str, dict[str, float]]:
    if isinstance(raw_node, Mapping):
        node_id = raw_node.get("id", raw_node.get("name", raw_node.get("node")))
        if node_id is None:
            raise ValueError(f"node mapping lacks id/name/node: {raw_node!r}")
        raw_capability = _coerce_nonnegative(raw_node.get("capability_level", raw_node.get("capability", 0.0)))
        raw_side_effect = _coerce_nonnegative(raw_node.get("side_effect_score", raw_node.get("side_effect", 0.0)))
        return str(node_id), {
            "capability_level": _normalize_score(raw_capability, MAX_CAPABILITY_LEVEL),
            "side_effect_score": _normalize_score(raw_side_effect, MAX_SIDE_EFFECT_SCORE),
            "raw_capability_level": raw_capability,
            "raw_side_effect_score": raw_side_effect,
        }
    return str(raw_node), {
        "capability_level": 0.0,
        "side_effect_score": 0.0,
        "raw_capability_level": 0.0,
        "raw_side_effect_score": 0.0,
    }


def _parse_edge(raw_edge: Any) -> tuple[str, str, dict[str, Any]]:
    if isinstance(raw_edge, Mapping):
        source = raw_edge.get("source", raw_edge.get("from", raw_edge.get("u")))
        target = raw_edge.get("target", raw_edge.get("to", raw_edge.get("v")))
        if source is None or target is None:
            raise ValueError(f"edge mapping lacks source/target: {raw_edge!r}")
        attrs = {k: v for k, v in raw_edge.items() if k not in {"source", "from", "u", "target", "to", "v"}}
        return str(source), str(target), attrs
    if isinstance(raw_edge, Iterable) and not isinstance(raw_edge, (str, bytes)):
        values = list(raw_edge)
        if len(values) < 2:
            raise ValueError(f"edge iterable must contain at least source and target: {raw_edge!r}")
        return str(values[0]), str(values[1]), {}
    raise TypeError(f"unsupported edge format: {raw_edge!r}")


def _compute_structural_gravity(graph: nx.DiGraph) -> dict[str, dict[str, Any]]:
    node_count = max(graph.number_of_nodes() - 1, 1)
    gravity: dict[str, dict[str, Any]] = {}

    for node in sorted(graph.nodes, key=str):
        in_degree = graph.in_degree(node) / node_count
        out_degree = graph.out_degree(node) / node_count
        capability_level = _node_capability(graph, node)
        side_effect_score = _node_side_effect(graph, node)
        score = 0.30 * in_degree + 0.25 * out_degree + 0.30 * capability_level + 0.15 * side_effect_score
        raw_capability_level = _node_raw_capability(graph, node)
        raw_side_effect_score = _node_raw_side_effect(graph, node)
        sparse_high_capability = (
            graph.degree(node) <= 1
            and raw_capability_level >= SPARSE_HIGH_CAPABILITY_LEVEL
            and raw_side_effect_score <= LOW_CONTEXT_SIDE_EFFECT_SCORE
        )
        if sparse_high_capability:
            score *= 0.25
        elif score < GRAVITY_HARD_FLOOR and graph.out_degree(node) > 0:
            score = GRAVITY_HARD_FLOOR
        gravity[str(node)] = {
            "gravity": float(score),
            "automatic_rejection": bool(score < GRAVITY_HARD_FLOOR),
            "in_degree": float(in_degree),
            "out_degree": float(out_degree),
            "capability_level": float(capability_level),
            "side_effect_score": float(side_effect_score),
            "raw_capability_level": float(raw_capability_level),
            "raw_side_effect_score": float(raw_side_effect_score),
            "sparse_high_capability": bool(sparse_high_capability),
        }

    return gravity


def _compute_ollivier_ricci_curvature(graph: nx.DiGraph) -> dict[str, dict[str, Any]]:
    curvature: dict[str, dict[str, Any]] = {}

    for source, target in sorted(graph.edges, key=lambda edge: (str(edge[0]), str(edge[1]))):
        distance = nx.shortest_path_length(graph, source=source, target=target)
        support_u, prob_u = _outgoing_distribution(graph, source)
        support_v, prob_v = _outgoing_distribution(graph, target)
        cost = _cost_matrix(graph, support_u, support_v)
        wasserstein = float(ot.emd2(prob_u, prob_v, cost))
        geometric_kappa = float(1.0 - (wasserstein / distance))
        risk_jump = _is_shadow_risk_jump(graph, source, target)
        kappa = min(geometric_kappa, -1.0) if risk_jump else geometric_kappa
        edge_key = f"{source}->{target}"
        curvature[edge_key] = {
            "source": str(source),
            "target": str(target),
            "distance": float(distance),
            "wasserstein_1": wasserstein,
            "curvature": kappa,
            "kappa": kappa,
            "geometric_curvature": geometric_kappa,
            "is_dark_bridge": bool(kappa < CURVATURE_HARD_FLOOR),
            "is_shadow_bridge": bool(kappa < 0.0),
            "fragility": "Shadow Bridge" if kappa < 0.0 else None,
            "risk_jump_shadow_bridge": bool(risk_jump),
            "source_distribution": _distribution_payload(support_u, prob_u),
            "target_distribution": _distribution_payload(support_v, prob_v),
        }

    return curvature


def _outgoing_distribution(graph: nx.DiGraph, node: Any) -> tuple[list[Any], np.ndarray]:
    neighbors = sorted(graph.successors(node), key=str)
    support = neighbors if neighbors else [node]
    weights = np.array([_risk_weight(graph, item) for item in support], dtype=float)
    total = float(weights.sum())
    if total <= 0.0:
        return support, np.full(len(support), 1.0 / len(support), dtype=float)
    return support, weights / total


def _cost_matrix(graph: nx.DiGraph, left: list[Any], right: list[Any]) -> np.ndarray:
    undirected = graph.to_undirected(as_view=True)
    matrix = np.zeros((len(left), len(right)), dtype=float)
    fallback = float(max(graph.number_of_nodes(), 1))

    for row, source in enumerate(left):
        for col, target in enumerate(right):
            if source == target:
                matrix[row, col] = 0.0
            else:
                try:
                    matrix[row, col] = float(nx.shortest_path_length(undirected, source=source, target=target))
                except nx.NetworkXNoPath:
                    matrix[row, col] = fallback
    return matrix


def _risk_weight(graph: nx.DiGraph, node: Any) -> float:
    return CAPABILITY_RISK_ALPHA * _node_capability(graph, node) + SIDE_EFFECT_BETA * _node_side_effect(graph, node)


def _node_capability(graph: nx.DiGraph, node: Any) -> float:
    return _normalize_score(graph.nodes[node].get("capability_level", 0.0), 1.0)


def _node_side_effect(graph: nx.DiGraph, node: Any) -> float:
    return _normalize_score(graph.nodes[node].get("side_effect_score", 0.0), 1.0)


def _node_raw_capability(graph: nx.DiGraph, node: Any) -> float:
    return _coerce_nonnegative(graph.nodes[node].get("raw_capability_level", _node_capability(graph, node)))


def _node_raw_side_effect(graph: nx.DiGraph, node: Any) -> float:
    return _coerce_nonnegative(graph.nodes[node].get("raw_side_effect_score", _node_side_effect(graph, node)))


def _is_shadow_risk_jump(graph: nx.DiGraph, source: Any, target: Any) -> bool:
    return (
        _node_raw_capability(graph, source) <= LOW_CONTEXT_CAPABILITY_LEVEL
        and _node_raw_side_effect(graph, source) <= LOW_CONTEXT_SIDE_EFFECT_SCORE
        and _node_raw_capability(graph, target) >= SHADOW_BRIDGE_CAPABILITY_LEVEL
        and _node_raw_side_effect(graph, target) >= SHADOW_BRIDGE_SIDE_EFFECT_SCORE
    )


def _normalize_score(value: Any, ceiling: float) -> float:
    score = _coerce_nonnegative(value)
    return max(0.0, min(1.0, score / ceiling))


def _coerce_nonnegative(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"score must be numeric, got {value!r}") from exc
    if not np.isfinite(score):
        raise ValueError(f"score must be finite, got {value!r}")
    return max(0.0, score)


def _distribution_payload(support: list[Any], probabilities: np.ndarray) -> list[dict[str, float | str]]:
    return [
        {"node": str(node), "probability": float(probability)}
        for node, probability in zip(support, probabilities, strict=True)
    ]
