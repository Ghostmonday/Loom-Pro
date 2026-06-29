"""Workflow evaluator — measurable confusion for mirror smoke tests."""

from __future__ import annotations

from aoc_supervisor.workflow_evaluator import PKM_INTENT, evaluate_merge, evaluate_prepare, evaluate_workflow


def test_prepare_greenfield_pkm_invariants_pass() -> None:
    from aoc_supervisor.orchestrate_session import _recommend_swarm, detect_intent_streams, swarm_rationale

    streams = detect_intent_streams(PKM_INTENT)
    work_units = 3
    payload = {
        "session_id": "test",
        "work_units": work_units,
        "high_risk_units": 1,
        "recommended_swarm": _recommend_swarm(work_units, intent_mode=False),
        "swarm_rationale": swarm_rationale(streams, _recommend_swarm(work_units, intent_mode=False)),
        "work_stream_titles": ["python low-risk changes in tiny_service"],
        "blueprint_mode": "graph",
    }
    results = evaluate_prepare(payload, intent=PKM_INTENT, greenfield=True)
    failed = [r for r in results if not r.passed]
    assert not failed, [(r.name, r.detail) for r in failed]


def test_pkm_workflow_zero_confusion_mock(mock_grid_client) -> None:  # noqa: ARG001
    client, _workers, _tmp, _store = mock_grid_client
    from aoc_supervisor.ui_intent import UiIntentDriver

    driver = UiIntentDriver(client)
    observation = driver.run_smoke_scenario("flow.pkm_greenfield_intent")
    evaluation = driver.evaluate_scenario(
        "flow.pkm_greenfield_intent",
        observation,
        workers=3,
    )
    assert observation.status == "completed"
    assert observation.merge is not None
    assert observation.merge["merge_pipeline"]["phase"] == "completed"
    assert evaluation.confusion_score() == 0, [
        (item.name, item.detail) for item in evaluation.invariants if not item.passed
    ]


def test_evaluate_merge_happy_path() -> None:
    results = evaluate_merge(
        {
            "merge_pipeline": {
                "phase": "completed",
                "validated": 2,
                "merged": 2,
                "blocked": 0,
                "conflicted": 0,
            }
        }
    )
    assert all(item.passed for item in results)


def test_evaluate_workflow_detects_oversubscribed_swarm() -> None:
    evaluation = evaluate_workflow(
        scenario_id="oversubscribe",
        swarm={
            "work_units": 3,
            "workers_ready": 16,
            "phase": "ready_to_deploy",
            "swarm_warning": None,
            "idle_agents": 0,
        },
        workers_requested=16,
    )
    assert evaluation.confusion_count >= 1
    assert any(item.name == "swarm.warns_on_idle" and not item.passed for item in evaluation.invariants)
