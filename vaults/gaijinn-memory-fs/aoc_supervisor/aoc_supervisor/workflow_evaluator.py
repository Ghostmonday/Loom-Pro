"""Workflow evaluator — measurable confusion checks for mirror UI smoke tests.

GAIJINN BLUEPRINT — evaluation / confusion metric
-------------------------------------------------
Layer: Mirror tests (Python); scores what terminal *should* show
Status: partial — prepare/swarm/grid/merge checks shipped; browser not executed here
Optimization: confusion_count == 0 (see ui/gaijinn-ui-intent-map.json)
Driver: ui_intent.UiIntentDriver replays API; terminal uses assertUiConsistency()

This module is the **scoreboard** for autonomous iteration (Codex tasks).
Do not polish CSS to pass — fix state sync between API payloads and UI spec.

Invariant sources (keep in sync):
  - state_machine.invariants in intent map
  - confusion_signals list in intent map
  - tests/test_workflow_evaluator.py scenarios

Gaps (planned, not coded)
  - Browser-side Playwright replay (optional; mirror driver is canonical)
  - Per-subphase invariant matrix (choosing_swarm vs deploying_workers)

Robustness path
  - Add InvariantResult per intent-map invariant id
  - Export JSON report for Codex --output-last-message summaries
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PERF_RESULTS_PATH = Path(".gaijinn/perf-bench-results.json")
HUMAN_SIGNOFF_PATH = Path(".gaijinn/human-signoff.md")

PKM_INTENT = (
    "Build a local-first personal knowledge manager for Linux that indexes PDFs, "
    "Markdown files, and audio transcripts, supports semantic search, and exposes "
    "a desktop UI. Must be offline-only and privacy-preserving."
)


@dataclass
class InvariantResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class WorkflowEvaluation:
    scenario_id: str
    passed: bool
    confusion_count: int
    invariants: list[InvariantResult] = field(default_factory=list)
    gate_mirror_passed: bool = True
    promotion_passed: bool = True

    def confusion_score(self) -> int:
        """Lower is better — count of failed sync/product invariants."""
        return self.confusion_count


def _check(name: str, ok: bool, detail: str = "") -> InvariantResult:
    return InvariantResult(name=name, passed=ok, detail=detail)


def evaluate_prepare(payload: Mapping[str, Any], *, intent: str, greenfield: bool = False) -> list[InvariantResult]:
    results: list[InvariantResult] = []
    work_units = int(payload.get("work_units", 0))
    recommended = int(payload.get("recommended_swarm", 0))
    rationale = str(payload.get("swarm_rationale", ""))
    streams = payload.get("work_stream_titles") or []
    mode = str(payload.get("blueprint_mode", ""))

    results.append(_check("prepare.session_id", bool(payload.get("session_id"))))
    results.append(_check("prepare.work_units_positive", work_units >= 1, f"work_units={work_units}"))
    results.append(_check("prepare.rationale_present", bool(rationale), rationale or "missing"))
    results.append(_check("prepare.recommended_matches_streams", recommended >= 1))

    if greenfield or mode == "intent":
        results.append(_check("prepare.intent_blueprint_mode", mode == "intent", f"mode={mode}"))
        results.append(_check("prepare.greenfield_stream_count", work_units >= 4, f"work_units={work_units}"))
        results.append(_check("prepare.streams_listed", len(streams) >= 4, f"streams={len(streams)}"))
        results.append(
            _check(
                "prepare.recommended_not_tiny_for_complex_intent",
                recommended >= min(work_units, 6),
                f"recommended={recommended} work_units={work_units}",
            )
        )
        tiny_paths = any("tiny_service" in str(title).lower() for title in streams)
        results.append(_check("prepare.not_template_scan_titles", not tiny_paths, "tiny_service titles detected"))

    return results


def evaluate_swarm(payload: Mapping[str, Any], *, workers: int) -> list[InvariantResult]:
    work_units = int(payload.get("work_units", workers))
    warning = payload.get("swarm_warning")
    idle = int(payload.get("idle_agents", 0))
    results = [
        _check("swarm.workers_ready", int(payload.get("workers_ready", 0)) == workers, str(payload)),
        _check("swarm.phase_ready", payload.get("phase") == "ready_to_deploy"),
    ]
    if workers > work_units:
        results.append(_check("swarm.warns_on_idle", bool(warning), str(warning)))
        results.append(_check("swarm.idle_count_correct", idle == workers - work_units, f"idle={idle}"))
    else:
        results.append(_check("swarm.no_idle_warning", not warning))
        results.append(_check("swarm.all_agents_productive", idle == 0, f"idle={idle}"))
    return results


def evaluate_grid_status(
    payload: Mapping[str, Any],
    *,
    workers: int,
    sprint_id: str,
) -> list[InvariantResult]:
    results: list[InvariantResult] = []
    worker_rows = list(payload.get("workers") or [])
    results.append(_check("grid.status_worker_count", len(worker_rows) >= workers, f"got={len(worker_rows)}"))
    for index, row in enumerate(worker_rows[:workers]):
        name = row.get("name", f"worker-{index}")
        for key in ("assigned_work_units", "spawned", "has_output"):
            results.append(_check(f"grid.{name}.{key}", key in row, str(row)))
    sprint = payload.get("sprint") or {}
    if sprint:
        results.append(_check("grid.sprint_id_matches", str(sprint.get("sprint_id", sprint_id)) == str(sprint_id)))
    return results


def evaluate_sprint_complete(
    workers: list[Mapping[str, Any]],
    *,
    workers_requested: int,
    allow_idle: bool = False,
) -> list[InvariantResult]:
    results: list[InvariantResult] = []
    rows = workers[:workers_requested]
    for index, row in enumerate(rows):
        name = str(row.get("name", f"worker-{index}"))
        units = row.get("assigned_work_units") or []
        status = str(row.get("status", ""))
        if units:
            results.append(_check(f"worker.{name}.completed_with_work", status == "completed", status))
        elif not allow_idle:
            results.append(_check(f"worker.{name}.idle_not_completed", status != "completed", status))
    return results


def evaluate_merge(payload: Mapping[str, Any]) -> list[InvariantResult]:
    merge = payload.get("merge_pipeline", payload)
    if not isinstance(merge, Mapping):
        merge = {}
    phase = str(merge.get("phase", ""))
    merged = int(merge.get("merged", 0) or 0)
    blocked = int(merge.get("blocked", 0) or 0)
    conflicted = int(merge.get("conflicted", 0) or 0)
    validated = int(merge.get("validated", 0) or 0)
    results = [
        _check("merge.phase_completed", phase == "completed", f"phase={phase}"),
        _check("merge.validated_workers", validated >= 1, f"validated={validated}"),
        _check("merge.merged_work", merged >= 1, f"merged={merged}"),
        _check("merge.no_blocked", blocked == 0, f"blocked={blocked}"),
        _check("merge.no_conflicted", conflicted == 0, f"conflicted={conflicted}"),
    ]
    structural = merge.get("structural_score")
    if not isinstance(structural, Mapping):
        structural = payload.get("structural_score") if isinstance(payload.get("structural_score"), Mapping) else None
    if isinstance(structural, Mapping):
        convergence = float(structural.get("convergence", 0) or 0)
        dry_run = bool(structural.get("dry_run"))
        min_convergence = 0.875 if dry_run else 1.0
        results.extend(
            [
                _check(
                    "merge.structural_convergence",
                    convergence >= min_convergence,
                    f"convergence={convergence} dry_run={dry_run}",
                ),
                _check(
                    "merge.handoff_isolation",
                    bool(structural.get("handoff_isolation")),
                    str(structural.get("handoff_isolation")),
                ),
                _check(
                    "merge.order_valid",
                    bool(structural.get("merge_order_valid")),
                    str(structural.get("merge_order_valid")),
                ),
            ]
        )
    return results


def evaluate_perf_gate(*, results_path: Path | None = None) -> list[InvariantResult]:
    path = results_path or PERF_RESULTS_PATH
    if not path.exists():
        return [_check("gate.perf_results_present", False, f"missing {path}")]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [_check("gate.perf_results_valid", False, str(exc))]
    passed = bool(payload.get("passed", False))
    failed_checks = [item for item in payload.get("checks", []) if not item.get("passed")]
    return [
        _check("gate.perf_bench_passed", passed, f"failed={len(failed_checks)}" if not passed else "passed"),
    ]


def evaluate_human_signoff_gate(
    *,
    signoff_path: Path | None = None,
    require_approved: bool = True,
) -> list[InvariantResult]:
    path = signoff_path or HUMAN_SIGNOFF_PATH
    if not path.exists():
        return [_check("gate.human_signoff_present", False, f"missing {path}")]
    text = path.read_text(encoding="utf-8")
    match = re.search(r"status:\s*(\w+)", text, re.IGNORECASE)
    status = match.group(1).lower() if match else "pending"
    approved = status == "approved"
    if require_approved:
        return [_check("gate.human_signoff_approved", approved, f"status={status}")]
    return [_check("gate.human_signoff_present", True, f"status={status}")]


def evaluate_promotion_gates(
    *,
    perf_results_path: Path | None = None,
    human_signoff_path: Path | None = None,
    require_approved: bool = True,
) -> list[InvariantResult]:
    checks: list[InvariantResult] = []
    checks.extend(evaluate_perf_gate(results_path=perf_results_path))
    checks.extend(evaluate_human_signoff_gate(signoff_path=human_signoff_path, require_approved=require_approved))
    return checks


def evaluate_workflow(
    *,
    scenario_id: str,
    prepare: Mapping[str, Any] | None = None,
    swarm: Mapping[str, Any] | None = None,
    grid_status: Mapping[str, Any] | None = None,
    workers: list[Mapping[str, Any]] | None = None,
    merge: Mapping[str, Any] | None = None,
    intent: str = "",
    workers_requested: int = 0,
    greenfield: bool = False,
    enforce_promotion_gates: bool = False,
) -> WorkflowEvaluation:
    checks: list[InvariantResult] = []
    gate_mirror_passed = True
    promotion_passed = True
    if prepare is not None:
        prepare_checks = evaluate_prepare(prepare, intent=intent, greenfield=greenfield)
        checks.extend(prepare_checks)
        gate_mirror_passed = all(item.passed for item in prepare_checks)
    if enforce_promotion_gates:
        promotion_checks = evaluate_promotion_gates()
        checks.extend(promotion_checks)
        promotion_passed = all(item.passed for item in promotion_checks)
    if swarm is not None and workers_requested:
        checks.extend(evaluate_swarm(swarm, workers=workers_requested))
    if grid_status is not None and workers_requested:
        sprint_id = str((grid_status.get("sprint") or {}).get("sprint_id", ""))
        checks.extend(evaluate_grid_status(grid_status, workers=workers_requested, sprint_id=sprint_id))
    if workers is not None and workers_requested:
        allow_idle = bool(swarm and swarm.get("swarm_warning")) if swarm else False
        checks.extend(
            evaluate_sprint_complete(
                workers,
                workers_requested=workers_requested,
                allow_idle=allow_idle,
            )
        )
    if merge is not None:
        checks.extend(evaluate_merge(merge))

    failed = [item for item in checks if not item.passed]
    return WorkflowEvaluation(
        scenario_id=scenario_id,
        passed=not failed,
        confusion_count=len(failed),
        invariants=checks,
        gate_mirror_passed=gate_mirror_passed,
        promotion_passed=promotion_passed,
    )
