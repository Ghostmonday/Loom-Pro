"""Deterministic Agent Intent Vector schema and renderers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

DEFAULT_DENIED_COMMANDS = ("git push",)
DEFAULT_PROHIBITIONS = (
    "no destructive cleanup outside workspace",
    "no edits outside assigned paths",
    "no git push",
    "no secret exfiltration",
)
SCHEMA_VERSION = 1


class GIVValidationError(ValueError):
    """Raised when an Agent Intent Vector is incomplete or unsafe."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class HandoffTicket:
    """Structured cross-boundary mutation request emitted by a worker agent."""

    ticket_id: str
    source_worker_id: str
    target_work_unit_id: str
    target_file: str
    required_mutation_context: str
    status: str = "pending"
    timestamp: str = field(default_factory=_utc_now)
    resolution_commit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ticket_id": self.ticket_id,
            "source_worker_id": self.source_worker_id,
            "target_work_unit_id": self.target_work_unit_id,
            "target_file": self.target_file,
            "required_mutation_context": self.required_mutation_context,
            "status": self.status,
            "timestamp": self.timestamp,
        }
        if self.resolution_commit is not None:
            payload["resolution_commit"] = self.resolution_commit
        return payload


@dataclass(frozen=True)
class GIV:
    """Worker-scoped Agent Intent Vector.

    The vector captures the paths, commands, capabilities, prohibitions, and
    invariants assigned to one worker. Construction validates the required
    safety floor and stores a canonical deterministic representation.
    """

    worker_id: str
    allowed_paths: tuple[str, ...]
    denied_paths: tuple[str, ...] = field(default_factory=tuple)
    allowed_commands: tuple[str, ...] = field(default_factory=tuple)
    denied_commands: tuple[str, ...] = field(default_factory=lambda: DEFAULT_DENIED_COMMANDS)
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    prohibitions: tuple[str, ...] = field(default_factory=lambda: DEFAULT_PROHIBITIONS)
    invariants: tuple[str, ...] = field(default_factory=tuple)
    structural_tokens: Mapping[str, bool] = field(default_factory=dict)
    sibling_denied_paths: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        worker_id = str(self.worker_id).strip()
        if not worker_id:
            raise GIVValidationError("worker_id is required")

        allowed_paths = _normalize_items(self.allowed_paths)
        if not allowed_paths:
            raise GIVValidationError("allowed_paths cannot be empty for worker-scoped intent")

        denied_commands = _normalize_items((*self.denied_commands, *DEFAULT_DENIED_COMMANDS))
        if "git push" not in denied_commands:
            raise GIVValidationError("denied_commands must include git push")

        prohibitions = _normalize_items((*self.prohibitions, *DEFAULT_PROHIBITIONS))
        structural_tokens = _structural_tokens(self.structural_tokens)

        object.__setattr__(self, "worker_id", worker_id)
        object.__setattr__(self, "allowed_paths", allowed_paths)
        object.__setattr__(self, "denied_paths", _normalize_items(self.denied_paths))
        object.__setattr__(self, "allowed_commands", _normalize_items(self.allowed_commands))
        object.__setattr__(self, "denied_commands", denied_commands)
        object.__setattr__(self, "capabilities", _normalize_items(self.capabilities))
        object.__setattr__(self, "prohibitions", prohibitions)
        object.__setattr__(self, "invariants", _normalize_items(self.invariants))
        object.__setattr__(self, "structural_tokens", structural_tokens)
        object.__setattr__(self, "sibling_denied_paths", _normalize_items(self.sibling_denied_paths))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible payload."""
        return {
            "schema_version": SCHEMA_VERSION,
            "worker_id": self.worker_id,
            "allowed_paths": list(self.allowed_paths),
            "denied_paths": list(self.denied_paths),
            "allowed_commands": list(self.allowed_commands),
            "denied_commands": list(self.denied_commands),
            "capabilities": list(self.capabilities),
            "prohibitions": list(self.prohibitions),
            "invariants": list(self.invariants),
            "structural_tokens": dict(self.structural_tokens),
            "sibling_denied_paths": list(self.sibling_denied_paths),
        }

    def to_json(self) -> str:
        """Serialize the vector as stable, pretty-printed JSON."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    def render_intent(self) -> str:
        """Render the vector as a human-readable intent.txt document."""
        sections = [
            "# Agent Intent Vector",
            "",
            f"Worker: {self.worker_id}",
            "",
            "## Allowed Paths",
            *_bullet_lines(self.allowed_paths),
            "",
            "## Denied Paths",
            *_bullet_lines(self.denied_paths),
            "",
            "## Allowed Commands",
            *_bullet_lines(self.allowed_commands),
            "",
            "## Denied Commands",
            *_bullet_lines(self.denied_commands),
            "",
            "## Capabilities",
            *_bullet_lines(self.capabilities),
            "",
            "## Prohibitions",
            *_bullet_lines(self.prohibitions),
            "",
            "## Invariants",
            *_bullet_lines(self.invariants),
            "",
            "## Structural Tokens",
            *_bullet_lines(f"{key}: {'true' if value else 'false'}" for key, value in self.structural_tokens.items()),
            "",
            "## Sibling Denied Paths",
            *_bullet_lines(self.sibling_denied_paths),
            "",
        ]
        return "\n".join(sections)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> GIV:
        """Build a vector from a mapping, applying default safety constraints."""
        schema_version = payload.get("schema_version", SCHEMA_VERSION)
        if schema_version != SCHEMA_VERSION:
            raise GIVValidationError(f"unsupported schema_version {schema_version!r}; expected {SCHEMA_VERSION}")
        return cls(
            worker_id=_required_text(payload, "worker_id"),
            allowed_paths=_sequence(payload, "allowed_paths"),
            denied_paths=_sequence(payload, "denied_paths"),
            allowed_commands=_sequence(payload, "allowed_commands"),
            denied_commands=_sequence(payload, "denied_commands", DEFAULT_DENIED_COMMANDS),
            capabilities=_sequence(payload, "capabilities"),
            prohibitions=_sequence(payload, "prohibitions", DEFAULT_PROHIBITIONS),
            invariants=_sequence(payload, "invariants"),
            structural_tokens=_mapping(payload, "structural_tokens"),
            sibling_denied_paths=_sequence(payload, "sibling_denied_paths"),
        )


def _normalize_items(items: Iterable[Any]) -> tuple[str, ...]:
    normalized = {str(item).strip() for item in items if str(item).strip()}
    return tuple(sorted(normalized))


def _bullet_lines(items: Iterable[str]) -> list[str]:
    values = list(items)
    if not values:
        return ["- none"]
    return [f"- {item}" for item in values]


def _structural_tokens(tokens: Mapping[str, Any]) -> dict[str, bool]:
    defaults = {
        "scope_strict": True,
        "no_sibling_trespass": True,
        "handoff_only": True,
    }
    merged = {**defaults, **{str(key): bool(value) for key, value in tokens.items()}}
    return {key: bool(merged[key]) for key in sorted(defaults)}


def _mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise GIVValidationError(f"{key} must be a mapping")
    return value


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GIVValidationError(f"{key} is required")
    return value


def _sequence(
    payload: Mapping[str, Any],
    key: str,
    default: tuple[str, ...] = (),
) -> tuple[Any, ...]:
    value = payload.get(key, default)
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise GIVValidationError(f"{key} must be a sequence")
    return tuple(value)


__all__ = [
    "DEFAULT_DENIED_COMMANDS",
    "DEFAULT_PROHIBITIONS",
    "GIV",
    "GIVValidationError",
    "HandoffTicket",
    "SCHEMA_VERSION",
]
