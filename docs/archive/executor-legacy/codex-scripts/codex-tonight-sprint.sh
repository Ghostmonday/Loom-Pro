#!/usr/bin/env bash
# Run tonight velocity sprints via local codex exec (sequential — single session).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SPRINT="${1:-1}"
OUT_DIR="${ROOT}/.gaijinn/codex"

case "$SPRINT" in
  1) TASK="${ROOT}/docs/codex-tasks/task-tonight-merge-deliverable.md" ;;
  2) TASK="${ROOT}/docs/codex-tasks/task-tonight-scope-selector.md" ;;
  3) TASK="${ROOT}/docs/codex-tasks/task-tonight-multi-phase.md" ;;
  *)
    echo "Usage: $0 [1|2|3]" >&2
    exit 2
    ;;
esac

if pgrep -af '[c]odex exec' >/dev/null 2>&1; then
  echo "ERROR: codex exec already running" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"
echo "==> Tonight sprint ${SPRINT}: $(basename "$TASK")"
codex exec -C "${ROOT}" -s workspace-write \
  --output-last-message "${OUT_DIR}/tonight-sprint-${SPRINT}-last.txt" \
  --json > "${OUT_DIR}/tonight-sprint-${SPRINT}.jsonl" 2>&1 <<PROMPT
$(cat "${TASK}")
PROMPT
echo "==> Done sprint ${SPRINT}"