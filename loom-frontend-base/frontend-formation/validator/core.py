"""Shared diagnostics and validation result types."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Violation:
    code: str
    severity: str
    element_ref: str
    message: str
    rule_name: str
    source: str | None = None

    def format(self) -> str:
        lines = [
            f"{self.code} {self.severity}",
            f"Element: {self.element_ref}",
            f"Violation: {self.message}",
            f"Rule: {self.rule_name}",
        ]
        if self.source:
            lines.append(f"Source: {self.source}")
        return "\n".join(lines) + "\n"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    violations: list[Violation] = field(default_factory=list)
    checked_screens: int = 0

    @property
    def error_count(self) -> int:
        return sum(v.severity == "ERROR" for v in self.violations)

    @property
    def warning_count(self) -> int:
        return sum(v.severity == "WARN" for v in self.violations)

    @property
    def passed(self) -> bool:
        return self.error_count == 0

    def extend(self, violations: Iterable[Violation]) -> None:
        self.violations.extend(violations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checked_screens": self.checked_screens,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "violations": [v.to_dict() for v in self.violations],
        }
