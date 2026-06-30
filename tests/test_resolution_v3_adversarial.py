"""Asserted adversarial regression suite for the Loom resolution engine v3."""

import sys

from loom_resolution_engine_v3 import (
    ACYCLIC_LAYERS,
    NORMAL,
    URGENT,
    ConstraintGraph,
    Edge,
    EngineStatus,
    Locus,
    Modality,
    Node,
    Status,
    Worklist,
    resolve,
)


def assert_strict_descent(result: dict) -> None:
    values = [psi for _, psi in result["psi_trace"]]
    assert all(after < before for before, after in zip(values, values[1:])), values


def assert_terminal(
    result: dict,
    status: EngineStatus,
    *,
    valid: bool,
    stable: bool,
    steps: int | None = None,
) -> None:
    assert result["status"] == status, result
    assert result["valid"] is valid, result
    assert result["stable"] is stable, result
    if steps is not None:
        assert result["steps"] == steps, result
    if status != EngineStatus.ENGINE_FAULT:
        assert_strict_descent(result)


def test_original_regression() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("OrderService", Status.KNOWN, "service", 1))
    cg.add_node(Node("PaymentGateway", Status.KNOWN, "service", 1))
    cg.add_edge(Edge("OrderService", "PaymentGateway", Modality.REQ, "calls"))
    cg.add_edge(Edge("OrderService", "AuditLog", Modality.REQ, "writes_to"))
    cg.add_edge(Edge("PaymentGateway", "OrderService", Modality.REQ, "calls_back"))
    cg.add_edge(Edge("PaymentGateway", "OrderService", Modality.FORBID, "calls_back"))
    cg.add_edge(Edge("AuditLog", "OrderService", Modality.REQ, "flushes_to"))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=4)
    assert result["psi_trace"][-1][1] == (0, 0, 0, 0)
    assert any("incompatible type 'composite'" in error for error in result["diagnostics"])


def test_two_disjoint_cycles() -> None:
    cg = ConstraintGraph()
    for node_id in ["A", "B", "C", "D"]:
        cg.add_node(Node(node_id, Status.KNOWN, "service", 1))
    cg.add_edge(Edge("A", "B", Modality.REQ, "x"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "y"))
    cg.add_edge(Edge("C", "D", Modality.REQ, "x"))
    cg.add_edge(Edge("D", "C", Modality.REQ, "y"))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=2)
    assert [psi for _, psi in result["psi_trace"]] == [
        (0, 0, 8, 0),
        (0, 0, 4, 0),
        (0, 0, 0, 0),
    ]


def test_cycle_entirely_outside_acyclic_layer_is_not_welded() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 2))
    cg.add_node(Node("B", Status.KNOWN, "service", 2))
    cg.add_edge(Edge("A", "B", Modality.REQ, "ab"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "ba"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=0)
    assert set(result["final_nodes"]) == {"A", "B"}
    assert result["log"] == []


def test_mixed_layer_cycle_without_layer_induced_cycle_is_not_welded() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 1))
    cg.add_node(Node("B", Status.KNOWN, "service", 2))
    cg.add_edge(Edge("A", "B", Modality.REQ, "ab"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "ba"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=0)
    assert set(result["final_nodes"]) == {"A", "B"}
    assert result["log"] == []


def test_mixed_layer_scc_with_layer_one_cycle_welds_layer_one_only() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 1))
    cg.add_node(Node("B", Status.KNOWN, "service", 1))
    cg.add_node(Node("C", Status.KNOWN, "service", 2))
    cg.add_edge(Edge("A", "B", Modality.REQ, "ab"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "ba"))
    cg.add_edge(Edge("B", "C", Modality.REQ, "bc"))
    cg.add_edge(Edge("C", "A", Modality.REQ, "ca"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=1)
    assert set(result["final_nodes"]) == {"C", "WELD[A|B]"}
    assert result["final_edges"] == [
        ("WELD[A|B]", "C", "REQ", "bc"),
        ("C", "WELD[A|B]", "REQ", "ca"),
    ]


def test_overlapping_cycles_one_scc() -> None:
    cg = ConstraintGraph()
    for node_id in ["A", "B", "C", "D"]:
        cg.add_node(Node(node_id, Status.KNOWN, "service", 1))
    cg.add_edge(Edge("A", "B", Modality.REQ, "p"))
    cg.add_edge(Edge("B", "C", Modality.REQ, "q"))
    cg.add_edge(Edge("C", "A", Modality.REQ, "r"))
    cg.add_edge(Edge("B", "D", Modality.REQ, "s"))
    cg.add_edge(Edge("D", "C", Modality.REQ, "t"))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=1)
    assert result["psi_trace"] == [(0, (0, 0, 16, 0)), (1, (0, 0, 0, 0))]
    assert any("size=4" in line for line in result["log"])


