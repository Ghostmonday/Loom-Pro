# Loom C17 — Terminal Forge Session Gate (LOOM-208)

**Depends on:** C01

## Objective

`terminal.js`: require `forge_session_id` query param or sessionStorage from handoff. `orchestrate.prepare` body includes `intent_forge_session_id`. Block raw `chat.submit_intent` otherwise.

## MAY edit

- `ui/terminal.js`
- `ui/loom-ui-intent-map.json` (`chat.submit_intent` postconditions)
- `tests/test_ui_intent_smoke.py`

## Verify

```bash
.venv/bin/python -m pytest tests/test_ui_intent_smoke.py -q --no-cov -k handoff
```