# Codex Task — Demo Merge Loop (API + Terminal + Evaluator)

## Objective
Close the **product demo loop**: after sprint completes, run **collect → validate → merge-grid** and surface status in the terminal. Wire merge into orchestrate API, browser state machine, mirror driver, and workflow evaluator so `confusion_count == 0` on the full Intent→Complete→Merge path under `GAIJINN_MOCK_GRID=1`.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Setup
```bash
cd /home/ghostmonday/Desktop/Loom
export GAIJINN_MOCK_GRID=1
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
```

## Context (read first)
- CLI merge pipeline is **shipped**: `aoc-cli/aoc_cli/helpers/merge.py` → `merge_pipeline_status()`
- Commands: `gaijinn collect`, `gaijinn validate-worker`, `gaijinn merge-grid`
- Session projects live at `.gaijinn/sessions/<session_id>/` (see `orchestrate_session.py`)
- Terminal stops at `endSprint()` → `Phase.COMPLETE` with no merge call (`ui/gaijinn-terminal.html`)
- API gap documented in `api.py`: no merge endpoint
- Intent map v3 lists merge gaps in `_ai_blueprint.layers`

## Files you MAY edit (only these)
- `aoc_supervisor/aoc_supervisor/api.py`
- `aoc_supervisor/aoc_supervisor/orchestrate_session.py`
- `aoc_supervisor/aoc_supervisor/workflow_evaluator.py`
- `aoc_supervisor/aoc_supervisor/ui_intent.py`
- `ui/gaijinn-terminal.html`
- `ui/loom-ui-intent-map.json` (merge actions/flow/invariants — do NOT change existing smoke_scenario steps unless adding merge step)
- `tests/test_supervisor.py` (merge endpoint tests only)
- `tests/test_workflow_evaluator.py`
- `tests/test_ui_intent_smoke.py` (merge smoke assertions only)

## Files you MUST NOT edit
- `aoc-cli/**` (merge CLI is done)
- `aoc_supervisor/aoc_supervisor/intent_blueprint.py` (unless a one-line import fix is strictly required)
- `tests/test_merge.py`, `tests/test_giv.py`
- `scripts/**`, `docs/**` (except this file is read-only contract)

## Implementation requirements

### 1. Orchestrate session — `run_merge(session_id)`
- Add method on `OrchestrateSessionStore` that resolves session project root and runs (via existing `_run_gaijinn`):
  1. `collect`
  2. `validate-worker`
  3. `merge-grid`
- Update session meta `phase` to `merge_complete` or `merge_failed` based on outcome
- Return public dict including `merge_pipeline` from `merge_pipeline_status(project_root)` (import from `aoc_cli.helpers.merge`)
- Under mock grid, workers may have minimal git state — merge should not crash; return structured status even if merge partially skips

### 2. API endpoints (`api.py`)
- `POST /api/v1/grid/merge` — body: `{ "session_id": "..." }` (required). Runs merge in thread pool (`asyncio.to_thread`). Returns merge_pipeline status + session phase.
- `GET /api/v1/grid/merge/status?session_id=...` — read-only `merge_pipeline_status` for session project root (no side effects).
- Optional: include `merge_pipeline` key in existing `GET /api/v1/grid/status` when `session_id` query param present.
- HTTP errors: 404 missing session, 500 with detail string on pipeline failure (do not leak raw tracebacks).

### 3. Terminal (`gaijinn-terminal.html`)
- After successful `endSprint(false)` (no sprint errors), if `state.sessionId` set:
  - `POST /api/v1/grid/merge` with session_id
  - Poll `GET /api/v1/grid/merge/status` until `phase == "completed"` or terminal failure states (`blocked`/`conflicted` > 0)
- Add merge subphase UX:
  - Workflow chip labels: include "Merging output" during merge; final "Deliverable ready" or "Merge blocked" on completion
  - Orchestrator message summarizing merged/blocked/conflicted counts
- On merge failure: stay in `Phase.COMPLETE` (sprint succeeded) but show warning status — do NOT regress grid visibility invariants
- Update header comment GAPS section to reflect wired merge

### 4. Intent map (`loom-ui-intent-map.json`)
- Add actions: `merge.run`, `merge.poll_status`
- Add flow step after `complete`: merge phase
- Add invariant: `merge.status_after_complete` — when merge triggered, `merge_pipeline.phase` progresses from idle → completed
- Update `_ai_blueprint.layers` gaps for orchestration/api/terminal/evaluator/merge_pipeline to `shipped` or `partial` as appropriate
- Add element `merge.chip` if new DOM id added

### 5. Mirror driver (`ui_intent.py`)
- Methods: `run_merge(session_id)`, `merge_status(session_id)`
- Extend `run_smoke_scenario` to handle `merge.run` / `merge.poll_status` steps
- Extend `evaluate_scenario` to pass merge payload to evaluator

### 6. Workflow evaluator (`workflow_evaluator.py`)
- Implement `evaluate_merge(payload: Mapping)` checking:
  - `merge.phase` reaches `completed` on happy path
  - `merged >= 1` when workers had assigned work and mock grid completed
  - `blocked == 0` and `conflicted == 0` on happy path
- Wire into `evaluate_workflow(..., merge=...)`

### 7. Tests
- `test_supervisor.py`: POST merge + GET status after mock sprint (use `mock_grid_client` pattern)
- `test_workflow_evaluator.py`: unit test `evaluate_merge` + extend PKM scenario to include merge step with confusion_score still 0
- `test_ui_intent_smoke.py`: assert terminal HTML references merge API paths; optional merge chip dom id
- All existing tests must still pass

## Verification (run after every iteration)
```bash
.venv/bin/python -m pytest tests/test_supervisor.py tests/test_workflow_evaluator.py tests/test_ui_intent_smoke.py -q
.venv/bin/python -m pytest -q
```

## Acceptance
1. Full mock flow: intent → prepare → swarm → spawn → complete → **merge** returns `merge_pipeline.phase == "completed"`
2. Terminal calls merge API on sprint success (grep `/api/v1/grid/merge` in HTML)
3. `evaluate_merge` exists and PKM workflow `confusion_score() == 0` with merge step
4. Full suite green (`pytest -q`)
5. One-paragraph summary in commit message of what was wired

## Constraints
- Max 3 fix iterations
- Do not change billing, council, or hermes endpoints
- Stealth contract: never expose blueprint.json/graph.json to browser
- Mock grid only for tests — no real `grok` spawn required