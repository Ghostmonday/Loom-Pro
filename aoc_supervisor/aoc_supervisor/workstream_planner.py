"""Executable workstream projection from Intent Forge artifacts.

Keyword-based greenfield decomposition lives in intent_blueprint.py during migration.
This module projects rich Intent Forge state into the legacy orchestration blueprint format.
"""

from __future__ import annotations

from typing import Any

from aoc_supervisor.intent_blueprint import (
    STREAM_SPECS,
    IntentStream,
    _validate_intent_streams,
    build_intent_blueprint,
    detect_intent_streams,
    write_intent_blueprint,
)

__all__ = [
    "build_intent_blueprint",
    "detect_intent_streams",
    "project_executable_blueprint",
    "write_intent_blueprint",
]

# Domain-addressed workstreams not always surfaced by keyword intent alone.
DOMAIN_STREAM_ADDITIONS: dict[str, dict[str, Any]] = {
    "authz": {
        "key": "authz",
        "title": "Authentication and authorization",
        "path": "src/auth/",
        "risk": "high",
        "depends_on": ("foundation", "api"),
    },
    "security_privacy": {
        "key": "privacy",
        "title": "Privacy and offline security",
        "path": "src/security/",
        "risk": "high",
        "depends_on": ("storage",),
    },
    "observability": {
        "key": "observability",
        "title": "Observability and audit logging",
        "path": "src/observability/",
        "risk": "medium",
        "depends_on": ("foundation",),
    },
    "data_model": {
        "key": "storage",
        "title": "Local storage layer",
        "path": "src/storage/",
        "risk": "medium",
        "depends_on": ("foundation",),
    },
    "testing_acceptance": {
        "key": "tests",
        "title": "Test suite and harness",
        "path": "tests/",
        "risk": "low",
        "depends_on": ("foundation",),
    },
    "interface_behavior": {
        "key": "desktop_ui",
        "title": "Desktop UI",
        "path": "src/ui/",
        "risk": "medium",
        "depends_on": ("search", "storage"),
    },
    "infrastructure": {
        "key": "api",
        "title": "Service API layer",
        "path": "src/api/",
        "risk": "low",
        "depends_on": ("foundation",),
    },
}

STREAM_DOMAIN_HINTS: dict[str, str] = {
    "authz": "authz",
    "privacy": "security_privacy",
    "observability": "observability",
    "storage": "data_model",
    "tests": "testing_acceptance",
    "desktop_ui": "interface_behavior",
    "api": "infrastructure",
    "cli": "interface_behavior",
    "search": "functional_requirements",
    "indexing": "functional_requirements",
    "game_logic": "functional_requirements",
}


def _merge_projection_context(
    *,
    artifact: dict[str, Any] | None,
    session_state: dict[str, Any] | None,
) -> dict[str, Any]:
    artifact = artifact if isinstance(artifact, dict) else {}
    session_state = session_state if isinstance(session_state, dict) else {}
    return {
        "product_definition": artifact.get("product_definition") or session_state.get("original_prompt", ""),
        "confirmed_requirements": session_state.get("confirmed_requirements")
        or artifact.get("confirmed_requirements")
        or [],
        "questions_and_answers": session_state.get("questions_and_answers") or [],
        "decisions": session_state.get("decisions") or artifact.get("decisions") or [],
        "acceptance_criteria": session_state.get("acceptance_criteria") or artifact.get("acceptance_criteria") or [],
        "domain_coverage": session_state.get("domain_coverage") or artifact.get("domain_coverage") or {},
        "assumptions": artifact.get("assumptions") or session_state.get("assumptions") or [],
        "risks": artifact.get("risks") or session_state.get("risks") or [],
    }


