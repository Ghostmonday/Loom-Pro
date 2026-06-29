#!/usr/bin/env bash
# Bootstrap Codex UI mirror iteration environment + baseline score.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export GAIJINN_MOCK_GRID=1
export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"

if [[ ! -x .venv/bin/python ]]; then
  echo "==> Creating venv"
  python3 -m venv .venv
  .venv/bin/pip install -q -e aoc-cli -e aoc_supervisor pytest
fi

echo "==> Baseline: PKM workflow confusion test"
.venv/bin/python -m pytest tests/test_workflow_evaluator.py::test_pkm_workflow_zero_confusion_mock -q

echo "==> Task contract: docs/codex-tasks/ui-mirror-task.md"
echo "==> Ready for: codex exec -C $ROOT -s workspace-write \"\$(cat docs/codex-tasks/ui-mirror-task.md)\""