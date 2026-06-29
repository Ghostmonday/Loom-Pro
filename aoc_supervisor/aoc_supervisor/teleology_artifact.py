"""LOOM C22 — Teleology Artifact Emitter.

Builds and persists the canonical ``teleology.json`` truth artifact from
Intent Forge session state when forge handoff is confirmed.

Layer 1 — Teleology truth: WHY + WHAT.
Source data for curvature analysis and Loom map generation (C23).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _ns_id(base: str) -> str:
    """Normalize a capability id to dotted-namespace form.

    Ensures ids like ``prepare``, ``spawn``, ``merge`` are valid
    dot-namespaced identifiers per the schema pattern ``^[a-z][a-z0-9_.]*$``.
    """
    result = base.lower().replace("-", "_").replace(" ", "_").replace(":", ".").strip(".")
    if result and not result[0].isalpha():
        result = "cap_" + result
    return result


def build_teleology_artifact(state: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical teleology truth artifact from forge session state.

    Parameters
    ----------
    state
        The Intent Forge session state dict (after handoff confirm has
        compiled the rich artifact and executable projection).

    Returns
    -------
    dict
        Teleology artifact conforming to ``teleology-output.schema.json``.
    """
    session_id = str(state.get("session_id", ""))

    # ---- goal (str) ----
    goal = str(state.get("original_prompt", "")).strip()
    if not goal and isinstance(state.get("artifact"), dict):
        goal = str(state["artifact"].get("product_definition", "")).strip()

    # ---- constraints (list[str]) ----
    constraints: list[str] = _gather_constraints(state)

    # ---- success_criteria (list[str]) ----
    success_criteria: list[str] = _gather_success_criteria(state)

    # ---- domains (list[str]) ----
    domains: list[str] = _gather_domains(state)

    # ---- required_capabilities (list[dict]) ----
    required_capabilities: list[dict[str, Any]] = _derive_capabilities(state)

    # ---- invariants (list[dict]) ----
    invariants: list[dict[str, Any]] = _gather_invariants(state)

    # ---- states (list[str]) ----
    states: list[str] = _gather_states(state)

    # ---- evidence (dict) ----
    evidence: dict[str, Any] = {
        "forge_prompt": goal,
        "questions_answered": sum(
            1 for qa in state.get("questions_and_answers", []) if isinstance(qa, dict) and qa.get("answer", "").strip()
        ),
        "handoff_at": str(state.get("finalized_at", "") or state.get("updated_at", "")),
    }

    artifact: dict[str, Any] = {
        "schema_version": 1,
        "session_id": session_id,
        "goal": goal or "Unspecified goal",
        "constraints": constraints or ["No explicit constraints recorded"],
        "success_criteria": success_criteria or ["No explicit success criteria recorded"],
        "domains": domains or ["general"],
        "required_capabilities": required_capabilities or [{"id": "prepare", "description": "Foundation preparation"}],
        "invariants": invariants,
        "states": states,
        "evidence": evidence,
    }

    if isinstance(state.get("artifact"), dict):
        mode = state["artifact"].get("validation", {}).get("status", "")
        if mode:
            artifact["session_kind"] = _infer_session_kind(state, mode)

    return artifact


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _gather_constraints(state: dict[str, Any]) -> list[str]:
    """Extract constraint-like statements from forge state."""
    out: list[str] = []

    # Direct constraints from state
    for item in state.get("constraints", []):
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and item.get("text"):
            out.append(str(item["text"]))

    # Non-goals often encode constraints
    for ng in state.get("non_goals", []):
        text = ng.get("text") if isinstance(ng, dict) else str(ng)
        if text:
            out.append(f"Non-goal: {text}")

    # Security/privacy domain coverage implies infra constraints
    privacy = state.get("domain_coverage", {}).get("security_privacy", {})
    if isinstance(privacy, dict) and privacy.get("addressed"):
        out.append("Security and privacy requirements must be met")

    return out


def _gather_success_criteria(state: dict[str, Any]) -> list[str]:
    """Extract acceptance / success criteria from forge state."""
    out: list[str] = []

    for ac in state.get("acceptance_criteria", []):
        text = ac.get("text") if isinstance(ac, dict) else str(ac)
        if text:
            out.append(text)

    covered = state.get("domain_coverage", {})
    if isinstance(covered, dict):
        addressed = [d for d, m in covered.items() if isinstance(m, dict) and m.get("addressed")]
        if addressed:
            out.append(f"Domains covered: {', '.join(sorted(addressed))}")

    return out


def _gather_domains(state: dict[str, Any]) -> list[str]:
    """Extract domain labels from the forge session."""
    covered = state.get("domain_coverage", {})
    if isinstance(covered, dict):
        return sorted(d for d, m in covered.items() if isinstance(m, dict) and m.get("addressed"))
    return []


