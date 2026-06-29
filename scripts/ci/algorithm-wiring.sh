#!/usr/bin/env bash
# Algorithm wiring traceability — production-like provider config, no mock grid.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"

export GAIJINN_REASONING_PROVIDER="${GAIJINN_REASONING_PROVIDER:-http}"
export GAIJINN_REASONING_URL="${GAIJINN_REASONING_URL:-http://127.0.0.1:9/analyze}"

# Production-like: do not enable test-only stand-ins for this suite.
unset GAIJINN_FAKE_REASONING || true
unset GAIJINN_MOCK_GRID || true

python3 -m pytest tests/test_algorithm_wiring.py -q --no-cov "$@"