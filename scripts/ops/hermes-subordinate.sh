#!/usr/bin/env bash
# Spawn an isolated Hermes worker (subordinate) for MiniMax M3 orchestrator Q&A.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: hermes-subordinate \"question for Hermes worker\"" >&2
  echo "Runs: hermes-worker --yolo -z \"...\"" >&2
  exit 1
fi

PROMPT="$*"
exec hermes-worker --yolo -z "$PROMPT"