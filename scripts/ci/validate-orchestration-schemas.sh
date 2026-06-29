#!/usr/bin/env bash
# Validate orchestration contract fixtures against JSON schemas.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY=python3
fi

"$PY" - <<'PY'
import json
from pathlib import Path

from aoc_supervisor.orchestration_envelope import validate_orchestration_event

fixture = Path("tests/fixtures/deliberation_canonical_sequence.json")
for event in json.loads(fixture.read_text(encoding="utf-8")):
    validate_orchestration_event(event)
print(f"validated {len(json.loads(fixture.read_text(encoding='utf-8')))} fixture events")
PY