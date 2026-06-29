"""Static prompt keyword parser for deterministic capability profiling."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

CAPABILITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "auth_security": (
        "auth",
        "authentication",
        "authorization",
        "jwt",
        "oauth",
        "permission",
        "permissions",
        "rbac",
        "security",
        "session",
        "sessions",
        "sso",
    ),
    "backend": (
        "api",
        "backend",
        "controller",
        "database",
        "endpoint",
        "fastapi",
        "graphql",
        "postgres",
        "rest",
        "server",
        "service",
        "worker",
    ),
    "billing_payment": (
        "billing",
        "checkout",
        "invoice",
        "invoices",
        "payment",
        "payments",
        "price",
        "prices",
        "refund",
        "stripe",
        "subscription",
        "subscriptions",
    ),
    "destructive_operations": (
        "delete",
        "destroy",
        "drop",
        "force push",
        "git reset",
        "purge",
        "remove",
        "reset hard",
        "rm -rf",
        "truncate",
        "wipe",
    ),
    "docs": (
        "docs",
        "documentation",
        "guide",
        "readme",
        "reference",
        "runbook",
    ),
    "frontend": (
        "css",
        "dynamic web terminal",
        "frontend",
        "grid",
        "grok build",
        "html",
        "react",
        "sse",
        "sse streaming",
        "streaming",
        "tailwind",
        "terminal",
        "terminal bridge",
        "terminal ui",
        "ui",
        "ux",
        "vue",
        "web page",
        "web terminal",
        "website",
    ),
    "migrations": (
        "alembic",
        "backfill",
        "migration",
        "migrations",
        "schema",
    ),
    "tests": (
        "coverage",
        "e2e",
        "integration test",
        "pytest",
        "spec",
        "test",
        "tests",
        "unit test",
    ),
}

RECOMMENDED_PATHS: dict[str, tuple[str, ...]] = {
    "auth_security": ("aoc-cli/aoc_cli/", "tests/", "docs/"),
    "backend": ("aoc-cli/aoc_cli/", "aoc_supervisor/aoc_supervisor/", "tests/"),
    "billing_payment": ("aoc_supervisor/aoc_supervisor/billing.py", "tests/", "docs/"),
    "destructive_operations": ("tests/", "docs/"),
    "docs": ("README.md", "docs/"),
    "frontend": ("aoc-cli/aoc_cli/", "tests/"),
    "migrations": ("migrations/", "tests/", "docs/"),
    "tests": ("tests/",),
}

RISK_FLAGS: dict[str, tuple[str, ...]] = {
    "auth_security": ("security-sensitive changes",),
    "billing_payment": ("money movement or billing changes",),
    "destructive_operations": ("destructive operation requested",),
    "migrations": ("database schema or data migration",),
}

BASE_PROHIBITIONS = (
    "no network calls",
    "no secret exfiltration",
)

CAPABILITY_PROHIBITIONS: dict[str, tuple[str, ...]] = {
    "auth_security": (
        "no credential exposure",
        "no weakening authentication or authorization checks",
    ),
    "billing_payment": (
        "no live payment charges",
        "no production billing mutations without explicit approval",
    ),
    "destructive_operations": (
        "no destructive cleanup outside workspace",
        "no irreversible file or data deletion",
    ),
    "migrations": (
        "no production schema changes without explicit approval",
        "no destructive migrations without rollback plan",
    ),
}

DANGEROUS_PHRASES: dict[str, tuple[str, ...]] = {
    "rm -rf": ("no recursive force deletion",),
    "drop database": ("no database dropping",),
    "drop table": ("no table dropping",),
    "delete all": ("no bulk deletion",),
    "destroy all": ("no bulk destruction",),
    "format disk": ("no disk formatting",),
    "git reset --hard": ("no hard reset",),
    "force push": ("no force push",),
    "purge production": ("no production purge",),
    "truncate table": ("no table truncation",),
    "wipe production": ("no production wipe",),
}


@dataclass
class MoatProfile:
    """Deterministic static capability profile derived from a prompt."""

    capabilities: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    prohibitions: list[str] = field(default_factory=list)
    recommended_paths: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.capabilities = _normalize_items(self.capabilities)
        self.risk_flags = _normalize_items(self.risk_flags)
        self.prohibitions = _normalize_items(self.prohibitions)
        self.recommended_paths = _normalize_items(self.recommended_paths)

    def to_dict(self) -> dict[str, list[str]]:
        """Return a JSON-compatible deterministic payload."""
        return {
            "capabilities": list(self.capabilities),
            "risk_flags": list(self.risk_flags),
            "prohibitions": list(self.prohibitions),
            "recommended_paths": list(self.recommended_paths),
        }


def parse_prompt(prompt: str) -> MoatProfile:
    """Parse a natural language prompt using fixed keyword maps only."""
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")

    normalized_prompt = _normalize_prompt(prompt)
    capabilities: set[str] = set()
    risk_flags: set[str] = set()
    prohibitions: set[str] = set(BASE_PROHIBITIONS)
    recommended_paths: set[str] = set()

    for capability, keywords in CAPABILITY_KEYWORDS.items():
        if _contains_any(normalized_prompt, keywords):
            capabilities.add(capability)
            recommended_paths.update(RECOMMENDED_PATHS.get(capability, ()))
            risk_flags.update(RISK_FLAGS.get(capability, ()))
            prohibitions.update(CAPABILITY_PROHIBITIONS.get(capability, ()))

    for phrase, phrase_prohibitions in DANGEROUS_PHRASES.items():
        if _contains_phrase(normalized_prompt, phrase):
            capabilities.add("destructive_operations")
            risk_flags.update(RISK_FLAGS["destructive_operations"])
            recommended_paths.update(RECOMMENDED_PATHS["destructive_operations"])
            prohibitions.update(CAPABILITY_PROHIBITIONS["destructive_operations"])
            prohibitions.update(phrase_prohibitions)

    return MoatProfile(
        capabilities=list(capabilities),
        risk_flags=list(risk_flags),
        prohibitions=list(prohibitions),
        recommended_paths=list(recommended_paths),
    )


def _normalize_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", prompt.casefold()).strip()


def _contains_any(prompt: str, keywords: Iterable[str]) -> bool:
    return any(_contains_phrase(prompt, keyword) for keyword in keywords)


def _contains_phrase(prompt: str, phrase: str) -> bool:
    normalized = _normalize_prompt(phrase)
    if not normalized:
        return False
    pattern = rf"(?<![a-z0-9_]){re.escape(normalized)}(?![a-z0-9_])"
    return re.search(pattern, prompt) is not None


def _normalize_items(items: Iterable[str]) -> list[str]:
    return sorted({str(item).strip() for item in items if str(item).strip()})


__all__ = [
    "MoatProfile",
    "parse_prompt",
]
