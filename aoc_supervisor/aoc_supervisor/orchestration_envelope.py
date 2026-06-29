"""Canonical orchestration event envelope for deliberation and session telemetry."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EVENT_SCHEMA_PATH = REPO_ROOT / "ui" / "orchestration-event.schema.json"

TELEOLOGY_SUBPHASES = {
    "intent_parse",
    "graph_ingest",
    "curvature_compute",
    "bridge_detect",
    "weld_plan",
    "partition",
    "blueprint_freeze",
}


@lru_cache(maxsize=1)
def load_event_schema() -> dict[str, Any]:
    return json.loads(EVENT_SCHEMA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _validator():
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return None

    return Draft202012Validator(load_event_schema())


def schema_validation_available() -> bool:
    return _validator() is not None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_event_id() -> str:
    return f"evt_{uuid.uuid4().hex}"


def _edge_classification(kappa: float) -> str:
    if kappa < -0.3:
        return "dark_bridge"
    if kappa < 0:
        return "shadow_bridge"
    if kappa > 0:
        return "positive"
    return "flat"


def _prune_none(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def _normalize_risk(value: Any) -> str:
    cleaned = str(value or "low").lower()
    if cleaned in {"low", "medium", "high"}:
        return cleaned
    return "low"


def _normalize_node(data: dict[str, Any]) -> dict[str, Any]:
    node_id = str(data.get("node_id") or data.get("id") or "")
    return _prune_none(
        {
            "node_id": node_id,
            "label": str(data.get("label") or Path(node_id).name or node_id),
            "path": node_id or None,
            "node_kind": str(data.get("node_kind") or "file"),
            "gravity": float(data.get("gravity", 0.3) or 0.3),
            "local_size": data.get("local_size"),
            "risk": data.get("risk", "low"),
            "status": str(data.get("status") or ("rejected" if data.get("rejected") else "discovered")),
            "work_unit_id": data.get("work_unit_id"),
            "worker_id": data.get("worker_id"),
        }
    )


def _normalize_edge(data: dict[str, Any], *, bridge: bool = False) -> dict[str, Any]:
    source = str(data.get("source", ""))
    target = str(data.get("target", ""))
    kappa = float(data.get("kappa", 0.0) or 0.0)
    edge_id = str(data.get("edge_id") or f"{source}->{target}")
    classification = data.get("classification")
    if classification is None:
        classification = _edge_classification(kappa) if bridge or kappa < 0 else _edge_classification(kappa)
    return _prune_none(
        {
            "edge_id": edge_id,
            "source": source,
            "target": target,
            "kappa": kappa,
            "geometric_curvature": data.get("geometric_curvature"),
            "wasserstein_1": data.get("wasserstein_1"),
            "classification": classification,
            "risk_jump": bool(data.get("risk_jump", kappa < -0.3)),
            "source_distribution": data.get("source_distribution"),
            "target_distribution": data.get("target_distribution"),
        }
    )


def _normalize_work_unit(data: dict[str, Any]) -> dict[str, Any]:
    work_unit_id = str(data.get("work_unit_id") or data.get("id") or "")
    allowed_paths = data.get("allowed_paths")
    if not isinstance(allowed_paths, list):
        files = data.get("files")
        allowed_path_count = int(files) if isinstance(files, int) else 1
    else:
        allowed_path_count = len(allowed_paths)
    return _prune_none(
        {
            "work_unit_id": work_unit_id,
            "title": str(data.get("title") or work_unit_id),
            "description": data.get("description"),
            "risk": _normalize_risk(data.get("risk") or data.get("estimated_risk")),
            "domain": data.get("domain", "code"),
            "allowed_path_count": max(allowed_path_count, 1),
            "allowed_paths": allowed_paths if isinstance(allowed_paths, list) else None,
            "denied_paths": data.get("denied_paths"),
            "acceptance_checks": data.get("acceptance_checks") or [],
            "depends_on": data.get("depends_on") or [],
            "strategy": data.get("strategy"),
            "state": "proposed" if data.get("preview") else str(data.get("state") or "approved"),
        }
    )


def map_legacy_deliberation_event(
    legacy_type: str,
    data: dict[str, Any],
    *,
    phase: str = "blueprinting",
    subphase: str | None = None,
) -> tuple[str, str, str | None, str, dict[str, Any]]:
    """Map legacy SSE deliberation events to canonical contract fields."""
    payload = dict(data)
    active_subphase = subphase or payload.get("phase") or payload.get("subphase")
    if active_subphase not in TELEOLOGY_SUBPHASES:
        active_subphase = None

    if legacy_type == "deliberation_start":
        return (
            "phase.begin",
            "blueprinting",
            active_subphase or "intent_parse",
            "guided",
            {
                "intent_summary": payload.get("intent"),
                "mode": payload.get("mode", "architectural_teleology"),
                "layer1_timeout_s": payload.get("layer1_timeout_s"),
                "provisional_session": True,
            },
        )
    if legacy_type in {"deliberation_heartbeat", "step_progress"}:
        return (
            "phase.progress",
            phase,
            active_subphase or (payload.get("step") and str(payload.get("step")).split("_")[0]),
            "guided",
            payload,
        )
    if legacy_type == "phase_begin":
        return ("phase.begin", phase, active_subphase, "guided", payload)
    if legacy_type == "phase_complete":
        return ("phase.complete", phase, active_subphase, "guided", payload)
    if legacy_type == "node_added":
        return ("topology.node.upsert", phase, active_subphase or "graph_ingest", "builder", _normalize_node(payload))
    if legacy_type == "edge_curvature":
        return (
            "topology.edge.curvature",
            phase,
            active_subphase or "curvature_compute",
            "builder",
            _normalize_edge(payload),
        )
    if legacy_type == "dark_bridge_detected":
        return (
            "topology.bridge.detected",
            phase,
            active_subphase or "bridge_detect",
            "builder",
            _normalize_edge(payload, bridge=True),
        )
    if legacy_type == "weld_start":
        return (
            "topology.weld.created",
            phase,
            active_subphase or "weld_plan",
            "builder",
            {
                "weld_id": payload.get("block_id", "geometry-weld"),
                "work_unit_id": payload.get("work_unit_id"),
                "node_ids": list(payload.get("cluster") or []),
                "state": "proposed",
                "mode": payload.get("mode", "atomic_weld"),
            },
        )
    if legacy_type == "weld_complete":
        return (
            "topology.weld.created",
            phase,
            active_subphase or "weld_plan",
            "builder",
            {
                "weld_id": payload.get("block_id", "geometry-weld"),
                "work_unit_id": payload.get("work_unit_id"),
                "node_ids": list(payload.get("cluster") or []),
                "state": "compiled",
            },
        )
    if legacy_type == "handoff_gateway":
        return (
            "topology.gateway.created",
            phase,
            active_subphase or "weld_plan",
            "builder",
            {
                "gateway_id": payload.get("gateway_id", "gateway"),
                "source_scope": payload.get("source_scope", "unknown"),
                "target_scope": payload.get("target_scope", "unknown"),
                "state": "proposed",
                "detail": payload.get("detail"),
            },
        )
    if legacy_type == "work_unit_assigned":
        return (
            "work_unit.upsert",
            phase,
            active_subphase or "partition",
            "builder",
            _normalize_work_unit(payload),
        )
    if legacy_type == "deliberation_complete":
        return (
            "phase.complete",
            "awaiting_swarm",
            "blueprint_freeze",
            "guided",
            {
                "session_id": payload.get("session_id"),
                "work_units": payload.get("work_units"),
                "high_risk_units": payload.get("high_risk_units"),
                "recommended_swarm": payload.get("recommended_swarm"),
                "prepare": payload.get("prepare"),
            },
        )
    if legacy_type == "deliberation_error":
        return ("error.summary", "failed", active_subphase, "guided", {"message": payload.get("message", "unknown")})

    return ("phase.progress", phase, active_subphase, "guided", {"legacy_type": legacy_type, **payload})


def validate_orchestration_event(event: dict[str, Any]) -> None:
    validator = _validator()
    if validator is None:
        return
    errors = sorted(validator.iter_errors(event), key=lambda item: item.path)
    if errors:
        detail = "; ".join(error.message for error in errors[:3])
        raise ValueError(f"orchestration event failed schema validation: {detail}")


@dataclass
class OrchestrationJournal:
    """Monotonic event journal for a single deliberation stream."""

    correlation_id: str
    session_id: str
    phase: str = "blueprinting"
    subphase: str | None = None
    sequence: int = -1
    last_event_id: str | None = None
    validate: bool = field(default_factory=schema_validation_available)
    _pending_session_id: str = field(init=False)

    def __post_init__(self) -> None:
        self._pending_session_id = self.session_id
        if self.validate and not schema_validation_available():
            self.validate = False

    def bind_session_id(self, session_id: str) -> None:
        cleaned = str(session_id or "").strip()
        if cleaned:
            self.session_id = cleaned

    @property
    def provisional_session(self) -> bool:
        return self.session_id == self._pending_session_id

    def emit_legacy(self, legacy_type: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(data or {})
        if legacy_type == "deliberation_complete" and payload.get("session_id"):
            self.bind_session_id(str(payload["session_id"]))
        event_type, phase, subphase, classification, canonical_data = map_legacy_deliberation_event(
            legacy_type,
            payload,
            phase=self.phase,
            subphase=self.subphase or payload.get("phase"),
        )
        if phase:
            self.phase = phase
        if subphase in TELEOLOGY_SUBPHASES:
            self.subphase = subphase
        elif payload.get("phase") in TELEOLOGY_SUBPHASES:
            self.subphase = str(payload["phase"])
        resolved_subphase = self.subphase if self.subphase in TELEOLOGY_SUBPHASES else None

        self.sequence += 1
        event_id = _new_event_id()
        envelope: dict[str, Any] = {
            "schema_version": 1,
            "event_id": event_id,
            "sequence": self.sequence,
            "emitted_at": _utc_now(),
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.last_event_id,
            "phase": self.phase,
            "subphase": resolved_subphase,
            "classification": classification,
            "event_type": event_type,
            "data": canonical_data,
        }
        if self.validate:
            validate_orchestration_event(envelope)
        self.last_event_id = event_id
        return envelope

    def to_legacy_wire(self, envelope: dict[str, Any]) -> dict[str, Any]:
        """Project canonical envelope to legacy {type,data} wire for transitional clients."""
        event_type = envelope["event_type"]
        data = dict(envelope.get("data") or {})
        legacy_type = {
            "phase.begin": "phase_begin",
            "phase.progress": "step_progress",
            "phase.complete": "phase_complete",
            "topology.node.upsert": "node_added",
            "topology.edge.curvature": "edge_curvature",
            "topology.bridge.detected": "dark_bridge_detected",
            "topology.weld.created": "weld_complete" if data.get("state") == "compiled" else "weld_start",
            "topology.gateway.created": "handoff_gateway",
            "work_unit.upsert": "work_unit_assigned",
            "error.summary": "deliberation_error",
        }.get(event_type, event_type)
        if event_type == "phase.begin" and data.get("provisional_session"):
            legacy_type = "deliberation_start"
        if event_type == "phase.progress" and "elapsed_ms" in data and "step" in data:
            legacy_type = "deliberation_heartbeat"
        if event_type == "phase.complete" and envelope.get("phase") == "awaiting_swarm":
            legacy_type = "deliberation_complete"
        if event_type == "topology.node.upsert":
            data = {
                "id": data.get("node_id"),
                "label": data.get("label"),
                "gravity": data.get("gravity"),
                "rejected": data.get("status") == "rejected",
            }
        if event_type == "topology.edge.curvature":
            data = {"source": data.get("source"), "target": data.get("target"), "kappa": data.get("kappa")}
        if event_type == "topology.bridge.detected":
            data = {"source": data.get("source"), "target": data.get("target"), "kappa": data.get("kappa")}
        if event_type == "work_unit.upsert":
            data = {
                "id": data.get("work_unit_id"),
                "title": data.get("title"),
                "files": data.get("allowed_path_count"),
                "risk": data.get("risk"),
                "depends_on": data.get("depends_on"),
                "preview": data.get("state") == "proposed",
            }
        return {"type": legacy_type, "data": data}


def sse_encode(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, separators=(",", ":"))
    return f"data: {body}\n\n"
