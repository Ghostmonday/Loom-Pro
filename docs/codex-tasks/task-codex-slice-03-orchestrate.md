# Codex Slice 3 — Orchestrate & Supervisor API

**MASTER:** `docs/codex-tasks/MASTER-codex-fullpass.md`  
**Depends on:** Slice 2 merged

## Objective

Audit orchestrate session, API, workflow evaluator, preflight, billing integration.

## MAY edit

- `aoc_supervisor/aoc_supervisor/{api,orchestrate_session,workflow_evaluator,preflight,billing,ui_intent,repo_paths}.py`
- `tests/test_orchestrate_session.py`, `tests/test_supervisor.py`, `tests/test_workflow_evaluator.py`, `tests/test_ui_intent_smoke.py`, `tests/test_preflight.py`

## MUST NOT edit

- `ui/gaijinn-terminal.html` (Cursor slice after this merges)

## Acceptance

```bash
export GAIJINN_MOCK_GRID=1
pytest tests/test_orchestrate_session.py tests/test_supervisor.py tests/test_workflow_evaluator.py tests/test_ui_intent_smoke.py -q
```

Report: `.gaijinn/codex/slice-03-report.md`
