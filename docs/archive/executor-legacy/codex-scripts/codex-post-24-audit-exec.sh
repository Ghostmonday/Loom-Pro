#!/usr/bin/env bash
# Post-24-failure audit & robustness — Codex verifies shipped fixes, audits gaps, hardens.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TASK_FILE="${ROOT}/docs/codex-tasks/task-fix-24-test-failures.md"
OUT_DIR="${ROOT}/.gaijinn/codex"

if pgrep -af '[c]odex exec' >/dev/null 2>&1; then
  echo "ERROR: another codex exec is already running." >&2
  pgrep -af '[c]odex exec' >&2 || true
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "==> Running local codex exec: post-24 audit & robustness"
codex exec -C "${ROOT}" -s workspace-write \
  --output-last-message "${OUT_DIR}/post-24-audit-last-message.txt" \
  --json > "${OUT_DIR}/post-24-audit-run.jsonl" 2>&1 <<PROMPT
$(cat "${TASK_FILE}")

The 24 failures are already fixed on main (ad150c0). Do NOT re-implement Categories A/B/C.
Verify suite green, audit for gaps, implement only open robustness items, write report to .gaijinn/codex/post-24-audit-report.md, council-post when done.
PROMPT

echo "==> Report: ${OUT_DIR}/post-24-audit-report.md"
echo "==> Log: ${OUT_DIR}/post-24-audit-run.jsonl"
echo "==> Summary: ${OUT_DIR}/post-24-audit-last-message.txt"