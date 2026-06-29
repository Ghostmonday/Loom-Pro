from __future__ import annotations

from pathlib import Path

import pytest
from aoc_cli.blueprint import (
    Blueprint,
    BlueprintValidationError,
    WorkUnit,
    generate_blueprint,
    resolve_work_unit_domain,
)
from aoc_cli.giv import GIV

VAULT_ROOT = Path(__file__).resolve().parents[1] / "vaults" / "gaijinn-memory-fs"


def test_generate_blueprint_groups_by_directory_language_and_risk() -> None:
    blueprint = generate_blueprint(
        {
            "nodes": [
                {"id": "pkg/a.py", "path": "pkg/a.py", "language": "python", "capability_level": 1},
                {"id": "pkg/b.py", "path": "pkg/b.py", "language": "python", "capability_level": 1},
                {"id": "pkg/c.md", "path": "pkg/c.md", "language": "markdown", "capability_level": 1},
            ],
            "edges": [],
        },
        {"gravity_meta": {"nodes": {}}, "curvature_meta": {"edges": {}, "shadow_bridge_count": 0}},
        GIV(worker_id="project", allowed_paths=("pkg/",)),
    )

    grouped_paths = [unit.allowed_paths for unit in blueprint.work_units]

    assert ("pkg/a.py", "pkg/b.py") in grouped_paths
    assert ("pkg/c.md",) in grouped_paths


DARK_BRIDGE_METRICS = {
    "gravity_meta": {"nodes": {}},
    "curvature_meta": {
        "shadow_bridge_count": 1,
        "shadow_bridges": [
            {
                "source": "router.py",
                "target": "deploy.py",
                "kappa": -0.42,
                "is_dark_bridge": True,
                "is_shadow_bridge": True,
            }
        ],
        "edges": {
            "router.py->deploy.py": {
                "source": "router.py",
                "target": "deploy.py",
                "kappa": -0.42,
                "is_dark_bridge": True,
                "is_shadow_bridge": True,
            },
            "helper.py->router.py": {
                "source": "helper.py",
                "target": "router.py",
                "kappa": 0.15,
                "is_shadow_bridge": False,
            },
        },
    },
}

DARK_BRIDGE_GRAPH = {
    "nodes": [
        {"id": "router.py", "path": "router.py", "language": "python", "capability_level": 1},
        {"id": "deploy.py", "path": "deploy.py", "language": "python", "capability_level": 5},
        {"id": "helper.py", "path": "helper.py", "language": "python", "capability_level": 1},
    ],
    "edges": [["router.py", "deploy.py"], ["helper.py", "router.py"]],
}


def test_dark_bridge_atomic_block_binds_endpoints() -> None:
    blueprint = generate_blueprint(
        DARK_BRIDGE_GRAPH,
        DARK_BRIDGE_METRICS,
        GIV(worker_id="project", allowed_paths=(".",)),
    )

    bound_unit = next(
        unit for unit in blueprint.work_units if {"router.py", "deploy.py"}.issubset(set(unit.allowed_paths))
    )
    assert bound_unit.allowed_paths == ("deploy.py", "router.py")
    assert bound_unit.estimated_risk == "high"
    helper_units = [unit for unit in blueprint.work_units if "helper.py" in unit.allowed_paths]
    assert len(helper_units) == 1
    assert helper_units[0].id != bound_unit.id


def test_handoff_gateway_mode_splits_dark_bridge_endpoints() -> None:
    graph = {
        "nodes": [
            {"id": "alpha/router.py", "path": "alpha/router.py", "language": "python", "capability_level": 1},
            {"id": "beta/deploy.py", "path": "beta/deploy.py", "language": "python", "capability_level": 5},
            {"id": "helper.py", "path": "helper.py", "language": "python", "capability_level": 1},
        ],
        "edges": [["alpha/router.py", "beta/deploy.py"], ["helper.py", "alpha/router.py"]],
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
                },
                "helper.py->alpha/router.py": {
                    "source": "helper.py",
                    "target": "alpha/router.py",
                    "kappa": 0.15,
                    "is_shadow_bridge": False,
                },
            },
        },
    }
    giv = GIV(worker_id="project", allowed_paths=(".",))
    weld = generate_blueprint(graph, metrics, giv, handoff_gateways=False)
    gateway = generate_blueprint(graph, metrics, giv, handoff_gateways=True)

    weld_bound = next(
        unit for unit in weld.work_units if {"alpha/router.py", "beta/deploy.py"}.issubset(set(unit.allowed_paths))
    )
    assert weld_bound.allowed_paths == ("alpha/router.py", "beta/deploy.py")

    router_units = [unit for unit in gateway.work_units if "alpha/router.py" in unit.allowed_paths]
    deploy_units = [unit for unit in gateway.work_units if "beta/deploy.py" in unit.allowed_paths]
    assert len(router_units) == 1
    assert len(deploy_units) == 1
    assert router_units[0].id != deploy_units[0].id
    assert len(gateway.work_units) > len(weld.work_units)
    assert any("Handoff gateway" in risk for risk in gateway.risks)


