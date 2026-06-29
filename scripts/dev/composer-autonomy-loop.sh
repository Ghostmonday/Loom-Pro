#!/usr/bin/env bash
# Keep council→Composer bridge alive while user is away.
# Runs watcher + health checks on an interval until stopped.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

INTERVAL="${GAIJINN_AUTONOMY_INTERVAL_SEC:-60}"
PIDFILE="${ROOT}/.gaijinn/composer-autonomy.pid"
LOG="${ROOT}/.gaijinn/composer-autonomy.log"

mkdir -p "${ROOT}/.gaijinn"
echo $$ > "$PIDFILE"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

log "autonomy loop started pid=$$ interval=${INTERVAL}s"

trap 'log "autonomy loop stopped"; rm -f "$PIDFILE"; exit 0' INT TERM

while true; do
  log "tick: cron-supervisor"
  bash scripts/dev/composer-cron-supervisor.sh >> "${ROOT}/.gaijinn/composer-supervisor.log" 2>&1 || log "supervisor exit $?"
  log "tick: council-composer-watcher"
  bash scripts/dev/council-composer-watcher.sh >> "$LOG" 2>&1 || log "watcher exit $?"
  log "tick: hermes-development-loop"
  bash scripts/dev/hermes-development-loop.sh >> "${ROOT}/.gaijinn/hermes-loop.log" 2>&1 || log "hermes-loop exit $?"
  log "tick: memory-execution-loop"
  bash scripts/dev/memory-execution-loop.sh >> "${ROOT}/.gaijinn/memory-loop.log" 2>&1 || log "memory-loop exit $?"
  if curl -sf http://127.0.0.1:8082/api/v1/health >/dev/null 2>&1; then
    log "tick: vault serve :8082 up"
  else
    log "tick: vault serve :8082 down"
  fi
  sleep "$INTERVAL"
done