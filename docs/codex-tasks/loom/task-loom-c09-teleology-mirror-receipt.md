# Loom C09 — Teleology Mirror Receipt (LOOM-204 partial)

**Intent:** `ui/loom-pipeline-intent-map.json` → `actions.teleology.deliberate`

## Objective

Add `UiIntentDriver.collect_teleology_receipt(intent, session_id?)` consuming `GET /api/v1/blueprint/deliberate` SSE until `blueprint_freeze`. Store subphases + `curvature_floor` on mirror as `teleology`.

## MAY edit

- `aoc_supervisor/aoc_supervisor/ui_intent.py`
- `aoc_supervisor/aoc_supervisor/intent_mirror.py`
- `tests/test_loom_teleology.py` (new)

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_teleology.py -q --no-cov
```