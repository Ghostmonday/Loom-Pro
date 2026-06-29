"""Algorithm wiring traceability for ENG-101..104 (GAIJINN-ENG-105)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aoc_supervisor.adaptive_question_engine import get_default_engine, set_default_provider
from aoc_supervisor.blueprint_compiler import compile_executable_projection
from aoc_supervisor.intent_blueprint_state import (
    bump_blueprint_version,
    new_element_id,
    new_question_id,
)
from aoc_supervisor.orchestrate_session import OrchestrateSessionStore
from aoc_supervisor.reasoning_provider import (
    DeterministicFakeReasoningProvider,
    HttpReasoningProvider,
    create_reasoning_provider,
)
from aoc_supervisor.workstream_planner import project_executable_blueprint

REPO_ROOT = Path(__file__).resolve().parents[1]
UI_DIR = REPO_ROOT / "ui"

DELETED_IMPL_MARKERS = (
    "ui/views/",
    "gaijinn-terminal.html",
    "intent-forge-api-adapter.js",
    "intent-forge-voice.js",
)

REQUIRED_ORCHESTRATE_BINDINGS = (
    "orchestrate.prepare",
    "orchestrate.swarm",
    "orchestrate.advance_phase",
    "deploy.sprint",
)

BINDING_KEYS = frozenset({"module", "entrypoint", "mode"})
VALID_MODES = frozenset({"real", "keyword", "mock", "fake"})

PKM_INTENT = (
    "Build a local-first personal knowledge manager for Linux that indexes PDFs, "
    "Markdown files, and audio transcripts, supports semantic search, and exposes "
    "a desktop UI. Must be offline-only and privacy-preserving."
)

PROMPT = "Build a secure API gateway with audit logging"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_binding(action_id: str, binding: dict) -> None:
    missing = BINDING_KEYS - binding.keys()
    assert not missing, f"{action_id} algorithm_binding missing {sorted(missing)}"
    assert binding["mode"] in VALID_MODES, f"{action_id} has invalid mode {binding['mode']!r}"


def test_ui_json_has_no_deleted_implementation_refs() -> None:
    for path in UI_DIR.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        for marker in DELETED_IMPL_MARKERS:
            assert marker not in text, f"{path.name} still references deleted implementation {marker!r}"


def test_gaijinn_intent_map_required_actions_have_algorithm_binding() -> None:
    catalog = _load_json(UI_DIR / "gaijinn-ui-intent-map.json")
    actions = catalog["actions"]
    for action_id in REQUIRED_ORCHESTRATE_BINDINGS:
        assert action_id in actions, f"missing action {action_id}"
        _assert_binding(action_id, actions[action_id]["algorithm_binding"])


def test_intent_forge_actions_have_algorithm_binding() -> None:
    catalog = _load_json(UI_DIR / "gaijinn-ui-intent-map.json")
    forge_actions = catalog["intent_forge"]["actions"]
    assert forge_actions, "intent_forge.actions must not be empty"
    for action_id, spec in forge_actions.items():
        assert "algorithm_binding" in spec, f"intent_forge.{action_id} missing algorithm_binding"
        _assert_binding(f"intent_forge.{action_id}", spec["algorithm_binding"])


def test_ai_blueprint_layers_reflect_eng_remediation() -> None:
    catalog = _load_json(UI_DIR / "gaijinn-ui-intent-map.json")
    layers = catalog["_ai_blueprint"]["layers"]
    assert layers["cli_graph_planner"]["status"] == "shipped"
    assert layers["intent_planner"]["status"] == "fallback"
    assert layers["intent_forge_projection"]["ticket"] == "ENG-101"
    assert layers["adaptive_interrogation"]["ticket"] == "ENG-102"
    assert layers["orchestration"]["status"] == "shipped"
    assert layers["orchestration"]["ticket"] == "ENG-104"
    assert layers["terminal_ui"]["status"] == "contract_only"
    assert layers["terminal_ui"]["module"] == "sandbox_frontend/"


def test_eng101_projection_uses_qa_evidence() -> None:
    def _qa_state(*, answers: list[tuple[str, str]]) -> dict:
        state = {
            "session_id": "sess-wiring-101",
            "original_prompt": PROMPT,
            "questions_and_answers": [],
            "confirmed_requirements": [],
            "domain_coverage": {},
        }
        for domain, answer in answers:
            question_id = new_question_id()
            state["questions_and_answers"].append(
                {
                    "question_id": question_id,
                    "text": f"Question for {domain}",
                    "answer": answer,
                    "domain": domain,
                }
            )
            state["confirmed_requirements"].append(
                {
                    "id": new_element_id("REQ"),
                    "text": answer,
                    "source_question_id": question_id,
                    "confidence": 1.0,
                    "domain": domain,
                }
            )
            state["domain_coverage"].setdefault(domain, {"addressed": True, "na": False})
        return state

    oauth_state = _qa_state(
        answers=[
            ("authz", "OAuth2 with role-based scopes for every endpoint."),
            ("observability", "Emit structured audit logs for every authorization decision."),
        ]
    )
    api_key_state = _qa_state(
        answers=[
            ("authz", "API keys only; no OAuth or social login."),
            ("observability", "Ship Prometheus metrics only; no audit trail."),
        ]
    )

    oauth_projection = compile_executable_projection(oauth_state)
    api_key_projection = compile_executable_projection(api_key_state)

    assert oauth_projection["projection_mode"] == "intent_forge"
    assert api_key_projection["projection_mode"] == "intent_forge"
    assert oauth_projection != api_key_projection

    empty = project_executable_blueprint(intent=PROMPT)
    assert empty["projection_mode"] == "keyword"


def test_eng102_production_provider_not_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAIJINN_FAKE_REASONING", raising=False)
    monkeypatch.setenv("GAIJINN_REASONING_PROVIDER", "http")
    monkeypatch.setenv("GAIJINN_REASONING_URL", "http://127.0.0.1:9/analyze")

    provider = create_reasoning_provider()
    assert isinstance(provider, HttpReasoningProvider)
    assert not isinstance(provider, DeterministicFakeReasoningProvider)


def test_eng102_startup_wiring_selects_http_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mirror api._app_lifespan: set_default_provider(create_reasoning_provider())."""
    monkeypatch.delenv("GAIJINN_FAKE_REASONING", raising=False)
    monkeypatch.setenv("GAIJINN_REASONING_PROVIDER", "http")
    monkeypatch.setenv("GAIJINN_REASONING_URL", "http://127.0.0.1:9/analyze")

    set_default_provider(create_reasoning_provider())
    provider = get_default_engine().provider
    assert provider.provider_id == "http"
    assert not isinstance(provider, DeterministicFakeReasoningProvider)


