"""Deterministic resolution rules A1, A2/D1, B1, and B2."""

from __future__ import annotations

from dataclasses import dataclass

from aoc_cli.resolution_v3.model import LABEL_TYPE_DOMAIN, Locus, LocusKind, Modality, Node, Status
from aoc_cli.resolution_v3.worklist import NORMAL, URGENT


@dataclass(frozen=True)
class _TargetDomain:
    domain: set[str]
    undeclared_labels: tuple[str, ...]


# PURE MATCHER: check_* functions are dry applicability queries used by stability.
def check_a1(cg, locus: Locus):
    if locus.kind != LocusKind.EDGE:
        return None
    edge = cg.edges[int(locus.identity)]
    if edge.active and edge.modality == Modality.REQ and edge.v not in cg.nodes:
        return ("A1", edge)
    return None


def check_a2_d1(cg, locus: Locus):
    if locus.kind != LocusKind.NODE:
        return None
    node = cg.nodes.get(str(locus.identity))
    if node and node.status == Status.LATENT_UNRESOLVED and len(node.domain) == 1:
        return ("A2_D1", node)
    return None


def check_b1(cg, locus: Locus):
    if locus.kind != LocusKind.EDGE:
        return None
    index = int(locus.identity)
    required = cg.edges[index]
    if not (required.active and required.modality == Modality.REQ):
        return None

    # Stable edge-index ordering prevents set iteration from selecting the clash.
    candidates = cg.watch.edges_touching(required.u) & cg.watch.edges_touching(required.v)
    for candidate_index in sorted(candidates):
        forbidden = cg.edges[candidate_index]
        if (
            forbidden.active
            and forbidden.modality == Modality.FORBID
            and forbidden.u == required.u
            and forbidden.v == required.v
            and forbidden.label == required.label
        ):
            return ("B1", (required, forbidden))
    return None


def applicable_rule(cg, locus: Locus):
    # Rule priority is semantic: A1, then singleton instantiation, then B1.
    return check_a1(cg, locus) or check_a2_d1(cg, locus) or check_b1(cg, locus)


def apply_a1(cg, worklist, edge) -> None:
    # Aggregate atomically: a separate refinement rewrite would not lower Psi.
    target_domain = _aggregate_target_domain(cg, edge.v)

    # Always materialize the target so growth debt falls, including STUCK cases.
    cg.add_node(Node(id=edge.v, status=Status.LATENT_UNRESOLVED, domain=target_domain.domain))

    if target_domain.undeclared_labels:
        domain_detail = f"undeclared labels={list(target_domain.undeclared_labels)}"
    elif target_domain.domain:
        domain_detail = f"intersected domain={sorted(target_domain.domain)}"
    else:
        domain_detail = "contradictory declared domains"

    cg.log.append(
        f"[A1] introduced latent node '{edge.v}' (required by {edge.u} -[{edge.label}]-> {edge.v}); {domain_detail}"
    )
    _requeue_target_closure(cg, worklist, edge.v)


def apply_a2_d1(cg, worklist, node) -> None:
    # Only a singleton domain may become KNOWN; ambiguity is never guessed away.
    node.type = next(iter(node.domain))
    node.layer = 1
    node.status = Status.KNOWN
    cg.log.append(f"[A2->D1] instantiated '{node.id}' as type={node.type}, layer={node.layer}")

    for edge_index in sorted(cg.watch.edges_touching(node.id)):
        edge = cg.edges[edge_index]
        worklist.push(Locus.edge(edge_index), NORMAL)
        worklist.push(Locus.node(edge.u), NORMAL)
        worklist.push(Locus.node(edge.v), NORMAL)


def apply_b1(cg, worklist, required, forbidden) -> None:
    del forbidden
    # Priority rule 5: FORBID remains active; deactivate only the matching REQ.
    required.active = False
    cg.log.append(
        f"[B1] clash on {required.u}->{required.v} '{required.label}' "
        "REQ vs FORBID; priority rule 5: FORBID wins -> REQ edge deactivated"
    )
    worklist.push(Locus.node(required.u), NORMAL)
    worklist.push(Locus.node(required.v), NORMAL)


