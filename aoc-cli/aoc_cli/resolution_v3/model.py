"""Core data types for the Loom constraint resolution engine v3."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class Modality(Enum):
    REQ = auto()
    FORBID = auto()
    PARTIAL = auto()


class Status(Enum):
    KNOWN = auto()
    LATENT_UNRESOLVED = auto()
    REJECTED = auto()


class Provenance(Enum):
    EXPLICIT = auto()
    INFERRED = auto()
    LLM_PROPOSED = auto()


class EngineStatus(Enum):
    CANONICAL = auto()
    STUCK = auto()
    ENGINE_FAULT = auto()


class LocusKind(Enum):
    NODE = auto()
    EDGE = auto()


@dataclass(frozen=True)
class Locus:
    # Typed loci keep node identifiers such as "edge:0" distinct from edge
    # indices. Never replace this with string-prefix parsing.
    kind: LocusKind
    identity: str | int

    @staticmethod
    def node(node_id: str) -> Locus:
        return Locus(LocusKind.NODE, node_id)

    @staticmethod
    def edge(index: int) -> Locus:
        return Locus(LocusKind.EDGE, index)

    def sort_key(self) -> tuple[int, str]:
        # Nodes sort before edges; identity is stringified only for ordering.
        kind_order = 0 if self.kind == LocusKind.NODE else 1
        return (kind_order, str(self.identity))


@dataclass
class Node:
    id: str
    status: Status
    type: str | None = None
    layer: int | None = None
    domain: set[str] = field(default_factory=set)
    root_permitted: bool = False
    sink_permitted: bool = False


@dataclass
class Edge:
    u: str
    v: str
    modality: Modality
    label: str
    provenance: Provenance = Provenance.EXPLICIT
    active: bool = True


# SCHEMA AUTHORITY: each declared edge label constrains the type of target v.
# Unknown labels remain explicit schema errors rather than unconstrained edges.
LABEL_TYPE_DOMAIN: dict[str, set[str]] = {
    "writes_to": {"log_sink"},
    "calls": {"service"},
    "calls_back": {"service"},
    "flushes_to": {"service", "log_sink"},
}

# Cycles are forbidden only inside the induced directed subgraph of these layers.
ACYCLIC_LAYERS = {1}
