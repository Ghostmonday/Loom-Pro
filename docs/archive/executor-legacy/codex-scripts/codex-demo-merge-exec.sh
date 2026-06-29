#!/usr/bin/env bash
# Run demo-merge-loop task via local codex exec (workspace-write).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TASK_FILE="${ROOT}/docs/codex-tasks/task-demo-merge-loop.md"
OUT_DIR="${ROOT}/.gaijinn/codex"
MODE="${1:-local}"

if pgrep -af '[c]odex exec' >/dev/null 2>&1; then
  echo "ERROR: another codex exec is already running. Wait or kill it first." >&2
  pgrep -af '[c]odex exec' >&2 || true
  exit 1
fi

mkdir -p "${OUT_DIR}"

case "$MODE" in
  local|exec)
    echo "==> Running local codex exec: demo-merge-loop"
    codex exec -C "${ROOT}" -s workspace-write \
      --output-last-message "${OUT_DIR}/demo-merge-last-message.txt" \
      --json > "${OUT_DIR}/demo-merge-run.jsonl" 2>&1 <<PROMPT
$(cat "${TASK_FILE}")

After implementation, run full verification and commit with message:
"feat(demo): wire post-sprint merge loop into API, terminal, and evaluator"
PROMPT
    echo "==> Log: ${OUT_DIR}/demo-merge-run.jsonl"
    echo "==> Summary: ${OUT_DIR}/demo-merge-last-message.txt"
    ;;
  *)
    echo "Usage: $0 [local]" >&2
    exit 2
    ;;
esac