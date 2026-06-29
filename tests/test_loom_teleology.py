"""LOOM-204 (C09) — Teleology Mirror Receipt.

UiIntentDriver.collect_teleology_receipt() hits the /blueprint/deliberate SSE
endpoint, consumes canonical events until blueprint_freeze, and stores
the parsed teleology on IntentMirrorState.teleology.
"""

from __future__ import annotations

from typing import Any

from aoc_supervisor.ui_intent import UiIntentDriver


class TestLoomTeleologyReceipt:
    """C09: teleology mirror receipt via collect_teleology_receipt()."""

    def test_collect_teleology_receipt_populates_mirror(self, mock_grid_client: Any) -> None:
        """Call collect_teleology_receipt and verify mirror.teleology subphases."""
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client, user_id="terminal-user")

        teleology = driver.collect_teleology_receipt(
            "Build a CLI note-taking app with markdown export",
        )

        # The teleology dict is returned and stored on the mirror
        assert driver.mirror.teleology is teleology
        assert teleology["intent"].startswith("Build a CLI note-taking app")

        # Expect at least intent_parse and blueprint_freeze subphases
        # (The mock environment doesn't exercise the full pipeline,
        #  but the SSE endpoint tracks the subphases it does visit.)
        found_subphases = set(teleology["subphases"].keys())
        assert "intent_parse" in found_subphases, "missing intent_parse subphase"
        assert "blueprint_freeze" in found_subphases, "missing blueprint_freeze subphase"

        # Each tracked subphase should have completion data
        for sp, info in teleology["subphases"].items():
            assert "status" in info, f"{sp} missing status"
            assert info["status"] in ("started", "complete"), f"{sp} unexpected status {info['status']!r}"

    def test_teleology_receipt_curvature_floor_present(self, mock_grid_client: Any) -> None:
        """Verify edge curvatures and curvature_floor are extracted."""
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client, user_id="terminal-user")

        teleology = driver.collect_teleology_receipt("Build a simple REST API")

        # curvature_floor should be present (may be 0.0 in mock mode)
        assert "curvature_floor" in teleology
        assert isinstance(teleology["curvature_floor"], (int, float))

        # edge_curvatures should be a list
        assert isinstance(teleology["edge_curvatures"], list)

    def test_teleology_receipt_blueprint_freeze_data(self, mock_grid_client: Any) -> None:
        """Verify blueprint_freeze contains session_id and work_units."""
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client, user_id="terminal-user")

        teleology = driver.collect_teleology_receipt("Refactor the auth module")

        freeze = teleology.get("blueprint_freeze", {})
        assert freeze.get("session_id"), "blueprint_freeze missing session_id"
        assert freeze.get("work_units", 0) > 0, "blueprint_freeze missing work_units"
        assert freeze.get("high_risk_units", 0) >= 0
        assert freeze.get("recommended_swarm", 0) > 0

    def test_teleology_receipt_events_stream(self, mock_grid_client: Any) -> None:
        """Verify that raw canonical events were captured."""
        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client, user_id="terminal-user")

        teleology = driver.collect_teleology_receipt("Build a weather dashboard")

        assert len(teleology["events"]) > 0

        # First event should be deliberation_start / phase.begin
        first = teleology["events"][0]
        assert first.get("event_type") in ("phase.begin",)
        assert first.get("data", {}).get("mode") == "architectural_teleology"

        # Last event should be deliberation_complete / phase.complete
        last = teleology["events"][-1]
        assert last.get("event_type") == "phase.complete"
        assert last.get("phase") == "awaiting_swarm"


class TestLoomC11TeleologyAfterHandoff:
    """C11 (LOOM-204): teleology receipt collection after handoff acceptance."""

    def test_after_handoff(self, mock_grid_client: Any) -> None:
        """Accept a forge handoff, then collect teleology receipt.

        Verifies the pipeline_handoff_with_teleology() coordinator:
          handoff.confirm → handoff.accept → collect_teleology_receipt
        """
        from aoc_supervisor.loom_pipeline import pipeline_handoff_with_teleology

        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client, user_id="terminal-user")

        # 1. Start free-tier session (auto-finalizes)
        driver.dispatch_loom_forge_action(
            "intake.start_session",
            {"prompt": "Build a CLI note app", "tier": "free"},
        )

        # 2. Confirm handoff
        driver.dispatch_loom_forge_action(
            "handoff.confirm",
            {"confirmation": "Proceed with architecture"},
        )
        assert driver.mirror.session_status == "FINALIZED"

        # 3. Accept + collect teleology via pipeline coordinator
        result = pipeline_handoff_with_teleology(driver, "Build a CLI note app")

        # Accept response
        accept = result["accept"]
        assert accept["session_status"] == "HANDED_OFF"
        assert driver.mirror.session_status == "HANDED_OFF"

        # Teleology receipt populated
        teleology = result["teleology"]
        assert isinstance(teleology, dict)
        assert teleology["intent"] == "Build a CLI note app"
        assert len(teleology["events"]) > 0
        assert "subphases" in teleology
        assert teleology["events"][0].get("event_type") == "phase.begin"

        # Mirror also updated
        assert driver.mirror.teleology is teleology

    def test_after_handoff_skips_teleology_when_disabled(self, mock_grid_client: Any) -> None:
        """Setting collect_teleology=False skips receipt collection."""
        from aoc_supervisor.loom_pipeline import pipeline_handoff_with_teleology

        client, _workers, _tmp, _store = mock_grid_client
        driver = UiIntentDriver(client, user_id="terminal-user")

        driver.dispatch_loom_forge_action(
            "intake.start_session",
            {"prompt": "Build a CLI note app", "tier": "free"},
        )
        driver.dispatch_loom_forge_action(
            "handoff.confirm",
            {"confirmation": "Proceed"},
        )

        result = pipeline_handoff_with_teleology(driver, "Build a CLI note app", collect_teleology=False)

        assert result["accept"]["session_status"] == "HANDED_OFF"
        assert result["teleology"] == {}
        assert driver.mirror.session_status == "HANDED_OFF"
