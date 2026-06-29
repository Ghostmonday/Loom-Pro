# Codex Task — Tonight Sprint 3: Multi-Phase Orchestration Skeleton

## Objective
Chain **backend → frontend → testing** based on `phases[]` chosen at prepare. Testing is always its own phase when selected — never implicit-only inside full_stack.

## Prerequisites
Sprint 2 `phases[]` selector must exist on session.

## Loaded context (opposite end)
Backend and frontend are the two **ends** of the stack. When the user picks a preset that **builds one end + testing** but does **not** build the opposite end, that opposite end must **already be loaded** before prepare succeeds:

| `phases[]` | Must load first (opposite end) |
|------------|--------------------------------|
| `["frontend", "testing"]` | **backend** — API/services already exist |
| `["backend", "testing"]` | **frontend** — client/UI already exists for integration tests |
| `["testing"]` only | **both** backend + frontend deliverables |
| `["frontend"]` only | **backend** recommended (warn if missing) |

**Load sources** (implement at least one for demo):
- `loaded_context.prior_session_id` — reuse a completed Gaijinn session deliverable
- `loaded_context.zip_path` or upload via API — import opposite-end zip
- `loaded_context.project_path` — path to existing project tree

Store on session: `loaded_context: { backend?: {...}, frontend?: {...} }`. Validate in `prepare()` — return 400 with clear message if required load missing. Terminal: when user picks Frontend+Testing or Backend+Testing, show **"Load [opposite end]"** panel (session picker or zip) before intent submit.

## Phase rules
- `pipeline_plan.phases` = copy of session `phases[]` in canonical order
- `pipeline_plan.current_index` = 0 at prepare; points into `phases` array
- After merge_complete for current phase, if more phases remain → `awaiting_next_phase` (not auto-start; user or API advances)
- `POST /api/v1/orchestrate/advance-phase` { session_id }:
  - increments index, sets `current_phase` to next id
  - resets swarm/deploy state for new phase stub (message: "Frontend phase queued — blueprint stub")
  - frontend phase uses stub intent context from backend merge summary
  - testing phase uses stub: "Run acceptance tests against merged deliverable"

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Files you MAY edit
- `aoc_supervisor/aoc_supervisor/orchestrate_session.py`
- `aoc_supervisor/aoc_supervisor/api.py`
- `ui/gaijinn-terminal.html` (phase rail)
- `ui/loom-ui-intent-map.json`
- `aoc_supervisor/aoc_supervisor/ui_intent.py`
- `tests/test_orchestrate_session.py`
- `tests/test_supervisor.py`

## UI
- Stage rail dynamic: show only selected phases from `phases[]` (e.g. Backend → Testing skips Frontend node)
- Highlight `current_phase`; completed phases get checkmark

## Tests (mock grid)
1. `phases: ["backend"]` — single phase, no advance needed
2. `phases: ["backend", "frontend", "testing"]` — advance-phase twice after backend merge stub
3. `phases: ["testing"]` — testing-only session starts on testing phase
4. `phases: ["backend", "testing"]` — advance once backend→testing

## Verification
```bash
.venv/bin/python -m pytest tests/test_orchestrate_session.py tests/test_supervisor.py -k "phase or advance or phases" -q
.venv/bin/python -m pytest -q
```

## Constraints
- Stub blueprints only — no real frontend codegen
- Commit: `feat(pipeline): multi-phase skeleton for backend, frontend, testing`