#!/usr/bin/env bash
# Install user crontab entries for Hermes vault pipeline + Composer watcher.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MARKER="# gaijinn-hermes-cron"

existing="$(crontab -l 2>/dev/null | grep -v "$MARKER" | grep -v "council-composer-watcher" | grep -v "hermes-development-loop" | grep -v "memory-execution-loop" || true)"

cat <<EOF | { echo "$existing"; cat; } | crontab -
$MARKER
*/3 * * * * cd $ROOT && bash scripts/dev/council-composer-watcher.sh >> .gaijinn/composer-watcher.log 2>&1
*/15 * * * * cd $ROOT && bash scripts/dev/hermes-development-loop.sh >> .gaijinn/hermes-loop.log 2>&1
*/30 * * * * cd $ROOT && bash scripts/dev/memory-execution-loop.sh >> .gaijinn/memory-loop.log 2>&1
EOF

echo "Installed Hermes crons:"
crontab -l | grep -A3 "$MARKER"