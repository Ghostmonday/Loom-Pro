"""Loom C02 — Mirror Intent Forge Actions (LOOM-209 partial).

UiIntentDriver dispatches intake.start_session → question.submit_answer →
handoff.confirm → handoff.accept, syncing IntentMirrorState.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from aoc_supervisor.adaptive_question_engine import set_default_provider
from aoc_supervisor.intent_forge_service import IntentForgeService
from aoc_supervisor.repo_paths import LOOM_PIPELINE_INTENT_MAP_PATH
from aoc_supervisor.ui_intent import UiIntentDriver
from fastapi.testclient import TestClient

from tests.fixtures.fake_reasoning_provider import (
    ScriptedFakeReasoningProvider,
    divergence_script,
)


def _headers(*, user_id: str = "alice") -> dict[str, str]:
    return {"X-User-Id": user_id, "Content-Type": "application/json"}


@pytest.fixture
def forge_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Intent Forge API client with isolated storage and deterministic reasoning."""
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
def driver(forge_client) -> UiIntentDriver:
    client, _service = forge_client
    return UiIntentDriver(client, user_id="alice")


class TestLoomMirrorForgeActions:
    """C02: mirror forge actions through UiIntentDriver."""

    def test_forge_mirror_start_session(self, driver: UiIntentDriver) -> None:
        """intake.start_session creates a forge session and sets mirror state."""
        data = driver.dispatch_loom_forge_action(
            "intake.start_session",
            {"prompt": "Build a CLI note app with markdown export", "tier": "paid"},
        )
        assert driver.forge_session_id
        assert "session_id" in data
        assert data["session_status"] in ("CREATED", "QUESTIONING", "ANALYZING")
        assert driver.mirror.session_status == data["session_status"]
        assert driver.mirror.intent_forge.get("session_id") == data["session_id"]
        assert driver.mirror.current_question

    def test_forge_mirror_submit_answer(self, driver: UiIntentDriver) -> None:
        """question.submit_answer submits to an active session and updates mirror."""
        driver.dispatch_loom_forge_action(
            "intake.start_session",
            {"prompt": "Build a markdown note app", "tier": "paid"},
        )
        first_q = driver.mirror.current_question
        assert first_q.get("question_id")

        data = driver.dispatch_loom_forge_action(
            "question.submit_answer",
            {"question_id": first_q["question_id"], "answer": "OAuth2 with JWT"},
        )
        assert driver.mirror.session_status == data["session_status"]
        assert driver.mirror.intent_forge.get("session_id") == driver.forge_session_id

    def test_full_forge_handoff_flow(self, driver: UiIntentDriver) -> None:
        """Free tier → confirm → accept → HANDED_OFF with mirror state.

        Free tier auto-finalizes (seed_free_tier populates domains), then
        confirm compiles artifact + executable_projection, accept sets HANDED_OFF.
        """
        # 1. Start free-tier session (auto-finalizes)
        init = driver.dispatch_loom_forge_action(
            "intake.start_session",
            {"prompt": "Build a CLI note app", "tier": "free"},
        )
        assert init.get("session_status") in ("CREATED", "FINALIZED")
        assert driver.mirror.session_status in ("CREATED", "FINALIZED")
        assert driver.mirror.intent_forge.get("session_id")

        # 2. Confirm handoff — artifact + executable_projection compiled
        driver.dispatch_loom_forge_action(
            "handoff.confirm",
            {"confirmation": "Proceed with architecture"},
        )
        assert driver.mirror.session_status == "FINALIZED"
        assert driver.mirror.artifact
        assert driver.mirror.executable_projection

        # 3. Accept handoff → HANDED_OFF
        accept = driver.dispatch_loom_forge_action("handoff.accept")
        assert accept["session_status"] == "HANDED_OFF"
        assert driver.mirror.session_status == "HANDED_OFF"
        assert driver.mirror.executable_projection


def test_handoff_to_prepare(driver: UiIntentDriver) -> None:
    """Loom scenario passes the handed-off forge session through prepare."""
    intent_map = json.loads(LOOM_PIPELINE_INTENT_MAP_PATH.read_text(encoding="utf-8"))
    scenario_map = deepcopy(intent_map)
    scenario = next(item for item in scenario_map["smoke_scenarios"] if item["id"] == "flow.loom_handoff_to_prepare")
    # Free tier is deterministic and immediately handoff-ready; the production
    # prepare gate remains enabled and therefore proves session-id propagation.
    scenario["steps"][0]["body"]["tier"] = "free"

    observation = driver.run_loom_pipeline_scenario(
        "flow.loom_handoff_to_prepare",
        intent_map=scenario_map,
    )

    assert driver.forge_session_id
    assert driver.mirror.session_status == "HANDED_OFF"
    assert observation.session_id == driver.forge_session_id
    assert observation.prepare is not None
    assert observation.prepare.work_units >= 1
    assert observation.prepare.blueprint_mode in {"intent", "graph", "loom_synthesis"}


def test_full_pipeline_mock(
    mock_grid_client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aoc_supervisor.api as api
    import aoc_supervisor.orchestrate_session as orchestrate_session

    client, _workers, project_root, _store = mock_grid_client
    forge_service = IntentForgeService(project_root / "forge-state")
    api._intent_forge_service = forge_service
    driver = UiIntentDriver(client)
    synthesize = api.synthesize_blueprint
    monkeypatch.setattr(
        api,
        "synthesize_blueprint",
        lambda request: synthesize(request, forge_service=forge_service),
    )
    run_gaijinn = orchestrate_session._run_gaijinn

    def run_pipeline_command(root: Path, *args: str, **kwargs) -> None:
        if args and args[0] == "run-grid":
            blueprint_path = root / ".gaijinn" / "blueprint.json"
            blueprint = blueprint_path.read_text(encoding="utf-8")
            run_gaijinn(
                root,
                "init",
                "--force",
                "--no-agent-files",
                "PKM",
                **kwargs,
            )
            run_gaijinn(root, "scan", ".", **kwargs)
            run_gaijinn(root, "analyze", **kwargs)
            run_gaijinn(root, "compile-prompt", **kwargs)
            blueprint_path.write_text(blueprint, encoding="utf-8")
        run_gaijinn(root, *args, **kwargs)

    import aoc_supervisor.api as api
    monkeypatch.setitem(api._session_store.advance_phase.__globals__, "_run_gaijinn", run_pipeline_command)

    intent_map = json.loads(LOOM_PIPELINE_INTENT_MAP_PATH.read_text(encoding="utf-8"))
    scenario_map = deepcopy(intent_map)
    scenario = next(item for item in scenario_map["smoke_scenarios"] if item["id"] == "flow.loom_full_pipeline_mock")
    scenario["steps"][0]["args"]["tier"] = "free"

    observation, assertions = driver.run_and_verify_scenario(
        "flow.loom_full_pipeline_mock",
        intent_map=scenario_map,
    )
    workflow = driver.evaluate_scenario(
        "flow.loom_full_pipeline_mock",
        observation,
        workers=3,
    )

    assert all(result.passed for result in assertions)
    assert observation.prepare is not None
    assert observation.prepare.blueprint_mode == "loom_synthesis"
    assert driver.mirror.merge_pipeline["phase"] == "completed"
    assert workflow.confusion_count == 0
