"""Scaffold tests for loom_blueprint_synthesizer (LOOM-203 / C04)."""

from __future__ import annotations

import json

import pytest
from aoc_supervisor.loom_blueprint_synthesizer import (
    SynthesisRequest,
    SynthesisResult,
    synthesize_blueprint,
)
from fastapi.testclient import TestClient


class TestSynthesisRequest:
    """SynthesisRequest construction and field access."""

    def test_required_fields_only(self) -> None:
        req = SynthesisRequest(session_id="sid-1", intent="build-api")
        assert req.session_id == "sid-1"
        assert req.intent == "build-api"
        assert req.forge_session_id is None
        assert req.phases is None
        assert req.blueprint_graph is None
        assert req.confirmed_requirements is None
        assert req.executable_projection is None

    def test_all_fields(self) -> None:
        req = SynthesisRequest(
            session_id="sid-2",
            intent="deploy-infra",
            forge_session_id="forge-abc",
            phases=["vision_intake", "blueprint_synthesis"],
            blueprint_graph={"nodes": ["n1"]},
            confirmed_requirements=[{"id": "req-1"}],
            executable_projection={"workflows": []},
        )
        assert req.forge_session_id == "forge-abc"
        assert req.phases == ["vision_intake", "blueprint_synthesis"]
        assert req.blueprint_graph == {"nodes": ["n1"]}
        assert req.confirmed_requirements == [{"id": "req-1"}]
        assert req.executable_projection == {"workflows": []}


class TestSynthesisResult:
    """SynthesisResult construction and public dict conversion."""

    def test_defaults(self) -> None:
        res = SynthesisResult(session_id="sid-1")
        assert res.session_id == "sid-1"
        assert res.work_units == 1
        assert res.blueprint == {}
        assert res.warnings == []

    def test_to_public_dict(self) -> None:
        res = SynthesisResult(
            session_id="sid-1",
            work_units=3,
            blueprint={"tasks": ["t1", "t2"]},
            warnings=["low resources"],
        )
        d = res.to_public_dict()
        assert d == {
            "session_id": "sid-1",
            "work_units": 3,
            "blueprint": {"tasks": ["t1", "t2"]},
            "warnings": ["low resources"],
        }

    def test_warnings_are_copied_not_mutated(self) -> None:
        res = SynthesisResult(session_id="sid-1")
        # Ensure the default factory creates a new list each time
        res.warnings.append("test")
        assert res.warnings == ["test"]


def test_forge_projection_input(tmp_path) -> None:
    from aoc_supervisor.intent_blueprint_state import new_blueprint_state
    from aoc_supervisor.intent_forge_service import IntentForgeService

    forge_service = IntentForgeService(tmp_path)
    forge_state = new_blueprint_state(
        session_id="forge-123",
        user_id="alice",
        tier="free",
        original_prompt="Build a markdown note CLI",
        session_status="HANDED_OFF",
    )
    forge_state["executable_projection"] = {
        "projection_mode": "intent_forge",
        "work_units": [{"id": "WU-001"}, {"id": "WU-002"}],
    }
    forge_service.store.create(forge_state)

    request = SynthesisRequest(
        session_id="loom-123",
        intent="Build a markdown note CLI",
        forge_session_id=forge_state["session_id"],
    )
    result = synthesize_blueprint(request, forge_service=forge_service)

    assert request.executable_projection == forge_state["executable_projection"]
    assert request.executable_projection is not forge_state["executable_projection"]
    assert result.blueprint == forge_state["executable_projection"]
    assert result.work_units == 2


def test_gravity_fusion(tmp_path) -> None:
    from aoc_supervisor.intent_blueprint_state import new_blueprint_state
    from aoc_supervisor.intent_forge_service import IntentForgeService

    forge_service = IntentForgeService(tmp_path)
    forge_state = new_blueprint_state(
        session_id="forge-gravity",
        user_id="alice",
        tier="paid",
        original_prompt="Build a local notes service",
        session_status="HANDED_OFF",
    )
    forge_state["executable_projection"] = {
        "schema_version": 1,
        "project_goal": "Build a local notes service",
        "projection_mode": "intent_forge",
        "work_units": [
            {
                "id": "WU-001",
                "allowed_paths": ["src/storage/"],
                "depends_on": [],
                "estimated_risk": "medium",
            },
            {
                "id": "WU-002",
                "allowed_paths": ["src/api/"],
                "depends_on": ["WU-001"],
                "estimated_risk": "high",
            },
        ],
        "dependencies": {"WU-001": [], "WU-002": ["WU-001"]},
    }
    forge_service.store.create(forge_state)

    result = synthesize_blueprint(
        SynthesisRequest(
            session_id="loom-gravity",
            intent="Build a local notes service",
            forge_session_id="forge-gravity",
        ),
        forge_service=forge_service,
    )

    assert result.blueprint["projection_mode"] == "loom_synthesis"
    assert result.blueprint["curvature_metrics"]["gravity_meta"]["nodes"]
    assert "src/storage/->src/api/" in result.blueprint["curvature_metrics"]["curvature_meta"]["edges"]
    assert result.work_units == len(result.blueprint["work_units"])
    assert result.work_units >= 1


