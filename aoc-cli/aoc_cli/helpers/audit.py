"""Structural audit helpers — zero-mutation repository readiness evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..blueprint import Blueprint, generate_blueprint, handoff_gateway_records
from ..giv import GIV
from ..gravity import CURVATURE_HARD_FLOOR, GRAVITY_HARD_FLOOR, compute_gravity_and_curvature
from .diagnostics import _integrity_score
from .merge import utc_now, write_merge_json
from .scan import _scan_directory

AUDIT_REPORT_PATH = Path(".gaijinn/audit-report.json")
AUDIT_SCHEMA_VERSION = 1

READINESS_TIERS = {
    "TIER_1_SWARM_READY": ("Safe for high-concurrency, fully isolated multi-worker sprints.",),
    "TIER_2_DEFERRED_ONLY": (
        "Safe for parallel work units, but requires strict sequential merge gates due to coupled modules.",
    ),
    "TIER_3_STRUCTURAL_LOCK": (
        "High structural regression risk. Refactor high-curvature modules before launching parallel agent swarms.",
    ),
}


def default_audit_giv(target: Path) -> GIV:
    """Broad read-only GIV profile used for audit-time blueprint simulation."""
    return GIV(
        worker_id="audit",
        allowed_paths=(target.as_posix() + "/",),
        denied_paths=(".gaijinn/",),
        capabilities=("structural_audit",),
        invariants=("audit is read-only", "no worker mutation"),
    )


def global_gravity_score(gravity_meta: Mapping[str, Any]) -> float:
    nodes = gravity_meta.get("nodes", {})
    if not isinstance(nodes, Mapping) or not nodes:
        return 1.0
    values = [float(meta.get("gravity", 0.0)) for meta in nodes.values() if isinstance(meta, Mapping)]
    if not values:
        return 1.0
    return sum(values) / len(values)


def format_shadow_bridge_violations(shadow_bridges: Sequence[Mapping[str, Any]]) -> list[str]:
    violations: list[str] = []
    for bridge in shadow_bridges:
        if not isinstance(bridge, Mapping):
            continue
        source = str(bridge.get("source", ""))
        target = str(bridge.get("target", ""))
        kappa = bridge.get("kappa", bridge.get("curvature", 0.0))
        violations.append(f"{source} -> {target} (kappa={float(kappa):.4f})")
    return sorted(violations)


def _atomic_weld_block_units(blueprint: Blueprint) -> list[Any]:
    """Work units created by union-find dark-bridge welding (multi-file atomic blocks)."""
    blocks: list[Any] = []
    for unit in blueprint.work_units:
        title = unit.title.lower()
        if len(unit.allowed_paths) <= 1:
            continue
        if "atomic block" in title or "coupling review block" in title or "dark bridge" in title:
            blocks.append(unit)
    return blocks


def atomic_weld_block_metrics(blueprint: Blueprint) -> dict[str, int]:
    """Summarize union-find weld serialization pressure in a blueprint."""
    blocks = _atomic_weld_block_units(blueprint)
    file_counts = [len(unit.allowed_paths) for unit in blocks]
    return {
        "atomic_weld_blocks": len(blocks),
        "largest_atomic_weld_file_count": max(file_counts) if file_counts else 0,
        "total_files_in_atomic_welds": sum(file_counts),
    }


def max_parallel_worker_capacity(blueprint: Blueprint) -> int:
    """Estimate max safe concurrent workers from blueprint dependency layers."""
    units = blueprint.work_units
    if not units:
        return 1

    incoming = {unit.id: set(unit.depends_on) for unit in units}
    levels: list[list[str]] = []
    completed: set[str] = set()
    ready = sorted(unit_id for unit_id, deps in incoming.items() if not deps)

    while ready:
        levels.append(list(ready))
        completed.update(ready)
        next_ready: list[str] = []
        for unit_id in ready:
            for other_id, deps in incoming.items():
                if unit_id in deps:
                    deps.discard(unit_id)
        for other_id, deps in incoming.items():
            if not deps and other_id not in completed and other_id not in next_ready:
                next_ready.append(other_id)
        ready = sorted(next_ready)

    if not levels:
        return 1
    return max(1, max(len(level) for level in levels))


def readiness_profile(global_gravity: float, shadow_bridge_count: int) -> tuple[str, str]:
    if global_gravity >= 0.60 and shadow_bridge_count == 0:
        tier = "TIER_1_SWARM_READY"
    elif global_gravity >= 0.25:
        tier = "TIER_2_DEFERRED_ONLY"
    else:
        tier = "TIER_3_STRUCTURAL_LOCK"
    return tier, READINESS_TIERS[tier][0]


def handoff_gateway_profile(
    graph: Mapping[str, Any],
    metrics: Mapping[str, Any],
    giv: GIV,
) -> dict[str, Any]:
    """Compare weld-mode vs gateway-mode blueprint partitioning for auditor guidance."""
    gateways = handoff_gateway_records(metrics)
    weld_blueprint = generate_blueprint(graph, metrics, giv, handoff_gateways=False)
    gateway_blueprint = generate_blueprint(graph, metrics, giv, handoff_gateways=True)
    weld_count = len(weld_blueprint.work_units)
    gateway_count = len(gateway_blueprint.work_units)
    weld_welds = atomic_weld_block_metrics(weld_blueprint)
    gateway_welds = atomic_weld_block_metrics(gateway_blueprint)
    weld_parallel = max_parallel_worker_capacity(weld_blueprint)
    gateway_parallel = max_parallel_worker_capacity(gateway_blueprint)
    blocks_eliminated = weld_welds["atomic_weld_blocks"] - gateway_welds["atomic_weld_blocks"]
    files_unlocked = weld_welds["total_files_in_atomic_welds"] - gateway_welds["total_files_in_atomic_welds"]
    return {
        "handoff_gateway_count": len(gateways),
        "handoff_gateways": gateways,
        "work_unit_count_weld_mode": weld_count,
        "work_unit_count_gateway_mode": gateway_count,
        "parallel_units_unlocked": max(0, gateway_count - weld_count),
        "curvature_hard_floor": CURVATURE_HARD_FLOOR,
        "legacy_mode": {
            "mode": "union_find_weld",
            "label": "Legacy Mode (Union-Find Weld)",
            "work_unit_count": weld_count,
            "atomic_weld_blocks": weld_welds["atomic_weld_blocks"],
            "largest_atomic_weld_file_count": weld_welds["largest_atomic_weld_file_count"],
            "total_files_in_atomic_welds": weld_welds["total_files_in_atomic_welds"],
            "max_parallel_workers": weld_parallel,
        },
        "gateway_mode": {
            "mode": "handoff_gateway",
            "label": "Gateway Mode (GAIJINN_HANDOFF_GATEWAYS=1)",
            "env_flag": "GAIJINN_HANDOFF_GATEWAYS=1",
            "work_unit_count": gateway_count,
            "atomic_weld_blocks": gateway_welds["atomic_weld_blocks"],
            "handoff_gateway_count": len(gateways),
            "max_parallel_workers": gateway_parallel,
        },
        "efficiency_delta": {
            "atomic_weld_blocks_eliminated": max(0, blocks_eliminated),
            "files_unlocked_from_atomic_welds": max(0, files_unlocked),
            "parallel_worker_delta": gateway_parallel - weld_parallel,
            "gateway_recommended": blocks_eliminated > 0 or len(gateways) > 0,
        },
    }


_VAULT_MEMORY_MIRROR_PREFIX = "vaults/gaijinn-memory-fs/"


def _exclude_vault_memory_mirror(graph: Mapping[str, Any]) -> dict[str, Any]:
    """Drop generated vault mirror nodes so monorepo audit does not straddle vault/code."""
    nodes = [
        node
        for node in graph.get("nodes", [])
        if isinstance(node, Mapping) and not str(node.get("path", "")).startswith(_VAULT_MEMORY_MIRROR_PREFIX)
    ]
    node_ids = {str(node.get("id", "")) for node in nodes}
    edges = [
        edge
        for edge in graph.get("edges", [])
        if isinstance(edge, Sequence) and len(edge) >= 2 and str(edge[0]) in node_ids and str(edge[1]) in node_ids
    ]
    interaction_graph = [
        item
        for item in graph.get("interaction_graph", [])
        if isinstance(item, Mapping) and not str(item.get("path", "")).startswith(_VAULT_MEMORY_MIRROR_PREFIX)
    ]
    filtered = dict(graph)
    filtered["nodes"] = nodes
    filtered["edges"] = edges
    filtered["interaction_graph"] = interaction_graph
    layer1 = filtered.get("layer1_reactive")
    if isinstance(layer1, Mapping):
        filtered["layer1_reactive"] = {
            **layer1,
            "file_nodes": len(nodes),
            "intent_nodes": len(interaction_graph),
        }
    return filtered


def run_structural_audit(target: Path) -> dict[str, Any]:
    """Scan, analyze, and summarize repository structural readiness (no mutation)."""
    root = target.resolve()
    graph = _exclude_vault_memory_mirror(_scan_directory(root))
    metrics = compute_gravity_and_curvature(graph)
    gravity_meta = metrics.get("gravity_meta", {})
    curvature_meta = metrics.get("curvature_meta", {})

    shadow_bridges = [meta for meta in curvature_meta.get("shadow_bridges", ()) if isinstance(meta, Mapping)]
    if not shadow_bridges:
        shadow_bridges = [
            meta
            for meta in curvature_meta.get("edges", {}).values()
            if isinstance(meta, Mapping) and meta.get("is_shadow_bridge")
        ]

    global_gravity = global_gravity_score(gravity_meta if isinstance(gravity_meta, Mapping) else {})
    shadow_count = len(shadow_bridges)
    tier, recommendation = readiness_profile(global_gravity, shadow_count)

    audit_giv = default_audit_giv(root)
    blueprint = generate_blueprint(graph, metrics, audit_giv)
    gateway_profile = handoff_gateway_profile(graph, metrics, audit_giv)
    max_width = max_parallel_worker_capacity(blueprint)

    rejected_nodes = (
        sorted(str(node) for node in gravity_meta.get("rejected_nodes", []) if node)
        if isinstance(gravity_meta, Mapping)
        else []
    )

    extended = {
        "node_count": len(graph.get("nodes", [])),
        "shadow_bridge_count": shadow_count,
        "rejected_nodes": len(rejected_nodes),
        "mean_severity": _mean_negative_curvature(curvature_meta),
    }
    integrity_score = _integrity_score(
        extended,
        worker_count=max_width,
        assignment_count=max(1, len(blueprint.work_units)),
        high_risk_assignments=sum(1 for unit in blueprint.work_units if unit.estimated_risk == "high"),
    )

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audited_at": utc_now(),
        "target_directory": str(root),
        "metrics": {
            "total_code_nodes": len(graph.get("nodes", [])),
            "total_import_edges": len(graph.get("edges", [])),
            "global_gravity_score": round(global_gravity, 4),
            "gravity_hard_floor": GRAVITY_HARD_FLOOR,
            "shadow_bridge_count": shadow_count,
            "rejected_node_count": len(rejected_nodes),
            "max_parallel_worker_capacity": max_width,
            "integrity_score": integrity_score,
            "work_unit_count": len(blueprint.work_units),
        },
        "governance_profile": {
            "readiness_tier": tier,
            "recommendation": recommendation,
            "critical_violations": format_shadow_bridge_violations(shadow_bridges),
            "rejected_nodes": rejected_nodes,
        },
        "topology": {
            "work_units": [unit.id for unit in blueprint.work_units],
            "dependencies": dict(sorted(blueprint.dependencies.items())),
        },
        "handoff_gateway_profile": gateway_profile,
    }


def write_audit_report(target: Path, payload: Mapping[str, Any], report_path: Path | None = None) -> Path:
    path = (report_path or (target / AUDIT_REPORT_PATH)).resolve()
    write_merge_json(path, dict(payload))
    return path


def _mean_negative_curvature(curvature_meta: Mapping[str, Any]) -> float:
    edges = curvature_meta.get("edges", {})
    if not isinstance(edges, Mapping):
        return 0.0
    negatives: list[float] = []
    for edge in edges.values():
        if not isinstance(edge, Mapping):
            continue
        kappa = edge.get("kappa", edge.get("curvature", 0.0))
        try:
            value = float(kappa)
        except (TypeError, ValueError):
            continue
        if value < 0.0:
            negatives.append(abs(value))
    return sum(negatives) / len(negatives) if negatives else 0.0


def _print_parallel_efficiency_matrix(gateway_profile: Mapping[str, Any]) -> None:
    legacy = gateway_profile.get("legacy_mode", {})
    gateway = gateway_profile.get("gateway_mode", {})
    delta = gateway_profile.get("efficiency_delta", {})
    if not legacy or not gateway:
        return

    print("=" * 80)
    print("PARALLEL EFFICIENCY MATRIX — WELD vs HANDOFF GATEWAY")
    print("=" * 80)
    print(f"{legacy.get('label', 'Legacy Mode')}")
    print(f"  Simulated Work Units          : {legacy.get('work_unit_count', 0)}")
    print(f"  Atomic Weld Blocks            : {legacy.get('atomic_weld_blocks', 0)}")
    largest = legacy.get("largest_atomic_weld_file_count", 0)
    if largest:
        print(f"  Largest Atomic Weld           : {largest} files (single-worker serialization)")
    print(f"  Max Safe Parallel Concurrency : {legacy.get('max_parallel_workers', 1)} workers")
    print("")
    env_flag = gateway.get("env_flag", "GAIJINN_HANDOFF_GATEWAYS=1")
    print(f"{gateway.get('label', 'Gateway Mode')} ({env_flag})")
    print(f"  Simulated Work Units          : {gateway.get('work_unit_count', 0)}")
    print(f"  Atomic Weld Blocks            : {gateway.get('atomic_weld_blocks', 0)}")
    floor = gateway_profile.get("curvature_hard_floor", CURVATURE_HARD_FLOOR)
    gateway_count = gateway.get("handoff_gateway_count", 0)
    print(f"  Handoff Gateways Mapped       : {gateway_count} (kappa <= {floor})")
    print(f"  Max Safe Parallel Concurrency : {gateway.get('max_parallel_workers', 1)} workers")
    print("-" * 80)
    blocks_eliminated = delta.get("atomic_weld_blocks_eliminated", 0)
    files_unlocked = delta.get("files_unlocked_from_atomic_welds", 0)
    worker_delta = delta.get("parallel_worker_delta", 0)
    if blocks_eliminated or gateway.get("handoff_gateway_count", 0):
        print("ECONOMIC ADVANTAGE (Gateway Mode)")
        if blocks_eliminated:
            print(f"  Atomic weld blocks eliminated : {blocks_eliminated}")
        if files_unlocked:
            print(f"  Files unlocked from welds     : {files_unlocked}")
        if worker_delta > 0:
            print(f"  Parallel worker velocity gain : +{worker_delta} workers")
        elif worker_delta < 0:
            print(f"  Parallel worker tradeoff      : {worker_delta} workers (handoff deps add merge gates)")
        if delta.get("gateway_recommended"):
            print(f"  Enable                        : export {env_flag}")
    else:
        print("[INFO] No dark-bridge atomic welds detected — gateway mode optional for this topology.")
    print("=" * 80)
    print("")


def print_brutalist_report(payload: Mapping[str, Any]) -> None:
    metrics = payload.get("metrics", {})
    governance = payload.get("governance_profile", {})
    gateway_profile = payload.get("handoff_gateway_profile", {})

    print("=" * 80)
    print("GAIJINN STRUCTURAL AUDIT REPORT -- REPOSITORY CONVERGENCE ASSURANCE")
    print("=" * 80)
    print(f"Target Dir : {payload.get('target_directory', '')}")
    print(f"Readiness  : {governance.get('readiness_tier', '')}")
    print(f"Action     : {governance.get('recommendation', '')}")
    print("-" * 80)
    print(f"Code Nodes Indexed            : {metrics.get('total_code_nodes', 0)}")
    gravity_floor = metrics.get("gravity_hard_floor", GRAVITY_HARD_FLOOR)
    global_gravity = metrics.get("global_gravity_score", 0)
    print(f"Global Structural Gravity     : {global_gravity:.4f} (Floor: {gravity_floor:.4f})")
    print(f"Shadow Bridges Detected       : {metrics.get('shadow_bridge_count', 0)}")
    print(f"Integrity Score               : {metrics.get('integrity_score', 0)}")
    print("=" * 80)
    print("")

    if gateway_profile:
        _print_parallel_efficiency_matrix(gateway_profile)

    print("-" * 80)
    print("CURRENT DEFAULT PLAN (Weld Mode Baseline)")
    print(f"  Simulated Work Units          : {metrics.get('work_unit_count', 0)}")
    print(f"  Max Safe Parallel Concurrency : {metrics.get('max_parallel_worker_capacity', 1)} workers")
    print("-" * 80)

    violations = governance.get("critical_violations", [])
    if violations:
        print("[CRITICAL BOUNDARY COLLAPSE RISK: SHADOW BRIDGES]")
        for violation in violations:
            print(f"  -> {violation}")
    else:
        print("[PASSED] Zero structural shadow bridges detected. Topology is cleanly decoupled.")
    print("=" * 80)
