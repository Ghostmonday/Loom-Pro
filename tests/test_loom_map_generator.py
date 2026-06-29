"""Tests for Loom C23 deterministic map draft generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aoc_supervisor.loom_map_generator import generate_map_draft
from aoc_supervisor.teleology_artifact import build_teleology_artifact

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _draft() -> dict:
    forge_state = _load("teleology_pipeline_executor.json")
    teleology = build_teleology_artifact(forge_state)
    topology = _load("topology_pipeline_executor.json")
    return generate_map_draft(teleology, topology)


def test_fixture_generates_prepare_action_and_dependency_order() -> None:
    draft = _draft()

    assert "prepare" in draft["actions"]
    positions = {step["action"]: step["order"] for step in draft["flow"]}
    assert positions["prepare"] < positions["wu_001"]
    assert positions["wu_001"] < positions["wu_002"]
    assert positions["wu_001"] < positions["wu_003"]


def test_actions_are_spec_only_and_include_topology_placement() -> None:
    action = _draft()["actions"]["prepare"]

    assert action["algorithm_binding"]["mode"] == "spec_only"
    assert action["algorithm_binding"]["gap"]
    assert action["topology"] == {
        "cluster_ids": ["foundation"],
        "work_unit_ids": ["prepare"],
    }


def test_topology_breaks_ties_between_independent_capabilities() -> None:
    draft = _draft()
    actions = [step["action"] for step in draft["flow"]]

    assert actions.index("wu_003") < actions.index("wu_002")


def test_success_criteria_become_spec_only_smoke_scenarios() -> None:
    forge_state = _load("teleology_pipeline_executor.json")
    teleology = build_teleology_artifact(forge_state)
    draft = generate_map_draft(
        teleology,
        _load("topology_pipeline_executor.json"),
    )

    assert len(draft["smoke_scenarios"]) == len(teleology["success_criteria"])
    assert all(scenario["implementation_status"] == "spec_only" for scenario in draft["smoke_scenarios"])


def test_states_become_adjacent_transitions() -> None:
    transitions = _draft()["state_machine"]["transitions"]

    assert [(item["from"], item["to"]) for item in transitions] == [
        ("foundation", "storage"),
        ("storage", "interface"),
    ]


def test_generation_is_deterministic() -> None:
    assert _draft() == _draft()


def test_unknown_dependency_is_rejected() -> None:
    teleology = {
        "session_id": "session",
        "required_capabilities": [
            {
                "id": "prepare",
                "description": "Prepare",
                "depends_on": ["missing"],
            }
        ],
        "success_criteria": ["Prepared"],
        "states": [],
    }
    topology = {
        "session_id": "session",
        "clusters": [],
        "work_units": [],
    }

    with pytest.raises(ValueError, match="unknown capabilities"):
        generate_map_draft(teleology, topology)


def test_dependency_cycle_is_rejected() -> None:
    teleology = {
        "session_id": "session",
        "required_capabilities": [
            {"id": "prepare", "description": "Prepare", "depends_on": ["run"]},
            {"id": "run", "description": "Run", "depends_on": ["prepare"]},
        ],
        "success_criteria": ["Runs"],
        "states": [],
    }
    topology = {
        "session_id": "session",
        "clusters": [],
        "work_units": [],
    }

    with pytest.raises(ValueError, match="cycle"):
        generate_map_draft(teleology, topology)
