"""REST preflight merge gate (/api/v1/preflight)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from aoc_cli.helpers.merge import HANDOFF_QUEUE_PATH, VALIDATED_PATH, write_merge_json
from aoc_supervisor.preflight import (
    PreflightResolutionError,
    run_preflight_check,
    verify_workspace_isolation_gate,
)
from fastapi.testclient import TestClient


def _minimal_blueprint() -> dict:
    return {
        "schema_version": 1,
        "project_goal": "preflight test",
        "assumptions": [],
        "work_units": [
            {
                "id": "WU-001",
                "title": "unit",
                "description": "unit",
                "allowed_paths": ["src/"],
                "denied_paths": [],
                "depends_on": [],
                "acceptance_checks": ["pytest"],
                "estimated_risk": "low",
            }
        ],
        "dependencies": {"WU-001": []},
        "risks": [],
    }


def _write_cleared_artifacts(project_root: Path, worker_id: str = "worker-001") -> None:
    gaijinn = project_root / ".gaijinn"
    workers = gaijinn / "workers"
    worker_dir = workers / worker_id
    worker_dir.mkdir(parents=True, exist_ok=True)
    (worker_dir / "giv.json").write_text(
        json.dumps({"worker_id": worker_id, "allowed_paths": ["src/"], "denied_paths": []}),
        encoding="utf-8",
    )
    write_merge_json(workers / "manifest.json", {"worker_details": [{"worker_id": worker_id}]})
    write_merge_json(gaijinn / "blueprint.json", _minimal_blueprint())
    validated = {
        worker_id: {
            "passed": True,
            "gates": {
                "path_allowlist": {"passed": True, "trespasses": []},
                "scope_isolation": {"passed": True, "violations": []},
            },
            "handoff_integrity": {
                "transaction_bus_synchronized": True,
                "pending_tickets": [],
            },
        }
    }
    write_merge_json(project_root / VALIDATED_PATH, validated)
    write_merge_json(
        project_root / HANDOFF_QUEUE_PATH,
        {
            "transaction_bus_synchronized": True,
            "pending_tickets": [],
            "handoff_tickets_raised": 0,
            "handoff_tickets_resolved": 0,
        },
    )


def _write_rejected_artifacts(
    project_root: Path,
    *,
    worker_id: str = "worker-001",
    trespasses: list[str] | None = None,
    pending_tickets: list[dict[str, str]] | None = None,
    bus_synced: bool = True,
) -> None:
    gaijinn = project_root / ".gaijinn"
    workers = gaijinn / "workers"
    worker_dir = workers / worker_id
    worker_dir.mkdir(parents=True, exist_ok=True)
    (worker_dir / "giv.json").write_text(
        json.dumps({"worker_id": worker_id, "allowed_paths": ["src/"], "denied_paths": []}),
        encoding="utf-8",
    )
    write_merge_json(workers / "manifest.json", {"worker_details": [{"worker_id": worker_id}]})
    write_merge_json(gaijinn / "blueprint.json", _minimal_blueprint())
    validated = {
        worker_id: {
            "passed": False,
            "gates": {
                "path_allowlist": {
                    "passed": not trespasses,
                    "trespasses": trespasses or [],
                },
                "scope_isolation": {"passed": True, "violations": []},
            },
            "handoff_integrity": {
                "transaction_bus_synchronized": bus_synced,
                "pending_tickets": pending_tickets or [],
            },
        }
    }
    write_merge_json(project_root / VALIDATED_PATH, validated)
    write_merge_json(
        project_root / HANDOFF_QUEUE_PATH,
        {
            "transaction_bus_synchronized": bus_synced,
            "pending_tickets": pending_tickets or [],
        },
    )


class TestPreflightCore:
    def test_cleared_when_artifacts_clean(self, tmp_path: Path) -> None:
        _write_cleared_artifacts(tmp_path)
        result = run_preflight_check(
            session_id="sess-test",
            worker_id="worker-001",
            project_path=str(tmp_path),
        )
        assert result.allow_merge is True
        assert result.status_code == "PREFLIGHT_CLEARED"
        assert result.trespass_violations == []
        assert result.pending_tickets_count == 0

    def test_rejected_on_trespass(self, tmp_path: Path) -> None:
        _write_rejected_artifacts(tmp_path, trespasses=["tiny_service/service.py"])
        result = run_preflight_check(
            session_id="sess-test",
            worker_id="worker-001",
            project_path=str(tmp_path),
        )
        assert result.allow_merge is False
        assert result.status_code == "PREFLIGHT_REJECTED"
        assert "tiny_service/service.py" in result.trespass_violations
        assert "workspace_isolation_violation" in result.rejection_reasons

    def test_rejected_on_pending_tickets(self, tmp_path: Path) -> None:
        pending = [
            {
                "ticket_id": "TX-HT-ABC123",
                "target_work_unit_id": "WU-002",
                "target_file": "tiny_service/service.py",
            }
        ]
        _write_rejected_artifacts(tmp_path, pending_tickets=pending, bus_synced=False)
        result = run_preflight_check(
            session_id="sess-test",
            worker_id="worker-001",
            project_path=str(tmp_path),
        )
        assert result.allow_merge is False
        assert result.pending_tickets_count == 1
        assert "pending_handoff_tickets" in result.rejection_reasons

    def test_verify_workspace_isolation_reads_validated_shape(self, tmp_path: Path) -> None:
        _write_rejected_artifacts(tmp_path, trespasses=["src/forbidden.py"])
        violations = verify_workspace_isolation_gate(tmp_path, "worker-001")
        assert violations == ["src/forbidden.py"]

    def test_empty_project_fails_closed(self, tmp_path: Path) -> None:
        result = run_preflight_check(
            session_id="sess-test",
            worker_id="worker-001",
            project_path=str(tmp_path),
        )
        assert result.allow_merge is False
        assert result.status_code == "PREFLIGHT_REJECTED"
        assert "blueprint_missing" in result.rejection_reasons

    def test_resolution_error_without_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GAIJINN_PROJECT_ROOT", raising=False)
        with (
            patch("aoc_supervisor.preflight.VICTORY_LAP_FALLBACK", Path("/nonexistent-victory")),
            pytest.raises(PreflightResolutionError),
        ):
            run_preflight_check(session_id="missing", worker_id="worker-001")


class TestPreflightAPI:
    @pytest.fixture
    def client(self, monkeypatch):
        import aoc_supervisor.api as api

        monkeypatch.setenv("GAIJINN_ALLOW_INSECURE_LOCAL", "1")
        with TestClient(api.app) as test_client:
            yield test_client

    def test_api_cleared_200(self, client: TestClient, tmp_path: Path) -> None:
        _write_cleared_artifacts(tmp_path)
        response = client.post(
            "/api/v1/preflight",
            json={
                "session_id": "sess-live",
                "worker_id": "worker-001",
                "project_path": str(tmp_path),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allow_merge"] is True
        assert data["status_code"] == "PREFLIGHT_CLEARED"

    def test_api_rejected_422(self, client: TestClient, tmp_path: Path) -> None:
        _write_rejected_artifacts(tmp_path, trespasses=["tiny_service/router.py"])
        response = client.post(
            "/api/v1/preflight",
            json={
                "session_id": "sess-live",
                "worker_id": "worker-001",
                "project_path": str(tmp_path),
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["allow_merge"] is False
        assert data["status_code"] == "PREFLIGHT_REJECTED"
        assert "tiny_service/router.py" in data["trespass_violations"]

    def test_api_requires_worker_id(self, client: TestClient) -> None:
        response = client.post("/api/v1/preflight", json={"session_id": "sess-live"})
        assert response.status_code == 400

    @pytest.mark.skipif(
        not Path("/tmp/gaijinn-victory-lap-gateway/.gaijinn/merge/validated.json").exists(),
        reason="victory lap artifacts not present",
    )
    def test_victory_lap_gateway_clears(self) -> None:
        result = run_preflight_check(
            session_id="victory-lap",
            worker_id="worker-001",
            project_path="/tmp/gaijinn-victory-lap-gateway",
        )
        assert result.allow_merge is True
        validated_path = Path("/tmp/gaijinn-victory-lap-gateway/.gaijinn/merge/validated.json")
        validated = json.loads(validated_path.read_text(encoding="utf-8"))
        assert validated["worker-001"]["gates"]["path_allowlist"]["trespasses"] == []
