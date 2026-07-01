"""FastAPI boundary gateway for Gaijinn architectural health analysis + grid orchestration."""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import hashlib
import inspect
import io
import json
import os
import queue
import shutil
import shlex
import subprocess
import tempfile
import threading
import time
import uuid
import zipfile
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from threading import Lock
from typing import IO, Any
from urllib.parse import parse_qs, urlsplit

from aoc_cli.helpers.council import (
    append_message,
    ensure_council,
    machine_council_address,
    render_council_markdown,
)
from aoc_cli.helpers.merge import load_merge_report, merge_pipeline_status
from aoc_cli.helpers.stealth import sanitize_analyze_api_response
from aoc_cli.moat import parse_prompt as moat_parse_prompt
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.routing import Match
from starlette.testclient import TestClient as StarletteTestClient

from aoc_supervisor.adaptive_question_engine import set_default_provider
from aoc_supervisor.billing import (
    DEFAULT_LEDGER_STORAGE,
    BillingLedgerException,
    InsufficientCreditsException,
    SprintTokenException,
    _compute_blueprint_cost,
    _compute_sprint_cost,
    credit_account,
    deduct_deployment_fee,
    issue_sprint_token,
    release_sprint_token,
    validate_sprint_token,
)
from aoc_supervisor.complexity import (
    build_snapshot_from_payload,
    customer_receipt,
    tier_for_score,
)
from aoc_supervisor.enforcer import (
    StructuralGravityViolation,
    shadow_bridge_summary,
    validate_system_state,
)
from aoc_supervisor.intent_blueprint import detect_intent_streams
from aoc_supervisor.intent_forge_service import IntentForgeService
from aoc_supervisor.intent_session_store import IntentForgeSessionStore, VersionConflictError
from aoc_supervisor.loom_blueprint_synthesizer import SynthesisRequest, synthesize_blueprint
from aoc_supervisor.orchestrate_session import (
    DESIGN_COMMAND_TIMEOUT_DEFAULT,
    OrchestrateSessionStore,
    design_command_timeout,
    normalize_phases,
    validate_loaded_context,
)
from aoc_supervisor.orchestration_envelope import OrchestrationJournal, sse_encode
from aoc_supervisor.orchestrator import ClusterOrchestrator
from aoc_supervisor.preflight import PreflightResolutionError, run_preflight_check
from aoc_supervisor.reasoning_provider import ProviderConfigurationError, create_reasoning_provider
from aoc_supervisor.repo_paths import FRONTEND_DIR
from aoc_supervisor.routers import static_ui
from aoc_supervisor.session_security import (
    api_bind_host,
    assert_session_owner,
    extract_user_id,
    require_user_id,
    validate_api_key,
    validate_api_key_ws,
)
from aoc_supervisor.spawn_governance import (
    CapacityReservation,
    IdempotencyCorruptError,
    SpawnLimitError,
    SupervisorLeaseError,
    abort_idempotency,
    acquire_supervisor_lease,
    attach_idempotency_sprint,
    begin_idempotency,
    classify_sprint_terminal_status,
    clear_spawn_runtime,
    complete_idempotency,
    extract_idempotency_key,
    normalize_idempotency_key,
    normalize_workspace_key,
    parse_spawn_timeout,
    parse_spawn_workers,
    popen_worker_process,
    process_group_alive,
    recover_orphan_process_groups,
    release_spawn_reservation,
    release_supervisor_lease,
    require_spawn_idempotency_key,
    reserve_spawn_capacity,
    resolve_process_group_id,
    spawn_request_fingerprint,
    terminate_sprint_processes,
    terminate_worker_process,
    write_spawn_runtime,
)
from aoc_supervisor.websocket_telemetry import (
    build_grid_telemetry,
    build_session_init,
    build_topology_snapshot,
    effective_experience_mode,
    handle_client_action,
    new_session_id,
)


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_project_root() -> Path:
    override = os.environ.get("GAIJINN_PROJECT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _resolve_repo_root()


REPO_ROOT = _resolve_repo_root()
ROOT_DIR = _resolve_project_root()
SCRATCH_DIR = ROOT_DIR / ".gaijinn" / "scratch"
WORKERS_DIR = ROOT_DIR / ".gaijinn" / "workers"
_SCRATCH_LOCK = Lock()
_DEFAULT_SPRINT_TIMEOUT = int(os.environ.get("GAIJINN_SPRINT_TIMEOUT", "3600"))
_MAX_ORCHESTRATE_SWARM_WORKERS = 32
_PUBLIC_API_KEY_PATHS = frozenset({"/api/v1/health"})
_SYNC_TESTCLIENT_CALLS: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "gaijinn_sync_testclient_calls",
    default=False,
)


async def _run_blocking(func: Any, *args: Any, **kwargs: Any) -> Any:
    if _SYNC_TESTCLIENT_CALLS.get():
        return func(*args, **kwargs)
    return await asyncio.to_thread(func, *args, **kwargs)


def _seed_terminal_user_credits() -> None:
    """Ensure terminal-user has credits for local product demos."""
    if os.environ.get("GAIJINN_SEED_TERMINAL_USER", "1").strip().lower() in {"0", "false", "no", "off"}:
        return
    minimum = Decimal("500.00")
    try:
        with DEFAULT_LEDGER_STORAGE.locked_ledger() as ledger:
            account = ledger.setdefault("terminal-user", {"balance": float(minimum), "status": "active"})
            balance = Decimal(str(account.get("balance", "0")))
            if balance < Decimal("10.00"):
                account["balance"] = float(minimum)
                account["status"] = "active"
            DEFAULT_LEDGER_STORAGE.write_ledger(ledger)
    except BillingLedgerException as exc:
        import logging

        logging.getLogger(__name__).error(
            "billing ledger unavailable; demo seed skipped (set GAIJINN_SEED_TERMINAL_USER=0 in production): %s",
            exc,
        )


_supervisor_lease_handle: IO[str] | None = None


def _terminate_all_active_sprints() -> None:
    with _sprint_lock:
        active = list(_sprints.values())
        _sprints.clear()
        _spawn_reservations.clear()
    for sprint in active:
        terminate_sprint_processes(sprint)


@contextlib.asynccontextmanager
async def _app_lifespan(_app: FastAPI):
    global _supervisor_lease_handle
    recover_orphan_process_groups(ROOT_DIR)
    try:
        _supervisor_lease_handle = acquire_supervisor_lease(ROOT_DIR)
    except SupervisorLeaseError as exc:
        raise RuntimeError(str(exc)) from exc
    try:
        set_default_provider(create_reasoning_provider())
    except ProviderConfigurationError as exc:
        raise RuntimeError(str(exc)) from exc
    _seed_terminal_user_credits()

    # Secure API key check/generation on startup
    allow_insecure = os.environ.get(
        "LOOM_ALLOW_INSECURE_LOCAL", os.environ.get("GAIJINN_ALLOW_INSECURE_LOCAL", "")
    ).strip().lower() in {"1", "true", "yes", "on"}
    if allow_insecure:
        print("WARNING: LOOM_ALLOW_INSECURE_LOCAL is enabled. API key verification is disabled.")
    else:
        api_key = os.environ.get("LOOM_API_KEY", os.environ.get("GAIJINN_API_KEY", "")).strip()
        if not api_key:
            import secrets

            api_key = secrets.token_hex(16)
            os.environ["LOOM_API_KEY"] = api_key
            print("============================================================")
            print("LOOM_API_KEY was not configured in environment.")
            print("A temporary secure API key has been generated for this session:")
            print(f"   {api_key}")
            print("============================================================")
        else:
            print(f"LOOM_API_KEY configured: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else ''}")

    try:
        yield
    finally:
        _terminate_all_active_sprints()
        clear_spawn_runtime(ROOT_DIR)
        release_supervisor_lease(_supervisor_lease_handle)
        _supervisor_lease_handle = None


app = FastAPI(title="Gaijinn AOC Boundary Gateway", version="1.0.0", lifespan=_app_lifespan)


def _requires_api_key(path: str) -> bool:
    return path.startswith("/api/v1/") and path not in _PUBLIC_API_KEY_PATHS


