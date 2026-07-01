"""Schema validation and legacy mapping for canonical orchestration envelopes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from aoc_supervisor.orchestration_envelope import (
    OrchestrationJournal,
    map_legacy_deliberation_event,
    validate_orchestration_event,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "deliberation_canonical_sequence.json"


@pytest.fixture
def journal() -> OrchestrationJournal:
    return OrchestrationJournal(correlation_id="delib-test", session_id="delib-test")


@pytest.fixture
def valid_event() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "event_id": "evt_123",
        "sequence": 0,
        "emitted_at": "2023-10-27T12:00:00Z",
        "session_id": "sess-123",
        "correlation_id": "corr-123",
        "phase": "blueprinting",
        "classification": "guided",
        "event_type": "phase.begin",
        "data": {"provisional_session": True},
    }


class TestLegacyMapping:
    def test_deliberation_start_maps_to_phase_begin(self, journal: OrchestrationJournal) -> None:
        envelope = journal.emit_legacy(
            "deliberation_start",
            {"intent": "build auth", "layer1_timeout_s": 3600, "mode": "architectural_teleology"},
        )
        assert envelope["event_type"] == "phase.begin"
        assert envelope["phase"] == "blueprinting"
        assert envelope["subphase"] == "intent_parse"
        assert envelope["data"]["provisional_session"] is True

    def test_node_added_normalizes_topology_node(self, journal: OrchestrationJournal) -> None:
        envelope = journal.emit_legacy("node_added", {"id": "aoc_cli/cli.py", "gravity": 0.8, "rejected": False})
        assert envelope["event_type"] == "topology.node.upsert"
        assert envelope["data"]["node_id"] == "aoc_cli/cli.py"
        assert envelope["data"]["status"] == "discovered"

    def test_dark_bridge_maps_to_topology_bridge(self, journal: OrchestrationJournal) -> None:
        envelope = journal.emit_legacy(
            "dark_bridge_detected",
            {"source": "a.py", "target": "b.py", "kappa": -0.42},
        )
        assert envelope["event_type"] == "topology.bridge.detected"
        assert envelope["data"]["classification"] == "dark_bridge"

    def test_deliberation_complete_binds_session_id(self, journal: OrchestrationJournal) -> None:
        envelope = journal.emit_legacy(
            "deliberation_complete",
            {"session_id": "sess-real-123", "work_units": 3},
        )
        assert envelope["event_type"] == "phase.complete"
        assert envelope["phase"] == "awaiting_swarm"
        assert journal.session_id == "sess-real-123"

    def test_legacy_wire_roundtrip(self, journal: OrchestrationJournal) -> None:
        envelope = journal.emit_legacy("edge_curvature", {"source": "a", "target": "b", "kappa": -0.1})
        legacy = journal.to_legacy_wire(envelope)
        assert legacy["type"] == "edge_curvature"
        assert legacy["data"]["kappa"] == -0.1


class TestSchemaValidation:
    def test_fixture_sequence_validates(self) -> None:
        sequence = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        for event in sequence:
            validate_orchestration_event(event)

    def test_generated_deliberation_sequence_validates(self, journal: OrchestrationJournal) -> None:
        steps = [
            ("deliberation_start", {"intent": "dogfood", "layer1_timeout_s": 120}),
            ("phase_begin", {"phase": "intent_parse", "message": "parse"}),
            ("work_unit_assigned", {"id": "WU-1", "title": "Auth", "files": 2, "risk": "medium", "preview": True}),
            ("phase_complete", {"phase": "intent_parse", "elapsed_ms": 12}),
            ("node_added", {"id": "auth.py", "gravity": 0.4}),
            (
                "edge_curvature",
                {"source": "auth.py", "target": "db.py", "kappa": -0.35},
            ),
            (
                "dark_bridge_detected",
                {"source": "auth.py", "target": "db.py", "kappa": -0.35},
            ),
            ("deliberation_complete", {"session_id": "sess-abc", "work_units": 1}),
        ]
        for legacy_type, payload in steps:
            envelope = journal.emit_legacy(legacy_type, payload)
            validate_orchestration_event(envelope)

    def test_map_legacy_unknown_falls_back_to_progress(self) -> None:
        event_type, phase, subphase, classification, _data = map_legacy_deliberation_event(
            "unknown_event",
            {"foo": "bar"},
        )
        assert event_type == "phase.progress"
        assert phase == "blueprinting"
        assert classification == "guided"

    def test_missing_required_field(self, valid_event):
        del valid_event["event_id"]
        with pytest.raises(
            ValueError, match="orchestration event failed schema validation: .*'event_id' is a required property"
        ):
            validate_orchestration_event(valid_event)

    def test_invalid_type(self, valid_event):
        valid_event["sequence"] = "not-an-int"
        with pytest.raises(
            ValueError, match="orchestration event failed schema validation: .*'not-an-int' is not of type 'integer'"
        ):
            validate_orchestration_event(valid_event)

    def test_invalid_event_type(self, valid_event):
        valid_event["event_type"] = "invalid.type"
        with pytest.raises(
            ValueError, match="orchestration event failed schema validation: .*'invalid.type' is not one of"
        ):
            validate_orchestration_event(valid_event)

    def test_data_mismatch_for_event_type(self, valid_event):
        valid_event["event_type"] = "topology.node.upsert"
        valid_event["data"] = {"wrong": "fields"}
        with pytest.raises(
            ValueError, match="orchestration event failed schema validation: .*'node_id' is a required property"
        ):
            validate_orchestration_event(valid_event)

    def test_multiple_errors_limit_and_sorting(self, valid_event):
        del valid_event["event_id"]
        del valid_event["session_id"]
        valid_event["sequence"] = -1
        valid_event["schema_version"] = 2

        with pytest.raises(ValueError) as excinfo:
            validate_orchestration_event(valid_event)

        message = str(excinfo.value)
        assert message.count("; ") <= 2
        assert "orchestration event failed schema validation: " in message
        assert (
            "is a required property" in message or "is less than the minimum" in message or "not equal to 1" in message
        )

    def test_validator_none_returns_early(self, valid_event):
        with patch("aoc_supervisor.orchestration_envelope._validator", return_value=None):
            del valid_event["event_id"]
            validate_orchestration_event(valid_event)
