# Loom C13 — Vision Canvas Q&A JS (LOOM-207)

**Depends on:** C12

## Objective

`ui/intent-forge.js`: dispatch `intake.start_session`, `question.submit_answer` per map. Exactly-one question invariant. Readiness panel updates from GET session.

## MAY edit

- `ui/intent-forge.js` (new)
- `tests/test_loom_ui_contract.py`

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_ui_contract.py -q --no-cov
```