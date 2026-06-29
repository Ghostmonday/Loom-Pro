# Codex Task — Merge Pipeline Invariants Audit

## Objective
Audit **collect → validate → merge-grid** pipeline invariants: GIV trespass detection, worker status classification, merge ordering, conflict reporting. Wire any missing `MergeValidation` / `failed` phase hooks if gaps exist in CLI only.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Setup
```bash
cd /home/ghostmonday/Desktop/Loom
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
```

## Files you MAY edit (only these)
- `aoc-cli/aoc_cli/helpers/merge.py`
- `aoc-cli/aoc_cli/commands/merge_grid.py`
- `aoc-cli/aoc_cli/commands/collect.py`
- `aoc-cli/aoc_cli/commands/validate_worker.py`
- `tests/test_merge.py`
- `tests/test_giv.py`

## Files you MUST NOT edit
- `ui/gaijinn-terminal.html`
- `aoc_supervisor/**`
- `ui/loom-ui-intent-map.json`

## Focus areas
- `classify_worker_status()`, `detect_trespasses()`, `worker_merge_order()`
- `merge_pipeline_status()` deterministic JSON artifacts
- Protected paths (`.gaijinn/`, `CLAUDE.md`) never merged from workers
- Blocked workers must not silently merge

## Verification
```bash
.venv/bin/python -m pytest tests/test_merge.py tests/test_giv.py -q
```

## Acceptance
1. Merge + GIV tests pass
2. New tests for any invariant gaps (same test files)
3. Summary of pipeline confusion risks and fixes

## Constraints
- Max 3 fix iterations
- Separate PR — CLI merge layer only