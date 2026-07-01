"""Session ID validation, path containment, and API principal checks.

``GAIJINN_REQUIRE_AUTH`` enforces principal-required session ownership for
trusted/local deployments. ``X-User-Id`` / body ``user_id`` are caller-supplied
identifiers — not verified credentials. Suitable with default ``127.0.0.1`` bind;
remote exposure still needs API keys, signed tokens, OAuth, or proxy auth.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request, WebSocket

SESSION_ID_PATTERN = re.compile(r"^[a-f0-9]{12}$")
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def validate_session_id(session_id: str) -> str:
    """Accept only orchestration session IDs (12 lowercase hex chars)."""
    normalized = session_id.strip()
    if not SESSION_ID_PATTERN.match(normalized):
        raise ValueError(f"invalid session_id: {session_id!r}")
    return normalized


def resolve_confined_session_path(sessions_dir: Path, session_id: str) -> Path:
    """Resolve a session directory and ensure it stays under sessions_dir."""
    normalized = validate_session_id(session_id)
    sessions_root = sessions_dir.resolve()
    candidate = (sessions_root / normalized).resolve()
    try:
        candidate.relative_to(sessions_root)
    except ValueError as exc:
        raise KeyError(f"session path escapes storage root: {normalized!r}") from exc
    if not candidate.is_dir():
        raise KeyError(f"unknown session {normalized!r}")
    meta_path = candidate / ".gaijinn" / "session.json"
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise KeyError(f"session metadata is invalid: {normalized!r}") from exc
        stored_id = str(meta.get("session_id", "")).strip()
        if stored_id and stored_id != normalized:
            raise KeyError(f"session metadata mismatch for {normalized!r}")
    return candidate


def extract_user_id(request: Request, payload: dict[str, Any] | None = None) -> str:
    if request.headers.get("X-User-Id"):
        return str(request.headers["X-User-Id"]).strip()
    if isinstance(payload, dict) and payload.get("user_id"):
        return str(payload["user_id"]).strip()
    return "anonymous"


def require_user_id(request: Request, payload: dict[str, Any] | None = None) -> str:
    """Return caller-supplied principal; reject anonymous when principal is required."""
    user_id = extract_user_id(request, payload)
    if principal_required() and user_id == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="principal required for session ownership (set X-User-Id or user_id)",
        )
    return user_id


def principal_required() -> bool:
    """True when GAIJINN_REQUIRE_AUTH demands a non-anonymous caller principal."""
    return os.environ.get("GAIJINN_REQUIRE_AUTH", "").strip().lower() in _TRUTHY


def auth_required() -> bool:
    """Backward-compatible alias for principal_required()."""
    return principal_required()


def api_bind_host() -> str:
    return os.environ.get("GAIJINN_API_BIND", "127.0.0.1").strip() or "127.0.0.1"


def assert_session_owner(session_root: Path, user_id: str) -> None:
    """Enforce per-session ownership when owner_user_id is recorded."""
    meta_path = session_root / ".gaijinn" / "session.json"
    if not meta_path.is_file():
        return
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="session metadata is invalid") from None
    owner = str(meta.get("owner_user_id", "")).strip()
    if not owner:
        return
    if user_id != owner:
        raise HTTPException(status_code=403, detail="session access denied for this principal")


def _check_api_key(headers: Any, query_params: Any) -> None:
    allow_insecure = os.environ.get("GAIJINN_ALLOW_INSECURE_LOCAL", "").strip().lower() in _TRUTHY
    if allow_insecure:
        return

    expected_key = os.environ.get("LOOM_API_KEY", os.environ.get("GAIJINN_API_KEY", "")).strip()
    if not expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    provided_key = (headers.get("X-Loom-Api-Key") or headers.get("X-Gaijinn-Api-Key") or "").strip()
    if not provided_key:
        provided_key = query_params.get("api_key", "").strip()

    if provided_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def validate_api_key(request: Request) -> None:
    """Validate X-Loom-Api-Key / X-Gaijinn-Api-Key header or api_key query param for HTTP."""
    _check_api_key(request.headers, request.query_params)


def validate_api_key_ws(websocket: WebSocket) -> None:
    """Validate X-Loom-Api-Key / X-Gaijinn-Api-Key header or api_key query param for WebSockets."""
    _check_api_key(websocket.headers, websocket.query_params)
