# Codex Task — Gaijinn UI State Model Iteration

## Objective (measurable)
Reduce `confusion_count` to **0** for smoke scenario `flow.pkm_greenfield_intent`.
Do NOT polish CSS, shadows, or animations. Fix **state synchronization** only.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Environment setup
```bash
cd /home/ghostmonday/Desktop/Loom
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && .venv/bin/pip install -e aoc-cli -e aoc_supervisor -q
export GAIJINN_MOCK_GRID=1
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
```

## Verification command (run after every change)
```bash
.venv/bin/python -m pytest tests/test_workflow_evaluator.py::test_pkm_workflow_zero_confusion_mock -q
```

Full suite (optional):
```bash
.venv/bin/python -m pytest tests/test_ui_intent_smoke.py tests/test_workflow_evaluator.py -q
```

## AI blueprint index
Read `ui/loom-ui-intent-map.json` → `_ai_blueprint` for per-layer status/gaps.
Module docstrings tagged **GAIJINN BLUEPRINT** mirror the same contract.

## Key files
| File | Role |
|------|------|
| `ui/gaijinn-terminal.html` | Browser state machine, `Phase`, `Subphase`, `assertUiConsistency()` |
| `ui/loom-ui-intent-map.json` | Mirror spec v3 — `state_machine.invariants`, `optimization_goal` |
| `aoc_supervisor/workflow_evaluator.py` | Scores `confusion_count` per workflow run |
| `aoc_supervisor/intent_blueprint.py` | Greenfield workstream decomposition |
| `aoc_supervisor/orchestrate_session.py` | Prepare/swarm API, swarm warnings |

## State narrative (product model)
```
Intent → Blueprint → Swarm → Deploy → Complete
```
Subphases: `choosing_swarm`, `deploying_workers`, `workers_running`

## Known confusion signals (must stay zero)
- Header says agents exist but `grid.empty` visible during sprint
- Worker log contradicts assignment (idle vs working)
- Recommended swarm contradicts work stream count
- Mock grid fakes PASS for idle workers

## Acceptance criteria
1. `test_pkm_workflow_zero_confusion_mock` passes
2. PKM prepare returns `blueprint_mode=intent`, `work_units >= 6`, rationale mentions indexing/search
3. No new pytest failures in `tests/test_ui_intent_smoke.py`

## Constraints
- `sandbox`: workspace-write within repo only
- Max 3 fix iterations before reporting blockers
- Post summary of what changed and final confusion_score