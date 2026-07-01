"""Deterministic blueprint schema and work-unit generator.

GAIJINN BLUEPRINT — graph-based planner (brownfield / existing repos)
---------------------------------------------------------------------
Layer: CLI compose phase (gaijinn plan) — geometry-conditioned task isolation (DCOE)
Status: shipped — distinct from intent_blueprint.py (greenfield keyword streams)
Entry: generate_blueprint(graph, metrics, giv) after scan + analyze

Partitioning rules (compiler invariants):
  - Dark Bridge: directed edge with κ < CURVATURE_HARD_FLOOR (-0.3) — latent coupling weld
  - Surgery rule: Dark Bridge endpoints MUST share one WorkUnit (never parallel-split)
  - Contraction rule: subgraphs linked only by κ ≥ 0 edges MAY run concurrently
  - Stealth: forced serialization logs via helpers.stealth dark_bridge_* helpers

Used when: orchestrate prepare default path → gaijinn plan (greenfield + brownfield)
Not used when: Intent Forge executable_projection or GAIJINN_KEYWORD_GREENFIELD=1 legacy fallback

AI agents — DO
  - Preserve non-overlapping allowed_paths per WorkUnit
  - Keep validate_blueprint() passing before writing blueprint.json
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from .giv import GIV
from .gravity import CURVATURE_HARD_FLOOR

SCHEMA_VERSION = 1
RISK_LEVELS = ("low", "medium", "high")
DOMAIN_LEVELS = ("code", "vault")
VAULT_PATH_PREFIXES = (
    "00_Brain/",
    "10_Operations/",
    "20_Projects/",
    "30_Decisions/",
    "40_Concepts/",
    "raw/",
    "_multi-agent/",
    "pending/",
    ".agents/",
    "ui/",
    "aoc_supervisor/",
)


class BlueprintValidationError(ValueError):
    """Raised when a generated blueprint violates isolation constraints."""


@dataclass(frozen=True)
class WorkUnit:
    id: str
    title: str
    description: str
    allowed_paths: tuple[str, ...]
    denied_paths: tuple[str, ...] = field(default_factory=tuple)
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    acceptance_checks: tuple[str, ...] = field(default_factory=tuple)
    estimated_risk: str = "low"
    domain: str = "code"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _required_text(self.id, "work unit id"))
        object.__setattr__(self, "title", _required_text(self.title, "work unit title"))
        object.__setattr__(
            self,
            "description",
            _required_text(self.description, "work unit description"),
        )
        object.__setattr__(self, "allowed_paths", _normalize_paths(self.allowed_paths))
        object.__setattr__(self, "denied_paths", _normalize_paths(self.denied_paths))
        object.__setattr__(self, "depends_on", _normalize_items(self.depends_on))
        object.__setattr__(self, "acceptance_checks", _normalize_items(self.acceptance_checks))
        risk = str(self.estimated_risk).strip().lower()
        if risk not in RISK_LEVELS:
            raise BlueprintValidationError(f"unsupported estimated_risk {self.estimated_risk!r}")
        object.__setattr__(self, "estimated_risk", risk)
        domain = str(self.domain).strip().lower() or resolve_work_unit_domain(self.allowed_paths)
        if domain not in DOMAIN_LEVELS:
            raise BlueprintValidationError(f"unsupported domain {self.domain!r}")
        object.__setattr__(self, "domain", domain)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "allowed_paths": list(self.allowed_paths),
            "denied_paths": list(self.denied_paths),
            "depends_on": list(self.depends_on),
            "acceptance_checks": list(self.acceptance_checks),
            "estimated_risk": self.estimated_risk,
            "domain": self.domain,
        }


@dataclass(frozen=True)
class Blueprint:
    schema_version: int
    project_goal: str
    assumptions: tuple[str, ...]
    work_units: tuple[WorkUnit, ...]
    dependencies: dict[str, list[str]]
    risks: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise BlueprintValidationError(f"schema_version must be {SCHEMA_VERSION}; found {self.schema_version!r}")
        object.__setattr__(self, "project_goal", _required_text(self.project_goal, "project_goal"))
        object.__setattr__(self, "assumptions", _normalize_items(self.assumptions))
        object.__setattr__(self, "work_units", tuple(self.work_units))
        object.__setattr__(
            self,
            "dependencies",
            {str(key): sorted(str(item) for item in value) for key, value in sorted(self.dependencies.items())},
        )
        object.__setattr__(self, "risks", _normalize_items(self.risks))
        validate_blueprint(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_goal": self.project_goal,
            "assumptions": list(self.assumptions),
            "work_units": [unit.to_dict() for unit in self.work_units],
            "dependencies": self.dependencies,
            "risks": list(self.risks),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def dependencies_from_units(cls, work_units: Sequence[WorkUnit]) -> dict[str, list[str]]:
        """Build the canonical dependencies mapping from WorkUnit.depends_on."""
        return dependencies_from_work_units(work_units)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Blueprint:
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise BlueprintValidationError(
                f"unsupported schema_version {payload.get('schema_version')!r}; expected {SCHEMA_VERSION}"
            )
        raw_units = payload.get("work_units")
        if not isinstance(raw_units, Iterable) or isinstance(raw_units, (str, bytes)):
            raise BlueprintValidationError("work_units must be a sequence")
        units = tuple(_work_unit_from_dict(unit) for unit in raw_units)
        dependencies = payload.get("dependencies", {})
        if not isinstance(dependencies, Mapping):
            raise BlueprintValidationError("dependencies must be an object")
        return cls(
            schema_version=SCHEMA_VERSION,
            project_goal=_required_text(payload.get("project_goal", ""), "project_goal"),
            assumptions=_sequence(payload, "assumptions"),
            work_units=units,
            dependencies={
                str(key): [str(item) for item in _iter_sequence(value, f"dependencies.{key}")]
                for key, value in dependencies.items()
            },
            risks=_sequence(payload, "risks"),
        )

    def to_markdown(self) -> str:
        lines = [
            "# Gaijinn Blueprint",
            "",
            "## Project Goal",
            "",
            self.project_goal,
            "",
            "## Assumptions",
            *_bullet_lines(self.assumptions),
            "",
            "## Work Units",
            "",
        ]
        for unit in self.work_units:
            lines.extend(
                [
                    f"### {unit.id}: {unit.title}",
                    "",
                    unit.description,
                    "",
                    f"- Estimated risk: {unit.estimated_risk}",
                    f"- Allowed paths: {', '.join(unit.allowed_paths)}",
                    f"- Denied paths: {_inline_list(unit.denied_paths)}",
                    f"- Depends on: {_inline_list(unit.depends_on)}",
                    "- Acceptance checks:",
                    *_bullet_lines(unit.acceptance_checks),
                    "",
                ]
            )
        lines.extend(
            [
                "## Dependencies",
                *_dependency_lines(self.dependencies),
                "",
                "## Risks",
                *_bullet_lines(self.risks),
                "",
            ]
        )
        return "\n".join(lines)


def dependencies_from_work_units(work_units: Iterable[WorkUnit]) -> dict[str, list[str]]:
    """Build the canonical dependencies mapping from WorkUnit.depends_on."""
    return {unit.id: list(unit.depends_on) for unit in work_units}


def stable_work_unit_id(allowed_paths: Sequence[str], acceptance_checks: Sequence[str]) -> str:
    """Return the permanent content-addressed WU id for a path/check scope."""
    payload = json.dumps(
        {
            "allowed_paths": sorted(str(path).strip() for path in allowed_paths if str(path).strip()),
            "acceptance_checks": sorted(str(check).strip() for check in acceptance_checks if str(check).strip()),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"WU-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:8]}"


def resolve_work_unit_domain(allowed_paths: Sequence[str]) -> str:
    """Resolve a work-unit domain once from its allowed path prefixes."""
    from .helpers.project_profile import is_obsidian_vault

    normalized = [_normalize_path(str(path)) for path in allowed_paths]
    normalized = [path for path in normalized if path]
    if not normalized:
        raise BlueprintValidationError("work unit allowed_paths cannot be empty")
    if is_obsidian_vault(Path.cwd()):
        return "vault"
    vault = [_is_vault_path(path) for path in normalized]
    if all(vault):
        return "vault"
    if any(vault):
        raise BlueprintValidationError(f"work unit straddles vault and code paths: {', '.join(normalized)}")
    return "code"


def _is_vault_path(path: str) -> bool:
    normalized = path.rstrip("/")
    if not normalized:
        return False
    # Monorepo production packages at repository root are code, not vault mirror paths.
    if normalized.startswith(("aoc-cli/", "aoc_supervisor/")):
        return False
    if normalized.startswith("vaults/"):
        parts = normalized.split("/")
        if len(parts) >= 3:
            return _is_vault_path("/".join(parts[2:]))
        return False
    if normalized.endswith(".md") and "/" not in normalized:
        return True
    if normalized in _VAULT_ROOT_ARTIFACTS:
        return True
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in VAULT_PATH_PREFIXES)


_VAULT_ROOT_ARTIFACTS = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        "Current_Context.md",
        "metadata.json",
        "giv.json",
        "intent.txt",
        "WORKER_INTENT.txt",
    }
)


def handoff_gateway_mode_enabled() -> bool:
    """Return True when dark-bridge couplings become HANDOFF gateways instead of welds."""
    return os.environ.get("GAIJINN_HANDOFF_GATEWAYS", "").strip().lower() in {"1", "true", "yes"}


def handoff_gateway_records(metrics: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Dark-bridge edges (kappa <= floor) surfaced as auditor handoff gateways."""
    records: list[dict[str, Any]] = []
    for source, target in _dark_bridge_edges(metrics):
        kappa = _gateway_edge_kappa(metrics, source, target)
        records.append(
            {
                "source": source,
                "target": target,
                "kappa": round(kappa, 4),
                "gateway_type": "HANDOFF_ONLY",
            }
        )
    return records


