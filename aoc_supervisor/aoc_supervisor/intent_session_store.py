"""Disk-backed Intent Forge session persistence with write-ahead transitions."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from aoc_supervisor.intent_blueprint_state import INTENT_FORGE_SCHEMA_VERSION, new_session_id


class VersionConflictError(Exception):
    """Raised when expected_blueprint_version does not match persisted state."""


class IdempotencyReplayError(Exception):
    """Raised when an idempotency key was already processed."""


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


class IntentForgeSessionStore:
    def __init__(self, host_root: Path) -> None:
        self.host_root = host_root.resolve()
        self.root = self.host_root / ".gaijinn" / "intent-forge" / "sessions"

    def session_dir(self, session_id: str) -> Path:
        return self.root / session_id

    def session_path(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "session.json"

    def blueprint_path(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "blueprint.json"

    def events_path(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "events.jsonl"

    def versions_dir(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "versions"

    def load(self, session_id: str) -> dict[str, Any]:
        path = self.session_path(session_id)
        if not path.is_file():
            raise KeyError(f"intent forge session not found: {session_id}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"invalid session payload: {session_id}")
        return payload

    def save(self, session_id: str, state: dict[str, Any], *, expected_version: int | None = None) -> None:
        current = self.load(session_id) if self.session_path(session_id).is_file() else None
        if (
            expected_version is not None
            and current is not None
            and int(current.get("blueprint_version", -1)) != int(expected_version)
        ):
            raise VersionConflictError(
                f"expected blueprint_version {expected_version}, found {current.get('blueprint_version')}"
            )
        state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _atomic_write_json(self.session_path(session_id), state)
        version = int(state.get("blueprint_version", 0))
        version_path = self.versions_dir(session_id) / f"v{version:04d}.json"
        _atomic_write_json(version_path, state)
        _atomic_write_json(self.blueprint_path(session_id), state)

    def create(self, state: dict[str, Any]) -> str:
        session_id = str(state.get("session_id") or new_session_id())
        state["session_id"] = session_id
        state["schema_version"] = INTENT_FORGE_SCHEMA_VERSION
        self.session_dir(session_id).mkdir(parents=True, exist_ok=True)
        _atomic_write_json(self.session_path(session_id), state)
        _atomic_write_json(self.blueprint_path(session_id), state)
        return session_id

    def append_event(self, session_id: str, event: dict[str, Any]) -> None:
        path = self.events_path(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    def claim_idempotency(self, state: dict[str, Any], key: str) -> None:
        normalized = key.strip()
        if not normalized:
            raise ValueError("idempotency_key is required")
        processed = state.setdefault("processed_idempotency_keys", [])
        if normalized in processed:
            raise IdempotencyReplayError(f"idempotency key already processed: {normalized}")
        processed.append(normalized)
