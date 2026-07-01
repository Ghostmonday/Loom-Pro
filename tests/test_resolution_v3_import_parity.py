"""Import-path parity tests for resolution v3.

Verifies that aoc_cli.resolution_v3 (package path) and
loom_resolution_engine_v3 (compatibility shim) expose the same public API
and produce identical results for equivalent constraint graphs.
"""

import aoc_cli.resolution_v3 as pkg

import loom_resolution_engine_v3 as shim

# ── Public API surface ──────────────────────────────────────────────────────

EXPECTED_PUBLIC_NAMES = {
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
}

# Fields returned by resolve() that must compare identically
COMPARISON_FIELDS = [
    "status",
    "steps",
    "psi_trace",
    "valid",
    "stable",
    "diagnostics",
    "final_nodes",
    "final_edges",
    "log",
]


def test_public_api_surfaces() -> None:
    """Both import paths expose every expected public name."""
    for name in EXPECTED_PUBLIC_NAMES:
        assert hasattr(pkg, name), f"aoc_cli.resolution_v3 missing {name}"
        assert hasattr(shim, name), f"loom_resolution_engine_v3 missing {name}"


def test_same_objects_for_core_types() -> None:
    """Core types from both paths are the same object (shim re-exports)."""
    for name in EXPECTED_PUBLIC_NAMES:
        p_obj = getattr(pkg, name)
        s_obj = getattr(shim, name)
        assert p_obj is s_obj, f"{name}: package {id(p_obj)} != shim {id(s_obj)}"


def test_resolve_is_same_function() -> None:
    """resolve is the exact same callable on both paths."""
    assert pkg.resolve is shim.resolve


def test_constraint_graph_is_same_class() -> None:
    """ConstraintGraph is the exact same class on both paths."""
    assert pkg.ConstraintGraph is shim.ConstraintGraph


# ── Graph case helpers ─────────────────────────────────────────────────────


def _compare_results(
    pkg_result: dict,
    shim_result: dict,
    case_name: str,
) -> None:
    """Assert every comparison field is identical between two result dicts."""
    for field in COMPARISON_FIELDS:
        p_val = pkg_result[field]
        s_val = shim_result[field]
        if field == "diagnostics":
            # diagnostics may differ in list ordering; compare as sorted sets
            assert sorted(p_val) == sorted(s_val), f"[{case_name}] diagnostics differ:\n  pkg: {p_val}\n  shim: {s_val}"
        elif field == "log":
            # logs may differ in ordering or minor whitespace; compare string containment
            p_str = "\n".join(p_val)
            s_str = "\n".join(s_val)
            assert p_str == s_str, f"[{case_name}] logs differ:\n  pkg: {p_val}\n  shim: {s_val}"
        else:
            assert p_val == s_val, f"[{case_name}] {field} differs:\n  pkg: {p_val}\n  shim: {s_val}"


def _run_parity(cg_builder, case_name: str) -> None:
    """Build equivalent graphs from both paths, resolve, and compare."""
    cg_pkg = cg_builder(pkg.ConstraintGraph, pkg.Node, pkg.Edge, pkg.Modality, pkg.Status)
    cg_shim = cg_builder(shim.ConstraintGraph, shim.Node, shim.Edge, shim.Modality, shim.Status)

    result_pkg = pkg.resolve(cg_pkg)
    result_shim = shim.resolve(cg_shim)

    _compare_results(result_pkg, result_shim, case_name)


# ── Graph cases ────────────────────────────────────────────────────────────


def test_parity_original_regression() -> None:
    """Original A1/A2/B1/B2 regression from adversarial suite."""

    def build(graph_cls, node_cls, edge_cls, modality, status):
        cg = graph_cls()
        cg.add_node(node_cls("OrderService", status.KNOWN, "service", 1))
        cg.add_node(node_cls("PaymentGateway", status.KNOWN, "service", 1))
        cg.add_edge(edge_cls("OrderService", "PaymentGateway", modality.REQ, "calls"))
        cg.add_edge(edge_cls("OrderService", "AuditLog", modality.REQ, "writes_to"))
        cg.add_edge(edge_cls("PaymentGateway", "OrderService", modality.REQ, "calls_back"))
        cg.add_edge(edge_cls("PaymentGateway", "OrderService", modality.FORBID, "calls_back"))
        cg.add_edge(edge_cls("AuditLog", "OrderService", modality.REQ, "flushes_to"))
        return cg

    _run_parity(build, "original_regression")


