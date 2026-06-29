from __future__ import annotations

import json
from pathlib import Path

from aoc_cli.errors import ConflictError
from aoc_cli.giv import GIV
from aoc_cli.helpers.merge import (
    classify_worker_status,
    compute_merge_structural_score,
    detect_trespasses,
    format_structural_score_council_message,
    merge_pipeline_status,
    merge_worker_breakdown,
    parse_conflict_files_from_error,
    scan_denied_command_violations,
    scope_changed_for_giv,
    sibling_dependency_deferral,
    unit_owner_map,
    worker_merge_order,
    write_merge_governance,
    write_merge_json,
)


def _sample_giv() -> GIV:
    return GIV(
        worker_id="worker-001",
        allowed_paths=("src/",),
        denied_paths=(".gaijinn/",),
    )


def test_worker_status_transitions(tmp_path: Path) -> None:
    worker_dir = tmp_path / "worker-001"
    worker_dir.mkdir()
    (worker_dir / "WORK_UNIT.md").write_text("# work", encoding="utf-8")
    giv = _sample_giv()

    assert classify_worker_status(worker_dir, giv, "HEAD") == "pending"

    (worker_dir / "output.log").write_text("FAILED (exit 1)\n", encoding="utf-8")
    assert classify_worker_status(worker_dir, giv, "HEAD") == "blocked"


def test_detect_trespasses_flags_out_of_scope_paths() -> None:
    giv = _sample_giv()
    trespasses = detect_trespasses(["src/ok.py", "docs/bad.md"], giv)
    assert trespasses == ["docs/bad.md"]


def test_worker_merge_order_respects_depends_on() -> None:
    from aoc_cli.blueprint import Blueprint, WorkUnit

    units = (
        WorkUnit(
            id="WU-001",
            title="first",
            description="a",
            allowed_paths=("a/",),
            depends_on=(),
            acceptance_checks=("pytest",),
        ),
        WorkUnit(
            id="WU-002",
            title="second",
            description="b",
            allowed_paths=("b/",),
            depends_on=("WU-001",),
            acceptance_checks=("pytest",),
        ),
    )
    blueprint = Blueprint(
        schema_version=1,
        project_goal="goal",
        assumptions=(),
        work_units=units,
        dependencies=Blueprint.dependencies_from_units(units),
        risks=(),
    )
    details = {
        "worker-002": {"assigned_work_units": ["WU-002"]},
        "worker-001": {"assigned_work_units": ["WU-001"]},
    }
    order = worker_merge_order(["worker-002", "worker-001"], details, blueprint)
    assert order == ["worker-001", "worker-002"]


def test_merge_report_generation_round_trip(tmp_path: Path) -> None:
    report_path = tmp_path / ".gaijinn" / "merge" / "report.json"
    payload = {
        "integration_branch": "gaijinn/integration",
        "base_ref": "main",
        "completed_at": "2026-06-15T00:00:00Z",
        "workers": {
            "worker-001": {"status": "merged", "merge_commit": "abc123"},
            "worker-002": {"status": "conflicted", "conflict_files": ["src/api.py"]},
        },
        "summary": {"merged": 1, "blocked": 0, "conflicted": 1, "total": 2},
    }
    write_merge_json(report_path, payload)
    loaded = json.loads(report_path.read_text(encoding="utf-8"))
    assert loaded["summary"]["conflicted"] == 1
    assert loaded["workers"]["worker-002"]["conflict_files"] == ["src/api.py"]


def test_merge_pipeline_status_reads_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    merge_dir = tmp_path / ".gaijinn" / "merge"
    merge_dir.mkdir(parents=True)
    write_merge_json(
        merge_dir / "collected.json",
        {"workers": {"worker-001": {}, "worker-002": {}}},
    )
    write_merge_json(
        merge_dir / "validated.json",
        {"worker-001": {"passed": True}, "worker-002": {"passed": False}},
    )
    write_merge_json(
        merge_dir / "report.json",
        {"summary": {"merged": 1, "blocked": 0, "conflicted": 1, "total": 2}},
    )

    status = merge_pipeline_status(tmp_path)
    assert status["phase"] == "completed"
    assert status["collected"] == 2
    assert status["validated"] == 2
    assert status["validated_passed"] == 1
    assert status["merged"] == 1
    assert status["conflicted"] == 1
    assert status["workers"]
    assert status["workers"][0]["worker_id"] == "worker-001"


