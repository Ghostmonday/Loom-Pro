"""Spawn recovery, lease, lock lifecycle, and process-group cleanup tests."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from aoc_supervisor.spawn_governance import (
    IdempotencyCorruptError,
    abort_idempotency,
    acquire_supervisor_lease,
    begin_idempotency,
    clear_idempotency_store,
    process_group_alive,
    recover_orphan_process_groups,
    release_supervisor_lease,
    terminate_worker_process,
)


def test_abort_idempotency_preserves_lock_inode(tmp_path: Path) -> None:
    clear_idempotency_store(tmp_path)
    decision = begin_idempotency(
        tmp_path,
        user_id="alice",
        key="lock-stable-01",
        request_hash="hash-a",
    )
    assert decision.record_path is not None
    lock_path = decision.record_path.with_suffix(decision.record_path.suffix + ".lock")
    inode_before = lock_path.stat().st_ino

    abort_idempotency(decision.record_path)

    assert lock_path.exists()
    assert lock_path.stat().st_ino == inode_before


def test_concurrent_idempotency_after_abort_uses_same_lock_inode(tmp_path: Path) -> None:
    clear_idempotency_store(tmp_path)
    first = begin_idempotency(
        tmp_path,
        user_id="alice",
        key="lock-stable-02",
        request_hash="hash-a",
    )
    assert first.record_path is not None
    lock_path = first.record_path.with_suffix(first.record_path.suffix + ".lock")
    inode_before = lock_path.stat().st_ino
    abort_idempotency(first.record_path)

    results: list[str] = []
    barrier = threading.Barrier(2)

    def _attempt() -> None:
        barrier.wait()
        decision = begin_idempotency(
            tmp_path,
            user_id="alice",
            key="lock-stable-02",
            request_hash="hash-a",
        )
        results.append(decision.action)

    threads = [threading.Thread(target=_attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert lock_path.exists()
    assert lock_path.stat().st_ino == inode_before
    assert results.count("proceed") == 1
    assert results.count("in_progress") == 1


def test_valid_json_with_invalid_idempotency_schema_fails_closed(tmp_path: Path) -> None:
    clear_idempotency_store(tmp_path)
    principal_dir = hashlib.sha256(b"alice").hexdigest()[:32]
    record = tmp_path / ".aoc" / "spawn-idempotency" / principal_dir / "schema-bad-01.json"
    record.parent.mkdir(parents=True)
    record.write_text(
        json.dumps({"status": "completed", "response": {"sprint_id": "old"}}),
        encoding="utf-8",
    )

    with pytest.raises(IdempotencyCorruptError):
        begin_idempotency(
            tmp_path,
            user_id="alice",
            key="schema-bad-01",
            request_hash="hash",
        )


def test_second_api_process_cannot_acquire_supervisor_lease(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "0")
    script = textwrap.dedent(
        f"""
        import sys
        from pathlib import Path
        from aoc_supervisor.spawn_governance import acquire_supervisor_lease, SupervisorLeaseError

        try:
            acquire_supervisor_lease(Path({str(tmp_path)!r}))
        except SupervisorLeaseError:
            sys.exit(0)
        sys.exit(1)
        """
    )
    handle = acquire_supervisor_lease(tmp_path)
    try:
        env = {**os.environ, "GAIJINN_ALLOW_MULTI_API_WORKER": "0"}
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=env,
        )
    finally:
        release_supervisor_lease(handle)
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_api_shutdown_terminates_active_process_groups() -> None:
    import aoc_supervisor.api as api

    proc = subprocess.Popen(["sleep", "300"], start_new_session=True)
    pgid = os.getpgid(proc.pid)
    try:
        with api._sprint_lock:
            api._sprints["shutdown-test"] = {
                "status": "running",
                "workspace_key": "shutdown-test",
                "processes": [
                    {
                        "name": "worker-001",
                        "proc": proc,
                        "process_group_id": pgid,
                        "status": "running",
                    }
                ],
            }
        api._terminate_all_active_sprints()
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if proc.poll() is not None or not process_group_alive(pgid):
                break
            time.sleep(0.05)
        assert proc.poll() is not None or not process_group_alive(pgid)
    finally:
        terminate_worker_process(proc, process_group_id=pgid, grace_seconds=0.0)


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_exited_group_leader_still_terminates_process_group() -> None:
    proc = Mock()
    proc.poll.return_value = 1

    with (
        patch("aoc_supervisor.spawn_governance.os.name", "posix"),
        patch("aoc_supervisor.spawn_governance.process_group_alive", return_value=True),
        patch("aoc_supervisor.spawn_governance.os.killpg") as mock_killpg,
        patch("aoc_supervisor.spawn_governance.time.sleep"),
    ):
        terminate_worker_process(proc, process_group_id=424242, grace_seconds=0.0)

    assert mock_killpg.call_count >= 1


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_recover_orphan_process_groups_terminates_persisted_groups(tmp_path: Path) -> None:
    proc = subprocess.Popen(["sleep", "300"], start_new_session=True)
    pgid = os.getpgid(proc.pid)
    runtime = tmp_path / ".aoc" / "spawn-runtime.json"
    runtime.parent.mkdir(parents=True)
    runtime.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sprints": [{"sprint_id": "orphan", "process_group_ids": [pgid]}],
            }
        ),
        encoding="utf-8",
    )
    try:
        recover_orphan_process_groups(tmp_path)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if proc.poll() is not None or not process_group_alive(pgid):
                break
            time.sleep(0.05)
        assert proc.poll() is not None or not process_group_alive(pgid)
        assert not runtime.exists()
    finally:
        terminate_worker_process(proc, process_group_id=pgid, grace_seconds=0.0)
