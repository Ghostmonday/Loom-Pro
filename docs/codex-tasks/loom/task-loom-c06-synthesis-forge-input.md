# Loom C06 — Synthesis Forge Input (LOOM-203)

**Depends on:** C04, C05

## Objective

Implement `synthesize_blueprint` step 1: load `executable_projection` from HANDED_OFF forge session via `IntentForgeService.get_session`.

## MAY edit

- `aoc_supervisor/aoc_supervisor/loom_blueprint_synthesizer.py`
- `tests/test_loom_synthesizer.py::test_forge_projection_input`

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_synthesizer.py::test_forge_projection_input -q --no-cov
```