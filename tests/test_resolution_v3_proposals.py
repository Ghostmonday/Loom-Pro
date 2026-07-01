"""Proposal data-model tests for resolution v3."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import loom_resolution_engine_v3 as loom


def _proposal(
    proposal_id: str,
    kind: loom.ProposalKind = loom.ProposalKind.RESOLVE_LATENT_TYPE,
    target_id: str = "Target",
    **kwargs,
) -> loom.ResolutionProposal:
    return loom.ResolutionProposal(
        proposal_id=proposal_id,
        kind=kind,
        target_id=target_id,
        **kwargs,
    )


def test_sort_key_is_order_independent() -> None:
    proposals = [
        _proposal("p4", loom.ProposalKind.RESOLVE_LATENT_TYPE, "B"),
        _proposal("p2", loom.ProposalKind.DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET, "A"),
        _proposal("p1", loom.ProposalKind.RESOLVE_LATENT_TYPE, "A"),
        _proposal("p3", loom.ProposalKind.DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET, "B"),
    ]

    assert loom.canonicalize_proposals(proposals) == loom.canonicalize_proposals(list(reversed(proposals)))


def test_canonicalize_orders_by_kind_then_target_then_id() -> None:
    proposals = [
        _proposal("p3", loom.ProposalKind.RESOLVE_LATENT_TYPE, "B"),
        _proposal("p1", loom.ProposalKind.DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET, "B"),
        _proposal("p4", loom.ProposalKind.RESOLVE_LATENT_TYPE, "A"),
        _proposal("p2", loom.ProposalKind.DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET, "A"),
    ]

    ordered_ids = [proposal.proposal_id for proposal in loom.canonicalize_proposals(proposals)]

    assert ordered_ids == ["p2", "p1", "p4", "p3"]


def test_scope_loci_sort_deterministically() -> None:
    loci = [
        loom.Locus.edge(10),
        loom.Locus.node("Beta"),
        loom.Locus.edge(2),
        loom.Locus.node("Alpha"),
    ]
    first = _proposal("p1", scope=frozenset(loci))
    second = _proposal("p2", scope=frozenset(reversed(loci)))

    expected = (
        loom.Locus.node("Alpha"),
        loom.Locus.node("Beta"),
        loom.Locus.edge(10),
        loom.Locus.edge(2),
    )
    assert first.sorted_scope() == expected
    assert second.sorted_scope() == expected


def test_resolution_proposal_is_frozen() -> None:
    proposal = _proposal("p1")

    with pytest.raises(FrozenInstanceError):
        proposal.source = "human"  # type: ignore[misc]


def test_proposal_decision_is_frozen() -> None:
    decision = loom.ProposalDecision(
        proposal_id="p1",
        status=loom.ProposalDecisionStatus.REJECTED,
        reason="not in scope",
    )

    with pytest.raises(FrozenInstanceError):
        decision.reason = "changed"  # type: ignore[misc]


def test_empty_proposal_id_is_rejected_deterministically() -> None:
    errors: list[str] = []
    for _ in range(2):
        with pytest.raises(ValueError) as exc_info:
            _proposal("")
        errors.append(str(exc_info.value))

    assert errors == ["ResolutionProposal.proposal_id must be a non-empty string"] * 2


def test_empty_target_id_is_rejected_deterministically() -> None:
    errors: list[str] = []
    for _ in range(2):
        with pytest.raises(ValueError) as exc_info:
            _proposal("p1", target_id="")
        errors.append(str(exc_info.value))

    assert errors == ["ResolutionProposal.target_id must be a non-empty string"] * 2


def test_invalid_kind_raises_type_error() -> None:
    with pytest.raises(TypeError, match="ResolutionProposal.kind must be a ProposalKind"):
        loom.ResolutionProposal(
            proposal_id="p1",
            kind="not_a_kind",  # type: ignore[arg-type]
            target_id="Target",
        )


def test_canonicalize_rejects_duplicate_proposal_ids() -> None:
    proposals = [
        _proposal("same", loom.ProposalKind.RESOLVE_LATENT_TYPE, "B"),
        _proposal("same", loom.ProposalKind.DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET, "A"),
    ]

    errors: list[str] = []
    for ordering in (proposals, list(reversed(proposals))):
        with pytest.raises(ValueError) as exc_info:
            loom.canonicalize_proposals(ordering)
        errors.append(str(exc_info.value))

    assert errors == ["duplicate proposal_id: same", "duplicate proposal_id: same"]


def test_reject_proposal_produces_expected_decision() -> None:
    proposal = _proposal("p1")

    decision = loom.reject_proposal(proposal, "proposal does not make progress")

    assert decision.proposal_id == proposal.proposal_id
    assert decision.status == loom.ProposalDecisionStatus.REJECTED
    assert decision.reason == "proposal does not make progress"
    assert decision.psi_before is None
    assert decision.psi_after is None
    assert decision.affected_loci == ()


def test_default_source_is_llm() -> None:
    assert _proposal("p1").source == "llm"


def test_optional_fields_default_empty() -> None:
    proposal = _proposal("p1")

    assert proposal.label_domain == frozenset()
    assert proposal.scope == frozenset()
    assert proposal.selected_type is None
    assert proposal.layer is None
    assert proposal.label is None


def test_no_graph_state_mutation() -> None:
    cg = loom.ConstraintGraph()
    before = cg.psi()
    proposal = _proposal("p1")

    loom.canonicalize_proposals([proposal])
    loom.reject_proposal(proposal, "not authorized")

    assert cg.psi() == before


def test_copy_graph_for_proposal_preserves_graph_payload() -> None:
    cg = loom.ConstraintGraph()
    cg.add_node(
        loom.Node(
            "A",
            loom.Status.KNOWN,
            "service",
            1,
            domain={"service", "worker"},
            root_permitted=True,
        )
    )
    cg.add_node(loom.Node("B", loom.Status.LATENT_UNRESOLVED, domain={"log_sink"}))
    cg.add_edge(loom.Edge("A", "B", loom.Modality.REQ, "writes_to", loom.Provenance.INFERRED, active=True))
    cg.add_edge(loom.Edge("B", "A", loom.Modality.FORBID, "calls", active=False))
    cg.log.append("original trace")

    copied = loom.copy_graph_for_proposal(cg)

    assert copied is not cg
    assert copied.nodes == cg.nodes
    assert copied.edges == cg.edges
    assert copied.log == cg.log
    assert copied.psi() == cg.psi()
    assert copied.watch.edges_touching("A") == {0, 1}
    assert copied.watch.edges_touching("B") == {0, 1}


def test_copy_graph_for_proposal_is_isolated_from_original() -> None:
    cg = loom.ConstraintGraph()
    cg.add_node(loom.Node("A", loom.Status.KNOWN, "service", 1, domain={"service"}))
    cg.add_node(loom.Node("B", loom.Status.LATENT_UNRESOLVED, domain={"log_sink"}))
    cg.add_edge(loom.Edge("A", "B", loom.Modality.REQ, "writes_to"))
    cg.log.append("original trace")

    copied = loom.copy_graph_for_proposal(cg)
    copied.nodes["A"].type = "changed"
    copied.nodes["A"].domain.add("mutated")
    copied.edges[0].active = False
    copied.log.append("copy trace")

    assert cg.nodes["A"].type == "service"
    assert cg.nodes["A"].domain == {"service"}
    assert cg.edges[0].active is True
    assert cg.log == ["original trace"]
