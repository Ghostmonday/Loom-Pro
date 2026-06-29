# Codex Task — Spawn Contract Hardening (GIV + grid-spawn + validate-worker)

## Objective
Harden allocation-time agent contracts so workers cannot write sibling work-unit paths. Maps to `test_merge_integrity.py` trespass gate. Target: next victory lap achieves `convergence: 1.0` when agents obey scope.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Context (read first)
- Victory lap: worker-001 trespassed `tiny_service/service.py` (WU-002 scope). Governance scored 0.75 correctly.
- Fix sequence: sibling denied paths + scope law prompt + loud validate gate. NO OS filesystem locking in this task.

## Files you MAY edit (only these)
- `aoc-cli/aoc_cli/giv.py`
- `aoc-cli/aoc_cli/helpers/workers.py`
- `aoc-cli/aoc_cli/commands/grid_spawn.py`
- `aoc-cli/aoc_cli/commands/validate_worker.py`
- `aoc-cli/aoc_cli/helpers/merge.py` (only if needed for shared trespass helpers)
- `tests/test_giv.py` (if exists) or `tests/test_merge.py`
- `tests/test_merge_integrity.py` (minimal assertion additions only)

## Files you MUST NOT edit
- `aoc_supervisor/**`, `ui/**`, `blueprint.py`, `gravity.py`, `docs/**` (except this file is read-only)

## Phase 1 — GIV structural tokens (extend existing GIV, no parallel schema)

Add to `GIV.to_dict()` / `from_dict()` / `render_intent()`:
- `structural_tokens`: dict with keys `scope_strict`, `no_sibling_trespass`, `handoff_only` (all default True for workers)
- `sibling_denied_paths`: tuple of paths owned by sibling workers (explicit list)

Add helper in `workers.py`:
```python
def _sibling_denied_paths(worker_index: int, assignments: dict[int, tuple[WorkUnit, ...]]) -> tuple[str, ...]:
    """Union of allowed_paths from all other workers' assigned work units."""
```

Update `_worker_giv()` to accept sibling_denied_paths and merge into `denied_paths` (deduped, sorted). Store sibling list separately in giv.json via new fields.

Update `run_grid.py` call site: pass assignments into `_worker_giv` so each worker gets sibling paths denied.

## Phase 2 — Scope law prompt in grid_spawn.py

Replace/enhance `_build_task_prompt()` with a one-screen scope law:
- WORKER ID, assigned work unit ids from metadata
- GAIJINN_TOKENS line: SCOPE_STRICT, NO_SIBLING_TRESPASS, HANDOFF_ONLY
- ALLOWED WRITE PATHS (bullets)
- PROHIBITED WRITE PATHS — mark sibling_denied_paths as "(OWNED BY SIBLING WORKER)"
- OPERATIONAL INVARIANTS: do not edit prohibited paths; request handoff in output instead
- CONVERGENCE CHECK: git diff outside allowlist fails validation
- Then ASSIGNED TASK (work unit markdown), council excerpt, execution rules

Keep council excerpt and execution rules. Do not remove `====` separator expectation in output (merge.py uses it for denied command scan).

## Phase 3 — validate_worker trespass gate

In `_validate_single_worker` or new helper in merge.py:
- After path_allowlist gate, add explicit `scope_isolation` gate using `detect_trespasses` on scoped changed files
- Fail with clear violations list including sibling paths
- Gate appears in validated.json under `gates.scope_isolation`

Ensure `path_is_allowed` already prefers explicit allow over broad deny (do not regress).

## Tests (required)

1. `_sibling_denied_paths` returns other workers' allowed paths
2. `_worker_giv` includes sibling paths in denied_paths and giv.json sibling_denied_paths
3. `_build_task_prompt` contains SCOPE_STRICT and sibling denied bullets when siblings exist
4. `scan_denied_command_ignores_grid_spawn_prompt_header` still passes (existing test)
5. Run: `.venv/bin/python -m pytest tests/test_merge.py tests/test_merge_integrity.py tests/test_cli.py -q --tb=short`

## Acceptance
1. All pytest above pass
2. `gaijinn run-grid --workers 2` on tiny-python-service produces giv.json with `sibling_denied_paths` populated per worker
3. Minimal diff — no unrelated refactors

## Verification command
```bash
cd /home/ghostmonday/Desktop/Loom
.venv/bin/python -m pytest tests/test_merge.py tests/test_merge_integrity.py -q --tb=short
```