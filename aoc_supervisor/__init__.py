"""Top-level package shim for the AOC supervisor."""

from pathlib import Path

_nested_package_path = Path(__file__).with_name("aoc_supervisor")
if _nested_package_path.is_dir():
    __path__.append(str(_nested_package_path))

from .aoc_supervisor import ClusterOrchestrator, StructuralGravityViolation, validate_system_state  # noqa: E402

__all__ = [
    "ClusterOrchestrator",
    "StructuralGravityViolation",
    "validate_system_state",
]
