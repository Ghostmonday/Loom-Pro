"""Canonical repository paths for UI contracts, sandbox frontend, and workspace roots.

GAIJINN BLUEPRINT — path contract (single source of truth)
----------------------------------------------------------
Layer: Cross-cutting / UI surface resolution
Status: sandbox_frontend replaces old ui/ implementation
Spec: docs/reference/sandbox-frontend-engineering-reference.md

AI agents (Codex, Cursor, Grok): import paths from here — never hardcode
UI asset locations. Mirror tests use UiIntentDriver against API contracts.
Old ui/ HTML/JS/CSS files removed; sandbox_frontend/ serves the new glass-morphism UI.
JSON contract files remain in ui/ for backend reference.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
UI_DIR = REPO_ROOT / "ui"
FRONTEND_DIR = REPO_ROOT / "sandbox_frontend"

# ── JSON Contracts (retained in ui/ — referenced by backend API) ──
INTENT_MAP_PATH = UI_DIR / "loom-ui-intent-map.json"
LOOM_SYSTEM_INTENT_MAP_PATH = UI_DIR / "loom-system-intent-map.json"
LOOM_PIPELINE_INTENT_MAP_PATH = UI_DIR / "loom-pipeline-intent-map.json"
LOOM_INTENT_FORGE_INTENT_MAP_PATH = UI_DIR / "loom-intent-forge-intent-map.json"
COMMAND_ENGINE_INTENT_MAP_PATH = UI_DIR / "command-engine-ui-intent-map.json"
PROCESS_STAGE_UX_MAP_PATH = UI_DIR / "process-stage-ux-map.json"
BLUEPRINT_UI_PATH = UI_DIR / "blueprint-ui.json"
EXPERIENCE_POLICY_PATH = UI_DIR / "experience-policy.json"
ORCHESTRATION_EVENT_SCHEMA_PATH = UI_DIR / "orchestration-event.schema.json"
ORCHESTRATION_SNAPSHOT_SCHEMA_PATH = UI_DIR / "orchestration-snapshot.schema.json"
ORCHESTRATION_VISUAL_GRAMMAR_PATH = UI_DIR / "orchestration-visual-grammar.json"

# ── Sandbox Frontend HTML pages (from sandbox_frontend/) ──
PLACEHOLDER_HTML_PATH = FRONTEND_DIR / "index.html"
INTENT_FORGE_HTML_PATH = FRONTEND_DIR / "index.html"  # hub page replaces old intent-forge
COMMAND_ENGINE_HTML_PATH = FRONTEND_DIR / "topological-observatory.html"  # replaces old command-engine

# ── Old JS/CSS paths (implementation removed, routes serve sandbox_frontend) ──
INTENT_FORGE_CSS_PATH = FRONTEND_DIR / "index.html"
INTENT_FORGE_JS_PATH = FRONTEND_DIR / "index.html"
COMMAND_ENGINE_JS_PATH = FRONTEND_DIR / "topological-observatory.html"
TERMINAL_JS_PATH = FRONTEND_DIR / "index.html"

# ── Sandbox Frontend page index for route mapping ──
SANDBOX_PAGES = {
    "hub": FRONTEND_DIR / "index.html",
    "blueprint-ratification": FRONTEND_DIR / "blueprint-ratification.html",
    "claims-ledger": FRONTEND_DIR / "claims-ledger.html",
    "curvature-analysis": FRONTEND_DIR / "curvature-analysis.html",
    "drift-monitor": FRONTEND_DIR / "drift-monitor.html",
    "packet-export": FRONTEND_DIR / "packet-export.html",
    "topological-observatory": FRONTEND_DIR / "topological-observatory.html",
}
