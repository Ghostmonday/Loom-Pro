"""Real merge-grid integration tests (no --dry-run).

Exercises collect → validate-worker → merge-grid on git-worktree workers with
actual branch merges. Complements mock-grid terminal smoke tests.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from aoc_cli.cli import app
from aoc_cli.helpers.merge import (
    GOVERNANCE_PATH,
    INTEGRATION_BRANCH,
    load_merge_governance,
    merge_pipeline_status,
    worker_merge_order,
    write_merge_governance,
)
from typer.testing import CliRunner

runner = CliRunner()

TINY_SOURCE = Path(__file__).resolve().parents[1] / "examples" / "tiny-python-service"

ROUTER_SOURCE = '''"""Route table."""

DEFAULT_ROUTE = "/health"
'''

DEPLOY_SOURCE = '''"""Deploy config."""

from .router import DEFAULT_ROUTE

BIND_HOST = "127.0.0.1"
DEFAULT_BIND_ROUTE = DEFAULT_ROUTE
'''


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Gaijinn Test",
        "GIT_AUTHOR_EMAIL": "gaijinn-test@example.com",
        "GIT_COMMITTER_NAME": "Gaijinn Test",
        "GIT_COMMITTER_EMAIL": "gaijinn-test@example.com",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "commit.gpgsign",
        "GIT_CONFIG_VALUE_0": "false",
    }
    result = subprocess.run(  # noqa: S607
        ["git", *args],
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr or result.stdout}")
    return result


def _project_test_env(project: Path) -> dict[str, str]:
    import sys

    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "").strip()
    project_path = str(project.resolve())
    env["PYTHONPATH"] = os.pathsep.join([project_path, existing] if existing else [project_path])
    toolchain_bin = str(Path(sys.executable).resolve().parent)
    path_entries = [toolchain_bin, env.get("PATH", "").strip()]
    env["PATH"] = os.pathsep.join(entry for entry in path_entries if entry)
    return env


def _work_unit(
    unit_id: str,
    title: str,
    allowed_paths: list[str],
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": unit_id,
        "title": title,
        "description": title,
        "allowed_paths": allowed_paths,
        "denied_paths": [],
        "depends_on": depends_on or [],
        "acceptance_checks": ["pytest"],
        "estimated_risk": "medium",
    }


def _tests_depend_on_service_blueprint() -> dict[str, Any]:
    """WU-001 owns tests and depends on WU-002 service (tiny-python-service pattern)."""
    return {
        "schema_version": 1,
        "project_goal": "Sibling-dependent validation deferral test",
        "assumptions": [
            "Pre-merge pytest defers when depends_on units are owned by sibling workers.",
            "Post-merge checks enforce integration tests after sequential merge.",
        ],
        "work_units": [
            _work_unit(
                "WU-001",
                "Tests depend on service layer",
                ["tests/test_api.py"],
                depends_on=["WU-002"],
            ),
            _work_unit(
                "WU-002",
                "Service layer",
                ["tiny_service/service.py"],
            ),
        ],
        "dependencies": {"WU-001": ["WU-002"], "WU-002": []},
        "risks": [],
    }


def _atomic_weld_blueprint() -> dict[str, Any]:
    """WU-001 owns welded router+deploy; WU-002 owns service and depends on WU-001."""
    return {
        "schema_version": 1,
        "project_goal": "Atomic weld merge integrity test",
        "assumptions": [
            "Dark Bridge endpoints share one work unit.",
            "Merge order respects blueprint depends_on.",
        ],
        "work_units": [
            _work_unit(
                "WU-001",
                "Consolidate coupling review block",
                ["tiny_service/router.py", "tiny_service/deploy.py"],
            ),
            _work_unit(
                "WU-002",
                "Service layer",
                ["tiny_service/service.py"],
                depends_on=["WU-001"],
            ),
        ],
        "dependencies": {"WU-001": [], "WU-002": ["WU-001"]},
        "risks": [],
    }


def _worker_handoff_gitignore_lines() -> str:
    from aoc_cli.helpers.constants import WORKER_HANDOFF_BASENAMES

    return "\n".join(sorted(WORKER_HANDOFF_BASENAMES)) + "\n"


def _bootstrap_tiny_merge_repo(
    tmp_path: Path,
    *,
    blueprint: dict[str, Any] | None = None,
) -> Path:
    """Copy tiny-python-service, add router/deploy, init clean git, run-grid worktrees."""
    project = tmp_path / "tiny-python-service"
    shutil.copytree(
        TINY_SOURCE,
        project,
        ignore=shutil.ignore_patterns(".gaijinn", "__pycache__", ".pytest_cache", ".git"),
    )
    (project / "tiny_service" / "router.py").write_text(ROUTER_SOURCE, encoding="utf-8")
    (project / "tiny_service" / "deploy.py").write_text(DEPLOY_SOURCE, encoding="utf-8")
    gitignore = project / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    gitignore.write_text(
        existing.rstrip() + "\n" + _worker_handoff_gitignore_lines() + ".gaijinn/\n__pycache__/\n.pytest_cache/\n",
        encoding="utf-8",
    )

    _git(project, "init", "-b", "main", check=True)
    _git(project, "config", "user.name", "Gaijinn Test", check=True)
    _git(project, "config", "user.email", "gaijinn-test@example.com", check=True)
    _git(project, "add", "-A", check=True)
    _git(project, "commit", "-m", "initial", check=True)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.chdir(project)
    try:
        for command in (
            ["init", "--force", "--no-agent-files", "Atomic weld merge integrity test"],
            ["compile-prompt"],
        ):
            result = runner.invoke(app, command, color=False)
            assert result.exit_code == 0, result.output

        blueprint_path = project / ".gaijinn" / "blueprint.json"
        blueprint_path.write_text(
            json.dumps(blueprint or _atomic_weld_blueprint(), indent=2) + "\n",
            encoding="utf-8",
        )

        status = _git(project, "status", "--porcelain", check=False)
        if status.stdout.strip():
            raise AssertionError(
                f"expected clean git tree before run-grid for git-worktree mode; found:\n{status.stdout}"
            )

        grid = runner.invoke(app, ["run-grid", "--workers", "2", "--force"], color=False)
        assert grid.exit_code == 0, grid.output
    finally:
        monkeypatch.undo()

    manifest = json.loads((project / ".gaijinn/workers/manifest.json").read_text(encoding="utf-8"))
    assert manifest.get("mode") == "git-worktree", "real merge tests require clean git worktrees"
    return project


def _commit_worker_edit(worker_dir: Path, *, message: str, edits: dict[str, str]) -> None:
    for rel_path, content in edits.items():
        path = worker_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        _git(worker_dir, "add", "--", rel_path, check=True)
    _git(worker_dir, "commit", "-m", message, check=True)
    (worker_dir / "output.log").write_text("build PASS\n", encoding="utf-8")
    from aoc_cli.state import transition_worker_state
    manifest_path = worker_dir.parent / "manifest.json"
    transition_worker_state(manifest_path, worker_dir.name, "completed")


def _run_merge_pipeline(project: Path) -> dict[str, Any]:
    for command in (["collect"], ["validate-worker"], ["merge-grid", "--no-test"]):
        result = runner.invoke(app, command, color=False)
        assert result.exit_code == 0, result.output
    write_merge_governance(project)
    return merge_pipeline_status(project)


@pytest.fixture
def merge_repo(tmp_path: Path) -> Path:
    return _bootstrap_tiny_merge_repo(tmp_path)


def test_atomic_weld_real_merge_grid_completes_without_conflict(merge_repo: Path, monkeypatch) -> None:
    """Dark-bridge endpoints on one worker merge cleanly; service worker merges after."""
    project = merge_repo
    monkeypatch.chdir(project)

    manifest = json.loads((project / ".gaijinn/workers/manifest.json").read_text(encoding="utf-8"))
    weld_worker = next(
        detail["worker_id"]
        for detail in manifest["worker_details"]
        if "WU-001" in detail.get("assigned_work_units", [])
    )
    service_worker = next(
        detail["worker_id"]
        for detail in manifest["worker_details"]
        if "WU-002" in detail.get("assigned_work_units", [])
    )

    weld_dir = project / ".gaijinn/workers" / weld_worker
    service_dir = project / ".gaijinn/workers" / service_worker

    router_base = (weld_dir / "tiny_service/router.py").read_text(encoding="utf-8")
    deploy_base = (weld_dir / "tiny_service/deploy.py").read_text(encoding="utf-8")
    service_base = (service_dir / "tiny_service/service.py").read_text(encoding="utf-8")

    _commit_worker_edit(
        weld_dir,
        message="weld: router then deploy (atomic block)",
        edits={
            "tiny_service/router.py": router_base + '\nROUTER_WELD_MARKER = "weld-worker"\n',
            "tiny_service/deploy.py": deploy_base + '\nDEPLOY_WELD_MARKER = "weld-worker"\n',
        },
    )
    _commit_worker_edit(
        service_dir,
        message="service layer change",
        edits={
            "tiny_service/service.py": service_base.replace(
                "class TaskService:",
                'SERVICE_MARKER = "service-worker"\n\nclass TaskService:',
            ),
        },
    )

    pipeline = _run_merge_pipeline(project)
    report = json.loads((project / ".gaijinn/merge/report.json").read_text(encoding="utf-8"))

    assert pipeline["phase"] == "completed"
    assert pipeline["validated_passed"] == 2
    assert report["summary"]["merged"] == 2
    assert report["summary"]["conflicted"] == 0
    assert report["summary"]["blocked"] == 0
    assert report.get("dry_run") is not True

    merged_ids = [worker_id for worker_id, result in report["workers"].items() if result["status"] == "merged"]
    assert merged_ids == [weld_worker, service_worker]

    _git(project, "checkout", INTEGRATION_BRANCH, check=True)
    router_text = (project / "tiny_service/router.py").read_text(encoding="utf-8")
    deploy_text = (project / "tiny_service/deploy.py").read_text(encoding="utf-8")
    service_text = (project / "tiny_service/service.py").read_text(encoding="utf-8")
    assert 'ROUTER_WELD_MARKER = "weld-worker"' in router_text
    assert 'DEPLOY_WELD_MARKER = "weld-worker"' in deploy_text
    assert 'SERVICE_MARKER = "service-worker"' in service_text

    router_idx = router_text.index("ROUTER_WELD_MARKER")
    deploy_idx = deploy_text.index("DEPLOY_WELD_MARKER")
    assert router_idx < len(router_text)
    assert deploy_idx < len(deploy_text)

    governance = load_merge_governance(project)
    assert governance is not None
    assert (project / GOVERNANCE_PATH).exists()
    structural = governance["structural_score"]
    assert structural["convergence"] == 1.0
    assert structural["conflict_free"] is True
    assert structural["handoff_isolation"] is True
    assert structural["merge_order_valid"] is True
    assert structural["dry_run"] is False
    assert pipeline["structural_score"]["convergence"] == 1.0


def test_merge_grid_worker_order_follows_blueprint_depends_on(merge_repo: Path) -> None:
    """WU-002 depends on WU-001 → weld worker merges before service worker."""
    project = merge_repo
    manifest = json.loads((project / ".gaijinn/workers/manifest.json").read_text(encoding="utf-8"))
    details = {item["worker_id"]: item for item in manifest["worker_details"]}

    from aoc_cli.blueprint import Blueprint

    blueprint = Blueprint.from_dict(_atomic_weld_blueprint())
    order = worker_merge_order(["worker-001", "worker-002"], details, blueprint)

    weld_worker = next(
        detail["worker_id"]
        for detail in manifest["worker_details"]
        if "WU-001" in detail.get("assigned_work_units", [])
    )
    service_worker = next(
        detail["worker_id"]
        for detail in manifest["worker_details"]
        if "WU-002" in detail.get("assigned_work_units", [])
    )
    assert order.index(weld_worker) < order.index(service_worker)


def test_merge_grid_surfaces_git_conflict_when_branches_collide(merge_repo: Path, monkeypatch) -> None:
    """Merge layer records conflicted workers when two branches touch the same file."""
    project = merge_repo
    monkeypatch.chdir(project)

    w1 = project / ".gaijinn/workers/worker-001"
    w2 = project / ".gaijinn/workers/worker-002"
    router_path = "tiny_service/router.py"

    router_w1 = (w1 / router_path).read_text(encoding="utf-8") + '\nROUTER_MARKER = "worker-001"\n'
    router_w2 = (w2 / router_path).read_text(encoding="utf-8") + '\nROUTER_MARKER = "worker-002"\n'
    _commit_worker_edit(w1, message="conflict-a", edits={router_path: router_w1})
    _commit_worker_edit(w2, message="conflict-b", edits={router_path: router_w2})

    merge_dir = project / ".gaijinn/merge"
    merge_dir.mkdir(parents=True, exist_ok=True)
    base_ref = _git(project, "rev-parse", "HEAD").stdout.strip()
    (merge_dir / "collected.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "collected_at": "2026-06-16T10:00:00Z",
                "base_branch": "main",
                "base_ref": base_ref,
                "workers": {
                    "worker-001": {"status": "completed"},
                    "worker-002": {"status": "completed"},
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (merge_dir / "validated.json").write_text(
        json.dumps(
            {
                "worker-001": {"passed": True, "gates": {}},
                "worker-002": {"passed": True, "gates": {}},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["merge-grid", "--no-test"], color=False)
    assert result.exit_code == 0, result.output

    report = json.loads((project / ".gaijinn/merge/report.json").read_text(encoding="utf-8"))
    pipeline = merge_pipeline_status(project)

    assert pipeline["phase"] == "completed"
    assert report["summary"]["conflicted"] >= 1
    conflicted = [
        worker_id for worker_id, payload in report["workers"].items() if payload.get("status") == "conflicted"
    ]
    assert conflicted
    conflict_files = report["workers"][conflicted[0]].get("conflict_files", [])
    assert any(router_path in entry for entry in conflict_files)


def test_merge_grid_post_merge_pytest_enforces_deferred_integration(tmp_path: Path, monkeypatch) -> None:
    """Deferred pre-merge tests must pass on integration branch after sibling merge order."""
    project = _bootstrap_tiny_merge_repo(tmp_path, blueprint=_tests_depend_on_service_blueprint())
    monkeypatch.chdir(project)

    manifest = json.loads((project / ".gaijinn/workers/manifest.json").read_text(encoding="utf-8"))
    tests_worker = next(
        detail["worker_id"]
        for detail in manifest["worker_details"]
        if "WU-001" in detail.get("assigned_work_units", [])
    )
    service_worker = next(
        detail["worker_id"]
        for detail in manifest["worker_details"]
        if "WU-002" in detail.get("assigned_work_units", [])
    )

    tests_dir = project / ".gaijinn/workers" / tests_worker
    service_dir = project / ".gaijinn/workers" / service_worker

    test_source = (tests_dir / "tests/test_api.py").read_text(encoding="utf-8")
    service_source = (service_dir / "tiny_service/service.py").read_text(encoding="utf-8")

    _commit_worker_edit(
        tests_dir,
        message="tests: assert DONE_STATUS from service",
        edits={
            "tests/test_api.py": test_source
            + "\n\n\ndef test_service_done_status_constant() -> None:\n"
            + "    from tiny_service.service import DONE_STATUS\n"
            + '    assert DONE_STATUS == "done"\n',
        },
    )
    _commit_worker_edit(
        service_dir,
        message="service: add DONE_STATUS",
        edits={
            "tiny_service/service.py": service_source.rstrip() + '\n\nDONE_STATUS = "done"\n',
        },
    )

    for command in (["collect"], ["validate-worker"], ["merge-grid"]):
        result = runner.invoke(app, command, color=False)
        assert result.exit_code == 0, result.output

    report = json.loads((project / ".gaijinn/merge/report.json").read_text(encoding="utf-8"))
    governance = load_merge_governance(project)
    assert governance is not None
    structural = governance["structural_score"]

    assert report["summary"]["merged"] == 2
    assert report["summary"]["blocked"] == 0
    assert report["merge_order"] == [service_worker, tests_worker]
    assert structural["convergence"] == 1.0
    assert structural["merge_order_valid"] is True

    _git(project, "checkout", INTEGRATION_BRANCH, check=True)
    pytest = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(project),
        env=_project_test_env(project),
        text=True,
        capture_output=True,
        check=False,
    )
    assert pytest.returncode == 0, pytest.stdout + pytest.stderr


def test_validate_worker_defers_tests_for_sibling_dependencies(tmp_path: Path, monkeypatch) -> None:
    """Worker owning tests that depend on sibling service defers pytest pre-merge."""
    project = _bootstrap_tiny_merge_repo(tmp_path, blueprint=_tests_depend_on_service_blueprint())
    monkeypatch.chdir(project)

    manifest = json.loads((project / ".gaijinn/workers/manifest.json").read_text(encoding="utf-8"))
    tests_worker = next(
        detail["worker_id"]
        for detail in manifest["worker_details"]
        if "WU-001" in detail.get("assigned_work_units", [])
    )
    service_worker = next(
        detail["worker_id"]
        for detail in manifest["worker_details"]
        if "WU-002" in detail.get("assigned_work_units", [])
    )

    tests_dir = project / ".gaijinn/workers" / tests_worker
    service_dir = project / ".gaijinn/workers" / service_worker

    test_source = (tests_dir / "tests/test_api.py").read_text(encoding="utf-8")
    service_source = (service_dir / "tiny_service/service.py").read_text(encoding="utf-8")

    _commit_worker_edit(
        tests_dir,
        message="tests: assert DONE_STATUS from service",
        edits={
            "tests/test_api.py": test_source
            + "\n\n\ndef test_service_done_status_constant() -> None:\n"
            + "    from tiny_service.service import DONE_STATUS\n"
            + '    assert DONE_STATUS == "done"\n',
        },
    )
    _commit_worker_edit(
        service_dir,
        message="service: add DONE_STATUS",
        edits={
            "tiny_service/service.py": service_source.rstrip() + '\n\nDONE_STATUS = "done"\n',
        },
    )
    # Service worker's log should not contain "build PASS" so validate-worker
    # runs real tests instead of mock-completed gate.
    (service_dir / "output.log").write_text("build completed; tests pending\n", encoding="utf-8")

    collect = runner.invoke(app, ["collect"], color=False)
    assert collect.exit_code == 0, collect.output
    validate = runner.invoke(app, ["validate-worker"], color=False)
    assert validate.exit_code == 0, validate.output

    validated = json.loads((project / ".gaijinn/merge/validated.json").read_text(encoding="utf-8"))
    tests_gate = validated[tests_worker]["gates"]["tests"]
    service_gate = validated[service_worker]["gates"]["tests"]

    assert validated[tests_worker]["passed"] is True
    assert tests_gate["deferred"] is True
    assert tests_gate["reason"] == "awaiting_sibling_merge"
    assert tests_gate["awaiting_units"] == ["WU-002"]
    assert tests_gate["awaiting_workers"] == [service_worker]
    assert tests_gate["ran"] is False

    assert validated[service_worker]["passed"] is True
    assert service_gate.get("deferred") is not True
    assert service_gate["ran"] is True
    assert service_gate["passed"] is True


def test_scope_changed_for_giv_excludes_handoff_artifacts() -> None:
    from aoc_cli.giv import GIV
    from aoc_cli.helpers.merge import detect_trespasses, scope_changed_for_giv

    changed = [
        "tiny_service/router.py",
        "WORK_UNIT.md",
        "giv.json",
        "output.log",
    ]
    assert scope_changed_for_giv(changed) == ["tiny_service/router.py"]
    giv = GIV(worker_id="worker-001", allowed_paths=("tiny_service/router.py",))
    assert detect_trespasses(changed, giv) == []
