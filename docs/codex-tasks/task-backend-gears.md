# Codex Task — Backend Gears (Pre-Dogfood)

**Status:** ✅ Complete — report: `.gaijinn/codex/slice-06-report.md` · full suite **284 passed**

## Objective

Harden backend machinery so Amir can dogfood with confidence. **No user-facing quality gates.** Creator-side correctness only.

**Dogfood target (later, not this sprint):** Rust + Go test editor, dark workstation elegance.

## Working directory

`/home/ghostmonday/Desktop/Loom`

## Setup

```bash
cd /home/ghostmonday/Desktop/Loom
export GAIJINN_MOCK_GRID=1
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
git pull --rebase origin main
```

## Files you MAY edit

- `aoc-cli/aoc_cli/**` (commands, helpers, blueprint, inferring, dataflow)
- `aoc_supervisor/aoc_supervisor/**` (except do not rewrite intent map JSON)
- `tests/test_*.py`

## Files you MUST NOT edit

- `ui/**` (Cursor owns terminal)
- `docs/codex-tasks/task-terminal-blueprint-review.md`

---

## P0 — Acceptance green

```bash
python -m pytest tests/ -q
bash scripts/ci/acceptance.sh
```

Fix any regression. Known invariant: `test_pkm_workflow_zero_confusion_mock` requires mock-grid merge convergence ≥ 0.875.

---

## P1 — Prompt → blueprint completeness (creator tooling)

Add **internal** dev helper (not user gate):

`aoc_supervisor/aoc_supervisor/prompt_coverage.py` (new)

```python
def explicit_requirements(intent: str) -> list[str]: ...
def blueprint_coverage(intent: str, blueprint: Mapping) -> dict[str, Any]: ...
```

- Map prompt phrases to expected `STREAM_SPECS` keys
- Return `{ "covered": [...], "missing": [...], "inferred": [...] }`
- Tests: tic-tac-toe, todo CLI, **test editor** prompt (see below)

**Test editor gold prompt (for fixture only — do not build yet):**

```
Build a test editor in Rust and Go, styled for developers who work at a dark, elegant workstation.
```

Expected streams (minimum): `foundation`, `editor_core`, `rust_core`, `go_bridge`, `editor_ui`, `tests`

---

## P2 — Blueprint factory (prevent fixture drift)

`aoc-cli/aoc_cli/blueprint.py`:

```python
@classmethod
def dependencies_from_units(cls, work_units: Sequence[WorkUnit]) -> dict[str, list[str]]: ...
```

Use in tests; do not weaken `_assert_dependencies_aligned_with_work_units`.

---

## P3 — Merge / validate robustness

- Mock grid: all completing workers pass `validate-worker` when log contains `build PASS`
- Dry-run convergence excludes `merge.not_dry_run` from scoring denominator
- Document in `tests/test_merge_integrity.py` if new mock behavior needs assertion

---

## P4 — Inference pipeline tests

Add if missing:

- `tests/test_semantic_moat.py`
- analyze → `inferred.json` integration smoke

---

## Acceptance

1. `265+ passed, 0 failed`
2. `bash scripts/ci/acceptance.sh` exits 0
3. `prompt_coverage` tests pass for tic-tac-toe + test-editor fixture
4. Council: `gaijinn council say --as codex "Backend gears ready (<hash>): acceptance green; prompt_coverage shipped"`

## Launch

```bash
bash scripts/codex/codex-backend-gears-exec.sh
```