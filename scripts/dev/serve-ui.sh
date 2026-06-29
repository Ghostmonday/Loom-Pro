#!/usr/bin/env bash
# Start Gaijinn supervisor for local UI development.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python3.11"
if [[ ! -x "$PY" ]]; then
  echo "Missing ${PY}. Run: python3.11 -m venv .venv && .venv/bin/python3.11 -m pip install -e '.[api]'" >&2
  exit 1
fi

"$PY" -m pip install -q -e ".[api]" 2>/dev/null || true
export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor"
exec "$PY" -m uvicorn aoc_supervisor.api:app --reload --host 127.0.0.1 --port 8080