def test_merge_worker_breakdown_merges_validation_and_report(tmp_path: Path) -> None:
    merge_dir = tmp_path / ".gaijinn" / "merge"
    merge_dir.mkdir(parents=True)
    write_merge_json(
        merge_dir / "validated.json",
        {
            "worker-001": {"passed": True, "gates": {"path_allowlist": {"passed": True}}},
            "worker-002": {"passed": False, "gates": {"tests": {"passed": False}}},
        },
    )
    write_merge_json(
        merge_dir / "report.json",
        {
            "workers": {
                "worker-001": {"status": "merged"},
                "worker-002": {"status": "conflicted", "conflict_files": ["src/api.py"]},
            },
            "summary": {"merged": 1, "blocked": 0, "conflicted": 1, "total": 2},
        },
    )

    breakdown = merge_worker_breakdown(tmp_path)
    assert [item["worker_id"] for item in breakdown] == ["worker-001", "worker-002"]
    assert breakdown[0]["passed"] is True
    assert breakdown[0]["merge_status"] == "merged"
    assert breakdown[1]["passed"] is False
    assert breakdown[1]["failed_gates"] == ["tests"]
    assert breakdown[1]["conflict_files"] == ["src/api.py"]


def test_compute_merge_structural_score_from_artifacts(tmp_path: Path) -> None:
    merge_dir = tmp_path / ".gaijinn" / "merge"
    workers_dir = tmp_path / ".gaijinn" / "workers"
    merge_dir.mkdir(parents=True)
    workers_dir.mkdir(parents=True)
    (workers_dir / "manifest.json").write_text(
        json.dumps(
            {
                "workers": ["worker-001", "worker-002"],
                "worker_details": [
                    {"worker_id": "worker-001", "assigned_work_units": ["WU-001"]},
                    {"worker_id": "worker-002", "assigned_work_units": ["WU-002"]},
                ],
            }
        ),
        encoding="utf-8",
    )
    write_merge_json(
        merge_dir / "collected.json",
        {"collected_at": "2026-06-16T10:00:00Z", "workers": {"worker-001": {}, "worker-002": {}}},
    )
    write_merge_json(
        merge_dir / "validated.json",
        {
            "worker-001": {"passed": True, "gates": {"path_allowlist": {"passed": True}}},
            "worker-002": {"passed": True, "gates": {"path_allowlist": {"passed": True}}},
        },
    )
    write_merge_json(
        merge_dir / "report.json",
        {
            "completed_at": "2026-06-16T10:00:01Z",
            "dry_run": False,
            "merge_order": ["worker-001", "worker-002"],
            "workers": {
                "worker-001": {"status": "merged", "merge_commit": "abc"},
                "worker-002": {"status": "merged", "merge_commit": "def"},
            },
            "summary": {"merged": 2, "blocked": 0, "conflicted": 0, "total": 2},
        },
    )
    (tmp_path / ".gaijinn" / "blueprint.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_goal": "g",
                "assumptions": [],
                "work_units": [
                    {
                        "id": "WU-001",
                        "title": "Consolidate coupling review block",
                        "description": "weld",
                        "allowed_paths": ["a.py"],
                        "denied_paths": [],
                        "depends_on": [],
                        "acceptance_checks": ["pytest"],
                        "estimated_risk": "high",
                    },
                    {
                        "id": "WU-002",
                        "title": "second",
                        "description": "b",
                        "allowed_paths": ["b.py"],
                        "denied_paths": [],
                        "depends_on": ["WU-001"],
                        "acceptance_checks": ["pytest"],
                        "estimated_risk": "low",
                    },
                ],
                "dependencies": {"WU-001": [], "WU-002": ["WU-001"]},
                "risks": [],
            }
        ),
        encoding="utf-8",
    )

    score = compute_merge_structural_score(tmp_path)
    assert score.convergence == 1.0
    assert score.atomic_weld_units == 1
    assert score.merge_latency_ms == 1000
    assert score.merge_order == ("worker-001", "worker-002")

    write_merge_governance(tmp_path, score)
    pipeline = merge_pipeline_status(tmp_path)
    assert pipeline["structural_score"]["convergence"] == 1.0
    assert "governance_path" in pipeline

    message = format_structural_score_council_message(score, session_id="sess-1")
    assert "sess-1" in message
    assert "1.00" in message


def test_scope_changed_for_giv_filters_handoff_basenames() -> None:
    changed = ["src/a.py", "WORK_UNIT.md", "giv.json"]
    assert scope_changed_for_giv(changed) == ["src/a.py"]


def test_path_is_allowed_prefers_explicit_allow_over_broad_deny() -> None:
    giv = _sample_giv()
    giv = GIV(
        worker_id="worker-001",
        allowed_paths=("tests/test_api.py",),
        denied_paths=("tests",),
    )
    assert detect_trespasses(["tests/test_api.py"], giv) == []


