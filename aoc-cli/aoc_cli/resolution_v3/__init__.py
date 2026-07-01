"""Modular Loom constraint resolution engine v3."""

from aoc_cli.resolution_v3.engine import Engine, resolve
from aoc_cli.resolution_v3.graph import ConstraintGraph
from aoc_cli.resolution_v3.model import (
    ACYCLIC_LAYERS,
    Edge,
    EngineStatus,
    Locus,
    LocusKind,
    Modality,
    Node,
    Provenance,
    Status,
)
from aoc_cli.resolution_v3.proposal import (
    ProposalDecision,
    ProposalDecisionStatus,
    ProposalKind,
    ResolutionProposal,
    canonicalize_proposals,
    copy_graph_for_proposal,
    reject_proposal,
)
from aoc_cli.resolution_v3.scc import tarjan_scc
from aoc_cli.resolution_v3.worklist import NORMAL, URGENT, Worklist

__all__ = [
    "ACYCLIC_LAYERS",
    "NORMAL",
    "URGENT",
    "ConstraintGraph",
    "Edge",
    "Engine",
    "EngineStatus",
    "Locus",
    "LocusKind",
    "Modality",
    "Node",
    "ProposalDecision",
    "ProposalDecisionStatus",
    "ProposalKind",
    "Provenance",
    "ResolutionProposal",
    "Status",
    "Worklist",
    "canonicalize_proposals",
    "copy_graph_for_proposal",
    "reject_proposal",
    "resolve",
    "tarjan_scc",
]
