"""Deterministic Loom map draft generation from teleology and topology."""

from __future__ import annotations

import heapq
import re
from collections.abc import Mapping, Sequence
from typing import Any


def generate_map_draft(teleology: dict, topology: dict) -> dict:
    """Return Loom contract fragments derived from layer 1 and layer 2 artifacts.

    Teleology owns capability definitions and dependencies. Topology supplies
    stable structural placement and breaks ties between otherwise independent
    capabilities.
    """
    if not isinstance(teleology, Mapping) or not isinstance(topology, Mapping):
        raise TypeError("teleology and topology must be mappings")

    teleology_session = str(teleology.get("session_id", "")).strip()
    topology_session = str(topology.get("session_id", "")).strip()
    if teleology_session and topology_session and teleology_session != topology_session:
        raise ValueError("teleology and topology session_id values must match")

    capabilities = _capabilities(teleology)
    structural_rank = _structural_rank(topology, capabilities)
    ordered_ids = _topological_order(capabilities, structural_rank)
    placements = _placements(topology)

    actions = {
        capability_id: {
            "description": capabilities[capability_id]["description"],
            "depends_on": list(capabilities[capability_id]["depends_on"]),
            "topology": placements.get(
                capability_id,
                {"cluster_ids": [], "work_unit_ids": []},
            ),
            "algorithm_binding": {
                "module": "unbound",
                "entrypoint": "unbound",
                "mode": "spec_only",
                "gap": (
                    f"Capability {capability_id!r} has no runtime entrypoint; "
                    "wire the C05-C08 implementation before execution."
                ),
            },
        }
        for capability_id in ordered_ids
    }

    flow = [
        {
            "order": index,
            "action": capability_id,
            "depends_on": list(capabilities[capability_id]["depends_on"]),
        }
        for index, capability_id in enumerate(ordered_ids, start=1)
    ]

    smoke_scenarios = [
        {
            "id": f"success.{index:03d}",
            "description": str(criterion),
            "assertions": [str(criterion)],
            "implementation_status": "spec_only",
        }
        for index, criterion in enumerate(
            _string_sequence(teleology.get("success_criteria"), "success_criteria"),
            start=1,
        )
    ]

    states = _deduplicated(_string_sequence(teleology.get("states", []), "states"))
    transitions = [
        {
            "from": source,
            "action": f"state.advance.{_identifier(target)}",
            "to": target,
        }
        for source, target in zip(states, states[1:])
    ]

    return {
        "actions": actions,
        "flow": flow,
        "smoke_scenarios": smoke_scenarios,
        "state_machine": {"transitions": transitions},
    }


