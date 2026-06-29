"""Three-gate promotion pipeline — mirror, perf, human sign-off."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aoc_cli.blueprint import Blueprint, WorkUnit, stable_work_unit_id
from aoc_cli.commands.merge_grid import _sequential_merge
from aoc_cli.commands.plan import _filter_completed_work_units
from aoc_cli.errors import MergeError
from aoc_cli.helpers.merge import (
    COLLECTED_PATH,
    REPORT_PATH,
    VALIDATED_PATH,
    archive_merge_artifacts,
    completion_ledger_is_protected,
    compute_merge_structural_score,
    content_hash_for_allowed_paths,
    upsert_completion_ledger_entries,
    write_merge_json,
)
from aoc_supervisor.workflow_evaluator import (
    evaluate_human_signoff_gate,
    evaluate_perf_gate,
    evaluate_workflow,
)

ROOT = Path(__file__).resolve().parents[1]


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test User",
            *args,
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()


def _blueprint(unit: WorkUnit) -> Blueprint:
    return Blueprint(
        schema_version=1,
        project_goal="test",
        assumptions=("test",),
        work_units=(unit,),
        dependencies=Blueprint.dependencies_from_units((unit,)),
        risks=("none",),
    )


def _copy_mode_repo(tmp_path: Path, *, worker_content: str = "v1\n") -> tuple[Path, WorkUnit, str]:
    repo = tmp_path
    (repo / "pkg").mkdir()
    (repo / "pkg" / "a.py").write_text("v1\n", encoding="utf-8")
    (repo / ".gaijinn" / "workers" / "worker-001" / "pkg").mkdir(parents=True)
    (repo / ".gaijinn" / "workers" / "worker-001" / "pkg" / "a.py").write_text(worker_content, encoding="utf-8")
    _git(repo, "init")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    base_ref = _git(repo, "rev-parse", "HEAD")
    unit = WorkUnit(
        id=stable_work_unit_id(("pkg/a.py",), ("pytest",)),
        title="pkg",
        description="update pkg",
        allowed_paths=("pkg/a.py",),
        acceptance_checks=("pytest",),
        estimated_risk="low",
        domain="code",
    )
    (repo / ".gaijinn" / "blueprint.json").write_text(_blueprint(unit).to_json(), encoding="utf-8")
    manifest = {
        "worker_details": [
            {
                "worker_id": "worker-001",
                "assigned_work_units": [unit.id],
                "branch": None,
            }
        ],
        "workers": ["worker-001"],
    }
    (repo / ".gaijinn" / "workers" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    write_merge_json(repo / VALIDATED_PATH, {"worker-001": {"passed": True}})
    return repo, unit, base_ref


def test_stable_work_unit_id_is_deterministic() -> None:
    first = stable_work_unit_id(("b.py", "a.py"), ("ruff", "pytest"))
    second = stable_work_unit_id(("a.py", "b.py"), ("pytest", "ruff"))

    assert first == second
    assert first.startswith("WU-")
    assert len(first) == 11


def test_zero_delta_matching_ledger_is_already_merged(tmp_path: Path) -> None:
    repo, unit, base_ref = _copy_mode_repo(tmp_path)
    upsert_completion_ledger_entries(
        repo,
        [
            {
                "wu_id": unit.id,
                "content_hash": content_hash_for_allowed_paths(repo, unit.allowed_paths),
                "merged_at": "2026-06-18T00:00:00Z",
                "worker_id": "worker-001",
                "allowed_paths": list(unit.allowed_paths),
                "acceptance_checks": list(unit.acceptance_checks),
            }
        ],
    )
    write_merge_json(repo / COLLECTED_PATH, {"workers": {"worker-001": {"changed_files": []}}})

    report = _sequential_merge(
        project_root=repo,
        workers_path=repo / ".gaijinn" / "workers",
        validated={"worker-001": {"passed": True}},
        base_branch="main",
        base_ref=base_ref,
        dry_run=False,
        skip_tests=True,
    )

    assert report["workers"]["worker-001"]["status"] == "already_merged"
    assert report["summary"]["already_merged"] == 1
    assert report["summary"]["blocked"] == 0


def test_zero_delta_without_matching_ledger_blocks(tmp_path: Path) -> None:
    repo, _unit, base_ref = _copy_mode_repo(tmp_path)
    write_merge_json(repo / COLLECTED_PATH, {"workers": {"worker-001": {"changed_files": []}}})

    report = _sequential_merge(
        project_root=repo,
        workers_path=repo / ".gaijinn" / "workers",
        validated={"worker-001": {"passed": True}},
        base_branch="main",
        base_ref=base_ref,
        dry_run=False,
        skip_tests=True,
    )

    assert report["workers"]["worker-001"]["status"] == "blocked"
    assert report["summary"]["blocked"] == 1


def test_merge_governance_counts_already_merged_as_work(tmp_path: Path) -> None:
    write_merge_json(tmp_path / VALIDATED_PATH, {"worker-001": {"passed": True}})
    write_merge_json(
        tmp_path / REPORT_PATH,
        {
            "dry_run": False,
            "merge_order": [],
            "workers": {"worker-001": {"status": "already_merged"}},
            "summary": {"merged": 0, "already_merged": 5, "blocked": 0, "conflicted": 0, "backlog_pre_sprint": 1},
        },
    )

    score = compute_merge_structural_score(tmp_path)

    assert score.blocked_workers == 0
    assert score.invariants["merge.no_blocked"] is True
    assert score.invariants["merge.merged_work"] is True


def test_merge_governance_all_done_backlog_passes_merged_work(tmp_path: Path) -> None:
    write_merge_json(tmp_path / VALIDATED_PATH, {})
    write_merge_json(
        tmp_path / REPORT_PATH,
        {
            "dry_run": False,
            "merge_order": [],
            "workers": {},
            "summary": {"merged": 0, "already_merged": 0, "blocked": 0, "conflicted": 0, "backlog_pre_sprint": 0},
        },
    )

    assert compute_merge_structural_score(tmp_path).invariants["merge.merged_work"] is True


def test_compounding_sprint_writes_ledger_plan_drops_then_zero_delta_is_not_blocked(tmp_path: Path) -> None:
    repo, unit, base_ref = _copy_mode_repo(tmp_path, worker_content="v2\n")
    write_merge_json(repo / COLLECTED_PATH, {"workers": {"worker-001": {"changed_files": ["pkg/a.py"]}}})

    first = _sequential_merge(
        project_root=repo,
        workers_path=repo / ".gaijinn" / "workers",
        validated={"worker-001": {"passed": True}},
        base_branch="main",
        base_ref=base_ref,
        dry_run=False,
        skip_tests=True,
    )
    assert first["summary"]["merged"] == 1

    filtered = _filter_completed_work_units(repo, _blueprint(unit))
    assert filtered.work_units == ()

    write_merge_json(repo / COLLECTED_PATH, {"workers": {"worker-001": {"changed_files": []}}})
    second = _sequential_merge(
        project_root=repo,
        workers_path=repo / ".gaijinn" / "workers",
        validated={"worker-001": {"passed": True}},
        base_branch="main",
        base_ref=base_ref,
        dry_run=False,
        skip_tests=True,
    )

    assert second["workers"]["worker-001"]["status"] == "already_merged"
    assert second["summary"]["blocked"] == 0


def test_promotion_gates_perf_from_results(tmp_path: Path) -> None:
    results = tmp_path / "perf.json"
    results.write_text(
        json.dumps({"passed": True, "checks": [{"name": "perf.health_latency", "passed": True}]}),
        encoding="utf-8",
    )
    checks = evaluate_perf_gate(results_path=results)
    assert all(item.passed for item in checks)


def test_human_signoff_pending_blocks_approval(tmp_path: Path) -> None:
    signoff = tmp_path / "human-signoff.md"
    signoff.write_text("status: pending\n", encoding="utf-8")
    checks = evaluate_human_signoff_gate(signoff_path=signoff, require_approved=True)
    assert any(item.name == "gate.human_signoff_approved" and not item.passed for item in checks)


def test_human_signoff_approved_passes(tmp_path: Path) -> None:
    signoff = tmp_path / "human-signoff.md"
    signoff.write_text("status: approved\napproved_by: Amir\n", encoding="utf-8")
    checks = evaluate_human_signoff_gate(signoff_path=signoff, require_approved=True)
    assert all(item.passed for item in checks)


def test_completion_ledger_protected_when_converged(tmp_path: Path) -> None:
    merge_dir = tmp_path / ".gaijinn" / "merge"
    merge_dir.mkdir(parents=True)
    (merge_dir / "governance.json").write_text(
        json.dumps({"structural_score": {"convergence": 1.0}}),
        encoding="utf-8",
    )
    upsert_completion_ledger_entries(
        tmp_path,
        [
            {
                "wu_id": "WU-test0001",
                "content_hash": "abc",
                "merged_at": "2026-06-18T00:00:00Z",
                "worker_id": "worker-001",
                "allowed_paths": ["a.py"],
                "acceptance_checks": ["vault_linter"],
            }
        ],
        allow_wipe=True,
    )
    assert completion_ledger_is_protected(
        tmp_path, hermes_state={"converged_at": "2026-06-18T12:00:00Z", "convergence": 1.0}
    )
    try:
        write_merge_json(merge_dir / "completion-ledger.json", {"schema_version": 1, "entries": []})
        raise AssertionError("expected MergeError")
    except MergeError:
        pass


def test_archive_merge_artifacts_copies_ledger(tmp_path: Path) -> None:
    merge_dir = tmp_path / ".gaijinn" / "merge"
    merge_dir.mkdir(parents=True)
    (merge_dir / "completion-ledger.json").write_text('{"entries": [{"wu_id": "WU-x"}]}\n', encoding="utf-8")
    (merge_dir / "governance.json").write_text('{"structural_score": {"convergence": 1.0}}\n', encoding="utf-8")

    archive_dir = archive_merge_artifacts(tmp_path, label="test-archive")

    assert (archive_dir / "completion-ledger.json").exists()
    assert (archive_dir / "governance.json").exists()


def test_evaluate_workflow_with_promotion_gates(tmp_path: Path) -> None:
    perf = tmp_path / "perf.json"
    perf.write_text(json.dumps({"passed": True, "checks": []}), encoding="utf-8")
    signoff = tmp_path / "signoff.md"
    signoff.write_text("status: approved\n", encoding="utf-8")

    from aoc_supervisor import workflow_evaluator as we

    original_perf = we.PERF_RESULTS_PATH
    original_signoff = we.HUMAN_SIGNOFF_PATH
    we.PERF_RESULTS_PATH = perf
    we.HUMAN_SIGNOFF_PATH = signoff
    try:
        evaluation = evaluate_workflow(
            scenario_id="gates",
            prepare={"session_id": "s", "work_units": 2, "recommended_swarm": 2, "swarm_rationale": "ok"},
            enforce_promotion_gates=True,
        )
        assert evaluation.gate_mirror_passed
        assert evaluation.promotion_passed
    finally:
        we.PERF_RESULTS_PATH = original_perf
        we.HUMAN_SIGNOFF_PATH = original_signoff
