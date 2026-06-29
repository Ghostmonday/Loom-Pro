# Loom C18 — Mirror Handoff → Prepare (LOOM-209 partial)

**Depends on:** C02, C01, C08 (synthesis optional stub)

## Objective

Implement `run_loom_pipeline_scenario` steps for `flow.loom_handoff_to_prepare`. Wire `dispatch_loom_action` for `blueprint.synthesize` when C08 done.

## MAY edit

- `aoc_supervisor/aoc_supervisor/ui_intent.py`
- `ui/loom-pipeline-intent-map.json` (flip scenario status)
- `tests/test_loom_mirror_forge.py::test_handoff_to_prepare`

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_mirror_forge.py::test_handoff_to_prepare -q --no-cov
```