# Loom C16 — Command Engine Deliberate Step (LOOM-206)

**Depends on:** C09, C18

**Intent:** `ui/command-engine-ui-intent-map.json` + `loom-pipeline` teleology action

## Objective

Minimal `ui/command-engine.html` + `command-engine.js`: read `session_id` query, run `deliberate.start` (SSE), show subphases, then button → `orchestrate.prepare` with `intent_forge_session_id`.

## MAY edit

- `ui/command-engine.html`, `ui/command-engine.js` (new)
- `aoc_supervisor/aoc_supervisor/routers/static_ui.py` (`/command-engine`)
- `tests/test_loom_ui_contract.py::test_command_engine`

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_ui_contract.py::test_command_engine -q --no-cov
```