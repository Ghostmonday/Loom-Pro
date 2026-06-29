"""Central Gaijinn CLI error types and rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GaijinnError(Exception):
    """Base class for expected user-facing CLI errors."""

    message: str
    cause: str | None = None
    fix_command: str | None = None


class StateError(GaijinnError):
    """Raised when persisted Gaijinn state is missing or invalid."""


class ValidationError(GaijinnError):
    """Raised when an artifact fails schema or content validation."""


class PrerequisiteError(GaijinnError):
    """Raised when a command is run before required artifacts exist."""


class SafetyError(GaijinnError):
    """Raised when a requested operation would violate isolation or safety."""


class GridSpawnError(GaijinnError):
    """Raised when Grok Build grid spawn prerequisites are missing or invalid."""


class SprintError(GaijinnError):
    """Raised when an atomic sprint cannot start or complete safely."""


class CollectError(GaijinnError):
    """Raised when worker collection prerequisites are missing or invalid."""


class MergeValidationError(GaijinnError):
    """Raised when a worker fails merge-pipeline validation gates."""


class MergeError(GaijinnError):
    """Raised when a git-level merge operation fails."""


class ConflictError(MergeError):
    """Raised when a merge conflict is detected during integration."""


def render_error(error: GaijinnError) -> str:
    lines = [f"Error: {error.message}"]
    if error.cause:
        lines.append(f"Cause: {error.cause}")
    if error.fix_command:
        lines.append(f"Fix: run `{error.fix_command}`")
    return "\n".join(lines)
