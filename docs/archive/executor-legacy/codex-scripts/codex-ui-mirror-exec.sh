#!/usr/bin/env bash
# Setup Codex UI mirror env and submit/run the task contract.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TASK_FILE="${ROOT}/docs/codex-tasks/ui-mirror-task.md"
OUT_DIR="${ROOT}/.gaijinn/codex"
CODEX_ENV="${CODEX_ENV:-Ghostmonday/Gaijinn}"
MODE="${1:-tasks}"  # tasks | local

"${ROOT}/scripts/codex/codex-ui-mirror-setup.sh"

case "$MODE" in
  tasks|cloud)
    echo "==> Submitting Codex Cloud task (env=${CODEX_ENV})"
    codex cloud exec --env "${CODEX_ENV}" --branch "$(git rev-parse --abbrev-ref HEAD)" "$(cat "${TASK_FILE}")"
    ;;
  local|exec)
    echo "==> Running local codex exec (workspace-write)"
    mkdir -p "${OUT_DIR}"
    codex exec -C "${ROOT}" -s workspace-write \
      --output-last-message "${OUT_DIR}/last-message.txt" \
      --json > "${OUT_DIR}/run.jsonl" 2>&1 <<PROMPT
$(cat "${TASK_FILE}")

Objective: confusion_count == 0 on flow.pkm_greenfield_intent. Baseline already passes.
Run verification after every change:
.venv/bin/python -m pytest tests/test_workflow_evaluator.py::test_pkm_workflow_zero_confusion_mock -q
PROMPT
    echo "==> Local run log: ${OUT_DIR}/run.jsonl"
    ;;
  *)
    echo "Usage: $0 [tasks|local]" >&2
    exit 2
    ;;
esac