def _derive_capabilities(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive required capabilities from the executable projection work units.

    Capability ids are normalized to dotted-namespace form.
    """
    capabilities: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    projection = state.get("executable_projection")
    if isinstance(projection, dict):
        for wu in projection.get("work_units", []):
            if not isinstance(wu, dict):
                continue
            label = str(wu.get("title", "") or wu.get("label", "") or "").strip()
            wu_id = str(wu.get("id", "") or "").strip()
            if not label and not wu_id:
                continue
            cap_id = _ns_id(wu_id or label)
            if cap_id in seen_ids:
                continue
            seen_ids.add(cap_id)
            depends: list[str] = []
            raw_deps = wu.get("depends_on", [])
            if isinstance(raw_deps, (list, tuple)):
                for dep in raw_deps:
                    d = _ns_id(str(dep).strip())
                    if d and d != cap_id:
                        depends.append(d)
            capabilities.append(
                {
                    "id": cap_id,
                    "description": label or f"Capability {cap_id}",
                    "depends_on": depends or None,
                }
            )

    # If projection had no work units, derive from confirmed requirements
    if not capabilities:
        for req in state.get("confirmed_requirements", []):
            if not isinstance(req, dict):
                continue
            text = str(req.get("text", "")).strip()
            domain = str(req.get("domain", "")).strip() or "functional_requirements"
            cap_id = _ns_id(domain)
            if cap_id not in seen_ids:
                seen_ids.add(cap_id)
                capabilities.append(
                    {
                        "id": cap_id,
                        "description": text[:120] or f"Requirement from {domain}",
                    }
                )

    return capabilities


def _gather_invariants(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract invariant-level statements (must-always-true rules)."""
    invariants: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in state.get("assumptions", []):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        risk = str(item.get("risk_if_wrong", "")).strip()
        if text and text not in seen:
            seen.add(text)
            entry: dict[str, Any] = {
                "id": _ns_id(text[:32]),
                "statement": text,
            }
            if risk:
                entry["forbid"] = risk
            invariants.append(entry)

    return invariants


def _gather_states(state: dict[str, Any]) -> list[str]:
    """Extract lifecycle phases / states from session and pipeline plan."""
    phases: list[str] = []

    projection = state.get("executable_projection")
    if isinstance(projection, dict):
        plan = projection.get("pipeline_plan") if isinstance(projection.get("pipeline_plan"), dict) else None
        if plan:
            for ph in plan.get("phases", []):
                if isinstance(ph, str) and ph.strip():
                    phases.append(ph.strip())

    if not phases:
        statuses = ("CREATED", "QUESTIONING", "VALIDATING", "FINALIZED", "HANDED_OFF")
        seen = set()
        for s in statuses:
            seen.add(s)
        phases = [s for s in statuses if s in seen]

    return phases


def _infer_session_kind(state: dict[str, Any], mode: str) -> str:
    """Infer session kind from state context."""
    tier = str(state.get("tier", "paid"))
    if tier == "free":
        return "genesis"
    return "continuation"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def _sessions_root(host_root: Path) -> Path:
    """Resolve the canonical sessions directory under host_root."""
    return host_root.resolve() / ".gaijinn" / "sessions"


def teleology_path(host_root: Path, session_id: str) -> Path:
    """Return the filesystem path for ``teleology.json`` of *session_id*."""
    return _sessions_root(host_root) / session_id / "teleology.json"


def write_teleology_artifact(host_root: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Build and atomically write the teleology artifact to disk.

    The file is written to ``.gaijinn/sessions/{session_id}/teleology.json``
    using atomic replace.

    Returns the built teleology dict.
    """
    artifact = build_teleology_artifact(state)
    session_id = str(state.get("session_id", ""))
    path = teleology_path(host_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=".teleology.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(artifact, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return artifact


def validate_teleology_artifact(artifact: dict[str, Any]) -> list[str]:
    """Validate a teleology artifact against the schema contract.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    required = {"goal", "constraints", "success_criteria", "domains", "required_capabilities", "invariants"}

    for key in required:
        if key not in artifact:
            errors.append(f"missing required key: {key}")

    if "session_id" not in artifact:
        errors.append("missing required key: session_id")
    if "schema_version" not in artifact:
        errors.append("missing required key: schema_version")

    if "schema_version" in artifact and artifact["schema_version"] != 1:
        errors.append(f"schema_version must be 1, got {artifact['schema_version']}")

    if "required_capabilities" in artifact:
        caps = artifact["required_capabilities"]
        if not isinstance(caps, list) or len(caps) < 1:
            errors.append("required_capabilities must be a non-empty list")
        else:
            for i, cap in enumerate(caps):
                if not isinstance(cap, dict):
                    errors.append(f"required_capabilities[{i}] must be an object")
                    continue
                if "id" not in cap:
                    errors.append(f"required_capabilities[{i}] missing id")
                elif not isinstance(cap["id"], str) or len(cap["id"]) == 0:
                    errors.append(f"required_capabilities[{i}].id must be a non-empty string")
                else:
                    import re

                    if not re.match(r"^[a-z][a-z0-9_.]*$", cap["id"]):
                        errors.append(f"required_capabilities[{i}].id {cap['id']!r} must match ^[a-z][a-z0-9_.]*$")
                if "description" not in cap:
                    errors.append(f"required_capabilities[{i}] missing description")

    return errors