def _create_initial_work_units(
    blocks: Iterable[frozenset[str]],
    nodes: Mapping[str, Mapping[str, Any]],
    node_risks: Mapping[str, str],
    giv_profile: GIV,
    graph: Mapping[str, Any],
) -> list[WorkUnit]:
    work_units: list[WorkUnit] = []
    grouped: dict[tuple[str, str, str], list[str]] = {}

    for block in blocks:
        if len(block) > 1:
            paths = tuple(sorted(block))
            work_units.append(_dark_bridge_block_work_unit(len(work_units) + 1, paths, giv_profile, node_risks))
            continue
        path = sorted(block)[0]
        node = nodes[path]
        key = (_directory(path), str(node.get("language") or "unknown"), node_risks[path])
        grouped.setdefault(key, []).append(path)

    for key, paths_list in _refine_grouped_blocks(grouped, graph):
        directory, language, risk = key
        paths = tuple(sorted(paths_list))
        work_units.append(_group_work_unit(len(work_units) + 1, directory, language, risk, paths, giv_profile))

    return work_units


def _build_blueprint_assumptions(
    gateway_mode: bool,
    serialization_events: list[tuple[str, str]],
) -> list[str]:
    from .helpers.stealth import dark_bridge_blueprint_assumption, stealth_mode

    if gateway_mode:
        geometry_assumption = (
            "Handoff gateway mode: dark-bridge couplings are HANDOFF_ONLY transaction boundaries, not atomic welds."
        )
    elif stealth_mode():
        geometry_assumption = (
            "Negative-curvature coupling welds are consolidated into atomic work units before parallel dispatch."
        )
    else:
        geometry_assumption = "Dark Bridge endpoints below the curvature hard floor are bound into atomic work units."

    assumptions = [
        "Work units are generated from the scanned graph, integrity preflight, and scope lock.",
        "Allowed paths are write scopes; workers may read broader project context as needed.",
        geometry_assumption,
    ]
    binding_note = dark_bridge_blueprint_assumption(len(serialization_events))
    if binding_note and not gateway_mode:
        assumptions.append(binding_note)

    return assumptions


