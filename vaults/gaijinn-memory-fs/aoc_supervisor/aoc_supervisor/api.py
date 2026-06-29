"""FastAPI boundary gateway for Gaijinn architectural health analysis + grid orchestration."""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import inspect
import io
import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import zipfile
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import parse_qs

from aoc_cli.helpers.council import (
    append_message,
    ensure_council,
    machine_council_address,
    render_council_markdown,
)
from aoc_cli.helpers.grid_executor import build_spawn_command, resolve_grid_executor
from aoc_cli.helpers.merge import load_merge_report, merge_pipeline_status
from aoc_cli.helpers.stealth import sanitize_analyze_api_response
from aoc_cli.moat import parse_prompt as moat_parse_prompt
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from starlette.routing import Match
from starlette.testclient import TestClient as StarletteTestClient

from aoc_supervisor.billing import (
    DEFAULT_LEDGER_STORAGE,
    BillingLedgerException,
    InsufficientCreditsException,
    SprintTokenException,
    _compute_blueprint_cost,
    _compute_sprint_cost,
    deduct_deployment_fee,
    issue_sprint_token,
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
from aoc_supervisor.orchestrate_session import (
    DESIGN_COMMAND_TIMEOUT_DEFAULT,
    OrchestrateSessionStore,
    design_command_timeout,
    normalize_phases,
    validate_loaded_context,
)
from aoc_supervisor.orchestrator import ClusterOrchestrator
from aoc_supervisor.preflight import PreflightResolutionError, run_preflight_check
from aoc_supervisor.repo_paths import (
    COMMAND_ENGINE_HTML_PATH,
    NEURAL_DRAFT_CSS_PATH,
    NEURAL_DRAFT_HTML_PATH,
    NEURAL_DRAFT_JS_PATH,
    TERMINAL_HTML_PATH,
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
    except BillingLedgerException:
        DEFAULT_LEDGER_STORAGE.write_ledger(
            {"terminal-user": {"balance": float(minimum), "status": "active"}},
        )


@contextlib.asynccontextmanager
async def _app_lifespan(_app: FastAPI):
    _seed_terminal_user_credits()
    yield


app = FastAPI(title="Gaijinn AOC Boundary Gateway", version="1.0.0", lifespan=_app_lifespan)


def _patch_testclient_for_httpx28() -> None:
    """Keep local TestClient smoke tests usable with Starlette's legacy httpx shim."""
    if getattr(StarletteTestClient, "_gaijinn_httpx28_patch", False):
        return
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
        for route in app_obj.router.routes:
            match, child_scope = route.matches(scope)
            if match == Match.FULL:
                starlette_request.scope.update(child_scope)
                return route, dict(child_scope.get("path_params", {}))
        raise HTTPException(status_code=404, detail="Not Found")

    async def _call_endpoint(route: Any, starlette_request: Request, path_params: dict[str, Any]) -> Any:
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

    def enter(self: Any) -> Any:
        return self

    def exit(self: Any, *_exc: Any) -> None:
        close = getattr(self, "close", None)
        if callable(close):
            close()

    StarletteTestClient.request = request  # type: ignore[method-assign]
    StarletteTestClient.__enter__ = enter  # type: ignore[method-assign]
    StarletteTestClient.__exit__ = exit  # type: ignore[method-assign]
    StarletteTestClient._gaijinn_httpx28_patch = True  # type: ignore[attr-defined]


_patch_testclient_for_httpx28()

# Global thread-safe ClusterOrchestrator singleton.
_orchestrator_lock = Lock()
_orchestrator: ClusterOrchestrator | None = None

# Build sessions (intent → blueprint → swarm) — always under main repo
_session_store = OrchestrateSessionStore(REPO_ROOT)

# Active sprint tracking
_sprints: dict[str, dict[str, Any]] = {}
_sprint_lock = Lock()
_next_sprint_id = 1


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


def _worker_runtime_status(proc: subprocess.Popen[Any]) -> tuple[str, int | None]:
    exit_code = proc.poll()
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
        status, exit_code = _worker_runtime_status(proc)
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
        sprint["status"] = "failed" if failed else "completed"
        sprint.setdefault("finished_at", time.time())


async def _monitor_sprint(sprint_id: str, manifest_path: Path, timeout: int) -> None:
    """Background monitor: update sprint + manifest as worker subprocesses finish."""
    while True:
        await asyncio.sleep(1.0)
        with _sprint_lock:
            sprint = _sprints.get(sprint_id)
        if sprint is None:
            return

        elapsed_total = time.time() - sprint["started_at"]
        _refresh_sprint_from_processes(sprint, manifest_path)

        running = int(sprint.get("running", 0) or 0)
        failed = int(sprint.get("failed", 0) or 0)
        if running == 0:
            sprint["status"] = "failed" if failed else "completed"
            sprint["finished_at"] = time.time()
            return
        if elapsed_total >= timeout:
            for entry in sprint.get("processes", []):
                proc = entry.get("proc")
                if proc is not None and proc.poll() is None:
                    proc.kill()
                    proc.wait()
                    entry["status"] = "timed_out"
            sprint["status"] = "timed_out"
            sprint["finished_at"] = time.time()
            return


def _spawn_worker_command(
    *,
    worker_name: str,
    worker_dir: Path,
    full_prompt: str,
    model: str,
    executor: str = "auto",
    has_assigned_work: bool = True,
) -> list[str]:
    mock_grid = os.environ.get("GAIJINN_MOCK_GRID", "").strip().lower() in {"1", "true", "yes", "on"}
    try:
        return build_spawn_command(
            worker_name=worker_name,
            worker_dir=worker_dir,
            full_prompt=full_prompt,
            model=model,
            executor=executor,
            has_assigned_work=has_assigned_work,
            mock_grid=mock_grid,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"{exc} (set GAIJINN_MOCK_GRID=1 for local UI testing)",
        ) from exc


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


@app.get("/")
async def terminal_ui() -> FileResponse:
    """Serve the Gaijinn Command Bridge terminal UI."""
    if not TERMINAL_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="gaijinn-terminal.html not found")
    return FileResponse(TERMINAL_HTML_PATH, media_type="text/html")


COMMAND_ENGINE_CSS_PATH = COMMAND_ENGINE_HTML_PATH.with_suffix(".css")
COMMAND_ENGINE_JS_PATH = COMMAND_ENGINE_HTML_PATH.with_suffix(".js")
BLUEPRINT_VIZ_JS_PATH = COMMAND_ENGINE_HTML_PATH.parent / "blueprint-viz-engine.js"


@app.get("/command-engine")
async def command_engine_ui() -> FileResponse:
    """Serve the brutalist command engine dashboard."""
    if not COMMAND_ENGINE_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="command-engine.html not found")
    return FileResponse(COMMAND_ENGINE_HTML_PATH, media_type="text/html")


