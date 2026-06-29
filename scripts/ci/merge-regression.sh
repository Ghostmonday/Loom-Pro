#!/usr/bin/env bash
# Structural merge regression gate — proves topological merge physics without live agents.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python_bin="${PYTHON:-python3}"

export PYTHONPATH="${repo_root}/aoc-cli:${repo_root}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"

echo "[merge-regression] merge integrity + governance invariants"
"${python_bin}" -m pytest \
  "${repo_root}/tests/test_merge_integrity.py" \
  "${repo_root}/tests/test_merge.py" \
  "${repo_root}/tests/test_handoff.py" \
  -q --tb=short

echo "[merge-regression] PASS"