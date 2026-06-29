"""Contradiction detection and resolution helpers for Intent Forge."""

from __future__ import annotations

from typing import Any

from aoc_supervisor.intent_blueprint_state import new_element_id


def detect_contradictions(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic contradiction scan over requirements and decisions."""
    resolved_pairs = {
        (
            str(item.get("element_a_id", "")),
            str(item.get("element_b_id", "")),
        )
        for item in state.get("contradictions", [])
        if isinstance(item, dict) and item.get("resolved")
    }
    existing_ids = {
        str(item.get("id", ""))
        for collection in ("confirmed_requirements", "decisions")
        for item in state.get(collection, [])
        if isinstance(item, dict)
    }
    found: list[dict[str, Any]] = []
    requirements = [
        item for item in state.get("confirmed_requirements", []) if isinstance(item, dict) and not item.get("stale")
    ]
    decisions = [item for item in state.get("decisions", []) if isinstance(item, dict) and not item.get("superseded")]

    for req in requirements:
        req_text = str(req.get("text", "")).lower()
        for dec in decisions:
            dec_text = str(dec.get("text", "")).lower()
            if "zero-latency" in req_text and "validation window" in dec_text:
                pair = (str(req.get("id", "")), str(dec.get("id", "")))
                if pair in resolved_pairs:
                    continue
                conflict_id = new_element_id("CF")
                if conflict_id in existing_ids:
                    continue
                found.append(
                    {
                        "id": conflict_id,
                        "element_a_id": str(req.get("id", "")),
                        "element_b_id": str(dec.get("id", "")),
                        "description": "Latency expectation conflicts with mandatory validation window.",
                        "resolved": False,
                        "blocking": True,
                    }
                )
    return found


def merge_contradictions(state: dict[str, Any], fresh: list[dict[str, Any]]) -> None:
    known = {str(item.get("id", "")): item for item in state.get("contradictions", []) if isinstance(item, dict)}
    for item in fresh:
        cid = str(item.get("id", ""))
        if cid and cid not in known:
            state.setdefault("contradictions", []).append(item)


def resolution_options(contradiction: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    _ = state
    a_id = str(contradiction.get("element_a_id", ""))
    b_id = str(contradiction.get("element_b_id", ""))
    return [
        {
            "option_id": "uphold_a",
            "label": f"Uphold {a_id} over {b_id}",
            "summary": "Keep the requirement and revise the conflicting decision.",
        },
        {
            "option_id": "synthesize",
            "label": "Synthesize hybrid",
            "summary": "Blend both elements with an explicit compromise requirement.",
            "recommended": True,
        },
        {
            "option_id": "custom",
            "label": "Custom answer",
            "summary": "Provide a free-form resolution.",
        },
    ]
