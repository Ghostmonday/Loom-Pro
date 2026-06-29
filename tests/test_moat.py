from __future__ import annotations

import pytest
from aoc_cli.moat import MoatProfile, parse_prompt


def test_parse_prompt_detects_requested_capability_areas() -> None:
    profile = parse_prompt(
        "Build a React frontend and FastAPI backend with JWT auth, Stripe billing, "
        "Postgres schema migrations, docs, and pytest coverage."
    )

    assert profile.capabilities == [
        "auth_security",
        "backend",
        "billing_payment",
        "docs",
        "frontend",
        "migrations",
        "tests",
    ]
    assert "security-sensitive changes" in profile.risk_flags
    assert "money movement or billing changes" in profile.risk_flags
    assert "database schema or data migration" in profile.risk_flags
    assert "aoc-cli/aoc_cli/" in profile.recommended_paths
    assert "aoc_supervisor/aoc_supervisor/" in profile.recommended_paths
    assert "docs/" in profile.recommended_paths
    assert "tests/" in profile.recommended_paths
    assert "no network calls" in profile.prohibitions
    assert "no live payment charges" in profile.prohibitions
    assert "no weakening authentication or authorization checks" in profile.prohibitions


def test_parse_prompt_is_deterministic() -> None:
    prompt = "Add tests, docs, and a backend API endpoint for auth."

    assert parse_prompt(prompt).to_dict() == parse_prompt(prompt).to_dict()


def test_dangerous_phrases_increase_prohibitions() -> None:
    regular_delete = parse_prompt("Remove an obsolete frontend component.")
    dangerous_delete = parse_prompt("Remove an obsolete frontend component, then rm -rf the old tree.")

    assert "destructive_operations" in regular_delete.capabilities
    assert "destructive_operations" in dangerous_delete.capabilities
    assert "no recursive force deletion" not in regular_delete.prohibitions
    assert "no recursive force deletion" in dangerous_delete.prohibitions
    assert len(dangerous_delete.prohibitions) > len(regular_delete.prohibitions)


def test_moat_profile_normalizes_fields() -> None:
    profile = MoatProfile(
        capabilities=["backend", " backend ", "frontend"],
        risk_flags=[" security-sensitive changes ", "security-sensitive changes"],
        prohibitions=["no network calls", ""],
        recommended_paths=["tests/", "aoc-cli/aoc_cli/", "tests/"],
    )

    assert profile.capabilities == ["backend", "frontend"]
    assert profile.risk_flags == ["security-sensitive changes"]
    assert profile.prohibitions == ["no network calls"]
    assert profile.recommended_paths == ["aoc-cli/aoc_cli/", "tests/"]


def test_parse_prompt_rejects_non_string_prompt() -> None:
    with pytest.raises(TypeError, match="prompt must be a string"):
        parse_prompt(None)  # type: ignore[arg-type]
