"""Validity and stability predicates for resolution v3."""

from __future__ import annotations

from aoc_cli.resolution_v3.model import LABEL_TYPE_DOMAIN, Locus, Modality, Status


def validation_errors(cg) -> list[str]:
    errors: list[str] = []

    if cg.growth_debt():
        errors.append("one or more required targets do not exist")
    if cg.unresolved_debt():
        errors.append("latent nodes or partial edges remain unresolved")
    if cg.cyclic_debt():
        errors.append("required-edge cycles remain in acyclic layers")
    if cg.clash_pairs():
        errors.append("REQ/FORBID clashes remain")

    for index, edge in enumerate(cg.edges):
        if not edge.active:
            continue
        if edge.u not in cg.nodes:
            errors.append(f"active edge {index} has missing source '{edge.u}'")
        if edge.v not in cg.nodes:
            errors.append(f"active edge {index} has missing target '{edge.v}'")
        if edge.u == edge.v and edge.modality == Modality.FORBID:
            errors.append(f"internal FORBID constraint remains on '{edge.u}' via edge {index} '{edge.label}'")

    rejected = sorted(node.id for node in cg.nodes.values() if node.status == Status.REJECTED)
    if rejected:
        errors.append(f"rejected nodes remain in topology: {rejected}")

    for node_id, node in sorted(cg.nodes.items()):
        if node.status == Status.KNOWN:
            if node.type is None:
                errors.append(f"known node '{node_id}' lacks resolved type")
            if node.layer is None:
                errors.append(f"known node '{node_id}' lacks resolved layer")
        if node.status == Status.LATENT_UNRESOLVED and not node.domain:
            undeclared = sorted(
                {
                    edge.label
                    for edge in cg.active_edges()
                    if edge.modality == Modality.REQ and edge.v == node_id and edge.label not in LABEL_TYPE_DOMAIN
                }
            )
            if undeclared:
                errors.append(f"target '{node_id}' uses undeclared schema labels: {undeclared}")
            else:
                errors.append(f"target '{node_id}' has contradictory required type domains")

    for index, edge in enumerate(cg.edges):
        if not edge.active or edge.label not in LABEL_TYPE_DOMAIN or edge.v not in cg.nodes:
            continue
        target = cg.nodes[edge.v]
        if target.status == Status.KNOWN and target.type not in LABEL_TYPE_DOMAIN[edge.label]:
            errors.append(
                f"active edge {index} label '{edge.label}' targets '{edge.v}' with incompatible type '{target.type}'"
            )

    degree: dict[str, int] = {node_id: 0 for node_id in cg.nodes}
    for edge in cg.active_edges():
        if edge.u in degree:
            degree[edge.u] += 1
        if edge.v in degree and edge.v != edge.u:
            degree[edge.v] += 1

    for node_id, node_degree in sorted(degree.items()):
        node = cg.nodes[node_id]
        if node_degree == 0 and not node.root_permitted and not node.sink_permitted:
            errors.append(f"orphan node '{node_id}' lacks ROOT_PERMITTED/SINK_PERMITTED")

    return errors


def is_valid(cg) -> bool:
    return not validation_errors(cg)


def is_stable(cg, engine) -> bool:
    loci = [Locus.node(node_id) for node_id in sorted(cg.nodes)]
    loci.extend(Locus.edge(index) for index in range(len(cg.edges)))
    for locus in loci:
        if engine.applicable_rule(locus) is not None:
            return False
    return not cg.find_violating_sccs()
