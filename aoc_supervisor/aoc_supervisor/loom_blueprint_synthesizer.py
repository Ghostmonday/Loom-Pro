"""Blueprint Synthesizer — transforms forge output into executable swarm projections."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aoc_cli.blueprint import generate_blueprint
from aoc_cli.giv import GIV
from aoc_cli.gravity import compute_gravity_and_curvature

from aoc_supervisor.intent_forge_service import IntentForgeService
from aoc_supervisor.orchestration_envelope import _edge_classification


@dataclass
class SynthesisRequest:
    """Payload for a blueprint synthesis invocation.

    Carries forge session context, confirmed requirements, and the
    executable projection that the blueprint compiler produced.
    """

    session_id: str
    intent: str
    forge_session_id: str | None = None
    phases: list[str] | None = None
    blueprint_graph: dict[str, Any] | None = None
    confirmed_requirements: list[dict[str, Any]] | None = None
    executable_projection: dict[str, Any] | None = None
    teleology_receipt: dict[str, Any] | None = None


@dataclass
class SynthesisResult:
    """Result container produced by blueprint synthesis.

    The ``blueprint`` dict holds the synthesised work-unit graph;
    ``warnings`` captures any anomalies encountered during synthesis.
    """

    session_id: str
    work_units: int = 1
    blueprint: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    dark_bridge_count: int | None = None
    teleology_receipt: dict[str, Any] | None = None

    def to_public_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dict with standard fields."""
        payload = {
            "session_id": self.session_id,
            "work_units": self.work_units,
            "blueprint": self.blueprint,
            "warnings": list(self.warnings),
        }
        if self.dark_bridge_count is not None:
            payload["dark_bridge_count"] = self.dark_bridge_count
        if self.teleology_receipt is not None:
            payload["teleology_receipt"] = deepcopy(self.teleology_receipt)
        return payload