def test_scan_denied_command_ignores_grid_spawn_prompt_header() -> None:
    log = """=== GAIJINN GRID SPAWN: worker-002 ===
GIT PUSH: DENIED — do not attempt to push to remote
============================================================

Implemented service changes successfully.
"""
    assert scan_denied_command_violations(log, ("git push",)) == []


def test_sibling_denied_paths_returns_other_workers_allowed_paths() -> None:
    from aoc_cli.blueprint import WorkUnit
    from aoc_cli.helpers.workers import _sibling_denied_paths

    assignments = {
        1: (WorkUnit(id="WU-001", title="router", description="a", allowed_paths=("tiny_service/router.py",)),),
        2: (WorkUnit(id="WU-002", title="service", description="b", allowed_paths=("tiny_service/service.py",)),),
        3: (WorkUnit(id="WU-003", title="tests", description="c", allowed_paths=("tests/test_tiny.py",)),),
    }

    assert _sibling_denied_paths(1, assignments) == ("tests/test_tiny.py", "tiny_service/service.py")


def test_worker_giv_denies_and_serializes_sibling_paths() -> None:
    from aoc_cli.blueprint import WorkUnit
    from aoc_cli.helpers.workers import _worker_giv

    base = GIV(worker_id="base", allowed_paths=("tiny_service/",), denied_paths=(".env",))
    assignments = {
        1: (WorkUnit(id="WU-001", title="router", description="a", allowed_paths=("tiny_service/router.py",)),),
        2: (WorkUnit(id="WU-002", title="service", description="b", allowed_paths=("tiny_service/service.py",)),),
    }

    worker_giv = _worker_giv(base, "worker-001", assignments[1], assignments)
    payload = worker_giv.to_dict()

    assert "tiny_service/service.py" in worker_giv.denied_paths
    assert worker_giv.sibling_denied_paths == ("tiny_service/service.py",)
    assert payload["sibling_denied_paths"] == ["tiny_service/service.py"]


def test_build_task_prompt_contains_scope_tokens_and_sibling_denied_bullets() -> None:
    from aoc_cli.commands.grid_spawn import _build_task_prompt

    prompt = _build_task_prompt(
        "worker-001",
        "# WU-001\nImplement router changes.",
        {
            "allowed_paths": ["tiny_service/router.py"],
            "denied_paths": ["tiny_service/service.py"],
            "sibling_denied_paths": ["tiny_service/service.py"],
            "structural_tokens": {
                "scope_strict": True,
                "no_sibling_trespass": True,
                "handoff_only": True,
            },
        },
        {"assigned_work_units": ["WU-001"]},
        blueprint={
            "work_units": [
                {"id": "WU-001", "allowed_paths": ["tiny_service/router.py"]},
                {"id": "WU-002", "allowed_paths": ["tiny_service/service.py"]},
            ]
        },
    )

    assert "GAIJINN_TOKENS: SCOPE_STRICT, NO_SIBLING_TRESPASS, HANDOFF_ONLY" in prompt
    assert "- tiny_service/service.py (OWNED BY SIBLING WORKER)" in prompt
    assert "ASSIGNED WORK UNITS: WU-001" in prompt
    assert "GAIJINN_HANDOFF_TICKET_START" in prompt


def test_conflict_detection_parses_files_from_error() -> None:
    error = ConflictError(
        "merge conflict",
        cause="conflicted files: src/api.py, src/service.py",
    )
    assert parse_conflict_files_from_error(error) == ["src/api.py", "src/service.py"]


def test_unit_owner_map_from_manifest_details() -> None:
    details = {
        "worker-001": {"assigned_work_units": ["WU-001", "WU-003"]},
        "worker-002": {"assigned_work_units": ["WU-002"]},
    }
    assert unit_owner_map(details) == {
        "WU-001": "worker-001",
        "WU-003": "worker-001",
        "WU-002": "worker-002",
    }


