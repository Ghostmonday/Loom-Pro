#!/usr/bin/env bash
# Launch independent Codex Cloud tasks in parallel (one PR per subsystem).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

CODEX_ENV="${CODEX_ENV:-Ghostmonday/Gaijinn}"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
OUT="${ROOT}/.gaijinn/codex/parallel-tasks.jsonl"
mkdir -p "${ROOT}/.gaijinn/codex"

# Optional: run baseline setup once (fast)
if [[ "${SKIP_SETUP:-}" != "1" ]]; then
  "${ROOT}/scripts/codex/codex-ui-mirror-setup.sh"
fi

TASKS=(
  "ui-state-machine:docs/codex-tasks/task-ui-state-machine.md"
  "intent-blueprint:docs/codex-tasks/task-intent-blueprint.md"
  "swarm-sizing:docs/codex-tasks/task-swarm-sizing.md"
  "merge-pipeline:docs/codex-tasks/task-merge-pipeline.md"
  "mirror-coverage:docs/codex-tasks/task-mirror-coverage.md"
)

: > "${OUT}"
echo "==> Launching ${#TASKS[@]} Codex Cloud tasks (env=${CODEX_ENV}, branch=${BRANCH})"

pids=()
for entry in "${TASKS[@]}"; do
  slug="${entry%%:*}"
  path="${entry#*:}"
  (
    url="$(codex cloud exec --env "${CODEX_ENV}" --branch "${BRANCH}" "$(cat "${ROOT}/${path}")" 2>&1 | tail -1)"
    printf '{"slug":"%s","task_file":"%s","url":"%s","launched_at":"%s"}\n' \
      "${slug}" "${path}" "${url}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  ) >> "${OUT}" &
  pids+=($!)
  echo "  started ${slug}"
done

for pid in "${pids[@]}"; do
  wait "${pid}" || true
done

echo "==> Task registry: ${OUT}"
cat "${OUT}"