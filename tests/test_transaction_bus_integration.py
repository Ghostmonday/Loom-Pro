"""Upstream integration validation for the multi-worker transaction bus contract.

Exercises collect-time handoff queue sync, validate-worker handoff_integrity,
merge-pipeline structural scoring, and preflight merge gate as one contract.
"""

from __future__ import annotations

import json
from pathlib import Path

from aoc_cli.helpers.handoff import (
    HANDOFF_TICKET_END,
    HANDOFF_TICKET_START,
    evaluate_handoff_transaction_integrity,
    sync_handoff_queue_at_collect,
)
from aoc_cli.helpers.merge import (
    HANDOFF_QUEUE_PATH,
    VALIDATED_PATH,
    compute_merge_structural_score,
    merge_pipeline_status,
    write_merge_governance,
    write_merge_json,
)
from aoc_supervisor.preflight import run_preflight_check


def _phase2_blueprint() -> dict:
    return {
        "schema_version": 1,
        "project_goal": "Phase 2 handoff proof",
        "assumptions": [],
        "work_units": [
            {
                "id": "WU-PH2-001",
                "title": "billing",
                "description": "billing gate",
                "allowed_paths": ["aoc_supervisor/aoc_supervisor/billing.py"],
                "denied_paths": [],
                "depends_on": [],
                "acceptance_checks": ["pytest"],
                "estimated_risk": "low",
            },
            {
                "id": "WU-PH2-002",
                "title": "preflight api",
                "description": "preflight api",
                "allowed_paths": [
                    "aoc_supervisor/aoc_supervisor/api.py",
                    "aoc_supervisor/aoc_supervisor/preflight.py",
                ],
                "denied_paths": [],
                "depends_on": [],
                "acceptance_checks": ["pytest"],
                "estimated_risk": "low",
            },
            {
                "id": "WU-PH2-003",
                "title": "handoff merge",
                "description": "handoff merge",
                "allowed_paths": [
                    "aoc-cli/aoc_cli/helpers/handoff.py",
                    "aoc-cli/aoc_cli/helpers/merge.py",
                ],
                "denied_paths": [],
                "depends_on": [],
                "acceptance_checks": ["pytest"],
                "estimated_risk": "low",
            },
        ],
        "dependencies": {},
        "risks": [],
    }


def _write_validated_from_integrity(
    project_root: Path,
    manifest_details: dict[str, dict],
    integrity: dict,
) -> None:
    validated: dict[str, dict] = {}
    bus_ok = integrity.get("transaction_bus_synchronized", True)
    for worker_id in manifest_details:
        validated[worker_id] = {
            "passed": bus_ok,
            "gates": {
                "path_allowlist": {"passed": True, "trespasses": []},
                "scope_isolation": {"passed": True, "violations": []},
            },
            "handoff_integrity": integrity,
        }
    write_merge_json(project_root / VALIDATED_PATH, validated)


def _setup_multi_worker_project(tmp_path: Path) -> tuple[Path, Path, dict[str, dict]]:
    project = tmp_path / "repo"
    workers = project / ".gaijinn" / "workers"
    (workers / "worker-001").mkdir(parents=True)
    (workers / "worker-002").mkdir(parents=True)
    (project / ".gaijinn" / "bridge").mkdir(parents=True)
    (project / ".gaijinn" / "merge").mkdir(parents=True)
    (project / ".gaijinn" / "blueprint.json").write_text(
        json.dumps(_phase2_blueprint()),
        encoding="utf-8",
    )
    manifest_details = {
        "worker-001": {"assigned_work_units": ["WU-PH2-003"]},
        "worker-002": {"assigned_work_units": ["WU-PH2-002"]},
    }
    write_merge_json(
        workers / "manifest.json",
        {"worker_details": [{"worker_id": worker_id, **detail} for worker_id, detail in manifest_details.items()]},
    )
    return project, workers, manifest_details


