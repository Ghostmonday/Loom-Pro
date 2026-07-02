"""Focused coverage for websocket_telemetry error paths, session state, and batching."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import aoc_supervisor.websocket_telemetry as wt
from aoc_supervisor.websocket_telemetry import (
    CURVATURE_FLOOR_DEFAULT,
    SchemaComplianceError,
    SequenceViolationError,
    _canvas_eligible_path,
    _git_base_commit,
    _jurisdiction_for_path,
    _load_json,
    _mitigation_for_edge,
    _work_unit_index,
    _wrap_event,
    build_grid_telemetry,
    build_session_init,
    build_topology_snapshot,
    effective_experience_mode,
    get_curvature_floor,
    handle_client_action,
    new_session_id,
)


@pytest.fixture(autouse=True)
def _reset_telemetry_state():
    wt._session_overrides.clear()
    wt._session_sequences.clear()
    yield
    wt._session_overrides.clear()
    wt._session_sequences.clear()


def _write_gaijinn_layout(
    root: Path,
    *,
    workers: list[dict] | None = None,
    tickets: list[dict] | None = None,
    metrics: dict | None = None,
    blueprint: dict | None = None,
    governance: dict | None = None,
) -> None:
    gaijinn = root / ".gaijinn"
    workers_dir = gaijinn / "workers"
    merge_dir = gaijinn / "merge"
    workers_dir.mkdir(parents=True, exist_ok=True)
    merge_dir.mkdir(parents=True, exist_ok=True)

    workers = workers or []
    manifest_workers: dict[str, dict] = {}
    collected_workers: dict[str, dict] = {}
    for spec in workers:
        wid = spec["id"]
        (workers_dir / wid).mkdir(exist_ok=True)
        if spec.get("giv"):
            (workers_dir / wid / "giv.json").write_text(json.dumps(spec["giv"]), encoding="utf-8")
        manifest_workers[wid] = {"assigned_work_units": spec.get("work_units", [])}
        collected_workers[wid] = {
            "status": spec.get("status", "executing"),
            "changed_files": spec.get("changed_files", []),
            "trespasses": spec.get("trespasses", []),
        }

    (workers_dir / "manifest.json").write_text(
        json.dumps({"worker_count": len(workers), "workers": manifest_workers}),
        encoding="utf-8",
    )
    (merge_dir / "collected.json").write_text(
        json.dumps({"workers": collected_workers}),
        encoding="utf-8",
    )
    (merge_dir / "handoff-queue.json").write_text(
        json.dumps({"tickets": tickets or []}),
        encoding="utf-8",
    )
    (merge_dir / "governance.json").write_text(
        json.dumps(governance or {"structural_score": {"validation_pass_rate": 0.9}}),
        encoding="utf-8",
    )

    if metrics is not None:
        (gaijinn / "metrics_manifest.json").write_text(json.dumps(metrics), encoding="utf-8")
    if blueprint is not None:
        (gaijinn / "blueprint.json").write_text(json.dumps(blueprint), encoding="utf-8")
    (gaijinn / "graph.json").write_text(json.dumps({"nodes": [{"id": "n1"}]}), encoding="utf-8")


# --- Message serialization edge cases ---


def test_load_json_missing_file_returns_empty_dict(tmp_path: Path) -> None:
    assert _load_json(tmp_path / "missing.json") == {}


def test_load_json_invalid_json_returns_empty_dict(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid", encoding="utf-8")
    assert _load_json(bad) == {}


def test_load_json_non_dict_payload_returns_empty_dict(tmp_path: Path) -> None:
    arr = tmp_path / "arr.json"
    arr.write_text("[1, 2, 3]", encoding="utf-8")
    assert _load_json(arr) == {}


def test_schema_load_failure_raises_schema_compliance_error(monkeypatch) -> None:
    sid = new_session_id()

    def _boom(*_args, **_kwargs):
        raise OSError("schema unreadable")

    monkeypatch.setattr(Path, "read_text", _boom)
    wt._loaded_schema = None
    with pytest.raises(SchemaComplianceError, match="Could not load schema"):
        _wrap_event(sid, "session.snapshot", "guided", "awaiting_intent", {"session_id": sid})


def test_git_base_commit_returns_unknown_on_subprocess_failure(tmp_path: Path) -> None:
    with patch("subprocess.run", side_effect=OSError("no git")):
        assert _git_base_commit(tmp_path) == "unknown"


# --- Session reconnect / effective mode ---


def test_effective_experience_mode_lowers_to_requested_rank() -> None:
    sid = new_session_id()
    handle_client_action(
        "SET_EXPERIENCE_MODE",
        {"mode": "operator"},
        session_id=sid,
        experience_mode="operator",
        project_root=Path("."),
    )
    assert effective_experience_mode(sid, "builder") == "builder"
    assert effective_experience_mode(sid, "guided") == "guided"


def test_effective_experience_mode_caps_unknown_requested_to_builder() -> None:
    sid = new_session_id()
    assert effective_experience_mode(sid, "superuser") == "builder"


def test_effective_experience_mode_keeps_stored_when_request_higher() -> None:
    sid = new_session_id()
    handle_client_action(
        "SET_EXPERIENCE_MODE",
        {"mode": "guided"},
        session_id=sid,
        experience_mode="operator",
        project_root=Path("."),
    )
    assert effective_experience_mode(sid, "operator") == "guided"


def test_reconnect_new_session_gets_fresh_sequence(tmp_path: Path) -> None:
    _write_gaijinn_layout(tmp_path, workers=[{"id": "worker-001"}])
    sid_a = new_session_id()
    sid_b = new_session_id()
    msg_a = build_session_init(tmp_path, session_id=sid_a)
    msg_b = build_session_init(tmp_path, session_id=sid_b)
    assert msg_a["sequence"] == 0
    assert msg_b["sequence"] == 0
    assert sid_a != sid_b


def test_sequence_regression_on_reconnect_same_session_raises() -> None:
    sid = new_session_id()
    _wrap_event(sid, "session.snapshot", "guided", "awaiting_intent", {"session_id": sid}, sequence=2)
    with pytest.raises(SequenceViolationError):
        _wrap_event(sid, "session.snapshot", "guided", "awaiting_intent", {"session_id": sid}, sequence=1)


# --- handle_client_action error / disconnect-style rejections ---


def test_mutate_geometry_rejects_insufficient_mode() -> None:
    sid = new_session_id()
    ack = handle_client_action(
        "MUTATE_GEOMETRY_STRATEGY",
        {"target_link": ["a", "b"], "selected_strategy": "WELD"},
        session_id=sid,
        experience_mode="guided",
        project_root=Path("."),
    )
    assert ack is not None
    assert ack["event"] == "ACTION_REJECTED"
    assert ack["payload"]["reason"] == "insufficient_mode"


def test_mutate_geometry_rejects_invalid_target_link() -> None:
    sid = new_session_id()
    ack = handle_client_action(
        "MUTATE_GEOMETRY_STRATEGY",
        {"target_link": ["only-one"], "selected_strategy": "WELD"},
        session_id=sid,
        experience_mode="builder",
        project_root=Path("."),
    )
    assert ack is not None
    assert ack["payload"]["reason"] == "invalid_target_link"


def test_mutate_geometry_handoff_only_strategy(tmp_path: Path) -> None:
    metrics = {
        "gravity_meta": {
            "nodes": {
                "aoc_supervisor/a.py": {"gravity": 1.0},
                "aoc_supervisor/b.py": {"gravity": 0.9},
            }
        },
        "curvature_meta": {
            "edges": {
                "e1": {"source": "aoc_supervisor/a.py", "target": "aoc_supervisor/b.py", "kappa": -0.5}
            }
        },
    }
    _write_gaijinn_layout(tmp_path, metrics=metrics, blueprint={"work_units": []})
    sid = new_session_id()
    topo = build_topology_snapshot(tmp_path, session_id=sid)
    link = topo["data"]["links"][0]
    ack = handle_client_action(
        "MUTATE_GEOMETRY_STRATEGY",
        {"target_link": [link["source"], link["target"]], "selected_strategy": "HANDOFF"},
        session_id=sid,
        experience_mode="builder",
        project_root=tmp_path,
    )
    assert ack is None
    topo_after = build_topology_snapshot(tmp_path, session_id=sid)
    updated = next(
        lnk for lnk in topo_after["data"]["links"] if lnk["source"] == link["source"] and lnk["target"] == link["target"]
    )
    assert updated["mitigation_strategy"] == "HANDOFF_ONLY"


def test_override_invariant_rejects_non_operator() -> None:
    sid = new_session_id()
    ack = handle_client_action(
        "OVERRIDE_SYSTEM_INVARIANT",
        {"invariant_key": "ricci_curvature_floor", "requested_value": -0.1},
        session_id=sid,
        experience_mode="builder",
        project_root=Path("."),
    )
    assert ack is not None
    assert ack["payload"]["reason"] == "operator_mode_required"


def test_override_invariant_rejects_unknown_key() -> None:
    sid = new_session_id()
    ack = handle_client_action(
        "OVERRIDE_SYSTEM_INVARIANT",
        {"invariant_key": "other", "requested_value": -0.1},
        session_id=sid,
        experience_mode="operator",
        project_root=Path("."),
    )
    assert ack["payload"]["reason"] == "unknown_invariant"


def test_override_invariant_rejects_invalid_value() -> None:
    sid = new_session_id()
    ack = handle_client_action(
        "OVERRIDE_SYSTEM_INVARIANT",
        {"invariant_key": "ricci_curvature_floor", "requested_value": "not-a-float"},
        session_id=sid,
        experience_mode="operator",
        project_root=Path("."),
    )
    assert ack["payload"]["reason"] == "invalid_value"


def test_override_invariant_applies_and_updates_floor(tmp_path: Path) -> None:
    sid = new_session_id()
    ack = handle_client_action(
        "OVERRIDE_SYSTEM_INVARIANT",
        {
            "invariant_key": "ricci_curvature_floor",
            "requested_value": -0.05,
            "justification": "test override",
        },
        session_id=sid,
        experience_mode="operator",
        project_root=tmp_path,
    )
    assert ack is not None
    assert ack["event"] == "INVARIANT_OVERRIDE_ACK"
    assert ack["payload"]["status"] == "APPLIED_UNSAFE"
    assert ack["payload"]["curvature_floor"] == -0.05
    assert get_curvature_floor(sid) == -0.05


def test_set_experience_mode_rejects_invalid_mode() -> None:
    sid = new_session_id()
    ack = handle_client_action(
        "SET_EXPERIENCE_MODE",
        {"mode": "turbo"},
        session_id=sid,
        experience_mode="builder",
        project_root=Path("."),
    )
    assert ack["payload"]["reason"] == "invalid_mode"


def test_unknown_action_rejected() -> None:
    sid = new_session_id()
    ack = handle_client_action(
        "PING",
        {},
        session_id=sid,
        experience_mode="builder",
        project_root=Path("."),
    )
    assert ack["payload"]["reason"] == "unknown_action"


# --- Topology helpers and mitigation strategies ---


def test_canvas_eligible_path_filters_prefixes_and_extensions() -> None:
    assert _canvas_eligible_path("aoc_supervisor/foo.py") is True
    assert _canvas_eligible_path(".hidden/foo.py") is False
    assert _canvas_eligible_path("docs/campaign/x.py") is False
    assert _canvas_eligible_path("random/foo.py") is False
    assert _canvas_eligible_path("aoc_supervisor/readme.md") is False


def test_work_unit_index_maps_paths_and_directory_prefixes() -> None:
    blueprint = {
        "work_units": [
            {"id": "wu_a", "allowed_paths": ["aoc_supervisor/", "tests/test_x.py"]},
            "not-a-dict",
            {"id": "", "allowed_paths": ["skip"]},
            {"id": "wu_b", "allowed_paths": "bad"},
        ]
    }
    index = _work_unit_index(blueprint)
    assert index["aoc_supervisor/"] == "wu_a"
    assert index["tests/test_x.py"] == "wu_a"


def test_jurisdiction_for_path_resolves_prefix_and_unassigned() -> None:
    blueprint = {"work_units": [{"id": "wu_1", "allowed_paths": ["aoc_supervisor/"], "denied_paths": ["vaults/"]}]}
    index = _work_unit_index(blueprint)
    assert _jurisdiction_for_path("aoc_supervisor/pkg/mod.py", index, blueprint) == "wu_1"
    assert _jurisdiction_for_path("unknown/path.py", index, blueprint) == "unassigned"


@pytest.mark.parametrize(
    ("kappa", "gateway", "expected"),
    [
        (-0.1, False, "INDEPENDENT"),
        (-0.1, True, "GOVERNED_HANDOFF"),
        (-0.5, True, "HANDOFF_ONLY"),
        (-0.5, False, "WELD_PROPOSED"),
    ],
)
def test_mitigation_for_edge(kappa: float, gateway: bool, expected: str) -> None:
    assert _mitigation_for_edge(kappa, gateway) == expected


def test_build_session_init_operator_mode_allows_geometry_override(tmp_path: Path) -> None:
    _write_gaijinn_layout(tmp_path)
    sid = new_session_id()
    msg = build_session_init(tmp_path, session_id=sid, experience_mode="operator")
    assert msg["data"]["global_constraints"]["allow_geometry_override"] is True


def test_build_session_init_metrics_failure_falls_back_to_defaults(tmp_path: Path) -> None:
    gaijinn = tmp_path / ".gaijinn"
    gaijinn.mkdir(parents=True)
    (gaijinn / "graph.json").write_text("{}", encoding="utf-8")
    (gaijinn / "metrics_manifest.json").write_text("not-json", encoding="utf-8")
    sid = new_session_id()
    msg = build_session_init(tmp_path, session_id=sid)
    summary = msg["data"]["repository_summary"]
    assert summary["architectural_complexity_index"] == 0.0
    assert summary["complexity_class"] == "starter"


def test_build_topology_snapshot_weld_and_bridge_paths(tmp_path: Path) -> None:
    metrics = {
        "gravity_meta": {
            "nodes": {
                "aoc_supervisor/src/a.py": {"gravity": 2.0},
                "aoc_supervisor/src/b.py": {"gravity": 1.5},
                "vaults/secret.py": {"gravity": 9.0},
            }
        },
        "curvature_meta": {
            "edges": {
                "bridge": {
                    "source": "aoc_supervisor/src/a.py",
                    "target": "aoc_supervisor/src/b.py",
                    "kappa": -0.4,
                }
            }
        },
    }
    blueprint = {
        "work_units": [
            {"id": "wu_alpha", "allowed_paths": ["aoc_supervisor/src/"]},
        ]
    }
    governance = {"structural_score": {"convergence": 0.88}}
    _write_gaijinn_layout(tmp_path, metrics=metrics, blueprint=blueprint, governance=governance)
    sid = new_session_id()

    with patch("aoc_supervisor.websocket_telemetry.handoff_gateway_mode_enabled", return_value=True):
        topo = build_topology_snapshot(tmp_path, session_id=sid)

    data = topo["data"]
    assert data["convergence_score"] == 0.88
    assert len(data["nodes"]) == 2
    assert any(node["on_shadow_bridge"] for node in data["nodes"])
    assert data["links"][0]["mitigation_strategy"] == "HANDOFF_ONLY"
    assert "weld_id" not in data["links"][0]


def test_build_topology_snapshot_weld_proposed_below_floor(tmp_path: Path) -> None:
    metrics = {
        "gravity_meta": {
            "nodes": {
                "tests/a.py": {"gravity": 1.0},
                "tests/b.py": {"gravity": 0.8},
            }
        },
        "curvature_meta": {
            "edges": {
                "edge": {
                    "source": "tests/a.py",
                    "target": "tests/b.py",
                    "curvature": CURVATURE_FLOOR_DEFAULT,
                }
            }
        },
    }
    _write_gaijinn_layout(tmp_path, metrics=metrics, blueprint={"work_units": []})
    sid = new_session_id()
    with patch("aoc_supervisor.websocket_telemetry.handoff_gateway_mode_enabled", return_value=False):
        topo = build_topology_snapshot(tmp_path, session_id=sid)
    link = topo["data"]["links"][0]
    assert link["mitigation_strategy"] == "WELD_PROPOSED"
    assert link["weld_id"] in topo["data"]["welds"]


# --- Telemetry batching / worker status mapping ---


def test_grid_telemetry_batches_worker_statuses_and_handoff_tickets(tmp_path: Path) -> None:
    workers = [
        {"id": "worker-001", "status": "COMPLETED", "work_units": ["wu_1"], "giv": {"scope": "a"}},
        {"id": "worker-002", "status": "DIRTY", "changed_files": ["a.py", "b.py"], "trespasses": ["t1"]},
        {"id": "worker-003", "status": "PENDING"},
        {"id": "worker-004", "status": "VALIDATED"},
        {"id": "worker-005", "status": "RUNNING", "changed_files": "not-a-list"},
    ]
    tickets = [
        {"ticket_id": "t-open", "source_worker_id": "worker-001", "target_work_unit_id": "wu_2", "status": "open"},
        {"ticket_id": "t-done", "source_worker_id": "worker-002", "target_work_unit_id": "wu_3", "status": "resolved"},
        "bad-ticket",
    ]
    _write_gaijinn_layout(tmp_path, workers=workers, tickets=tickets)
    msg = build_grid_telemetry(tmp_path)

    data = msg["data"]
    assert msg["session_id"] == "sess_default"
    assert data["active_workers"] == 5
    assert data["workers"]["worker-001"]["status"] == "COMPLETED"
    assert data["workers"]["worker-002"]["status"] == "VIOLATION_DETECTED"
    assert data["workers"]["worker-003"]["status"] == "WAITING_ON_HANDOFF"
    assert data["workers"]["worker-003"]["target_lane"] == "cross_boundary_transit"
    assert data["workers"]["worker-004"]["status"] == "COMPLETED"
    assert data["workers"]["worker-005"]["status"] == "EXECUTING_REFACTOR"
    assert data["workers"]["worker-005"]["mutated_paths"] == []
    assert data["workers"]["worker-001"]["giv_token_signature"].startswith("giv_sig_")
    assert len(data["active_handoff_tickets"]) == 1
    assert data["active_handoff_tickets"][0]["ticket_id"] == "t-open"
    assert data["sprints_consumed"] == 2


def test_grid_telemetry_truncates_mutated_paths_to_eight(tmp_path: Path) -> None:
    changed = [f"file_{i}.py" for i in range(12)]
    _write_gaijinn_layout(
        tmp_path,
        workers=[{"id": "worker-001", "changed_files": changed}],
    )
    msg = build_grid_telemetry(tmp_path, session_id=new_session_id())
    assert len(msg["data"]["workers"]["worker-001"]["mutated_paths"]) == 8