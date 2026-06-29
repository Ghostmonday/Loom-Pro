"""Voice submission contract tests for Perfect SPEC Interrogation."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

INTENT_MAP = Path(__file__).resolve().parents[1] / "ui" / "gaijinn-ui-intent-map.json"


def test_intent_map_declares_voice_invariants() -> None:
    intent_map = json.loads(INTENT_MAP.read_text(encoding="utf-8"))
    text = json.dumps(intent_map).lower()
    for token in ("microphone", "voice", "transcript", "push-to-talk"):
        assert token in text, f"UI intent map must declare voice invariant coverage for `{token}`"


class TestVoiceBackendSubmissionContract:
    """Backend must accept text plus provenance — never raw audio by default."""

    def test_answer_endpoint_accepts_voice_provenance_without_audio(self, tmp_path, monkeypatch) -> None:
        import aoc_supervisor.api as api
        from aoc_supervisor.intent_forge_service import IntentForgeService

        monkeypatch.setenv("GAIJINN_ALLOW_MULTI_API_WORKER", "1")
        monkeypatch.setattr(api, "ROOT_DIR", tmp_path)
        api._intent_forge_service = IntentForgeService(tmp_path)
        headers = {"X-User-Id": "voice-tester", "Content-Type": "application/json"}

        with TestClient(api.app) as client:
            created = client.post(
                "/api/v1/intent-forge/sessions",
                json={"prompt": "Build a secure API gateway", "tier": "paid"},
                headers=headers,
            ).json()
            qid = created["current_question"]["question_id"]
            res = client.post(
                f"/api/v1/intent-forge/sessions/{created['session_id']}/answers",
                json={
                    "question_id": qid,
                    "answer": "OAuth2 with scoped tokens for every endpoint.",
                    "input_provenance": {"source": "voice", "transcript_edited": True},
                    "idempotency_key": "voice-answer-001",
                    "expected_blueprint_version": created["blueprint_version"],
                },
                headers=headers,
            )
            assert res.status_code == 200, "DoD-12: voice-derived text must submit like typed answers"
            body = res.json()
            latest = body.get("questions_and_answers", [])[-1]
            assert latest.get("answer"), "Answer text must persist"
            assert "audio" not in json.dumps(body).lower() or body.get("voice_audio_retained") is False, (
                "DoD-12/13: raw audio must not be stored by default"
            )
