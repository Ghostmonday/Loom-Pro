#!/usr/bin/env bash
set -u

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
workdir="$(mktemp -d "${TMPDIR:-/tmp}/gaijinn-acceptance.XXXXXX")"
python_bin="${PYTHON:-}"
status=0

if [[ -z "${python_bin}" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  else
    python_bin="python"
  fi
fi

export PYTHONPATH="${repo_root}/aoc-cli:${repo_root}/aoc_supervisor${PYTHONPATH:+:${PYTHONPATH}}"

run_step() {
  local name="$1"
  shift
  printf '[RUN] %s\n' "${name}"
  if "$@"; then
    printf '[PASS] %s\n' "${name}"
  else
    printf '[FAIL] %s\n' "${name}"
    status=1
  fi
}

run_gaijinn() {
  "${python_bin}" -m aoc_cli "$@"
}

if [[ "${GAIJINN_TEST_INJECT_FAILURE:-0}" == "1" ]]; then
  # Injected failure: run_step with a false command proves status propagation
  run_step "injected-failure" false
  unset GAIJINN_TEST_INJECT_FAILURE
  exit "${status}"
fi

rsync -a --exclude '.gaijinn' "${repo_root}/examples/tiny-python-service/" "${workdir}/"
cd "${workdir}" || exit 1
run_step "gaijinn init" run_gaijinn init --no-agent-files "Build a backend API service with tests"
run_step "gaijinn scan" run_gaijinn scan .
run_step "gaijinn analyze" run_gaijinn analyze
run_step "gaijinn compile-prompt" run_gaijinn compile-prompt
run_step "gaijinn plan" run_gaijinn plan --workers 2
run_step "gaijinn run-grid" run_gaijinn run-grid --workers 2
if [[ "${GAIJINN_SKIP_GRID_SPAWN:-1}" != "1" ]] && command -v grok >/dev/null 2>&1; then
  run_step "gaijinn grid-spawn" run_gaijinn grid-spawn --workers 2
fi
run_step "gaijinn status" run_gaijinn status --strict
run_step "gaijinn doctor" run_gaijinn doctor --strict
cd "${repo_root}" || exit 1

run_step "algorithm-wiring" bash "${repo_root}/scripts/ci/algorithm-wiring.sh"
run_step "pytest" "${python_bin}" -m pytest "${repo_root}/tests"

if [[ "${status}" -eq 0 ]]; then
  printf 'PASS acceptance workflow\n'
else
  printf 'FAIL acceptance workflow\n'
fi

printf 'Acceptance workspace: %s\n' "${workdir}"
exit "${status}"
