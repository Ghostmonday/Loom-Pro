"""Validated Gaijinn project state model."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import StateError

SCHEMA_VERSION = 1
GAIJINN_DIR = Path(".gaijinn")
PROJECT_STATE_PATH = GAIJINN_DIR / "project.json"
DEFAULT_BLUEPRINT_PATH = GAIJINN_DIR / "GENERATE_BLUEPRINT.md"
DEFAULT_GRAPH_PATH = GAIJINN_DIR / "graph.json"
DEFAULT_METRICS_PATH = GAIJINN_DIR / "metrics_manifest.json"
DEFAULT_INTENT_PATH = GAIJINN_DIR / "intent.txt"
DEFAULT_WORKERS_PATH = GAIJINN_DIR / "workers"
PATH_FIELDS = (
    "blueprint_path",
    "graph_path",
    "metrics_path",
    "intent_path",
    "workers_path",
)


@dataclass(frozen=True)
class ProjectState:
    schema_version: int
    project_root: Path
    initialized_at: str
    prompt_hash: str
    activation_status: str
    blueprint_path: Path
    graph_path: Path
    metrics_path: Path
    intent_path: Path
    workers_path: Path
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def state_path(self) -> Path:
        return self.project_root / PROJECT_STATE_PATH


def new_state(
    root: Path,
    project_prompt: str,
    *,
    activation_status: str = "inactive",
    extra: Mapping[str, Any] | None = None,
) -> ProjectState:
    """Build a current ProjectState for `gaijinn init`."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return ProjectState(
        schema_version=SCHEMA_VERSION,
        project_root=root.resolve(),
        initialized_at=now,
        prompt_hash=_prompt_hash(project_prompt),
        activation_status=activation_status,
        blueprint_path=DEFAULT_BLUEPRINT_PATH,
        graph_path=DEFAULT_GRAPH_PATH,
        metrics_path=DEFAULT_METRICS_PATH,
        intent_path=DEFAULT_INTENT_PATH,
        workers_path=DEFAULT_WORKERS_PATH,
        extra=dict(extra or {}),
    )


def read_state(root: Path) -> ProjectState:
    """Read and validate .gaijinn/project.json."""
    state_path = root / PROJECT_STATE_PATH
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StateError(
            "missing .gaijinn/project.json",
            fix_command='gaijinn init "PROJECT PROMPT"',
        ) from exc
    except json.JSONDecodeError as exc:
        raise StateError(
            "invalid JSON in .gaijinn/project.json",
            cause=f"line {exc.lineno}, column {exc.colno}: {exc.msg}",
            fix_command='gaijinn init --force "PROJECT PROMPT"',
        ) from exc

    if not isinstance(payload, dict):
        raise StateError(".gaijinn/project.json must contain a JSON object")

    return _state_from_payload(root, payload)


def write_state(state: ProjectState) -> None:
    """Atomically write .gaijinn/project.json with deterministic formatting."""
    payload = _state_to_payload(state)
    target = state.state_path
    target.parent.mkdir(parents=True, exist_ok=True)

    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(target)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def ensure_state(root: Path) -> ProjectState:
    """Return validated state or raise a human-readable StateError."""
    try:
        return read_state(root)
    except StateError:
        raise


def state_payload(state: ProjectState) -> dict[str, Any]:
    """Return the deterministic JSON payload for tests and command integration."""
    return _state_to_payload(state)


