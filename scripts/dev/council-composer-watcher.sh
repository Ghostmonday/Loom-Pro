#!/usr/bin/env bash
# Council → Composer bridge for Hermes cron.
# Watches platform + vault council for @composer / ACTION:<name> and updates inbox.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"

python3 scripts/dev/council_composer_watcher.py "$@"