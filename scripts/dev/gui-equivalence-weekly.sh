#!/usr/bin/env bash
# Weekly API ↔ intent-map contract check (HTML surfaces removed).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"
python -m pytest tests/test_ui_intent_smoke.py -q "$@"