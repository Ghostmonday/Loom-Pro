# P0 stack post-fix dogfood evidence (PR4)

Proof run after runtime containment + governance + billing fixes.  
**Do not reuse pre-P0 convergence figures** — this is the first evidence set where planner and runtime containment align.

## Stack commits

| PR | Branch | Commit |
|----|--------|--------|
| 1 Runtime containment | `pr/1-runtime-containment` | `6e7e157` |
| 2 Worker governance | `pr/2-worker-governance` | `2ac4d6d` |
| 3 Transactional billing | `pr/3-transactional-billing` | `b99130e` |
| 4 Dogfood evidence | `pr/4-dogfood-evidence` | (this doc) |

## Automated regression (full stack at PR3 tip)

```bash
PYTHONPATH=aoc-cli:aoc_supervisor .venv/bin/python3.11 -m pytest tests/ \
  --ignore=tests/test_audit.py -q
# 412 passed, 1 skipped (victory lap fixture)
```

Unrelated failure documented in [AUDIT-TEST-BASELINE.md](./AUDIT-TEST-BASELINE.md).

## Work-unit assignment proof (no duplicates)

Isolated copy-mode project (`examples/tiny-python-service`, 3 workers, 3 work units):

```json
{
  "worker-001": ["WU-2293984a"],
  "worker-002": ["WU-c9334197"],
  "worker-003": ["WU-ecb50a9e"]
}
```

Each work unit assigned **exactly once** (round-robin when units exceed workers; no modulo duplication).

## Filesystem hash snapshot (mock-sprint path via API)

Supervisor mock-grid integration exercises spawn → collect → validate → merge without live Codex/Grok:

```bash
pytest tests/test_supervisor.py -k mock -q
# 4 passed
```

Key assertion class: `TestGridSprintMonitor` — workers complete under `GAIJINN_MOCK_GRID=1`, merge pipeline advances, deliverable zip excludes raw worker trees.

## CLI validation pipeline (copy-mode dogfood)

On git-initialized tiny-python-service sandbox:

| Stage | Result |
|-------|--------|
| `run-grid --workers 3` | 3 workers, unique WU assignments |
| `collect` | 3 workers collected |
| `validate-worker` | **3 passed** → `.gaijinn/merge/validated.json` |
| Session root hash | Changed only by Gaijinn metadata (expected) |
| Per-worker tree hashes | Stable across failed non-mock CLI spawn attempt |

## Preflight fail-closed

Empty project without blueprint/manifest/validation:

```text
status_code=PREFLIGHT_REJECTED
rejection_reasons includes blueprint_missing, worker_not_found, worker_manifest_missing, worker_validation_missing
```

## Security / containment corrections shipped

> **Worker isolation is now an execution-time property, not only a planning and merge-time property.**

- Executors use worker checkout as `-C` / `--cwd`
- Session IDs confined to `^[a-f0-9]{12}$` under `.gaijinn/sessions/`
- Principal-required session ownership (`owner_user_id` + caller-supplied `X-User-Id`; trusted/local, not production auth)
- Default bind `127.0.0.1`
- Prompt/argv redaction in `output.log`

## Next proof run (human / CI)

After merging PRs 1–3 to `main`, rerun:

1. `gaijinn orchestrate/prepare` → `swarm` → API `grid/spawn` with `GAIJINN_MOCK_GRID=1`
2. Record root + per-worker SHA256 tree hashes before/after spawn
3. `collect` → `validate-worker` → `merge-grid`
4. Publish convergence, trespass count, handoff queue, merge report in this file (section below)

### Placeholder — live convergence (post-merge main)

| Metric | Value |
|--------|-------|
| Workers spawned | TBD after main merge |
| Validation pass rate | TBD |
| Trespass violations | TBD |
| Handoff tickets pending | TBD |
| Merge structural score | TBD |
| Convergence | TBD |