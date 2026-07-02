"""Focused coverage for ui_intent handler blocks and scenario edge paths."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from aoc_supervisor.adaptive_question_engine import set_default_provider
from aoc_supervisor.intent_forge_service import IntentForgeService
from aoc_supervisor.repo_paths import LOOM_PIPELINE_INTENT_MAP_PATH
from aoc_supervisor.ui_intent import SprintObservation, UiIntentDriver
from fastapi.testclient import TestClient

from tests.fixtures.fake_reasoning_provider import (
    ScriptedFakeReasoningProvider,
    divergence_script,
)


def _headers(*, user_id: str = "alice") -> dict[str, str]:
    return {"X-User-Id": user_id, "Content-Type": "application/json"}


@pytest.fixture
def forge_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import aoc_supervisor.api as api

    monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
    monkeypatch.setenv("GAIJINN_FAKE_REASONING", "1")
    monkeypatch.setenv("GAIJINN_ALLOW_INSECURE_LOCAL", "1")
    monkeypatch.setenv("GAIJINN_SEED_TERMINAL_USER", "1")
    monkeypatch.setattr(api, "ROOT_DIR", tmp_path)
    api._intent_forge_service = IntentForgeService(tmp_path)
    with TestClient(api.app) as client:
        set_default_provider(ScriptedFakeReasoningProvider(script=divergence_script()))
        yield client, api._intent_forge_service


@pytest.fixture
def forge_driver(forge_client) -> UiIntentDriver:
    client, _service = forge_client
    return UiIntentDriver(client, user_id="alice")


def _mock_http_error(monkeypatch: pytest.MonkeyPatch, driver: UiIntentDriver, status_code: int = 400) -> None:
    original_post = driver.client.post

    def failing_post(url: str, *args: Any, **kwargs: Any) -> Any:
        if "/intent-forge/" in url:
            response = MagicMock()
            response.status_code = status_code
            response.text = "simulated forge failure"
            return response
        return original_post(url, *args, **kwargs)

    monkeypatch.setattr(driver.client, "post", failing_post)


class TestForgeDispatchHandlers:
    def test_intake_uses_intent_fallback_and_default_tier(self, forge_driver: UiIntentDriver) -> None:
        data = forge_driver._dispatch_forge_intake_start_session({"intent": "Build a markdown wiki"})
        assert forge_driver.forge_session_id == data["session_id"]
        assert forge_driver.last_forge_action == "intake.start_session"
        assert forge_driver.mirror.readiness["can_handoff"] is False or data.get("current_question")

    def test_submit_answer_updates_mirror_readiness(self, forge_driver: UiIntentDriver) -> None:
        forge_driver._dispatch_forge_intake_start_session({"prompt": "Build a CRM", "tier": "paid"})
        question_id = forge_driver.mirror.current_question["question_id"]
        sid = forge_driver.forge_session_id
        assert sid

        data = forge_driver._dispatch_forge_question_submit_answer(
            sid,
            {"question_id": question_id, "answer": "OAuth2 with scoped tokens"},
        )
        assert forge_driver.last_forge_action == "question.submit_answer"
        assert forge_driver.mirror.session_status == data["session_status"]
        assert "can_handoff" in forge_driver.mirror.readiness

    def test_handoff_confirm_and_accept_compile_artifact(self, forge_driver: UiIntentDriver) -> None:
        forge_driver._dispatch_forge_intake_start_session({"prompt": "Build a CLI tool", "tier": "free"})
        sid = forge_driver.forge_session_id
        assert sid

        confirm = forge_driver._dispatch_forge_handoff_confirm(sid, {"confirmation": "Proceed"})
        assert forge_driver.last_forge_action == "handoff.confirm"
        assert forge_driver.mirror.artifact or confirm.get("artifact") is not None

        accept = forge_driver._dispatch_forge_handoff_accept(sid)
        assert accept["session_status"] == "HANDED_OFF"
        assert forge_driver.mirror.executable_projection

    def test_dispatch_loom_forge_requires_session(self, forge_driver: UiIntentDriver) -> None:
        with pytest.raises(RuntimeError, match="forge session required"):
            forge_driver.dispatch_loom_forge_action("question.submit_answer", {"answer": "x"})

    def test_dispatch_loom_forge_unknown_action(self, forge_driver: UiIntentDriver) -> None:
        forge_driver.dispatch_loom_forge_action(
            "intake.start_session",
            {"prompt": "Build a CLI note app with markdown export", "tier": "free"},
        )
        with pytest.raises(KeyError, match="unknown forge action"):
            forge_driver.dispatch_loom_forge_action("intake.unknown_action")

    def test_forge_start_session_http_error(
        self,
        forge_driver: UiIntentDriver,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _mock_http_error(monkeypatch, forge_driver)
        with pytest.raises(RuntimeError, match="forge start_session failed"):
            forge_driver._dispatch_forge_intake_start_session({"prompt": "fail", "tier": "paid"})

    def test_forge_followup_http_errors(
        self,
        forge_driver: UiIntentDriver,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        forge_driver._dispatch_forge_intake_start_session(
            {"prompt": "Build a CLI note app with markdown export", "tier": "free"},
        )
        sid = forge_driver.forge_session_id
        _mock_http_error(monkeypatch, forge_driver)

        with pytest.raises(RuntimeError, match="forge submit_answer failed"):
            forge_driver._dispatch_forge_question_submit_answer(sid, {"question_id": "q1", "answer": "a"})

        with pytest.raises(RuntimeError, match="forge confirm_handoff failed"):
            forge_driver._dispatch_forge_handoff_confirm(sid, {"confirmation": "Proceed"})

        with pytest.raises(RuntimeError, match="forge accept_handoff failed"):
            forge_driver._dispatch_forge_handoff_accept(sid)


class TestScenarioRunners:
    def test_run_smoke_scenario_api_step_updates_mirror(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        intent_map = {
            "smoke_scenarios": [
                {
                    "id": "test.api_quote",
                    "steps": [
                        {
                            "api": "POST /api/v1/quote",
                            "body": {
                                "workers": 2,
                                "agent_slots": 2,
                                "assignment_count": 2,
                                "nodes": [{"id": "n1"}],
                            },
                        }
                    ],
                }
            ]
        }
        observation = driver.run_smoke_scenario("test.api_quote", intent_map=intent_map)
        assert observation.status == "api_ok"
        assert driver.mirror.intent_forge

    def test_run_smoke_scenario_api_failure_raises(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        intent_map = {
            "smoke_scenarios": [
                {
                    "id": "test.api_fail",
                    "steps": [{"api": "POST /api/v1/orchestrate/prepare", "body": {"intent": "x", "phases": []}}],
                }
            ]
        }
        with pytest.raises(RuntimeError, match="failed 400"):
            driver.run_smoke_scenario("test.api_fail", intent_map=intent_map)

    def test_run_smoke_scenario_unknown_id_raises(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        with pytest.raises(KeyError, match="unknown smoke scenario"):
            driver.run_smoke_scenario("missing.scenario")

    def test_run_smoke_scenario_empty_steps_raises(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        intent_map = {"smoke_scenarios": [{"id": "test.empty", "steps": []}]}
        with pytest.raises(RuntimeError, match="no executable steps"):
            driver.run_smoke_scenario("test.empty", intent_map=intent_map)

    def test_run_loom_pipeline_expect_status_skips_error(
        self,
        mock_grid_client: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        monkeypatch.delenv("GAIJINN_ALLOW_RAW_INTENT_PREPARE", raising=False)
        driver = UiIntentDriver(client)
        intent_map = {
            "smoke_scenarios": [
                {
                    "id": "test.expect_status_then_prepare",
                    "steps": [
                        {
                            "api": "POST /api/v1/orchestrate/prepare",
                            "body": {"intent": "Build an app", "phases": ["backend"]},
                            "expect_status": 409,
                        },
                        {
                            "action": "orchestrate.prepare",
                            "args": {"intent": "Build a tic-tac-toe game", "phases": ["backend"]},
                        },
                    ],
                }
            ]
        }
        monkeypatch.setenv("GAIJINN_ALLOW_RAW_INTENT_PREPARE", "1")
        observation = driver.run_loom_pipeline_scenario("test.expect_status_then_prepare", intent_map=intent_map)
        assert observation.status == "prepared"
        assert observation.prepare is not None

    def test_run_loom_pipeline_interrogation_api_path(self, forge_driver: UiIntentDriver) -> None:
        intent_map = {
            "smoke_scenarios": [
                {
                    "id": "test.interrogation_paid",
                    "steps": [
                        {
                            "api": "POST /api/v1/intent-forge/sessions",
                            "body": {
                                "prompt": "Build a secure API gateway with audit logging",
                                "tier": "paid",
                            },
                        },
                        {
                            "action": "question.submit_answer",
                            "args": {"answer": "OAuth2 with scoped tokens for every endpoint."},
                        },
                    ],
                }
            ]
        }
        observation = forge_driver.run_loom_pipeline_scenario("test.interrogation_paid", intent_map=intent_map)
        assert observation.session_id
        assert forge_driver.mirror.session_status in {"QUESTIONING", "FINALIZED", "ANALYZING"}

    def test_run_loom_pipeline_repeat_until_can_handoff(self, forge_driver: UiIntentDriver) -> None:
        intent_map = {
            "smoke_scenarios": [
                {
                    "id": "test.repeat_handoff",
                    "steps": [
                        {
                            "action": "intake.start_session",
                            "args": {"prompt": "Build a notes app", "tier": "free"},
                        },
                        {
                            "action": "question.submit_answer",
                            "args": {"answer": "Offline SQLite only"},
                            "repeat_until": "readiness.can_handoff",
                        },
                    ],
                }
            ]
        }
        forge_driver.run_loom_pipeline_scenario("test.repeat_handoff", intent_map=intent_map)
        assert forge_driver.mirror.readiness.get("can_handoff") is True

    def test_run_loom_pipeline_generic_api_failure(self, forge_driver: UiIntentDriver) -> None:
        intent_map = {
            "smoke_scenarios": [
                {
                    "id": "test.bad_api",
                    "steps": [
                        {
                            "api": "POST /api/v1/intent-forge/sessions",
                            "body": {"prompt": "", "tier": "paid"},
                        }
                    ],
                }
            ]
        }
        with pytest.raises(RuntimeError, match="failed"):
            forge_driver.run_loom_pipeline_scenario("test.bad_api", intent_map=intent_map)

    def test_run_loom_pipeline_unknown_scenario_raises(self, forge_driver: UiIntentDriver) -> None:
        with pytest.raises(KeyError, match="unknown Loom pipeline scenario"):
            forge_driver.run_loom_pipeline_scenario("missing.loom")


class TestIntentActionDispatch:
    def test_full_flow_chains_prepare_swarm_deploy(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        observation = driver.full_flow("Build a tic-tac-toe game", workers=2, timeout=60)
        assert observation.status == "completed"
        assert observation.prepare is not None
        assert observation.session_id

    def test_grid_poll_status_requires_active_sprint(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        with pytest.raises(RuntimeError, match="grid.poll_status requires an active sprint"):
            driver.dispatch_intent_action("grid.poll_status")

    def test_deliverable_download_records_response_metadata(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        observation = driver.run_smoke_scenario("flow.intent_swarm_deploy_mock")
        result = driver.dispatch_intent_action(
            "deliverable.download",
            {"session_id": observation.session_id},
            observation=observation,
        )
        assert result.deliverable_status == 200
        assert "zip" in (result.deliverable_content_type or "")

    def test_chat_submit_intent_runs_full_flow(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        observation = driver.dispatch_intent_action(
            "chat.submit_intent",
            {"text": "Build a tic-tac-toe game", "workers": 2, "timeout": 60},
        )
        assert observation.status == "completed"
        assert observation.prepare is not None

    def test_wait_for_sprint_terminal_counts_worker_statuses(
        self,
        mock_grid_client: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        calls = {"n": 0}

        def fake_grid_status(_sprint_id: str) -> dict[str, Any]:
            calls["n"] += 1
            if calls["n"] == 1:
                return {
                    "sprint": {"status": "running"},
                    "workers": [
                        {"name": "worker-001", "status": "completed"},
                        {"name": "worker-002", "status": "completed"},
                    ],
                }
            return {"sprint": {"status": "running"}, "workers": []}

        monkeypatch.setattr(driver, "grid_status", fake_grid_status)
        monkeypatch.setattr("aoc_supervisor.ui_intent.time.sleep", lambda _s: None)

        observation = driver.wait_for_sprint_terminal("sprint-123", workers=2, timeout_s=5.0)
        assert observation.status == "completed"
        assert len(observation.workers) == 2

    def test_wait_for_sprint_terminal_marks_failed_when_worker_fails(
        self,
        mock_grid_client: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)

        def fake_grid_status(_sprint_id: str) -> dict[str, Any]:
            return {
                "sprint": {"status": "running"},
                "workers": [
                    {"name": "worker-001", "status": "failed"},
                    {"name": "worker-002", "status": "completed"},
                ],
            }

        monkeypatch.setattr(driver, "grid_status", fake_grid_status)
        monkeypatch.setattr("aoc_supervisor.ui_intent.time.sleep", lambda _s: None)

        observation = driver.wait_for_sprint_terminal("sprint-456", workers=2, timeout_s=1.0)
        assert observation.status == "failed"

    def test_blueprint_synthesize_updates_mirror_baseline(
        self,
        mock_grid_client: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import aoc_supervisor.api as api

        client, _workers, project_root, _store = mock_grid_client
        forge_service = IntentForgeService(project_root / "forge-synth")
        api._intent_forge_service = forge_service
        driver = UiIntentDriver(client)
        synthesize = api.synthesize_blueprint
        monkeypatch.setattr(
            api,
            "synthesize_blueprint",
            lambda request: synthesize(request, forge_service=forge_service),
        )

        driver.dispatch_loom_forge_action(
            "intake.start_session",
            {"prompt": "Build a local PKM", "tier": "free"},
        )
        driver.dispatch_loom_forge_action("handoff.confirm", {"confirmation": "Proceed"})
        driver.dispatch_loom_forge_action("handoff.accept")
        driver.collect_teleology_receipt("Build a local PKM")

        result = driver.dispatch_loom_action("blueprint.synthesize")
        assert isinstance(result, dict)
        assert driver.mirror.blueprint
        assert "dark_bridge_count" in driver.mirror.baseline

    def test_session_required_helpers_raise(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        with pytest.raises(RuntimeError, match="session_id required"):
            driver.assign_swarm(2)
        with pytest.raises(RuntimeError, match="session_id required"):
            driver.run_merge()
        with pytest.raises(RuntimeError, match="session_id required"):
            driver.merge_report()

    def test_quote_and_purchase_after_prepare(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        driver.prepare("Build a dashboard with charts and filters")
        quote = driver.quote(2)
        assert quote
        purchase = driver.purchase(2)
        assert purchase["sprint_token"]

    def test_merge_report_and_diff_after_smoke_flow(self, mock_grid_client: Any) -> None:
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client)
        observation = driver.run_smoke_scenario("flow.intent_swarm_deploy_mock")
        merge_report = driver.merge_report(observation.session_id)
        assert merge_report["report"]["summary"]["merged"] >= 1
        diff = driver.project_diff(observation.session_id)
        assert "available" in diff