"""WebSocket telemetry contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aoc_supervisor.websocket_telemetry import (
    SchemaComplianceError,
    SequenceViolationError,
    _wrap_event,
    build_grid_telemetry,
    build_session_init,
    build_topology_snapshot,
    handle_client_action,
    new_session_id,
)


def test_session_init_shape() -> None:
    root = Path(__file__).resolve().parents[1]
    sid = new_session_id()
    msg = build_session_init(root, session_id=sid, experience_mode="builder")
    assert msg["event_type"] == "session.snapshot"
    assert msg["data"]["session_id"] == sid
    assert "global_constraints" in msg["data"]
    assert "schema_version" in msg
    assert "sequence" in msg
    assert "emitted_at" in msg


def test_topology_snapshot_from_repo() -> None:
    root = Path(__file__).resolve().parents[1]
    sid = new_session_id()
    msg = build_topology_snapshot(root, session_id=sid)
    assert msg["event_type"] == "topology.constraints.summary"
    assert isinstance(msg["data"]["nodes"], list)
    assert isinstance(msg["data"]["links"], list)


def test_mutate_geometry_strategy_builder() -> None:
    root = Path(__file__).resolve().parents[1]
    sid = new_session_id()
    topo_before = build_topology_snapshot(root, session_id=sid)
    links = topo_before["data"]["links"]
    if not links:
        return
    first = links[0]
    ack = handle_client_action(
        "MUTATE_GEOMETRY_STRATEGY",
        {"target_link": [first["source"], first["target"]], "selected_strategy": "WELD"},
        session_id=sid,
        experience_mode="builder",
        project_root=root,
    )
    assert ack is None
    topo_after = build_topology_snapshot(root, session_id=sid)
    match = next(
        link
        for link in topo_after["data"]["links"]
        if link["source"] == first["source"] and link["target"] == first["target"]
    )
    assert match["mitigation_strategy"] == "WELD"


def test_grid_telemetry_shape() -> None:
    root = Path(__file__).resolve().parents[1]
    sid = new_session_id()
    msg = build_grid_telemetry(root, session_id=sid)
    assert msg["event_type"] == "merge.state.updated"
    assert "workers" in msg["data"]


def test_sequence_monotonic_ordering() -> None:
    root = Path(__file__).resolve().parents[1]
    sid = new_session_id()

    msg1 = build_session_init(root, session_id=sid)
    msg2 = build_topology_snapshot(root, session_id=sid)
    msg3 = build_grid_telemetry(root, session_id=sid)

    assert msg1["sequence"] == 0
    assert msg2["sequence"] == 1
    assert msg3["sequence"] == 2


def test_sequence_regression_raises() -> None:
    sid = new_session_id()

    # Create initial event to initialize sequence to 0
    _wrap_event(sid, "session.snapshot", "guided", "awaiting_intent", {}, sequence=0)

    # Try to validate with the same or lower sequence number
    with pytest.raises(SequenceViolationError):
        _wrap_event(sid, "session.snapshot", "guided", "awaiting_intent", {}, sequence=0)


def test_schema_compliance_validation() -> None:
    sid = new_session_id()

    # Missing required field or invalid type in envelope raises SchemaComplianceError
    with pytest.raises(SchemaComplianceError):
        # Invalid event_type
        _wrap_event(sid, "invalid.event.type", "guided", "awaiting_intent", {})


def test_density_spike_stability(tmp_path) -> None:
    # Set up workers directory structure inside tmp_path
    gaijinn_dir = tmp_path / ".gaijinn"
    workers_dir = gaijinn_dir / "workers"
    workers_dir.mkdir(parents=True)

    merge_dir = gaijinn_dir / "merge"
    merge_dir.mkdir(parents=True)

    # 50 worker directories and entries
    workers_manifest = {}
    collected_workers = {}
    for i in range(1, 51):
        wid = f"worker-{i:03d}"
        worker_dir = workers_dir / wid
        worker_dir.mkdir()

        # Write dummy giv.json
        (worker_dir / "giv.json").write_text("{}", encoding="utf-8")

        # Manifest mapping
        workers_manifest[wid] = {"assigned_work_units": [f"wu_{i}"]}

        # Collected mapping
        collected_workers[wid] = {"status": "executing", "changed_files": [f"file_{i}.py"], "trespasses": []}

    # Write manifest.json
    manifest_data = {"worker_count": 50, "workers": workers_manifest}
    (workers_dir / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

    # Write collected.json
    collected_data = {"workers": collected_workers}
    (merge_dir / "collected.json").write_text(json.dumps(collected_data), encoding="utf-8")

    # Write empty handoff-queue.json and governance.json
    (merge_dir / "handoff-queue.json").write_text(json.dumps({"tickets": []}), encoding="utf-8")
    (merge_dir / "governance.json").write_text(json.dumps({}), encoding="utf-8")

    # Execute build_grid_telemetry on tmp_path
    sid = new_session_id()
    msg = build_grid_telemetry(tmp_path, session_id=sid)

    # Assertions
    assert msg["event_type"] == "merge.state.updated"
    assert len(msg["data"]["workers"]) == 50
    assert msg["data"]["active_workers"] == 50