def test_min_dark_bridges(tmp_path) -> None:
    from aoc_supervisor.intent_blueprint_state import new_blueprint_state
    from aoc_supervisor.intent_forge_service import IntentForgeService

    forge_service = IntentForgeService(tmp_path)
    forge_state = new_blueprint_state(
        session_id="forge-dark-bridges",
        user_id="alice",
        tier="paid",
        original_prompt="Separate a low-risk router from high-risk deployment",
        session_status="HANDED_OFF",
    )
    forge_state["executable_projection"] = {
        "schema_version": 1,
        "project_goal": forge_state["original_prompt"],
        "work_units": [
            {
                "id": "WU-001",
                "allowed_paths": ["src/router.py"],
                "depends_on": [],
                "estimated_risk": "low",
            },
            {
                "id": "WU-002",
                "allowed_paths": ["ops/deploy.py"],
                "depends_on": ["WU-001"],
                "estimated_risk": "high",
            },
        ],
        "dependencies": {"WU-001": [], "WU-002": ["WU-001"]},
    }
    forge_service.store.create(forge_state)
    receipt = {"subphases_completed": ["blueprint_freeze"], "dark_bridge_count": 1}

    result = synthesize_blueprint(
        SynthesisRequest(
            session_id="loom-dark-bridges",
            intent=forge_state["original_prompt"],
            forge_session_id=forge_state["session_id"],
            teleology_receipt=receipt,
        ),
        forge_service=forge_service,
    )

    assert result.dark_bridge_count == 0
    assert result.blueprint["dark_bridge_count"] <= result.blueprint["graph_only_dark_bridge_count"]
    assert result.blueprint["teleology_receipt"] == receipt
    persisted = json.loads((tmp_path / ".gaijinn" / "blueprint.json").read_text(encoding="utf-8"))
    assert persisted == result.blueprint


def test_synthesize_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    import aoc_supervisor.api as api

    captured: list[SynthesisRequest] = []
    forge_state = {
        "session_id": "forge-123",
        "user_id": "alice",
        "session_status": "HANDED_OFF",
        "original_prompt": "Build a markdown note CLI",
        "blueprint_graph": {"nodes": [{"id": "notes"}], "edges": []},
        "confirmed_requirements": [{"id": "req-1", "text": "Export markdown"}],
        "executable_projection": {"work_units": [{"id": "WU-001"}]},
    }
    receipt = {"subphases_completed": ["blueprint_freeze"]}

    def fake_get_session(session_id: str) -> dict:
        assert session_id == "forge-123"
        return forge_state

    def fake_synthesize(request: SynthesisRequest) -> SynthesisResult:
        captured.append(request)
        return SynthesisResult(
            session_id=request.session_id,
            work_units=1,
            blueprint={"work_units": [{"id": "WU-001"}]},
        )

    monkeypatch.setenv("GAIJINN_ALLOW_INSECURE_LOCAL", "1")
    monkeypatch.setattr(api._intent_forge_service, "get_session", fake_get_session)
    monkeypatch.setattr(api, "synthesize_blueprint", fake_synthesize)

    client = TestClient(api.app)
    response = client.post(
        "/api/v1/loom/blueprint/synthesize",
        json={
            "intent_forge_session_id": "forge-123",
            "teleology_receipt": receipt,
        },
        headers={"X-User-Id": "alice"},
    )

    assert response.status_code == 200
    assert response.json()["work_units"] == 1
    assert len(captured) == 1
    synthesis_request = captured[0]
    assert synthesis_request.forge_session_id == "forge-123"
    assert synthesis_request.executable_projection == forge_state["executable_projection"]
    assert getattr(synthesis_request, "teleology_receipt") == receipt
