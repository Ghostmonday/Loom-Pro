"""Termination ranking for the Loom constraint resolution engine v3."""

from __future__ import annotations

from aoc_cli.resolution_v3.model import ACYCLIC_LAYERS, Modality, Status
from aoc_cli.resolution_v3.scc import tarjan_scc


# Psi component 1: every active REQ whose target is absent contributes debt.
def growth_debt(cg) -> int:
    return sum(1 for edge in cg.active_edges() if edge.modality == Modality.REQ and edge.v not in cg.nodes)


# Psi component 2: latent nodes and active PARTIAL obligations remain unresolved.
def unresolved_debt(cg) -> int:
    latent = sum(1 for node in cg.nodes.values() if node.status == Status.LATENT_UNRESOLVED)
    partial = sum(1 for edge in cg.active_edges() if edge.modality == Modality.PARTIAL)
    return latent + partial


def find_violating_sccs(cg) -> list[frozenset[str]]:
    violating: list[frozenset[str]] = []

    for layer in sorted(ACYCLIC_LAYERS):
        # LAYER SEMANTICS: detect cycles in the directed subgraph induced by one
        # acyclic layer. Cross-layer traversal alone is never a layer violation.
        layer_nodes = sorted(
            node_id for node_id, node in cg.nodes.items() if node.status == Status.KNOWN and node.layer == layer
        )
        layer_node_set = set(layer_nodes)
        adj: dict[str, list[str]] = {}

        for edge in cg.active_edges():
            if edge.modality != Modality.REQ:
                continue
            if edge.u not in layer_node_set or edge.v not in layer_node_set:
                continue
            adj.setdefault(edge.u, []).append(edge.v)

        for scc in tarjan_scc(adj, layer_nodes):
            # Tarjan returns singleton SCCs for ordinary nodes; only a REQ
            # self-loop makes a singleton an actual directed cycle.
            has_self_loop = any(
                edge.active and edge.modality == Modality.REQ and edge.u == edge.v and edge.u in scc
                for edge in cg.edges
            )
            if len(scc) == 1 and not has_self_loop:
                continue

            violating.append(scc)

    # Canonical SCC ordering ensures B2 always chooses the same first weld.
    return sorted(violating, key=lambda component: tuple(sorted(component)))


def cyclic_debt(cg) -> int:
    """Quadratic cyclic mass over acyclicity-violating SCCs."""
    return sum(len(scc) ** 2 for scc in find_violating_sccs(cg))


def clash_pairs(cg) -> int:
    required_counts: dict[tuple[str, str, str], int] = {}
    forbidden_counts: dict[tuple[str, str, str], int] = {}

    for edge in cg.active_edges():
        key = (edge.u, edge.v, edge.label)
        if edge.modality == Modality.REQ:
            required_counts[key] = required_counts.get(key, 0) + 1
        elif edge.modality == Modality.FORBID:
            forbidden_counts[key] = forbidden_counts.get(key, 0) + 1

    # Multiplicity matters: each matching REQ/FORBID pair is independent debt.
    return sum(required_count * forbidden_counts.get(key, 0) for key, required_count in required_counts.items())


def psi(cg) -> tuple[int, int, int, int]:
    # TERMINATION CONTRACT: tuple order is part of the proof. Never reorder,
    # weaken, or append components merely to make a new rewrite pass descent.
    return (growth_debt(cg), unresolved_debt(cg), cyclic_debt(cg), clash_pairs(cg))
