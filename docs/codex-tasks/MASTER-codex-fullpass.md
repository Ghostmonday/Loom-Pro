# MASTER: Codex Full-Codebase Pass (Pre-Dogfood)

**Baseline tag:** `pre-codex-fullpass-6361ad5`  
**Branch:** `main`  
**Orchestrator:** **Hermes** (council-backed, parallel local Codex)  
**Implementer:** Codex per slice  
**Reviewer:** Cursor merges only · Amir judges dogfood

**Hermes handoff:** `docs/codex-tasks/task-hermes-codex-orchestrator.md` · Council [#34]

**Progress (2026-06-17):** Slices 1, 2, 4, 5, 6 ✅ on `main` — **284 passed**, acceptance green. Slice 3 🔄 in-flight (`.gaijinn/codex/slice-03-status.md`). Dogfood blocked on slice 3 + UI review.

## Rules

1. **Cursor MUST NOT** commit to `aoc-cli/`, `aoc_supervisor/`, backend `tests/` except merge conflicts and Amir-approved hotfixes.
2. Every slice: task doc → `codex exec` → log in `.gaijinn/codex/` → slice acceptance → full suite → merge → council.
3. **No user-facing quality gates.** `prompt_coverage` is internal dev tooling only.
4. **Dogfood** (Rust/Go test editor) starts only after Slice 6 + Amir blueprint sign-off.

## Slice DAG

```
Slice 1 CLI core → Slice 2 merge/grid → Slice 3 orchestrate/API
  → Slice 4 intent/inference → Slice 5 tests/CI → Slice 6 prompt_coverage → DOGFOOD
```

Parallel UI (Cursor): `task-terminal-blueprint-review.md` after Slice 3 merges.

## Slices

| # | Task doc | Exec script | Acceptance |
|---|----------|-------------|------------|
| 1 | `task-codex-slice-01-cli-core.md` | `codex-slice-01-cli-core-exec.sh` | `pytest tests/test_cli.py tests/test_gravity.py tests/test_blueprint.py tests/test_moat.py -q` |
| 2 | `task-codex-slice-02-merge-grid.md` | `codex-slice-02-merge-grid-exec.sh` | `pytest tests/test_merge*.py tests/test_handoff.py tests/test_grid_executor.py -q` |
| 3 | `task-codex-slice-03-orchestrate.md` | `codex-slice-03-orchestrate-exec.sh` | `pytest tests/test_orchestrate_session.py tests/test_supervisor.py tests/test_workflow_evaluator.py tests/test_ui_intent_smoke.py -q` |
| 4 | `task-codex-slice-04-inference.md` | `codex-slice-04-inference-exec.sh` | `pytest tests/test_intent*.py tests/test_inferring.py tests/test_dataflow.py tests/test_blueprint_compiler.py -q` |
| 5 | `task-codex-slice-05-tests-ci.md` | `codex-slice-05-tests-ci-exec.sh` | `pytest tests/ -q && bash scripts/ci/acceptance.sh` |
| 6 | `task-backend-gears.md` | `codex-backend-gears-exec.sh` | `prompt_coverage` tests + full suite |

## Slice independence (can Hermes run all 6 in parallel?)

**Production code — mostly YES (disjoint paths):**

| Slice | Primary code | Overlaps |
|-------|--------------|----------|
| 1 | `aoc-cli` core, `blueprint.py`, scan/analyze/plan | Does not touch merge, supervisor, inference |
| 2 | `merge`, `handoff`, collect/grid commands | Does not touch cli core, supervisor |
| 3 | `aoc_supervisor/*` | Does not touch aoc-cli (imports only) |
| 4 | `intent_blueprint`, `inferring`, `intent_scan`, etc. | Does not touch merge or orchestrate files |
| 6 | `prompt_coverage.py` (new) | Small; keep scoped |

**Tests — NOT fully parallel-safe:**

| Slice | Test scope |
|-------|------------|
| 1–4 | Each owns **named** test files only (no overlap between slices) |
| **5** | `tests/**` — **entire tree** — conflicts if run while 1–4 are editing their tests |
| 6 | New `test_prompt_coverage*` — OK parallel if Slice 5 excluded |

**Verdict:** Hermes may run **Slices 1, 2, 3, 4, 6 in parallel** (5 worktrees). **Slice 5 must run last** after 1–4–6 merge to `main` (integration + CI sweep).

Optional aggressive mode (all 6 parallel): only if Slice 5 is **read-only verify** until others merge — not recommended.

## Parallel waves (Hermes — local worktrees)

| Mode | Waves | Slices |
|------|-------|--------|
| **Recommended** | Wave 1 | 1 + 2 + 3 + 4 + 6 parallel → merge stack → Wave 2: Slice 5 |
| Conservative | Wave 1 | 1 + 4 → Wave 2 | 2 → 3 → 6 → 5 |

## Per-slice merge protocol (Cursor reviews Hermes/Codex output)

1. Read `.gaijinn/codex/slice-NN-run.jsonl` + last message
2. Reject drive-by refactors unrelated to slice scope
3. Run slice acceptance then `python -m pytest tests/ -q`
4. Merge to `main`, tag `codex-slice-NN-done`
5. `gaijinn council say --as codex "Slice N complete (<hash>): ..."`

## Dogfood prompt (after Slice 6)

```
Build a test editor in Rust and Go, styled for developers who work at a dark, elegant workstation.
```

Grid: `GAIJINN_MOCK_GRID=0`, `executor=codex`.