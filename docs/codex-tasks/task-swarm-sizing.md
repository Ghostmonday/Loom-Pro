# Codex Task — Swarm Sizing & Recommendations Audit

## Objective
Audit **swarm recommendation logic** and API/UI-facing swarm fields. Recommended swarm must match work stream count in intent mode; warnings when workers > work_units must be honest.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Setup
```bash
cd /home/ghostmonday/Desktop/Loom
export GAIJINN_MOCK_GRID=1
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
```

## Files you MAY edit (only these)
- `aoc_supervisor/aoc_supervisor/orchestrate_session.py` (swarm/prepare paths only — do not rewrite blueprint generation)
- `aoc_supervisor/aoc_supervisor/api.py` (orchestrate prepare/swarm response fields only)
- `tests/test_orchestrate_session.py`

## Files you MUST NOT edit
- `ui/gaijinn-terminal.html`
- `intent_blueprint.py`
- `workflow_evaluator.py`, `ui_intent.py`
- `aoc-cli/**`

## Focus areas
- `_recommend_swarm()`, `_suggest_swarm()` intent_mode vs graph mode
- `assign_swarm()` — no duplicate blueprint runs
- API payloads: `recommended_swarm`, `suggested_swarm`, `swarm_rationale`, `swarm_warning`, `work_stream_titles`
- PKM prepare: `recommended_swarm == work_units`

## Verification
```bash
.venv/bin/python -m pytest tests/test_orchestrate_session.py -q
```

## Acceptance
1. All orchestrate session tests pass
2. PKM path recommends one agent per work stream
3. Summary of sizing bugs and API field fixes

## Constraints
- Max 3 fix iterations
- Separate PR — orchestration layer only