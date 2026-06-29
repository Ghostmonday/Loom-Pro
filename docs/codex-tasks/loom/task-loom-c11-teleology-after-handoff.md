# Loom C11 — Teleology After Handoff (LOOM-204)

**Depends on:** C09, C03

## Objective

After `accept_handoff`, optionally invoke teleology receipt collection before synthesis (service hook or documented call sequence in `intent_forge_service` / new `loom_pipeline.py` coordinator).

## MAY edit

- `aoc_supervisor/aoc_supervisor/intent_forge_service.py` OR `loom_pipeline.py` (new thin coordinator)
- `tests/test_loom_teleology.py::test_after_handoff`

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_teleology.py::test_after_handoff -q --no-cov
```