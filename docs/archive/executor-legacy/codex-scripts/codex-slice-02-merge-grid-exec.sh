#!/usr/bin/env bash
# Codex Slice 2 — Merge & Grid
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TASK_FILE="${ROOT}/docs/codex-tasks/task-codex-slice-02-merge-grid.md"
OUT_DIR="${ROOT}/.gaijinn/codex"

if pgrep -af '[c]odex exec' >/dev/null 2>&1; then
  echo "ERROR: another codex exec is already running." >&2
  pgrep -af '[c]odex exec' >&2 || true
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "==> Slice 2: Merge & Grid"
codex exec -C "${ROOT}" -s workspace-write \
  --output-last-message "${OUT_DIR}/slice-02-last-message.txt" \
  --json > "${OUT_DIR}/slice-02-run.jsonl" 2>&1 <<PROMPT
$(cat "${TASK_FILE}")
PROMPT

echo "==> Running acceptance..."
python3 -m pytest tests/test_merge*.py tests/test_handoff.py tests/test_grid_executor.py -q

echo "==> Report: ${OUT_DIR}/slice-02-report.md"
echo "==> Log: ${OUT_DIR}/slice-02-run.jsonl"
echo "==> Done."
