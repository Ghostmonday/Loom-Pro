"""Canonical repository paths for UI and workspace roots.

GAIJINN BLUEPRINT — path contract (single source of truth)
----------------------------------------------------------
Layer: Cross-cutting / UI surface resolution
Status: shipped
Spec: ui/gaijinn-ui-intent-map.json, ui/README.md

AI agents (Codex, Cursor, Grok): import paths from here — never hardcode
``gaijinn-terminal.html`` at repo root. Terminal and mirror tests must stay
isomorphic: same phases, API sequence, invariant names.

Gaps: none for path resolution.
Extend: add ORCHESTRATE_DIR, CODEX_TASKS_DIR if new surfaces appear.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
UI_DIR = REPO_ROOT / "ui"
TERMINAL_HTML_PATH = UI_DIR / "gaijinn-terminal.html"
COMMAND_ENGINE_HTML_PATH = UI_DIR / "views" / "command-engine.html"
NEURAL_DRAFT_HTML_PATH = UI_DIR / "neural-draft" / "index.html"
NEURAL_DRAFT_CSS_PATH = UI_DIR / "neural-draft" / "console.css"
NEURAL_DRAFT_JS_PATH = UI_DIR / "neural-draft" / "console.js"
INTENT_MAP_PATH = UI_DIR / "gaijinn-ui-intent-map.json"
