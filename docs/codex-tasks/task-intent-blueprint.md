# Codex Task — Intent-Driven Blueprint Audit

## Objective
Audit and harden **greenfield intent → work unit decomposition** in `intent_blueprint.py`. PKM intent must yield ≥6 distinct streams; tiny_service template must not leak into greenfield paths.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Setup
```bash
cd /home/ghostmonday/Desktop/Loom
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
```

## Files you MAY edit (only these)
- `aoc_supervisor/aoc_supervisor/intent_blueprint.py`
- `tests/test_intent_blueprint.py`

## Files you MUST NOT edit
- `ui/gaijinn-terminal.html`
- `ui/loom-ui-intent-map.json`
- `orchestrate_session.py`, `api.py`, `workflow_evaluator.py`, `ui_intent.py`
- `aoc-cli/**`

## Focus areas
- `detect_intent_streams()` coverage for PKM keywords (PDF, Markdown, transcripts, semantic search, desktop UI, offline, privacy)
- `build_intent_blueprint()` — `blueprint_mode=intent`, distinct `allowed_paths` per stream
- `swarm_rationale()` / `swarm_warning()` accuracy when workers > work_units
- Edge cases: short intents, ambiguous intents, non-greenfield fallback

## Verification
```bash
.venv/bin/python -m pytest tests/test_intent_blueprint.py -q
```

## Acceptance
1. All `test_intent_blueprint.py` tests pass
2. Add tests for any new gaps found (same file only)
3. Summary: streams detected for PKM, work unit count, rationale quality

## Constraints
- Max 3 fix iterations
- Separate PR — planner layer only