"""Speculative LLM proposals for resolution v3.

Pure data models only; no graph mutation, no engine integration.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

from aoc_cli.resolution_v3.graph import ConstraintGraph
from aoc_cli.resolution_v3.model import Edge, Locus, Node


class ProposalKind(Enum):
    RESOLVE_LATENT_TYPE = "resolve_latent_type"
    DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET = "declare_label_domain_and_resolve_target"


class ProposalDecisionStatus(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ResolutionProposal:
    proposal_id: str
    kind: ProposalKind
    target_id: str
    selected_type: str | None = None
    layer: int | None = None
    label: str | None = None
    label_domain: frozenset[str] = field(default_factory=frozenset)
    scope: frozenset[Locus] = field(default_factory=frozenset)
    source: str = "llm"

    def __post_init__(self) -> None:
        if not isinstance(self.proposal_id, str) or self.proposal_id.strip() == "":
            raise ValueError("ResolutionProposal.proposal_id must be a non-empty string")
        if not isinstance(self.target_id, str) or self.target_id.strip() == "":
            raise ValueError("ResolutionProposal.target_id must be a non-empty string")
        if not isinstance(self.kind, ProposalKind):
            raise TypeError("ResolutionProposal.kind must be a ProposalKind")
        object.__setattr__(self, "label_domain", frozenset(self.label_domain))
        object.__setattr__(self, "scope", frozenset(self.scope))

    def sort_key(self) -> tuple[str, str, str]:
        return (self.kind.name, self.target_id, self.proposal_id)

    def sorted_scope(self) -> tuple[Locus, ...]:
        return tuple(sorted(self.scope, key=lambda locus: locus.sort_key()))


@dataclass(frozen=True)
class ProposalDecision:
    proposal_id: str
    status: ProposalDecisionStatus
    reason: str
    psi_before: tuple[int, int, int, int] | None = None
    psi_after: tuple[int, int, int, int] | None = None
    affected_loci: tuple[Locus, ...] = ()


def canonicalize_proposals(proposals: Iterable[ResolutionProposal]) -> tuple[ResolutionProposal, ...]:
    ordered = sorted(list(proposals), key=lambda proposal: proposal.sort_key())
    seen: set[str] = set()
    for proposal in ordered:
        if proposal.proposal_id in seen:
            raise ValueError(f"duplicate proposal_id: {proposal.proposal_id}")
        seen.add(proposal.proposal_id)
    return tuple(ordered)


def reject_proposal(proposal: ResolutionProposal, reason: str) -> ProposalDecision:
    return ProposalDecision(
        proposal_id=proposal.proposal_id,
        status=ProposalDecisionStatus.REJECTED,
        reason=reason,
    )


def copy_graph_for_proposal(cg: ConstraintGraph) -> ConstraintGraph:
    """Return an isolated graph copy for speculative proposal checks."""
    copied = ConstraintGraph()

    for node_id in sorted(cg.nodes):
        node = cg.nodes[node_id]
        copied.add_node(
            Node(
                id=node.id,
                status=node.status,
                type=node.type,
                layer=node.layer,
                domain=set(node.domain),
                root_permitted=node.root_permitted,
                sink_permitted=node.sink_permitted,
            )
        )

    for edge in cg.edges:
        copied.add_edge(
            Edge(
                u=edge.u,
                v=edge.v,
                modality=edge.modality,
                label=edge.label,
                provenance=edge.provenance,
                active=edge.active,
            )
        )

    copied.log = list(cg.log)
    return copied


__all__ = [
    "ProposalDecision",
    "ProposalDecisionStatus",
    "ProposalKind",
    "ResolutionProposal",
    "canonicalize_proposals",
    "copy_graph_for_proposal",
    "reject_proposal",
]
