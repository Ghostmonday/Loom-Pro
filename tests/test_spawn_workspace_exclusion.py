"""Workspace-root exclusion tests for grid spawn."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from aoc_supervisor.spawn_governance import (
    WorkspaceBusyError,
    normalize_workspace_key,
    reserve_spawn_capacity,
)
from fastapi.testclient import TestClient

from tests.test_supervisor import SAMPLE_ACI_PAYLOAD, _spawn_headers


def test_reserve_spawn_capacity_rejects_occupied_workspace() -> None:
    sprints = {
        "busy": {
            "status": "running",
            "workspace_key": "workspace-a",
            "processes": [{"name": "worker-001", "proc": Mock(poll=Mock(return_value=None)), "status": "running"}],
        }
    }
    reservations: dict = {}
    with pytest.raises(WorkspaceBusyError, match="workspace already"):
        reserve_spawn_capacity(
            sprints,
            reservations,
            requested_workers=1,
            workspace_key="workspace-a",
            session_id=None,
            sprint_id="next",
        )


@pytest.fixture
def workspace_spawn_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import aoc_supervisor.api as api
    from aoc_supervisor.billing import LocalFileLedgerStorageProvider, clear_sprint_tokens
    from aoc_supervisor.spawn_governance import clear_idempotency_store, clear_spawn_runtime

    monkeypatch.setenv("GAIJINN_MOCK_GRID", "1")
    monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
    clear_idempotency_store(tmp_path)
    clear_spawn_runtime(tmp_path)
    clear_sprint_tokens()

    ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
    lock_path = tmp_path / ".aoc" / "billing" / "accounts.lock"
    provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)
    provider.write_ledger({"alice": {"balance": "100.00", "status": "active"}})

    workers_dir = tmp_path / ".gaijinn" / "workers"
    workers_dir.mkdir(parents=True)
    (workers_dir / "manifest.json").write_text(
        json.dumps({"worker_details": [{"worker_id": "worker-001", "status": "created"}]}),
        encoding="utf-8",
    )
    (workers_dir / "worker-001").mkdir()
    (workers_dir / "worker-001" / "output.log").write_text("", encoding="utf-8")

    with (
        patch.object(api, "DEFAULT_LEDGER_STORAGE", provider),
        patch.object(api, "ROOT_DIR", tmp_path),
        patch.object(api, "WORKERS_DIR", workers_dir),
        patch.object(api, "SCRATCH_DIR", tmp_path / ".gaijinn" / "scratch"),
        patch("aoc_supervisor.api.subprocess.Popen") as mock_popen,
        TestClient(api.app) as client,
    ):
        mock_proc = mock_popen.return_value
        mock_proc.pid = 4242
        with api._sprint_lock:
            api._sprints.clear()
            api._spawn_reservations.clear()
        try:
            yield client, api, workers_dir
        finally:
            with api._sprint_lock:
                api._sprints.clear()
                api._spawn_reservations.clear()


def test_two_global_spawns_cannot_share_worker_directories(workspace_spawn_client) -> None:
    client, api, workers_dir = workspace_spawn_client
    workspace_key = normalize_workspace_key(workers_dir)
    busy_proc = Mock()
    busy_proc.poll.return_value = None

    with api._sprint_lock:
        api._sprints["busy"] = {
            "status": "running",
            "started_at": time.time(),
            "workspace_key": workspace_key,
            "processes": [{"name": "worker-001", "proc": busy_proc, "status": "running"}],
        }

    purchase = client.post(
        "/api/v1/blueprint/purchase",
        json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
        headers={"X-User-Id": "alice"},
    ).json()

    response = client.post(
        "/api/v1/grid/spawn",
        json={"workers": 1, "sprint_token": purchase["sprint_token"]},
        headers=_spawn_headers(idempotency_key="global-workspace-key-b"),
    )
    assert response.status_code == 429
    assert "workspace already" in response.json()["detail"]


def test_two_session_spawns_cannot_share_session_worker_root(workspace_spawn_client, tmp_path: Path) -> None:
    client, api, _workers_dir = workspace_spawn_client
    session_id = "sess-workspace-excl"
    session_root = tmp_path / "sessions" / session_id
    session_workers = session_root / ".gaijinn" / "workers"
    session_workers.mkdir(parents=True)
    (session_workers / "manifest.json").write_text(
        json.dumps({"worker_details": [{"worker_id": "worker-001", "status": "created"}]}),
        encoding="utf-8",
    )
    (session_workers / "worker-001").mkdir()
    (session_workers / "worker-001" / "output.log").write_text("", encoding="utf-8")

    workspace_key = normalize_workspace_key(session_workers)
    busy_proc = Mock()
    busy_proc.poll.return_value = None

    with api._sprint_lock:
        api._sprints["busy-session"] = {
            "status": "running",
            "started_at": time.time(),
            "session_id": session_id,
            "workspace_key": workspace_key,
            "processes": [{"name": "worker-001", "proc": busy_proc, "status": "running"}],
        }

    purchase = client.post(
        "/api/v1/blueprint/purchase",
        json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
        headers={"X-User-Id": "alice"},
    ).json()

    with (
        patch.object(api._session_store, "project_root", return_value=session_root),
        patch.object(api._session_store, "workers_dir", return_value=session_workers),
        patch("aoc_supervisor.api.assert_session_owner"),
    ):
        response = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": purchase["sprint_token"], "session_id": session_id},
            headers=_spawn_headers(idempotency_key="session-workspace-key-b"),
        )

    assert response.status_code == 429
    assert "workspace already" in response.json()["detail"]
