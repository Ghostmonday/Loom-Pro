#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -m pytest
python3 -m validator.cli.main --project examples/passing/frontend-formation.yaml --spec-dir specification
set +e
python3 -m validator.cli.main --project examples/failing/frontend-formation.yaml --spec-dir specification >/dev/null
status=$?
set -e
if [[ "$status" -ne 1 ]]; then
  echo "Expected failing fixture to exit 1; got $status" >&2
  exit 1
fi
echo "Verification complete."
