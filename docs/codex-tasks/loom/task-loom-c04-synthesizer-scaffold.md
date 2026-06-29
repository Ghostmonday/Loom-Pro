# Loom C04 — Blueprint Synthesizer Scaffold (LOOM-203)

**Intent:** `ui/loom-pipeline-intent-map.json` → `actions.blueprint.synthesize`

## Objective

Create `aoc_supervisor/aoc_supervisor/loom_blueprint_synthesizer.py` with typed `SynthesisRequest`, `SynthesisResult`, stub `synthesize_blueprint()` raising `NotImplementedError` until C06–C08.

## MAY edit

- `aoc_supervisor/aoc_supervisor/loom_blueprint_synthesizer.py` (new)
- `tests/test_loom_synthesizer.py` (new — scaffold tests only)

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_synthesizer.py -q --no-cov
```