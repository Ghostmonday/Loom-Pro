"""Integration tests for production reasoning provider wiring at API startup."""

from __future__ import annotations

import pytest
from aoc_supervisor.adaptive_question_engine import get_default_engine
from aoc_supervisor.reasoning_provider import (
    DeterministicFakeReasoningProvider,
    HttpReasoningProvider,
    create_reasoning_provider,
    fake_reasoning_enabled,
)
from fastapi.testclient import TestClient


def test_create_reasoning_provider_uses_fake_only_when_flag_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAIJINN_FAKE_REASONING", raising=False)
    monkeypatch.setenv("GAIJINN_REASONING_PROVIDER", "http")
    monkeypatch.setenv("GAIJINN_REASONING_URL", "http://127.0.0.1:9/analyze")

    provider = create_reasoning_provider()
    assert isinstance(provider, HttpReasoningProvider)
    assert provider.provider_id == "http"
    assert not isinstance(provider, DeterministicFakeReasoningProvider)

    monkeypatch.setenv("GAIJINN_FAKE_REASONING", "1")
    fake = create_reasoning_provider()
    assert isinstance(fake, DeterministicFakeReasoningProvider)
    assert fake_reasoning_enabled()


def test_api_lifespan_wires_http_provider_without_fake_flag(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aoc_supervisor.api as api

    monkeypatch.delenv("GAIJINN_FAKE_REASONING", raising=False)
    monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
    monkeypatch.setenv("GAIJINN_REASONING_PROVIDER", "http")
    monkeypatch.setenv("GAIJINN_REASONING_URL", "http://127.0.0.1:9/analyze")
    monkeypatch.setattr(api, "ROOT_DIR", tmp_path)

    with TestClient(api.app) as _client:
        engine = get_default_engine()
        provider = engine.provider
        assert provider.provider_id == "http"
        assert not isinstance(provider, DeterministicFakeReasoningProvider)