def test_weld_manufactures_clash() -> None:
    cg = ConstraintGraph()
    for node_id in ["A", "B", "X"]:
        cg.add_node(Node(node_id, Status.KNOWN, "service", 1))
    cg.add_edge(Edge("A", "B", Modality.REQ, "cyc"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "cyc2"))
    cg.add_edge(Edge("A", "X", Modality.REQ, "uses"))
    cg.add_edge(Edge("B", "X", Modality.FORBID, "uses"))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=2)
    assert [psi for _, psi in result["psi_trace"]] == [
        (0, 0, 4, 0),
        (0, 0, 0, 1),
        (0, 0, 0, 0),
    ]


def test_b2_absorbs_internal_req_but_preserves_internal_partial() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 1))
    cg.add_node(Node("B", Status.KNOWN, "service", 1))
    cg.add_edge(Edge("A", "B", Modality.REQ, "ab"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "ba"))
    cg.add_edge(Edge("A", "B", Modality.PARTIAL, "soft_obligation"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=1)
    assert ("WELD[A|B]", "WELD[A|B]", "PARTIAL", "soft_obligation") in result["final_edges"]
    assert ("WELD[A|B]", "WELD[A|B]", "REQ", "ab") not in result["final_edges"]
    assert ("WELD[A|B]", "WELD[A|B]", "REQ", "ba") not in result["final_edges"]


def test_b2_preserves_internal_forbid_as_explicit_contradiction() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 1))
    cg.add_node(Node("B", Status.KNOWN, "service", 1))
    cg.add_edge(Edge("A", "B", Modality.REQ, "ab"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "ba"))
    cg.add_edge(Edge("A", "B", Modality.FORBID, "forbidden_internal"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=1)
    assert ("WELD[A|B]", "WELD[A|B]", "FORBID", "forbidden_internal") in result["final_edges"]
    assert any("internal FORBID constraint remains" in error for error in result["diagnostics"])


def test_b2_preserves_member_authority_flags_on_composite() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 1, root_permitted=True))
    cg.add_node(Node("B", Status.KNOWN, "service", 1, sink_permitted=True))
    cg.add_edge(Edge("A", "B", Modality.REQ, "ab"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "ba"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=1)
    assert result["final_nodes"]["WELD[A|B]"] == ("KNOWN", "composite", 1, True, True)


def test_b2_rewires_external_edges_deterministically() -> None:
    cg = ConstraintGraph()
    for node_id in ["A", "B", "X", "Y"]:
        cg.add_node(Node(node_id, Status.KNOWN, "service", 1))
    cg.add_edge(Edge("A", "B", Modality.REQ, "ab"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "ba"))
    cg.add_edge(Edge("X", "B", Modality.REQ, "xb"))
    cg.add_edge(Edge("A", "Y", Modality.REQ, "ay"))
    cg.add_edge(Edge("B", "Y", Modality.FORBID, "guard"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=1)
    assert result["final_edges"] == [
        ("X", "WELD[A|B]", "REQ", "xb"),
        ("WELD[A|B]", "Y", "REQ", "ay"),
        ("WELD[A|B]", "Y", "FORBID", "guard"),
    ]


def test_honest_stuck_ambiguity() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("AuditLog", Status.KNOWN, "log_sink", 1))
    cg.add_edge(Edge("AuditLog", "Downstream", Modality.REQ, "flushes_to"))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=1)
    assert result["psi_trace"] == [(0, (1, 0, 0, 0)), (1, (0, 1, 0, 0))]


def _target_domain_case(edges: list[tuple[str, str]]) -> tuple[ConstraintGraph, dict]:
    cg = ConstraintGraph()
    for source, _ in edges:
        cg.add_node(Node(source, Status.KNOWN, "service", 1))
    for source, label in edges:
        cg.add_edge(Edge(source, "Target", Modality.REQ, label))

    result = resolve(cg)
    return cg, result


def test_a1_incompatible_target_domains_are_order_independent() -> None:
    first_cg, first = _target_domain_case([("Writer", "writes_to"), ("Caller", "calls")])
    second_cg, second = _target_domain_case([("Caller", "calls"), ("Writer", "writes_to")])

    for cg, result in [(first_cg, first), (second_cg, second)]:
        assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=1)
        assert cg.nodes["Target"].status == Status.LATENT_UNRESOLVED
        assert cg.nodes["Target"].domain == set()
        assert cg.nodes["Target"].type is None
        assert any(
            "target 'Target' has contradictory required type domains" in error for error in result["diagnostics"]
        )

    assert first["status"] == second["status"]
    assert first["valid"] == second["valid"]
    assert first_cg.nodes["Target"].domain == second_cg.nodes["Target"].domain