def generate_blueprint(
    graph: Mapping[str, Any],
    metrics: Mapping[str, Any],
    giv: GIV | Mapping[str, Any],
    *,
    handoff_gateways: bool | None = None,
) -> Blueprint:
    """Generate geometry-conditioned work units from graph curvature, metrics, and GIV."""
    giv_profile = giv if isinstance(giv, GIV) else GIV.from_dict(giv)
    gateway_mode = handoff_gateway_mode_enabled() if handoff_gateways is None else handoff_gateways
    nodes = _graph_nodes(graph)
    dark_bridge_files = _dark_bridge_files(metrics)
    node_risks = {path: _node_risk(path, node, metrics, path in dark_bridge_files) for path, node in nodes.items()}

    dark_edges = _dark_bridge_edges(metrics)
    if gateway_mode:
        blocks = [frozenset({path}) for path in sorted(nodes.keys())]
        serialization_events: list[tuple[str, str]] = []
    else:
        blocks, serialization_events = _atomic_blocks(set(nodes.keys()), dark_edges)
    work_units = _create_initial_work_units(blocks, nodes, node_risks, giv_profile, graph)

    work_units, dependencies = _resolve_work_units_and_dependencies(
        work_units,
        graph,
        metrics,
        giv_profile,
        node_risks,
        handoff_gateways=gateway_mode,
    )

    risks = _risks(metrics, work_units, serialization_events, handoff_gateways=gateway_mode)
    assumptions = _build_blueprint_assumptions(gateway_mode, serialization_events)

    return Blueprint(
        schema_version=SCHEMA_VERSION,
        project_goal=_project_goal(giv_profile),
        assumptions=tuple(assumptions),
        work_units=tuple(work_units),
        dependencies=dependencies,
        risks=risks,
    )


def validate_blueprint(blueprint: Blueprint) -> None:
    ids = [unit.id for unit in blueprint.work_units]
    if len(ids) != len(set(ids)):
        raise BlueprintValidationError("work unit ids must be unique")

    id_set = set(ids)
    for unit in blueprint.work_units:
        resolved_domain = resolve_work_unit_domain(unit.allowed_paths)
        if unit.domain != resolved_domain:
            raise BlueprintValidationError(
                f"{unit.id} domain {unit.domain!r} does not match allowed_paths domain {resolved_domain!r}"
            )
        if not unit.acceptance_checks:
            raise BlueprintValidationError(f"{unit.id} acceptance_checks cannot be empty")
        for dependency in unit.depends_on:
            if dependency not in id_set:
                raise BlueprintValidationError(f"{unit.id} depends on unknown work unit {dependency!r}")

    for unit_id, depends_on in blueprint.dependencies.items():
        if unit_id not in id_set:
            raise BlueprintValidationError(f"dependencies references unknown work unit {unit_id!r}")
        for dependency in depends_on:
            if dependency not in id_set:
                raise BlueprintValidationError(f"{unit_id} dependencies references unknown work unit {dependency!r}")

    _assert_dependencies_aligned_with_work_units(blueprint)
    graph = _dependency_graph_from_mapping(blueprint.dependencies, ids)
    _validate_dependency_graph_acyclic(graph, ids)

    owners: dict[str, str] = {}
    for unit in blueprint.work_units:
        for allowed_path in unit.allowed_paths:
            for owned_path, owner in owners.items():
                if _paths_overlap(owned_path, allowed_path):
                    raise BlueprintValidationError(
                        f"overlapping write paths: {unit.id} {allowed_path!r} overlaps {owner} {owned_path!r}"
                    )
            owners[allowed_path] = unit.id


