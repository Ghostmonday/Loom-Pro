"""Intent Forge executable projection tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aoc_supervisor.blueprint_compiler import compile_executable_projection
from aoc_supervisor.intent_blueprint_state import (
    REQUIRED_DOMAINS,
    bump_blueprint_version,
    new_blueprint_state,
    new_element_id,
    new_question_id,
)
from aoc_supervisor.intent_forge_service import IntentForgeService
from aoc_supervisor.orchestrate_session import OrchestrateSessionStore
from aoc_supervisor.workstream_planner import project_executable_blueprint
from fastapi.testclient import TestClient

PROMPT = "Build a secure API gateway with audit logging"


def _qa_state(*, prompt: str, answers: list[tuple[str, str]]) -> dict:
    state = new_blueprint_state(
        session_id="sess-projection",
        user_id="alice",
        tier="paid",
        original_prompt=prompt,
        session_status="VALIDATING",
    )
    for domain, answer in answers:
        question_id = new_question_id()
        state.setdefault("questions_and_answers", []).append(
            {
                "question_id": question_id,
                "text": f"Question for {domain}",
                "answer": answer,
                "domain": domain,
            }
        )
        state.setdefault("confirmed_requirements", []).append(
            {
                "id": new_element_id("REQ"),
                "text": answer,
                "source_question_id": question_id,
                "confidence": 1.0,
                "domain": domain,
            }
        )
        coverage = state.setdefault("domain_coverage", {})
        if isinstance(coverage, dict):
            coverage.setdefault(domain, {"addressed": True, "na": False})
            coverage[domain]["addressed"] = True
    return state


def test_no_qa_falls_back_to_keyword_projection_mode() -> None:
    blueprint = project_executable_blueprint(intent=PROMPT)
    assert blueprint["projection_mode"] == "keyword"
    assert blueprint["blueprint_mode"] == "intent"
    assert blueprint["work_units"]


def test_qa_projection_mode_is_intent_forge() -> None:
    state = _qa_state(
        prompt=PROMPT,
        answers=[("functional_requirements", "Expose REST endpoints with OpenAPI docs.")],
    )
    blueprint = compile_executable_projection(state)
    assert blueprint["projection_mode"] == "intent_forge"
    assert blueprint["blueprint_mode"] == "intent"
    assert blueprint["schema_version"] == 1
    assert blueprint["project_goal"] == PROMPT


def test_same_prompt_different_answers_yield_different_projections() -> None:
    oauth_state = _qa_state(
        prompt=PROMPT,
        answers=[
            ("authz", "OAuth2 with role-based scopes for every endpoint."),
            ("observability", "Emit structured audit logs for every authorization decision."),
        ],
    )
    api_key_state = _qa_state(
        prompt=PROMPT,
        answers=[
            ("authz", "API keys only; no OAuth or social login."),
            ("observability", "Ship Prometheus metrics only; no audit trail."),
        ],
    )
    oauth_projection = compile_executable_projection(oauth_state)
    api_key_projection = compile_executable_projection(api_key_state)

    assert oauth_projection != api_key_projection
    oauth_titles = set(oauth_projection["work_stream_titles"])
    api_key_titles = set(api_key_projection["work_stream_titles"])
    assert oauth_titles != api_key_titles or oauth_projection["work_units"] != api_key_projection["work_units"]
    oauth_descriptions = " ".join(unit["description"] for unit in oauth_projection["work_units"])
    api_key_descriptions = " ".join(unit["description"] for unit in api_key_projection["work_units"])
    assert "OAuth2" in oauth_descriptions
    assert "API keys" in api_key_descriptions


def test_acceptance_criteria_shape_acceptance_checks() -> None:
    state = _qa_state(
        prompt=PROMPT,
        answers=[("testing_acceptance", "All endpoints return typed error envelopes.")],
    )
    state["acceptance_criteria"] = [
        {"text": "Every endpoint has contract tests."},
        {"text": "Audit events are queryable for 30 days."},
    ]
    blueprint = compile_executable_projection(state)
    checks = blueprint["work_units"][0]["acceptance_checks"]
    assert "pytest" in checks
    assert "Every endpoint has contract tests." in checks
    assert "Audit events are queryable for 30 days." in checks


def test_projection_blueprint_is_valid_for_orchestrate_prepare(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = OrchestrateSessionStore(tmp_path)
    state = _qa_state(
        prompt=PROMPT,
        answers=[("functional_requirements", "Support REST and gRPC on the same port.")],
    )
    executable = compile_executable_projection(state)

    def _noop_gaijinn(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_gaijinn", _noop_gaijinn)
    monkeypatch.setattr("aoc_supervisor.orchestrate_session._seed_session_project", lambda *_a, **_k: None)

    snapshot = store.prepare(
        PROMPT,
        executable_blueprint=executable,
        orchestrate_session_id="forge-handoff-001",
    )
    blueprint_path = snapshot.project_root / ".gaijinn" / "blueprint.json"
    assert blueprint_path.exists()
    persisted = json.loads(blueprint_path.read_text(encoding="utf-8"))
    assert persisted["projection_mode"] == "intent_forge"
    assert persisted["blueprint_mode"] == "intent"
    assert snapshot.work_units == len(executable["work_units"])


@pytest.fixture
def forge_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import aoc_supervisor.api as api

    monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
    monkeypatch.setenv("GAIJINN_ALLOW_INSECURE_LOCAL", "1")
    monkeypatch.setattr(api, "ROOT_DIR", tmp_path)
    api._intent_forge_service = IntentForgeService(tmp_path)
    with TestClient(api.app) as client:
        yield client, api._intent_forge_service


def _headers() -> dict[str, str]:
    return {"X-User-Id": "alice", "Content-Type": "application/json"}


def _handoff_free(client, session: dict) -> dict:
    version = session["blueprint_version"]
    confirmed = client.post(
        f"/api/v1/intent-forge/sessions/{session['session_id']}/handoff",
        json={
            "action": "confirm",
            "confirmation": "Proceed",
            "idempotency_key": f"handoff-confirm-{version}",
            "expected_blueprint_version": version,
        },
        headers=_headers(),
    )
    assert confirmed.status_code == 200
    version = confirmed.json()["blueprint_version"]
    accepted = client.post(
        f"/api/v1/intent-forge/sessions/{session['session_id']}/handoff",
        json={
            "action": "accept",
            "idempotency_key": f"handoff-accept-{version}",
            "expected_blueprint_version": version,
        },
        headers=_headers(),
    )
    assert accepted.status_code == 200
    return accepted.json()


def test_prepare_with_intent_forge_session_uses_projection_blueprint(forge_env, tmp_path: Path, monkeypatch) -> None:
    client, _service = forge_env
    created = client.post(
        "/api/v1/intent-forge/sessions",
        json={"prompt": "Build a markdown note CLI", "tier": "free"},
        headers=_headers(),
    ).json()
    handed = _handoff_free(client, created)
    sid = handed["session_id"]
    executable = handed["executable_projection"]
    assert isinstance(executable, dict)
    assert executable.get("projection_mode") == "keyword"

    def _noop_gaijinn(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_gaijinn", _noop_gaijinn)
    monkeypatch.setattr("aoc_supervisor.orchestrate_session._seed_session_project", lambda *_a, **_k: None)

    prepare = client.post(
        "/api/v1/orchestrate/prepare",
        json={"intent": created["original_prompt"], "intent_forge_session_id": sid},
        headers=_headers(),
    )
    assert prepare.status_code == 200
    payload = prepare.json()
    assert payload["session_id"] == sid
    assert payload["work_units"] == len(executable["work_units"])
    assert payload.get("executable_projection") is None


def test_confirm_handoff_compiles_intent_forge_projection(tmp_path: Path) -> None:
    service = IntentForgeService(tmp_path)
    state = _qa_state(
        prompt=PROMPT,
        answers=[
            ("authz", "OAuth2 with role-based scopes for every endpoint."),
            ("observability", "Emit structured audit logs for every authorization decision."),
        ],
    )
    state["user_id"] = "alice"
    state["session_status"] = "FINAL_CONFIRMATION"
    coverage = state.setdefault("domain_coverage", {})
    confidence = state.setdefault("confidence_by_domain", {})
    if isinstance(coverage, dict) and isinstance(confidence, dict):
        for domain in REQUIRED_DOMAINS:
            coverage.setdefault(domain, {"addressed": True, "na": False})
            coverage[domain]["addressed"] = True
            confidence[domain] = 1.0
    bump_blueprint_version(state)
    service.store.create(state)

    confirmed = service.confirm_handoff(
        state["session_id"],
        idempotency_key="handoff-projection-confirm",
        expected_blueprint_version=state["blueprint_version"],
        confirmation="Proceed",
    )
    projection = confirmed["executable_projection"]
    assert projection["projection_mode"] == "intent_forge"
    descriptions = " ".join(unit["description"] for unit in projection["work_units"])
    assert "OAuth2" in descriptions

    accepted = service.accept_handoff(
        state["session_id"],
        idempotency_key="handoff-projection-accept",
        expected_blueprint_version=confirmed["blueprint_version"],
    )
    assert accepted["session_status"] == "HANDED_OFF"
    assert accepted["executable_projection"]["projection_mode"] == "intent_forge"