@app.get("/command-engine.css")
async def command_engine_css() -> FileResponse:
    if not COMMAND_ENGINE_CSS_PATH.exists():
        raise HTTPException(status_code=404, detail="command-engine.css not found")
    return FileResponse(COMMAND_ENGINE_CSS_PATH, media_type="text/css")


@app.get("/command-engine.js")
async def command_engine_js() -> FileResponse:
    if not COMMAND_ENGINE_JS_PATH.exists():
        raise HTTPException(status_code=404, detail="command-engine.js not found")
    return FileResponse(COMMAND_ENGINE_JS_PATH, media_type="application/javascript")


@app.get("/blueprint-viz-engine.js")
async def blueprint_viz_engine_js() -> FileResponse:
    if not BLUEPRINT_VIZ_JS_PATH.exists():
        raise HTTPException(status_code=404, detail="blueprint-viz-engine.js not found")
    return FileResponse(BLUEPRINT_VIZ_JS_PATH, media_type="application/javascript")


@app.get("/internal")
async def neural_draft_ui() -> FileResponse:
    """Serve Neural Draft LLC internal manufacturing console (not public GTM)."""
    if not NEURAL_DRAFT_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="neural-draft/index.html not found")
    return FileResponse(NEURAL_DRAFT_HTML_PATH, media_type="text/html")


@app.get("/internal.css")
async def neural_draft_css() -> FileResponse:
    if not NEURAL_DRAFT_CSS_PATH.exists():
        raise HTTPException(status_code=404, detail="neural-draft/console.css not found")
    return FileResponse(NEURAL_DRAFT_CSS_PATH, media_type="text/css")


