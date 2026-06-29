"""Intent Forge orchestration events using the canonical envelope."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_intent_event(
    *,
    session_id: str,
    event_type: str,
    data: dict[str, Any],
    sequence: int,
    blueprint_version: int,
    phase: str = "blueprinting",
    subphase: str | None = "intent_forge",
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "event_id": f"evt_{uuid.uuid4().hex}",
        "sequence": sequence,
        "emitted_at": _utc_now(),
        "session_id": session_id,
        "correlation_id": correlation_id,
        "causation_id": causation_id,
        "phase": phase,
        "subphase": subphase,
        "classification": "guided",
        "event_type": event_type,
        "data": {**data, "blueprint_version": blueprint_version},
    }
