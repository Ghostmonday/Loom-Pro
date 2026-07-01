"""Spawn governance: idempotency keys, concurrency caps, and limit helpers.

Capacity reservations and sprint registry are process-local. A supervisor API lease
enforces a single API worker per deployment unless GAIJINN_ALLOW_MULTI_API_WORKER=1.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import signal
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX only
    msvcrt = None  # type: ignore[assignment]

_IDEMPOTENCY_KEY_RE = re.compile(r"^[a-zA-Z0-9_-]{8,128}$")
_IDEMPOTENCY_STALE_SECONDS = int(os.environ.get("GAIJINN_IDEMPOTENCY_STALE_SECONDS", "300"))
_IDEMPOTENCY_SCHEMA_VERSION = 1
_SPAWN_RUNTIME_SCHEMA_VERSION = 1
_MIN_SPAWN_TIMEOUT = 1
_DEFAULT_MAX_SPAWN_TIMEOUT = 7200
_SUPPORTED_IDEMPOTENCY_STATUSES = frozenset({"in_progress", "completed"})


class SpawnLimitError(Exception):
    """Raised when a spawn request would exceed configured resource limits."""


class WorkspaceBusyError(SpawnLimitError):
    """Raised when a workers_root already has an active or reserved sprint."""


class IdempotencyCorruptError(Exception):
    """Raised when an idempotency record exists but cannot be parsed (fail closed)."""


class SupervisorLeaseError(Exception):
    """Raised when another API worker already holds the deployment lease."""


@dataclass(frozen=True)
class SpawnMetrics:
    active_workers: int
    active_sprints: int
    session_active_workers: int
    reserved_workers: int
    reserved_sprints: int


@dataclass(frozen=True)
class IdempotencyDecision:
    """Outcome of an idempotency pre-check before spawn side effects."""

    action: str  # proceed | replay | conflict | in_progress | corrupt
    response: dict[str, Any] | None = None
    record_path: Path | None = None


@dataclass
class CapacityReservation:
    reservation_id: str
    workers: int
    workspace_key: str
    session_id: str | None = None
    sprint_id: str | None = None
    created_at: float = field(default_factory=time.time)


def max_active_workers() -> int:
    return max(1, int(os.environ.get("GAIJINN_MAX_ACTIVE_WORKERS", "32")))


def max_concurrent_sprints() -> int:
    return max(1, int(os.environ.get("GAIJINN_MAX_CONCURRENT_SPRINTS", "8")))


def max_workers_per_session() -> int:
    return max(1, int(os.environ.get("GAIJINN_MAX_WORKERS_PER_SESSION", "16")))


def max_spawn_timeout() -> int:
    return max(_MIN_SPAWN_TIMEOUT, int(os.environ.get("GAIJINN_MAX_SPAWN_TIMEOUT", str(_DEFAULT_MAX_SPAWN_TIMEOUT))))


def require_spawn_idempotency_key() -> bool:
    return os.environ.get("GAIJINN_REQUIRE_SPAWN_IDEMPOTENCY", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def allow_multi_api_worker() -> bool:
    return os.environ.get("GAIJINN_ALLOW_MULTI_API_WORKER", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def extract_idempotency_key(headers: Mapping[str, str], body: Mapping[str, Any] | None) -> str | None:
    for header_name in ("x-idempotency-key", "X-Idempotency-Key"):
        value = str(headers.get(header_name, "")).strip()
        if value:
            return value
    if isinstance(body, dict):
        value = str(body.get("idempotency_key", "")).strip()
        if value:
            return value
    return None


def normalize_idempotency_key(raw: str) -> str:
    key = raw.strip()
    if not _IDEMPOTENCY_KEY_RE.match(key):
        raise ValueError("idempotency key must be 8-128 characters (letters, digits, underscore, hyphen)")
    return key


def normalize_workspace_key(workers_root: str | Path) -> str:
    resolved = Path(workers_root).expanduser().resolve()
    digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()
    return digest[:32]


def parse_spawn_workers(raw: Any) -> int:
    if isinstance(raw, bool):
        raise ValueError("workers must be an integer, not a boolean")
    if not isinstance(raw, int):
        raise ValueError("workers must be a positive integer")
    if raw < 1:
        raise ValueError("workers must be a positive integer")
    return raw


def parse_spawn_timeout(raw: Any, *, default: int) -> int:
    if raw is None:
        value = default
    elif isinstance(raw, bool):
        raise ValueError("timeout must be an integer, not a boolean")
    elif isinstance(raw, int):
        value = raw
    elif isinstance(raw, str):
        stripped = raw.strip()
        if not stripped.isdigit():
            raise ValueError("timeout must be an integer number of seconds")
        value = int(stripped)
    else:
        raise ValueError("timeout must be an integer number of seconds")
    ceiling = max_spawn_timeout()
    if value < _MIN_SPAWN_TIMEOUT or value > ceiling:
        raise ValueError(f"timeout must be between {_MIN_SPAWN_TIMEOUT} and {ceiling} seconds")
    return value


def spawn_request_fingerprint(*, user_id: str, body: Mapping[str, Any]) -> str:
    payload = {
        "user_id": user_id,
        "workers": body.get("workers"),
        "sprint_token": body.get("sprint_token"),
        "session_id": body.get("session_id"),
        "model": body.get("model"),
        "executor": body.get("executor"),
        "task": body.get("task"),
        "timeout": body.get("timeout"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _idempotency_root(project_root: Path) -> Path:
    return project_root / ".aoc" / "spawn-idempotency"


def _spawn_runtime_path(project_root: Path) -> Path:
    return project_root / ".aoc" / "spawn-runtime.json"


def _supervisor_lease_path(project_root: Path) -> Path:
    return project_root / ".aoc" / "supervisor.api.lock"


def _principal_dir_name(user_id: str) -> str:
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    return digest[:32]


def _record_path(project_root: Path, user_id: str, key: str) -> Path:
    principal_dir = _principal_dir_name(user_id)
    safe_key = normalize_idempotency_key(key)
    return _idempotency_root(project_root) / principal_dir / f"{safe_key}.json"


def _lock_path(record_path: Path) -> Path:
    return record_path.with_suffix(record_path.suffix + ".lock")


def _locking_available() -> bool:
    return fcntl is not None or msvcrt is not None


def _acquire_handle_lock(handle: IO[str], *, blocking: bool) -> None:
    if fcntl is not None:
        flags = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
        fcntl.flock(handle.fileno(), flags)
        return
    if msvcrt is not None:
        flags = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
        msvcrt.locking(handle.fileno(), flags, 1)
        return
    raise RuntimeError("file locking is unavailable on this platform")


def _release_handle_lock(handle: IO[str]) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return
    if msvcrt is not None:
        with contextlib.suppress(OSError):
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


@contextlib.contextmanager
def _exclusive_file_lock(lock_file: Path):
    if not _locking_available():
        raise RuntimeError("spawn idempotency requires POSIX fcntl or Windows msvcrt locking")
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with lock_file.open("a+", encoding="utf-8") as handle:
        _acquire_handle_lock(handle, blocking=True)
        try:
            yield
        finally:
            _release_handle_lock(handle)


def _validate_idempotency_record(
    record: Mapping[str, Any],
    *,
    expected_key: str,
    expected_user_id: str,
) -> None:
    version = record.get("schema_version")
    if version != _IDEMPOTENCY_SCHEMA_VERSION:
        raise IdempotencyCorruptError("idempotency record schema version unsupported")

    stored_key = str(record.get("key", "")).strip()
    stored_user = str(record.get("user_id", "")).strip()
    request_hash = str(record.get("request_hash", "")).strip()
    status = str(record.get("status", "")).strip()

    if not stored_key or not stored_user or not request_hash:
        raise IdempotencyCorruptError("idempotency record missing required identity fields")
    if stored_key != normalize_idempotency_key(expected_key):
        raise IdempotencyCorruptError("idempotency record key mismatch")
    if stored_user != expected_user_id:
        raise IdempotencyCorruptError("idempotency record principal mismatch")
    if status not in _SUPPORTED_IDEMPOTENCY_STATUSES:
        raise IdempotencyCorruptError(f"idempotency record status unsupported: {status}")

    if status == "completed":
        response = record.get("response")
        if not isinstance(response, dict) or not str(response.get("sprint_id", "")).strip():
            raise IdempotencyCorruptError("completed idempotency record requires response.sprint_id")
        return

    started_at = record.get("started_at")
    if not isinstance(started_at, (int, float)):
        raise IdempotencyCorruptError("in_progress idempotency record requires numeric started_at")


def _new_idempotency_record(*, key: str, user_id: str, request_hash: str, started_at: float) -> dict[str, Any]:
    return {
        "schema_version": _IDEMPOTENCY_SCHEMA_VERSION,
        "key": normalize_idempotency_key(key),
        "user_id": user_id,
        "request_hash": request_hash,
        "status": "in_progress",
        "started_at": started_at,
        "sprint_id": None,
        "response": None,
    }


def _read_record_locked(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise IdempotencyCorruptError(f"idempotency record unreadable: {path}") from exc
    if not text.strip():
        raise IdempotencyCorruptError(f"idempotency record empty: {path}")
    try:
        record = json.loads(text)
    except json.JSONDecodeError as exc:
        raise IdempotencyCorruptError(f"idempotency record corrupt: {path}") from exc
    if not isinstance(record, dict):
        raise IdempotencyCorruptError(f"idempotency record invalid: {path}")
    return record


def _atomic_write_json(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(record), indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def begin_idempotency(
    project_root: Path,
    *,
    user_id: str,
    key: str,
    request_hash: str,
    sprint_alive: Callable[[str], bool] | None = None,
) -> IdempotencyDecision:
    """Reserve or replay an idempotent grid spawn under an exclusive record lock."""
    path = _record_path(project_root, user_id, key)
    lock = _lock_path(path)
    now = time.time()
    with _exclusive_file_lock(lock):
        existing = _read_record_locked(path) if path.is_file() else None
        if existing is not None:
            _validate_idempotency_record(existing, expected_key=key, expected_user_id=user_id)
            stored_hash = str(existing.get("request_hash", ""))
            status = str(existing.get("status", ""))
            if stored_hash != request_hash:
                return IdempotencyDecision(action="conflict")
            if status == "completed" and isinstance(existing.get("response"), dict):
                return IdempotencyDecision(action="replay", response=dict(existing["response"]))
            if status == "in_progress":
                started = float(existing.get("started_at", now))
                sprint_id = str(existing.get("sprint_id", "")).strip()
                if now - started < _IDEMPOTENCY_STALE_SECONDS:
                    return IdempotencyDecision(action="in_progress")
                if sprint_id and sprint_alive is not None and sprint_alive(sprint_id):
                    return IdempotencyDecision(action="in_progress")
        record = _new_idempotency_record(key=key, user_id=user_id, request_hash=request_hash, started_at=now)
        _atomic_write_json(path, record)
        return IdempotencyDecision(action="proceed", record_path=path)


def attach_idempotency_sprint(record_path: Path, sprint_id: str) -> None:
    lock = _lock_path(record_path)
    with _exclusive_file_lock(lock):
        record = _read_record_locked(record_path)
        if record is None:
            raise IdempotencyCorruptError(f"missing idempotency record: {record_path}")
        _validate_idempotency_record(
            record,
            expected_key=str(record.get("key", "")),
            expected_user_id=str(record.get("user_id", "")),
        )
        record["sprint_id"] = sprint_id
        _atomic_write_json(record_path, record)


def complete_idempotency(record_path: Path, response: Mapping[str, Any], *, sprint_id: str | None = None) -> None:
    lock = _lock_path(record_path)
    with _exclusive_file_lock(lock):
        record = _read_record_locked(record_path)
        if record is None:
            raise IdempotencyCorruptError(f"missing idempotency record: {record_path}")
        _validate_idempotency_record(
            record,
            expected_key=str(record.get("key", "")),
            expected_user_id=str(record.get("user_id", "")),
        )
        record["status"] = "completed"
        record["completed_at"] = time.time()
        record["response"] = dict(response)
        if sprint_id:
            record["sprint_id"] = sprint_id
        _atomic_write_json(record_path, record)


def abort_idempotency(record_path: Path | None) -> None:
    """Delete only the JSON record. Lock files remain for stable inode locking."""
    if record_path is None:
        return
    lock = _lock_path(record_path)
    with _exclusive_file_lock(lock):
        record_path.unlink(missing_ok=True)


def clear_idempotency_store(project_root: Path) -> None:
    root = _idempotency_root(project_root)
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            with contextlib.suppress(OSError):
                path.rmdir()
    with contextlib.suppress(OSError):
        root.rmdir()


def acquire_supervisor_lease(project_root: Path) -> IO[str] | None:
    """Acquire a process-lifetime API singleton lease. Lock file is never unlinked."""
    if allow_multi_api_worker():
        return None
    if not _locking_available():
        raise SupervisorLeaseError("supervisor lease requires POSIX fcntl or Windows msvcrt locking")
    path = _supervisor_lease_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        _acquire_handle_lock(handle, blocking=False)
    except (BlockingIOError, OSError) as exc:
        handle.close()
        raise SupervisorLeaseError(
            "another API worker holds the supervisor lease "
            "(run a single API process or set GAIJINN_ALLOW_MULTI_API_WORKER=1)"
        ) from exc
    return handle


def release_supervisor_lease(handle: IO[str] | None) -> None:
    if handle is None:
        return
    try:
        _release_handle_lock(handle)
    finally:
        handle.close()


def process_group_alive(process_group_id: int | None) -> bool:
    if process_group_id is None or os.name != "posix":
        return False
    try:
        os.killpg(process_group_id, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def resolve_process_group_id(proc: Any) -> int | None:
    if proc is None or os.name != "posix":
        return None
    pid = getattr(proc, "pid", None)
    if not isinstance(pid, int):
        return None
    try:
        return os.getpgid(pid)
    except (ProcessLookupError, OSError):
        return pid


def _process_is_running(entry: Mapping[str, Any]) -> bool:
    if not isinstance(entry, dict):
        return False
    process_group_id = entry.get("process_group_id")
    if isinstance(process_group_id, int) and process_group_alive(process_group_id):
        return True
    proc = entry.get("proc")
    if proc is None:
        return False
    # Handle both subprocess.Popen and asyncio.subprocess.Process
    poll = getattr(proc, "poll", None)
    if callable(poll):
        exit_code = poll()
    else:
        exit_code = getattr(proc, "returncode", None)
    if exit_code is None:
        return True
    status = str(entry.get("status", ""))
    return status in {"running", "spawned"}


def _sprint_is_active(sprint: Mapping[str, Any]) -> bool:
    if classify_sprint_terminal_status(sprint) == "running":
        return True
    sprint_status = str(sprint.get("status", ""))
    return sprint_status == "running"


def _occupied_workspace_keys(
    sprints: Mapping[str, Mapping[str, Any]],
    reservations: Mapping[str, CapacityReservation] | None = None,
) -> set[str]:
    occupied: set[str] = set()
    for sprint in sprints.values():
        if not isinstance(sprint, dict):
            continue
        workspace_key = str(sprint.get("workspace_key", "")).strip()
        if workspace_key and _sprint_is_active(sprint):
            occupied.add(workspace_key)
    for reservation in (reservations or {}).values():
        workspace_key = str(reservation.workspace_key).strip()
        if workspace_key:
            occupied.add(workspace_key)
    return occupied


def enforce_workspace_exclusion(
    sprints: Mapping[str, Mapping[str, Any]],
    reservations: Mapping[str, CapacityReservation] | None,
    workspace_key: str,
) -> None:
    if workspace_key in _occupied_workspace_keys(sprints, reservations):
        raise WorkspaceBusyError("workspace already has an active or reserved sprint")


def collect_spawn_metrics(
    sprints: Mapping[str, Mapping[str, Any]],
    *,
    reservations: Mapping[str, CapacityReservation] | None = None,
    session_id: str | None = None,
) -> SpawnMetrics:
    active_workers = 0
    active_sprints = 0
    session_active_workers = 0
    reserved_workers = 0
    reserved_sprints = 0
    normalized_session = (session_id or "").strip()

    for sprint in sprints.values():
        if not isinstance(sprint, dict):
            continue
        processes = sprint.get("processes", [])
        running_in_sprint = 0
        if isinstance(processes, list):
            for entry in processes:
                if isinstance(entry, dict) and _process_is_running(entry):
                    active_workers += 1
                    running_in_sprint += 1
        sprint_status = str(sprint.get("status", ""))
        if running_in_sprint > 0 or sprint_status == "running":
            active_sprints += 1
        if normalized_session and str(sprint.get("session_id", "")).strip() == normalized_session:
            session_active_workers += running_in_sprint

    for reservation in (reservations or {}).values():
        reserved_workers += reservation.workers
        reserved_sprints += 1
        if normalized_session and (reservation.session_id or "").strip() == normalized_session:
            session_active_workers += reservation.workers

    return SpawnMetrics(
        active_workers=active_workers + reserved_workers,
        active_sprints=active_sprints + reserved_sprints,
        session_active_workers=session_active_workers,
        reserved_workers=reserved_workers,
        reserved_sprints=reserved_sprints,
    )


def enforce_spawn_limits(
    metrics: SpawnMetrics,
    *,
    requested_workers: int,
    session_id: str | None = None,
) -> None:
    if requested_workers < 1:
        raise SpawnLimitError("workers must be a positive integer")

    if metrics.active_workers + requested_workers > max_active_workers():
        raise SpawnLimitError(
            f"active worker cap exceeded ({metrics.active_workers + requested_workers} > {max_active_workers()})"
        )

    if metrics.active_sprints + 1 > max_concurrent_sprints():
        raise SpawnLimitError(
            f"concurrent sprint cap exceeded ({metrics.active_sprints + 1} > {max_concurrent_sprints()})"
        )

    if session_id and metrics.session_active_workers + requested_workers > max_workers_per_session():
        raise SpawnLimitError(
            "session worker cap exceeded "
            f"({metrics.session_active_workers + requested_workers} > {max_workers_per_session()})"
        )


def reserve_spawn_capacity(
    sprints: Mapping[str, Mapping[str, Any]],
    reservations: dict[str, CapacityReservation],
    *,
    requested_workers: int,
    workspace_key: str,
    session_id: str | None,
    sprint_id: str,
) -> CapacityReservation:
    """Reserve capacity slots. Caller must hold the sprint registry lock."""
    enforce_workspace_exclusion(sprints, reservations, workspace_key)
    metrics = collect_spawn_metrics(sprints, reservations=reservations, session_id=session_id)
    enforce_spawn_limits(metrics, requested_workers=requested_workers, session_id=session_id)
    reservation = CapacityReservation(
        reservation_id=sprint_id,
        workers=requested_workers,
        workspace_key=workspace_key,
        session_id=session_id or None,
        sprint_id=sprint_id,
    )
    reservations[sprint_id] = reservation
    return reservation


def release_spawn_reservation(reservations: dict[str, CapacityReservation], reservation_id: str | None) -> None:
    if reservation_id:
        reservations.pop(reservation_id, None)


def classify_sprint_terminal_status(sprint: Mapping[str, Any]) -> str:
    processes = sprint.get("processes", [])
    if not isinstance(processes, list) or not processes:
        return str(sprint.get("status", "completed"))
    statuses: list[str] = []
    for entry in processes:
        if not isinstance(entry, dict):
            continue
        process_group_id = entry.get("process_group_id")
        if isinstance(process_group_id, int) and process_group_alive(process_group_id):
            return "running"
        proc = entry.get("proc")
        if proc is not None and getattr(proc, "poll", lambda: None)() is None:
            return "running"
        statuses.append(str(entry.get("status", "")))
    if any(status == "timed_out" for status in statuses):
        return "timed_out"
    if any(status not in {"", "completed"} for status in statuses):
        return "failed"
    return "completed"


def popen_worker_process(*args: Any, **kwargs: Any):
    """Start a worker subprocess in its own POSIX session when supported."""
    import subprocess

    if os.name == "posix":
        kwargs.setdefault("start_new_session", True)
    return subprocess.Popen(*args, **kwargs)  # noqa: S603


def terminate_worker_process(
    proc: Any = None,
    *,
    process_group_id: int | None = None,
    grace_seconds: float = 5.0,
) -> None:
    pgid = process_group_id
    if pgid is None and proc is not None and os.name == "posix":
        pgid = resolve_process_group_id(proc)

    if os.name == "posix" and isinstance(pgid, int):
        if not process_group_alive(pgid):
            return
        with contextlib.suppress(ProcessLookupError):
            os.killpg(pgid, signal.SIGTERM)
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline:
            if not process_group_alive(pgid):
                return
            time.sleep(0.05)
        with contextlib.suppress(ProcessLookupError):
            os.killpg(pgid, signal.SIGKILL)
        if proc is not None:
            with contextlib.suppress(Exception):
                proc.wait(timeout=2)
        return

    if proc is None or getattr(proc, "poll", lambda: None)() is not None:
        return
    with contextlib.suppress(ProcessLookupError):
        proc.terminate()
    with contextlib.suppress(Exception):
        proc.wait(timeout=grace_seconds)
    if getattr(proc, "poll", lambda: None)() is None:
        with contextlib.suppress(ProcessLookupError):
            proc.kill()


def terminate_sprint_processes(sprint: Mapping[str, Any], *, grace_seconds: float = 5.0) -> None:
    processes = sprint.get("processes", [])
    if not isinstance(processes, list):
        return
    for entry in processes:
        if not isinstance(entry, dict):
            continue
        terminate_worker_process(
            entry.get("proc"),
            process_group_id=entry.get("process_group_id") if isinstance(entry.get("process_group_id"), int) else None,
            grace_seconds=grace_seconds,
        )


def write_spawn_runtime(project_root: Path, sprints: Mapping[str, Mapping[str, Any]]) -> None:
    active: list[dict[str, Any]] = []
    for sprint_id, sprint in sprints.items():
        if not isinstance(sprint, dict) or classify_sprint_terminal_status(sprint) != "running":
            continue
        group_ids: list[int] = []
        for entry in sprint.get("processes", []):
            if not isinstance(entry, dict):
                continue
            pgid = entry.get("process_group_id")
            if isinstance(pgid, int):
                group_ids.append(pgid)
        active.append(
            {
                "sprint_id": sprint_id,
                "workspace_key": sprint.get("workspace_key"),
                "process_group_ids": group_ids,
            }
        )
    payload = {"schema_version": _SPAWN_RUNTIME_SCHEMA_VERSION, "sprints": active}
    _atomic_write_json(_spawn_runtime_path(project_root), payload)


def clear_spawn_runtime(project_root: Path) -> None:
    path = _spawn_runtime_path(project_root)
    path.unlink(missing_ok=True)


def recover_orphan_process_groups(project_root: Path) -> None:
    path = _spawn_runtime_path(project_root)
    if not path.is_file():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        path.unlink(missing_ok=True)
        return
    if not isinstance(payload, dict):
        path.unlink(missing_ok=True)
        return
    for sprint in payload.get("sprints", []):
        if not isinstance(sprint, dict):
            continue
        for pgid in sprint.get("process_group_ids", []):
            if isinstance(pgid, int):
                terminate_worker_process(process_group_id=pgid, grace_seconds=0.0)
    path.unlink(missing_ok=True)
