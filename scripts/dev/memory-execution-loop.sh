#!/usr/bin/env bash
# Memory ↔ Execution loop — one measurable cycle for platform + vault joint health.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VAULT="${ROOT}/vaults/gaijinn-memory-fs"
OUT="${ROOT}/.gaijinn/loop-state.json"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cd "$ROOT"
export PYTHONPATH="${ROOT}/aoc-cli:${ROOT}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"

mirror_passed=false
vault_linter_passed=false
vault_linter_skipped=false
pytest_exit=1
vault_exit=1

if python3 -m pytest \
  tests/test_gui_equivalence.py \
  tests/test_promotion_gates.py \
  tests/test_ui_intent_smoke.py -q --tb=no 2>/dev/null; then
  mirror_passed=true
  pytest_exit=0
fi

if [[ -f "${VAULT}/10_Operations/knowledge-linter.py" ]]; then
  if python3 "${VAULT}/10_Operations/knowledge-linter.py" --worker-gate; then
    vault_linter_passed=true
    vault_exit=0
  fi
else
  vault_linter_skipped=true
  vault_exit=0
fi

loop_passed=false
if $mirror_passed && { $vault_linter_passed || $vault_linter_skipped; }; then
  loop_passed=true
fi

mkdir -p "$(dirname "$OUT")"
python3 - <<PY "$OUT" "$TS" "$pytest_exit" "$vault_exit" "$vault_linter_skipped"
import json, sys
from pathlib import Path
out, ts, pexit, vexit, vskip = sys.argv[1:6]
mirror = int(pexit) == 0
vlinter = int(vexit) == 0
skipped = vskip == "true"
loop_ok = mirror and (vlinter or skipped)
payload = {
    "schema_version": 1,
    "cycle_at": ts,
    "phases": {
        "learn": {"vault_events": "vaults/gaijinn-memory-fs/_multi-agent/events.md",
                  "platform_ops": ".gaijinn/operations/"},
        "act": {"next": "gaijinn serve + GUI deploy or plan/run-grid per project"},
        "measure": {
            "gate_1_mirror_smoke": mirror,
            "vault_knowledge_linter": vlinter and not skipped,
            "vault_linter_skipped": skipped,
        },
        "distill": {"on_pass": "append events.md + update .gaijinn/operations/",
                    "on_fail": "council say + fix before next ACT"},
    },
    "passed": loop_ok,
    "exit_codes": {"pytest_smoke": int(pexit), "vault_linter": int(vexit)},
    "spec": ".gaijinn/operations/MEMORY-EXECUTION-LOOP.md",
}
Path(out).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY

if $loop_passed; then
  echo "LOOP: PASS — learn→act→measure→distill ready for next cycle"
  exit 0
fi
echo "LOOP: FAIL — see .gaijinn/loop-state.json"
exit 1