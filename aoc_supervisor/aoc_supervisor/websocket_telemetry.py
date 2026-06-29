"""WebSocket telemetry — SESSION_INIT, TOPOLOGY_SNAPSHOT, GRID_TELEMETRY."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any

from aoc_cli.blueprint import handoff_gateway_mode_enabled

from aoc_supervisor.complexity import build_snapshot, tier_for_score

CURVATURE_FLOOR_DEFAULT = -0.30
CANVAS_NODE_LIMIT = 40
CANVAS_LINK_LIMIT = 80

# Paths shown on the structural canvas — real source topology, not repo litter.
_CANVAS_PREFIXES = (
    "aoc-cli/",
    "aoc_supervisor/",
    "tests/",
    "ui/",
    "scripts/",
)
_CANVAS_SKIP_PREFIXES = (
    ".",
    "docs/campaign/",
    "dist/",
    "vaults/",
    ".gaijinn/",
    ".github/",
)

# Per-connection session overrides (in-memory; does not mutate canonical blueprint)
_session_overrides: dict[str, dict[str, Any]] = {}

# Monotonic sequence tracking per session
_session_sequences: dict[str, int] = {}
_loaded_schema: dict[str, Any] | None = None


class SequenceViolationError(RuntimeError):
    """Raised when a sequence regression is detected."""
    pass


class SchemaComplianceError(ValueError):
    """Raised when an outgoing message fails schema validation."""
    pass


def _validate_sequence_invariant(session_id: str, seq: int) -> None:
    last_seq = _session_sequences.get(session_id)
    if last_seq is not None and seq <= last_seq:
        raise SequenceViolationError(
            f"Sequence regression: proposed {seq} <= last {last_seq} for session {session_id}"
        )
    _session_sequences[session_id] = seq


def _validate_outgoing(msg: dict[str, Any]) -> None:
    global _loaded_schema
    if _loaded_schema is None:
        schema_path = Path(__file__).resolve().parents[2] / "ui" / "orchestration-event.schema.json"
        try:
            _loaded_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise SchemaComplianceError(f"Could not load schema from {schema_path}: {e}")

    from jsonschema import Draft202012Validator
    validator = Draft202012Validator(_loaded_schema)
    errors = list(validator.iter_errors(msg))
    if errors:
        details = "; ".join(e.message for e in errors)
        raise SchemaComplianceError(f"Schema validation failed: {details}")


def _wrap_event(
    session_id: str,
    event_type: str,
    classification: str,
    phase: str,
    data: dict[str, Any],
    *,
    sequence: int | None = None,
) -> dict[str, Any]:
    if sequence is None:
        last_seq = _session_sequences.get(session_id)
        seq = 0 if last_seq is None else last_seq + 1
    else:
        seq = sequence

    _validate_sequence_invariant(session_id, seq)

    event_id = f"evt_{uuid.uuid4().hex}"
    emitted_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    envelope = {
        "schema_version": 1,
        "event_id": event_id,
        "sequence": seq,
        "emitted_at": emitted_at,
        "session_id": session_id,
        "event_type": event_type,
        "classification": classification,
        "phase": phase,
        "data": data,
    }

    _validate_outgoing(envelope)
    return envelope


def _now() -> int:
    return int(time.time())


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _git_base_commit(project_root: Path) -> str:
    import subprocess

    try:
        out = subprocess.run(  # noqa: S603
            ["git", "-C", str(project_root), "rev-parse", "--short", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode == 0:
            return out.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown"


def new_session_id() -> str:
    return f"sess_{uuid.uuid4().hex[:8]}"


def get_curvature_floor(session_id: str) -> float:
    override = _session_overrides.get(session_id, {})
    return float(override.get("curvature_floor", CURVATURE_FLOOR_DEFAULT))


def _canvas_eligible_path(path: str) -> bool:
    normalized = str(path).replace("\\", "/")
    if any(normalized.startswith(skip) for skip in _CANVAS_SKIP_PREFIXES):
        return False
    if not any(normalized.startswith(prefix) for prefix in _CANVAS_PREFIXES):
        return False
    return normalized.endswith((".py", ".js", ".ts", ".tsx", ".go", ".rs", ".sh"))


def _work_unit_index(blueprint: dict[str, Any]) -> dict[str, str]:
    """Map repo-relative file path → work unit id."""
    index: dict[str, str] = {}
    units = blueprint.get("work_units", [])
    if not isinstance(units, list):
        return index
    for unit in units:
        if not isinstance(unit, dict):
            continue
        wu_id = str(unit.get("id", ""))
        if not wu_id:
            continue
        allowed = unit.get("allowed_paths", [])
        if not isinstance(allowed, list):
            continue
        for raw in allowed:
            path = str(raw).replace("\\", "/").rstrip("/")
            if not path:
                continue
            index[path] = wu_id
            # Directory scope: mark children
            if not path.endswith((".py", ".js", ".ts", ".tsx", ".go", ".rs")):
                prefix = f"{path}/"
                index[prefix] = wu_id
    return index


def _jurisdiction_for_path(path: str, wu_index: dict[str, str], blueprint: dict[str, Any]) -> str:
    normalized = str(path).replace("\\", "/")
    if normalized in wu_index:
        return wu_index[normalized]
    for prefix, wu_id in wu_index.items():
        if prefix.endswith("/") and normalized.startswith(prefix):
            return wu_id
    units = blueprint.get("work_units", [])
    if isinstance(units, list):
        for unit in units:
            if not isinstance(unit, dict):
                continue
            denied = unit.get("denied_paths", [])
            if isinstance(denied, list) and any(normalized.startswith(str(d).rstrip("/") + "/") for d in denied):
                continue
    return "unassigned"


def build_session_init(
    project_root: Path,
    *,
    session_id: str,
    experience_mode: str = "builder",
    account_plan: str = "business",
) -> dict[str, Any]:
    metrics_path = project_root / ".gaijinn" / "metrics_manifest.json"
    graph_path = project_root / ".gaijinn" / "graph.json"
    node_count = 0
    graph_payload = _load_json(graph_path)
    nodes = graph_payload.get("nodes", [])
    if isinstance(nodes, list):
        node_count = len(nodes)

    aci_score = 0
    complexity_class = "starter"
    if metrics_path.exists():
        try:
            snap = build_snapshot(
                metrics_path=metrics_path, blueprint_path=project_root / ".gaijinn" / "blueprint.json"
            )
            aci_score = snap.integrity_score
            complexity_class = tier_for_score(aci_score)
        except (ValueError, OSError):
            pass

    floor = get_curvature_floor(session_id)
    allow_override = experience_mode == "operator"
    return _wrap_event(
        session_id=session_id,
        event_type="session.snapshot",
        classification="guided",
        phase="awaiting_intent",
        data={
            "session_id": session_id,
            "experience_mode": experience_mode,
            "account_plan": account_plan,
            "global_constraints": {
                "curvature_threshold": floor,
                "enforce_giv_containment": True,
                "allow_geometry_override": allow_override,
            },
            "repository_summary": {
                "total_files": node_count,
                "base_commit": _git_base_commit(project_root),
                "architectural_complexity_index": round(aci_score / 2500.0, 2) if aci_score else 0.0,
                "complexity_class": complexity_class,
            },
        },
    )


def _mitigation_for_edge(kappa: float, gateway_mode: bool) -> str:
    if kappa > -0.30:
        return "GOVERNED_HANDOFF" if gateway_mode else "INDEPENDENT"
    if gateway_mode:
        return "HANDOFF_ONLY"
    return "WELD_PROPOSED"


def build_topology_snapshot(
    project_root: Path,
    *,
    session_id: str,
    version: str = "1.0.4",
) -> dict[str, Any]:
    metrics_path = project_root / ".gaijinn" / "metrics_manifest.json"
    blueprint_path = project_root / ".gaijinn" / "blueprint.json"
    governance_path = project_root / ".gaijinn" / "merge" / "governance.json"

    metrics = _load_json(metrics_path)
    blueprint = _load_json(blueprint_path)
    governance = _load_json(governance_path)
    structural = governance.get("structural_score", {}) if isinstance(governance, dict) else {}
    convergence = structural.get("convergence")
    if convergence is None:
        convergence = 0.0

    gravity_nodes = metrics.get("gravity_meta", {}).get("nodes", {})
    curvature_edges = metrics.get("curvature_meta", {}).get("edges", {})
    floor = get_curvature_floor(session_id)
    gateway_mode = handoff_gateway_mode_enabled()

    # Strategy overrides from builder weld affirmations
    overrides = _session_overrides.get(session_id, {}).get("weld_overrides", {})

    wu_index = _work_unit_index(blueprint)

    # Rank eligible source nodes by structural gravity (not alphabetical).
    ranked: list[tuple[str, float, dict[str, Any]]] = []
    bridge_paths: set[str] = set()
    if isinstance(curvature_edges, dict):
        for edge in curvature_edges.values():
            if not isinstance(edge, dict):
                continue
            kappa = float(edge.get("kappa", edge.get("curvature", 0.0)) or 0.0)
            if kappa < 0:
                bridge_paths.add(str(edge.get("source", "")))
                bridge_paths.add(str(edge.get("target", "")))

    if isinstance(gravity_nodes, dict):
        for path, meta in gravity_nodes.items():
            if not isinstance(meta, dict):
                continue
            path_str = str(path).replace("\\", "/")
            if not _canvas_eligible_path(path_str):
                continue
            gravity = float(meta.get("gravity", 0.0) or 0.0)
            score = gravity + (0.15 if path_str in bridge_paths else 0.0)
            ranked.append((path_str, score, meta))

    ranked.sort(key=lambda item: item[1], reverse=True)
    selected_paths = {path for path, _, _ in ranked[:CANVAS_NODE_LIMIT]}

    nodes_out: list[dict[str, Any]] = []
    path_to_node: dict[str, str] = {}
    for idx, (path_str, score, meta) in enumerate(ranked[:CANVAS_NODE_LIMIT], start=1):
        node_id = f"node_{idx:03d}"
        path_to_node[path_str] = node_id
        nodes_out.append(
            {
                "id": node_id,
                "path": path_str,
                "aci": round(float(meta.get("gravity", score) or 0.0), 2),
                "jurisdiction": _jurisdiction_for_path(path_str, wu_index, blueprint),
                "on_shadow_bridge": path_str in bridge_paths,
            }
        )

    links_out: list[dict[str, Any]] = []
    welds: dict[str, Any] = {}
    if isinstance(curvature_edges, dict):
        for edge in sorted(
            curvature_edges.values(),
            key=lambda e: float(e.get("kappa", e.get("curvature", 0.0)) or 0.0) if isinstance(e, dict) else 0.0,
        ):
            if not isinstance(edge, dict):
                continue
            source_path = str(edge.get("source", "")).replace("\\", "/")
            target_path = str(edge.get("target", "")).replace("\\", "/")
            if source_path not in selected_paths or target_path not in selected_paths:
                continue
            source_id = path_to_node.get(source_path)
            target_id = path_to_node.get(target_path)
            if not source_id or not target_id:
                continue
            kappa = float(edge.get("kappa", edge.get("curvature", 0.0)) or 0.0)
            is_bridge = kappa < 0.0
            pair_key = tuple(sorted([source_id, target_id]))
            strategy = overrides.get(pair_key) or _mitigation_for_edge(kappa, gateway_mode)
            link = {
                "source": source_id,
                "target": target_id,
                "curvature": round(kappa, 2),
                "is_shadow_bridge": is_bridge,
                "mitigation_strategy": strategy,
            }
            if strategy == "WELD" or (strategy == "WELD_PROPOSED" and kappa <= floor):
                weld_id = f"weld_{hashlib.sha256(f'{source_id}:{target_id}'.encode()).hexdigest()[:8]}"
                link["weld_id"] = weld_id
                if weld_id not in welds:
                    welds[weld_id] = {
                        "label": f"{Path(source_path).name} ↔ {Path(target_path).name}",
                        "member_node_ids": [source_id, target_id],
                        "status": "ACTIVE" if strategy == "WELD" else "PENDING_APPROVAL",
                    }
            links_out.append(link)
            if len(links_out) >= CANVAS_LINK_LIMIT:
                break

    total_eligible = len(ranked)
    shadow_count = sum(1 for link in links_out if link.get("is_shadow_bridge"))

    return _wrap_event(
        session_id=session_id,
        event_type="topology.constraints.summary",
        classification="builder",
        phase="blueprinting",
        data={
            "version": version,
            "data_source": "live",
            "convergence_score": float(convergence) if convergence is not None else 0.0,
            "nodes": nodes_out,
            "links": links_out,
            "welds": welds,
            "gateway_mode": gateway_mode,
            "work_unit_count": len(blueprint.get("work_units", []))
            if isinstance(blueprint.get("work_units"), list)
            else 0,
            "graph_stats": {
                "total_graph_nodes": len(gravity_nodes) if isinstance(gravity_nodes, dict) else 0,
                "canvas_eligible_nodes": total_eligible,
                "canvas_node_limit": CANVAS_NODE_LIMIT,
                "shadow_bridges_shown": shadow_count,
            },
        },
    )


def build_grid_telemetry(project_root: Path, *, session_id: str | None = None) -> dict[str, Any]:
    workers_dir = project_root / ".gaijinn" / "workers"
    manifest = _load_json(workers_dir / "manifest.json")
    collected = _load_json(project_root / ".gaijinn" / "merge" / "collected.json")
    handoff_queue = _load_json(project_root / ".gaijinn" / "merge" / "handoff-queue.json")
    governance = _load_json(project_root / ".gaijinn" / "merge" / "governance.json")

    worker_dirs = sorted(p for p in workers_dir.glob("worker-*") if p.is_dir())
    collected_workers = collected.get("workers", {}) if isinstance(collected.get("workers"), dict) else {}

    workers_out: dict[str, Any] = {}
    for worker_dir in worker_dirs:
        wid = worker_dir.name
        record = collected_workers.get(wid, {}) if isinstance(collected_workers.get(wid), dict) else {}
        status_raw = str(record.get("status", "IDLE")).upper()
        if status_raw in {"COMPLETED", "VALIDATED"}:
            status = "COMPLETED"
        elif status_raw in {"DIRTY", "BLOCKED"}:
            status = "VIOLATION_DETECTED"
        elif status_raw == "PENDING":
            status = "WAITING_ON_HANDOFF"
        else:
            status = "EXECUTING_REFACTOR"
        changed = record.get("changed_files", [])
        if not isinstance(changed, list):
            changed = []
        giv_path = worker_dir / "giv.json"
        giv_sig = ""
        if giv_path.exists():
            giv_sig = f"giv_sig_{hashlib.sha256(giv_path.read_bytes()).hexdigest()[:24]}"
        detail = manifest.get("workers", {}).get(wid, {}) if isinstance(manifest.get("workers"), dict) else {}
        wu_ids = detail.get("assigned_work_units", []) if isinstance(detail, dict) else []
        workers_out[wid] = {
            "worker_id": wid,
            "work_unit_id": str(wu_ids[0]) if wu_ids else "",
            "status": status,
            "target_lane": "cross_boundary_transit" if status == "WAITING_ON_HANDOFF" else "unlocked_lane_alpha",
            "giv_token_signature": giv_sig,
            "mutated_paths": [str(p) for p in changed[:8]],
            "violation_alerts": record.get("trespasses", []) if isinstance(record.get("trespasses"), list) else [],
        }

    tickets_raw = handoff_queue.get("tickets", []) if isinstance(handoff_queue.get("tickets"), list) else []
    active_tickets = []
    for ticket in tickets_raw:
        if not isinstance(ticket, dict):
            continue
        if str(ticket.get("status", "")).lower() in {"resolved", "closed"}:
            continue
        active_tickets.append(
            {
                "ticket_id": str(ticket.get("ticket_id", "")),
                "from_worker": str(ticket.get("source_worker_id", "")),
                "to_worker": str(ticket.get("target_work_unit_id", "")),
                "payload_hash": f"sha256_{hashlib.sha256(json.dumps(ticket, sort_keys=True).encode()).hexdigest()}",
                "status": "IN_TRANSIT",
            }
        )

    structural = governance.get("structural_score", {}) if isinstance(governance, dict) else {}

    if session_id is None:
        session_id = "sess_default"

    return _wrap_event(
        session_id=session_id,
        event_type="merge.state.updated",
        classification="builder",
        phase="sprinting",
        data={
            "active_workers": len(worker_dirs),
            "total_sprint_allocation": int(manifest.get("worker_count", len(worker_dirs)) or len(worker_dirs)) * 100,
            "sprints_consumed": len([w for w in workers_out.values() if w["status"] == "COMPLETED"]),
            "workers": workers_out,
            "active_handoff_tickets": active_tickets,
            "validation_pass_rate": structural.get("validation_pass_rate"),
            "transaction_bus_synchronized": structural.get("transaction_bus_synchronized"),
        },
    )


def handle_client_action(
    action: str,
    payload: dict[str, Any],
    *,
    session_id: str,
    experience_mode: str,
    project_root: Path,
) -> dict[str, Any] | None:
    if action == "MUTATE_GEOMETRY_STRATEGY":
        if experience_mode not in {"builder", "operator"}:
            return {
                "event": "ACTION_REJECTED",
                "timestamp": _now(),
                "payload": {"reason": "insufficient_mode", "required": "builder"},
            }
        target = payload.get("target_link", [])
        strategy = str(payload.get("selected_strategy", "")).upper()
        if not isinstance(target, list) or len(target) < 2:
            return {"event": "ACTION_REJECTED", "timestamp": _now(), "payload": {"reason": "invalid_target_link"}}
        pair = tuple(sorted([str(target[0]), str(target[1])]))
        store = _session_overrides.setdefault(session_id, {})
        welds = store.setdefault("weld_overrides", {})
        welds[pair] = "WELD" if strategy == "WELD" else "HANDOFF_ONLY"
        return None

    if action == "OVERRIDE_SYSTEM_INVARIANT":
        if experience_mode != "operator":
            return {
                "event": "ACTION_REJECTED",
                "timestamp": _now(),
                "payload": {"reason": "operator_mode_required"},
            }
        key = str(payload.get("invariant_key", ""))
        if key != "ricci_curvature_floor":
            return {"event": "ACTION_REJECTED", "timestamp": _now(), "payload": {"reason": "unknown_invariant"}}
        try:
            requested = float(payload.get("requested_value", CURVATURE_FLOOR_DEFAULT))
        except (TypeError, ValueError):
            return {"event": "ACTION_REJECTED", "timestamp": _now(), "payload": {"reason": "invalid_value"}}
        store = _session_overrides.setdefault(session_id, {})
        store["curvature_floor"] = requested
        store["unsafe_geometry"] = True
        base = _git_base_commit(project_root)
        audit_token = f"AUDIT_UNSAFE_GEOMETRY_{base}_{_now()}"
        return {
            "event": "INVARIANT_OVERRIDE_ACK",
            "timestamp": _now(),
            "payload": {
                "status": "APPLIED_UNSAFE",
                "audit_token": audit_token,
                "new_geometry_signature": f"custom_dirty_hash_{hashlib.sha256(audit_token.encode()).hexdigest()[:5]}",
                "curvature_floor": requested,
                "justification": str(payload.get("justification", "")),
            },
        }

    if action == "SET_EXPERIENCE_MODE":
        mode = str(payload.get("mode", "builder")).lower()
        if mode not in {"guided", "builder", "operator"}:
            return {"event": "ACTION_REJECTED", "timestamp": _now(), "payload": {"reason": "invalid_mode"}}
        store = _session_overrides.setdefault(session_id, {})
        store["experience_mode"] = mode
        return None

    return {"event": "ACTION_REJECTED", "timestamp": _now(), "payload": {"reason": "unknown_action"}}


def effective_experience_mode(session_id: str, requested: str) -> str:
    """Client may only lower mode; server stores effective projection."""
    rank = {"guided": 1, "builder": 2, "operator": 3}
    stored = _session_overrides.get(session_id, {}).get("experience_mode", requested)
    req = requested if requested in rank else "builder"
    st = stored if stored in rank else "builder"
    return req if rank[req] <= rank[st] else st