def apply_b2(cg, worklist) -> bool:
    # B2 consumes only SCCs already proven to violate an acyclic layer.
    violating = cg.find_violating_sccs()
    if not violating:
        return False

    # One canonical SCC per rewrite keeps strict descent independently checkable.
    scc = violating[0]
    members = sorted(scc)

    if len(members) == 1:
        _remove_singleton_self_loop(cg, worklist, members[0])
        return True

    composite_id = cg.allocate_composite_id(members)
    composite_layer = min(cg.nodes[member].layer for member in members if cg.nodes[member].layer is not None)

    external_in_req = any(
        edge.active and edge.modality == Modality.REQ and edge.v in scc and edge.u not in scc for edge in cg.edges
    )
    external_out_req = any(
        edge.active and edge.modality == Modality.REQ and edge.u in scc and edge.v not in scc for edge in cg.edges
    )
    # Preserve member authority flags across the weld.
    inherited_root = any(cg.nodes[member].root_permitted for member in members)
    inherited_sink = any(cg.nodes[member].sink_permitted for member in members)

    touched_indices: set[int] = set()
    for index, edge in enumerate(cg.edges):
        changed = False
        if edge.u in scc:
            edge.u = composite_id
            changed = True
        if edge.v in scc:
            edge.v = composite_id
            changed = True
        if changed:
            touched_indices.add(index)

    # Absorb internal REQ only. PARTIAL and FORBID obligations remain visible.
    for index in touched_indices:
        edge = cg.edges[index]
        if edge.active and edge.u == composite_id and edge.v == composite_id and edge.modality == Modality.REQ:
            edge.active = False

    for member in members:
        del cg.nodes[member]

    cg.add_node(
        Node(
            id=composite_id,
            status=Status.KNOWN,
            type="composite",
            layer=composite_layer,
            root_permitted=inherited_root or not external_in_req,
            sink_permitted=inherited_sink or not external_out_req,
        )
    )

    # Endpoint rewrites invalidate the watch index before affected loci are used.
    cg.watch.rebuild()
    cg.log.append(f"[B2] welded SCC {members} (size={len(members)}) into '{composite_id}'")

    worklist.push(Locus.node(composite_id), URGENT)
    for index in sorted(touched_indices):
        if cg.edges[index].active:
            worklist.push(Locus.edge(index), URGENT)
    return True


def _remove_singleton_self_loop(cg, worklist, node_id: str) -> None:
    deactivated: list[int] = []
    for index, edge in enumerate(cg.edges):
        if edge.active and edge.modality == Modality.REQ and edge.u == node_id and edge.v == node_id:
            edge.active = False
            deactivated.append(index)

    if not deactivated:
        raise RuntimeError(f"violating singleton SCC '{node_id}' had no active REQ self-loop")

    node = cg.nodes[node_id]
    node.root_permitted = True
    node.sink_permitted = True
    cg.log.append(
        f"[B2-self] removed prohibited REQ self-loop(s) {deactivated} "
        f"from '{node_id}'; node preserved and tagged ROOT/SINK_PERMITTED"
    )
    worklist.push(Locus.node(node_id), URGENT)


def _aggregate_target_domain(cg, target_id: str) -> _TargetDomain:
    # Labels constrain target v. Only active incoming REQ edges participate.
    incoming = sorted(
        (
            (edge.u, edge.v, edge.label, index, edge)
            for index, edge in enumerate(cg.edges)
            if edge.active and edge.modality == Modality.REQ and edge.v == target_id
        ),
        # Semantic fields lead; edge index is only the deterministic tie-breaker.
        key=lambda item: (item[0], item[1], item[2], item[3]),
    )

    # Undeclared schema is distinct from contradictory declared domains.
    undeclared = sorted({edge.label for *_, edge in incoming if edge.label not in LABEL_TYPE_DOMAIN})
    if undeclared:
        return _TargetDomain(domain=set(), undeclared_labels=tuple(undeclared))

    domain: set[str] | None = None
    for *_, edge in incoming:
        edge_domain = set(LABEL_TYPE_DOMAIN[edge.label])
        domain = edge_domain if domain is None else domain & edge_domain

    return _TargetDomain(domain=domain or set(), undeclared_labels=())


def _requeue_target_closure(cg, worklist, target_id: str) -> None:
    # Minimum closure: target enables A2/D1; touching edges may expose B1.
    worklist.push(Locus.node(target_id), NORMAL)
    for index, edge in enumerate(cg.edges):
        if edge.active and (edge.u == target_id or edge.v == target_id):
            worklist.push(Locus.edge(index), NORMAL)