def _state_from_payload(root: Path, payload: Mapping[str, Any]) -> ProjectState:
    schema_version = payload.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise StateError(
            "unsupported .gaijinn/project.json schema_version",
            cause=f"expected {SCHEMA_VERSION}; found {schema_version!r}",
            fix_command='gaijinn init --force "PROJECT PROMPT"',
        )

    root = root.resolve()
    legacy_payload = "project_prompt" in payload or "artifacts" in payload
    if not legacy_payload:
        required = {"project_root", "initialized_at", "prompt_hash", "activation_status", *PATH_FIELDS}
        missing = [key for key in required if key not in payload]
        if missing:
            joined = ", ".join(sorted(missing))
            raise StateError(f".gaijinn/project.json is missing required field(s): {joined}")

    artifacts = payload.get("artifacts") if isinstance(payload.get("artifacts"), Mapping) else {}
    prompt = payload.get("project_prompt")
    prompt_hash = payload.get("prompt_hash")
    if not isinstance(prompt_hash, str) or not prompt_hash.strip():
        prompt_hash = _prompt_hash(prompt if isinstance(prompt, str) else "")

    values: dict[str, Any] = {
        "schema_version": schema_version,
        "project_root": _optional_text(payload, "project_root", str(root)),
        "initialized_at": _optional_text(payload, "initialized_at", "1970-01-01T00:00:00Z"),
        "prompt_hash": prompt_hash,
        "activation_status": _optional_text(payload, "activation_status", "inactive"),
        "blueprint_path": _path_text(payload, artifacts, "blueprint_path", "blueprint_seed", DEFAULT_BLUEPRINT_PATH),
        "graph_path": _path_text(payload, artifacts, "graph_path", "graph", DEFAULT_GRAPH_PATH),
        "metrics_path": _path_text(payload, artifacts, "metrics_path", "metrics", DEFAULT_METRICS_PATH),
        "intent_path": _path_text(payload, artifacts, "intent_path", "intent", DEFAULT_INTENT_PATH),
        "workers_path": _path_text(payload, artifacts, "workers_path", "workers", DEFAULT_WORKERS_PATH),
    }

    missing = [key for key, value in values.items() if key != "schema_version" and not value]
    if missing:
        joined = ", ".join(sorted(missing))
        raise StateError(f".gaijinn/project.json is missing required field(s): {joined}")

    project_root = _resolve_project_root(root, values["project_root"])
    path_values = {key: _validate_path_field(key, values[key]) for key in PATH_FIELDS}

    extra = {key: value for key, value in payload.items() if key not in _formal_keys()}
    return ProjectState(
        schema_version=SCHEMA_VERSION,
        project_root=project_root,
        initialized_at=values["initialized_at"],
        prompt_hash=values["prompt_hash"],
        activation_status=values["activation_status"],
        blueprint_path=path_values["blueprint_path"],
        graph_path=path_values["graph_path"],
        metrics_path=path_values["metrics_path"],
        intent_path=path_values["intent_path"],
        workers_path=path_values["workers_path"],
        extra=extra,
    )


def _state_to_payload(state: ProjectState) -> dict[str, Any]:
    payload = dict(state.extra)
    payload.update(
        {
            "schema_version": state.schema_version,
            "project_root": str(state.project_root),
            "initialized_at": state.initialized_at,
            "prompt_hash": state.prompt_hash,
            "activation_status": state.activation_status,
            "blueprint_path": state.blueprint_path.as_posix(),
            "graph_path": state.graph_path.as_posix(),
            "metrics_path": state.metrics_path.as_posix(),
            "intent_path": state.intent_path.as_posix(),
            "workers_path": state.workers_path.as_posix(),
        }
    )
    if state.schema_version != SCHEMA_VERSION:
        raise StateError(f"cannot write unsupported schema_version {state.schema_version!r}")
    for key in PATH_FIELDS:
        _validate_path_field(key, payload[key])
    return payload


def _optional_text(payload: Mapping[str, Any], key: str, default: str) -> str:
    value = payload.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise StateError(f".gaijinn/project.json field `{key}` must be a string")
    return value.strip()


def _path_text(
    payload: Mapping[str, Any],
    artifacts: Mapping[str, Any],
    formal_key: str,
    legacy_key: str,
    default: Path,
) -> str:
    value = payload.get(formal_key, artifacts.get(legacy_key, default.as_posix()))
    if not isinstance(value, str):
        raise StateError(f".gaijinn/project.json field `{formal_key}` must be a string path")
    return value.strip()


def _resolve_project_root(root: Path, value: str) -> Path:
    override = os.environ.get("GAIJINN_PROJECT_ROOT", "").strip()
    if override:
        try:
            return Path(override).expanduser().resolve()
        except (OSError, RuntimeError) as exc:
            raise StateError("GAIJINN_PROJECT_ROOT is not a valid path") from exc
    return _validate_project_root(value, root)


