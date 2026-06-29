#!/usr/bin/env bash
# Hermes unattended vault development — one pipeline step per cron tick.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor"
export GAIJINN_PROJECT_ROOT="${GAIJINN_PROJECT_ROOT:-${ROOT}/vaults/gaijinn-memory-fs}"
export GAIJINN_OPERATOR="${GAIJINN_OPERATOR:-1}"

exec python3 scripts/dev/hermes_development_loop.py "$@"