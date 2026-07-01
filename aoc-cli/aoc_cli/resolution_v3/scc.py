"""Strongly connected component helpers for resolution v3."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _Frame:
    node_id: str
    neighbors: list[str]
    next_neighbor: int = 0


def tarjan_scc(adj: dict[str, list[str]], all_nodes: list[str]) -> list[frozenset[str]]:
    """Return maximal SCCs in deterministic Tarjan order."""
    # RECURSION SAFETY: this is intentionally iterative. Reintroducing recursive
    # DFS would make valid large graphs depend on Python's recursion limit.
    index_counter = 0
    stack: list[str] = []
    lowlink: dict[str, int] = {}
    index: dict[str, int] = {}
    on_stack: set[str] = set()
    result: list[frozenset[str]] = []

    def push_frame(node_id: str, frames: list[_Frame]) -> None:
        nonlocal index_counter
        index[node_id] = index_counter
        lowlink[node_id] = index_counter
        index_counter += 1
        stack.append(node_id)
        on_stack.add(node_id)
        # DETERMINISM: adjacency order must not inherit edge insertion order.
        frames.append(_Frame(node_id=node_id, neighbors=sorted(adj.get(node_id, []))))

    def emit_component(node_id: str) -> None:
        component: list[str] = []
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node_id:
                break
        result.append(frozenset(component))

    # Canonical root order makes component discovery reproducible.
    for node_id in sorted(all_nodes):
        if node_id not in index:
            frames: list[_Frame] = []
            push_frame(node_id, frames)

            while frames:
                frame = frames[-1]
                if frame.next_neighbor < len(frame.neighbors):
                    neighbor = frame.neighbors[frame.next_neighbor]
                    frame.next_neighbor += 1
                    if neighbor not in index:
                        push_frame(neighbor, frames)
                    elif neighbor in on_stack:
                        lowlink[frame.node_id] = min(lowlink[frame.node_id], index[neighbor])
                    continue

                frames.pop()
                if lowlink[frame.node_id] == index[frame.node_id]:
                    emit_component(frame.node_id)
                if frames:
                    # Propagate the completed child's lowlink into its parent,
                    # mirroring recursive Tarjan after a DFS call returns.
                    parent = frames[-1].node_id
                    lowlink[parent] = min(lowlink[parent], lowlink[frame.node_id])

    return result
