"""Cycle detection invariants for blueprint.py (Grok audit remediation)."""

from __future__ import annotations

import pytest
from aoc_cli.blueprint import (
    Blueprint,
    BlueprintValidationError,
    WorkUnit,
    _dependency_graph_from_mapping,
    _validate_dependency_graph_acyclic,
    generate_blueprint,
)
from aoc_cli.giv import GIV


def _unit(
    unit_id: str,
    path: str,
    *,
    depends_on: tuple[str, ...] = (),
) -> WorkUnit:
    return WorkUnit(
        id=unit_id,
        title=unit_id,
        description=unit_id,
        allowed_paths=(path,),
        depends_on=depends_on,
        acceptance_checks=("pytest",),
    )


def test_validate_dependency_graph_acyclic_detects_three_cycle() -> None:
    graph = _dependency_graph_from_mapping(
        {
            "WU-001": ["WU-002"],
            "WU-002": ["WU-003"],
            "WU-003": ["WU-001"],
        },
        ("WU-001", "WU-002", "WU-003"),
    )
    with pytest.raises(
        BlueprintValidationError,
        match=r"dependency cycle detected: WU-001 -> WU-002 -> WU-003 -> WU-001",
    ):
        _validate_dependency_graph_acyclic(graph, ("WU-001", "WU-002", "WU-003"))


def test_validate_dependency_graph_acyclic_handles_deep_chain_without_recursion() -> None:
    depth = 250
    ids = [f"WU-{index:03d}" for index in range(1, depth + 1)]
    dependencies = {ids[index]: [ids[index + 1]] for index in range(depth - 1)}
    graph = _dependency_graph_from_mapping(dependencies, ids)
    _validate_dependency_graph_acyclic(graph, ids)


def test_validate_blueprint_rejects_divergent_depends_on_payload() -> None:
    units = (
        _unit("WU-001", "one.py", depends_on=("WU-002",)),
        _unit("WU-002", "two.py"),
    )
    with pytest.raises(BlueprintValidationError, match="diverges from dependencies"):
        Blueprint(
            schema_version=1,
            project_goal="alignment",
            assumptions=(),
            work_units=units,
            dependencies={"WU-001": [], "WU-002": []},
            risks=(),
        )


def test_generate_blueprint_welds_cyclic_import_graph() -> None:
    graph = {
        "nodes": [
            {"id": "pkg/a.py", "path": "pkg/a.py", "language": "python", "capability_level": 1},
            {"id": "pkg/b.py", "path": "pkg/b.py", "language": "python", "capability_level": 1},
            {"id": "lib/c.py", "path": "lib/c.py", "language": "python", "capability_level": 1},
        ],
        "edges": [["pkg/a.py", "pkg/b.py"], ["pkg/b.py", "lib/c.py"], ["lib/c.py", "pkg/a.py"]],
    }
    metrics = {"gravity_meta": {"nodes": {}}, "curvature_meta": {"edges": {}, "shadow_bridge_count": 0}}
    blueprint = generate_blueprint(graph, metrics, GIV(worker_id="project", allowed_paths=(".",)))
    assert any("cycle" in unit.title.lower() for unit in blueprint.work_units)
    assert len(blueprint.work_units) < 3
    for unit in blueprint.work_units:
        assert unit.depends_on == tuple(blueprint.dependencies.get(unit.id, ()))


def test_handoff_gateway_dependencies_remain_acyclic_on_dark_bridge_split() -> None:
    graph = {
        "nodes": [
            {"id": "alpha/router.py", "path": "alpha/router.py", "language": "python", "capability_level": 1},
            {"id": "beta/deploy.py", "path": "beta/deploy.py", "language": "python", "capability_level": 5},
        ],
        "edges": [["alpha/router.py", "beta/deploy.py"]],
    }
    metrics = {
        "gravity_meta": {"nodes": {}},
        "curvature_meta": {
            "shadow_bridge_count": 1,
            "shadow_bridges": [
                {
                    "source": "alpha/router.py",
                    "target": "beta/deploy.py",
                    "kappa": -0.42,
                    "is_dark_bridge": True,
                    "is_shadow_bridge": True,
                }
            ],
            "edges": {
                "alpha/router.py->beta/deploy.py": {
                    "source": "alpha/router.py",
                    "target": "beta/deploy.py",
                    "kappa": -0.42,
                    "is_dark_bridge": True,
                    "is_shadow_bridge": True,
                }
            },
        },
    }
    blueprint = generate_blueprint(
        graph,
        metrics,
        GIV(worker_id="project", allowed_paths=(".",)),
        handoff_gateways=True,
    )
    for unit in blueprint.work_units:
        assert unit.depends_on == tuple(blueprint.dependencies.get(unit.id, ()))