def _assert_dependencies_aligned_with_work_units(blueprint: Blueprint) -> None:
    """dependencies mapping is canonical; work unit depends_on must mirror it exactly."""
    for unit in blueprint.work_units:
        canonical = tuple(blueprint.dependencies.get(unit.id, ()))
        if unit.depends_on != canonical:
            raise BlueprintValidationError(
                f"{unit.id} depends_on {list(unit.depends_on)} diverges from dependencies {list(canonical)}"
            )


def _dependency_graph_from_mapping(
    dependencies: Mapping[str, Iterable[str]],
    unit_ids: Iterable[str],
) -> dict[str, set[str]]:
    graph = {unit_id: set() for unit_id in unit_ids}
    for unit_id, depends_on in dependencies.items():
        graph.setdefault(unit_id, set()).update(depends_on)
    return graph


def _find_dependency_cycle(graph: Mapping[str, set[str]], ids: Iterable[str]) -> list[str] | None:
    """Return the first dependency cycle found via iterative DFS, or None if acyclic."""
    white, gray, black = 0, 1, 2
    color: dict[str, int] = {unit_id: white for unit_id in ids}
    path: list[str] = []

    for start in ids:
        if color.get(start, white) == black:
            continue
        stack: list[tuple[str, int]] = [(start, 0)]
        while stack:
            node, child_idx = stack[-1]
            state = color.get(node, white)
            if state == white:
                color[node] = gray
                path.append(node)
            deps = sorted(graph.get(node, ()))
            if child_idx < len(deps):
                stack[-1] = (node, child_idx + 1)
                child = deps[child_idx]
                child_state = color.get(child, white)
                if child_state == gray:
                    cycle_start = path.index(child)
                    return [*path[cycle_start:], child]
                if child_state == white:
                    stack.append((child, 0))
                continue
            color[node] = black
            if path and path[-1] == node:
                path.pop()
            stack.pop()
    return None


def _validate_dependency_graph_acyclic(graph: Mapping[str, set[str]], ids: Iterable[str]) -> None:
    """Iterative DFS (gray/black) — safe for deep enterprise dependency chains."""
    cycle = _find_dependency_cycle(graph, ids)
    if cycle is not None:
        raise BlueprintValidationError(f"dependency cycle detected: {' -> '.join(cycle)}")


def _work_unit_from_dict(payload: Any) -> WorkUnit:
    if not isinstance(payload, Mapping):
        raise BlueprintValidationError("work unit must be an object")
    allowed_paths = _sequence(payload, "allowed_paths")
    return WorkUnit(
        id=_required_text(payload.get("id", ""), "work unit id"),
        title=_required_text(payload.get("title", ""), "work unit title"),
        description=_required_text(payload.get("description", ""), "work unit description"),
        allowed_paths=allowed_paths,
        denied_paths=_sequence(payload, "denied_paths"),
        depends_on=_sequence(payload, "depends_on"),
        acceptance_checks=_sequence(payload, "acceptance_checks"),
        estimated_risk=str(payload.get("estimated_risk", "low")),
        domain=str(payload.get("domain") or resolve_work_unit_domain(allowed_paths)),
    )


def _sequence(payload: Mapping[str, Any], key: str) -> tuple[Any, ...]:
    return tuple(_iter_sequence(payload.get(key, ()), key))


def _iter_sequence(value: Any, key: str) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise BlueprintValidationError(f"{key} must be a sequence")
    return tuple(value)


