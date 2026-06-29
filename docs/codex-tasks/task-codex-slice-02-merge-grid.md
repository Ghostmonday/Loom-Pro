# Codex Slice 2 — Merge / Collect / Grid

**MASTER:** `docs/codex-tasks/MASTER-codex-fullpass.md`  
**Depends on:** Slice 1 merged

## Objective

Audit and harden merge pipeline, handoff, collect, grid spawn/executor.

## MAY edit

- `aoc-cli/aoc_cli/helpers/{merge,handoff,scan,grid_executor,workers}.py`
- `aoc-cli/aoc_cli/commands/{collect,validate_worker,merge_grid,run_grid,grid_spawn}.py`
- `tests/test_merge*.py`, `tests/test_handoff.py`, `tests/test_grid_executor.py`, `tests/test_transaction_bus_integration.py`

## MUST NOT edit

- `ui/**`, `intent_blueprint.py`, inference modules

## Acceptance

```bash
pytest tests/test_merge.py tests/test_merge_integrity.py tests/test_handoff.py tests/test_grid_executor.py -q
```

Report: `.gaijinn/codex/slice-02-report.md`