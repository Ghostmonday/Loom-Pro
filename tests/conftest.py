"""Pytest configuration for Gaijinn.

GAIJINN BLUEPRINT: mock_grid_client fixture = default terminal smoke env
(GAIJINN_MOCK_GRID=1). Matches ui/gaijinn-ui-intent-map.json smoke_scenarios.
"""

from __future__ import annotations

import json
import os
from unittest.mock import patch

# Deterministic fake reasoning for the full pytest suite unless a test opts out.
os.environ.setdefault("GAIJINN_FAKE_REASONING", "1")
# TestClient now runs app lifespan startup/shutdown; allow parallel test clients.
os.environ.setdefault("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
os.environ.setdefault("GAIJINN_ALLOW_INSECURE_LOCAL", "1")

import pytest
from aoc_supervisor.orchestrate_session import OrchestrateSessionStore
from fastapi.testclient import TestClient


@pytest.fixture
def mock_grid_client(tmp_path, monkeypatch):
    import aoc_supervisor.api as api
    from aoc_supervisor.billing import LocalFileLedgerStorageProvider, clear_sprint_tokens

    monkeypatch.setenv("GAIJINN_MOCK_GRID", "1")
    monkeypatch.setenv("GAIJINN_SEED_TERMINAL_USER", "1")
    monkeypatch.setenv("GAIJINN_ALLOW_INSECURE_LOCAL", "1")
    monkeypatch.setenv("GAIJINN_ALLOW_RAW_INTENT_PREPARE", "1")
    # Snap-packaged terminals set SNAP globally; must not disable repo .venv for gaijinn subprocesses.
    monkeypatch.delenv("SNAP", raising=False)

    ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
    lock_path = tmp_path / ".aoc" / "billing" / "accounts.lock"
    provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)
    provider.write_ledger({"terminal-user": {"balance": "500.00", "status": "active"}})

    workers_dir = tmp_path / ".gaijinn" / "workers"
    workers_dir.mkdir(parents=True)
    for name in ("worker-001", "worker-002"):
        (workers_dir / name).mkdir()
        (workers_dir / name / "WORK_UNIT.md").write_text(f"# {name}\n", encoding="utf-8")
    (workers_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "worker_count": 2,
                "worker_details": [
                    {"worker_id": "worker-001", "status": "created", "assigned_work_units": ["WU-001"]},
                    {"worker_id": "worker-002", "status": "created", "assigned_work_units": ["WU-002"]},
                ],
            }
        ),
        encoding="utf-8",
    )

    session_store = OrchestrateSessionStore(tmp_path)
    clear_sprint_tokens()
    api._sprints.clear()
    with (
        patch.object(api, "DEFAULT_LEDGER_STORAGE", provider),
        patch.object(api, "ROOT_DIR", tmp_path),
        patch.object(api, "WORKERS_DIR", workers_dir),
        patch.object(api, "SCRATCH_DIR", tmp_path / ".gaijinn" / "scratch"),
        patch.object(api, "_session_store", session_store),
        TestClient(api.app) as client,
    ):
        yield client, workers_dir, tmp_path, session_store
