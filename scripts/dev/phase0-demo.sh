#!/usr/bin/env bash
# Phase 0 — prepare project + serve terminal with mock grid (no grok required).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT="${GAIJINN_PROJECT_ROOT:-$ROOT/examples/tiny-python-service}"

cd "$PROJECT"

if [[ ! -d .gaijinn/workers/worker-001 ]]; then
  echo "==> Seeding Gaijinn workflow in $PROJECT"
  gaijinn init --force --no-agent-files "Phase 0 terminal demo project"
  gaijinn scan .
  gaijinn analyze
  gaijinn compile-prompt
  gaijinn plan --workers 2
  gaijinn run-grid --workers 2
fi

export GAIJINN_PROJECT_ROOT="$PROJECT"
export GAIJINN_MOCK_GRID=1
export GAIJINN_SEED_TERMINAL_USER=1

echo "==> Serving terminal at http://127.0.0.1:8080"
echo "    Project root: $PROJECT"
echo "    Mock grid: ON (set GAIJINN_MOCK_GRID=0 when grok is on PATH)"
exec gaijinn serve --host 127.0.0.1 --port 8080