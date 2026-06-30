"""Versioned deterministic worklist for resolution v3."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from aoc_cli.resolution_v3.model import Locus

URGENT = 0
NORMAL = 1


@dataclass(order=True)
class _Entry:
    priority: int
    sort_key: tuple[int, str]
    version: int = field(compare=False)
    locus: Locus = field(compare=False)


class Worklist:
    """Priority worklist with lazy deletion and non-downgradable promotion."""

    def __init__(self) -> None:
        self._heap: list[_Entry] = []
        self._current: dict[Locus, tuple[int, int]] = {}

    def push(self, locus: Locus | str, priority: int = NORMAL) -> None:
        # Compatibility accepts a plain string as a node locus only. Edge loci
        # must remain typed so node IDs cannot collide with encoded edge names.
        locus = self._normalize(locus)
        current = self._current.get(locus)
        if current is None:
            effective_priority = priority
            version = 1
        else:
            current_priority, current_version = current
            # Promotion is monotone: pushing NORMAL can never downgrade URGENT.
            effective_priority = min(current_priority, priority)
            version = current_version + 1

        self._current[locus] = (effective_priority, version)
        heapq.heappush(
            self._heap,
            _Entry(priority=effective_priority, sort_key=locus.sort_key(), version=version, locus=locus),
        )

    def pop(self) -> Locus | None:
        while self._heap:
            entry = heapq.heappop(self._heap)
            current = self._current.get(entry.locus)
            # Lazy deletion: superseded heap entries remain until encountered.
            if current == (entry.priority, entry.version):
                del self._current[entry.locus]
                return entry.locus
        return None

    def __bool__(self) -> bool:
        return bool(self._current)

    @staticmethod
    def _normalize(locus: Locus | str) -> Locus:
        if isinstance(locus, Locus):
            return locus
        return Locus.node(locus)