def test_sibling_dependency_deferral_when_dep_owned_by_other_worker() -> None:
    from aoc_cli.blueprint import Blueprint, WorkUnit

    units = (
        WorkUnit(
            id="WU-001",
            title="tests",
            description="a",
            allowed_paths=("tests/",),
            depends_on=("WU-002", "WU-003"),
            acceptance_checks=("pytest",),
        ),
        WorkUnit(
            id="WU-002",
            title="service",
            description="b",
            allowed_paths=("tiny_service/service.py",),
            depends_on=(),
            acceptance_checks=("pytest",),
        ),
        WorkUnit(
            id="WU-003",
            title="api",
            description="c",
            allowed_paths=("tiny_service/api.py",),
            depends_on=("WU-002",),
            acceptance_checks=("pytest",),
        ),
    )
    blueprint = Blueprint(
        schema_version=1,
        project_goal="goal",
        assumptions=(),
        work_units=units,
        dependencies=Blueprint.dependencies_from_units(units),
        risks=(),
    )
    details = {
        "worker-001": {"assigned_work_units": ["WU-001", "WU-003"]},
        "worker-002": {"assigned_work_units": ["WU-002"]},
    }

    defer, units, workers = sibling_dependency_deferral(
        "worker-001",
        details["worker-001"],
        details,
        blueprint,
    )
    assert defer is True
    assert units == ["WU-002"]
    assert workers == ["worker-002"]

    no_defer, _, _ = sibling_dependency_deferral(
        "worker-002",
        details["worker-002"],
        details,
        blueprint,
    )
    assert no_defer is False


def test_compute_merge_structural_score_uses_report_merge_order_not_sorted_keys(tmp_path: Path) -> None:
    """sort_keys on report JSON must not scramble actual merge sequence for governance."""
    merge_dir = tmp_path / ".gaijinn" / "merge"
    workers_dir = tmp_path / ".gaijinn" / "workers"
    merge_dir.mkdir(parents=True)
    workers_dir.mkdir(parents=True)
    (workers_dir / "manifest.json").write_text(
        json.dumps(
            {
                "workers": ["worker-001", "worker-002"],
                "worker_details": [
                    {"worker_id": "worker-001", "assigned_work_units": ["WU-001"]},
                    {"worker_id": "worker-002", "assigned_work_units": ["WU-002"]},
                ],
            }
        ),
        encoding="utf-8",
    )
    write_merge_json(
        merge_dir / "validated.json",
        {
            "worker-001": {"passed": True, "gates": {"path_allowlist": {"passed": True}}},
            "worker-002": {"passed": True, "gates": {"path_allowlist": {"passed": True}}},
        },
    )
    write_merge_json(
        merge_dir / "report.json",
        {
            "completed_at": "2026-06-16T10:00:01Z",
            "dry_run": False,
            "merge_order": ["worker-002", "worker-001"],
            "workers": {
                "worker-001": {"status": "merged"},
                "worker-002": {"status": "merged"},
            },
            "summary": {"merged": 2, "blocked": 0, "conflicted": 0, "total": 2},
        },
    )

    (tmp_path / ".gaijinn" / "blueprint.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_goal": "g",
                "assumptions": [],
                "work_units": [
                    {
                        "id": "WU-001",
                        "title": "tests",
                        "description": "a",
                        "allowed_paths": ["tests/"],
                        "denied_paths": [],
                        "depends_on": ["WU-002"],
                        "acceptance_checks": ["pytest"],
                        "estimated_risk": "low",
                    },
                    {
                        "id": "WU-002",
                        "title": "service",
                        "description": "b",
                        "allowed_paths": ["tiny_service/"],
                        "denied_paths": [],
                        "depends_on": [],
                        "acceptance_checks": ["pytest"],
                        "estimated_risk": "low",
                    },
                ],
                "dependencies": {"WU-001": ["WU-002"], "WU-002": []},
                "risks": [],
            }
        ),
        encoding="utf-8",
    )

    score = compute_merge_structural_score(tmp_path)
    assert score.merge_order == ("worker-002", "worker-001")
    assert score.merge_order_valid is True


def test_sibling_dependency_deferral_skips_same_worker_deps() -> None:
    from aoc_cli.blueprint import Blueprint, WorkUnit

    units = (
        WorkUnit(
            id="WU-001",
            title="first",
            description="a",
            allowed_paths=("a/",),
            depends_on=(),
            acceptance_checks=("pytest",),
        ),
        WorkUnit(
            id="WU-002",
            title="second",
            description="b",
            allowed_paths=("b/",),
            depends_on=("WU-001",),
            acceptance_checks=("pytest",),
        ),
    )
    blueprint = Blueprint(
        schema_version=1,
        project_goal="goal",
        assumptions=(),
        work_units=units,
        dependencies=Blueprint.dependencies_from_units(units),
        risks=(),
    )
    details = {"worker-001": {"assigned_work_units": ["WU-001", "WU-002"]}}

    defer, units, workers = sibling_dependency_deferral(
        "worker-001",
        details["worker-001"],
        details,
        blueprint,
    )
    assert defer is False
    assert units == []
    assert workers == []