def _graph_nodes(graph: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    nodes: dict[str, Mapping[str, Any]] = {}
    for raw_node in graph.get("nodes", ()):
        if not isinstance(raw_node, Mapping):
            continue
        path = raw_node.get("path", raw_node.get("id", raw_node.get("name")))
        if path is None:
            continue
        normalized = _normalize_path(str(path))
        if normalized:
            nodes[normalized] = raw_node
    return dict(sorted(nodes.items()))


class _UnionFind:
    def __init__(self, items: Iterable[str]) -> None:
        self._parent = {item: item for item in items}

    def find(self, item: str) -> str:
        parent = self._parent[item]
        if parent != item:
            self._parent[item] = self.find(parent)
        return self._parent[item]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if root_left < root_right:
            self._parent[root_right] = root_left
        else:
            self._parent[root_left] = root_right

    def components(self) -> list[frozenset[str]]:
        buckets: dict[str, set[str]] = {}
        for item in sorted(self._parent):
            root = self.find(item)
            buckets.setdefault(root, set()).add(item)
        return [frozenset(bucket) for bucket in buckets.values()]


def _edge_kappa(raw_edge: Mapping[str, Any]) -> float:
    return _float_value(raw_edge.get("kappa", raw_edge.get("curvature", 0.0)), 0.0)


def _is_dark_bridge_edge(raw_edge: Mapping[str, Any]) -> bool:
    if raw_edge.get("is_dark_bridge") is True:
        return True
    kappa = _edge_kappa(raw_edge)
    if kappa < CURVATURE_HARD_FLOOR:
        return True
    return raw_edge.get("is_shadow_bridge") is True and kappa < 0.0


def _dark_bridge_edges(metrics: Mapping[str, Any]) -> list[tuple[str, str]]:
    curvature_meta = metrics.get("curvature_meta", {})
    pairs: list[tuple[str, str]] = []
    if not isinstance(curvature_meta, Mapping):
        return pairs

    seen: set[tuple[str, str]] = set()
    for raw_edge in curvature_meta.get("shadow_bridges", ()):
        if isinstance(raw_edge, Mapping) and _is_dark_bridge_edge(raw_edge):
            source = _normalize_path(str(raw_edge.get("source", "")))
            target = _normalize_path(str(raw_edge.get("target", "")))
            if source and target:
                key = (source, target) if source <= target else (target, source)
                if key not in seen:
                    seen.add(key)
                    pairs.append((source, target))

    edges = curvature_meta.get("edges", {})
    edge_values = edges.values() if isinstance(edges, Mapping) else ()
    for raw_edge in edge_values:
        if isinstance(raw_edge, Mapping) and _is_dark_bridge_edge(raw_edge):
            source = _normalize_path(str(raw_edge.get("source", "")))
            target = _normalize_path(str(raw_edge.get("target", "")))
            if source and target:
                key = (source, target) if source <= target else (target, source)
                if key not in seen:
                    seen.add(key)
                    pairs.append((source, target))
    return sorted(pairs)


def _dark_bridge_files(metrics: Mapping[str, Any]) -> set[str]:
    files: set[str] = set()
    for source, target in _dark_bridge_edges(metrics):
        files.update((source, target))
    return files


def _atomic_blocks(
    node_paths: set[str],
    dark_edges: list[tuple[str, str]],
) -> tuple[list[frozenset[str]], list[tuple[str, str]]]:
    from .helpers.stealth import dark_bridge_internal_log

    union = _UnionFind(node_paths)
    serialization_events: list[tuple[str, str]] = []
    for source, target in dark_edges:
        if source not in node_paths or target not in node_paths:
            continue
        if union.find(source) != union.find(target):
            union.union(source, target)
            serialization_events.append((source, target))
            _ = dark_bridge_internal_log(source, target)
    return sorted(union.components(), key=lambda block: sorted(block)[0]), serialization_events


def _node_risk(path: str, node: Mapping[str, Any], metrics: Mapping[str, Any], is_shadow: bool) -> str:
    if is_shadow:
        return "high"
    gravity_meta = metrics.get("gravity_meta", {})
    node_meta = {}
    if isinstance(gravity_meta, Mapping) and isinstance(gravity_meta.get("nodes"), Mapping):
        node_meta = gravity_meta["nodes"].get(path, {})
    gravity = _float_value(node_meta.get("gravity") if isinstance(node_meta, Mapping) else None, 1.0)
    rejected = bool(node_meta.get("automatic_rejection")) if isinstance(node_meta, Mapping) else False
    capability = _float_value(node.get("capability_level"), 0.0)
    side_effect = _float_value(node.get("side_effect_score"), 0.0)
    if rejected or gravity < 0.20 or capability >= 5.0 or side_effect >= 2.0:
        return "high"
    if gravity < 0.35 or capability >= 3.0 or side_effect >= 1.0:
        return "medium"
    return "low"


def _dark_bridge_block_work_unit(
    index: int,
    paths: tuple[str, ...],
    giv: GIV,
    node_risks: Mapping[str, str],
) -> WorkUnit:
    from .helpers.stealth import stealth_coupling_label, stealth_mode

    label = stealth_coupling_label()
    scope = ", ".join(paths)
    risk = "high" if any(node_risks.get(path) == "high" for path in paths) else "medium"
    if stealth_mode():
        title = f"Consolidate {label} block ({len(paths)} files)"
        description = (
            f"Geometry-conditioned atomic block: {label} weld binds {scope}. "
            "Execute sequentially on one worker with strict scope lock."
        )
    else:
        title = f"Dark Bridge atomic block ({len(paths)} files)"
        description = f"Negative curvature weld binds {scope}. Nodes cannot be split across parallel workers."
    return WorkUnit(
        id=f"WU-{index:03d}",
        title=title,
        description=description,
        allowed_paths=paths,
        denied_paths=_denied_paths(giv, paths),
        acceptance_checks=_acceptance_checks(giv, high_risk=risk == "high"),
        estimated_risk=risk,
        domain=resolve_work_unit_domain(paths),
    )


def _convex_hull_welding_threshold() -> int:
    return int(os.environ.get("GAIJINN_CONVEX_HULL_THRESHOLD", "12"))


def _refine_grouped_blocks(
    grouped: dict[tuple[str, str, str], list[str]], graph: Mapping[str, Any]
) -> list[tuple[tuple[str, str, str], list[str]]]:
    """Prevent Cascading Convex Hull Over-Welding by capping parallel group sizes while preserving cycles."""
    import networkx as nx

    refined: list[tuple[tuple[str, str, str], list[str]]] = []
    threshold = _convex_hull_welding_threshold()

    # Build a dependency graph of only the files in the current group
    group_edges = []
    for raw_edge in graph.get("edges", []):
        source, target = _edge_pair(raw_edge)
        if source and target:
            group_edges.append((source, target))

    for key, paths in sorted(grouped.items()):
        if len(paths) <= threshold:
            refined.append((key, paths))
            continue

        # Find Strongly Connected Components (SCCs) to avoid slicing cycles
        sub_g = nx.DiGraph()
        sub_g.add_nodes_from(paths)
        sub_g.add_edges_from([(s, t) for s, t in group_edges if s in paths and t in paths])

        # Deterministic SCC order: sort by the first node in each component
        sccs_raw = list(nx.strongly_connected_components(sub_g))
        sccs = sorted([sorted(list(scc)) for scc in sccs_raw], key=lambda x: x[0])

        current_chunk = []
        for scc in sccs:
            if len(current_chunk) + len(scc) > threshold and current_chunk:
                refined.append((key, current_chunk))
                current_chunk = list(scc)
            else:
                current_chunk.extend(scc)

        if current_chunk:
            refined.append((key, current_chunk))
    return refined


def _group_work_unit(
    index: int,
    directory: str,
    language: str,
    risk: str,
    paths: tuple[str, ...],
    giv: GIV,
) -> WorkUnit:
    title_scope = directory if directory != "." else "repository root"
    return WorkUnit(
        id=f"WU-{index:03d}",
        title=f"{language} {risk}-risk changes in {title_scope}",
        description=(
            f"Implement and validate the {language} files grouped by directory `{directory}` and risk `{risk}`."
        ),
        allowed_paths=paths,
        denied_paths=_denied_paths(giv, paths),
        acceptance_checks=_acceptance_checks(giv, high_risk=risk == "high"),
        estimated_risk=risk,
        domain=resolve_work_unit_domain(paths),
    )


def _gateway_edge_kappa(metrics: Mapping[str, Any], source: str, target: str) -> float:
    curvature_meta = metrics.get("curvature_meta", {})
    if not isinstance(curvature_meta, Mapping):
        return CURVATURE_HARD_FLOOR
    for raw_edge in curvature_meta.get("shadow_bridges", ()):
        if not isinstance(raw_edge, Mapping):
            continue
        edge_source = _normalize_path(str(raw_edge.get("source", "")))
        edge_target = _normalize_path(str(raw_edge.get("target", "")))
        if {edge_source, edge_target} == {source, target}:
            return _edge_kappa(raw_edge)
    edges = curvature_meta.get("edges", {})
    if isinstance(edges, Mapping):
        for raw_edge in edges.values():
            if not isinstance(raw_edge, Mapping):
                continue
            edge_source = _normalize_path(str(raw_edge.get("source", "")))
            edge_target = _normalize_path(str(raw_edge.get("target", "")))
            if edge_source == source and edge_target == target:
                return _edge_kappa(raw_edge)
    return CURVATURE_HARD_FLOOR


def _resolve_work_units_and_dependencies(
    work_units: list[WorkUnit],
    graph: Mapping[str, Any],
    metrics: Mapping[str, Any],
    giv: GIV,
    node_risks: Mapping[str, str],
    *,
    handoff_gateways: bool,
) -> tuple[list[WorkUnit], dict[str, list[str]]]:
    """Compute dependencies; weld cyclic participants into one atomic block until acyclic."""
    units = list(work_units)
    while True:
        dependencies = _dependencies(units, graph, metrics, handoff_gateways=handoff_gateways)
        units = _apply_dependencies_to_units(units, dependencies)
        unit_ids = [unit.id for unit in units]
        dep_graph = _dependency_graph_from_mapping(dependencies, unit_ids)
        cycle = _find_dependency_cycle(dep_graph, unit_ids)
        if cycle is None:
            return _renumber_work_units(units, dependencies)
        cycle_ids = set(cycle)
        units = _weld_cycle_work_units(units, cycle_ids, giv, node_risks)


def _renumber_work_units(
    work_units: list[WorkUnit],
    dependencies: Mapping[str, list[str]],
) -> tuple[list[WorkUnit], dict[str, list[str]]]:
    id_map = {unit.id: stable_work_unit_id(unit.allowed_paths, unit.acceptance_checks) for unit in work_units}
    units = [
        WorkUnit(
            id=id_map[unit.id],
            title=unit.title,
            description=unit.description,
            allowed_paths=unit.allowed_paths,
            denied_paths=unit.denied_paths,
            depends_on=tuple(
                id_map[dependency] for dependency in dependencies.get(unit.id, ()) if dependency in id_map
            ),
            acceptance_checks=unit.acceptance_checks,
            estimated_risk=unit.estimated_risk,
            domain=unit.domain,
        )
        for unit in work_units
    ]
    remapped = {
        id_map[unit_id]: sorted(id_map[dependency] for dependency in dep_list if dependency in id_map)
        for unit_id, dep_list in dependencies.items()
        if unit_id in id_map
    }
    return units, remapped


def _apply_dependencies_to_units(
    work_units: Iterable[WorkUnit],
    dependencies: Mapping[str, list[str]],
) -> list[WorkUnit]:
    return [
        WorkUnit(
            id=unit.id,
            title=unit.title,
            description=unit.description,
            allowed_paths=unit.allowed_paths,
            denied_paths=unit.denied_paths,
            depends_on=tuple(dependencies.get(unit.id, ())),
            acceptance_checks=unit.acceptance_checks,
            estimated_risk=unit.estimated_risk,
            domain=unit.domain,
        )
        for unit in work_units
    ]


def _weld_cycle_work_units(
    work_units: list[WorkUnit],
    cycle_ids: set[str],
    giv: GIV,
    node_risks: Mapping[str, str],
) -> list[WorkUnit]:
    """Merge work units participating in a dependency cycle into one serialized block."""
    cycle_units = [unit for unit in work_units if unit.id in cycle_ids]
    remaining = [unit for unit in work_units if unit.id not in cycle_ids]
    if not cycle_units:
        return work_units
    paths = tuple(sorted({path for unit in cycle_units for path in unit.allowed_paths}))
    welded = _cycle_weld_work_unit(_next_work_unit_index(work_units), paths, giv, node_risks, len(cycle_units))
    return remaining + [welded]


def _next_work_unit_index(work_units: Iterable[WorkUnit]) -> int:
    highest = 0
    for unit in work_units:
        unit_id = str(unit.id)
        if not unit_id.startswith("WU-"):
            continue
        try:
            highest = max(highest, int(unit_id.removeprefix("WU-")))
        except ValueError:
            continue
    return highest + 1


def _cycle_weld_work_unit(
    index: int,
    paths: tuple[str, ...],
    giv: GIV,
    node_risks: Mapping[str, str],
    cycle_size: int,
) -> WorkUnit:
    risk = "high" if any(node_risks.get(path) == "high" for path in paths) else "medium"
    return WorkUnit(
        id=f"WU-{index:03d}",
        title=f"Dependency cycle atomic block ({len(paths)} files)",
        description=(
            f"Import-cycle weld binds {cycle_size} work units and {len(paths)} file(s). "
            "Cycle-participating paths must execute on one worker."
        ),
        allowed_paths=paths,
        denied_paths=_denied_paths(giv, paths),
        acceptance_checks=_acceptance_checks(giv, high_risk=risk == "high"),
        estimated_risk=risk,
        domain=resolve_work_unit_domain(paths),
    )


def _dependencies(
    work_units: Iterable[WorkUnit],
    graph: Mapping[str, Any],
    metrics: Mapping[str, Any] | None = None,
    *,
    handoff_gateways: bool = False,
) -> dict[str, list[str]]:
    units = tuple(work_units)
    owner_by_path = {path: unit.id for unit in units for path in unit.allowed_paths}
    dependencies = {unit.id: set() for unit in units}
    dark_pairs = {(source, target) for source, target in (_dark_bridge_edges(metrics or {}) if metrics else [])}
    curvature_meta = metrics.get("curvature_meta", {}) if isinstance(metrics, Mapping) else {}
    edge_meta_by_pair: dict[tuple[str, str], Mapping[str, Any]] = {}
    edges = curvature_meta.get("edges", {}) if isinstance(curvature_meta, Mapping) else {}
    if isinstance(edges, Mapping):
        for raw_edge in edges.values():
            if isinstance(raw_edge, Mapping):
                source = _normalize_path(str(raw_edge.get("source", "")))
                target = _normalize_path(str(raw_edge.get("target", "")))
                if source and target:
                    edge_meta_by_pair[(source, target)] = raw_edge

    for raw_edge in graph.get("edges", ()):
        source, target = _edge_pair(raw_edge)
        if not source or not target:
            continue
        if (source, target) in dark_pairs:
            if handoff_gateways:
                source_owner = owner_by_path.get(source)
                target_owner = owner_by_path.get(target)
                if source_owner and target_owner and source_owner != target_owner:
                    dependencies[source_owner].add(target_owner)
            continue
        edge_meta = edge_meta_by_pair.get((source, target), {})
        if isinstance(edge_meta, Mapping) and _edge_kappa(edge_meta) < 0.0:
            continue
        source_owner = owner_by_path.get(source)
        target_owner = owner_by_path.get(target)
        if source_owner and target_owner and source_owner != target_owner:
            dependencies[source_owner].add(target_owner)
    result = {unit_id: sorted(values) for unit_id, values in sorted(dependencies.items())}
    return result


def _edge_pair(raw_edge: Any) -> tuple[str, str]:
    if isinstance(raw_edge, Mapping):
        return (
            _normalize_path(str(raw_edge.get("source", raw_edge.get("from", raw_edge.get("u", ""))))),
            _normalize_path(str(raw_edge.get("target", raw_edge.get("to", raw_edge.get("v", ""))))),
        )
    if isinstance(raw_edge, Iterable) and not isinstance(raw_edge, (str, bytes)):
        values = list(raw_edge)
        if len(values) >= 2:
            return _normalize_path(str(values[0])), _normalize_path(str(values[1]))
    return "", ""


def _risks(
    metrics: Mapping[str, Any],
    work_units: Iterable[WorkUnit],
    serialization_events: Iterable[tuple[str, str]] | None = None,
    *,
    handoff_gateways: bool = False,
) -> tuple[str, ...]:
    from .helpers.stealth import dark_bridge_internal_log, dark_bridge_user_log, stealth_mode

    risks = {f"{unit.id}: estimated {unit.estimated_risk} risk" for unit in work_units if unit.estimated_risk != "low"}
    dark_count = len(_dark_bridge_edges(metrics))
    if dark_count > 0:
        if handoff_gateways:
            for source, target in _dark_bridge_edges(metrics):
                kappa = _gateway_edge_kappa(metrics, source, target)
                risks.add(
                    f"Handoff gateway: {source} -> {target} (kappa={kappa:.4f}) — emit HANDOFF ticket, do not weld"
                )
        elif stealth_mode():
            risks.add(dark_bridge_user_log())
        else:
            risks.add(f"{dark_count} Dark Bridge edge(s) forced atomic work-unit binding")
    if serialization_events and not stealth_mode():
        for source, target in serialization_events:
            risks.add(dark_bridge_internal_log(source, target))
    curvature_meta = metrics.get("curvature_meta", {})
    if isinstance(curvature_meta, Mapping) and int(curvature_meta.get("shadow_bridge_count", 0) or 0) > 0:
        label = "coupling review" if stealth_mode() else "Shadow Bridge"
        risks.add(f"{curvature_meta.get('shadow_bridge_count')} {label} edge(s) detected in preflight")
    gravity_meta = metrics.get("gravity_meta", {})
    if isinstance(gravity_meta, Mapping) and gravity_meta.get("automatic_rejection"):
        risks.add("One or more graph nodes are below the gravity hard floor")
    return tuple(sorted(risks)) or ("No elevated graph risks detected.",)


def _project_goal(giv: GIV) -> str:
    capabilities = ", ".join(giv.capabilities) if giv.capabilities else "general implementation"
    return f"Deliver isolated work units for {capabilities} while preserving GIV invariants."


def _denied_paths(giv: GIV, allowed_paths: tuple[str, ...]) -> tuple[str, ...]:
    denied = set(giv.denied_paths)
    for path in giv.allowed_paths:
        normalized = _normalize_path(path)
        if normalized and normalized not in allowed_paths and normalized != ".":
            denied.add(normalized)
    return tuple(sorted(denied))


def _acceptance_checks(giv: GIV, *, high_risk: bool) -> tuple[str, ...]:
    from .helpers.project_profile import is_obsidian_vault

    if is_obsidian_vault(Path.cwd()):
        checks: set[str] = {"vault_linter"}
    else:
        checks = {"pytest"}
        checks.update(command for command in giv.allowed_commands if command.startswith(("pytest", "ruff", "mypy")))
    if high_risk:
        checks.add("review metrics manifest for rejected nodes or Shadow Bridges")
    return tuple(sorted(checks))


def _directory(path: str) -> str:
    parent = PurePosixPath(path).parent.as_posix()
    return parent if parent != "." else "."


def _normalize_items(items: Iterable[Any]) -> tuple[str, ...]:
    return tuple(sorted({str(item).strip() for item in items if str(item).strip()}))


def _normalize_paths(paths: Iterable[Any]) -> tuple[str, ...]:
    normalized = {_normalize_path(str(path)) for path in paths}
    return tuple(sorted(path for path in normalized if path))


def _normalize_path(path: str) -> str:
    value = path.strip().replace("\\", "/")
    if not value:
        return ""
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        return ""
    return pure.as_posix()


def _required_text(value: Any, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise BlueprintValidationError(f"{field_name} is required")
    return text


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _paths_overlap(left: str, right: str) -> bool:
    left_parts = PurePosixPath(left).parts
    right_parts = PurePosixPath(right).parts
    return (
        left_parts == right_parts
        or left_parts == right_parts[: len(left_parts)]
        or right_parts == left_parts[: len(right_parts)]
    )


def _bullet_lines(items: Iterable[str]) -> list[str]:
    values = list(items)
    if not values:
        return ["- none"]
    return [f"- {item}" for item in values]


def _dependency_lines(dependencies: Mapping[str, list[str]]) -> list[str]:
    if not dependencies:
        return ["- none"]
    return [f"- {unit_id}: {_inline_list(depends_on)}" for unit_id, depends_on in sorted(dependencies.items())]


def _inline_list(items: Iterable[str]) -> str:
    values = list(items)
    return ", ".join(values) if values else "none"


__all__ = [
    "Blueprint",
    "BlueprintValidationError",
    "WorkUnit",
    "generate_blueprint",
    "resolve_work_unit_domain",
    "stable_work_unit_id",
    "validate_blueprint",
]
