"""Adversarial concurrency tests for spawn governance primitives."""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from aoc_supervisor.spawn_governance import (
    CapacityReservation,
    IdempotencyCorruptError,
    begin_idempotency,
    clear_idempotency_store,
    collect_spawn_metrics,
    reserve_spawn_capacity,
    terminate_worker_process,
)


def test_concurrent_idempotency_reservation_allows_one_proceed(tmp_path: Path) -> None:
    clear_idempotency_store(tmp_path)
    results: list[str] = []
    barrier = threading.Barrier(2)

    def _attempt() -> None:
        barrier.wait()
        decision = begin_idempotency(
            tmp_path,
            user_id="alice",
            key="race-key-001",
            request_hash="same-hash",
        )
        results.append(decision.action)

    threads = [threading.Thread(target=_attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert "proceed" in results
    assert results.count("proceed") == 1
    assert results.count("in_progress") == 1


def test_corrupt_idempotency_record_fails_closed(tmp_path: Path) -> None:
    clear_idempotency_store(tmp_path)
    principal_dir = hashlib.sha256(b"alice").hexdigest()[:32]
    record = tmp_path / ".aoc" / "spawn-idempotency" / principal_dir / "race-key-002.json"
    record.parent.mkdir(parents=True)
    record.write_text("{not-json", encoding="utf-8")

    with pytest.raises(IdempotencyCorruptError):
        begin_idempotency(
            tmp_path,
            user_id="alice",
            key="race-key-002",
            request_hash="hash",
        )


def test_concurrent_capacity_reservation_allows_one_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAIJINN_MAX_ACTIVE_WORKERS", "2")
    monkeypatch.setenv("GAIJINN_MAX_CONCURRENT_SPRINTS", "2")
    sprints: dict[str, dict] = {}
    reservations: dict[str, CapacityReservation] = {}
    busy_proc = Mock()
    busy_proc.poll.return_value = None
    sprints["busy"] = {
        "status": "running",
        "session_id": None,
        "processes": [{"name": "worker-001", "proc": busy_proc, "status": "running"}],
    }
    outcomes: list[str] = []
    barrier = threading.Barrier(2)
    lock = threading.Lock()

    def _attempt(reservation_id: str) -> None:
        barrier.wait()
        try:
            with lock:
                reserve_spawn_capacity(
                    sprints,
                    reservations,
                    requested_workers=1,
                    workspace_key=f"workspace-{reservation_id}",
                    session_id=None,
                    sprint_id=reservation_id,
                )
            outcomes.append("reserved")
        except Exception:
            outcomes.append("rejected")

    threads = [
        threading.Thread(target=_attempt, args=("res-a",)),
        threading.Thread(target=_attempt, args=("res-b",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert outcomes.count("reserved") == 1
    assert outcomes.count("rejected") == 1
    metrics = collect_spawn_metrics(sprints, reservations=reservations)
    assert metrics.active_workers == 2


def test_idempotency_key_fingerprint_conflict(tmp_path: Path) -> None:
    clear_idempotency_store(tmp_path)
    begin_idempotency(
        tmp_path,
        user_id="alice",
        key="race-key-003",
        request_hash="hash-a",
    )
    decision = begin_idempotency(
        tmp_path,
        user_id="alice",
        key="race-key-003",
        request_hash="hash-b",
    )
    assert decision.action == "conflict"


def test_process_group_termination_targets_group() -> None:
    proc = Mock()
    proc.poll.return_value = 1
    proc.pid = 9999
    proc.wait.return_value = None

    with (
        patch("aoc_supervisor.spawn_governance.os.name", "posix"),
        patch("aoc_supervisor.spawn_governance.process_group_alive", return_value=True),
        patch("aoc_supervisor.spawn_governance.os.killpg") as mock_killpg,
        patch("aoc_supervisor.spawn_governance.time.sleep"),
    ):
        terminate_worker_process(proc, process_group_id=8888, grace_seconds=0.0)

    assert mock_killpg.call_count >= 1
    signals = [call.args[1] for call in mock_killpg.call_args_list]
    import signal

    assert signal.SIGTERM in signals
