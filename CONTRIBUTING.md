# Contributing

- Run `pytest` before opening a PR. All tests must pass.
- Run `ruff check .` and `ruff format --check .`. The repo is Ruff-clean.
- Run `bash scripts/ci/acceptance.sh` to verify the E2E workflow.
- Keep coverage at or above the current baseline.
- No network calls in core local flows.
- Use deterministic, explicit patterns. Prefer small isolated modules.
