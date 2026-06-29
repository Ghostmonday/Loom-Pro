# Codex Task — Neural Draft Internal UI

**Working directory:** `/home/ghostmonday/Desktop/Loom`  
**Design package:** `.gaijinn/design/neural-draft-internal-ui/`  
**Component map:** `ui/blueprint-ui.json`  
**Classification:** TRADE SECRET — Neural Draft LLC internal only

---

## Objective

Ship `ui/neural-draft/` — performant internal manufacturing console served at `/internal`. Wire 12 process-stage control points to existing FastAPI. **Not** `docs/campaign/website/`.

## Stack (locked)

- API: FastAPI (`aoc_supervisor/api.py`) — no Rust API rewrite
- UI: Vanilla HTML/CSS/JS — no React/Vue bundle
- Future: Tauri 2 shell (separate task)

## Files you MAY edit

- `ui/neural-draft/**`
- `ui/blueprint-ui.json`
- `aoc_supervisor/aoc_supervisor/api.py` (add `/internal` routes only)
- `aoc_supervisor/aoc_supervisor/repo_paths.py`
- `tests/test_neural_draft_ui.py`

## Files you MUST NOT edit

- `ui/gaijinn-terminal.html` (monolithic — use component WUs)
- `docs/campaign/website/**`

## Acceptance

1. `GET /internal` returns trade-secret banner + 5-stage rail
2. Prepare → blueprint approval toggle → deploy blocked until approved
3. Merge matrix shows disposition from `merge/status`
4. `pytest tests/test_neural_draft_ui.py -q` green
5. No initial JS bundle over 100KB

## Verification

```bash
.venv/bin/python -m pytest tests/test_neural_draft_ui.py -q
```