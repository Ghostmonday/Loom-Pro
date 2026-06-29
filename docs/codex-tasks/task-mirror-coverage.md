# Codex Task — Mirror Test Coverage Audit

## Objective
Expand **measurable mirror smoke coverage**: `workflow_evaluator.py`, `UiIntentDriver`, intent map `smoke_scenarios`. Target `confusion_count == 0` with explicit invariant assertions — do not fix browser HTML here.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Setup
```bash
cd /home/ghostmonday/Desktop/Loom
export GAIJINN_MOCK_GRID=1
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
```

## Files you MAY edit (only these)
- `aoc_supervisor/aoc_supervisor/workflow_evaluator.py`
- `aoc_supervisor/aoc_supervisor/ui_intent.py`
- `tests/test_workflow_evaluator.py`
- `tests/test_ui_intent_smoke.py`
- `ui/loom-ui-intent-map.json` (`smoke_scenarios`, `state_machine.invariants` documentation only)

## Files you MUST NOT edit
- `ui/gaijinn-terminal.html`
- `intent_blueprint.py`
- `orchestrate_session.py`, `api.py`
- `aoc-cli/**`

## Focus areas
- `evaluate_prepare()`, `evaluate_swarm()`, `evaluate_workflow()` invariant checks
- PKM scenario `flow.pkm_greenfield_intent` — confusion signals from intent map
- Missing assertions: idle worker standby, grid visibility, swarm_warning when oversubscribed
- `UiIntentDriver` parity with documented API sequence

## Verification
```bash
.venv/bin/python -m pytest tests/test_workflow_evaluator.py tests/test_ui_intent_smoke.py -q
```

## Acceptance
1. `test_pkm_workflow_zero_confusion_mock` passes with `confusion_count == 0`
2. At least one new invariant test if gaps found
3. Summary: confusion_score and coverage added

## Constraints
- Max 3 fix iterations
- Separate PR — evaluation/mirror layer only