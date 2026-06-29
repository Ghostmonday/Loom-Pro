# Codex Task — UI State Machine Audit (browser only)

## Objective
Audit and fix **browser-side** state synchronization in `ui/gaijinn-terminal.html` against `ui/loom-ui-intent-map.json` `state_machine` (phases, subphases, invariants). No CSS polish.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Setup
```bash
cd /home/ghostmonday/Desktop/Loom
export GAIJINN_MOCK_GRID=1
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
```

## Files you MAY edit (only these)
- `ui/gaijinn-terminal.html`
- `ui/loom-ui-intent-map.json` (only if terminal invariants need spec alignment — no smoke_scenarios)

## Files you MUST NOT edit
- `aoc_supervisor/**`
- `aoc-cli/**`
- `tests/**`
- `workflow_evaluator.py`, `ui_intent.py`, `intent_blueprint.py`, `orchestrate_session.py`

## Focus areas
- `Phase` / `Subphase` transitions: Intent → Blueprint → Swarm → Deploy → Complete
- `setGridView()` / `assertUiConsistency()` vs spec invariants
- Live grid only when subphase is `deploying_workers` or `workers_running` (not during `choosing_swarm`)
- Worker cards: standby vs done vs running labels match assignment semantics
- Swarm picker UX copy (no nested dead-ends)

## Verification (read-only — do not modify tests)
```bash
.venv/bin/python -m pytest tests/test_ui_intent_smoke.py -q
```

## Acceptance
1. State transitions in terminal match intent map narrative
2. No regression in `test_ui_intent_smoke.py`
3. Summary of invariant gaps found and fixes applied

## Constraints
- Max 3 fix iterations
- Separate PR — do not touch evaluator or backend