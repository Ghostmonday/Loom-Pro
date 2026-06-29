#!/usr/bin/env bash
# Aggregate worker output.log files into a timestamped corpus archive.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT="${GAIJINN_PROJECT_ROOT:-$ROOT}"
WORKERS="$PROJECT/.gaijinn/workers"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$PROJECT/.gaijinn/corpus/sprint-$STAMP"

if [[ ! -d "$WORKERS" ]]; then
  echo "No workers dir at $WORKERS — run a sprint first." >&2
  exit 1
fi

mkdir -p "$OUT"
copied=0
for log in "$WORKERS"/worker-*/output.log; do
  [[ -f "$log" ]] || continue
  worker="$(basename "$(dirname "$log")")"
  cp "$log" "$OUT/$worker.log"
  copied=$((copied + 1))
done

if [[ -f "$WORKERS/manifest.json" ]]; then
  cp "$WORKERS/manifest.json" "$OUT/manifest.json"
fi

cat > "$OUT/meta.json" <<EOF
{
  "collected_at": "$STAMP",
  "project_root": "$PROJECT",
  "worker_logs": $copied
}
EOF

echo "Corpus saved: $OUT ($copied logs)"