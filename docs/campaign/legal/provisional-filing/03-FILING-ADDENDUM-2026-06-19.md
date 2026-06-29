# Filing addendum — reduction to practice update

**Append to specification for filing bundle** (merged by `build-provisional-pdf.sh`)

## Additional empirical validation (2026-06-18 — 2026-06-19)

### Vault dogfood sprint (Obsidian memory vault)

| Metric | Result |
|--------|--------|
| Workers merged | 6/6 (dogfood sprint) |
| Stable work-unit IDs | Content-addressed `WU-{sha256(paths+checks)[:8]}` |
| Completion ledger | 22 entries after ADAPT recovery backfill |
| Convergence | 1.0 (production threshold) |
| Vault linter | PASS |
| Plan backlog post-ledger | 0 work units |

### Merge compounding (Claim 6 support)

Mechanisms shipped and dogfooded:

- `completion-ledger.json` — append-only, keyed by stable WU id, post-weld `content_hash`
- `already_merged` disposition in `merge-grid` (not collect) for zero-delta workers
- Ledger-aware `plan` filter excluding completed scopes
- Governance invariant `merge.merged_work` with honest convergence (no vanity 1.0 on empty merge)

Artifacts: `vaults/gaijinn-memory-fs/.gaijinn/merge/completion-ledger.json`, `governance.json`, `_multi-agent/events.md` event [63], [79].

### Monorepo Phase 2 (unchanged baseline)

171 code nodes · 4 concurrent workers · validation pass rate 1.0 · TX-HT-6D0B24 · transaction bus synchronized · convergence 0.8889 (honest no-op detection).

---

*This addendum strengthens reduction-to-practice for independent claim 6 without altering claim numbering in PART XI.*