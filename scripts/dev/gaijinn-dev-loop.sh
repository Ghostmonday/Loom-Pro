#!/usr/bin/env bash
# Gaijinn unattended development loop for vault dogfood.
# Runs one pipeline step per cron tick. State in .gaijinn/hermes-loop-state.json.
set -euo pipefail

# Resolve symlinks so cron (workdir=project root) works whether called as
# `gaijinn-dev-loop.sh` (symlink) or `scripts/dev/gaijinn-dev-loop.sh` (direct).
SELF="$(readlink -f "$0")"
ROOT="$(cd "$(dirname "$SELF")/../.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"

exec python3 scripts/dev/hermes_development_loop.py "$@"
