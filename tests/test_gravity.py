from __future__ import annotations

import pytest
from aoc_cli.gravity import GRAVITY_HARD_FLOOR, compute_gravity_and_curvature


def test_compute_gravity_and_curvature_valid_graph() -> None:
    metrics = compute_gravity_and_curvature(
        {
            "nodes": [
                {"id": "ingest", "capability_level": 2, "side_effect_score": 0.5},
                {"id": "plan", "capability_level": 3, "side_effect_score": 1},
                {"id": "apply", "capability_level": 4, "side_effect_score": 1},
            ],
            "edges": [("ingest", "plan"), ("plan", "apply")],
        }
    )

    assert metrics["gravity_meta"]["hard_floor"] == GRAVITY_HARD_FLOOR
    assert metrics["gravity_meta"]["automatic_rejection"] is False
    assert metrics["gravity_meta"]["rejected_nodes"] == []
    assert set(metrics["gravity_meta"]["nodes"]) == {"ingest", "plan", "apply"}
    assert metrics["curvature_meta"]["shadow_bridge_count"] == 0
    assert metrics["curvature_meta"]["edges"]["ingest->plan"]["curvature"] == 0.0
    assert metrics["curvature_meta"]["edges"]["plan->apply"]["curvature"] == 1.0


def test_compute_gravity_and_curvature_rejects_non_mapping_input() -> None:
    with pytest.raises(TypeError, match="graph_data must be a dictionary-like mapping"):
        compute_gravity_and_curvature(["not", "a", "mapping"])


def test_compute_gravity_and_curvature_rejects_non_numeric_scores() -> None:
    with pytest.raises(ValueError, match="score must be numeric, got 'high'"):
        compute_gravity_and_curvature(
            {
                "nodes": [{"id": "deploy", "capability_level": "high"}],
                "edges": [],
            }
        )


def test_compute_gravity_and_curvature_flags_shadow_bridge_risk_jump() -> None:
    metrics = compute_gravity_and_curvature(
        {
            "nodes": [
                {"id": "router", "capability_level": 1, "side_effect_score": 0},
                {"id": "deploy", "capability_level": 5, "side_effect_score": 3},
            ],
            "edges": [("router", "deploy")],
        }
    )

    edge = metrics["curvature_meta"]["edges"]["router->deploy"]
    assert metrics["curvature_meta"]["shadow_bridge_count"] == 1
    assert metrics["curvature_meta"]["shadow_bridges"] == [edge]
    assert edge["is_shadow_bridge"] is True
    assert edge["risk_jump_shadow_bridge"] is True
    assert edge["curvature"] == -1.0