def test_non_negative_edges_allow_parallel_work_units() -> None:
    blueprint = generate_blueprint(
        {
            "nodes": [
                {"id": "alpha/a.py", "path": "alpha/a.py", "language": "python", "capability_level": 1},
                {"id": "beta/b.py", "path": "beta/b.py", "language": "python", "capability_level": 1},
            ],
            "edges": [["alpha/a.py", "beta/b.py"]],
        },
        {
            "gravity_meta": {"nodes": {}},
            "curvature_meta": {
                "shadow_bridge_count": 0,
                "edges": {
                    "alpha/a.py->beta/b.py": {
                        "source": "alpha/a.py",
                        "target": "beta/b.py",
                        "kappa": 0.2,
                        "is_shadow_bridge": False,
                    }
                },
            },
        },
        GIV(worker_id="project", allowed_paths=(".",)),
    )

    assert len(blueprint.work_units) == 2
    assert blueprint.dependencies[blueprint.work_units[0].id] or blueprint.dependencies[blueprint.work_units[1].id]


def test_dependencies_follow_importer_to_imported_edges() -> None:
    blueprint = generate_blueprint(
        {
            "nodes": [
                {"id": "app/main.py", "path": "app/main.py", "language": "python", "capability_level": 1},
                {"id": "lib/util.py", "path": "lib/util.py", "language": "python", "capability_level": 1},
            ],
            "edges": [["app/main.py", "lib/util.py"]],
        },
        {"gravity_meta": {"nodes": {}}, "curvature_meta": {"edges": {}, "shadow_bridge_count": 0}},
        GIV(worker_id="project", allowed_paths=(".",)),
    )

    unit_by_path = {unit.allowed_paths: unit for unit in blueprint.work_units}
    importer_unit = unit_by_path[("app/main.py",)]
    imported_unit = unit_by_path[("lib/util.py",)]

    assert blueprint.dependencies[importer_unit.id] == [imported_unit.id]
    assert blueprint.dependencies[imported_unit.id] == []
    assert importer_unit.depends_on == (imported_unit.id,)


def test_blueprint_validation_rejects_overlapping_write_paths() -> None:
    with pytest.raises(BlueprintValidationError, match="overlapping write paths"):
        generate_blueprint(
            {
                "nodes": [
                    {"id": "pkg", "path": "pkg", "language": "unknown"},
                    {"id": "pkg/a.py", "path": "pkg/a.py", "language": "python"},
                ],
                "edges": [],
            },
            {"gravity_meta": {"nodes": {}}, "curvature_meta": {"edges": {}, "shadow_bridge_count": 0}},
            GIV(worker_id="project", allowed_paths=("pkg/",)),
        )


def test_blueprint_validation_rejects_dependency_cycles() -> None:
    units = (
        WorkUnit(
            id="WU-001",
            title="One",
            description="First unit",
            allowed_paths=("one.py",),
            depends_on=("WU-002",),
            acceptance_checks=("pytest",),
        ),
        WorkUnit(
            id="WU-002",
            title="Two",
            description="Second unit",
            allowed_paths=("two.py",),
            depends_on=("WU-003",),
            acceptance_checks=("pytest",),
        ),
        WorkUnit(
            id="WU-003",
            title="Three",
            description="Third unit",
            allowed_paths=("three.py",),
            depends_on=("WU-001",),
            acceptance_checks=("pytest",),
        ),
    )

    with pytest.raises(
        BlueprintValidationError,
        match="dependency cycle detected: WU-001 -> WU-002 -> WU-003 -> WU-001",
    ):
        Blueprint(
            schema_version=1,
            project_goal="Detect dependency cycles",
            assumptions=(),
            work_units=units,
            dependencies=Blueprint.dependencies_from_units(units),
            risks=(),
        )


def test_resolve_work_unit_domain_allows_vault_mixed_file_types() -> None:
    domain = resolve_work_unit_domain(
        (
            "40_Concepts/council-memory-index.md",
            ".agents/vault.yaml",
            "ui/vault-ui-intent-map.json",
            "10_Operations/knowledge-linter.py",
        )
    )
    assert domain == "vault"


def test_resolve_work_unit_domain_still_rejects_monorepo_straddle() -> None:
    with pytest.raises(BlueprintValidationError, match="straddles vault and code paths"):
        resolve_work_unit_domain(("40_Concepts/foo.md", "aoc-cli/aoc_cli/blueprint.py"))


def test_generate_blueprint_from_obsidian_vault_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(VAULT_ROOT)
    blueprint = generate_blueprint(
        {
            "nodes": [
                {"id": "40_Concepts/foo.md", "path": "40_Concepts/foo.md", "language": "markdown"},
                {"id": ".agents/vault.yaml", "path": ".agents/vault.yaml", "language": "yaml"},
                {"id": "ui/map.json", "path": "ui/vault-ui-intent-map.json", "language": "json"},
            ],
            "edges": [],
        },
        {"gravity_meta": {"nodes": {}}, "curvature_meta": {"edges": {}, "shadow_bridge_count": 0}},
        GIV(worker_id="vault", allowed_paths=(".",)),
    )
    assert blueprint.work_units
    assert all(unit.domain == "vault" for unit in blueprint.work_units)