def _capabilities(teleology: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    raw_capabilities = teleology.get("required_capabilities")
    if not isinstance(raw_capabilities, list) or not raw_capabilities:
        raise ValueError("teleology.required_capabilities must be a non-empty list")

    capabilities: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(raw_capabilities):
        if not isinstance(raw, Mapping):
            raise ValueError(f"required_capabilities[{index}] must be an object")
        capability_id = str(raw.get("id", "")).strip()
        if not capability_id:
            raise ValueError(f"required_capabilities[{index}].id is required")
        if capability_id in capabilities:
            raise ValueError(f"duplicate capability id: {capability_id}")
        description = str(raw.get("description", "")).strip()
        raw_dependencies = raw.get("depends_on")
        dependencies = _deduplicated(
            _string_sequence(
                [] if raw_dependencies is None else raw_dependencies,
                f"{capability_id}.depends_on",
            )
        )
        capabilities[capability_id] = {
            "description": description,
            "depends_on": tuple(dependencies),
            "source_index": index,
        }

    known_ids = set(capabilities)
    for capability_id, capability in capabilities.items():
        unknown = [dep for dep in capability["depends_on"] if dep not in known_ids]
        if unknown:
            raise ValueError(f"capability {capability_id!r} depends on unknown capabilities: {unknown}")
        if capability_id in capability["depends_on"]:
            raise ValueError(f"capability {capability_id!r} cannot depend on itself")
    return capabilities


def _structural_rank(
    topology: Mapping[str, Any],
    capabilities: Mapping[str, Mapping[str, Any]],
) -> dict[str, tuple[int, int]]:
    ordered: list[str] = []
    clusters = topology.get("clusters", [])
    if isinstance(clusters, list):
        for cluster in clusters:
            if isinstance(cluster, Mapping):
                node_ids = cluster.get("node_ids", [])
                if isinstance(node_ids, list):
                    ordered.extend(str(node_id) for node_id in node_ids)

    work_units = topology.get("work_units", [])
    if isinstance(work_units, list):
        for work_unit in work_units:
            if isinstance(work_unit, Mapping):
                ordered.append(str(work_unit.get("id", "")))

    topology_index: dict[str, int] = {}
    for item in ordered:
        if item in capabilities and item not in topology_index:
            topology_index[item] = len(topology_index)

    fallback = len(topology_index)
    return {
        capability_id: (
            topology_index.get(capability_id, fallback + int(capability["source_index"])),
            int(capability["source_index"]),
        )
        for capability_id, capability in capabilities.items()
    }


def _topological_order(
    capabilities: Mapping[str, Mapping[str, Any]],
    structural_rank: Mapping[str, tuple[int, int]],
) -> list[str]:
    indegree = {capability_id: len(capability["depends_on"]) for capability_id, capability in capabilities.items()}
    dependents = {capability_id: [] for capability_id in capabilities}
    for capability_id, capability in capabilities.items():
        for dependency in capability["depends_on"]:
            dependents[dependency].append(capability_id)

    ready = [
        (structural_rank[capability_id], capability_id) for capability_id, degree in indegree.items() if degree == 0
    ]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        _rank, capability_id = heapq.heappop(ready)
        ordered.append(capability_id)
        for dependent in dependents[capability_id]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(
                    ready,
                    (structural_rank[dependent], dependent),
                )

    if len(ordered) != len(capabilities):
        cyclic = sorted(capability_id for capability_id, degree in indegree.items() if degree)
        raise ValueError(f"capability dependency cycle detected: {cyclic}")
    return ordered


def _placements(topology: Mapping[str, Any]) -> dict[str, dict[str, list[str]]]:
    placements: dict[str, dict[str, list[str]]] = {}
    clusters = topology.get("clusters", [])
    if isinstance(clusters, list):
        for cluster in clusters:
            if not isinstance(cluster, Mapping):
                continue
            cluster_id = str(cluster.get("id", "")).strip()
            node_ids = cluster.get("node_ids", [])
            if not cluster_id or not isinstance(node_ids, list):
                continue
            for node_id in node_ids:
                placement = placements.setdefault(str(node_id), {"cluster_ids": [], "work_unit_ids": []})
                placement["cluster_ids"].append(cluster_id)

    work_units = topology.get("work_units", [])
    if isinstance(work_units, list):
        for work_unit in work_units:
            if not isinstance(work_unit, Mapping):
                continue
            work_unit_id = str(work_unit.get("id", "")).strip()
            if not work_unit_id:
                continue
            placement = placements.setdefault(work_unit_id, {"cluster_ids": [], "work_unit_ids": []})
            placement["work_unit_ids"].append(work_unit_id)

    for placement in placements.values():
        placement["cluster_ids"] = _deduplicated(placement["cluster_ids"])
        placement["work_unit_ids"] = _deduplicated(placement["work_unit_ids"])
    return placements


def _string_sequence(value: Any, field: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be a list of strings")
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{index}] must be a non-empty string")
        result.append(item.strip())
    return result


def _deduplicated(items: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _identifier(value: str) -> str:
    identifier = re.sub(r"[^a-z0-9_.]+", "_", value.strip().lower())
    return identifier.strip("_.") or "state"
