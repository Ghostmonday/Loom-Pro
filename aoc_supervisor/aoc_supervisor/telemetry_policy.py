"""Telemetry consent enforcement for Intent Forge sessions."""

from __future__ import annotations

from typing import Any

DEFAULT_CONSENT: dict[str, bool] = {
    "operational": True,
    "analytics": False,
    "training": False,
}


def normalize_consent(consent: dict[str, Any] | None) -> dict[str, bool]:
    """Resolve consent at session creation. Operational records are always enabled."""
    resolved = dict(DEFAULT_CONSENT)
    if isinstance(consent, dict):
        for key in DEFAULT_CONSENT:
            if key in consent:
                resolved[key] = bool(consent[key])
    resolved["operational"] = True
    return resolved


def analytics_allowed(state: dict[str, Any]) -> bool:
    consent = state.get("telemetry_consent", {})
    return bool(consent.get("analytics")) if isinstance(consent, dict) else False


def training_allowed(state: dict[str, Any]) -> bool:
    consent = state.get("telemetry_consent", {})
    return bool(consent.get("training")) if isinstance(consent, dict) else False


def build_aggregate_signals(state: dict[str, Any]) -> dict[str, Any]:
    """Aggregate product signals without raw user answers."""
    qa = [item for item in state.get("questions_and_answers", []) if isinstance(item, dict)]
    active = [item for item in qa if not item.get("superseded_by")]
    revisions = [item for item in qa if item.get("revises")]
    contradictions = [item for item in state.get("contradictions", []) if isinstance(item, dict)]
    return {
        "session_id": state.get("session_id"),
        "session_status": state.get("session_status"),
        "tier": state.get("tier"),
        "question_count": len(active),
        "revision_count": len(revisions),
        "contradiction_count": len(contradictions),
        "unresolved_contradiction_count": sum(1 for item in contradictions if not item.get("resolved")),
        "domain_confidence_delta": dict(state.get("confidence_by_domain", {})),
        "blueprint_version": state.get("blueprint_version"),
        "finalized": state.get("session_status") in {"FINALIZED", "HANDED_OFF"},
    }


def export_optional_telemetry(state: dict[str, Any]) -> dict[str, Any] | None:
    """Return optional telemetry payload only when consent allows collection."""
    if not analytics_allowed(state):
        return None
    payload = build_aggregate_signals(state)
    if training_allowed(state):
        payload["training_export_permitted"] = True
    return payload