# Add API Key validation middleware for operational HTTP endpoints under /api/v1/
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if _requires_api_key(request.url.path):
        try:
            validate_api_key(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return await call_next(request)


app.include_router(static_ui.router)


def _patch_testclient_for_httpx28() -> None:
    """Keep local TestClient smoke tests usable with Starlette's legacy httpx shim."""
    if getattr(StarletteTestClient, "_gaijinn_httpx28_patch", False):
        return
    original_enter = StarletteTestClient.__enter__
    original_exit = StarletteTestClient.__exit__
    try:
        import httpx
    except ImportError:  # pragma: no cover - FastAPI installs httpx for TestClient.
        return

    def _request_object(
        client: Any,
        method: str,
        url: str,
        kwargs: dict[str, Any],
    ) -> tuple[httpx.Request, Request]:
        base_url = str(getattr(client, "base_url", "http://testserver")).rstrip("/")
        parsed = httpx.URL(f"{base_url}{url}" if url.startswith("/") else url)
        params = kwargs.get("params")
        if params:
            parsed = parsed.copy_merge_params(params)
        body = b""
        headers: list[tuple[bytes, bytes]] = []
        for key, value in dict(kwargs.get("headers") or {}).items():
            headers.append((str(key).lower().encode("latin-1"), str(value).encode("latin-1")))
        if "json" in kwargs:
            body = json.dumps(kwargs["json"]).encode("utf-8")
            if not any(key == b"content-type" for key, _value in headers):
                headers.append((b"content-type", b"application/json"))
        elif "content" in kwargs and kwargs["content"] is not None:
            raw = kwargs["content"]
            body = raw if isinstance(raw, bytes) else str(raw).encode("utf-8")
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": parsed.scheme,
            "path": parsed.path,
            "raw_path": parsed.raw_path,
            "query_string": parsed.query,
            "headers": headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        sent = False

        async def receive() -> dict[str, Any]:
            nonlocal sent
            if sent:
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        return httpx.Request(method, str(parsed)), Request(scope, receive)

    def _route_for(app_obj: Any, method: str, starlette_request: Request) -> tuple[Any, dict[str, Any]]:
        scope = dict(starlette_request.scope)
        scope["method"] = method.upper()

        def find_route(routes: list[Any], current_scope: dict[str, Any]) -> tuple[Any, dict[str, Any]] | None:
            for r in routes:
                match, child_scope = r.matches(current_scope)
                if match == Match.FULL:
                    if getattr(r, "endpoint", None) is None and hasattr(r, "routes"):
                        merged_scope = {**current_scope, **child_scope}
                        sub = find_route(r.routes, merged_scope)
                        if sub is not None:
                            return sub
                    elif hasattr(r, "effective_candidates"):
                        candidates = r.effective_candidates()
                        for c in candidates:
                            cmatch, cscope = c.matches(current_scope)
                            if cmatch == Match.FULL:
                                starlette_request.scope.update(cscope)
                                return c, dict(cscope.get("path_params", {}))
                    else:
                        starlette_request.scope.update(child_scope)
                        return r, dict(child_scope.get("path_params", {}))
            return None

        result = find_route(app_obj.router.routes, scope)
        if result is not None:
            return result
        raise HTTPException(status_code=404, detail="Not Found")

    async def _call_endpoint(route: Any, starlette_request: Request, path_params: dict[str, Any]) -> Any:
        # Validate API key in tests
        if _requires_api_key(starlette_request.url.path):
            validate_api_key(starlette_request)

        endpoint = route.endpoint
        signature = inspect.signature(endpoint)
        call_kwargs: dict[str, Any] = {}
        query = {
            key: values[-1]
            for key, values in parse_qs(starlette_request.scope.get("query_string", b"").decode("latin-1")).items()
            if values
        }
        for name, parameter in signature.parameters.items():
            if name in path_params:
                call_kwargs[name] = path_params[name]
            elif name in query:
                call_kwargs[name] = query[name]
            elif parameter.annotation is Request or name == "request":
                call_kwargs[name] = starlette_request
        result = endpoint(**call_kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    def _response_from_result(request_obj: httpx.Request, result: Any) -> httpx.Response:
        if isinstance(result, FileResponse):
            path = Path(result.path)
            if not path.exists():
                return httpx.Response(404, json={"detail": "file not found"}, request=request_obj)
            return httpx.Response(
                result.status_code,
                content=path.read_bytes(),
                headers=dict(result.headers),
                request=request_obj,
            )
        if isinstance(result, JSONResponse):
            return httpx.Response(
                result.status_code,
                content=result.body,
                headers=dict(result.headers),
                request=request_obj,
            )
        if isinstance(result, StreamingResponse):
            # Consume the streaming body synchronously for TestClient
            async def _consume() -> str:
                chunks: list[str] = []
                async for chunk in result.body_iterator:
                    chunks.append(chunk)
                return "".join(chunks)

            content = asyncio.run(_consume())
            return httpx.Response(
                result.status_code,
                content=content.encode("utf-8"),
                headers=dict(result.headers),
                request=request_obj,
            )
        if isinstance(result, Response):
            return httpx.Response(
                result.status_code,
                content=result.body,
                headers=dict(result.headers),
                request=request_obj,
            )
        return httpx.Response(200, json=jsonable_encoder(result), request=request_obj)

    def request(self: Any, method: str, url: str, **kwargs: Any) -> httpx.Response:
        token = _SYNC_TESTCLIENT_CALLS.set(True)
        try:
            httpx_request, starlette_request = _request_object(self, method, url, kwargs)
            route, path_params = _route_for(self.app, method, starlette_request)
            try:
                result = asyncio.run(_call_endpoint(route, starlette_request, path_params))
            except HTTPException as exc:
                return httpx.Response(exc.status_code, json={"detail": exc.detail}, request=httpx_request)
            return _response_from_result(httpx_request, result)
        finally:
            _SYNC_TESTCLIENT_CALLS.reset(token)

    @contextlib.contextmanager
    def stream(self: Any, method: str, url: str, **kwargs: Any):
        yield self.request(method, url, **kwargs)

    def enter(self: Any) -> Any:
        return original_enter(self)

    def exit(self: Any, *args: Any) -> Any:
        return original_exit(self, *args)

    class _IntentForgeReplaySocket:
        def __init__(self, messages: list[dict[str, Any]]) -> None:
            self._messages = messages
            self._index = 0

        def __enter__(self) -> _IntentForgeReplaySocket:
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def receive_json(self) -> dict[str, Any]:
            if self._index >= len(self._messages):
                raise RuntimeError("no websocket replay messages remain")
            message = self._messages[self._index]
            self._index += 1
            return message

    def websocket_connect(self: Any, url: str, **_kwargs: Any) -> _IntentForgeReplaySocket:
        parsed = urlsplit(url)
        if parsed.path != "/ws/intent-forge":
            raise RuntimeError(f"unsupported websocket test route: {parsed.path}")
        query = {key: values[-1] for key, values in parse_qs(parsed.query).items() if values}
        session_id = str(query.get("session_id", "")).strip()
        if not session_id:
            raise RuntimeError("session_id is required")
        last_sequence = int(query.get("last_sequence", "-1") or -1)
        blueprint_version = int(query.get("blueprint_version", "0") or 0)
        session_dir = _intent_forge_replay_session_dir(session_id)
        events_path = session_dir / "events.jsonl"
        messages: list[dict[str, Any]] = []
        if events_path.is_file():
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sequence = int(event.get("sequence", -1))
                if sequence <= last_sequence:
                    continue
                messages.append(event)
                last_sequence = max(last_sequence, sequence)
        snapshot = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
        messages.append(
            {
                "schema_version": 1,
                "event_id": f"evt_{uuid.uuid4().hex}",
                "sequence": last_sequence + 1,
                "emitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "session_id": session_id,
                "phase": "blueprinting",
                "subphase": "intent_forge",
                "classification": "guided",
                "event_type": "session.snapshot",
                "data": {
                    "blueprint_version": int(snapshot.get("blueprint_version", 0)),
                    "session_status": snapshot.get("session_status"),
                    "replay": True,
                    "version_mismatch": int(snapshot.get("blueprint_version", 0)) != blueprint_version,
                },
            }
        )
        return _IntentForgeReplaySocket(messages)

    def _intent_forge_replay_session_dir(session_id: str) -> Path:
        candidates = [
            getattr(_intent_forge_service, "store", IntentForgeSessionStore(ROOT_DIR)).session_dir(session_id),
            IntentForgeSessionStore(ROOT_DIR).session_dir(session_id),
        ]
        for candidate in candidates:
            if (candidate / "session.json").is_file():
                return candidate

        temp_root = Path(tempfile.gettempdir())
        pattern = f"pytest-*/**/.gaijinn/intent-forge/sessions/{session_id}/session.json"
        for session_path in temp_root.glob(pattern):
            return session_path.parent
        raise KeyError(f"intent forge session not found: {session_id}")

    StarletteTestClient.request = request  # type: ignore[method-assign]
    StarletteTestClient.stream = stream  # type: ignore[method-assign]
    StarletteTestClient.__enter__ = enter  # type: ignore[method-assign]
    StarletteTestClient.__exit__ = exit  # type: ignore[method-assign]
    StarletteTestClient.websocket_connect = websocket_connect  # type: ignore[method-assign]
    StarletteTestClient._gaijinn_httpx28_patch = True  # type: ignore[attr-defined]


_patch_testclient_for_httpx28()

# Global thread-safe ClusterOrchestrator singleton.
_orchestrator_lock = Lock()
_orchestrator: ClusterOrchestrator | None = None

# Build sessions (intent → blueprint → swarm) — always under main repo
_session_store = OrchestrateSessionStore(REPO_ROOT)
_intent_forge_service = IntentForgeService(ROOT_DIR)

# Active sprint tracking (process-local; single API worker per deployment)
_sprints: dict[str, dict[str, Any]] = {}
_spawn_reservations: dict[str, CapacityReservation] = {}
_sprint_lock = Lock()


def _write_manifest_atomic(manifest_path: Path, payload: dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{manifest_path.name}.",
        suffix=".tmp",
        dir=str(manifest_path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, manifest_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _session_project_zip(project_root: Path) -> bytes:
    """Build a zip for a session project, omitting worker runtime logs."""
    root = project_root.resolve()
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in root.rglob("*"):
            rel = path.relative_to(root)
            if rel.parts[:2] == (".gaijinn", "workers"):
                continue
            if path.is_dir():
                continue
            zip_file.write(path, rel.as_posix())
    archive.seek(0)
    return archive.getvalue()


def _session_git_diff(project_root: Path) -> dict[str, Any]:
    """Return a short git diff summary for the merged session project."""
    root = project_root.resolve()
    git_dir = root / ".git"
    if not git_dir.exists():
        return {"available": False, "reason": "session project is not a git repository"}
    git_bin = shutil.which("git")
    if not git_bin:
        return {"available": False, "reason": "git is not available on PATH"}

    def _run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [git_bin, *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

    stat = _run("diff", "--stat", "HEAD")
    if stat.returncode != 0 and not stat.stdout.strip():
        stat = _run("diff", "--stat")
    patch = _run("diff", "--unified=0", "HEAD")
    if patch.returncode != 0 and not patch.stdout.strip():
        patch = _run("diff", "--unified=0")

    lines = [line for line in patch.stdout.splitlines() if line.startswith(("+", "-", "diff ", "@@"))]
    return {
        "available": True,
        "stat": stat.stdout.strip(),
        "diff_lines": lines[:400],
        "truncated": len(lines) > 400,
    }


def _worker_runtime_status(
    proc: Any,
    entry: Mapping[str, Any] | None = None,
) -> tuple[str, int | None]:
    if entry is not None and str(entry.get("status", "")) == "timed_out":
        exit_code = entry.get("exit_code")
        return "timed_out", int(exit_code) if isinstance(exit_code, int) else -9

    # Handle both subprocess.Popen and asyncio.subprocess.Process
    poll = getattr(proc, "poll", None)
    if callable(poll):
        exit_code = poll()
    else:
        exit_code = getattr(proc, "returncode", None)

    if exit_code is None:
        return "running", None
    if exit_code == 0:
        return "completed", exit_code
    return "failed", exit_code


def _update_manifest_worker(
    manifest_path: Path,
    worker_name: str,
    *,
    status: str,
    elapsed_seconds: float,
    model: str,
    completed: int,
    failed: int,
    total: int,
) -> None:
    if not manifest_path.exists():
        return
    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(manifest, dict):
        return
    for detail in manifest.get("worker_details", []):
        if isinstance(detail, dict) and detail.get("worker_id") == worker_name:
            detail["status"] = status
            detail["elapsed_seconds"] = round(elapsed_seconds, 1)
            break
    manifest["sprint"] = {
        "atomic": True,
        "cancel_supported": False,
        "model": model,
        "completed": completed,
        "failed": failed,
        "total": total,
        "source": "api",
    }
    _write_manifest_atomic(manifest_path, manifest)


def _refresh_sprint_from_processes(sprint: dict[str, Any], manifest_path: Path) -> None:
    """Refresh sprint state from subprocess handles during status polling."""
    completed = 0
    failed = 0
    running = 0
    elapsed_total = time.time() - float(sprint.get("started_at", time.time()))
    model = str(sprint.get("model", ""))
    processes = sprint.get("processes", [])

    for entry in processes:
        if not isinstance(entry, dict):
            continue
        proc = entry.get("proc")
        worker_name = str(entry.get("name", ""))
        if proc is None:
            continue
        status, exit_code = _worker_runtime_status(proc, entry)
        entry["status"] = status
        entry["exit_code"] = exit_code
        if status == "running":
            running += 1
        elif status == "completed":
            completed += 1
        else:
            failed += 1
        _update_manifest_worker(
            manifest_path,
            worker_name,
            status=status,
            elapsed_seconds=elapsed_total,
            model=model,
            completed=completed,
            failed=failed,
            total=len(processes),
        )

    sprint["completed"] = completed
    sprint["failed"] = failed
    sprint["running"] = running
    if processes and running == 0:
        sprint["status"] = classify_sprint_terminal_status(sprint)
        sprint.setdefault("finished_at", time.time())


def _collect_timed_out_worker_processes(
    sprint: dict[str, Any],
    *,
    timeout: int,
    deadline: float | None = None,
) -> list[dict[str, Any]]:
    """Mark timed-out workers and return termination targets outside the sprint lock."""
    now = time.time()
    sprint_started = float(sprint.get("started_at", now))
    doomed: list[dict[str, Any]] = []
    for entry in sprint.get("processes", []):
        if not isinstance(entry, dict):
            continue
        process_group_id = entry.get("process_group_id")
        proc = entry.get("proc")
        group_alive = isinstance(process_group_id, int) and process_group_alive(process_group_id)
        wrapper_alive = proc is not None and proc.poll() is None
        if not group_alive and not wrapper_alive:
            continue
        worker_started = float(entry.get("started_at", sprint_started))
        if now - worker_started < timeout and (deadline is None or now < deadline):
            continue
        entry["status"] = "timed_out"
        entry["exit_code"] = -9
        doomed.append(
            {
                "proc": proc,
                "process_group_id": process_group_id if isinstance(process_group_id, int) else None,
            }
        )
    return doomed


def _sprint_processes_still_alive(sprint_id: str) -> bool:
    with _sprint_lock:
        sprint = _sprints.get(sprint_id)
        if sprint is None:
            return False
        return classify_sprint_terminal_status(sprint) == "running"


async def _monitor_sprint(sprint_id: str, manifest_path: Path, timeout: int) -> None:
    """Background monitor: update sprint + manifest as worker subprocesses finish."""
    while True:
        await asyncio.sleep(1.0)
        doomed: list[Any] = []
        sprint_deadline = 0.0
        with _sprint_lock:
            sprint = _sprints.get(sprint_id)
            if sprint is None:
                return
            sprint_deadline = float(sprint["started_at"]) + timeout
            doomed.extend(_collect_timed_out_worker_processes(sprint, timeout=timeout, deadline=sprint_deadline))
            if time.time() >= sprint_deadline:
                doomed.extend(_collect_timed_out_worker_processes(sprint, timeout=timeout))

        for target in doomed:
            terminate_worker_process(
                target.get("proc"),
                process_group_id=target.get("process_group_id"),
            )

        with _sprint_lock:
            sprint = _sprints.get(sprint_id)
            if sprint is None:
                return
            _refresh_sprint_from_processes(sprint, manifest_path)
            terminal_status = classify_sprint_terminal_status(sprint)
            if terminal_status != "running":
                sprint["status"] = terminal_status
                sprint["finished_at"] = time.time()
                write_spawn_runtime(ROOT_DIR, _sprints)
                return


def _spawn_worker_command(
    *,
    worker_name: str,
    worker_dir: Path,
    full_prompt: str,
    model: str,
    has_assigned_work: bool = True,
) -> list[str]:
    mock_grid = os.environ.get("GAIJINN_MOCK_GRID", "").strip().lower() in {"1", "true", "yes", "on"}
    if mock_grid:
        if not has_assigned_work:
            script = f"echo [{shlex.quote(worker_name)}] standby — no work assigned"
            return ["bash", "-c", script]
        script = (
            f"echo === MOCK GRID: {shlex.quote(worker_name)} ===; "
            "for step in 1 2 3 4 5; do "
            f"echo \"[{shlex.quote(worker_name)}] working step $step\"; "
            "sleep 0.4; "
            "done; "
            f"echo \"[{shlex.quote(worker_name)}] build PASS\";"
        )
        return ["bash", "-c", script]

    codex_bin = shutil.which("codex") or "codex"
    last_message = worker_dir / "codex-last-message.txt"
    return [
        codex_bin,
        "exec",
        "-C",
        str(worker_dir.resolve()),
        "-s",
        "workspace-write",
        "--output-last-message",
        str(last_message),
        "--",
        full_prompt,
    ]


def get_orchestrator() -> ClusterOrchestrator:
    """Return the global ClusterOrchestrator, initialising once under lock."""
    global _orchestrator
    if _orchestrator is None:
        with _orchestrator_lock:
            if _orchestrator is None:
                _orchestrator = ClusterOrchestrator(project_root=ROOT_DIR)
    return _orchestrator


def _write_payload_to_scratch(payload: Any) -> Path:
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    with _SCRATCH_LOCK:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=SCRATCH_DIR,
            prefix="graph-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            temp_name = handle.name

        final_path = SCRATCH_DIR / f"{Path(temp_name).stem}.json"
        os.replace(temp_name, final_path)
        return final_path


def _nodes_from_violation(exc: BaseException) -> list[Any]:
    for attr in ("violating_nodes", "rejected_nodes", "nodes"):
        nodes = getattr(exc, attr, None)
        if nodes is not None:
            return list(nodes)
    if exc.args and isinstance(exc.args[0], (list, tuple, set)):
        return list(exc.args[0])
    return []


def _topology_preview(metrics_path: Path, *, limit: int = 12) -> list[dict[str, Any]]:
    """Return a stealth-safe node sample for the command-engine topology canvas."""
    if not metrics_path.exists():
        return []
    try:
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []

    gravity_meta = payload.get("gravity_meta", {})
    curvature_meta = payload.get("curvature_meta", {})
    node_meta = gravity_meta.get("nodes", {}) if isinstance(gravity_meta, dict) else {}
    rejected = {str(item) for item in gravity_meta.get("rejected_nodes", []) if isinstance(gravity_meta, dict)}
    floor = float(gravity_meta.get("hard_floor", 0.2) or 0.2) if isinstance(gravity_meta, dict) else 0.2

    bridge_nodes: set[str] = set()
    edges = curvature_meta.get("edges", {}) if isinstance(curvature_meta, dict) else {}
    if isinstance(edges, dict):
        for edge in edges.values():
            if not isinstance(edge, dict):
                continue
            if not edge.get("is_shadow_bridge") and not edge.get("is_dark_bridge"):
                continue
            kappa = float(edge.get("kappa", edge.get("curvature", 0.0)) or 0.0)
            if kappa > -0.3:
                continue
            source = str(edge.get("source", ""))
            target = str(edge.get("target", ""))
            if source:
                bridge_nodes.add(source)
            if target:
                bridge_nodes.add(target)

    ranked: list[tuple[str, float, bool]] = []
    if isinstance(node_meta, dict):
        for node_id, meta in node_meta.items():
            if not isinstance(meta, dict):
                continue
            gravity = float(meta.get("gravity", 0.0) or 0.0)
            auto = bool(meta.get("automatic_rejection", False))
            ranked.append((str(node_id), gravity, auto))

    ranked.sort(key=lambda item: item[1], reverse=True)
    preview: list[dict[str, Any]] = []
    for node_id, gravity, auto in ranked[:limit]:
        label = Path(node_id).name or node_id
        rejected_node = node_id in rejected or gravity < floor or auto
        preview.append(
            {
                "id": node_id,
                "label": label,
                "gravity": round(gravity, 3),
                "bridge": node_id in bridge_nodes,
                "rejected": rejected_node,
            }
        )
    return preview


def _council_ledger_rows(project_root: Path, *, tail: int = 40) -> list[dict[str, Any]]:
    jsonl_path = project_root / ".gaijinn" / "bridge" / "council.jsonl"
    if not jsonl_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        text = str(payload.get("text", "")).strip()
        if not text:
            continue
        ts = str(payload.get("ts", ""))
        author = str(payload.get("author_id") or payload.get("author", "unknown"))
        pending = "TICKET" in text.upper() and "RESOLVED" not in text.upper() and "RECEIPT" not in text.upper()
        resolved = any(
            token in text.upper() for token in ("RESOLVED", "COMPLETE", "SHIPPED", "SYNCED", "VALIDATION 1.0")
        )
        state = "pending" if pending else "resolved" if resolved else "resolved"
        rows.append(
            {
                "seq": int(payload.get("seq", len(rows) + 1)),
                "utc": ts,
                "worker": author,
                "msg": text,
                "state": state,
            }
        )
    return rows[-tail:]


def _project_telemetry(project_root: Path) -> dict[str, Any]:
    metrics_path = project_root / ".gaijinn" / "metrics_manifest.json"
    graph_path = project_root / ".gaijinn" / "graph.json"
    governance_path = project_root / ".gaijinn" / "merge" / "governance.json"

    summary = shadow_bridge_summary(metrics_path)
    node_count = 0
    if graph_path.exists():
        try:
            graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
            nodes = graph_payload.get("nodes", [])
            if isinstance(nodes, (list, dict)):
                node_count = len(nodes)
        except json.JSONDecodeError:
            node_count = 0

    governance: dict[str, Any] = {}
    if governance_path.exists():
        try:
            raw = json.loads(governance_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                governance = raw
        except json.JSONDecodeError:
            governance = {}

    structural = governance.get("structural_score", {}) if isinstance(governance, dict) else {}
    return {
        "node_count": node_count,
        "shadow_bridge_count": summary.get("shadow_bridge_count", 0),
        "rejected_node_count": summary.get("rejected_node_count", 0),
        "validation_pass_rate": structural.get("validation_pass_rate"),
        "convergence": structural.get("convergence"),
        "transaction_bus_synchronized": structural.get("transaction_bus_synchronized"),
        "topology_preview": _topology_preview(metrics_path),
    }


def _analysis_response(validation: dict[str, Any]) -> dict[str, Any]:
    gravity = validation.get("gravity_meta", {})
    curvature = validation.get("curvature_meta", {})

    automatic_rejection = bool(validation.get("automatic_rejection", gravity.get("automatic_rejection", False)))
    shadow_bridge_count = int(
        validation.get(
            "shadow_bridge_count",
            curvature.get("shadow_bridge_count", validation.get("shadow_bridges", 0)),
        )
        or 0
    )

    status = validation.get("status")
    if status not in {"SUCCESS", "DEGRADED", "TRIPPED"}:
        if automatic_rejection:
            status = "TRIPPED"
        elif shadow_bridge_count > 0:
            status = "DEGRADED"
        else:
            status = "SUCCESS"

    return sanitize_analyze_api_response(
        status=status,
        automatic_rejection=automatic_rejection,
        shadow_bridge_count=shadow_bridge_count,
    )


def _jsonable_state(state: Any) -> dict[str, Any]:
    if isinstance(state, dict):
        return state
    if hasattr(state, "model_dump"):
        return state.model_dump()
    if hasattr(state, "dict"):
        return state.dict()
    if hasattr(state, "__dict__"):
        return dict(state.__dict__)
    return {"state": str(state)}


# ─── EXISTING ENDPOINTS ───


# Static UI routes moved to static_ui router


@app.websocket("/ws/intent-forge")
async def websocket_intent_forge(websocket: WebSocket, _auth=Depends(validate_api_key_ws)) -> None:
    """Replay Intent Forge canonical events with sequence and blueprint version filtering."""
    await websocket.accept()
    session_id = str(websocket.query_params.get("session_id", "")).strip()
    if not session_id:
        await websocket.close(code=1008)
        return
    last_sequence = int(websocket.query_params.get("last_sequence", "-1") or -1)
    events_path = ROOT_DIR / ".gaijinn" / "intent-forge" / "sessions" / session_id / "events.jsonl"
    blueprint_version = int(websocket.query_params.get("blueprint_version", "0") or 0)
    try:
        if events_path.is_file():
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if int(event.get("sequence", -1)) <= last_sequence:
                    continue
                await websocket.send_json(event)
                last_sequence = max(last_sequence, int(event.get("sequence", -1)))
        try:
            snapshot = await _run_blocking(_intent_forge_service.get_session, session_id)
            await websocket.send_json(
                {
                    "schema_version": 1,
                    "event_id": f"evt_{uuid.uuid4().hex}",
                    "sequence": last_sequence + 1,
                    "emitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "session_id": session_id,
                    "phase": "blueprinting",
                    "subphase": "intent_forge",
                    "classification": "guided",
                    "event_type": "session.snapshot",
                    "data": {
                        "blueprint_version": int(snapshot.get("blueprint_version", 0)),
                        "session_status": snapshot.get("session_status"),
                        "replay": True,
                        "version_mismatch": int(snapshot.get("blueprint_version", 0)) != blueprint_version,
                    },
                }
            )
        except KeyError:
            pass
        while True:
            await asyncio.sleep(30.0)
            await websocket.send_json(
                {
                    "schema_version": 1,
                    "event_id": f"evt_{uuid.uuid4().hex}",
                    "sequence": last_sequence + 1,
                    "emitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "session_id": session_id,
                    "phase": "blueprinting",
                    "subphase": "intent_forge",
                    "classification": "guided",
                    "event_type": "session.snapshot",
                    "data": {"heartbeat": True},
                }
            )
    except WebSocketDisconnect:
        return


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket, _auth=Depends(validate_api_key_ws)) -> None:
    """Stream SESSION_INIT, TOPOLOGY_SNAPSHOT, GRID_TELEMETRY from live project artifacts."""
    await websocket.accept()
    requested_mode = websocket.query_params.get("mode", "builder")
    session_id = new_session_id()
    mode = effective_experience_mode(session_id, requested_mode)

    async def push_snapshot() -> None:
        await websocket.send_json(build_session_init(ROOT_DIR, session_id=session_id, experience_mode=mode))
        await websocket.send_json(build_topology_snapshot(ROOT_DIR, session_id=session_id))
        await websocket.send_json(build_grid_telemetry(ROOT_DIR, session_id=session_id))

    try:
        await push_snapshot()
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            action = str(msg.get("action", ""))
            payload = msg.get("payload", {}) if isinstance(msg.get("payload"), dict) else {}
            mode = effective_experience_mode(session_id, str(payload.get("mode", mode)))
            ack = handle_client_action(
                action,
                payload,
                session_id=session_id,
                experience_mode=mode,
                project_root=ROOT_DIR,
            )
            if ack:
                await websocket.send_json(ack)
            if action in {"MUTATE_GEOMETRY_STRATEGY", "OVERRIDE_SYSTEM_INVARIANT", "SET_EXPERIENCE_MODE"}:
                await websocket.send_json(
                    build_session_init(ROOT_DIR, session_id=session_id, experience_mode=mode),
                )
                await websocket.send_json(build_topology_snapshot(ROOT_DIR, session_id=session_id))
    except WebSocketDisconnect:
        return
    except Exception:
        with contextlib.suppress(Exception):
            await websocket.close()


@app.websocket("/api/v1/telemetry/stream")
async def telemetry_stream(websocket: WebSocket, _auth=Depends(validate_api_key_ws)) -> None:
    """Dedicated telemetry stream — SESSION_INIT, TOPOLOGY_SNAPSHOT, GRID_TELEMETRY."""
    await websocket.accept()
    session_id = str(websocket.query_params.get("session_id", "")).strip() or new_session_id()
    mode = str(websocket.query_params.get("mode", "builder")).strip()

    async def push_all() -> None:
        await websocket.send_json(build_session_init(ROOT_DIR, session_id=session_id, experience_mode=mode))
        await websocket.send_json(build_topology_snapshot(ROOT_DIR, session_id=session_id))
        await websocket.send_json(build_grid_telemetry(ROOT_DIR, session_id=session_id))

    try:
        await push_all()
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("action", "")
            if action == "ping":
                await websocket.send_json({"action": "pong", "session_id": session_id})
            elif action == "refresh":
                await push_all()
    except WebSocketDisconnect:
        pass
    except Exception:
        with contextlib.suppress(Exception):
            await websocket.close()


# Internal UI routes moved to static_ui router


@app.post("/api/v1/analyze")
async def analyze(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    payload_path = _write_payload_to_scratch(payload)

    try:
        validate_system_state(payload_path)
    except StructuralGravityViolation as exc:
        raise HTTPException(
            status_code=422,
            detail={"violating_nodes": _nodes_from_violation(exc)},
        ) from exc

    response = _analysis_response(payload)
    response["billing"] = {
        "charged": False,
        "note": "Preflight is free. Request POST /api/v1/quote then /api/v1/blueprint/purchase before deploy.",
    }
    return response


@app.get("/api/v1/analyze")
async def analyze_project() -> dict[str, Any]:
    """Stealth analyze for the host project graph (server-side metrics only)."""
    metrics_path = ROOT_DIR / ".gaijinn" / "metrics_manifest.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="metrics_manifest.json not found — run gaijinn analyze")

    try:
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="invalid metrics manifest") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="metrics manifest must be a JSON object")

    response = _analysis_response(payload)
    telemetry = _project_telemetry(ROOT_DIR)
    response.update(
        {
            "node_count": telemetry["node_count"],
            "topology_preview": telemetry["topology_preview"],
            "gateway_count": telemetry["shadow_bridge_count"],
        }
    )
    return response


@app.post("/api/v1/moat/parse")
async def moat_parse(request: Request) -> dict[str, Any]:
    """Parse operation prompt via moat.py keyword maps (deterministic)."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")
    prompt = str(body.get("prompt", "")).strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    try:
        if _SYNC_TESTCLIENT_CALLS.get():
            profile = moat_parse_prompt(prompt)
        else:
            profile = await asyncio.to_thread(moat_parse_prompt, prompt)
    except TypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return profile.to_dict()


@app.get("/api/v1/project/telemetry")
async def project_telemetry() -> dict[str, Any]:
    """Return governance + topology preview for command-engine status strip."""
    return _project_telemetry(ROOT_DIR)


# Architectural teleology: design phase runs as long as the project needs.
# Full gaijinn scan/analyze/plan is teleology — visualizer streams real stages, no fake dwell.
DELIBERATION_HEARTBEAT_S = 5.0

TELEOLOGY_PHASES: dict[str, str] = {
    "intent_parse": "telos — intent decomposed into capability streams and GIV contracts",
    "graph_ingest": "context — scan maps structure so no node is purpose-orphaned",
    "curvature_compute": "geometry — gravity floor + Ollivier-Ricci curvature on edges",
    "bridge_detect": "traps — shadow bridges where neighborhoods mismatch (purpose trap doors)",
    "weld_plan": "surgery — union-find welds vs handoff gateways",
    "partition": "partition — non-overlapping work units from teleological scope",
    "blueprint_freeze": "freeze — blueprint manifest materialized",
}


def _sse_event(event_type: str, data: dict[str, Any]) -> str:
    payload = json.dumps({"type": event_type, "data": data}, separators=(",", ":"))
    return f"data: {payload}\n\n"


def _session_graph_nodes(session_root: Path, *, limit: int = 48) -> list[dict[str, Any]]:
    graph_path = session_root / ".gaijinn" / "graph.json"
    metrics_path = session_root / ".gaijinn" / "metrics_manifest.json"
    if not graph_path.exists():
        return []
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    nodes = graph.get("nodes", [])
    if isinstance(nodes, dict):
        nodes = list(nodes.keys())
    gravity_by_id = {item["id"]: item.get("gravity", 0.3) for item in _topology_preview(metrics_path, limit=128)}
    out: list[dict[str, Any]] = []
    for node_id in [str(n) for n in nodes][:limit]:
        gravity = gravity_by_id.get(node_id, 0.3)
        out.append(
            {
                "id": node_id,
                "label": Path(node_id).name or node_id,
                "gravity": gravity,
                "rejected": gravity < 0.2,
            }
        )
    return out


def _session_curvature_events(session_root: Path, *, limit: int = 32) -> list[dict[str, Any]]:
    metrics_path = session_root / ".gaijinn" / "metrics_manifest.json"
    if not metrics_path.exists():
        return []
    try:
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    edges = payload.get("curvature_meta", {}).get("edges", {})
    if not isinstance(edges, dict):
        return []
    out: list[dict[str, Any]] = []
    for edge in list(edges.values())[:limit]:
        if not isinstance(edge, dict):
            continue
        kappa = float(edge.get("kappa", edge.get("curvature", 0.0)) or 0.0)
        src = str(edge.get("source", ""))
        tgt = str(edge.get("target", ""))
        if not src or not tgt:
            continue
        out.append({"source": src, "target": tgt, "kappa": round(kappa, 3), "dark": kappa < -0.3})
    return out


def _session_blueprint_events(session_root: Path) -> dict[str, Any]:
    blueprint_path = session_root / ".gaijinn" / "blueprint.json"
    if not blueprint_path.exists():
        return {"work_units": [], "welds": [], "gateways": []}
    try:
        payload = json.loads(blueprint_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"work_units": [], "welds": [], "gateways": []}
    units = payload.get("work_units", [])
    work_units: list[dict[str, Any]] = []
    if isinstance(units, list):
        for unit in units:
            if not isinstance(unit, dict):
                continue
            paths = unit.get("allowed_paths", [])
            work_units.append(
                {
                    "id": str(unit.get("id", "")),
                    "title": str(unit.get("title", "")),
                    "files": len(paths) if isinstance(paths, list) else 0,
                    "risk": str(unit.get("estimated_risk", "low")),
                    "depends_on": unit.get("depends_on", []),
                }
            )
    gateways: list[str] = []
    welds: list[str] = []
    for risk in payload.get("risks", []):
        text = str(risk)
        if "Handoff gateway" in text:
            gateways.append(text)
        elif "weld" in text.lower():
            welds.append(text)
    return {"work_units": work_units, "welds": welds, "gateways": gateways}


@app.get("/api/v1/blueprint/deliberate")
async def blueprint_deliberate(
    intent: str,
    timeout: int | None = None,
    stream_format: str = "canonical",
) -> StreamingResponse:
    """SSE stream — real prepare() stages drive deliberation (architectural teleology)."""
    cleaned = str(intent or "").strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="intent is required")
    layer1_timeout_s = design_command_timeout(timeout)
    wire_format = str(stream_format or "canonical").strip().lower()
    if wire_format not in {"canonical", "legacy", "dual"}:
        raise HTTPException(status_code=400, detail="stream_format must be canonical, legacy, or dual")

    if _SYNC_TESTCLIENT_CALLS.get():
        correlation_id = f"delib-{uuid.uuid4().hex}"
        journal = OrchestrationJournal(correlation_id=correlation_id, session_id=correlation_id)
        snapshot = _session_store.prepare(cleaned, layer1_timeout=layer1_timeout_s)
        public = snapshot.to_public_dict()
        events = [
            journal.emit_legacy(
                "deliberation_start",
                {
                    "intent": cleaned[:200],
                    "mode": "architectural_teleology",
                    "layer1_timeout_s": layer1_timeout_s,
                    "layer1_timeout_default_s": DESIGN_COMMAND_TIMEOUT_DEFAULT,
                },
            ),
            journal.emit_legacy(
                "deliberation_complete",
                {
                    "session_id": public.get("session_id"),
                    "work_units": public.get("work_units"),
                    "high_risk_units": public.get("high_risk_units"),
                    "recommended_swarm": public.get("recommended_swarm"),
                    "prepare": public,
                },
            ),
        ]
        if wire_format == "legacy":
            lines = [sse_encode(journal.to_legacy_wire(event)) for event in events]
        elif wire_format == "dual":
            lines = [sse_encode({"canonical": event, "legacy": journal.to_legacy_wire(event)}) for event in events]
        else:
            lines = [sse_encode(event) for event in events]
        return Response(
            "".join(lines),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    async def event_stream():
        step_queue: queue.Queue[tuple[str, str, dict[str, Any], float]] = queue.Queue()
        result_holder: dict[str, Any] = {}
        error_holder: dict[str, Exception] = {}
        correlation_id = f"delib-{uuid.uuid4().hex}"
        journal = OrchestrationJournal(correlation_id=correlation_id, session_id=correlation_id)

        def on_step(step: str, payload: dict[str, Any]) -> None:
            step_queue.put(("step", step, payload, time.monotonic()))

        def run_prepare() -> None:
            try:
                snapshot = _session_store.prepare(
                    cleaned,
                    on_step=on_step,
                    layer1_timeout=layer1_timeout_s,
                )
                result_holder["snapshot"] = snapshot
                step_queue.put(("done", "", {}, time.monotonic()))
            except Exception as exc:
                error_holder["error"] = exc
                step_queue.put(("error", str(exc), {}, time.monotonic()))

        def emit_deliberation(legacy_type: str, data: dict[str, Any] | None = None) -> str:
            envelope = journal.emit_legacy(legacy_type, data)
            if wire_format == "legacy":
                payload: dict[str, Any] = journal.to_legacy_wire(envelope)
            elif wire_format == "dual":
                payload = {"canonical": envelope, "legacy": journal.to_legacy_wire(envelope)}
            else:
                payload = envelope
            return sse_encode(payload)

        thread = threading.Thread(target=run_prepare, daemon=True)
        thread.start()

        deliberation_started = time.monotonic()
        last_heartbeat = deliberation_started

        yield emit_deliberation(
            "deliberation_start",
            {
                "intent": cleaned[:200],
                "mode": "architectural_teleology",
                "layer1_timeout_s": layer1_timeout_s,
                "layer1_timeout_default_s": DESIGN_COMMAND_TIMEOUT_DEFAULT,
            },
        )

        session_root: Path | None = None
        phase_started: dict[str, float] = {}
        active_phase: str | None = None
        current_step: str | None = None

        def begin_phase(phase: str) -> None:
            nonlocal active_phase
            active_phase = phase
            phase_started[phase] = time.monotonic()

        def complete_phase(phase: str, extra: dict[str, Any] | None = None) -> str:
            started = phase_started.get(phase, time.monotonic())
            elapsed_ms = int((time.monotonic() - started) * 1000)
            payload = {"phase": phase, "elapsed_ms": elapsed_ms, **(extra or {})}
            return emit_deliberation("phase_complete", payload)

        while thread.is_alive() or not step_queue.empty():
            try:
                kind, step, payload, stamp = step_queue.get(timeout=0.15)
            except queue.Empty:
                now = time.monotonic()
                if thread.is_alive() and now - last_heartbeat >= DELIBERATION_HEARTBEAT_S:
                    elapsed_ms = int((now - deliberation_started) * 1000)
                    yield emit_deliberation(
                        "deliberation_heartbeat",
                        {
                            "elapsed_ms": elapsed_ms,
                            "phase": active_phase,
                            "step": current_step,
                            "layer1_timeout_s": layer1_timeout_s,
                        },
                    )
                    last_heartbeat = now
                await asyncio.sleep(0.02)
                continue

            if kind == "error":
                yield emit_deliberation("deliberation_error", {"message": step[-500:]})
                break

            if kind == "done":
                snapshot = result_holder.get("snapshot")
                if snapshot is None:
                    yield emit_deliberation("deliberation_error", {"message": "prepare returned no snapshot"})
                    break
                public = snapshot.to_public_dict()
                if active_phase:
                    yield complete_phase(active_phase)
                yield emit_deliberation(
                    "deliberation_complete",
                    {
                        "session_id": public.get("session_id"),
                        "work_units": public.get("work_units"),
                        "high_risk_units": public.get("high_risk_units"),
                        "recommended_swarm": public.get("recommended_swarm"),
                        "prepare": public,
                    },
                )
                break

            current_step = step
            yield emit_deliberation("step_progress", {"step": step, **payload})

            if step == "session_seed":
                root = payload.get("session_root")
                if root:
                    session_root = Path(str(root))

            if step == "init_start":
                begin_phase("intent_parse")
                yield emit_deliberation(
                    "phase_begin",
                    {"phase": "intent_parse", "message": TELEOLOGY_PHASES["intent_parse"], "step": step},
                )

            if step == "compile_prompt_complete" and session_root:
                streams = await asyncio.to_thread(lambda: detect_intent_streams(cleaned))
                for stream in streams[:8]:
                    yield emit_deliberation(
                        "work_unit_assigned",
                        {
                            "id": stream.key,
                            "files": 1,
                            "risk": stream.risk,
                            "title": stream.title,
                            "preview": True,
                        },
                    )
                yield complete_phase("intent_parse", {"streams": len(streams)})

            if step == "scan_start":
                begin_phase("graph_ingest")
                yield emit_deliberation(
                    "phase_begin",
                    {"phase": "graph_ingest", "message": TELEOLOGY_PHASES["graph_ingest"], "step": step},
                )

            if step == "scan_complete" and session_root:
                nodes = await asyncio.to_thread(_session_graph_nodes, session_root)
                for node in nodes:
                    yield emit_deliberation("node_added", node)
                yield complete_phase("graph_ingest", {"nodes": len(nodes)})

            if step == "analyze_start":
                begin_phase("curvature_compute")
                yield emit_deliberation(
                    "phase_begin",
                    {"phase": "curvature_compute", "message": TELEOLOGY_PHASES["curvature_compute"], "step": step},
                )

            if step == "analyze_complete" and session_root:
                edges = await asyncio.to_thread(_session_curvature_events, session_root)
                bridge_count = 0
                for edge in edges:
                    yield emit_deliberation(
                        "edge_curvature",
                        {"source": edge["source"], "target": edge["target"], "kappa": edge["kappa"]},
                    )
                    if edge.get("dark"):
                        bridge_count += 1
                        yield emit_deliberation(
                            "dark_bridge_detected",
                            {"source": edge["source"], "target": edge["target"], "kappa": edge["kappa"]},
                        )
                yield complete_phase("curvature_compute", {"edges": len(edges)})

                begin_phase("bridge_detect")
                yield emit_deliberation(
                    "phase_begin",
                    {"phase": "bridge_detect", "message": TELEOLOGY_PHASES["bridge_detect"], "step": step},
                )
                yield complete_phase("bridge_detect", {"bridges": bridge_count})

            if step in {"plan_start", "intent_blueprint_start"}:
                begin_phase("weld_plan")
                yield emit_deliberation(
                    "phase_begin",
                    {"phase": "weld_plan", "message": TELEOLOGY_PHASES["weld_plan"], "step": step},
                )

            if step in {"plan_complete", "intent_blueprint_complete"} and session_root:
                blueprint = await asyncio.to_thread(_session_blueprint_events, session_root)
                if blueprint["welds"]:
                    yield emit_deliberation("weld_start", {"cluster": blueprint["welds"][:4], "mode": "atomic_weld"})
                    yield emit_deliberation("weld_complete", {"block_id": "geometry-weld"})
                for gateway in blueprint["gateways"][:6]:
                    yield emit_deliberation("handoff_gateway", {"detail": gateway})
                yield complete_phase("weld_plan", {"gateways": len(blueprint["gateways"])})
                begin_phase("partition")
                yield emit_deliberation(
                    "phase_begin",
                    {"phase": "partition", "message": TELEOLOGY_PHASES["partition"], "step": step},
                )
                for wu in blueprint["work_units"]:
                    yield emit_deliberation("work_unit_assigned", wu)
                yield complete_phase("partition", {"work_units": len(blueprint["work_units"])})

                begin_phase("blueprint_freeze")
                yield emit_deliberation(
                    "phase_begin",
                    {"phase": "blueprint_freeze", "message": TELEOLOGY_PHASES["blueprint_freeze"], "step": step},
                )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.get("/api/v1/health")
async def health() -> JSONResponse:
    orchestrator = get_orchestrator()
    state = {
        "blocked": orchestrator.blocked,
        "active_jobs": len(orchestrator.jobs),
        "active_sprints": len(_sprints),
        "source": "cluster_orchestrator",
    }
    return JSONResponse(content=jsonable_encoder(state))


# ─── ACI BILLING ENDPOINTS ───


def _extract_user_id(request: Request, payload: dict[str, Any] | None = None) -> str:
    return extract_user_id(request, payload)


def _guard_session_access(session_id: str, user_id: str) -> None:
    if not session_id:
        return
    session_root = _session_store.project_root(session_id)
    assert_session_owner(session_root, user_id)


def _safe_argv_for_log(cmd: list[str]) -> str:
    if not cmd:
        return ""
    safe = list(cmd)
    if safe and len(safe[-1]) > 120:
        digest = hashlib.sha256(safe[-1].encode("utf-8")).hexdigest()[:16]
        safe[-1] = f"<prompt len={len(cmd[-1])} sha256={digest}>"
    return " ".join(safe)


def _prompt_digest(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        return "empty"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _quote_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    workers = payload.get("workers", payload.get("agent_slots", 1))
    if not isinstance(workers, int) or workers < 1:
        raise HTTPException(status_code=400, detail="workers must be a positive integer")

    snapshot = build_snapshot_from_payload(payload, worker_count=workers)
    with DEFAULT_LEDGER_STORAGE.locked_ledger() as ledger:
        blueprint_price = _compute_blueprint_cost(snapshot, ledger)
        sprint_price = _compute_sprint_cost(snapshot, ledger)

    receipt = customer_receipt(snapshot, worker_count=workers)
    return {
        "integrity_score": snapshot.integrity_score,
        "tier": tier_for_score(snapshot.integrity_score),
        "blueprint_price": float(blueprint_price),
        "sprint_price": float(sprint_price),
        "receipt": receipt,
        "snapshot": snapshot,
        "workers": workers,
    }


@app.post("/api/v1/quote")
async def quote(request: Request) -> dict[str, Any]:
    """Return ACI-based pricing without charging the account."""
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")

    quote_data = _quote_from_payload(payload)
    return {
        "integrity_score": quote_data["integrity_score"],
        "tier": quote_data["tier"],
        "deploy_fee": quote_data["blueprint_price"],
        "sprint_fee": quote_data["sprint_price"],
        "receipt": quote_data["receipt"],
    }


@app.post("/api/v1/blueprint/purchase")
async def blueprint_purchase(request: Request) -> dict[str, Any]:
    """Charge the deploy fee and return a sprint entitlement token."""
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")

    user_id = _extract_user_id(request, payload)
    quote_data = _quote_from_payload(payload)
    snapshot = quote_data["snapshot"]
    workers = quote_data["workers"]
    deploy_fee = Decimal(str(quote_data["blueprint_price"]))
    sprint_price = Decimal(str(quote_data["sprint_price"]))

    try:
        charged = deduct_deployment_fee(user_id, deploy_fee, storage_provider=DEFAULT_LEDGER_STORAGE)
    except InsufficientCreditsException as exc:
        raise HTTPException(
            status_code=402,
            detail={"error": str(exc), "deploy_fee": float(deploy_fee)},
        ) from exc

    token_record = issue_sprint_token(
        user_id,
        worker_count=workers,
        sprint_price=sprint_price,
    )

    return {
        "sprint_token": token_record["token"],
        "expires_at": token_record["expires_at"],
        "deploy_fee": charged,
        "receipt": customer_receipt(snapshot, worker_count=workers),
    }


# ─── COUNCIL (shared multi-agent thread) ───


@app.get("/api/v1/council/show")
async def council_show() -> dict[str, Any]:
    """Return the shared council markdown thread."""
    ensure_council(ROOT_DIR)
    return {
        "path": str(ROOT_DIR / ".gaijinn" / "bridge" / "council.md"),
        "markdown": render_council_markdown(ROOT_DIR),
    }


@app.get("/api/v1/council/ledger")
async def council_ledger(tail: int = 40) -> dict[str, Any]:
    """Return structured council rows for command-engine ledger tailing."""
    ensure_council(ROOT_DIR)
    limit = max(1, min(int(tail), 200))
    if _SYNC_TESTCLIENT_CALLS.get():
        rows = _council_ledger_rows(ROOT_DIR, tail=limit)
    else:
        rows = await asyncio.to_thread(_council_ledger_rows, ROOT_DIR, tail=limit)
    return {
        "path": str(ROOT_DIR / ".gaijinn" / "bridge" / "council.jsonl"),
        "rows": rows,
        "count": len(rows),
    }


# ── Intent Forge API (pre-orchestration blueprint sessions) ─────────────────


def _intent_forge_idempotency(body: dict[str, Any]) -> str:
    key = str(body.get("idempotency_key", "")).strip()
    if not key:
        raise HTTPException(status_code=400, detail="idempotency_key is required")
    return key


def _intent_forge_expected_version(body: dict[str, Any]) -> int:
    raw = body.get("expected_blueprint_version")
    if raw is None:
        raise HTTPException(status_code=400, detail="expected_blueprint_version is required")
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="expected_blueprint_version must be an integer") from exc


@app.post("/api/v1/intent-forge/sessions")
async def intent_forge_create_session(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")
    user_id = require_user_id(request, body)
    prompt = str(body.get("prompt", body.get("intent", ""))).strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    tier = str(body.get("tier", "paid")).strip().lower() or "paid"
    if tier not in {"free", "paid"}:
        raise HTTPException(status_code=400, detail="tier must be free or paid")
    consent = body.get("telemetry_consent")
    telemetry_consent = consent if isinstance(consent, dict) else None
    try:
        return await _run_blocking(
            _intent_forge_service.create_session,
            user_id=user_id,
            prompt=prompt,
            tier=tier,
            telemetry_consent=telemetry_consent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/intent-forge/sessions/{session_id}")
async def intent_forge_get_session(session_id: str, request: Request) -> dict[str, Any]:
    user_id = require_user_id(request)
    try:
        state = await _run_blocking(_intent_forge_service.get_session, session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if str(state.get("user_id", "")) != user_id:
        raise HTTPException(status_code=403, detail="session access denied")
    return state


@app.post("/api/v1/intent-forge/sessions/{session_id}/answers")
async def intent_forge_submit_answer(session_id: str, request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")
    user_id = require_user_id(request, body)
    try:
        state = await _run_blocking(_intent_forge_service.get_session, session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if str(state.get("user_id", "")) != user_id:
        raise HTTPException(status_code=403, detail="session access denied")
    try:
        return await _run_blocking(
            _intent_forge_service.submit_answer,
            session_id,
            question_id=str(body.get("question_id", "")).strip(),
            answer=str(body.get("answer", "")),
            idempotency_key=_intent_forge_idempotency(body),
            expected_blueprint_version=_intent_forge_expected_version(body),
            action=str(body.get("action", "answer")).strip().lower() or "answer",
        )
    except VersionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/intent-forge/sessions/{session_id}/pause")
async def intent_forge_pause(session_id: str, request: Request) -> dict[str, Any]:
    body = await _json_body(request)
    user_id = require_user_id(request, body)
    _assert_intent_forge_owner(session_id, user_id)
    try:
        return await _run_blocking(
            _intent_forge_service.pause,
            session_id,
            idempotency_key=_intent_forge_idempotency(body),
            expected_blueprint_version=_intent_forge_expected_version(body),
        )
    except VersionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/intent-forge/sessions/{session_id}/resume")
async def intent_forge_resume(session_id: str, request: Request) -> dict[str, Any]:
    body = await _json_body(request)
    user_id = require_user_id(request, body)
    _assert_intent_forge_owner(session_id, user_id)
    try:
        return await _run_blocking(
            _intent_forge_service.resume,
            session_id,
            idempotency_key=_intent_forge_idempotency(body),
            expected_blueprint_version=_intent_forge_expected_version(body),
        )
    except VersionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/intent-forge/sessions/{session_id}/revise")
async def intent_forge_revise(session_id: str, request: Request) -> dict[str, Any]:
    body = await _json_body(request)
    user_id = require_user_id(request, body)
    _assert_intent_forge_owner(session_id, user_id)
    question_id = str(body.get("question_id", "")).strip()
    if not question_id:
        raise HTTPException(status_code=400, detail="question_id is required")
    answer = str(body.get("answer", "")).strip()
    if not answer:
        raise HTTPException(status_code=400, detail="answer is required")
    try:
        return await _run_blocking(
            _intent_forge_service.revise_answer,
            session_id,
            question_id=question_id,
            answer=answer,
            idempotency_key=_intent_forge_idempotency(body),
            expected_blueprint_version=_intent_forge_expected_version(body),
        )
    except VersionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/intent-forge/sessions/{session_id}/finalize")
async def intent_forge_finalize(session_id: str, request: Request) -> dict[str, Any]:
    body = await _json_body(request)
    user_id = require_user_id(request, body)
    _assert_intent_forge_owner(session_id, user_id)
    try:
        return await _run_blocking(
            _intent_forge_service.finalize,
            session_id,
            idempotency_key=_intent_forge_idempotency(body),
            expected_blueprint_version=_intent_forge_expected_version(body),
            force=bool(body.get("force", False)),
        )
    except VersionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/v1/intent-forge/sessions/{session_id}/handoff")
async def intent_forge_handoff(session_id: str, request: Request) -> dict[str, Any]:
    body = await _json_body(request)
    user_id = require_user_id(request, body)
    _assert_intent_forge_owner(session_id, user_id)
    action = str(body.get("action", "confirm")).strip().lower() or "confirm"
    try:
        if action == "accept":
            state = await _run_blocking(
                _intent_forge_service.accept_handoff,
                session_id,
                idempotency_key=_intent_forge_idempotency(body),
                expected_blueprint_version=_intent_forge_expected_version(body),
            )
        else:
            state = await _run_blocking(
                _intent_forge_service.confirm_handoff,
                session_id,
                idempotency_key=_intent_forge_idempotency(body),
                expected_blueprint_version=_intent_forge_expected_version(body),
                confirmation=str(body.get("confirmation", "")),
            )
    except VersionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        **state,
        "command_engine_url": f"/command-engine?step=plan&session_id={session_id}",
    }


async def _json_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")
    return body


def _assert_intent_forge_owner(session_id: str, user_id: str) -> None:
    try:
        state = _intent_forge_service.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if str(state.get("user_id", "")) != user_id:
        raise HTTPException(status_code=403, detail="session access denied")


@app.post("/api/v1/loom/blueprint/synthesize")
async def loom_blueprint_synthesize(request: Request) -> dict[str, Any]:
    body = await _json_body(request)
    user_id = require_user_id(request, body)
    intent_forge_session_id = str(body.get("intent_forge_session_id", "")).strip()
    if not intent_forge_session_id:
        raise HTTPException(status_code=400, detail="intent_forge_session_id is required")
    teleology_receipt = body.get("teleology_receipt")
    if teleology_receipt is not None and not isinstance(teleology_receipt, dict):
        raise HTTPException(status_code=400, detail="teleology_receipt must be an object")

    try:
        forge_state = await _run_blocking(
            _intent_forge_service.get_session,
            intent_forge_session_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if str(forge_state.get("user_id", "")) != user_id:
        raise HTTPException(status_code=403, detail="intent forge session access denied")
    if forge_state.get("session_status") != "HANDED_OFF":
        raise HTTPException(
            status_code=409,
            detail="intent forge session must be HANDED_OFF before synthesis",
        )

    phases = forge_state.get("phases")
    blueprint_graph = forge_state.get("blueprint_graph")
    confirmed_requirements = forge_state.get("confirmed_requirements")
    executable_projection = forge_state.get("executable_projection")
    synthesis_request = SynthesisRequest(
        session_id=intent_forge_session_id,
        intent=str(forge_state.get("original_prompt", "")).strip(),
        forge_session_id=intent_forge_session_id,
        phases=phases if isinstance(phases, list) else None,
        blueprint_graph=blueprint_graph if isinstance(blueprint_graph, dict) else None,
        confirmed_requirements=(confirmed_requirements if isinstance(confirmed_requirements, list) else None),
        executable_projection=(executable_projection if isinstance(executable_projection, dict) else None),
    )
    setattr(synthesis_request, "teleology_receipt", teleology_receipt)
    try:
        result = await _run_blocking(synthesize_blueprint, synthesis_request)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    synthesized_blueprint = result.to_public_dict().get("blueprint", {})
    if isinstance(synthesized_blueprint, dict) and synthesized_blueprint:
        forge_state["executable_projection"] = synthesized_blueprint
        forge_state["projection_mode"] = synthesized_blueprint.get("projection_mode", "loom_synthesis")
        await _run_blocking(
            _intent_forge_service.store.save,
            intent_forge_session_id,
            forge_state,
        )

    return result.to_public_dict()


# ── GAIJINN BLUEPRINT: Orchestrate API (terminal v2 backbone) ─────────────
# Stealth contract: public JSON has stats only (work_units, rationale, warnings).
# Never return blueprint.json, graph.json, or curvature metrics to the browser.
# Session artifacts: .gaijinn/sessions/<id>/ on host (see OrchestrateSessionStore).
# Gaps: no webhook on complete; failed phase unset here.
# Spec: ui/gaijinn-ui-intent-map.json → actions.orchestrate.prepare|swarm


@app.post("/api/v1/orchestrate/prepare")
async def orchestrate_prepare(request: Request) -> dict[str, Any]:
    """Stealth blueprint from user intent — returns stats only, never raw blueprint."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    intent = str(body.get("intent", "")).strip()
    if not intent:
        raise HTTPException(status_code=400, detail="intent is required")
    intent_forge_session_id = str(body.get("intent_forge_session_id", "")).strip()
    if not intent_forge_session_id and os.environ.get("GAIJINN_ALLOW_RAW_INTENT_PREPARE") != "1":
        raise HTTPException(
            status_code=409,
            detail=(
                "Loom prepare gate requires a non-empty intent_forge_session_id; "
                "set GAIJINN_ALLOW_RAW_INTENT_PREPARE=1 only for legacy raw prepare"
            ),
        )
    try:
        phases = normalize_phases(body.get("phases"))
        loaded_context = validate_loaded_context(phases, body.get("loaded_context"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    layer1_timeout_raw = body.get("layer1_timeout")
    layer1_timeout: int | None = None
    if layer1_timeout_raw is not None:
        try:
            layer1_timeout = design_command_timeout(int(layer1_timeout_raw))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="layer1_timeout must be an integer (seconds)") from exc
    owner_user_id = require_user_id(request, body if isinstance(body, dict) else None)
    executable_blueprint: dict[str, Any] | None = None
    if intent_forge_session_id:
        try:
            forge_state = await _run_blocking(_intent_forge_service.get_session, intent_forge_session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if str(forge_state.get("user_id", "")) != owner_user_id:
            raise HTTPException(status_code=403, detail="intent forge session access denied")
        if forge_state.get("session_status") != "HANDED_OFF":
            raise HTTPException(status_code=409, detail="intent forge session must be HANDED_OFF before prepare")
        executable_blueprint = forge_state.get("executable_projection")
        if not isinstance(executable_blueprint, dict):
            raise HTTPException(status_code=409, detail="intent forge executable projection missing")
        intent = str(forge_state.get("original_prompt", intent)).strip() or intent
    try:
        snapshot = await _run_blocking(
            _session_store.prepare,
            intent,
            list(phases),
            loaded_context,
            owner_user_id=owner_user_id,
            layer1_timeout=layer1_timeout,
            executable_blueprint=executable_blueprint,
            orchestrate_session_id=intent_forge_session_id or None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    payload = snapshot.to_public_dict()
    payload["layer1_timeout_s"] = design_command_timeout(layer1_timeout)
    return payload


@app.post("/api/v1/orchestrate/swarm")
async def orchestrate_swarm(request: Request) -> dict[str, Any]:
    """Assign swarm size and materialize worker grid for a prepared session."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    user_id = require_user_id(request, body if isinstance(body, dict) else None)
    session_id = str(body.get("session_id", "")).strip()
    workers = body.get("workers")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    if not isinstance(workers, int) or workers < 1:
        raise HTTPException(status_code=400, detail="workers must be a positive integer")
    if workers > _MAX_ORCHESTRATE_SWARM_WORKERS:
        raise HTTPException(
            status_code=400,
            detail=f"workers must be <= {_MAX_ORCHESTRATE_SWARM_WORKERS}",
        )
    try:
        _guard_session_access(session_id, user_id)
        snapshot = await _run_blocking(_session_store.assign_swarm, session_id, workers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return snapshot.to_public_dict()


@app.get("/api/v1/orchestrate/session/{session_id}")
async def orchestrate_session(session_id: str, request: Request) -> dict[str, Any]:
    user_id = require_user_id(request)
    try:
        _guard_session_access(session_id, user_id)
        snapshot = _session_store.get(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return snapshot.to_public_dict()


@app.post("/api/v1/orchestrate/advance-phase")
async def orchestrate_advance_phase(request: Request) -> dict[str, Any]:
    """Queue the next selected phase after the current phase has merged."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    session_id = str(body.get("session_id", "")).strip() if isinstance(body, dict) else ""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    try:
        snapshot = await _run_blocking(_session_store.advance_phase, session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return snapshot.to_public_dict()


@app.post("/api/v1/grid/merge")
async def grid_merge(request: Request) -> dict[str, Any]:
    """Run post-sprint collect → validate-worker → merge-grid for a session."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    session_id = str(body.get("session_id", "")).strip() if isinstance(body, dict) else ""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    try:
        payload = await _run_blocking(_session_store.run_merge, session_id)
        payload["project_path"] = str(_session_store.project_root(session_id))
        return payload
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/v1/preflight", response_model=None)
async def preflight_merge_check(request: Request) -> JSONResponse:
    """Upstream CI gate: workspace isolation + transaction bus before merge."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")

    session_id = str(body.get("session_id", "")).strip()
    worker_id = str(body.get("worker_id", "")).strip()
    target_branch = str(body.get("target_branch", "gaijinn/integration")).strip() or "gaijinn/integration"
    project_path = str(body.get("project_path", "")).strip() or None

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    if not worker_id:
        raise HTTPException(status_code=400, detail="worker_id is required")

    session_roots: dict[str, Path] | None = None
    if not project_path:
        with contextlib.suppress(KeyError):
            session_roots = {session_id: _session_store.project_root(session_id)}

    try:
        result = await _run_blocking(
            run_preflight_check,
            session_id=session_id,
            worker_id=worker_id,
            target_branch=target_branch,
            project_path=project_path,
            session_roots=session_roots,
        )
    except PreflightResolutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload = jsonable_encoder(result.to_dict())
    status_code = 200 if result.allow_merge else 422
    return JSONResponse(status_code=status_code, content=payload)


@app.get("/api/v1/grid/merge/status")
async def grid_merge_status(session_id: str) -> dict[str, Any]:
    """Read post-sprint merge status for a session without side effects."""
    sid = str(session_id or "").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required")
    try:
        project_root = _session_store.project_root(sid)
        snapshot = _session_store.get(sid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "session_id": sid,
        "phase": snapshot.phase,
        "current_phase": snapshot.current_phase,
        "pipeline_plan": snapshot.pipeline_plan,
        "project_path": str(project_root),
        "merge_pipeline": merge_pipeline_status(project_root),
    }


@app.get("/api/v1/grid/deliverable")
async def grid_deliverable(session_id: str) -> Response:
    """Download a zip archive of the merged session project."""
    sid = str(session_id or "").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required")
    try:
        project_root = _session_store.project_root(sid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    archive = await _run_blocking(_session_project_zip, project_root)
    headers = {"Content-Disposition": f'attachment; filename="gaijinn-deliverable-{sid}.zip"'}
    return Response(content=archive, media_type="application/zip", headers=headers)


@app.get("/api/v1/grid/merge/report")
async def grid_merge_report(session_id: str) -> dict[str, Any]:
    """Return merge report JSON for deliverable review (worker outcomes, conflicts)."""
    sid = str(session_id or "").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required")
    try:
        project_root = _session_store.project_root(sid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    report = await _run_blocking(load_merge_report, project_root)
    if report is None:
        raise HTTPException(status_code=404, detail="merge report not found for session")
    return {
        "session_id": sid,
        "project_path": str(project_root),
        "report": report,
        "merge_pipeline": merge_pipeline_status(project_root),
    }


@app.get("/api/v1/grid/diff")
async def grid_diff(session_id: str) -> dict[str, Any]:
    """Return git diff summary for the merged session project."""
    sid = str(session_id or "").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required")
    try:
        project_root = _session_store.project_root(sid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    diff = await _run_blocking(_session_git_diff, project_root)
    return {"session_id": sid, "project_path": str(project_root), **diff}


@app.post("/api/v1/council/say")
async def council_say(request: Request) -> dict[str, Any]:
    """Append a message to the council thread (terminal + agents)."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if not isinstance(body, dict) or not str(body.get("text", "")).strip():
        raise HTTPException(status_code=400, detail="text is required")

    author = str(body.get("author", "user")).strip().lower()
    author_id = body.get("author_id")
    role = str(body.get("role", "participant"))

    try:
        msg = append_message(
            str(body["text"]),
            author=author,
            author_id=str(author_id) if author_id else None,
            role=role,
            project_root=ROOT_DIR,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"seq": msg.seq, "author": msg.author, "author_id": msg.author_id, "posted": True}


@app.post("/api/v1/hermes/chat")
async def hermes_chat(request: Request) -> dict[str, Any]:
    """Run a one-shot Hermes session from the Gaijinn terminal chat."""
    if shutil.which("hermes") is None:
        raise HTTPException(status_code=503, detail="hermes executable not found on PATH")

    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")

    user_message = str(body.get("message", "")).strip()
    if not user_message:
        user_message = "Read the Gaijinn machine council and give a one-sentence status."

    ensure_council(global_council=True)
    council_path = machine_council_address()
    prompt = (
        f"Read the file {council_path} for multi-agent context.\n"
        f"User message from Gaijinn terminal chat: {user_message}\n"
        "Reply concisely (1-3 sentences). Then run:\n"
        'gaijinn council say --global --as hermes --id hermes "one-line summary of your reply"'
    )

    hermes_model = os.environ.get("HERMES_DEFAULT_MODEL", "").strip()
    hermes_bin = shutil.which("hermes") or "hermes"
    hermes_cmd: list[str] = [hermes_bin]
    if hermes_model:
        hermes_cmd.extend(["-m", hermes_model])
    hermes_cmd.extend(["--", "-z", prompt])

    try:
        proc = await asyncio.create_subprocess_exec(
            *hermes_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(ROOT_DIR),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180.0)
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="hermes session timed out") from exc

    if proc.returncode != 0:
        err = stderr.decode("utf-8", errors="replace").strip() or "hermes failed"
        raise HTTPException(status_code=500, detail=err)

    reply = stdout.decode("utf-8", errors="replace").strip()
    if reply:
        with contextlib.suppress(ValueError):
            append_message(
                reply,
                author="hermes",
                author_id="hermes",
                role="advisor",
                global_council=True,
            )

    return {
        "author": "hermes",
        "reply": reply,
        "council": council_path,
    }


# ─── GRID SPAWN ENDPOINT ───


@app.post("/api/v1/grid/spawn")
async def grid_spawn(request: Request) -> dict[str, Any]:
    """Spawn Codex or Grok agents per worker cell to code work units. Atomic sprint — no cancel."""
    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")

    user_id = require_user_id(request, body)
    idempotency_key = extract_idempotency_key(request.headers, body)
    if require_spawn_idempotency_key() and not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="X-Idempotency-Key is required for /grid/spawn (8-128 chars: letters, digits, _, -)",
        )

    try:
        workers = parse_spawn_workers(body.get("workers", 4))
        body = {**body, "workers": workers}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        timeout = parse_spawn_timeout(body.get("timeout"), default=_DEFAULT_SPRINT_TIMEOUT)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    model = str(body.get("model", "grok-composer-2.5-fast")).strip()
    task = body.get("task", "")
    session_id = str(body.get("session_id", "")).strip()
    sprint_token = body.get("sprint_token")

    idempotency_path: Path | None = None
    capacity_reservation_id: str | None = None
    sprint_id = uuid.uuid4().hex[:12]

    if idempotency_key:
        try:
            normalized_key = normalize_idempotency_key(idempotency_key)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        fingerprint = spawn_request_fingerprint(user_id=user_id, body=body)
        try:
            decision = begin_idempotency(
                ROOT_DIR,
                user_id=user_id,
                key=normalized_key,
                request_hash=fingerprint,
                sprint_alive=_sprint_processes_still_alive,
            )
        except IdempotencyCorruptError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if decision.action == "replay" and decision.response is not None:
            replay = dict(decision.response)
            replay["idempotent_replay"] = True
            return replay
        if decision.action == "conflict":
            raise HTTPException(
                status_code=422,
                detail="idempotency key reused with different spawn parameters",
            )
        if decision.action == "in_progress":
            raise HTTPException(
                status_code=409,
                detail="spawn with this idempotency key is already in progress",
            )
        idempotency_path = decision.record_path

    if not sprint_token:
        abort_idempotency(idempotency_path)
        raise HTTPException(status_code=401, detail="sprint_token is required")

    try:
        token_record = validate_sprint_token(
            str(sprint_token),
            user_id=user_id,
            workers=workers,
        )
    except SprintTokenException as exc:
        abort_idempotency(idempotency_path)
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    workers_root = WORKERS_DIR
    if session_id:
        try:
            _guard_session_access(session_id, user_id)
            workers_root = _session_store.workers_dir(session_id)
        except ValueError as exc:
            abort_idempotency(idempotency_path)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except KeyError as exc:
            abort_idempotency(idempotency_path)
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    manifest_path = workers_root / "manifest.json"
    if not manifest_path.exists():
        abort_idempotency(idempotency_path)
        raise HTTPException(
            status_code=400, detail="No worker manifest found. Run 'gaijinn run-grid --workers N' first."
        )

    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        abort_idempotency(idempotency_path)
        raise HTTPException(status_code=500, detail=f"Failed to read manifest: {exc}") from exc

    registered = manifest.get("worker_details", [])
    manifest_by_worker = {
        str(detail.get("worker_id", "")): detail
        for detail in registered
        if isinstance(detail, dict) and detail.get("worker_id")
    }
    if len(registered) < workers:
        abort_idempotency(idempotency_path)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Manifest has {len(registered)} workers but {workers} requested. "
                f"Run 'gaijinn run-grid --workers {workers}' first."
            ),
        )

    missing_workers = [
        f"worker-{index:03d}" for index in range(1, workers + 1) if not (workers_root / f"worker-{index:03d}").is_dir()
    ]
    if missing_workers:
        abort_idempotency(idempotency_path)
        raise HTTPException(
            status_code=400,
            detail=f"Worker directories missing before spawn: {', '.join(missing_workers)}",
        )

    workspace_key = normalize_workspace_key(workers_root)

    try:
        with _sprint_lock:
            reserve_spawn_capacity(
                _sprints,
                _spawn_reservations,
                requested_workers=workers,
                workspace_key=workspace_key,
                session_id=session_id or None,
                sprint_id=sprint_id,
            )
            capacity_reservation_id = sprint_id
    except SpawnLimitError as exc:
        abort_idempotency(idempotency_path)
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    mock_grid = os.environ.get("GAIJINN_MOCK_GRID", "").strip().lower() in {"1", "true", "yes", "on"}
    if not mock_grid:
        if not shutil.which("codex"):
            with _sprint_lock:
                release_spawn_reservation(_spawn_reservations, capacity_reservation_id)
            abort_idempotency(idempotency_path)
            raise HTTPException(
                status_code=503,
                detail="codex executable not found on PATH (set GAIJINN_MOCK_GRID=1 for local UI testing)",
            )
        resolved_executor = "codex"
    else:
        resolved_executor = "mock"

    sprint_price = Decimal(str(token_record["sprint_price"]))
    charged = False
    consumed = False
    processes: list[dict[str, Any]] = []
    worker_list: list[dict[str, Any]] = []

    def _rollback_partial_spawn() -> None:
        for entry in processes:
            terminate_worker_process(
                entry.get("proc"),
                process_group_id=entry.get("process_group_id")
                if isinstance(entry.get("process_group_id"), int)
                else None,
            )
        with _sprint_lock:
            _sprints.pop(sprint_id, None)
            release_spawn_reservation(_spawn_reservations, capacity_reservation_id)
            write_spawn_runtime(ROOT_DIR, _sprints)
        if consumed:
            release_sprint_token(str(sprint_token))
        if charged:
            credit_account(user_id, sprint_price, storage_provider=DEFAULT_LEDGER_STORAGE)

    try:
        if idempotency_path is not None:
            attach_idempotency_sprint(idempotency_path, sprint_id)

        deduct_deployment_fee(
            user_id,
            sprint_price,
            storage_provider=DEFAULT_LEDGER_STORAGE,
        )
        charged = True
        validate_sprint_token(
            str(sprint_token),
            user_id=user_id,
            workers=workers,
            consume=True,
        )
        consumed = True

        for index in range(1, workers + 1):
            worker_name = f"worker-{index:03d}"
            worker_dir = workers_root / worker_name
            log_path = worker_dir / "output.log"

            work_unit_path = worker_dir / "WORK_UNIT.md"
            intent_path = worker_dir / "WORKER_INTENT.txt"
            giv_path = worker_dir / "giv.json"

            work_unit_text = ""
            if work_unit_path.exists():
                work_unit_text = work_unit_path.read_text(encoding="utf-8")
            elif intent_path.exists():
                work_unit_text = intent_path.read_text(encoding="utf-8")

            giv: dict[str, Any] = {}
            if giv_path.exists():
                try:
                    with giv_path.open("r", encoding="utf-8") as f:
                        giv = json.load(f)
                except (OSError, json.JSONDecodeError):
                    giv = {}

            prompt_lines = [
                "You are a Gaijinn-governed subagent. Execute the assigned work unit exactly.",
                "",
                "=== GIV CONTRACT ===",
            ]
            allowed = giv.get("allowed_paths", [])
            denied = giv.get("denied_paths", [])
            if allowed:
                prompt_lines.append(f"Allowed paths: {', '.join(allowed)}")
            if denied:
                prompt_lines.append(f"Denied paths: {', '.join(denied)}")
            prompt_lines.append("Git push: DENIED")
            prompt_lines.append("")
            prompt_lines.append("=== USER INTENT ===")
            prompt_lines.append(task.strip() if task else "(none)")
            prompt_lines.append("")
            prompt_lines.append("=== WORK UNIT ===")
            prompt_lines.append(work_unit_text if work_unit_text else "Execute the user intent within GIV scope.")
            prompt_lines.append("")
            prompt_lines.append("Run to completion. Verify changes compile. Report errors honestly.")
            full_prompt = "\n".join(prompt_lines)

            manifest_detail = manifest_by_worker.get(worker_name, {})
            assigned_units = manifest_detail.get("assigned_work_units", [])
            has_assigned_work = isinstance(assigned_units, list) and bool(assigned_units)

            cmd = _spawn_worker_command(
                worker_name=worker_name,
                worker_dir=worker_dir,
                full_prompt=full_prompt,
                model=model,
                has_assigned_work=has_assigned_work,
            )

            with log_path.open("w", encoding="utf-8") as lf:
                lf.write(f"=== GAIJINN GRID SPAWN: {worker_name} ===\n")
                lf.write(f"Executor: {resolved_executor}\n")
                lf.write(f"Model: {model}\n")
                lf.write(f"Started: {time.ctime()}\n")
                lf.write(f"Prompt digest: {_prompt_digest(full_prompt)}\n")
                lf.write(f"Command: {_safe_argv_for_log(cmd)}\n")
                lf.write("=" * 60 + "\n\n")

            if mock_grid:
                with log_path.open("a", encoding="utf-8") as stdout_file:
                    proc = popen_worker_process(
                        cmd,
                        stdout=stdout_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        cwd=str(worker_dir.resolve()),
                    )
            else:
                stdout_file = log_path.open("a", encoding="utf-8")
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(worker_dir.resolve()),
                )
                if proc.stdout:
                    asyncio.create_task(
                        _read_stream(sprint_id, worker_name, manifest_detail.get("domain"), proc.stdout, stdout_file)
                    )

            processes.append(
                {
                    "name": worker_name,
                    "proc": proc,
                    "process_group_id": resolve_process_group_id(proc),
                    "dir": str(worker_dir),
                    "status": "running",
                    "started_at": time.time(),
                }
            )
            worker_list.append({"name": worker_name, "status": "spawned", "pid": proc.pid})

    except InsufficientCreditsException as exc:
        with _sprint_lock:
            release_spawn_reservation(_spawn_reservations, capacity_reservation_id)
        abort_idempotency(idempotency_path)
        raise HTTPException(
            status_code=402,
            detail={"error": str(exc), "sprint_price": float(sprint_price)},
        ) from exc
    except SprintTokenException as exc:
        _rollback_partial_spawn()
        abort_idempotency(idempotency_path)
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except HTTPException:
        _rollback_partial_spawn()
        abort_idempotency(idempotency_path)
        raise
    except IdempotencyCorruptError as exc:
        _rollback_partial_spawn()
        abort_idempotency(idempotency_path)
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        _rollback_partial_spawn()
        abort_idempotency(idempotency_path)
        raise HTTPException(status_code=500, detail=f"grid spawn failed: {exc}") from exc

    sprint_info = {
        "sprint_id": sprint_id,
        "workers": worker_list,
        "processes": processes,
        "started_at": time.time(),
        "model": model,
        "executor": resolved_executor,
        "status": "running",
        "completed": 0,
        "failed": 0,
        "running": len(processes),
        "manifest_path": str(manifest_path),
        "workers_root": str(workers_root),
        "workspace_key": workspace_key,
        "session_id": session_id or None,
        "timeout": timeout,
    }

    response = {
        "sprint_id": sprint_id,
        "workers": [w["name"] for w in worker_list],
        "status": "spawned",
        "count": len(worker_list),
        "session_id": session_id or None,
        "idempotency_key": idempotency_key,
    }

    with _sprint_lock:
        _sprints[sprint_id] = sprint_info
        release_spawn_reservation(_spawn_reservations, capacity_reservation_id)
        capacity_reservation_id = None
        write_spawn_runtime(ROOT_DIR, _sprints)

    try:
        if idempotency_path is not None:
            complete_idempotency(idempotency_path, response, sprint_id=sprint_id)
    except Exception as exc:
        _rollback_partial_spawn()
        abort_idempotency(idempotency_path)
        raise HTTPException(status_code=500, detail=f"idempotency completion failed: {exc}") from exc

    asyncio.create_task(_monitor_sprint(sprint_id, manifest_path, timeout))
    return response


# ─── GRID STREAM (SSE) ENDPOINT ───


@app.get("/api/v1/grid/stream/{cell:path}")
async def grid_stream(cell: str):
    """SSE endpoint streaming live output from a worker's output.log."""
    worker_dir = WORKERS_DIR / cell
    log_path = worker_dir / "output.log"

    if not worker_dir.exists():
        raise HTTPException(status_code=404, detail=f"Worker {cell} not found")

    if _SYNC_TESTCLIENT_CALLS.get():
        lines: list[str] = []
        if log_path.exists():
            for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.strip():
                    lines.append(f"data: {line}\n\n")
        return Response(
            "".join(lines),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def event_stream():
        last_size = 0

        # Read existing content first
        if log_path.exists():
            with log_path.open("r", encoding="utf-8") as f:
                content = f.read()
                last_size = len(content.encode("utf-8"))
                for line in content.split("\n"):
                    if line.strip():
                        yield f"data: {line}\n\n"

        idle_ticks = 0
        while idle_ticks < 20:
            try:
                emitted = False
                if log_path.exists():
                    current_size = log_path.stat().st_size
                    if current_size > last_size:
                        with log_path.open("r", encoding="utf-8") as f:
                            f.seek(last_size)
                            new_content = f.read()
                            last_size = current_size
                            for line in new_content.split("\n"):
                                if line.strip():
                                    yield f"data: {line}\n\n"
                                    emitted = True
                if emitted:
                    idle_ticks = 0
                else:
                    idle_ticks += 1
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
        yield "event: done\ndata: stream closed\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── GAIJINN BLUEPRINT: Grid status (terminal pollSprint mirror) ───────────
# Exposes assigned_work_units, spawned, has_output for workerPresentation() in UI.
# Must list all manifest workers when session-scoped sprint (not only spawned subset).
# Spec invariant: worker.status_matches_assignment


def _worker_status_row(
    worker_id: str,
    *,
    workers_root: Path,
    runtime: Mapping[str, Any],
    manifest_detail: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    worker_dir = workers_root / worker_id
    log_path = worker_dir / "output.log"
    log_size = log_path.stat().st_size if log_path.exists() else 0
    detail = manifest_detail or {}
    status = str(runtime.get("status") or detail.get("status", "created"))
    assigned = detail.get("assigned_work_units", [])
    if not isinstance(assigned, list):
        assigned = []
    return {
        "name": worker_id,
        "status": status,
        "elapsed": detail.get("elapsed_seconds", 0),
        "log_size": log_size,
        "assigned_work_units": assigned,
        "spawned": bool(runtime),
        "has_output": log_size > 0,
    }


@app.get("/api/v1/grid/status")
async def grid_status(sprint_id: str | None = None, session_id: str | None = None):
    """Return per-cell + aggregate sprint progress from live sprint state and manifest."""
    workers_root = WORKERS_DIR
    manifest_path = WORKERS_DIR / "manifest.json"
    workers_status: list[dict[str, Any]] = []
    runtime_by_name: dict[str, dict[str, Any]] = {}
    sprint: dict[str, Any] | None = None

    if sprint_id:
        with _sprint_lock:
            sprint = _sprints.get(sprint_id)
        if sprint is not None:
            if sprint.get("workers_root"):
                workers_root = Path(str(sprint["workers_root"]))
            if sprint.get("manifest_path"):
                manifest_path = Path(str(sprint["manifest_path"]))
            _refresh_sprint_from_processes(sprint, manifest_path)
            for entry in sprint.get("processes", []):
                name = str(entry.get("name", ""))
                if name:
                    runtime_by_name[name] = entry

    manifest_details: dict[str, dict[str, Any]] = {}
    if manifest_path.exists():
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
            for d in manifest.get("worker_details", []):
                if isinstance(d, dict):
                    worker_id = str(d.get("worker_id", ""))
                    if worker_id:
                        manifest_details[worker_id] = d
        except (OSError, json.JSONDecodeError):
            pass

    seen: set[str] = set()
    for worker_id in sorted(manifest_details):
        seen.add(worker_id)
        workers_status.append(
            _worker_status_row(
                worker_id,
                workers_root=workers_root,
                runtime=runtime_by_name.get(worker_id, {}),
                manifest_detail=manifest_details[worker_id],
            )
        )

    for name, runtime in sorted(runtime_by_name.items()):
        if name in seen:
            continue
        workers_status.append(
            _worker_status_row(
                name,
                workers_root=workers_root,
                runtime=runtime,
            )
        )

    sprint_data = None
    if sprint_id and sprint_id in _sprints:
        s = _sprints[sprint_id]
        elapsed = time.time() - s["started_at"]
        sprint_data = {
            "sprint_id": sprint_id,
            "elapsed": round(elapsed, 1),
            "model": s["model"],
            "worker_count": len(s.get("processes", s.get("workers", []))),
            "status": s.get("status", "running"),
            "completed": s.get("completed", 0),
            "failed": s.get("failed", 0),
            "running": s.get("running", 0),
        }

    payload: dict[str, Any] = {
        "workers": workers_status,
        "total": len(workers_status),
        "sprint": sprint_data,
    }
    if session_id:
        try:
            payload["merge_pipeline"] = merge_pipeline_status(_session_store.project_root(session_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return payload


# ─── GRID LOGS ENDPOINT ───


@app.get("/api/v1/grid/logs")
async def grid_logs():
    """Return all raw output logs for post-hoc signal analysis."""
    logs = {}
    if WORKERS_DIR.exists():
        for worker_dir in sorted(WORKERS_DIR.iterdir()):
            if worker_dir.is_dir():
                log_path = worker_dir / "output.log"
                if log_path.exists():
                    try:
                        with log_path.open("r", encoding="utf-8") as f:
                            logs[worker_dir.name] = f.read()
                    except OSError:
                        logs[worker_dir.name] = "(error reading log)"
    return {"logs": logs}


async def _read_stream(
    sprint_id: str, worker_id: str, domain: str | None, stream: asyncio.StreamReader, log_file: IO[str]
):
    """Read a subprocess stream, write to log file, and broadcast lines to the sprint aggregate."""
    broadcaster = await get_broadcaster(sprint_id)
    while True:
        line = await stream.readline()
        if not line:
            break
        try:
            text = line.decode("utf-8").rstrip()
        except UnicodeDecodeError:
            text = line.decode("latin-1", errors="replace").rstrip()

        if text:
            log_file.write(text + "\n")
            log_file.flush()
            event_type = "log"
            if "TX-HT-" in text:
                event_type = "council_transaction"
            await broadcaster.broadcast(event_type=event_type, worker_id=worker_id, domain=domain, payload=text)


class SprintBroadcaster:
    """Multiplexes worker logs and council events into a single async stream."""

    def __init__(self, sprint_id: str, capacity: int = 1000):
        self.sprint_id = sprint_id
        self.ring_buffer: list[dict[str, Any]] = []
        self.capacity = capacity
        self.listeners: set[asyncio.Queue] = set()
        self.lock = asyncio.Lock()
        self.counter = 0

    async def broadcast(self, event_type: str, worker_id: str | None, payload: Any, domain: str | None = None):
        self.counter += 1
        event = {
            "id": f"{self.sprint_id}-{self.counter}",
            "event": event_type,
            "worker_id": worker_id,
            "domain": domain,
            "timestamp": time.time(),
            "payload": payload,
        }
        async with self.lock:
            self.ring_buffer.append(event)
            if len(self.ring_buffer) > self.capacity:
                self.ring_buffer.pop(0)
            for q in self.listeners:
                await q.put(event)

    async def subscribe(self, last_event_id: str | None = None) -> asyncio.Queue:
        q = asyncio.Queue()
        async with self.lock:
            if last_event_id:
                replay_started = False
                found_id = False
                for event in self.ring_buffer:
                    if event["id"] == last_event_id:
                        found_id = True
                        replay_started = True
                        continue
                    if replay_started:
                        await q.put(event)
                if not found_id:
                    for event in self.ring_buffer:
                        await q.put(event)
            self.listeners.add(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue):
        async with self.lock:
            self.listeners.discard(q)


_broadcasters: dict[str, SprintBroadcaster] = {}
_broadcaster_lock = asyncio.Lock()


async def get_broadcaster(sprint_id: str) -> SprintBroadcaster:
    async with _broadcaster_lock:
        if sprint_id not in _broadcasters:
            _broadcasters[sprint_id] = SprintBroadcaster(sprint_id)
        return _broadcasters[sprint_id]


@app.get("/api/v1/sprint/{sprint_id}/stream")
async def sprint_aggregate_stream(sprint_id: str, request: Request):
    """Aggregate SSE endpoint multiplexing all worker logs for a sprint."""
    last_event_id = request.headers.get("Last-Event-ID")
    broadcaster = await get_broadcaster(sprint_id)
    q = await broadcaster.subscribe(last_event_id)

    async def event_generator():
        try:
            while True:
                event = await q.get()
                # struct: id, event, data (Avoid double quotes in f-string for 3.10 compat)
                yield f"id: {event.get('id')}\nevent: {event.get('event')}\ndata: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            await broadcaster.unsubscribe(q)

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/v1/sprint/{sprint_id}/council")
async def sprint_council_event(sprint_id: str, message: str, worker_id: str | None = None, domain: str | None = None):
    """External hook to inject council transaction events into the sprint stream."""
    broadcaster = await get_broadcaster(sprint_id)
    await broadcaster.broadcast(event_type="council_transaction", worker_id=worker_id, domain=domain, payload=message)
    return {"status": "broadcasted"}


# Mount new generated frontend screens for live integration/browser access
_generated_dir = REPO_ROOT / "loom-frontend-base" / ".generated" / "loom"
if _generated_dir.is_dir():
    app.mount(
        "/vision_canvas",
        StaticFiles(directory=str(_generated_dir / "vision_canvas"), html=True),
        name="new_vision_canvas",
    )
    app.mount(
        "/command_engine",
        StaticFiles(directory=str(_generated_dir / "command_engine"), html=True),
        name="new_command_engine",
    )
    app.mount(
        "/terminal_screen",
        StaticFiles(directory=str(_generated_dir / "terminal"), html=True),
        name="new_terminal",
    )
    app.mount(
        "/continuation",
        StaticFiles(directory=str(_generated_dir / "continuation"), html=True),
        name="new_continuation",
    )
    app.mount(
        "/deliverable_launch",
        StaticFiles(directory=str(_generated_dir / "deliverable_launch"), html=True),
        name="new_deliverable_launch",
    )

# Mount sandbox_frontend static files at root (unified shell SPA serving).
_frontend_dir = FRONTEND_DIR
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="sandbox_ui_static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=api_bind_host(), port=int(os.environ.get("GAIJINN_API_PORT", "8080")))
