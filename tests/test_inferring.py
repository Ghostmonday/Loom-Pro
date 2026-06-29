from __future__ import annotations

from aoc_cli.inferring import infer_reflective_layer


def _pipeline_fixture() -> list[dict]:
    return [
        {
            "agent_intent": "pipeline_create",
            "valid_prior_state": None,
            "resulting_state": "pipeline_created",
            "context_params": ["orgID", "userID"],
            "query_params": ["resourceID"],
            "resource_cluster": "pipeline",
        },
        {
            "agent_intent": "pipeline_activate",
            "valid_prior_state": "pipeline_created",
            "resulting_state": "pipeline_active",
            "context_params": ["orgID", "userID"],
            "query_params": ["resourceID"],
            "resource_cluster": "pipeline",
        },
        {
            "agent_intent": "pipeline_trigger",
            "valid_prior_state": "pipeline_active",
            "resulting_state": "pipeline_running",
            "context_params": ["orgID", "userID"],
            "query_params": ["resourceID"],
            "resource_cluster": "pipeline",
        },
        {
            "agent_intent": "pipeline_cancel",
            "valid_prior_state": "pipeline_running",
            "resulting_state": "pipeline_cancelled",
            "context_params": ["orgID", "userID"],
            "query_params": ["resourceID"],
            "resource_cluster": "pipeline",
        },
    ]


def _run_failure_fixture() -> list[dict]:
    return [
        {
            "agent_intent": "run_start",
            "valid_prior_state": None,
            "resulting_state": "run_pending",
            "resource_cluster": "run",
        },
        {
            "agent_intent": "run_execute",
            "valid_prior_state": "run_pending",
            "resulting_state": "run_running",
            "resource_cluster": "run",
        },
        {
            "agent_intent": "run_fail",
            "valid_prior_state": "run_running",
            "resulting_state": "run_failed",
            "resource_cluster": "run",
        },
    ]


def _org_secret_fixture() -> list[dict]:
    return [
        {
            "agent_intent": "secret_create",
            "valid_prior_state": None,
            "resulting_state": "secret_created",
            "context_params": ["orgID", "userID"],
            "query_params": ["resourceID"],
            "resource_cluster": "org",
        },
        {
            "agent_intent": "secret_read",
            "valid_prior_state": "secret_created",
            "resulting_state": "secret_read",
            "context_params": ["orgID", "userID"],
            "query_params": ["resourceID"],
            "resource_cluster": "org",
        },
        {
            "agent_intent": "secret_delete",
            "valid_prior_state": None,
            "resulting_state": "secret_deleted",
            "context_params": [],
            "query_params": ["resourceID"],
            "resource_cluster": "org",
        },
    ]


def test_state_path_chaining_compiles_lifecycle_chain() -> None:
    meta = infer_reflective_layer(_pipeline_fixture())
    chains = meta["state_path_chaining"]["lifecycle_chains"]
    edges = meta["state_path_chaining"]["edges"]

    assert meta["intent_node_count"] == 4
    assert ("pipeline_create", "pipeline_activate") in {(e["source"], e["target"]) for e in edges}
    assert any(
        chain["steps"]
        == [
            "pipeline_create",
            "pipeline_activate",
            "pipeline_trigger",
            "pipeline_cancel",
        ]
        for chain in chains
    )


def test_topological_boundary_scan_detects_run_failed_ceiling() -> None:
    meta = infer_reflective_layer(_run_failure_fixture())
    ceilings = meta["topological_boundary_scan"]["capability_ceilings"]
    failed_ceiling = next(item for item in ceilings if item["terminal_state"] == "run_failed")

    assert failed_ceiling["missing_recoveries"]
    assert any(
        recovery["missing_resulting_state"] == "run_pending" for recovery in failed_ceiling["missing_recoveries"]
    )
    assert "new lifecycle chain" in failed_ceiling["description"]


def test_curvature_measurement_detects_secret_delete_shadowbridge() -> None:
    meta = infer_reflective_layer(_org_secret_fixture())
    bridges = meta["curvature_measurement"]["shadowbridges"]
    delete_bridge = next(item for item in bridges if item["agent_intent"] == "secret_delete")

    assert delete_bridge["is_shadowbridge"] is True
    assert "orgID" in delete_bridge["missing_context_params"] or "userID" in delete_bridge["missing_context_params"]
    assert "org" in delete_bridge["resource_cluster"]


def test_dependency_contracts_require_prior_state() -> None:
    meta = infer_reflective_layer(_pipeline_fixture())
    contracts = meta["state_path_chaining"]["dependency_contracts"]
    activate_contract = next(item for item in contracts if item["intent"] == "pipeline_activate")

    assert activate_contract["requires_prior_state"] == "pipeline_created"
    assert activate_contract["requires_node"] == "pipeline_create"


def test_empty_interaction_graph_returns_zero_counts() -> None:
    meta = infer_reflective_layer([])
    assert meta["intent_node_count"] == 0
    assert meta["topological_boundary_scan"]["ceiling_count"] == 0
    assert meta["curvature_measurement"]["shadowbridge_count"] == 0
    assert meta["topological_inference"]["gap_count"] == 0


def test_topological_inference_detects_disconnected_created_to_active_gap() -> None:
    graph = [
        {
            "agent_intent": "pipeline_create",
            "valid_prior_state": None,
            "resulting_state": "pipeline_created",
            "resource_cluster": "pipeline",
        },
        {
            "agent_intent": "pipeline_trigger",
            "valid_prior_state": "pipeline_active",
            "resulting_state": "pipeline_running",
            "resource_cluster": "pipeline",
        },
    ]
    meta = infer_reflective_layer(graph)
    gaps = meta["topological_inference"]["disconnected_lifecycle_gaps"]
    assert any(gap["from_state"] == "pipeline_created" and gap["to_state"] == "pipeline_active" for gap in gaps)
