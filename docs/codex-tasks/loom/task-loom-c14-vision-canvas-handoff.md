# Loom C14 — Vision Canvas Handoff (LOOM-207)

**Depends on:** C13, C02

## Objective

Wire `handoff.confirm` + `handoff.accept` in `intent-forge.js`. Redirect to `handoff_target` from map with `session_id`.

## MAY edit

- `ui/intent-forge.js`
- `ui/loom-intent-forge-intent-map.json` (if handoff_target needs tweak)

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_ui_contract.py::test_intent_forge_handoff_actions -q --no-cov
```