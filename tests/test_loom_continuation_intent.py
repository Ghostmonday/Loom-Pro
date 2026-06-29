"""LOOM-210 contract tests for Continuation and Launch Presentation maps."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
UI_DIR = REPO_ROOT / "ui"

NEW_MAPS = (
    "loom-continuation-intent-map.json",
    "loom-deliverable-intent-map.json",
)

CONTINUATION_ACTIONS = (
    "intake.attach_project",
    "intake.resume_session",
    "intake.session_kind_select",
    "graph.bootstrap",
    "interrogation.set_mode",
    "continuation.confirm_scope",
    "question.submit_answer",
    "handoff.confirm",
    "handoff.accept",
)

CONTINUATION_SMOKES = (
    "flow.loom_continuation_attach_brownfield",
    "flow.loom_continuation_v2_lineage",
    "flow.loom_continuation_skip_interrogation",
)

DELIVERABLE_SMOKES = (
    "flow.loom_launch_terminal",
    "flow.loom_launch_web",
    "flow.loom_reentry_after_launch",
)


def _load(name: str) -> dict:
    return json.loads((UI_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", NEW_MAPS)
def test_new_loom_maps_are_valid_json(name: str) -> None:
    payload = _load(name)
    assert payload["system"] == "loom"
    assert payload["parent_spec"] == "ui/loom-system-intent-map.json"


def test_continuation_required_actions_and_bindings_exist() -> None:
    actions = _load("loom-continuation-intent-map.json")["actions"]
    for action_id in CONTINUATION_ACTIONS:
        assert action_id in actions
        binding = actions[action_id]["algorithm_binding"]
        assert {"module", "entrypoint", "mode"} <= set(binding)
        assert "gap" in binding


@pytest.mark.parametrize(
    ("map_name", "required_ids"),
    (
        ("loom-continuation-intent-map.json", CONTINUATION_SMOKES),
        ("loom-deliverable-intent-map.json", DELIVERABLE_SMOKES),
    ),
)
def test_required_smoke_scenarios_are_spec_only(map_name: str, required_ids: tuple[str, ...]) -> None:
    scenarios = {item["id"]: item for item in _load(map_name)["smoke_scenarios"]}
    for scenario_id in required_ids:
        assert scenario_id in scenarios
        assert scenarios[scenario_id]["implementation_status"] == "spec_only"


def test_system_lists_continuation_and_deliverable_child_maps() -> None:
    system = _load("loom-system-intent-map.json")
    child_maps = set(system["child_maps"])
    assert "ui/loom-continuation-intent-map.json" in child_maps
    assert "ui/loom-deliverable-intent-map.json" in child_maps


def test_loom_210_ticket_and_c21_slice_are_present() -> None:
    system = _load("loom-system-intent-map.json")
    tickets = {item["id"]: item for item in system["_ai_blueprint"]["implementation_tickets"]}
    assert "LOOM-210" in tickets
    assert set(CONTINUATION_SMOKES + DELIVERABLE_SMOKES) <= set(tickets["LOOM-210"]["smoke"])

    slices = {item["id"]: item for item in system["_ai_blueprint"]["codex_slices"]}
    assert slices["C21"]["ticket"] == "LOOM-210"
    assert slices["C21"]["doc"].endswith("task-loom-c21-continuation-launch-intent-map.md")


@pytest.mark.parametrize("name", NEW_MAPS)
def test_no_duplicate_action_ids(name: str) -> None:
    raw = json.loads(
        (UI_DIR / name).read_text(encoding="utf-8"),
        object_pairs_hook=lambda pairs: pairs,
    )
    action_pairs = next(value for key, value in raw if key == "actions")
    action_ids = [key for key, _value in action_pairs]
    duplicates = [key for key, count in Counter(action_ids).items() if count > 1]
    assert duplicates == []
