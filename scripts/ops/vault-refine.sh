#!/usr/bin/env bash
# vault-refine: periodic vault refinement — analyze integrity, check state, log convergence.
# Scheduled via Hermes cron every 360m (no_agent). Fixes the missing script for job id 1118eee84631.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

STATE="$ROOT/.gaijinn/hermes-loop-state.json"
LOGFILE="$ROOT/.gaijinn/vault-refine.log"

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" >> "$LOGFILE"; }

log "START vault-refine"

# 1. Run gaijinn analyze (integrity preflight / refinement)
log "  → gaijinn analyze"
gaijinn analyze 2>&1 >> "$LOGFILE" && ANALYZE_OK=true || ANALYZE_OK=false
log "  analyze pass: $ANALYZE_OK"

# 2. Check convergence state
log "  → convergence check"
if [ -f "$STATE" ]; then
  PHASE=$(python3 -c "import json; s=json.load(open('$STATE')); print(s.get('phase','unknown'))" 2>/dev/null || echo "unknown")
  CONV=$(python3 -c "import json; s=json.load(open('$STATE')); print(s.get('convergence','unknown'))" 2>/dev/null || echo "unknown")
  log "  phase=$PHASE convergence=$CONV"
else
  PHASE="no-state"
  log "  no state file found"
fi

# 3. Run gaijinn status for full picture
log "  → gaijinn status"
gaijinn status 2>&1 >> "$LOGFILE" || log "  status non-zero exit"

log "DONE vault-refine (analyze=$ANALYZE_OK phase=$PHASE)"