def _validate_project_root(value: str, expected_root: Path) -> Path:
    try:
        path = Path(value).expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise StateError(".gaijinn/project.json field `project_root` is not a valid path") from exc
    if path != expected_root:
        raise StateError(f".gaijinn/project.json project_root points to {path}; expected {expected_root}")
    return path


def _validate_path_field(key: str, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise StateError(f".gaijinn/project.json field `{key}` must be a non-empty string path")

    path = Path(value)
    if path.is_absolute():
        raise StateError(f".gaijinn/project.json field `{key}` must be relative, found {value!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise StateError(f".gaijinn/project.json field `{key}` contains an unsafe path segment: {value!r}")
    if not path.parts or path.parts[0] != GAIJINN_DIR.name:
        raise StateError(f".gaijinn/project.json field `{key}` must stay under .gaijinn/: {value!r}")
    return path


def _prompt_hash(project_prompt: str) -> str:
    return hashlib.sha256(project_prompt.encode("utf-8")).hexdigest()


def _formal_keys() -> set[str]:
    return {
        "schema_version",
        "project_root",
        "initialized_at",
        "prompt_hash",
        "activation_status",
        *PATH_FIELDS,
    }


VALID_TRANSITIONS = {
    None: {"pending", "initialized", "created", "completed", "failed", "timed_out", "merged", "already_merged", "blocked", "conflicted"},
    "pending": {"spawning", "executing", "merged", "already_merged", "blocked", "conflicted"},
    "initialized": {"spawning"},
    "created": {"spawning", "executing", "completed", "failed", "timed_out", "merged", "already_merged", "blocked", "conflicted"},
    "spawning": {"executing", "completed", "failed", "timed_out"},
    "executing": {"completed", "failed", "timed_out"},
    "completed": {"merged", "already_merged", "blocked", "conflicted"},
    "failed": set(),
    "timed_out": set(),
    "blocked": {"merged", "already_merged", "conflicted"},
    "conflicted": {"merged", "already_merged", "blocked"},
    "merged": {"already_merged", "blocked", "conflicted"},
    "already_merged": {"merged", "blocked", "conflicted"},
}


def validate_worker_state_transition(from_state: str | None, to_state: str) -> None:
    """Enforces structural state machine invariants across parallel worker processes."""
    f_state = from_state.strip().lower() if from_state is not None else None
    t_state = to_state.strip().lower()

    if f_state == t_state:
        return

    allowed_next = VALID_TRANSITIONS.get(f_state, set())
    if t_state not in allowed_next:
        raise StateError(
            f"[STATE INVARIANT VIOLATION] Illegal state jump attempted: "
            f"'{from_state}' -> '{to_state}'."
        )


def transition_worker_state(manifest_path: Path, worker_id: str, new_status: str) -> None:
    """Transition a worker's status in the worker manifest file, validating the transition first."""
    if not manifest_path.exists():
        raise StateError(
            f"Worker manifest not found at {manifest_path}",
            cause="manifest.json must exist to transition worker state"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StateError(
            f"invalid JSON in worker manifest {manifest_path}",
            cause=str(exc)
        )

    found = False
    for detail in manifest.get("worker_details", []):
        if detail.get("worker_id") == worker_id:
            old_status = detail.get("status")
            validate_worker_state_transition(old_status, new_status)
            detail["status"] = new_status
            found = True
            break

    if not found:
        workers_list = manifest.get("workers", [])
        if worker_id in workers_list or worker_id.startswith("worker-"):
            validate_worker_state_transition(None, new_status)
            worker_details = manifest.setdefault("worker_details", [])
            worker_details.append({
                "worker_id": worker_id,
                "status": new_status
            })
        else:
            raise StateError(
                f"Worker {worker_id} not found in manifest",
                cause="Only registered workers can transition state"
            )

    temp_fd, temp_name = tempfile.mkstemp(
        prefix=f".{manifest_path.name}.",
        suffix=".tmp",
        dir=str(manifest_path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(manifest_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

