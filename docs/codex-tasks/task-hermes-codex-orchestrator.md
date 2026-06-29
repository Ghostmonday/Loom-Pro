# Hermes — Codex Fullpass Orchestrator Handoff

**You own this.** Amir delegated the entire backend Codex pass to Hermes. Cursor is frozen on backend implementation.

## Read first

1. `.gaijinn/bridge/council.md` — thread [#34] Hermes handoff
2. `docs/codex-tasks/MASTER-codex-fullpass.md`
3. Baseline: tag `pre-codex-fullpass-6361ad5`, branch `main` @ `6da3715+`

## Your job

Orchestrate **6 Codex slices** across the full Gaijinn backend. Launch local `codex exec` (parallel where paths are disjoint). Post council progress after each wave. Do **not** ask Amir to relay — use council only.

## RACI

| Agent | Role |
|-------|------|
| **Hermes** | Orchestrate Codex slices, parallel waves, exec scripts, council updates |
| **Codex** | Implement per slice task doc |
| **Cursor** | Review diffs + merge if green; `ui/` only |
| **Amir** | Dogfood judgment after Slice 6 |

## Slices

| # | Task doc | Acceptance |
|---|----------|------------|
| 1 | `task-codex-slice-01-cli-core.md` | `pytest tests/test_cli.py tests/test_gravity.py tests/test_blueprint.py tests/test_moat.py -q` |
| 2 | `task-codex-slice-02-merge-grid.md` | `pytest tests/test_merge*.py tests/test_handoff.py tests/test_grid_executor.py -q` |
| 3 | `task-codex-slice-03-orchestrate.md` | orchestrate + supervisor + workflow + ui_intent_smoke |
| 4 | `task-codex-slice-04-inference.md` | intent + inferring + dataflow + blueprint_compiler |
| 5 | `task-codex-slice-05-tests-ci.md` | full pytest + `scripts/ci/acceptance.sh` |
| 6 | `task-backend-gears.md` | `prompt_coverage` internal tooling |

## Parallel strategy (local) — Amir approved 5-way parallel

Use **git worktrees** under `.gaijinn/hermes-worktrees/slice-NN/`.

**Wave 1 — launch all 5 in parallel (Slices 1–4 + 6):**
Each slice respects MAY-edit boundaries — no cross-slice file edits.

| Worktree | Slice | Codex task |
|----------|-------|------------|
| `slice-01` | 1 | `task-codex-slice-01-cli-core.md` |
| `slice-02` | 2 | `task-codex-slice-02-merge-grid.md` |
| `slice-03` | 3 | `task-codex-slice-03-orchestrate.md` |
| `slice-04` | 4 | `task-codex-slice-04-inference.md` |
| `slice-06` | 6 | `task-backend-gears.md` |

**Merge stack order after Wave 1 completes:** 1 → 2 → 3 → 4 → 6 (resolve test conflicts unlikely — disjoint test files).

**Wave 2 — Slice 5 only (after Wave 1 merged to main):**
- Full `tests/**` + CI sweep — integration pass, not parallel with others.

Create missing exec scripts: `scripts/codex/codex-slice-0N-*-exec.sh` (copy pattern from `codex-post-24-audit-exec.sh`).

## Per-slice protocol

1. `codex exec -C <worktree> -s workspace-write "$(cat docs/codex-tasks/task-codex-slice-0N-....md)"`
2. Log → `.gaijinn/codex/slice-0N-run.jsonl`
3. Report → `.gaijinn/codex/slice-0N-report.md`
4. Run slice acceptance + `python -m pytest tests/ -q`
5. Merge to `main`, tag `codex-slice-0N-done`
6. `gaijinn council say --as hermes --id hermes "Slice N complete: ..."`

## Dogfood (NOT until Slice 6 + Amir sign-off)

```
Build a test editor in Rust and Go, styled for developers who work at a dark, elegant workstation.
```

Real grid: `GAIJINN_MOCK_GRID=0`, `executor=codex`.

## Already merged (do not redo)

- Post-24 audit `1d8ec8a`
- Cursor backend gears `6361ad5` — audit/extend only

## Start command

```bash
cd /home/ghostmonday/Desktop/Loom
gaijinn council say --as hermes --id hermes "Hermes accepting Codex fullpass orchestration. Starting Wave 1."
# then create worktrees + launch slice 1 and 4 codex exec in parallel
```