def _active_qa_entries(context: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in context.get("questions_and_answers", []):
        if isinstance(entry, dict) and not entry.get("superseded_by"):
            entries.append(entry)
    return entries


def _active_requirements(context: dict[str, Any]) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for req in context.get("confirmed_requirements", []):
        if isinstance(req, dict) and not req.get("stale"):
            requirements.append(req)
    return requirements


def _has_qa_evidence(context: dict[str, Any]) -> bool:
    return bool(_active_qa_entries(context) or _active_requirements(context))


def _build_projection_corpus(intent: str, context: dict[str, Any]) -> str:
    parts = [intent.strip()]
    for entry in _active_qa_entries(context):
        answer = str(entry.get("answer", "")).strip()
        if answer:
            parts.append(answer)
    for req in _active_requirements(context):
        text = str(req.get("text", "")).strip()
        if text:
            parts.append(text)
    for decision in context.get("decisions", []):
        if isinstance(decision, dict) and not decision.get("superseded"):
            text = str(decision.get("text", "")).strip()
            if text:
                parts.append(text)
    return " ".join(part for part in parts if part)


def _domain_is_addressed(context: dict[str, Any], domain: str) -> bool:
    coverage = context.get("domain_coverage", {})
    if not isinstance(coverage, dict):
        return False
    meta = coverage.get(domain, {})
    if not isinstance(meta, dict):
        return False
    if meta.get("na"):
        return False
    return bool(meta.get("addressed"))


def _augment_streams_from_domains(streams: list[IntentStream], context: dict[str, Any]) -> list[IntentStream]:
    keys = {stream.key for stream in streams}
    paths = {stream.path for stream in streams}
    augmented = list(streams)

    for domain, spec in DOMAIN_STREAM_ADDITIONS.items():
        if not _domain_is_addressed(context, domain):
            continue
        key = str(spec["key"])
        path = str(spec["path"])
        if key in keys or path in paths:
            continue
        augmented.append(
            IntentStream(
                key=key,
                title=str(spec["title"]),
                path=path,
                risk=str(spec["risk"]),
                depends_on_keys=tuple(spec.get("depends_on", ())),
            )
        )
        keys.add(key)
        paths.add(path)

    order = {spec["key"]: index for index, spec in enumerate(STREAM_SPECS)}
    augmented.sort(key=lambda stream: order.get(stream.key, 999))
    _validate_intent_streams(augmented)
    return augmented


def _domain_requirement_notes(context: dict[str, Any]) -> dict[str, list[str]]:
    notes: dict[str, list[str]] = {}
    for req in _active_requirements(context):
        domain = str(req.get("domain", "")).strip()
        text = str(req.get("text", "")).strip()
        if not domain or not text:
            continue
        notes.setdefault(domain, []).append(text)
    for entry in _active_qa_entries(context):
        domain = str(entry.get("domain", "")).strip()
        answer = str(entry.get("answer", "")).strip()
        if not domain or not answer:
            continue
        notes.setdefault(domain, []).append(answer)
    return notes


def _acceptance_checks(context: dict[str, Any]) -> list[str]:
    checks = ["pytest"]
    seen = {"pytest"}
    for item in context.get("acceptance_criteria", []):
        if isinstance(item, dict):
            text = str(item.get("text") or item.get("criterion") or "").strip()
        else:
            text = str(item).strip()
        if text and text not in seen:
            checks.append(text[:160])
            seen.add(text)
    return checks


def _collect_assumptions(context: dict[str, Any]) -> list[str]:
    assumptions = [
        "Work units are projected from Intent Forge confirmed requirements and Q&A evidence.",
        "Repository scan informs GIV and context only; interrogated intent defines architecture boundaries.",
        "Allowed paths are write scopes; workers may read broader project context as needed.",
    ]
    seen = set(assumptions)
    for item in context.get("assumptions", []):
        text = str(item.get("text", "")).strip() if isinstance(item, dict) else str(item).strip()
        if text and text not in seen:
            assumptions.append(text)
            seen.add(text)
    for decision in context.get("decisions", []):
        if isinstance(decision, dict) and not decision.get("superseded"):
            text = str(decision.get("text", "")).strip()
            if text:
                line = f"Decision: {text}"
                if line not in seen:
                    assumptions.append(line)
                    seen.add(line)
    return assumptions


def _work_unit_description(*, intent: str, stream: IntentStream, context: dict[str, Any]) -> str:
    base = f"Implement {stream.title.lower()} for the product goal: {intent.strip()}"
    domain_notes = _domain_requirement_notes(context)
    hinted_domain = STREAM_DOMAIN_HINTS.get(stream.key, "")
    snippets: list[str] = []
    if hinted_domain and hinted_domain in domain_notes:
        snippets.extend(domain_notes[hinted_domain])
    if not snippets:
        for notes in domain_notes.values():
            snippets.extend(notes)
    if snippets:
        joined = "; ".join(snippets[:4])
        return f"{base} Confirmed requirements: {joined}"
    return base


def _assemble_blueprint(
    *,
    intent: str,
    streams: list[IntentStream],
    context: dict[str, Any],
    projection_mode: str,
) -> dict[str, Any]:
    if not streams:
        raise ValueError("intent did not yield any workstreams")

    key_to_id = {stream.key: f"WU-{index:03d}" for index, stream in enumerate(streams, start=1)}
    acceptance_checks = _acceptance_checks(context)
    work_units: list[dict[str, Any]] = []
    dependencies: dict[str, list[str]] = {}

    for stream in streams:
        unit_id = key_to_id[stream.key]
        depends_on = [
            key_to_id[dep_key]
            for dep_key in stream.depends_on_keys
            if dep_key in key_to_id and key_to_id[dep_key] != unit_id
        ]
        dependencies[unit_id] = depends_on
        work_units.append(
            {
                "id": unit_id,
                "title": stream.title,
                "description": _work_unit_description(intent=intent, stream=stream, context=context),
                "allowed_paths": [stream.path],
                "denied_paths": [".gaijinn/workers"],
                "depends_on": depends_on,
                "acceptance_checks": list(acceptance_checks),
                "estimated_risk": stream.risk,
            }
        )

    risks = [
        f"{unit['id']}: estimated {unit['estimated_risk']} risk"
        for unit in work_units
        if unit["estimated_risk"] != "low"
    ]
    for item in context.get("risks", []):
        if isinstance(item, dict):
            text = str(item.get("text", "")).strip()
            if text:
                risks.append(text)

    return {
        "schema_version": 1,
        "project_goal": intent.strip(),
        "assumptions": _collect_assumptions(context),
        "work_units": work_units,
        "dependencies": dependencies,
        "risks": risks,
        "blueprint_mode": "intent",
        "projection_mode": projection_mode,
        "work_stream_titles": [stream.title for stream in streams],
    }


def project_executable_blueprint(
    *,
    intent: str,
    artifact: dict[str, Any] | None = None,
    session_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile a legacy .gaijinn/blueprint.json projection from Intent Forge output."""
    intent = intent.strip()
    if not intent:
        raise ValueError("intent is required")

    context = _merge_projection_context(artifact=artifact, session_state=session_state)
    if not _has_qa_evidence(context):
        blueprint = build_intent_blueprint(intent)
        blueprint["projection_mode"] = "keyword"
        return blueprint

    corpus = _build_projection_corpus(intent, context)
    streams = _augment_streams_from_domains(detect_intent_streams(corpus), context)
    return _assemble_blueprint(
        intent=intent,
        streams=streams,
        context=context,
        projection_mode="intent_forge",
    )