def test_eng103_greenfield_default_calls_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = OrchestrateSessionStore(tmp_path)
    calls: list[tuple[str, ...]] = []

    def fake_run(_root: Path, *args: str, **_kwargs) -> None:
        calls.append(args)

    monkeypatch.delenv("GAIJINN_KEYWORD_GREENFIELD", raising=False)
    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_gaijinn", fake_run)

    snapshot = store.prepare(PKM_INTENT)
    assert snapshot.blueprint_mode == "graph"
    assert ("plan", "--workers", "4") in calls
    assert not any(call and call[0] == "intent_blueprint" for call in calls)


def test_eng103_keyword_fallback_is_env_gated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = OrchestrateSessionStore(tmp_path)
    calls: list[tuple[str, ...]] = []

    def fake_run(_root: Path, *args: str, **_kwargs) -> None:
        calls.append(args)

    monkeypatch.setenv("GAIJINN_KEYWORD_GREENFIELD", "1")
    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_gaijinn", fake_run)

    snapshot = store.prepare(PKM_INTENT)
    assert snapshot.blueprint_mode == "intent"
    assert ("plan", "--workers", "4") not in calls


def test_eng104_advance_phase_invokes_blueprint_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = OrchestrateSessionStore(tmp_path)
    session_id = "aabbccddeeff"
    session_root = store.sessions_dir / session_id
    gaijinn_dir = session_root / ".gaijinn"
    gaijinn_dir.mkdir(parents=True, exist_ok=True)
    (session_root / "src").mkdir(parents=True, exist_ok=True)
    (gaijinn_dir / "intent.txt").write_text("Build a REST API backend service\n", encoding="utf-8")
    phase_one_titles = ("Service API layer", "Core project scaffold")
    phase_two_titles = ("Desktop UI", "Editor UI and theming")
    (gaijinn_dir / "blueprint.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_goal": "Build a REST API backend service",
                "blueprint_mode": "intent",
                "work_stream_titles": list(phase_one_titles),
                "work_units": [
                    {"id": f"WU-{index:03d}", "title": title, "allowed_paths": [f"src/{index}/"]}
                    for index, title in enumerate(phase_one_titles, start=1)
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    meta = {
        "session_id": session_id,
        "owner_user_id": "terminal-user",
        "intent": "Build a REST API backend service",
        "phase": "awaiting_next_phase",
        "phases": ["backend", "frontend"],
        "current_phase": "backend",
        "pipeline_plan": {
            "phases": ["backend", "frontend"],
            "current_index": 0,
            "current_phase": "backend",
            "completed_phases": ["backend"],
        },
        "loaded_context": {},
        "blueprint_mode": "intent",
        "work_stream_titles": list(phase_one_titles),
        "swarm_rationale": "demo",
        "workers_ready": 2,
        "selected_swarm": 2,
    }
    (gaijinn_dir / "session.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    store._active[session_id] = session_root

    pipeline_calls: list[str] = []

    def fake_pipeline(
        project_root: Path,
        intent: str,
        *,
        command_timeout: int | None = None,
        use_intent_blueprint: bool = False,
        loaded_context: dict | None = None,
    ) -> tuple[int, int, tuple[str, ...], str, tuple[str, ...]]:
        pipeline_calls.append(intent)
        blueprint = {
            "schema_version": 1,
            "project_goal": intent,
            "blueprint_mode": "intent",
            "loaded_context": loaded_context,
            "work_stream_titles": list(phase_two_titles),
            "work_units": [
                {"id": f"WU-{index:03d}", "title": title, "allowed_paths": [f"src/ui/{index}/"]}
                for index, title in enumerate(phase_two_titles, start=1)
            ],
        }
        (project_root / ".gaijinn" / "blueprint.json").write_text(
            json.dumps(blueprint, indent=2) + "\n",
            encoding="utf-8",
        )
        return len(phase_two_titles), 0, phase_two_titles, "intent", phase_two_titles

    monkeypatch.setattr("aoc_supervisor.orchestrate_session._run_blueprint_pipeline", fake_pipeline)

    advanced = store.advance_phase(session_id)
    public = advanced.to_public_dict()

    assert pipeline_calls, "advance_phase must invoke _run_blueprint_pipeline"
    assert "frontend UI integrating with backend context" in pipeline_calls[0]
    assert advanced.work_stream_titles == phase_two_titles
    assert phase_two_titles != phase_one_titles
    assert "blueprint stub" not in (public.get("message") or "").lower()
    assert "blueprint ready" in (public.get("message") or "").lower()


def test_eng101_handoff_projection_differs_by_answers(tmp_path: Path) -> None:
    from aoc_supervisor.intent_blueprint_state import REQUIRED_DOMAINS
    from aoc_supervisor.intent_forge_service import IntentForgeService

    service = IntentForgeService(tmp_path)

    def _state(answers: list[tuple[str, str]]) -> dict:
        state = {
            "session_id": "handoff-wiring",
            "user_id": "alice",
            "tier": "paid",
            "original_prompt": PROMPT,
            "session_status": "FINAL_CONFIRMATION",
            "questions_and_answers": [],
            "confirmed_requirements": [],
            "domain_coverage": {},
            "confidence_by_domain": {},
        }
        for domain, answer in answers:
            question_id = new_question_id()
            state["questions_and_answers"].append(
                {"question_id": question_id, "text": f"Q {domain}", "answer": answer, "domain": domain}
            )
            state["confirmed_requirements"].append(
                {
                    "id": new_element_id("REQ"),
                    "text": answer,
                    "source_question_id": question_id,
                    "confidence": 1.0,
                    "domain": domain,
                }
            )
            state["domain_coverage"][domain] = {"addressed": True, "na": False}
            state["confidence_by_domain"][domain] = 1.0
        for domain in REQUIRED_DOMAINS:
            state["domain_coverage"].setdefault(domain, {"addressed": True, "na": False})
            state["confidence_by_domain"].setdefault(domain, 1.0)
        bump_blueprint_version(state)
        return state

    oauth = _state(
        [
            ("authz", "OAuth2 with role-based scopes for every endpoint."),
            ("observability", "Emit structured audit logs for every authorization decision."),
        ]
    )
    api_key = _state(
        [
            ("authz", "API keys only; no OAuth or social login."),
            ("observability", "Ship Prometheus metrics only; no audit trail."),
        ]
    )
    service.store.create(oauth)
    service.store.create({**api_key, "session_id": "handoff-wiring-b"})

    oauth_confirmed = service.confirm_handoff(
        "handoff-wiring",
        idempotency_key="wiring-oauth",
        expected_blueprint_version=oauth["blueprint_version"],
        confirmation="Proceed",
    )
    api_confirmed = service.confirm_handoff(
        "handoff-wiring-b",
        idempotency_key="wiring-api",
        expected_blueprint_version=api_key["blueprint_version"],
        confirmation="Proceed",
    )

    assert oauth_confirmed["executable_projection"]["projection_mode"] == "intent_forge"
    assert api_confirmed["executable_projection"]["projection_mode"] == "intent_forge"
    assert oauth_confirmed["executable_projection"] != api_confirmed["executable_projection"]
