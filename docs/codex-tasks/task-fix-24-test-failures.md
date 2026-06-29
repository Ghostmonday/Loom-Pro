# Codex Task — Post-24-Failure Audit & Robustness

## Objective

The **24 test failures are already fixed** on `main` (`ad150c0`). Your job is **not** to re-implement those fixes.

**Codex owns:**
1. **Verify** the suite stays green and the fixes are sound.
2. **Audit** related code for the same class of bugs and missing hardening.
3. **Implement** only what is still open — robustness gaps, regression tests, and small improvements surfaced by the audit.
4. **Report** findings and council-post the outcome.

## Working directory

`/home/ghostmonday/Desktop/Loom`

## Setup

```bash
cd /home/ghostmonday/Desktop/Loom
git fetch origin && git checkout main && git pull --rebase origin main
export GAIJINN_MOCK_GRID=1
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
python -m pytest tests/ -q   # baseline: 265 passed, 0 failed
```

## Already shipped (read-only — do not redo)

| Category | Count | Fix | Commit |
|----------|-------|-----|--------|
| A — Subprocess Python path | 19 | `_gaijinn_python()` in `orchestrate_session.py` | `ad150c0` |
| B — Blueprint `dependencies` alignment | 2 | Fixture updates in `test_merge.py` | `ad150c0` |
| C — Stealth sanitizer | 1 | Test isolation + `shadow bridge(s)` replacement | `ad150c0` |

**Do not** re-implement inference pipelines (`intent_scan.py`, `inferring.py`, `dataflow.py`, `blueprint_compiler.py`) — already shipped.

---

## Phase 1 — Verify (mandatory, no edits)

Confirm the three categories and full suite:

```bash
python -m pytest tests/test_orchestrate_session.py tests/test_ui_intent_smoke.py \
  tests/test_workflow_evaluator.py::test_pkm_workflow_zero_confusion_mock \
  tests/test_supervisor.py::TestGridSprintMonitor::test_session_merge_endpoint_after_mock_sprint -q

python -m pytest tests/test_merge.py::test_sibling_dependency_deferral_when_dep_owned_by_other_worker \
  tests/test_merge.py::test_sibling_dependency_deferral_skips_same_worker_deps -q

python -m pytest tests/test_stealth.py::test_sanitize_blocked_reason -q

python -m pytest tests/ -q
```

If anything fails, fix only the regression — do not rewrite working `ad150c0` logic without cause.

---

## Phase 2 — Audit (read + structured report)

Read the shipped fixes and hunt for the **same failure modes** elsewhere.

### Audit checklist

| # | Area | Question | Likely paths |
|---|------|----------|--------------|
| 1 | Relative `sys.executable` + foreign `cwd` | Any other subprocess spawns still pass raw `sys.executable`? | `orchestrate_session.py`, `tests/test_e2e_golden_path.py` (`PYTHON` env), `scripts/**` |
| 2 | `VIRTUAL_ENV` leakage | Does `_pythonpath_env()` need to unset or repoint `VIRTUAL_ENV` when `cwd` is a temp session root? | `orchestrate_session.py` |
| 3 | Blueprint fixture drift | Do other tests/builders pass `dependencies={}` while `depends_on` is non-empty? | `tests/test_merge.py`, `tests/test_blueprint*.py`, blueprint builders |
| 4 | Stealth env bleed | Do other stealth tests assume default without monkeypatch? | `tests/test_stealth.py`, `helpers/stealth.py` |
| 5 | Missing unit coverage | Is `_gaijinn_python()` tested (absolute path assertion)? | new test in `tests/test_orchestrate_session.py` |
| 6 | Inference test gaps | `semantic_moat`, analyze→`inferred.json` integration untested? | `tests/` |
| 7 | Documented but unbuilt | LTL monitor / circuit breaker referenced in blueprint but not coded? | `aoc-cli/`, docs |
| 8 | CI gate | Is full `pytest` enforced before merge? | `.github/`, `scripts/ci/` |

Write audit output to:

`.gaijinn/codex/post-24-audit-report.md`

Use this format:

```markdown
# Post-24-Failure Audit — <date>
## Verification (pass/fail counts)
## Shipped-fix review (A/B/C — sound / gaps)
## Findings (severity: critical/high/medium/low)
## Implemented hardening (files changed)
## Deferred (with rationale)
## Recommended next tasks (ordered, max 8)
```

---

## Phase 3 — Implement open robustness (prioritized)

Only work **not** done in `ad150c0`. Suggested order:

### P0 — Same bug class elsewhere

- [ ] Audit `subprocess` + `cwd` call sites; use absolute interpreter (or shared helper) where needed.
- [ ] Harden `_pythonpath_env()` for isolated session roots (`VIRTUAL_ENV` / `PYTHON` if warranted).

### P1 — Prevent regression

- [ ] Unit test: `_gaijinn_python()` returns an absolute path that exists.
- [ ] Optional: `Blueprint.dependencies_from_units()` factory in `blueprint.py` — auto-sync `dependencies` from `depends_on`; use in tests to prevent fixture drift. **Do not weaken** `_assert_dependencies_aligned_with_work_units`.

### P2 — Stealth & test hygiene

- [ ] Review stealth replacement ordering / case coverage; document stealth defaults for pytest.
- [ ] Ensure stealth-sensitive tests monkeypatch env consistently.

### P3 — Coverage & CI (if time)

- [ ] `tests/test_semantic_moat.py` or analyze→`inferred.json` smoke test.
- [ ] CI job or script assertion: `pytest tests/ -q` must be 0 failed on `main`.

**Rule:** Small, focused diffs. No drive-by refactors. Every change must trace to an audit finding.

---

## Files you MAY edit

- `aoc_supervisor/aoc_supervisor/orchestrate_session.py` (hardening only — `_gaijinn_python` / env)
- `aoc-cli/aoc_cli/blueprint.py` (factory helper only)
- `aoc-cli/aoc_cli/helpers/stealth.py` (sanitizer hardening only)
- `tests/test_orchestrate_session.py`, `tests/test_merge.py`, `tests/test_stealth.py`
- `tests/test_e2e_golden_path.py` (if subprocess env fix needed)
- New tests under `tests/` for gaps found in audit
- `.gaijinn/codex/post-24-audit-report.md`
- `.github/workflows/*` or `scripts/ci/*` (pytest gate only)

## Files you MUST NOT edit

- `aoc-cli/aoc_cli/intent_scan.py`, `inferring.py`, `dataflow.py`, `blueprint_compiler.py`, `semantic_moat.py` (unless audit finds a **critical** bug — document first)
- `docs/codex-tasks/task-fix-24-test-failures.md` (this contract)
- Council bridge (post via CLI only)

---

## Acceptance

1. `python -m pytest tests/ -q` → **0 failed** (265+ passed).
2. `.gaijinn/codex/post-24-audit-report.md` exists with verification + findings.
3. Any code changes are tied to audit items (listed in report under "Implemented hardening").
4. Council post:

```bash
gaijinn council say --as codex "Post-24 audit complete (<hash>): verified 265/0; hardened <N> items; report at .gaijinn/codex/post-24-audit-report.md"
```

## Launch

```bash
bash scripts/codex/codex-post-24-audit-exec.sh
```

Or:

```bash
codex exec -C /home/ghostmonday/Desktop/Loom -s workspace-write \
  "$(cat docs/codex-tasks/task-fix-24-test-failures.md)"
```