def _project_root() -> Path:
    override = os.environ.get("GAIJINN_PROJECT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def _projection_graph(projection: dict[str, Any]) -> dict[str, list[Any]] | None:
    """Translate forge workstreams into the file graph consumed by gravity."""
    raw_units = projection.get("work_units")
    if not isinstance(raw_units, list):
        return None

    units_by_id: dict[str, list[str]] = {}
    nodes: list[dict[str, Any]] = []
    risk_scores = {
        "low": (1, 0.5),
        "medium": (3, 1.5),
        "high": (5, 3),
    }

    for raw_unit in raw_units:
        if not isinstance(raw_unit, dict):
            continue
        unit_id = str(raw_unit.get("id", "")).strip()
        raw_paths = raw_unit.get("allowed_paths")
        if not unit_id or not isinstance(raw_paths, list):
            continue
        paths = sorted({str(path).strip() for path in raw_paths if str(path).strip()})
        if not paths:
            continue
        units_by_id[unit_id] = paths
        risk = str(raw_unit.get("estimated_risk", "low")).strip().lower()
        capability_level, side_effect_score = risk_scores.get(risk, risk_scores["low"])
        for path in paths:
            suffix = Path(path.rstrip("/")).suffix.lstrip(".")
            nodes.append(
                {
                    "id": path,
                    "path": path,
                    "language": suffix or "unknown",
                    "capability_level": capability_level,
                    "side_effect_score": side_effect_score,
                }
            )

    if not nodes:
        return None

    dependencies = projection.get("dependencies")
    edges: set[tuple[str, str]] = set()
    for raw_unit in raw_units:
        if not isinstance(raw_unit, dict):
            continue
        unit_id = str(raw_unit.get("id", "")).strip()
        raw_dependencies = raw_unit.get("depends_on", ())
        if isinstance(dependencies, dict):
            raw_dependencies = dependencies.get(unit_id, raw_dependencies)
        if not isinstance(raw_dependencies, (list, tuple)):
            continue
        for dependency_id in raw_dependencies:
            for source in units_by_id.get(str(dependency_id), ()):
                for target in units_by_id.get(unit_id, ()):
                    if source != target:
                        edges.add((source, target))

    return {
        "nodes": sorted(nodes, key=lambda node: str(node["id"])),
        "edges": [list(edge) for edge in sorted(edges)],
    }


def _dark_bridge_edges(metrics: Mapping[str, Any]) -> list[tuple[str, str]]:
    curvature_meta = metrics.get("curvature_meta", {})
    if not isinstance(curvature_meta, Mapping):
        return []

    raw_edges = curvature_meta.get("edges", {})
    edge_values = raw_edges.values() if isinstance(raw_edges, Mapping) else raw_edges
    if not isinstance(edge_values, (list, tuple)) and not hasattr(edge_values, "__iter__"):
        return []

    pairs: set[tuple[str, str]] = set()
    for raw_edge in edge_values:
        if not isinstance(raw_edge, Mapping):
            continue
        try:
            kappa = float(raw_edge.get("kappa", raw_edge.get("curvature", 0.0)) or 0.0)
        except (TypeError, ValueError):
            continue
        if raw_edge.get("is_dark_bridge") is not True and _edge_classification(kappa) != "dark_bridge":
            continue
        source = str(raw_edge.get("source", "")).strip()
        target = str(raw_edge.get("target", "")).strip()
        if source and target:
            pairs.add((source, target))
    return sorted(pairs)


def _remaining_dark_bridge_count(plan: Mapping[str, Any], dark_edges: list[tuple[str, str]]) -> int:
    owners: dict[str, str] = {}
    raw_units = plan.get("work_units", ())
    if isinstance(raw_units, list):
        for raw_unit in raw_units:
            if not isinstance(raw_unit, Mapping):
                continue
            unit_id = str(raw_unit.get("id", "")).strip()
            raw_paths = raw_unit.get("allowed_paths", ())
            if not unit_id or not isinstance(raw_paths, (list, tuple)):
                continue
            for path in raw_paths:
                owners[str(path)] = unit_id
    return sum(1 for source, target in dark_edges if not owners.get(source) or owners.get(source) != owners.get(target))


def _write_blueprint(session_root: Path, blueprint: dict[str, Any]) -> None:
    path = session_root / ".gaijinn" / "blueprint.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".blueprint.", suffix=".tmp", dir=str(path.parent), text=True)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(blueprint, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _session_root(service: IntentForgeService) -> Path:
    host_root = getattr(getattr(service, "store", None), "host_root", None)
    return Path(host_root).resolve() if host_root is not None else _project_root()


def _finish_synthesis(
    request: SynthesisRequest,
    service: IntentForgeService,
    blueprint: dict[str, Any],
    *,
    warnings: list[str] | None = None,
    dark_bridge_count: int,
    annotate_blueprint: bool = True,
) -> SynthesisResult:
    receipt = deepcopy(request.teleology_receipt) if isinstance(request.teleology_receipt, dict) else None
    if annotate_blueprint:
        blueprint["dark_bridge_count"] = dark_bridge_count
        if receipt is not None:
            blueprint["teleology_receipt"] = receipt
    _write_blueprint(_session_root(service), blueprint)
    work_units = blueprint.get("work_units")
    return SynthesisResult(
        session_id=request.session_id,
        work_units=len(work_units) if isinstance(work_units, list) else 0,
        blueprint=blueprint,
        warnings=warnings or [],
        dark_bridge_count=dark_bridge_count,
        teleology_receipt=receipt,
    )


def synthesize_blueprint(
    request: SynthesisRequest,
    *,
    forge_service: IntentForgeService | None = None,
) -> SynthesisResult:
    """Fuse a handed-off forge projection with gravity-conditioned planning.

    Raises
    ------
    ValueError
        If the forge session has not been handed off or has no executable
        projection.
    """
    forge_session_id = request.forge_session_id or request.session_id
    service = forge_service or IntentForgeService(_project_root())
    forge_state = service.get_session(forge_session_id)

    if forge_state.get("session_status") != "HANDED_OFF":
        raise ValueError("intent forge session must be HANDED_OFF before synthesis")

    projection = forge_state.get("executable_projection")
    if not isinstance(projection, dict):
        raise ValueError("HANDED_OFF intent forge session has no executable_projection")

    executable_projection = deepcopy(projection)
    request.forge_session_id = forge_session_id
    request.executable_projection = deepcopy(executable_projection)

    graph = _projection_graph(executable_projection)
    if graph is None:
        return _finish_synthesis(
            request,
            service,
            executable_projection,
            warnings=["forge projection has no allowed_paths; gravity fusion skipped"],
            dark_bridge_count=0,
            annotate_blueprint=False,
        )

    metrics = compute_gravity_and_curvature(graph)
    allowed_paths = tuple(str(node["path"]) for node in graph["nodes"])
    giv = GIV(worker_id=f"loom-{request.session_id}", allowed_paths=allowed_paths)
    dark_edges = _dark_bridge_edges(metrics)
    candidates = []
    for strategy, handoff_gateways in (("atomic_weld", False), ("handoff_partition", True)):
        plan = generate_blueprint(graph, metrics, giv, handoff_gateways=handoff_gateways).to_dict()
        candidates.append((_remaining_dark_bridge_count(plan, dark_edges), strategy, plan))
    dark_bridge_count, strategy, gravity_plan = min(candidates, key=lambda candidate: (candidate[0], candidate[1]))

    executable_projection.update(gravity_plan)
    executable_projection["curvature_metrics"] = metrics
    executable_projection["projection_mode"] = "loom_synthesis"
    executable_projection["synthesis_strategy"] = strategy
    executable_projection["graph_only_dark_bridge_count"] = len(dark_edges)
    return _finish_synthesis(
        request,
        service,
        executable_projection,
        dark_bridge_count=dark_bridge_count,
    )
