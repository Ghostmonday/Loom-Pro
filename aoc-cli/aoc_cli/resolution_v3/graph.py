"""Mutable constraint graph shell for the resolution engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aoc_cli.resolution_v3.model import Edge, Node
from aoc_cli.resolution_v3.watch import WatchIndex

if TYPE_CHECKING:
    from aoc_cli.resolution_v3.engine import Engine


class ConstraintGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        # Edge-array indices are stable handles used by loci and the watch index.
        # Deactivate or rewire edges in place; do not compact this list mid-run.
        self.edges: list[Edge] = []
        self.log: list[str] = []
        self.watch = WatchIndex(self)

    def add_node(self, node: Node) -> None:
        if node.id in self.nodes:
            raise ValueError(f"node id already exists: {node.id}")
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> int:
        index = len(self.edges)
        self.edges.append(edge)
        self.watch.register_edge(index, edge)
        return index

    def active_edges(self) -> list[Edge]:
        return [edge for edge in self.edges if edge.active]

    # These methods are thin graph-facing adapters. Local imports avoid module
    # cycles without duplicating potential, validation, or stability semantics.
    def growth_debt(self) -> int:
        from aoc_cli.resolution_v3.potential import growth_debt

        return growth_debt(self)

    def unresolved_debt(self) -> int:
        from aoc_cli.resolution_v3.potential import unresolved_debt

        return unresolved_debt(self)

    def find_violating_sccs(self) -> list[frozenset[str]]:
        from aoc_cli.resolution_v3.potential import find_violating_sccs

        return find_violating_sccs(self)

    def cyclic_debt(self) -> int:
        from aoc_cli.resolution_v3.potential import cyclic_debt

        return cyclic_debt(self)

    def clash_pairs(self) -> int:
        from aoc_cli.resolution_v3.potential import clash_pairs

        return clash_pairs(self)

    def psi(self) -> tuple[int, int, int, int]:
        from aoc_cli.resolution_v3.potential import psi

        return psi(self)

    def validation_errors(self) -> list[str]:
        from aoc_cli.resolution_v3.validation import validation_errors

        return validation_errors(self)

    def is_valid(self) -> bool:
        from aoc_cli.resolution_v3.validation import is_valid

        return is_valid(self)

    def is_stable(self, engine: Engine) -> bool:
        from aoc_cli.resolution_v3.validation import is_stable

        return is_stable(self, engine)

    def allocate_composite_id(self, members: list[str]) -> str:
        # Members arrive sorted from B2, making the base ID deterministic.
        base = "WELD[" + "|".join(members) + "]"
        candidate = base
        suffix = 2
        while candidate in self.nodes:
            candidate = f"{base}#{suffix}"
            suffix += 1
        return candidate
