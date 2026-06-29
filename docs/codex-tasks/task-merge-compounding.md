# Codex Task — Merge Compounding + Vault/Code Split

**Working directory:** `/home/ghostmonday/Desktop/Loom`  
**Design package:** `.gaijinn/design/merge-compounding/` (layer1, layer2, blueprint)  
**Ship order:** `aoc-cli` first (all projects), dogfood on `vaults/gaijinn-memory-fs` second.

---

## Objective

Fix merge compounding: zero-delta copy-mode workers that already shipped work must become `already_merged`, not `blocked`. Sprints must compound via `completion-ledger.json`, stable WU ids, and ledger-aware `plan`.

**Done when:** `pytest` green including new integration test; vault dogfood replay of 14 zero-delta workers → convergence climbs, Hermes does not idle-trap.

---

## Locked design decisions (do not re-litigate)

### Q1 — `already_merged` disposition: merge_grid only

- `classify_worker_status` zero-delta → `pending` stays as-is (executor observation).
- **Do not** push ledger check into `collect`.
- **Single source of truth:** `merge_grid.py` with blueprint→WU mapping at merge time.

### Q2 — `content_hash`: post-weld file contents (C)

- Hash merged file contents from the sprint that **first completed** the WU.
- Compute **after** `apply_copy_mode_worker_changes` — project root state, not worker pre-merge sandbox.
- Scope: files under that WU's `allowed_paths`.
- **Not** identity hash for `content_hash` (that cannot detect drift).

### Q3 — Stable WU ids: migrate + backfill (A)

- Formula (permanent, never index-based):  
  `sha256(sorted(allowed_paths) + sorted(acceptance_checks))[:8]` → e.g. `WU-a3f8c201`
- Backfill ledger from **last governance.json merged list only** (11 workers), **not** the 3 blocked.
- No dual-id transition period (B) or hard cut (C).

### Q4 — Plan partitioning (C, corrected)

- `scan` / `analyze` **still run** for vault (detect new/changed notes).
- **Code domain:** graph-partition every plan (cheap, deterministic).
- **Vault domain:** scan for new content; emit WUs only for files **not** in ledger or carried-forward blueprint.
- Do **not** skip regen entirely (A) or regen+filter only (B) for vault boundaries.

### Q5 — `merge.merged_work`

```python
merge.merged_work := (merged + already_merged >= 1) OR backlog_pre_sprint == 0
```

### Q6 — `merge.no_blocked`

- `already_merged` must **not** increment `blocked_count`.
- `already_merged` must **not** fail `merge.no_blocked`.

### Q7 — Hermes `_decide_action` (conditional)

After merge when `merged_workers == 0` is possible:

| Condition | Action |
|-----------|--------|
| `backlog == 0` (post ledger-filter) | `converged` + linter |
| `backlog > 0` and ledger grew this sprint | `plan_next_sprint` |
| `backlog > 0` and nothing merged or already_merged | `stuck` + council post |

### Q8 — run-grid scope: fail closed + bootstrap escape hatch

- Raise if `blueprint.json` missing or any WU has empty/root-only paths when `workers > 1`.
- Keep single-worker fallback only behind explicit `init --bootstrap-single-worker` (or equivalent flag) with `workers == 1`.
- Do not silently fall back when `_load_blueprint_optional` returns None due to bugs.

### Q9 — Domain resolution: prefix table → `work_unit.domain` at plan time

- Path-prefix table assigns `domain` (`vault` | `code`) **once** at blueprint generation.
- `validate_worker` keys acceptance off resolved `domain`, not re-derived prefixes.
- WU straddling vault+code prefixes or matching neither → **hard error at plan time**.

### Q10 — Implementation location

- **Primary:** `aoc-cli/` (domain-general).
- **Dogfood:** `vaults/gaijinn-memory-fs` after tests pass.

---

## Files to modify (minimum)

| File | Change |
|------|--------|
| `aoc-cli/aoc_cli/blueprint.py` | Stable WU id; domain field; prefix table; vault carry-forward |
| `aoc-cli/aoc_cli/commands/plan.py` | Ledger filter; code vs vault partition |
| `aoc-cli/aoc_cli/commands/merge_grid.py` | `already_merged`; write `completion-ledger.json` |
| `aoc-cli/aoc_cli/helpers/merge.py` | Governance scoring Q5/Q6; content_hash helper |
| `aoc-cli/aoc_cli/commands/collect.py` | No ledger logic (Q1) |
| `aoc-cli/aoc_cli/commands/run_grid.py` | Fail closed + bootstrap gate (Q8) |
| `aoc-cli/aoc_cli/commands/validate_worker.py` | Acceptance by `work_unit.domain` |
| `aoc-cli/aoc_cli/helpers/project_profile.py` | `project_kind` from `project.json` + profile |
| `scripts/dev/hermes_development_loop.py` | Q7 decision tree |
| `tests/` | New integration test for compounding sprint |

**New artifact:** `.gaijinn/merge/completion-ledger.json`

```json
{
  "schema_version": 1,
  "entries": [
    {
      "wu_id": "WU-a3f8c201",
      "content_hash": "<sha256 of allowed_paths files at post-weld>",
      "merged_at": "ISO8601Z",
      "worker_id": "worker-003",
      "allowed_paths": ["..."],
      "acceptance_checks": ["..."]
    }
  ]
}
```

---

## merge_grid already_merged algorithm (Q1 + Q2)

For copy-mode worker with empty `changed_files`:

1. Resolve assigned WU ids from worker metadata / blueprint.
2. For each WU, load ledger entry if any.
3. Compute `content_hash` from **current project root** files under `allowed_paths`.
4. If ledger entry exists and `content_hash` matches → `status: already_merged` (do not increment blocked).
5. Else → `status: blocked` (unchanged behavior).

For workers with changes: merge normally; on success append/update ledger with post-weld hash.

---

## Backfill (Q3)

Read `vaults/gaijinn-memory-fs/.gaijinn/merge/governance.json` + `report.json` merged workers only. Map worker→WU via manifest. Seed ledger with post-weld hashes from current project root. **Exclude** blocked workers from backfill.

---

## Tests required

1. **Unit:** stable WU id deterministic across two `plan` runs with same paths.
2. **Unit:** zero-delta + matching ledger → `already_merged`, `blocked_count` unchanged.
3. **Unit:** zero-delta + no ledger / hash mismatch → `blocked`.
4. **Unit:** `merge.merged_work` passes with 5 `already_merged`, 0 fresh, backlog>0.
5. **Unit:** `merge.merged_work` passes with backlog==0, all already_merged.
6. **Integration:** sprint N merge → ledger written → `plan` drops completed WUs → sprint N+1 zero-delta → not all blocked.
7. **Hermes:** `merged_workers==0`, `already_merged>0`, backlog>0 → `plan_next_sprint` not `idle`.

Run: `python -m pytest -q` from repo root.

---

## Council

Post summary when done:
```bash
gaijinn council say --as codex "merge-compounding shipped: ledger, stable WU ids, already_merged, plan filter, hermes decide. pytest N/N."
```

---

## Do NOT

- Add ledger checks to `collect` or change `classify_worker_status` blocked semantics.
- Use identity hash for `content_hash`.
- Credit blocked workers in backfill.
- Vault-only hacks without aoc-cli changes.
- Silent `'.'` scope fallback for multi-worker grids.