"""Intent Forge validation and artifact compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aoc_supervisor.claims_ledger import build_claim_ledger
from aoc_supervisor.intent_blueprint_state import REQUIRED_DOMAINS
from aoc_supervisor.workstream_planner import project_executable_blueprint


@dataclass
class ValidationResult:
    ok: bool
    blocking_items: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_blueprint_state(state: dict[str, Any], *, finalize: bool = False) -> ValidationResult:
    blocking: list[str] = []
    warnings: list[str] = []

    unresolved = [item for item in state.get("unresolved_items", []) if isinstance(item, dict) and item.get("blocking")]
    if unresolved:
        blocking.append(f"{len(unresolved)} blocking unresolved items remain")

    contradictions = [
        item for item in state.get("contradictions", []) if isinstance(item, dict) and not item.get("resolved")
    ]
    if contradictions:
        blocking.append(f"{len(contradictions)} unresolved contradictions remain")

    stale_nodes = [
        node
        for node in state.get("blueprint_graph", {}).get("nodes", [])
        if isinstance(node, dict) and node.get("stale")
    ]
    if stale_nodes and finalize:
        blocking.append(f"{len(stale_nodes)} stale graph nodes remain")

    coverage = state.get("domain_coverage", {})
    confidence = state.get("confidence_by_domain", {})
    thresholds = state.get("confidence_threshold", {})
    for domain in REQUIRED_DOMAINS:
        meta = coverage.get(domain, {}) if isinstance(coverage, dict) else {}
        if isinstance(meta, dict) and meta.get("na"):
            continue
        if isinstance(meta, dict) and not meta.get("addressed") and finalize:
            blocking.append(f"domain not addressed: {domain}")
        threshold = float(thresholds.get(domain, 0.65) if isinstance(thresholds, dict) else 0.65)
        score = float(confidence.get(domain, 0.0) if isinstance(confidence, dict) else 0.0)
        if finalize and score < threshold:
            blocking.append(f"domain confidence below threshold: {domain}")

    if not state.get("confirmed_requirements") and finalize:
        warnings.append("no confirmed requirements recorded")

    return ValidationResult(ok=not blocking, blocking_items=blocking, warnings=warnings)


def compile_rich_artifact(state: dict[str, Any], *, provisional: bool = False) -> dict[str, Any]:
    intent = str(state.get("original_prompt", "")).strip()
    claims_ledger = build_claim_ledger(state)
    return {
        "schema_version": 1,
        "provisional": provisional,
        "session_id": state.get("session_id"),
        "blueprint_version": state.get("blueprint_version"),
        "product_definition": intent,
        "confirmed_requirements": state.get("confirmed_requirements", []),
        "inferred_requirements": state.get("inferred_requirements", []),
        "decisions": state.get("decisions", []),
        "assumptions": state.get("assumptions", []),
        "non_goals": state.get("non_goals", []),
        "deferred_items": state.get("deferred_items", []),
        "risks": state.get("risks", []),
        "acceptance_criteria": state.get("acceptance_criteria", []),
        "domain_coverage": state.get("domain_coverage", {}),
        "confidence_by_domain": state.get("confidence_by_domain", {}),
        "dependency_graph": state.get("blueprint_graph", {}),
        "claims_ledger": claims_ledger,
        "forced_finalization": state.get("forced_finalization"),
        "validation": {
            "status": "provisional" if provisional else "complete",
            "readiness": "unverified" if provisional else "verified",
        },
    }


def compile_executable_projection(state: dict[str, Any]) -> dict[str, Any]:
    artifact = state.get("artifact") if isinstance(state.get("artifact"), dict) else None
    intent = str(state.get("original_prompt", "")).strip()
    return project_executable_blueprint(
        intent=intent,
        artifact=artifact,
        session_state={**state, "claims_ledger": build_claim_ledger(state)},
    )
