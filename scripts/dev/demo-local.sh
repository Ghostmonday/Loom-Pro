#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
workdir="$(mktemp -d "${TMPDIR:-/tmp}/gaijinn-demo-local.XXXXXX")"

cp -R "${repo_root}/examples/tiny-python-service/." "${workdir}/"
cd "${workdir}"

export PYTHONPATH="${repo_root}/aoc-cli:${repo_root}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"

python_bin="${PYTHON:-}"
if [[ -z "${python_bin}" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  else
    python_bin="python"
  fi
fi

run_gaijinn() {
  printf '+ gaijinn'
  printf ' %q' "$@"
  printf '\n'
  "${python_bin}" -m aoc_cli "$@"
}

run_gaijinn init --no-agent-files "Build a backend API service with tests"
run_gaijinn scan .
run_gaijinn analyze
run_gaijinn compile-prompt
run_gaijinn plan --workers 2
run_gaijinn run-grid --workers 2
if [[ "${GAIJINN_SKIP_GRID_SPAWN:-1}" != "1" ]] && command -v grok >/dev/null 2>&1; then
  run_gaijinn grid-spawn --workers 2
fi
run_gaijinn status --strict

printf 'Demo workspace: %s\n' "${workdir}"
