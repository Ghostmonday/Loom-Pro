#!/usr/bin/env bash
# Codex: Loom C01 prepare handoff gate (backend only — no UI)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"
mkdir -p .gaijinn/codex
TASK="${ROOT}/docs/codex-tasks/loom/task-loom-c01-prepare-gate.md"
LOG="${ROOT}/.gaijinn/codex/loom-c01-run.jsonl"
codex exec --full-auto "$(cat "$TASK")" 2>&1 | tee -a "$LOG"
.venv/bin/python -m pytest tests/test_loom_pipeline_intent.py::test_loom_c01_prepare_gate tests/test_ui_intent_smoke.py -q --no-cov