def test_parity_weld_manufactures_clash() -> None:
    """Weld introduces a clash between REQ and FORBID."""

    def build(graph_cls, node_cls, edge_cls, modality, status):
        cg = graph_cls()
        for node_id in ["A", "B", "X"]:
            cg.add_node(node_cls(node_id, status.KNOWN, "service", 1))
        cg.add_edge(edge_cls("A", "B", modality.REQ, "cyc"))
        cg.add_edge(edge_cls("B", "A", modality.REQ, "cyc2"))
        cg.add_edge(edge_cls("A", "X", modality.REQ, "uses"))
        cg.add_edge(edge_cls("B", "X", modality.FORBID, "uses"))
        return cg

    _run_parity(build, "weld_manufactures_clash")


def test_parity_missing_source_is_stuck() -> None:
    """Edge to a missing source node causes STUCK status."""

    def build(graph_cls, node_cls, edge_cls, modality, status):
        cg = graph_cls()
        cg.add_node(node_cls("Target", status.KNOWN, "service", 1))
        cg.add_edge(edge_cls("MissingSource", "Target", modality.REQ, "calls"))
        return cg

    _run_parity(build, "missing_source_is_stuck")


def test_parity_edge_target_type_mismatch_is_stuck() -> None:
    """Declared edge labels reject incompatible known target types on both import paths."""

    def build(graph_cls, node_cls, edge_cls, modality, status):
        cg = graph_cls()
        cg.add_node(node_cls("A", status.KNOWN, "service", 1))
        cg.add_node(node_cls("X", status.KNOWN, "log_sink", 1))
        cg.add_edge(edge_cls("A", "X", modality.REQ, "calls"))
        return cg

    _run_parity(build, "edge_target_type_mismatch")


def test_parity_singleton_prohibited_self_loop() -> None:
    """A singleton node with a self-loop REQ edge is still canonical."""

    def build(graph_cls, node_cls, edge_cls, modality, status):
        cg = graph_cls()
        cg.add_node(node_cls("A", status.KNOWN, "service", 1))
        cg.add_edge(edge_cls("A", "A", modality.REQ, "recursive"))
        return cg

    _run_parity(build, "singleton_self_loop")


def test_parity_composite_identifier_collision() -> None:
    """Weld identifier collision produces deduplicated WELD[A|B]#2 node."""

    def build(graph_cls, node_cls, edge_cls, modality, status):
        cg = graph_cls()
        cg.add_node(node_cls("A", status.KNOWN, "service", 1))
        cg.add_node(node_cls("B", status.KNOWN, "service", 1))
        cg.add_node(node_cls("WELD[A|B]", status.KNOWN, "preexisting", 1, root_permitted=True))
        cg.add_edge(edge_cls("A", "B", modality.REQ, "x"))
        cg.add_edge(edge_cls("B", "A", modality.REQ, "y"))
        return cg

    _run_parity(build, "composite_identifier_collision")


def test_parity_urgent_promotion() -> None:
    """URGENT items always pop before NORMAL regardless of push order."""
    pkg_worklist = pkg.Worklist()
    pkg_worklist.push("z", pkg.URGENT)
    pkg_worklist.push("z", pkg.NORMAL)
    pkg_worklist.push("a", pkg.NORMAL)
    assert pkg_worklist.pop() == pkg.Locus.node("z")
    assert pkg_worklist.pop() == pkg.Locus.node("a")

    shim_worklist = shim.Worklist()
    shim_worklist.push("z", shim.URGENT)
    shim_worklist.push("z", shim.NORMAL)
    shim_worklist.push("a", shim.NORMAL)
    assert shim_worklist.pop() == shim.Locus.node("z")
    assert shim_worklist.pop() == shim.Locus.node("a")
