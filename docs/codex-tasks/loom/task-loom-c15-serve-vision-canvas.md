# Loom C15 — Serve Vision Canvas at / (LOOM-207)

**Depends on:** C14

## Objective

`static_ui.py`: route `/` serves `intent-forge.html`; serve `/ui/intent-forge.js` + css.

## MAY edit

- `aoc_supervisor/aoc_supervisor/routers/static_ui.py`
- `aoc_supervisor/aoc_supervisor/repo_paths.py`

## Verify

```bash
# with uvicorn running:
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/ui/intent-forge.js
```