@app.get("/internal.js")
async def neural_draft_js() -> FileResponse:
    if not NEURAL_DRAFT_JS_PATH.exists():
        raise HTTPException(status_code=404, detail="neural-draft/console.js not found")
    return FileResponse(NEURAL_DRAFT_JS_PATH, media_type="application/javascript")


@app.post("/api/v1/analyze")
async def analyze(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    payload_path = _write_payload_to_scratch(payload)

    try:
        validation = validate_system_state(payload_path)
    except StructuralGravityViolation as exc:
        raise HTTPException(
            status_code=422,
            detail={"violating_nodes": _nodes_from_violation(exc)},
        ) from exc

    response = _analysis_response(validation)
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
async def blueprint_deliberate(intent: str, timeout: int | None = None) -> StreamingResponse:
    """SSE stream — real prepare() stages drive deliberation (architectural teleology)."""
    cleaned = str(intent or "").strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="intent is required")
    layer1_timeout_s = design_command_timeout(timeout)

    async def event_stream():
        step_queue: queue.Queue[tuple[str, str, dict[str, Any], float]] = queue.Queue()
        result_holder: dict[str, Any] = {}
        error_holder: dict[str, Exception] = {}

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

        thread = threading.Thread(target=run_prepare, daemon=True)
        thread.start()

        deliberation_started = time.monotonic()
        last_heartbeat = deliberation_started

        yield _sse_event(
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
            return _sse_event("phase_complete", payload)

        while thread.is_alive() or not step_queue.empty():
            try:
                kind, step, payload, stamp = step_queue.get(timeout=0.15)
            except queue.Empty:
                now = time.monotonic()
                if thread.is_alive() and now - last_heartbeat >= DELIBERATION_HEARTBEAT_S:
                    elapsed_ms = int((now - deliberation_started) * 1000)
                    yield _sse_event(
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
                yield _sse_event("deliberation_error", {"message": step[-500:]})
                break

            if kind == "done":
                snapshot = result_holder.get("snapshot")
                if snapshot is None:
                    yield _sse_event("deliberation_error", {"message": "prepare returned no snapshot"})
                    break
                public = snapshot.to_public_dict()
                if active_phase:
                    yield complete_phase(active_phase)
                yield _sse_event(
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
            yield _sse_event("step_progress", {"step": step, **payload})

            if step == "session_seed":
                root = payload.get("session_root")
                if root:
                    session_root = Path(str(root))

            if step == "init_start":
                begin_phase("intent_parse")
                yield _sse_event(
                    "phase_begin",
                    {"phase": "intent_parse", "message": TELEOLOGY_PHASES["intent_parse"], "step": step},
                )

            if step == "compile_prompt_complete" and session_root:
                streams = await asyncio.to_thread(lambda: detect_intent_streams(cleaned))
                for stream in streams[:8]:
                    yield _sse_event(
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
                yield _sse_event(
                    "phase_begin",
                    {"phase": "graph_ingest", "message": TELEOLOGY_PHASES["graph_ingest"], "step": step},
                )

            if step == "scan_complete" and session_root:
                nodes = await asyncio.to_thread(_session_graph_nodes, session_root)
                for node in nodes:
                    yield _sse_event("node_added", node)
                yield complete_phase("graph_ingest", {"nodes": len(nodes)})

            if step == "analyze_start":
                begin_phase("curvature_compute")
                yield _sse_event(
                    "phase_begin",
                    {"phase": "curvature_compute", "message": TELEOLOGY_PHASES["curvature_compute"], "step": step},
                )

            if step == "analyze_complete" and session_root:
                edges = await asyncio.to_thread(_session_curvature_events, session_root)
                bridge_count = 0
                for edge in edges:
                    yield _sse_event(
                        "edge_curvature",
                        {"source": edge["source"], "target": edge["target"], "kappa": edge["kappa"]},
                    )
                    if edge.get("dark"):
                        bridge_count += 1
                        yield _sse_event(
                            "dark_bridge_detected",
                            {"source": edge["source"], "target": edge["target"], "kappa": edge["kappa"]},
                        )
                yield complete_phase("curvature_compute", {"edges": len(edges)})

                begin_phase("bridge_detect")
                yield _sse_event(
                    "phase_begin",
                    {"phase": "bridge_detect", "message": TELEOLOGY_PHASES["bridge_detect"], "step": step},
                )
                yield complete_phase("bridge_detect", {"bridges": bridge_count})

            if step in {"plan_start", "intent_blueprint_start"}:
                begin_phase("weld_plan")
                yield _sse_event(
                    "phase_begin",
                    {"phase": "weld_plan", "message": TELEOLOGY_PHASES["weld_plan"], "step": step},
                )

            if step in {"plan_complete", "intent_blueprint_complete"} and session_root:
                blueprint = await asyncio.to_thread(_session_blueprint_events, session_root)
                if blueprint["welds"]:
                    yield _sse_event("weld_start", {"cluster": blueprint["welds"][:4], "mode": "atomic_weld"})
                    yield _sse_event("weld_complete", {"block_id": "geometry-weld"})
                for gateway in blueprint["gateways"][:6]:
                    yield _sse_event("handoff_gateway", {"detail": gateway})
                yield complete_phase("weld_plan", {"gateways": len(blueprint["gateways"])})
                begin_phase("partition")
                yield _sse_event(
                    "phase_begin",
                    {"phase": "partition", "message": TELEOLOGY_PHASES["partition"], "step": step},
                )
                for wu in blueprint["work_units"]:
                    yield _sse_event("work_unit_assigned", wu)
                yield complete_phase("partition", {"work_units": len(blueprint["work_units"])})

                begin_phase("blueprint_freeze")
                yield _sse_event(
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
    if request.headers.get("X-User-Id"):
        return str(request.headers["X-User-Id"])
    if isinstance(payload, dict) and payload.get("user_id"):
        return str(payload["user_id"])
    return "anonymous"


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
    rows = await asyncio.to_thread(_council_ledger_rows, ROOT_DIR, tail=limit)
    return {
        "path": str(ROOT_DIR / ".gaijinn" / "bridge" / "council.jsonl"),
        "rows": rows,
        "count": len(rows),
    }


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
    try:
        snapshot = await _run_blocking(
            _session_store.prepare,
            intent,
            list(phases),
            loaded_context,
            layer1_timeout=layer1_timeout,
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
    session_id = str(body.get("session_id", "")).strip()
    workers = body.get("workers")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    if not isinstance(workers, int) or workers < 1:
        raise HTTPException(status_code=400, detail="workers must be a positive integer")
    try:
        snapshot = await _run_blocking(_session_store.assign_swarm, session_id, workers)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return snapshot.to_public_dict()


@app.get("/api/v1/orchestrate/session/{session_id}")
async def orchestrate_session(session_id: str) -> dict[str, Any]:
    try:
        snapshot = _session_store.get(session_id)
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

    from aoc_cli.helpers.project_profile import load_executor_profile

    hermes_model = load_executor_profile(ROOT_DIR).get("hermes_model", "").strip()
    hermes_cmd: list[str] = ["hermes"]
    if hermes_model:
        hermes_cmd.extend(["-m", hermes_model])
    hermes_cmd.extend(["-z", prompt])

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
    global _next_sprint_id

    try:
        body = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    user_id = _extract_user_id(request, body if isinstance(body, dict) else None)
    workers = body.get("workers", 4)
    from aoc_cli.helpers.project_profile import load_executor_profile

    profile = load_executor_profile(ROOT_DIR)
    model = str(body.get("model", profile.get("grid_model", "grok-composer-2.5-fast"))).strip()
    executor = str(body.get("executor", profile.get("grid_executor", "auto"))).strip().lower() or "auto"
    task = body.get("task", "")
    session_id = str(body.get("session_id", "")).strip()
    sprint_token = body.get("sprint_token")

    if not isinstance(workers, int) or workers < 1:
        raise HTTPException(status_code=400, detail="workers must be a positive integer")

    if not sprint_token:
        raise HTTPException(status_code=401, detail="sprint_token is required")

    try:
        token_record = validate_sprint_token(
            str(sprint_token),
            user_id=user_id,
            workers=workers,
        )
    except SprintTokenException as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        deduct_deployment_fee(
            user_id,
            Decimal(str(token_record["sprint_price"])),
            storage_provider=DEFAULT_LEDGER_STORAGE,
        )
    except InsufficientCreditsException as exc:
        raise HTTPException(
            status_code=402,
            detail={"error": str(exc), "sprint_price": token_record["sprint_price"]},
        ) from exc

    try:
        validate_sprint_token(
            str(sprint_token),
            user_id=user_id,
            workers=workers,
            consume=True,
        )
    except SprintTokenException as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    workers_root = WORKERS_DIR
    if session_id:
        try:
            workers_root = _session_store.workers_dir(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Read manifest
    manifest_path = workers_root / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(
            status_code=400, detail="No worker manifest found. Run 'gaijinn run-grid --workers N' first."
        )

    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read manifest: {exc}") from exc

    registered = manifest.get("worker_details", [])
    manifest_by_worker = {
        str(detail.get("worker_id", "")): detail
        for detail in registered
        if isinstance(detail, dict) and detail.get("worker_id")
    }
    if len(registered) < workers:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Manifest has {len(registered)} workers but {workers} requested. "
                f"Run 'gaijinn run-grid --workers {workers}' first."
            ),
        )

    mock_grid = os.environ.get("GAIJINN_MOCK_GRID", "").strip().lower() in {"1", "true", "yes", "on"}
    if not mock_grid:
        try:
            resolved_executor = resolve_grid_executor(executor)
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(
                status_code=503,
                detail=f"{exc} (set GAIJINN_MOCK_GRID=1 for local UI testing)",
            ) from exc
    else:
        resolved_executor = "mock"

    # Create sprint
    sprint_id = str(_next_sprint_id)
    _next_sprint_id += 1

    worker_list = []
    processes = []

    for i in range(workers):
        worker_name = f"worker-{i + 1:03d}"
        worker_dir = workers_root / worker_name

        if not worker_dir.exists():
            worker_list.append({"name": worker_name, "status": "not_found"})
            continue

        log_path = worker_dir / "output.log"

        # Build task prompt from work unit + GIV
        work_unit_path = worker_dir / "WORK_UNIT.md"
        intent_path = worker_dir / "WORKER_INTENT.txt"
        giv_path = worker_dir / "giv.json"

        work_unit_text = ""
        if work_unit_path.exists():
            work_unit_text = work_unit_path.read_text(encoding="utf-8")
        elif intent_path.exists():
            work_unit_text = intent_path.read_text(encoding="utf-8")

        giv = {}
        if giv_path.exists():
            try:
                with giv_path.open("r", encoding="utf-8") as f:
                    giv = json.load(f)
            except (OSError, json.JSONDecodeError):
                giv = {}

        # Build prompt with GIV constraints
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
            executor=executor,
            has_assigned_work=has_assigned_work,
        )

        with log_path.open("w", encoding="utf-8") as lf:
            lf.write(f"=== GAIJINN GRID SPAWN: {worker_name} ===\n")
            lf.write(f"Executor: {resolved_executor}\n")
            lf.write(f"Model: {model}\n")
            lf.write(f"Started: {time.ctime()}\n")
            lf.write(f"Command: {' '.join(cmd)}\n")
            lf.write("=" * 60 + "\n\n")

        with log_path.open("a", encoding="utf-8") as stdout_file:
            proc = subprocess.Popen(
                cmd,
                stdout=stdout_file,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(worker_dir.resolve()),
            )

        processes.append({"name": worker_name, "proc": proc, "dir": str(worker_dir), "status": "running"})
        worker_list.append({"name": worker_name, "status": "spawned", "pid": proc.pid})

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
        "session_id": session_id or None,
    }

    with _sprint_lock:
        _sprints[sprint_id] = sprint_info

    timeout = int(body.get("timeout", _DEFAULT_SPRINT_TIMEOUT))
    asyncio.create_task(_monitor_sprint(sprint_id, manifest_path, timeout))

    return {
        "sprint_id": sprint_id,
        "workers": [w["name"] for w in worker_list],
        "status": "spawned",
        "count": len(worker_list),
    }


# ─── GRID STREAM (SSE) ENDPOINT ───


@app.get("/api/v1/grid/stream/{cell:path}")
async def grid_stream(cell: str):
    """SSE endpoint streaming live output from a worker's output.log."""
    worker_dir = WORKERS_DIR / cell
    log_path = worker_dir / "output.log"

    if not worker_dir.exists():
        raise HTTPException(status_code=404, detail=f"Worker {cell} not found")

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
