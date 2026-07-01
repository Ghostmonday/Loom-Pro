"""Result payload formatting for resolution v3."""

from __future__ import annotations


def report_payload(cg, status, steps: int, trace, valid=None, stable=None, fault_detail: str | None = None) -> dict:
    # REPORTING IS FAIL-SOFT: diagnostic computation must not hide the original
    # engine result when reporting is invoked from an exception path.
    if valid is None:
        try:
            valid = cg.is_valid()
        except Exception:
            valid = False
    if stable is None:
        stable = False

    try:
        diagnostics = cg.validation_errors()
    except Exception as error:
        diagnostics = [f"diagnostic failure: {type(error).__name__}: {error}"]

    return {
        "status": status,
        "steps": steps,
        "psi_trace": trace,
        "valid": valid,
        "stable": stable,
        "fault_detail": fault_detail,
        # CANONICAL OUTPUT: semantic collections are sorted so equivalent graphs
        # serialize identically regardless of node or edge insertion order.
        "diagnostics": sorted(diagnostics),
        "final_nodes": {
            node_id: (node.status.name, node.type, node.layer, node.root_permitted, node.sink_permitted)
            for node_id, node in sorted(cg.nodes.items())
        },
        "final_edges": sorted((edge.u, edge.v, edge.modality.name, edge.label) for edge in cg.active_edges()),
        # The justification log intentionally preserves actual rewrite order.
        "log": list(cg.log),
    }
