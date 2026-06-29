"""Shared constants for Gaijinn CLI commands.

GAIJINN BLUEPRINT: artifact paths under .gaijinn/ are the runtime contract.
UI_CONTRACT_PATH is repo-relative (ui/) — doctor checks from project cwd.
"""

from __future__ import annotations

import os
from pathlib import Path

# ── Env Var Backward Compatibility Shim ─────────────────────────────────
# Maps old GAIJINN_* env vars to LOOM_* equivalents. Active at import time.
# Remove this shim after all external integrations have migrated.

_GAIJINN_TO_LOOM_ENV: dict[str, str] = {
    "GAIJINN_ALLOW_INSECURE_LOCAL": "LOOM_ALLOW_INSECURE_LOCAL",
    "GAIJINN_ALLOW_MULTI_API_WORKER": "LOOM_ALLOW_MULTI_API_WORKER",
    "GAIJINN_ALLOW_RAW_INTENT_PREPARE": "LOOM_ALLOW_RAW_INTENT_PREPARE",
    "GAIJINN_API_BIND": "LOOM_API_BIND",
    "GAIJINN_API_KEY": "LOOM_API_KEY",
    "GAIJINN_API_PORT": "LOOM_API_PORT",
    "GAIJINN_CODEX_PROFILE": "LOOM_CODEX_PROFILE",
    "GAIJINN_CONVEX_HULL_THRESHOLD": "LOOM_CONVEX_HULL_THRESHOLD",
    "GAIJINN_COUNCIL_AUTHOR_ID": "LOOM_COUNCIL_AUTHOR_ID",
    "GAIJINN_COUNCIL_TZ": "LOOM_COUNCIL_TZ",
    "GAIJINN_DEEPSEEK_PROVIDER": "LOOM_DEEPSEEK_PROVIDER",
    "GAIJINN_DESIGN_TIMEOUT": "LOOM_DESIGN_TIMEOUT",
    "GAIJINN_FAKE_REASONING": "LOOM_FAKE_REASONING",
    "GAIJINN_HANDOFF_GATEWAYS": "LOOM_HANDOFF_GATEWAYS",
    "GAIJINN_IDEMPOTENCY_STALE_SECONDS": "LOOM_IDEMPOTENCY_STALE_SECONDS",
    "GAIJINN_KEYWORD_GREENFIELD": "LOOM_KEYWORD_GREENFIELD",
    "GAIJINN_LEDGER_LOCK_TIMEOUT": "LOOM_LEDGER_LOCK_TIMEOUT",
    "GAIJINN_MAX_ACTIVE_WORKERS": "LOOM_MAX_ACTIVE_WORKERS",
    "GAIJINN_MAX_CONCURRENT_SPRINTS": "LOOM_MAX_CONCURRENT_SPRINTS",
    "GAIJINN_MAX_SPAWN_TIMEOUT": "LOOM_MAX_SPAWN_TIMEOUT",
    "GAIJINN_MAX_WORKERS_PER_SESSION": "LOOM_MAX_WORKERS_PER_SESSION",
    "GAIJINN_MOCK_GRID": "LOOM_MOCK_GRID",
    "GAIJINN_OPERATOR": "LOOM_OPERATOR",
    "GAIJINN_PROJECT_ROOT": "LOOM_PROJECT_ROOT",
    "GAIJINN_PYTHON": "LOOM_PYTHON",
    "GAIJINN_REASONING_PROVIDER": "LOOM_REASONING_PROVIDER",
    "GAIJINN_REASONING_TIMEOUT": "LOOM_REASONING_TIMEOUT",
    "GAIJINN_REASONING_URL": "LOOM_REASONING_URL",
    "GAIJINN_REQUIRE_AUTH": "LOOM_REQUIRE_AUTH",
    "GAIJINN_REQUIRE_SPAWN_IDEMPOTENCY": "LOOM_REQUIRE_SPAWN_IDEMPOTENCY",
    "GAIJINN_SEED_TERMINAL_USER": "LOOM_SEED_TERMINAL_USER",
    "GAIJINN_SEMANTIC_LLM": "LOOM_SEMANTIC_LLM",
    "GAIJINN_SEMANTIC_LLM_URL": "LOOM_SEMANTIC_LLM_URL",
    "GAIJINN_SKIP_MERGE_TESTS": "LOOM_SKIP_MERGE_TESTS",
    "GAIJINN_SPRINT_TIMEOUT": "LOOM_SPRINT_TIMEOUT",
    "GAIJINN_STEALTH": "LOOM_STEALTH",
    "GAIJINN_TEST_INJECT_FAILURE": "LOOM_TEST_INJECT_FAILURE",
}


def _init_env_shim() -> None:
    """Mirror old GAIJINN_* env vars to LOOM_* for backward compatibility."""
    for old_key, new_key in _GAIJINN_TO_LOOM_ENV.items():
        if new_key not in os.environ and old_key in os.environ:
            os.environ[new_key] = os.environ[old_key]


_init_env_shim()

# ── Constants ──────────────────────────────────────────────────────────

DEFAULT_GRAPH_PATH = Path(".gaijinn/graph.json")
DEFAULT_METRICS_PATH = Path(".gaijinn/metrics_manifest.json")
DEFAULT_POLL_INTERVAL = 1.0
GAIJINN_DIR = Path(".gaijinn")
LICENSE_PATH = GAIJINN_DIR / "license.json"
PROJECT_PATH = GAIJINN_DIR / "project.json"
BLUEPRINT_SEED_PATH = GAIJINN_DIR / "GENERATE_BLUEPRINT.md"
BLUEPRINT_TEMPLATE_PATH = GAIJINN_DIR / "blueprint.md"
BLUEPRINT_JSON_PATH = GAIJINN_DIR / "blueprint.json"
INFERRED_JSON_PATH = GAIJINN_DIR / "inferred.json"
INTENT_PATH = GAIJINN_DIR / "intent.txt"
GIV_PATH = GAIJINN_DIR / "giv.json"
WORKERS_DIR = GAIJINN_DIR / "workers"
BRIDGE_DIR = GAIJINN_DIR / "bridge"
COUNCIL_MD_PATH = BRIDGE_DIR / "council.md"
MANIFEST_PATH = WORKERS_DIR / "manifest.json"
OUTPUT_LOG_FILENAME = "output.log"
# Run-grid handoff files live at the worker root and always differ from the integration base.
WORKER_HANDOFF_BASENAMES = frozenset(
    {
        "WORK_UNIT.md",
        "WORKER_INTENT.txt",
        "intent.txt",
        "giv.json",
        "metadata.json",
        OUTPUT_LOG_FILENAME,
    }
)
DEFAULT_GRID_MODEL = "grok-composer-2.5-fast"
GROK_BINARY = "grok"
HERMES_BINARY = "hermes"
UI_CONTRACT_PATH = Path("ui/gaijinn-ui-intent-map.json")
AGENT_FILE_PATHS = (Path("CLAUDE.md"), Path(".cursorrules"))
GAIJINN_AGENT_BLOCK_BEGIN = "<!-- BEGIN GAIJINN INIT -->"
GAIJINN_AGENT_BLOCK_END = "<!-- END GAIJINN INIT -->"
