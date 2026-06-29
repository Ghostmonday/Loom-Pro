# MANDATORY side quest — Loom skill sanity on real Gaijinn

**Run once before Wave 2.** Do not skip. Takes ~15 min.  
**Skills:** `loom-intent-mapping-v2` only (`~/.openclaw/skills/loom-intent-mapping-v2/`). Do NOT load v1.  
**Repo:** `/home/ghostmonday/Desktop/gaijinn` branch `main`

## Why

Prove the skill works on **real code**, not sandbox fiction. If you cannot verify → mark `partial` + `gap`. Never fake `verified`.

## Target (real — already in repo)

| Piece | Real location |
|-------|----------------|
| **Action** | `grid.poll_status` in `ui/gaijinn-ui-intent-map.json` |
| **Algorithm** | `aoc-cli/aoc_cli/helpers/merge.py` → `classify_worker_status` |
| **Display UI** | `sprint.status`, `grid.cell_count` in same map |
| **Bug context** | Zero-delta workers must not deadlock as `blocked` |
| **Tests** | `tests/test_promotion_gates.py` — `test_zero_delta_*` |

## Steps (follow skill mapping loop)

1. `cd ~/Desktop/gaijinn && git checkout main && git pull`
2. Load `SKILL.md` + `references/backend.md` + `references/frontend.md` + `references/tests.md`
3. Read `ui/gaijinn-ui-intent-map.json` actions `grid.poll_status` + elements `sprint.status`
4. Open `merge.py::classify_worker_status` — confirm binding (do not invent module path)
5. Classify: `grid.poll_status` = **action_control** (full contract); `sprint.status` = **display**
6. Propose **minimal JSON patch** only for gaps (thin `grid.poll_status` today lacks full backend fields)
7. Add **invariant** (forbidden transition — skill gap Claude found):

```json
{
  "id": "worker.zero_delta_never_blocked",
  "when": "worker.delta == 0 AND ledger_match",
  "forbid": "status == blocked",
  "reason": "Zero-delta with matching ledger is already_merged, not blocked"
}
```

Put forbidden transitions in `invariants` or `state_machine`, not fake guards.

8. Propose smoke scenario (do not flip status unless test passes):

```json
{
  "id": "flow.grid_zero_delta_not_blocked",
  "steps": [
    { "action": "grid.poll_status" }
  ],
  "assertions": [
    { "path": "workers[*].status", "operator": "not_in", "value": ["blocked"] }
  ],
  "implementation_status": "partial",
  "evidence": { "test": "tests/test_promotion_gates.py::test_zero_delta_matching_ledger_is_already_merged" }
}
```

9. Run verify:

```bash
jq empty ui/gaijinn-ui-intent-map.json
.venv/bin/python -m pytest tests/test_promotion_gates.py -q -k zero_delta --no-cov
.venv/bin/python -m pytest tests/test_merge.py::test_classify_worker_status -q --no-cov 2>/dev/null || true
```

10. **Report** (paste to user):

```
SKILL SANITY REPORT
- Repo/branch/commit: ...
- Binding verified: yes/no (module::symbol)
- JSON patch: none | path + summary
- implementation_status: partial | verified (only if pytest green)
- Gaps honestly marked: ...
- Forbidden transition: invariant proposed yes/no
- Skill behaved honestly: yes/no
```

## Rules

- NO commit unless user approves (this is a dry-run sanity pass)
- NO inventing `worker.report_status` if that action id is not in maps — use `grid.poll_status` + `classify_worker_status`
- If binding differs from Claude's sandbox example, **trust the repo**

## Pass criteria

- Skill refused to fake verified without pytest
- Real module/entrypoint cited from disk
- Display vs action_control split correct
- Forbidden transition documented as invariant

## Then

Resume main mission: `docs/operations/clawx-mission.md` → Wave 2 (C05, C10)