"""Internal prompt-to-blueprint coverage helpers for creator tooling."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .intent_blueprint import STREAM_SPECS, _keyword_matches, _normalized_intent

_SPEC_BY_KEY = {str(spec["key"]): spec for spec in STREAM_SPECS}
_KEY_BY_PATH = {str(spec["path"]): str(spec["key"]) for spec in STREAM_SPECS}
_KEY_BY_TITLE = {str(spec["title"]): str(spec["key"]) for spec in STREAM_SPECS}
_ORDER = {str(spec["key"]): index for index, spec in enumerate(STREAM_SPECS)}

_PHRASE_REQUIREMENTS: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    (re.compile(r"\btic[- ]?tac[- ]?toe\b", re.IGNORECASE), ("game_logic",)),
    (re.compile(r"\btest editor\b", re.IGNORECASE), ("editor_core", "tests")),
    (re.compile(r"\btodo(?:s)?\b|\btask list\b", re.IGNORECASE), ("storage",)),
    (re.compile(r"\bgo\b|\bgolang\b", re.IGNORECASE), ("go_bridge",)),
)


def explicit_requirements(intent: str) -> list[str]:
    """Return STREAM_SPECS keys explicitly requested by prompt text."""
    text = _normalized_intent(intent)
    required: set[str] = set()

    for spec in STREAM_SPECS:
        key = str(spec["key"])
        if any(_keyword_matches(text, str(keyword)) for keyword in spec.get("keywords", ())):
            required.add(key)

    for pattern, keys in _PHRASE_REQUIREMENTS:
        if pattern.search(intent):
            required.update(key for key in keys if key in _SPEC_BY_KEY)

    if required and "foundation" in _SPEC_BY_KEY:
        required.add("foundation")

    return sorted(required, key=lambda key: _ORDER.get(key, 999))


def _blueprint_stream_keys(blueprint: Mapping[str, Any]) -> set[str]:
    keys: set[str] = set()
    for unit in blueprint.get("work_units", ()):
        if not isinstance(unit, Mapping):
            continue
        title = unit.get("title")
        if isinstance(title, str) and title in _KEY_BY_TITLE:
            keys.add(_KEY_BY_TITLE[title])
        for path in unit.get("allowed_paths", ()):
            if isinstance(path, str) and path in _KEY_BY_PATH:
                keys.add(_KEY_BY_PATH[path])
    return keys


def blueprint_coverage(intent: str, blueprint: Mapping[str, Any]) -> dict[str, Any]:
    """Compare explicit prompt requirements with streams present in a blueprint."""
    required = explicit_requirements(intent)
    present = _blueprint_stream_keys(blueprint)
    required_set = set(required)
    return {
        "covered": [key for key in required if key in present],
        "missing": [key for key in required if key not in present],
        "inferred": sorted((key for key in present if key not in required_set), key=lambda key: _ORDER.get(key, 999)),
    }
