"""Regression tests for P0 containment (session + assignment)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aoc_cli.blueprint import WorkUnit
from aoc_cli.giv import GIV
from aoc_cli.helpers.workers import _assign_work_units, _worker_giv
from aoc_supervisor.orchestrate_session import OrchestrateSessionStore
from aoc_supervisor.session_security import resolve_confined_session_path, validate_session_id


def test_validate_session_id_rejects_path_escape() -> None:
    with pytest.raises(ValueError):
        validate_session_id("/etc")
    with pytest.raises(ValueError):
        validate_session_id("../sessions/foo")


def test_resolve_confined_session_path(tmp_path: Path) -> None:
    store = OrchestrateSessionStore(tmp_path)
    session_id = "abc123def456"
    session_root = store.sessions_dir / session_id
    session_root.mkdir(parents=True)
    (session_root / ".gaijinn").mkdir()
    (session_root / ".gaijinn" / "session.json").write_text(
        f'{{"session_id": "{session_id}"}}\n',
        encoding="utf-8",
    )
    resolved = resolve_confined_session_path(store.sessions_dir, session_id)
    assert resolved == session_root.resolve()

    with pytest.raises(ValueError):
        resolve_confined_session_path(store.sessions_dir, "/etc")


def test_assign_work_units_no_duplicates() -> None:
    unit = WorkUnit(
        id="WU-1",
        title="t",
        description="d",
        allowed_paths=("src/",),
        acceptance_checks=("ok",),
    )
    assignments = _assign_work_units((unit,), 3)
    assert assignments[1] == (unit,)
    assert assignments[2] == ()
    assert assignments[3] == ()


def test_standby_worker_scoped_to_standby_marker() -> None:
    base = GIV(worker_id="worker-002", allowed_paths=("src/",), denied_paths=())
    giv = _worker_giv(base, "worker-002", (), assignments={1: (), 2: (), 3: ()})
    assert giv.allowed_paths == (".gaijinn/standby/worker-002/",)


def test_validate_path_containment_success(tmp_path: Path) -> None:
    from aoc_cli.moat_authority import set_allowed_roots, unpatch_file_operations, validate_path_containment

    allowed = tmp_path / "allowed"
    allowed.mkdir()

    set_allowed_roots([allowed])
    try:
        # Should not raise
        validate_path_containment(allowed / "file.txt")
        validate_path_containment(allowed / "subdir" / "file.txt")
    finally:
        unpatch_file_operations()


def test_validate_path_containment_failure(tmp_path: Path) -> None:
    from aoc_cli.moat_authority import (
        MoatContainmentError,
        set_allowed_roots,
        unpatch_file_operations,
        validate_path_containment,
    )

    allowed = tmp_path / "allowed"
    allowed.mkdir()
    other = tmp_path / "other"
    other.mkdir()

    set_allowed_roots([allowed])
    try:
        with pytest.raises(MoatContainmentError):
            validate_path_containment(other / "file.txt")
        with pytest.raises(MoatContainmentError):
            validate_path_containment("/etc/passwd")
    finally:
        unpatch_file_operations()


def test_intercept_open_success(tmp_path: Path) -> None:
    from aoc_cli.moat_authority import patch_file_operations, unpatch_file_operations

    allowed = tmp_path / "allowed"
    allowed.mkdir()
    file_path = allowed / "test.txt"

    patch_file_operations([allowed])
    try:
        # Open for writing should succeed
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("hello")

        # Open for reading should succeed
        with open(file_path, encoding="utf-8") as f:
            assert f.read() == "hello"
    finally:
        unpatch_file_operations()


def test_intercept_open_failure(tmp_path: Path) -> None:
    from aoc_cli.moat_authority import MoatContainmentError, patch_file_operations, unpatch_file_operations

    allowed = tmp_path / "allowed"
    allowed.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    forbidden_file = other / "secret.txt"

    patch_file_operations([allowed])
    try:
        with pytest.raises(MoatContainmentError), open(forbidden_file, "w"):
            pass
    finally:
        unpatch_file_operations()


def test_intercept_subprocess_failure(tmp_path: Path) -> None:
    import subprocess

    from aoc_cli.moat_authority import MoatContainmentError, patch_file_operations, unpatch_file_operations

    allowed = tmp_path / "allowed"
    allowed.mkdir()
    other = tmp_path / "other"
    other.mkdir()

    patch_file_operations([allowed])
    try:
        with pytest.raises(MoatContainmentError):
            subprocess.run(["cat", str(other / "secret.txt")], capture_output=True)

        with pytest.raises(MoatContainmentError):
            subprocess.Popen(["ls", str(other)])
    finally:
        unpatch_file_operations()
