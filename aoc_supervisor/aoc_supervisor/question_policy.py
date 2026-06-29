"""Impact-ranked question selection and stopping rules for Intent Forge."""

from __future__ import annotations

from typing import Any

from aoc_supervisor.adaptive_question_engine import (
    AdaptiveQuestionEngine,
    get_analysis_recovery,
    get_default_engine,
)
from aoc_supervisor.intent_blueprint_state import REQUIRED_DOMAINS, new_element_id, new_question_id
from aoc_supervisor.reasoning_provider import ProviderFailureError

# Descriptive reference prompts for telemetry and compiled artifacts only.
# Production questioning MUST NOT select from this table.
DOMAIN_PROMPTS: dict[str, str] = {
    "product_scope": "What is the primary product goal and what is explicitly out of scope for V1?",
    "target_users": "Who are the primary user roles and what permissions should each role have?",
    "user_journeys": "Describe the critical user journey from first touch to successful outcome.",
    "functional_requirements": "What are the must-have functional capabilities for the first release?",
    "non_functional_requirements": "What reliability, availability, or compliance constraints apply?",
    "interface_behavior": "How should the primary interface behave under normal and error conditions?",
    "data_model": "What core entities must be stored and how do they relate?",
    "business_rules": "What business rules must always hold regardless of implementation detail?",
    "authz": "How should authentication and authorization work for each role?",
    "security_privacy": "What security, privacy, or compliance requirements are mandatory?",
    "error_handling": "How should the system recover from partial failures and surface errors to users?",
    "infrastructure": "What deployment environment and operational constraints should V1 target?",
    "performance": "What performance or scaling targets matter for the first release?",
    "observability": "What logging, metrics, or audit signals are required?",
    "testing_acceptance": "What acceptance criteria prove each critical requirement is met?",
    "risks_assumptions": "What assumptions are you making and what risks worry you most?",
}

PROMPT_SIGNALS: dict[str, tuple[str, ...]] = {
    "filesystem_tool": (
        "filesystem",
        "file system",
        "ssd",
        "solid state",
        "disk",
        "drive",
        "nvme",
        "storage",
        "partition",
    ),
    "analytics": ("analy", "statistic", "metric", "report", "dashboard", "insight", "actionable"),
    "personal_tool": ("my ", "local", "personal", "desktop", "machine"),
    "api_product": ("api", "service", "endpoint", "rest", "graphql"),
    "multi_user": ("team", "role", "permission", "tenant", "organization", "user"),
}

PROFILE_AUTO_NA: dict[str, set[str]] = {
    "filesystem_tool": {"authz", "user_journeys"},
    "personal_tool": {"authz", "user_journeys", "target_users"},
    "analytics": set(),
}


def _answered_domains(state: dict[str, Any]) -> set[str]:
    answered: set[str] = set()
    for entry in state.get("questions_and_answers", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("superseded_by"):
            continue
        domain = str(entry.get("domain", "")).strip()
        if domain:
            answered.add(domain)
    return answered


def infer_prompt_tags(prompt: str) -> set[str]:
    lowered = prompt.strip().lower()
    if not lowered:
        return set()
    tags: set[str] = set()
    for tag, keywords in PROMPT_SIGNALS.items():
        if any(keyword in lowered for keyword in keywords):
            tags.add(tag)
    if "filesystem_tool" in tags and "multi_user" not in tags:
        tags.add("personal_tool")
    return tags


def apply_prompt_profile(state: dict[str, Any]) -> set[str]:
    """Mark irrelevant domains N/A based on intake prompt signals."""
    tags = infer_prompt_tags(str(state.get("original_prompt", "")))
    coverage = state.setdefault("domain_coverage", {})
    if not isinstance(coverage, dict):
        return tags
    for tag in tags:
        for domain in PROFILE_AUTO_NA.get(tag, set()):
            meta = coverage.setdefault(domain, {"addressed": False, "na": False})
            if isinstance(meta, dict):
                meta["na"] = True
    return tags


def apply_intake_prompt(state: dict[str, Any]) -> None:
    """Seed product_scope from the intake prompt — never re-ask what they already said."""
    prompt = str(state.get("original_prompt", "")).strip()
    if not prompt:
        return
    for entry in state.get("questions_and_answers", []):
        if isinstance(entry, dict) and entry.get("source") == "intake_prompt":
            return

    apply_prompt_profile(state)
    question_id = new_question_id()
    state.setdefault("questions_and_answers", []).append(
        {
            "question_id": question_id,
            "text": "Initial intent (intake)",
            "answer": prompt,
            "domain": "product_scope",
            "decision_target": "product_scope",
            "timestamp": state.get("updated_at"),
            "source": "intake_prompt",
        }
    )
    req_id = new_element_id("REQ")
    state.setdefault("confirmed_requirements", []).append(
        {
            "id": req_id,
            "text": prompt,
            "source_question_id": question_id,
            "confidence": 0.85,
            "domain": "product_scope",
        }
    )
    coverage = state.setdefault("domain_coverage", {})
    if isinstance(coverage, dict):
        coverage.setdefault("product_scope", {"addressed": True, "na": False})
        coverage["product_scope"]["addressed"] = True
    confidence = state.setdefault("confidence_by_domain", {})
    if isinstance(confidence, dict):
        confidence["product_scope"] = 0.85
    graph = state.setdefault("blueprint_graph", {"version": 0, "nodes": [], "edges": []})
    if isinstance(graph, dict):
        graph.setdefault("nodes", []).append(
            {
                "id": req_id,
                "label": prompt[:80],
                "kind": "requirement",
                "domain": "product_scope",
                "confidence": 0.85,
            }
        )


def rank_candidate_domains(state: dict[str, Any]) -> list[str]:
    """Telemetry-only view of uncovered descriptive domains; not used for questioning."""
    coverage = state.get("domain_coverage", {})
    candidates: list[str] = []
    for domain in REQUIRED_DOMAINS:
        meta = coverage.get(domain, {}) if isinstance(coverage, dict) else {}
        if isinstance(meta, dict) and meta.get("na"):
            continue
        if domain in _answered_domains(state):
            continue
        candidates.append(domain)
    return candidates


def should_stop_questioning(state: dict[str, Any], *, engine: AdaptiveQuestionEngine | None = None) -> bool:
    active_engine = engine or get_default_engine()
    return active_engine.should_stop(state)


def build_next_question(
    state: dict[str, Any],
    *,
    engine: AdaptiveQuestionEngine | None = None,
) -> dict[str, Any] | None:
    """Compatibility wrapper over the adaptive whole-state engine."""
    active_engine = engine or get_default_engine()
    try:
        return active_engine.select_next(state)
    except ProviderFailureError as error:
        state["analysis_recovery"] = {
            "code": error.code,
            "message": error.message,
            "retryable": error.retryable,
        }
        return None


__all__ = [
    "DOMAIN_PROMPTS",
    "PROMPT_SIGNALS",
    "PROFILE_AUTO_NA",
    "apply_intake_prompt",
    "apply_prompt_profile",
    "build_next_question",
    "get_analysis_recovery",
    "infer_prompt_tags",
    "rank_candidate_domains",
    "should_stop_questioning",
]
