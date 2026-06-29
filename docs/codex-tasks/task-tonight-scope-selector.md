# Codex Task — Tonight Sprint 2: Phase Scope Selector

## Objective
Let users pick **which pipeline phases to run** at intent start. Three independent phases (always in this order when multiple): **backend → frontend → testing**.

## Phase model (canonical)
- `backend` — API/services/data layer sprint
- `frontend` — UI/client sprint (uses backend output as context when backend ran first)
- `testing` — **its own phase** — automated test sprint against merged output (NOT bundled only into "full stack")

## Valid selections (store as ordered list `phases[]`)
| Preset label | `phases` value |
|--------------|----------------|
| Backend only | `["backend"]` |
| Frontend only | `["frontend"]` |
| Testing only | `["testing"]` |
| Backend + Frontend | `["backend", "frontend"]` |
| Backend + Testing | `["backend", "testing"]` |
| Frontend + Testing | `["frontend", "testing"]` |
| Full stack | `["backend", "frontend", "testing"]` |

Reject empty lists, unknown phase names, or wrong order (e.g. `["frontend", "backend"]` → normalize to canonical order).

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Files you MAY edit
- `ui/gaijinn-terminal.html`
- `ui/loom-ui-intent-map.json`
- `aoc_supervisor/aoc_supervisor/orchestrate_session.py`
- `aoc_supervisor/aoc_supervisor/api.py` (orchestrate prepare only)
- `aoc_supervisor/aoc_supervisor/ui_intent.py`
- `tests/test_orchestrate_session.py`
- `tests/test_ui_intent_smoke.py`

## Requirements
1. UI before first intent: preset chips for all 7 combinations above (or 3 toggles + live preset label). Default `["backend"]`.
2. `POST /api/v1/orchestrate/prepare` body: `{ "intent": "...", "phases": ["backend", "testing"] }`
3. `session.json` stores `phases` array + `current_phase` (first phase id). `to_public_dict()` returns `phases`, `current_phase`, `phase_count`.
4. Terminal blueprint card shows: `Phases: Backend → Testing` (human labels, arrow between enabled phases).
5. Intent map: `actions.phases.select`, flow step before `orchestrate.prepare`; document 3-phase model in `_ai_blueprint`.
6. Tests: prepare persists each of the 7 preset phase lists; invalid phases return 400.

## Verification
```bash
.venv/bin/python -m pytest tests/test_orchestrate_session.py tests/test_ui_intent_smoke.py -q
.venv/bin/python -m pytest -q
```

## UI hint (sprint 2 minimum)
When preset is **Frontend + Testing** or **Backend + Testing**, show helper text: *"Requires [opposite end] already loaded — you'll attach it in the next step (sprint 3)."* Do not block prepare yet unless trivial.

## Constraints
- Do NOT implement full loaded_context validation (sprint 3) — hints only in sprint 2
- Do NOT implement phase advancement / chaining (sprint 3)
- Use `phases[]` not legacy `scope` enum — if `scope` exists in code, migrate to `phases`
- Commit: `feat(phases): three-phase scope selector (backend, frontend, testing)`