#!/usr/bin/env bash
# Composer supervisor — watches Hermes cron outputs and applies minimal adjustments.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VAULT="${ROOT}/vaults/gaijinn-memory-fs"
LOG="${ROOT}/.gaijinn/composer-supervisor.log"
REPORT="${ROOT}/.gaijinn/cron-supervisor-report.json"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

cd "$ROOT"
export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor"
export GAIJINN_PROJECT_ROOT="${VAULT}"
export GAIJINN_OPERATOR=1

hermes_phase="$(python3 -c "import json;print(json.load(open('.gaijinn/hermes-loop-state.json')).get('phase','?'))" 2>/dev/null || echo '?')"
convergence="$(python3 -c "
import json
from pathlib import Path
p=Path('vaults/gaijinn-memory-fs/.gaijinn/merge/governance.json')
if p.exists():
    print(json.load(open(p)).get('structural_score',{}).get('convergence','?'))
else: print('none')
" 2>/dev/null || echo '?')"
merged="$(python3 -c "
import json
from pathlib import Path
p=Path('vaults/gaijinn-memory-fs/.gaijinn/merge/governance.json')
if p.exists():
    print(json.load(open(p)).get('structural_score',{}).get('merged_workers',0))
else: print(0)
" 2>/dev/null || echo 0)"

log "supervisor: hermes_phase=$hermes_phase convergence=$convergence merged=$merged"

action="none"
if [[ "$merged" == "0" && "$hermes_phase" == "idle" ]]; then
  log "adjust: stale idle with 0 merges — forcing hermes loop"
  bash scripts/dev/hermes-development-loop.sh --force >>"$LOG" 2>&1 || true
  action="hermes_loop_force"
fi

if [[ "$convergence" != "none" && "$convergence" != "?" ]]; then
  python3 - <<'PY' "$convergence" "$merged" "$hermes_phase" "$action" "$REPORT"
import json, sys
from datetime import datetime, timezone
from pathlib import Path
conv, merged, phase, action, path = sys.argv[1:6]
spawn_active = Path(".gaijinn/hermes-spawn.pid").exists()
progressing = float(conv) > 0.6667 or int(merged) > 0 or phase in {"spawn", "wait_spawn", "merge"} or spawn_active
payload = {
    "schema_version": 1,
    "at": datetime.now(timezone.utc).isoformat(),
    "hermes_phase": phase,
    "convergence": conv,
    "merged_workers": int(merged),
    "progressing": progressing,
    "last_adjustment": action,
    "vault": "vaults/gaijinn-memory-fs",
}
open(path, "w").write(json.dumps(payload, indent=2) + "\n")
print(json.dumps(payload))
PY
fi

if [[ "$action" != "none" ]]; then
  gaijinn council say --global --as cursor \
    "CRON SUPERVISOR: adjustment=$action phase=$hermes_phase merged=$merged convergence=$convergence" \
    2>/dev/null || true
fi