class TestTransactionBusUpstreamIntegration:
    def test_queue_sync_validate_preflight_contract_aligned(self, tmp_path: Path, monkeypatch) -> None:
        project, workers, manifest_details = _setup_multi_worker_project(tmp_path)
        ticket_log = f"""
{HANDOFF_TICKET_START}
{{
  "target_work_unit_id": "WU-PH2-002",
  "target_file": "aoc_supervisor/aoc_supervisor/api.py",
  "required_mutation_context": "wire preflight response metrics"
}}
{HANDOFF_TICKET_END}
"""
        (workers / "worker-001" / "output.log").write_text(ticket_log, encoding="utf-8")
        monkeypatch.chdir(project)
        monkeypatch.setattr("aoc_cli.helpers.handoff.ticket_is_resolved", lambda *args, **kwargs: True)

        queue = sync_handoff_queue_at_collect(
            project_root=project,
            workers_path=workers,
            manifest_details=manifest_details,
            base_ref="HEAD",
        )
        integrity = evaluate_handoff_transaction_integrity(
            project_root=project,
            workers_path=workers,
            manifest_details=manifest_details,
            base_ref="HEAD",
        )

        assert queue["transaction_bus_synchronized"] == integrity["transaction_bus_synchronized"]
        assert queue["handoff_tickets_raised"] == integrity["handoff_tickets_raised"]
        assert queue["handoff_tickets_resolved"] == integrity["handoff_tickets_resolved"]
        assert queue["pending_tickets"] == integrity["pending_tickets"]

        _write_validated_from_integrity(project, manifest_details, integrity)
        write_merge_json(
            project / ".gaijinn/merge/collected.json",
            {"collected_at": "2026-06-16T12:00:00Z", "workers": manifest_details},
        )
        write_merge_json(
            project / ".gaijinn/merge/report.json",
            {
                "completed_at": "2026-06-16T12:00:01Z",
                "dry_run": False,
                "merge_order": ["worker-001", "worker-002"],
                "workers": {
                    "worker-001": {"status": "merged"},
                    "worker-002": {"status": "merged"},
                },
                "summary": {"merged": 2, "blocked": 0, "conflicted": 0, "total": 2},
            },
        )

        score = compute_merge_structural_score(project)
        assert score.transaction_bus_synchronized is True
        write_merge_governance(project, score)
        pipeline = merge_pipeline_status(project)
        assert pipeline["structural_score"]["transaction_bus_synchronized"] is True

        for worker_id in manifest_details:
            preflight = run_preflight_check(
                session_id="sess-upstream",
                worker_id=worker_id,
                project_path=str(project),
            )
            assert preflight.allow_merge is True

    def test_unresolved_bus_blocks_merge_pipeline_and_preflight(self, tmp_path: Path, monkeypatch) -> None:
        project, workers, manifest_details = _setup_multi_worker_project(tmp_path)
        ticket_log = f"""
{HANDOFF_TICKET_START}
{{
  "target_work_unit_id": "WU-PH2-002",
  "target_file": "aoc_supervisor/aoc_supervisor/api.py",
  "required_mutation_context": "unresolved mutation"
}}
{HANDOFF_TICKET_END}
"""
        (workers / "worker-001" / "output.log").write_text(ticket_log, encoding="utf-8")
        monkeypatch.chdir(project)
        monkeypatch.setattr("aoc_cli.helpers.handoff.ticket_is_resolved", lambda *args, **kwargs: False)

        queue = sync_handoff_queue_at_collect(
            project_root=project,
            workers_path=workers,
            manifest_details=manifest_details,
            base_ref="HEAD",
        )
        integrity = evaluate_handoff_transaction_integrity(
            project_root=project,
            workers_path=workers,
            manifest_details=manifest_details,
            base_ref="HEAD",
        )
        assert queue["transaction_bus_synchronized"] is False

        _write_validated_from_integrity(project, manifest_details, integrity)
        write_merge_json(
            project / ".gaijinn/merge/collected.json",
            {"collected_at": "2026-06-16T12:00:00Z", "workers": manifest_details},
        )
        write_merge_json(
            project / ".gaijinn/merge/report.json",
            {
                "completed_at": "2026-06-16T12:00:01Z",
                "dry_run": False,
                "merge_order": ["worker-001", "worker-002"],
                "workers": {
                    "worker-001": {"status": "merged"},
                    "worker-002": {"status": "merged"},
                },
                "summary": {"merged": 2, "blocked": 0, "conflicted": 0, "total": 2},
            },
        )

        score = compute_merge_structural_score(project)
        assert score.transaction_bus_synchronized is False
        assert score.invariants["merge.transaction_bus_synchronized"] is False
        assert score.convergence < 1.0

        preflight = run_preflight_check(
            session_id="sess-blocked",
            worker_id="worker-002",
            project_path=str(project),
        )
        assert preflight.allow_merge is False
        assert preflight.pending_tickets_count == 1

        queue_payload = json.loads((project / HANDOFF_QUEUE_PATH).read_text(encoding="utf-8"))
        assert queue_payload["handoff_tickets_raised"] == 1
        assert queue_payload["handoff_tickets_resolved"] == 0
