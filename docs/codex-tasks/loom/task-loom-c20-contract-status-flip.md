# Loom C20 — Contract Status Flip

**Depends on:** C19

## Objective

Update `ui/loom-pipeline-intent-map.json` smoke_scenarios: change `implementation_status` from `spec_only` to `shipped` for all scenarios that pass. Add `codex_slices_completed` list to `loom-system-intent-map.json`.

## MAY edit

- `ui/loom-system-intent-map.json`
- `ui/loom-pipeline-intent-map.json`
- `tests/test_loom_pipeline_intent.py`

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_pipeline_intent.py tests/test_loom_mirror_forge.py -q --no-cov
```