def test_a1_compatible_target_domains_are_order_independent() -> None:
    first_cg, first = _target_domain_case([("Auditor", "flushes_to"), ("Caller", "calls")])
    second_cg, second = _target_domain_case([("Caller", "calls"), ("Auditor", "flushes_to")])

    for cg, result in [(first_cg, first), (second_cg, second)]:
        assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=2)
        assert cg.nodes["Target"].status == Status.KNOWN
        assert cg.nodes["Target"].type == "service"

    assert first["status"] == second["status"]
    assert first_cg.nodes["Target"].type == second_cg.nodes["Target"].type


def test_a1_repeated_compatible_constraints_materialize_one_target() -> None:
    cg, result = _target_domain_case([("CallerA", "calls"), ("CallerB", "calls")])

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=2)
    assert list(node_id for node_id in cg.nodes if node_id == "Target") == ["Target"]
    assert cg.nodes["Target"].status == Status.KNOWN
    assert cg.nodes["Target"].type == "service"


def test_a1_undeclared_label_materializes_empty_domain() -> None:
    cg, result = _target_domain_case([("Source", "unknown_label")])

    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=1)
    assert cg.nodes["Target"].status == Status.LATENT_UNRESOLVED
    assert cg.nodes["Target"].domain == set()
    assert cg.nodes["Target"].type is None
    assert any(
        "target 'Target' uses undeclared schema labels: ['unknown_label']" in error for error in result["diagnostics"]
    )


def test_a1_declared_plus_undeclared_label_does_not_infer_type() -> None:
    cg, result = _target_domain_case([("Caller", "calls"), ("Mystery", "unknown_label")])

    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=1)
    assert cg.nodes["Target"].status == Status.LATENT_UNRESOLVED
    assert cg.nodes["Target"].domain == set()
    assert cg.nodes["Target"].type is None
    assert any(
        "target 'Target' uses undeclared schema labels: ['unknown_label']" in error for error in result["diagnostics"]
    )


def test_a1_requeues_touching_edges_so_b1_fires() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("Source", Status.KNOWN, "service", 1))
    cg.add_edge(Edge("Source", "Target", Modality.REQ, "calls"))
    cg.add_edge(Edge("Source", "Target", Modality.FORBID, "calls"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=3)
    assert cg.nodes["Target"].status == Status.KNOWN
    assert cg.nodes["Target"].type == "service"
    assert not cg.edges[0].active
    assert cg.edges[1].active
    assert any("[B1] clash on Source->Target 'calls'" in line for line in result["log"])


def test_injected_engine_fault() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("OrderService", Status.KNOWN, "service", 1))
    cg.add_edge(Edge("OrderService", "AuditLog", Modality.REQ, "writes_to"))

    result = resolve(cg, injected_fault=True)
    assert result["status"] == EngineStatus.ENGINE_FAULT, result
    assert result["steps"] == 2, result
    assert result["fault_detail"] and "INJECTED" in result["fault_detail"]


def test_initial_psi_exception_is_reported_as_engine_fault() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("Root", Status.KNOWN, "service", 1, root_permitted=True))

    def broken_psi():
        raise RuntimeError("initial psi unavailable")

    cg.psi = broken_psi

    result = resolve(cg)

    assert result["status"] == EngineStatus.ENGINE_FAULT, result
    assert result["steps"] == 0, result
    assert result["psi_trace"] == []
    assert result["fault_detail"] == "engine exception: RuntimeError: initial psi unavailable"


def test_large_acyclic_layer_one_graph_resolves_without_recursion_fault() -> None:
    cg = ConstraintGraph()
    node_count = sys.getrecursionlimit() + 100
    for index in range(node_count):
        cg.add_node(Node(f"N{index:04d}", Status.KNOWN, "service", 1))
    for index in range(node_count - 1):
        cg.add_edge(Edge(f"N{index:04d}", f"N{index + 1:04d}", Modality.REQ, "calls"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=0)
    assert result["fault_detail"] is None


def test_clash_resolution_splits_scc() -> None:
    cg = ConstraintGraph()
    for node_id in ["A", "B", "C", "D"]:
        cg.add_node(Node(node_id, Status.KNOWN, "service", 1))

    cg.add_edge(Edge("A", "B", Modality.REQ, "ab"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "ba"))
    cg.add_edge(Edge("C", "D", Modality.REQ, "cd"))
    cg.add_edge(Edge("D", "C", Modality.REQ, "dc"))
    cg.add_edge(Edge("B", "C", Modality.REQ, "bridge"))
    cg.add_edge(Edge("B", "C", Modality.FORBID, "bridge"))
    cg.add_edge(Edge("D", "A", Modality.REQ, "return"))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=3)
    assert [psi for _, psi in result["psi_trace"]] == [
        (0, 0, 16, 1),
        (0, 0, 8, 0),
        (0, 0, 4, 0),
        (0, 0, 0, 0),
    ]


