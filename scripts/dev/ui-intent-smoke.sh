#!/usr/bin/env bash
# AI-driven terminal smoke tests via gaijinn-ui-intent-map.json (no browser required).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"
python3 -m pytest tests/test_ui_intent_smoke.py -q "$@"