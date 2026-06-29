# Codex Slice 5 — Full Test Suite & CI

**MASTER:** `docs/codex-tasks/MASTER-codex-fullpass.md`
**Depends on:** Slice 1–4 merged (but may run independently)
**Status:** ✅ Complete — report: `.gaijinn/codex/slice-05-report.md`

## Objective

Full suite green, acceptance script green, CI workflow asserts pytest on main.

## Baseline

- At slice start (post slice 4): 276 passed (`pytest tests/ -q`)
- Current full suite (post slice 6): **284 passed**
- acceptance.sh: exists and functional
- CI: `.github/workflows/ci.yml` runs pytest, ruff, acceptance
- CI gate: `.github/workflows/gaijinn-gate.yml` for integration branch PRs

## MAY edit

- `tests/**` (any remaining gaps)
- `scripts/ci/**`, `.github/workflows/**`

## MUST NOT edit

- `ui/**` unless test-only smoke assertions
- `aoc-cli/` core files — no production code changes
- `aoc_supervisor/` — no production code changes

## Work

1. Verify full suite passes: `python3 -m pytest tests/ -q`
2. Verify acceptance script passes: `bash scripts/ci/acceptance.sh`
3. Ensure CI workflow asserts pytest runs on push/PR to main:
   - `.github/workflows/ci.yml` currently runs pytest on every push/PR — good
   - Add explicit assertion that pytest passes on main (e.g. condition or separate job)
4. Fix any test gaps or flaky tests found in audit
5. Write `.gaijinn/codex/slice-05-report.md` (findings + changes)

## Acceptance

```bash
python3 -m pytest tests/ -q
bash scripts/ci/acceptance.sh
```

Both must pass. Report at `.gaijinn/codex/slice-05-report.md`
