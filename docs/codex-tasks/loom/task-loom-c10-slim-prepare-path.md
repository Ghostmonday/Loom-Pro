# Loom C10 — Slim Prepare Path (LOOM-205)

**Depends on:** C01

## Objective

When `executable_blueprint` or loom synthesis artifact present, skip `init/scan/analyze/compile-prompt` in `OrchestrateSessionStore.prepare`. Write blueprint directly; still compute swarm stats.

## MAY edit

- `aoc_supervisor/aoc_supervisor/orchestrate_session.py`
- `tests/test_orchestrate_session.py`

## Verify

```bash
.venv/bin/python -m pytest tests/test_orchestrate_session.py -q --no-cov -k slim
```