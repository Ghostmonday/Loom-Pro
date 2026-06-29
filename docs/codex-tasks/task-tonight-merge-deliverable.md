# Codex Task — Tonight Sprint 1: Merge Deliverable UI

## Objective
Polish post-merge **Deliverable Ready** experience in terminal + minimal API. Sprint 1 of tonight velocity bundle (see `.gaijinn/tonight-sprints.json`).

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Setup
```bash
cd /home/ghostmonday/Desktop/Loom
export GAIJINN_MOCK_GRID=1
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
```

## Files you MAY edit
- `ui/gaijinn-terminal.html`
- `ui/loom-ui-intent-map.json`
- `aoc_supervisor/aoc_supervisor/api.py` (deliverable endpoint only)
- `aoc_supervisor/aoc_supervisor/ui_intent.py`
- `tests/test_ui_intent_smoke.py`
- `tests/test_supervisor.py` (deliverable tests only)

## Requirements
1. After `runPostSprintMerge()` success, show deliverable panel/card with:
   - merged / blocked / conflicted counts
   - session_id + session project path (server-side path ok for demo)
   - Button: "Download deliverable" → `GET /api/v1/grid/deliverable?session_id=` returns zip of session project (exclude `.gaijinn/workers` heavy logs if needed)
2. Sprint failure → `Phase.FAILED` (already partial — ensure consistent)
3. Merge failure → stay COMPLETE with warning (existing behavior)
4. Workflow chip: `Merging output` → `Deliverable ready`
5. Intent map: add `deliverable.download` action + element refs

## Verification
```bash
.venv/bin/python -m pytest tests/test_ui_intent_smoke.py tests/test_supervisor.py -k "merge or deliverable or full_flow" -q
.venv/bin/python -m pytest -q
```

## Constraints
- Max 3 fix iterations
- Commit: `feat(terminal): deliverable ready panel + zip export`