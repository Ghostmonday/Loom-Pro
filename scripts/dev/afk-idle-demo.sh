#!/usr/bin/env bash
# Live demo: mark Composer idle → AFK daemon detects → grok wakes Composer → heartbeat updates.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

AFK="${ROOT}/.gaijinn/afk"
LOG="${AFK}/demo.log"
DEMO_PROMPT="${AFK}/demo-wake-prompt.txt"

log() { echo "$(date -u +%H:%M:%SZ) $*" | tee -a "$LOG"; }

: >"$LOG"
log "=== AFK IDLE → WAKE DEMO ==="

log "STEP 1: Mark Composer IDLE (stale heartbeat)"
python3 scripts/dev/composer-heartbeat.py mark-idle --note "demo: Amir walked away"
python3 scripts/dev/composer-heartbeat.py status | tee -a "$LOG"

log "STEP 2: Idle detection (daemon logic)"
python3 - <<'PY' | tee -a "$LOG"
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path("scripts/dev").resolve()))
# inline idle check
import importlib.util
spec = importlib.util.spec_from_file_location("hb", "scripts/dev/composer-heartbeat.py")
hb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hb)
idle = hb.is_idle()
print(f"detect_idle={idle} threshold_sec={hb.IDLE_SEC}")
if not idle:
    print("ERROR: expected idle=true")
    sys.exit(1)
PY

log "STEP 3: Build wake prompt (single turn, fast)"
cat >"$DEMO_PROMPT" <<'EOF'
# WAKE — Composer 2.5 @ Grok Build beta

You were **idle**. The AFK daemon detected stale heartbeat and woke you.

## Do exactly this (one turn):
1. Run: `python3 scripts/dev/composer-heartbeat.py touch`
2. Run: `gaijinn council say --global --as cursor "AFK WAKE: Composer 2.5 resumed by idle detector demo. Heartbeat fresh."`
3. Run: `.venv/bin/python -m pytest tests/test_promotion_gates.py -q`
4. Reply one line: `WAKE OK: <pytest summary>`

No other work. This proves idle → wake → ack.
EOF

log "STEP 4: grok headless wake (Composer 2.5)"
rm -f "${AFK}/session.json"
set +e
JSON_OUT="$(grok \
  --prompt-file "$DEMO_PROMPT" \
  --always-approve \
  --model grok-build \
  --cwd "$ROOT" \
  --max-turns 15 \
  --output-format json 2>>"$LOG")"
EXIT=$?
set -e
printf '%s' "$JSON_OUT" >>"${AFK}/demo-grok.json" 2>/dev/null || echo "$JSON_OUT" >>"$LOG"

if [[ -n "$JSON_OUT" ]]; then
  printf '%s' "$JSON_OUT" | python3 -c "
import json,sys
from pathlib import Path
raw=sys.stdin.read()
try: d=json.loads(raw)
except: sys.exit(0)
sid=d.get('sessionId')
if sid:
    Path(sys.argv[1]).write_text(json.dumps({'sessionId':sid},indent=2)+'\n')
" "${AFK}/session.json" 2>/dev/null || true
fi
log "grok exit=$EXIT"

log "STEP 5: Verify heartbeat + council"
python3 scripts/dev/composer-heartbeat.py status | tee -a "$LOG"
python3 - <<'PY' | tee -a "$LOG"
import json
from pathlib import Path
hb = json.loads(Path(".gaijinn/composer-heartbeat.json").read_text())
idle_sec = __import__("datetime").datetime.fromisoformat(hb["last_ack_at"].replace("Z","+00:00"))
from datetime import datetime, timezone
age = (datetime.now(timezone.utc) - idle_sec).total_seconds()
print(f"heartbeat_age_sec={age:.1f} status={hb.get('status')}")
if age > 120:
    raise SystemExit("FAIL: heartbeat still stale")
print("PASS: Composer woke and acked")
PY

log "STEP 6: Council tail (last AFK wake line)"
grep -i "AFK WAKE" ~/.gaijinn/bridge/council.md 2>/dev/null | tail -1 | tee -a "$LOG" || log "(council line pending)"

log "=== DEMO COMPLETE ==="
echo ""
echo "Full log: $LOG"
echo "Heartbeat: .gaijinn/composer-heartbeat.json"