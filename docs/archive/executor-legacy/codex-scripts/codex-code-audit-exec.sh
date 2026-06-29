#!/usr/bin/env bash
# Run read-only code audit via local codex exec.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TASK_FILE="${ROOT}/docs/codex-tasks/task-code-audit.md"
OUT_DIR="${ROOT}/.gaijinn/codex"

if pgrep -af '[c]odex exec' >/dev/null 2>&1; then
  echo "ERROR: another codex exec is already running." >&2
  pgrep -af '[c]odex exec' >&2 || true
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "==> Running local codex exec: code-audit (read-only)"
codex exec -C "${ROOT}" -s workspace-write \
  --output-last-message "${OUT_DIR}/code-audit-last-message.txt" \
  --json > "${OUT_DIR}/code-audit-run.jsonl" 2>&1 <<PROMPT
$(cat "${TASK_FILE}")

Write the audit report only. Do not modify any source files.
PROMPT

echo "==> Report: ${OUT_DIR}/code-audit-report.md"
echo "==> Log: ${OUT_DIR}/code-audit-run.jsonl"
echo "==> Summary: ${OUT_DIR}/code-audit-last-message.txt"