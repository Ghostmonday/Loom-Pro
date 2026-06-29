from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from aoc_cli.blueprint import Blueprint, WorkUnit
from aoc_cli.cli import app
from aoc_cli.helpers.audit import (
    AUDIT_SCHEMA_VERSION,
    max_parallel_worker_capacity,
    readiness_profile,
    run_structural_audit,
)
from typer.testing import CliRunner

runner = CliRunner()

TINY_SOURCE = Path(__file__).resolve().parents[1] / "examples" / "tiny-python-service"


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=str(path), check=True, capture_output=True)  # noqa: S607
    subprocess.run(  # noqa: S607
        ["git", "config", "user.email", "tests@example.invalid"],  # noqa: S607
        cwd=str(path),
        check=True,
        capture_output=True,  # noqa: S607, E501
    )
    subprocess.run(["git", "config", "user.name", "Gaijinn Tests"], cwd=str(path), check=True, capture_output=True)  # noqa: S607
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=str(path), check=True, capture_output=True)  # noqa: S607
    subprocess.run(["git", "add", "-A"], cwd=str(path), check=True, capture_output=True)  # noqa: S607
    subprocess.run(["git", "commit", "-m", "audit test"], cwd=str(path), check=True, capture_output=True)  # noqa: S607


def test_readiness_profile_tiers() -> None:
    tier, _ = readiness_profile(0.75, 0)
    assert tier == "TIER_1_SWARM_READY"
    tier, _ = readiness_profile(0.40, 2)
    assert tier == "TIER_2_DEFERRED_ONLY"
    tier, _ = readiness_profile(0.10, 0)
    assert tier == "TIER_3_STRUCTURAL_LOCK"


def test_max_parallel_worker_capacity_from_dependency_layers() -> None:
    units = (
        WorkUnit(
            id="WU-001",
            title="a",
            description="a",
            allowed_paths=("a/",),
            depends_on=(),
            acceptance_checks=("pytest",),
        ),
        WorkUnit(
            id="WU-002",
            title="b",
            description="b",
            allowed_paths=("b/",),
            depends_on=(),
            acceptance_checks=("pytest",),
        ),
        WorkUnit(
            id="WU-003",
            title="c",
            description="c",
            allowed_paths=("c/",),
            depends_on=("WU-001", "WU-002"),
            acceptance_checks=("pytest",),
        ),
    )
    blueprint = Blueprint(
        schema_version=1,
        project_goal="test",
        assumptions=(),
        work_units=units,
        dependencies=Blueprint.dependencies_from_units(units),
        risks=(),
    )
    assert max_parallel_worker_capacity(blueprint) == 2


def test_audit_requires_git_repository(tmp_path: Path) -> None:
    repo = tmp_path / "no-git"
    repo.mkdir()
    (repo / "main.py").write_text("print('ok')\n", encoding="utf-8")

    result = runner.invoke(app, ["audit", str(repo)], color=False)
    assert result.exit_code != 0
    assert "git repository" in result.output.lower()


def test_audit_tiny_python_service_writes_report(tmp_path: Path) -> None:
    import shutil

    repo = tmp_path / "tiny"
    shutil.copytree(
        TINY_SOURCE,
        repo,
        ignore=shutil.ignore_patterns(".gaijinn", "__pycache__", ".pytest_cache", ".git"),
    )
    _init_git_repo(repo)

    result = runner.invoke(app, ["audit", str(repo)], color=False)
    assert result.exit_code == 0, result.output
    assert "GAIJINN STRUCTURAL AUDIT REPORT" in result.output
    assert "Readiness" in result.output

    report_path = repo / ".gaijinn" / "audit-report.json"
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == AUDIT_SCHEMA_VERSION
    assert payload["metrics"]["total_code_nodes"] >= 1
    assert "governance_profile" in payload
    assert "readiness_tier" in payload["governance_profile"]


def test_audit_json_only_stdout(tmp_path: Path) -> None:
    import shutil

    repo = tmp_path / "tiny-json"
    shutil.copytree(
        TINY_SOURCE,
        repo,
        ignore=shutil.ignore_patterns(".gaijinn", "__pycache__", ".pytest_cache", ".git"),
    )
    _init_git_repo(repo)

    result = runner.invoke(app, ["audit", str(repo), "--json-only", "--stdout-only"], color=False)
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == AUDIT_SCHEMA_VERSION
    assert not (repo / ".gaijinn" / "audit-report.json").exists()


def test_atomic_weld_block_metrics_detects_multi_file_welds() -> None:
    from aoc_cli.blueprint import Blueprint, WorkUnit
    from aoc_cli.helpers.audit import atomic_weld_block_metrics

    units = (
        WorkUnit(
            id="WU-001",
            title="Consolidate coupling review block (40 files)",
            description="weld",
            allowed_paths=tuple(f"src/f{i}.py" for i in range(40)),
            acceptance_checks=("pytest",),
        ),
        WorkUnit(
            id="WU-002",
            title="python low-risk changes in lib",
            description="normal",
            allowed_paths=("lib/a.py",),
            acceptance_checks=("pytest",),
        ),
    )
    blueprint = Blueprint(
        schema_version=1,
        project_goal="test",
        assumptions=(),
        work_units=units,
        dependencies=Blueprint.dependencies_from_units(units),
        risks=(),
    )
    metrics = atomic_weld_block_metrics(blueprint)
    assert metrics["atomic_weld_blocks"] == 1
    assert metrics["largest_atomic_weld_file_count"] == 40
    assert metrics["total_files_in_atomic_welds"] == 40


def test_handoff_gateway_profile_unlocks_parallel_units() -> None:
    from aoc_cli.blueprint import handoff_gateway_records
    from aoc_cli.giv import GIV
    from aoc_cli.helpers.audit import handoff_gateway_profile

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
    giv = GIV(worker_id="audit", allowed_paths=(".",))
    profile = handoff_gateway_profile(graph, metrics, giv)
    assert profile["handoff_gateway_count"] == 1
    assert profile["work_unit_count_gateway_mode"] > profile["work_unit_count_weld_mode"]
    assert profile["parallel_units_unlocked"] >= 1
    assert profile["legacy_mode"]["atomic_weld_blocks"] >= 1
    assert profile["gateway_mode"]["atomic_weld_blocks"] == 0
    assert profile["efficiency_delta"]["atomic_weld_blocks_eliminated"] >= 1
    assert handoff_gateway_records(metrics)[0]["gateway_type"] == "HANDOFF_ONLY"


def test_run_structural_audit_on_gaijinn_repo() -> None:
    root = Path(__file__).resolve().parents[1]
    if not (root / ".git").exists():
        pytest.skip("Gaijinn repo has no .git in this environment")
    payload = run_structural_audit(root)
    assert payload["metrics"]["total_code_nodes"] > 10
    assert payload["governance_profile"]["readiness_tier"].startswith("TIER_")
    assert "handoff_gateway_profile" in payload
