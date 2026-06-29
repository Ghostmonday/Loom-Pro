# Loom C12 — Vision Canvas HTML Shell (LOOM-207)

**Intent:** `ui/loom-intent-forge-intent-map.json` → `elements.*`

## Objective

Create `ui/intent-forge.html` with every `dom_id` from loom-intent-forge map. Static layout only — no JS logic yet.

## MAY edit

- `ui/intent-forge.html` (new)
- `ui/intent-forge.css` (new, minimal)
- `aoc_supervisor/aoc_supervisor/repo_paths.py` (`INTENT_FORGE_HTML_PATH`)
- `tests/test_loom_ui_contract.py` (new — dom_id presence)

## MUST NOT edit

- `intent-forge.js` (C13)

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_ui_contract.py::test_intent_forge_dom_ids -q --no-cov
```