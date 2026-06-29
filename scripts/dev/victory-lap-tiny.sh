#!/usr/bin/env bash
# Real-agent victory lap on tiny-python-service (no GAIJINN_MOCK_GRID).
# Gateway-mode exam: coupled handoff proof with zero atomic weld units.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VICTORY="${VICTORY_DIR:-/tmp/gaijinn-victory-lap-$(date +%s)}"
GAIJINN="${GAIJINN_BIN:-$ROOT/.venv/bin/gaijinn}"
WORKERS="${WORKERS:-2}"
TIMEOUT="${GRID_SPAWN_TIMEOUT:-1800}"

unset GAIJINN_MOCK_GRID
export PATH="$ROOT/.venv/bin:$HOME/.local/bin:$PATH"
export GAIJINN_HANDOFF_GATEWAYS=1

echo "==> Victory lap workspace: $VICTORY"
rm -rf "$VICTORY"
mkdir -p "$VICTORY"
rsync -a --exclude '.gaijinn' --exclude '__pycache__' --exclude '.pytest_cache' --exclude '.git' \
  "$ROOT/examples/tiny-python-service/" "$VICTORY/"

cd "$VICTORY"

cat >> .gitignore <<'EOF'
WORK_UNIT.md
WORKER_INTENT.txt
intent.txt
giv.json
metadata.json
output.log
__pycache__/
.pytest_cache/
EOF

git init -b main >/dev/null
git add -A
git commit -m "victory lap: coupled tiny-python-service (gateway mode)" >/dev/null

echo "==> Gaijinn preflight (GAIJINN_HANDOFF_GATEWAYS=1)"
"$GAIJINN" init --force --no-agent-files \
  "Handoff gateway victory lap: tests worker adds DONE_STATUS assertion via HANDOFF ticket; service worker applies DONE_STATUS in tiny_service/service.py. No sibling trespass."
"$GAIJINN" scan .
"$GAIJINN" analyze
"$GAIJINN" compile-prompt
"$GAIJINN" plan --workers "$WORKERS"

echo "==> Structural audit (weld vs gateway telemetry)"
"$GAIJINN" audit .

# Two-unit handoff blueprint: zero atomic weld units, explicit depends_on gateway.
python3 <<'PY'
import json
from pathlib import Path

blueprint = {
    "schema_version": 1,
    "project_goal": "Handoff gateway victory lap — cross-worker transaction bus proof",
    "assumptions": [
        "Handoff gateway mode: dark-bridge couplings are HANDOFF_ONLY transaction boundaries, not atomic welds.",
        "Tests worker emits HANDOFF ticket; service worker ingests and mutates tiny_service/service.py.",
    ],
    "work_units": [
        {
            "id": "WU-001",
            "title": "Tests require service handoff gateway",
            "description": (
                "Add test_service_done_status_constant in tests/test_api.py importing DONE_STATUS "
                "from tiny_service.service. Do NOT edit tiny_service/service.py — emit HANDOFF ticket."
            ),
            "allowed_paths": ["tests/test_api.py"],
            "denied_paths": [],
            "depends_on": ["WU-002"],
            "acceptance_checks": ["pytest"],
            "estimated_risk": "medium",
        },
        {
            "id": "WU-002",
            "title": "Service layer handoff gateway target",
            "description": (
                "Apply pending HANDOFF mutations: add DONE_STATUS = \"done\" to tiny_service/service.py. "
                "Ingest any HANDOFF INGEST block tickets before editing."
            ),
            "allowed_paths": ["tiny_service/service.py"],
            "denied_paths": [],
            "depends_on": [],
            "acceptance_checks": ["pytest"],
            "estimated_risk": "medium",
        },
    ],
    "dependencies": {"WU-001": ["WU-002"], "WU-002": []},
    "risks": [
        "Handoff gateway: tests/test_api.py -> tiny_service/service.py — emit HANDOFF ticket, do not weld",
    ],
}
path = Path(".gaijinn/blueprint.json")
path.write_text(json.dumps(blueprint, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"Wrote handoff-gateway blueprint → {path}")
PY

"$GAIJINN" run-grid --workers "$WORKERS" --force

MANIFEST="$VICTORY/.gaijinn/workers/manifest.json"
echo "==> Worker mode: $(python3 -c "import json; print(json.load(open('$MANIFEST'))['mode'])")"

echo "==> grid-spawn (real grok, timeout=${TIMEOUT}s)"
"$GAIJINN" grid-spawn --workers "$WORKERS" --timeout "$TIMEOUT"

echo "==> Post-sprint merge pipeline"
"$GAIJINN" collect
"$GAIJINN" validate-worker
MERGE_ARGS=(merge-grid)
if [[ "${SKIP_MERGE_TESTS:-0}" == "1" ]]; then
  MERGE_ARGS+=(--no-test)
fi
"$GAIJINN" "${MERGE_ARGS[@]}"

echo ""
echo "==> HANDOFF QUEUE"
if [[ -f "$VICTORY/.gaijinn/merge/handoff-queue.json" ]]; then
  python3 -m json.tool "$VICTORY/.gaijinn/merge/handoff-queue.json"
else
  echo "(no handoff-queue.json)"
fi

echo ""
echo "==> COUNCIL HANDOFF RECEIPTS"
if [[ -f "$VICTORY/.gaijinn/bridge/council.jsonl" ]]; then
  python3 -c "
import json
from pathlib import Path
for line in Path('$VICTORY/.gaijinn/bridge/council.jsonl').read_text().splitlines():
    if not line.strip():
        continue
    msg = json.loads(line)
    if msg.get('type') in ('HANDOFF_TRANSACTION_REQUEST', 'HANDOFF_TRANSACTION_RECEIPT'):
        print(json.dumps(msg, indent=2))
"
else
  echo "(no council.jsonl)"
fi

echo ""
echo "==> GOVERNANCE SCORE"
python3 -m json.tool "$VICTORY/.gaijinn/merge/governance.json"

echo ""
echo "==> MERGE PIPELINE"
"$GAIJINN" status --json | python3 -c "import json,sys; p=json.load(sys.stdin); print(json.dumps(p.get('merge_pipeline',p), indent=2))"

echo ""
echo "Victory lap complete: $VICTORY"