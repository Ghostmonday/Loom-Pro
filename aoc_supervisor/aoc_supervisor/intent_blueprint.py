"""Intent-driven blueprint generation for greenfield orchestrate sessions.

GAIJINN BLUEPRINT — planner layer (human intent → work units)
-------------------------------------------------------------
Layer: Orchestration / intent decomposition (NOT graph curvature)
Status: partial — keyword STREAM_SPECS shipped; no LLM reasoning here
Canonical spec: ui/gaijinn-ui-intent-map.json → flow.pkm_greenfield_intent
Mirror: tests/test_intent_blueprint.py, workflow_evaluator.evaluate_prepare

Dual blueprint modes (orchestrate_session.prepare):
  - ``graph``: default greenfield + brownfield → gaijinn plan (generate_blueprint)
  - ``intent``: Intent Forge projection or GAIJINN_KEYWORD_GREENFIELD=1 legacy STREAM_SPECS

AI agents — DO
  - Add STREAM_SPECS rows for new domains (keywords, path, depends_on, risk)
  - Keep allowed_paths disjoint; high-risk units ≤ 2 per session
  - Preserve blueprint_mode=intent in written JSON for evaluator

AI agents — DON'T
  - Call scan/analyze output to override greenfield streams (supporting only)
  - Emit tiny_service paths for PKM-scale intents

Gaps (planned, not coded)
  - LLM-assisted stream proposals with GIV-bounded approval
  - Intent stream editor in terminal before swarm
  - Cross-session blueprint templates / industry packs

Robustness path
  - More keywords + negative guards in detect_intent_streams()
  - Per-stream acceptance_checks wired to validate_worker
  - Confusion target: prepare.greenfield_stream_count, not_template_scan_titles
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GREENFIELD_PATTERN = re.compile(
    r"\b(build|create|make|design|implement|develop|ship|scaffold)\b",
    re.IGNORECASE,
)

STEM_KEYWORDS = frozenset({"encrypt", "index", "persist", "preserv", "retriev"})
FORBIDDEN_INTENT_PATH_FRAGMENTS = ("tiny_service",)

# GAIJINN: extend this table for new domains — each row → one WorkUnit path.
STREAM_SPECS: tuple[dict[str, Any], ...] = (
    {
        "key": "foundation",
        "title": "Core project scaffold",
        "keywords": ("build", "create", "implement", "scaffold", "foundation", "bootstrap"),
        "path": "src/core/",
        "risk": "medium",
        "depends_on": (),
    },
    {
        "key": "storage",
        "title": "Local storage layer",
        "keywords": ("storage", "database", "persist", "sqlite", "store", "vault", "repository", "knowledge"),
        "path": "src/storage/",
        "risk": "medium",
        "depends_on": ("foundation",),
    },
    {
        "key": "indexing",
        "title": "Document indexing",
        "keywords": ("index", "indexing", "pdf", "markdown", "ingest", "parse", "catalog", "scanner", "filesystem"),
        "path": "src/indexing/",
        "risk": "medium",
        "depends_on": ("foundation", "storage"),
    },
    {
        "key": "search",
        "title": "Semantic search",
        "keywords": ("search", "semantic", "query", "retriev", "embedding", "vector", "find"),
        "path": "src/search/",
        "risk": "medium",
        "depends_on": ("indexing",),
    },
    {
        "key": "desktop_ui",
        "title": "Desktop UI",
        "keywords": ("desktop", "ui", "gui", "interface", "electron", "gtk", "qt", "window", "frontend"),
        "path": "src/ui/",
        "risk": "medium",
        "depends_on": ("search", "storage"),
    },
    {
        "key": "transcript",
        "title": "Audio transcript ingestion",
        "keywords": ("transcript", "audio", "speech", "whisper", "asr", "voice", "podcast"),
        "path": "src/ingestion/transcripts/",
        "risk": "medium",
        "depends_on": ("indexing",),
    },
    {
        "key": "privacy",
        "title": "Privacy and offline security",
        "keywords": ("privacy", "offline", "local-first", "encrypt", "preserv", "air-gap", "on-device"),
        "path": "src/security/",
        "risk": "high",
        "depends_on": ("storage",),
    },
    {
        "key": "api",
        "title": "Service API layer",
        "keywords": ("api", "rest", "endpoint", "grpc", "service"),
        "path": "src/api/",
        "risk": "low",
        "depends_on": ("foundation",),
    },
    {
        "key": "game_logic",
        "title": "Game rules and state",
        "keywords": ("game", "tic-tac-toe", "tictactoe", "board", "rules", "win", "player"),
        "path": "src/game/",
        "risk": "low",
        "depends_on": ("foundation",),
    },
    {
        "key": "cli",
        "title": "CLI tooling",
        "keywords": ("cli", "command-line", "terminal tool", "shell"),
        "path": "src/cli/",
        "risk": "low",
        "depends_on": ("foundation",),
    },
    {
        "key": "editor_core",
        "title": "Test editor core",
        "keywords": ("editor", "test editor", "ide", "workstation", "buffer", "syntax"),
        "path": "src/editor/",
        "risk": "medium",
        "depends_on": ("foundation",),
    },
    {
        "key": "rust_core",
        "title": "Rust engine layer",
        "keywords": ("rust", "cargo", "crate", "tokio", "ffi"),
        "path": "crates/editor-core/",
        "risk": "medium",
        "depends_on": ("foundation", "editor_core"),
    },
    {
        "key": "go_bridge",
        "title": "Go services bridge",
        "keywords": ("golang", "go ", " go,", "grpc-go", "go module"),
        "path": "services/bridge/",
        "risk": "medium",
        "depends_on": ("foundation", "rust_core"),
    },
    {
        "key": "editor_ui",
        "title": "Editor UI and theming",
        "keywords": (
            "dark",
            "elegance",
            "elegant",
            "theme",
            "styling",
            "workstation",
            "aesthetic",
            "gtk",
            "egui",
            "tauri",
        ),
        "path": "src/ui/editor/",
        "risk": "medium",
        "depends_on": ("editor_core", "rust_core"),
    },
    {
        "key": "tests",
        "title": "Test suite and harness",
        "keywords": (
            "unit test",
            "unit tests",
            "pytest",
            "test suite",
            "test harness",
            "integration test",
            "test editor",
        ),
        "path": "tests/",
        "risk": "low",
        "depends_on": ("foundation",),
    },
)


@dataclass(frozen=True)
class IntentStream:
    key: str
    title: str
    path: str
    risk: str
    depends_on_keys: tuple[str, ...]


def is_greenfield_intent(intent: str) -> bool:
    text = intent.strip()
    if not text:
        return False
    return GREENFIELD_PATTERN.search(text) is not None


def _normalized_intent(intent: str) -> str:
    return f" {intent.strip().lower()} "


def _keyword_matches(text: str, keyword: str) -> bool:
    """Match intent keywords without letting short tokens leak through substrings."""
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    escaped = re.escape(keyword)
    if keyword in STEM_KEYWORDS:
        return re.search(rf"\b{escaped}\w*", text) is not None
    return re.search(rf"(?<!\w){escaped}(?!\w)", text) is not None


def _validate_intent_streams(streams: list[IntentStream]) -> None:
    paths = [stream.path for stream in streams]
    duplicate_paths = sorted({path for path in paths if paths.count(path) > 1})
    if duplicate_paths:
        raise ValueError(f"intent streams must have distinct paths: {', '.join(duplicate_paths)}")

    forbidden_paths = [path for path in paths if any(fragment in path for fragment in FORBIDDEN_INTENT_PATH_FRAGMENTS)]
    if forbidden_paths:
        raise ValueError(f"intent streams cannot use template paths: {', '.join(forbidden_paths)}")


def detect_intent_streams(intent: str) -> list[IntentStream]:
    """Map user intent to isolated workstreams (deterministic keyword match)."""
    text = _normalized_intent(intent)
    selected: list[IntentStream] = []

    for spec in STREAM_SPECS:
        if any(_keyword_matches(text, keyword) for keyword in spec["keywords"]):
            selected.append(
                IntentStream(
                    key=str(spec["key"]),
                    title=str(spec["title"]),
                    path=str(spec["path"]),
                    risk=str(spec["risk"]),
                    depends_on_keys=tuple(spec.get("depends_on", ())),
                )
            )

    if not selected and is_greenfield_intent(intent):
        selected.append(
            IntentStream(
                key="foundation",
                title="Core implementation",
                path="src/core/",
                risk="medium",
                depends_on_keys=(),
            )
        )

    # Foundation is implied when multiple product streams exist.
    keys = {stream.key for stream in selected}
    if len(selected) > 1 and "foundation" not in keys:
        foundation = next(spec for spec in STREAM_SPECS if spec["key"] == "foundation")
        selected.insert(
            0,
            IntentStream(
                key="foundation",
                title=str(foundation["title"]),
                path=str(foundation["path"]),
                risk=str(foundation["risk"]),
                depends_on_keys=(),
            ),
        )

    # Stable ordering for reproducible blueprints.
    order = {spec["key"]: index for index, spec in enumerate(STREAM_SPECS)}
    selected.sort(key=lambda stream: order.get(stream.key, 999))
    _validate_intent_streams(selected)
    return selected


def swarm_rationale(streams: list[IntentStream], recommended: int) -> str:
    if not streams:
        return f"Recommended: {recommended} agents based on project scope."
    labels = ", ".join(stream.title.lower() for stream in streams[:8])
    if len(streams) > 8:
        labels += ", …"
    return f"Recommended: {recommended} agents based on {labels}."


def swarm_warning(workers: int, work_units: int) -> str | None:
    if workers <= work_units:
        return None
    idle = workers - work_units
    unit_label = "agent" if work_units == 1 else "agents"
    return f"Only {work_units} {unit_label} can receive work. {idle} would be idle."


def build_intent_blueprint(intent: str) -> dict[str, Any]:
    """Build a blueprint dict from user intent (greenfield source of truth)."""
    streams = detect_intent_streams(intent)
    if not streams:
        raise ValueError("intent did not yield any workstreams")

    key_to_id = {stream.key: f"WU-{index:03d}" for index, stream in enumerate(streams, start=1)}
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
                "description": (f"Implement {stream.title.lower()} for the product goal: {intent.strip()}"),
                "allowed_paths": [stream.path],
                "denied_paths": [".gaijinn/workers"],
                "depends_on": depends_on,
                "acceptance_checks": ["pytest"],
                "estimated_risk": stream.risk,
            }
        )

    risks = [
        f"{unit['id']}: estimated {unit['estimated_risk']} risk"
        for unit in work_units
        if unit["estimated_risk"] != "low"
    ]

    return {
        "schema_version": 1,
        "project_goal": intent.strip(),
        "assumptions": [
            "Work units are generated from user intent for greenfield orchestrate sessions.",
            "Repository scan informs GIV and context only; intent defines architecture boundaries.",
            "Allowed paths are write scopes; workers may read broader project context as needed.",
        ],
        "work_units": work_units,
        "dependencies": dependencies,
        "risks": risks,
        "blueprint_mode": "intent",
        "work_stream_titles": [stream.title for stream in streams],
    }


def write_intent_blueprint(project_root: Path, intent: str) -> dict[str, Any]:
    payload = build_intent_blueprint(intent)
    gaijinn_dir = project_root / ".gaijinn"
    gaijinn_dir.mkdir(parents=True, exist_ok=True)
    blueprint_path = gaijinn_dir / "blueprint.json"
    blueprint_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Gaijinn Blueprint (intent-driven)",
        "",
        f"**Goal:** {payload['project_goal']}",
        "",
        "## Work streams",
        "",
    ]
    for unit in payload["work_units"]:
        lines.append(f"- **{unit['id']}** — {unit['title']}")
    lines.append("")
    (gaijinn_dir / "blueprint.md").write_text("\n".join(lines), encoding="utf-8")
    return payload
