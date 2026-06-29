#!/usr/bin/env bash
# Backend gears — acceptance green + prompt coverage tooling (pre-dogfood).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TASK_FILE="${ROOT}/docs/codex-tasks/task-backend-gears.md"
OUT_DIR="${ROOT}/.gaijinn/codex"

if pgrep -af '[c]odex exec' >/dev/null 2>&1; then
  echo "ERROR: another codex exec is already running." >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"

echo "==> Running local codex exec: backend-gears"
codex exec -C "${ROOT}" -s workspace-write \
  --output-last-message "${OUT_DIR}/backend-gears-last-message.txt" \
  --json > "${OUT_DIR}/backend-gears-run.jsonl" 2>&1 <<PROMPT
$(cat "${TASK_FILE}")

Backend gears for pre-dogfood. Acceptance must be green. prompt_coverage is internal dev tooling only.
PROMPT

echo "==> Log: ${OUT_DIR}/backend-gears-run.jsonl"