"""Spawn governance: idempotency, concurrency caps, and worker timeout cleanup."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from aoc_supervisor.spawn_governance import (
    SpawnLimitError,
    clear_idempotency_store,
    collect_spawn_metrics,
    enforce_spawn_limits,
    normalize_idempotency_key,
    parse_spawn_timeout,
    parse_spawn_workers,
    spawn_request_fingerprint,
)
from fastapi.testclient import TestClient

from tests.test_supervisor import SAMPLE_ACI_PAYLOAD, _spawn_headers


def test_normalize_idempotency_key_rejects_short_keys() -> None:
    with pytest.raises(ValueError):
        normalize_idempotency_key("short")


def test_parse_spawn_workers_rejects_boolean() -> None:
    with pytest.raises(ValueError, match="boolean"):
        parse_spawn_workers(True)


def test_parse_spawn_timeout_rejects_invalid_string() -> None:
    with pytest.raises(ValueError, match="integer"):
        parse_spawn_timeout("invalid", default=30)


def test_spawn_request_fingerprint_changes_when_payload_changes() -> None:
    base = {
        "workers": 1,
        "sprint_token": "tok-a",
        "session_id": "",
        "model": "m",
        "executor": "auto",
        "task": "",
        "timeout": 30,
    }
    first = spawn_request_fingerprint(user_id="alice", body=base)
    second = spawn_request_fingerprint(user_id="alice", body={**base, "workers": 2})
    assert first != second


def test_enforce_spawn_limits_rejects_worker_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAIJINN_MAX_ACTIVE_WORKERS", "1")
    metrics = collect_spawn_metrics(
        {
            "1": {
                "status": "running",
                "started_at": time.time(),
                "processes": [
                    {"name": "worker-001", "proc": Mock(poll=Mock(return_value=None)), "status": "running"},
                ],
            }
        }
    )
    with pytest.raises(SpawnLimitError, match="active worker cap"):
        enforce_spawn_limits(metrics, requested_workers=1)


def test_collect_timed_out_workers_marks_processes() -> None:
    import aoc_supervisor.api as api

    proc = Mock()
    proc.poll.return_value = None
    sprint = {
        "started_at": time.time() - 120,
        "processes": [
            {
                "name": "worker-001",
                "proc": proc,
                "status": "running",
                "started_at": time.time() - 120,
            }
        ],
    }
    doomed = api._collect_timed_out_worker_processes(sprint, timeout=30)
    assert len(doomed) == 1
    assert doomed[0]["proc"] is proc
    assert sprint["processes"][0]["status"] == "timed_out"


def test_classify_sprint_terminal_status_prefers_timed_out() -> None:
    from aoc_supervisor.spawn_governance import classify_sprint_terminal_status

    sprint = {
        "processes": [
            {"status": "timed_out", "proc": Mock(poll=Mock(return_value=1))},
            {"status": "failed", "proc": Mock(poll=Mock(return_value=1))},
        ]
    }
    assert classify_sprint_terminal_status(sprint) == "timed_out"


class TestGridSpawnGovernance:
    @pytest.fixture
    def spawn_client(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        import aoc_supervisor.api as api
        from aoc_supervisor.billing import LocalFileLedgerStorageProvider, clear_sprint_tokens

        monkeypatch.setenv("GAIJINN_MOCK_GRID", "1")
        monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
        clear_idempotency_store(tmp_path)
        from aoc_supervisor.spawn_governance import clear_spawn_runtime

        clear_spawn_runtime(tmp_path)
        clear_sprint_tokens()

        ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
        lock_path = tmp_path / ".aoc" / "billing" / "accounts.lock"
        provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)
        provider.write_ledger({"alice": {"balance": "100.00", "status": "active"}})

        workers_dir = tmp_path / ".gaijinn" / "workers"
        workers_dir.mkdir(parents=True)
        (workers_dir / "manifest.json").write_text(
            '{"worker_details": [{"worker_id": "worker-001", "status": "created"}]}',
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
                yield client, provider, api
            finally:
                with api._sprint_lock:
                    api._sprints.clear()
                    api._spawn_reservations.clear()

    def test_spawn_requires_idempotency_key(self, spawn_client) -> None:
        client, _provider, _api = spawn_client
        response = client.post("/api/v1/grid/spawn", json={"workers": 1}, headers={"X-User-Id": "alice"})
        assert response.status_code == 400
        assert "Idempotency-Key" in response.json()["detail"]

    def test_spawn_idempotent_replay_returns_cached_response(self, spawn_client) -> None:
        client, provider, _api = spawn_client
        headers = _spawn_headers(idempotency_key="idem-replay-001")

        purchase = client.post(
            "/api/v1/blueprint/purchase",
            json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
            headers={"X-User-Id": "alice"},
        ).json()
        balance_after_purchase = provider.read_ledger()["alice"]["balance"]

        first = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": purchase["sprint_token"]},
            headers=headers,
        )
        assert first.status_code == 200
        balance_after_spawn = provider.read_ledger()["alice"]["balance"]
        assert balance_after_spawn < balance_after_purchase

        second = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": purchase["sprint_token"]},
            headers=headers,
        )
        assert second.status_code == 200
        assert second.json()["idempotent_replay"] is True
        assert second.json()["sprint_id"] == first.json()["sprint_id"]
        assert provider.read_ledger()["alice"]["balance"] == balance_after_spawn

    def test_spawn_rejects_concurrent_worker_cap(self, spawn_client, monkeypatch: pytest.MonkeyPatch) -> None:
        client, _provider, api = spawn_client
        monkeypatch.setenv("GAIJINN_MAX_ACTIVE_WORKERS", "1")

        busy_proc = Mock()
        busy_proc.poll.return_value = None
        with api._sprint_lock:
            api._sprints.clear()
            api._sprints["busy"] = {
                "status": "running",
                "started_at": time.time(),
                "session_id": None,
                "workspace_key": "other-workspace-key",
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
            headers=_spawn_headers(idempotency_key="idem-cap-blocked"),
        )
        assert response.status_code == 429
        assert "active worker cap" in response.json()["detail"]

    def test_spawn_invalid_timeout_has_no_side_effects(self, spawn_client) -> None:
        client, provider, _api = spawn_client

        purchase = client.post(
            "/api/v1/blueprint/purchase",
            json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
            headers={"X-User-Id": "alice"},
        ).json()
        balance_after_purchase = provider.read_ledger()["alice"]["balance"]

        with patch("aoc_supervisor.api.subprocess.Popen") as mock_popen:
            response = client.post(
                "/api/v1/grid/spawn",
                json={"workers": 1, "sprint_token": purchase["sprint_token"], "timeout": "invalid"},
                headers=_spawn_headers(idempotency_key="idem-invalid-timeout"),
            )

        assert response.status_code == 400
        assert "timeout" in response.json()["detail"].lower()
        mock_popen.assert_not_called()
        assert provider.read_ledger()["alice"]["balance"] == balance_after_purchase

        retry = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": purchase["sprint_token"]},
            headers=_spawn_headers(idempotency_key="idem-invalid-timeout-2"),
        )
        assert retry.status_code == 200

    def test_spawn_completion_write_failure_rolls_back(self, spawn_client) -> None:
        client, provider, api = spawn_client

        purchase = client.post(
            "/api/v1/blueprint/purchase",
            json={**SAMPLE_ACI_PAYLOAD, "workers": 1},
            headers={"X-User-Id": "alice"},
        ).json()
        balance_after_purchase = provider.read_ledger()["alice"]["balance"]

        with patch("aoc_supervisor.api.complete_idempotency", side_effect=OSError("disk full")):
            response = client.post(
                "/api/v1/grid/spawn",
                json={"workers": 1, "sprint_token": purchase["sprint_token"]},
                headers=_spawn_headers(idempotency_key="idem-complete-fail"),
            )

        assert response.status_code == 500
        assert "idempotency completion failed" in response.json()["detail"]
        assert provider.read_ledger()["alice"]["balance"] == balance_after_purchase
        with api._sprint_lock:
            assert not api._sprints
            assert not api._spawn_reservations

        retry = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 1, "sprint_token": purchase["sprint_token"]},
            headers=_spawn_headers(idempotency_key="idem-complete-fail-2"),
        )
        assert retry.status_code == 200
