#!/usr/bin/env bash
# Codex Slice 3 — Orchestrate & API
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TASK_FILE="${ROOT}/docs/codex-tasks/task-codex-slice-03-orchestrate.md"
OUT_DIR="${ROOT}/.gaijinn/codex"

if pgrep -af '[c]odex exec' >/dev/null 2>&1; then
  echo "ERROR: another codex exec is already running." >&2
  pgrep -af '[c]odex exec' >&2 || true
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "==> Slice 3: Orchestrate & API"
codex exec -C "${ROOT}" -s workspace-write \
  --output-last-message "${OUT_DIR}/slice-03-last-message.txt" \
  --json > "${OUT_DIR}/slice-03-run.jsonl" 2>&1 <<PROMPT
$(cat "${TASK_FILE}")
PROMPT

echo "==> Running acceptance..."
python3 -m pytest tests/test_orchestrate_session.py tests/test_supervisor.py tests/test_workflow_evaluator.py tests/test_ui_intent_smoke.py -q

echo "==> Report: ${OUT_DIR}/slice-03-report.md"
echo "==> Log: ${OUT_DIR}/slice-03-run.jsonl"
echo "==> Done."
