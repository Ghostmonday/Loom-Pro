# Loom C19 — Full Pipeline Mirror (LOOM-209)

**Depends on:** C01–C11, C18

**Smoke:** `flow.loom_full_pipeline_mock`

## Objective

`UiIntentDriver.run_and_verify_scenario('flow.loom_full_pipeline_mock')` passes with zero workflow confusion. All pipeline actions dispatched per `loom-pipeline-intent-map.json`.

## MAY edit

- `aoc_supervisor/aoc_supervisor/ui_intent.py`
- `aoc_supervisor/aoc_supervisor/intent_mirror.py`
- `tests/test_loom_mirror_forge.py::test_full_pipeline_mock`

## Verify

```bash
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_RAW_INTENT_PREPARE=1
.venv/bin/python -m pytest tests/test_loom_mirror_forge.py::test_full_pipeline_mock -q --no-cov
```

## Acceptance

- `prepare.blueprint_mode == loom_synthesis`
- `merge_pipeline.phase == completed`
- `workflow_evaluator` confusion_count == 0