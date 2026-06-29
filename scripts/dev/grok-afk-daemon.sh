#!/usr/bin/env bash
# Non-stop AFK daemon: pings headless Grok until the agent writes .gaijinn/afk/done
# or you touch .gaijinn/afk/stop
#
# Start:  bash scripts/dev/grok-afk-daemon.sh
# Stop:   touch .gaijinn/afk/stop
# Status: tail -f .gaijinn/afk/daemon.log
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

AFK="${ROOT}/.gaijinn/afk"
MISSION="${AFK}/mission.md"
DONE="${AFK}/done"
STOP="${AFK}/stop"
SESSION="${AFK}/session.json"
AFK_MODE="${AFK_MODE:-worker}"
case "$AFK_MODE" in
  composer-lead)
    PROMPT_TMPL="${ROOT}/scripts/dev/afk-ping-composer-lead.md"
    ;;
  *)
    PROMPT_TMPL="${ROOT}/scripts/dev/afk-ping-prompt.md"
    ;;
esac
if [[ -n "${AFK_PROMPT_FILE:-}" ]]; then
  PROMPT_TMPL="$AFK_PROMPT_FILE"
fi
LOG="${AFK}/daemon.log"
PIDFILE="${AFK}/daemon.pid"

INTERVAL="${AFK_INTERVAL_SEC:-90}"
MAX_TURNS="${AFK_MAX_TURNS:-60}"
MODEL="${AFK_MODEL:-grok-build}"

mkdir -p "$AFK"

usage() {
  cat <<'EOF'
grok-afk-daemon — keep Grok working while you are AFK

  bash scripts/dev/grok-afk-daemon.sh          # start (clears prior done/stop)
  bash scripts/dev/grok-afk-daemon.sh --continue  # keep session, don't clear done

Stop:
  touch .gaijinn/afk/stop
  kill "$(cat .gaijinn/afk/daemon.pid)"

Agent stops itself:
  writes .gaijinn/afk/done when mission acceptance criteria are met

Edit mission before starting:
  .gaijinn/afk/mission.md
EOF
}

CONTINUE=0
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
if [[ "${1:-}" == "--continue" ]]; then
  CONTINUE=1
fi

LOCKFILE="${AFK}/daemon.lock"
exec 9>"$LOCKFILE"
if ! flock -n 9; then
  echo "afk-daemon already running (lock held) — stop with: touch .gaijinn/afk/stop"
  exit 1
fi

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "afk-daemon already running pid=$old_pid — stop with: touch .gaijinn/afk/stop"
    exit 1
  fi
  rm -f "$PIDFILE"
fi

if [[ ! -f "$MISSION" ]]; then
  echo "missing $MISSION — create it first (see .gaijinn/afk/mission.example.md)"
  exit 1
fi

if [[ "$CONTINUE" -eq 0 ]]; then
  rm -f "$DONE" "$STOP" "$SESSION"
fi

log() {
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >>"$LOG"
}

cleanup() {
  log "afk-daemon stopped (signal)"
  rm -f "$PIDFILE"
  exit 0
}
trap cleanup INT TERM

echo $$ >"$PIDFILE"
log "afk-daemon started pid=$$ interval=${INTERVAL}s max_turns=$MAX_TURNS model=$MODEL mode=$AFK_MODE"

if ! command -v grok >/dev/null 2>&1; then
  log "ERROR: grok not on PATH"
  rm -f "$PIDFILE"
  exit 1
fi

build_prompt() {
  local mission_text
  mission_text="$(cat "$MISSION")"
  local tmpl
  tmpl="$(cat "$PROMPT_TMPL")"
  printf '%s\n\n---\n\n## MISSION (from .gaijinn/afk/mission.md)\n\n%s' "$tmpl" "$mission_text"
}

session_id() {
  if [[ -f "$SESSION" ]]; then
    python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('sessionId',''))" "$SESSION" 2>/dev/null || true
  fi
}

ping=0
while [[ ! -f "$DONE" && ! -f "$STOP" ]]; do
  ping=$((ping + 1))

  IDLE_JSON="$(python3 "${ROOT}/scripts/dev/composer-heartbeat.py" status 2>/dev/null || echo '{}')"
  COMPOSER_IDLE="$(python3 -c "import json,sys; d=json.load(sys.stdin); print('true' if d.get('idle') else 'false')" <<<"$IDLE_JSON" 2>/dev/null || echo "true")"
  log "ping! #$ping composer_idle=$COMPOSER_IDLE"

  if [[ "$COMPOSER_IDLE" != "true" && "${AFK_WAKE_ONLY_WHEN_IDLE:-1}" == "1" ]]; then
    log "skip: Composer not idle (heartbeat fresh) — sleep ${INTERVAL}s"
    sleep "$INTERVAL"
    continue
  fi

  log "wake: Composer idle — launching grok"

  PROMPT_FILE="${AFK}/ping-prompt.txt"
  build_prompt >"$PROMPT_FILE"

  GROK_ARGS=()
  sid="$(session_id)"
  if [[ -n "$sid" ]]; then
    GROK_ARGS+=(--resume "$sid")
  fi
  GROK_ARGS+=(
    --prompt-file "$PROMPT_FILE"
    --always-approve
    --model "$MODEL"
    --cwd "$ROOT"
    --output-format json
    --max-turns "$MAX_TURNS"
  )

  set +e
  JSON_OUT="$(grok "${GROK_ARGS[@]}" 2>>"$LOG")"
  exit_code=$?
  set -e

  if [[ -n "$JSON_OUT" ]]; then
    printf '%s' "$JSON_OUT" | python3 -c "
import json, sys
path = sys.argv[1]
raw = sys.stdin.read()
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)
sid = data.get('sessionId')
if sid:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'sessionId': sid, 'stopReason': data.get('stopReason')}, f, indent=2)
        f.write('\n')
" "$SESSION" 2>/dev/null || true
  fi

  if [[ -f "$DONE" ]]; then
    log "agent wrote done — $(head -1 "$DONE")"
    break
  fi
  if [[ -f "$STOP" ]]; then
    log "stop file detected — exiting"
    break
  fi

  if [[ $exit_code -ne 0 ]]; then
    if grep -q "Session does not exist" <<<"$JSON_OUT" 2>/dev/null || [[ $exit_code -eq 1 ]]; then
      rm -f "$SESSION"
      log "cleared stale session.json (grok exit=$exit_code)"
    fi
    log "grok exit=$exit_code (will retry in ${INTERVAL}s)"
  else
    log "ping #$ping complete (next in ${INTERVAL}s)"
  fi

  sleep "$INTERVAL"
done

rm -f "$PIDFILE"
if [[ -f "$DONE" ]]; then
  log "afk-daemon finished — milestone reached"
else
  log "afk-daemon finished — user stop"
fi