def test_singleton_prohibited_self_loop() -> None:
    assert 1 in ACYCLIC_LAYERS
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 1))
    cg.add_edge(Edge("A", "A", Modality.REQ, "recursive"))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=1)
    assert result["psi_trace"] == [(0, (0, 0, 1, 0)), (1, (0, 0, 0, 0))]
    assert "A" in result["final_nodes"]
    assert result["final_nodes"]["A"][0] == "KNOWN"
    assert any("node preserved" in line for line in result["log"])


def test_missing_source_is_stuck_not_canonical() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("Target", Status.KNOWN, "service", 1))
    cg.add_edge(Edge("MissingSource", "Target", Modality.REQ, "calls"))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=0)
    assert any("missing source" in error for error in result["diagnostics"])


def test_known_node_missing_type_is_stuck_not_canonical() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("X", Status.KNOWN, None, 1, root_permitted=True))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=0)
    assert any("known node 'X' lacks resolved type" in error for error in result["diagnostics"])


def test_known_node_missing_layer_is_stuck_not_canonical() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("X", Status.KNOWN, "service", None, root_permitted=True))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=0)
    assert any("known node 'X' lacks resolved layer" in error for error in result["diagnostics"])


def test_active_edge_label_must_match_known_target_type() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 1))
    cg.add_node(Node("X", Status.KNOWN, "log_sink", 1))
    cg.add_edge(Edge("A", "X", Modality.REQ, "calls"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=0)
    assert any(
        "active edge 0 label 'calls' targets 'X' with incompatible type 'log_sink'" in error
        for error in result["diagnostics"]
    )


def test_valid_known_node_and_edge_types_remain_canonical() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 1))
    cg.add_node(Node("X", Status.KNOWN, "service", 1))
    cg.add_edge(Edge("A", "X", Modality.REQ, "calls"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=0)


def test_unpermitted_orphan_is_stuck() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("Orphan", Status.KNOWN, "service", 1))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.STUCK, valid=False, stable=True, steps=0)
    assert any("orphan node" in error for error in result["diagnostics"])

    permitted = ConstraintGraph()
    permitted.add_node(Node("PermittedRoot", Status.KNOWN, "service", 1, root_permitted=True))
    permitted_result = resolve(permitted)
    assert_terminal(permitted_result, EngineStatus.CANONICAL, valid=True, stable=True, steps=0)


def test_urgent_promotion_cannot_be_downgraded() -> None:
    worklist = Worklist()
    worklist.push("z", URGENT)
    worklist.push("z", NORMAL)
    worklist.push("a", NORMAL)
    assert worklist.pop() == Locus.node("z")
    assert worklist.pop() == Locus.node("a")


def test_node_named_like_edge_locus_is_not_misparsed() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("edge:0", Status.KNOWN, "service", 1, root_permitted=True))
    cg.add_node(Node("Target", Status.KNOWN, "service", 1, sink_permitted=True))
    cg.add_edge(Edge("edge:0", "Target", Modality.REQ, "calls"))

    result = resolve(cg)

    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=0)
    assert "edge:0" in result["final_nodes"]


def test_composite_identifier_collision_is_safe() -> None:
    cg = ConstraintGraph()
    cg.add_node(Node("A", Status.KNOWN, "service", 1))
    cg.add_node(Node("B", Status.KNOWN, "service", 1))
    cg.add_node(Node("WELD[A|B]", Status.KNOWN, "preexisting", 1, root_permitted=True))
    cg.add_edge(Edge("A", "B", Modality.REQ, "x"))
    cg.add_edge(Edge("B", "A", Modality.REQ, "y"))

    result = resolve(cg)
    assert_terminal(result, EngineStatus.CANONICAL, valid=True, stable=True, steps=1)
    assert "WELD[A|B]" in result["final_nodes"]
    assert "WELD[A|B]#2" in result["final_nodes"]
    assert result["final_nodes"]["WELD[A|B]"][1] == "preexisting"
