# Loom C05 — Synthesize API Route (LOOM-203)

**Depends on:** C04

## Objective

Add `POST /api/v1/loom/blueprint/synthesize` in `api.py`. Body: `{intent_forge_session_id, teleology_receipt?}`. Validates `HANDED_OFF`, delegates to `synthesize_blueprint` (stub OK).

## MAY edit

- `aoc_supervisor/aoc_supervisor/api.py`
- `tests/test_loom_synthesizer.py::test_synthesize_endpoint`

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_synthesizer.py::test_synthesize_endpoint -q --no-cov
```