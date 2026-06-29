# Claw X SESSION START — mandatory every time

**Do this before any Codex slice, dump, or "what's next?" answer.**  
If you skip this, you will repeat stale-queue mistakes. No exceptions.

---

## Step 0 — Announce

Reply first line only:

```
SESSION START: reading ops docs + syncing main
```

---

## Step 1 — Read these 4 files (in order)

| # | File | Why |
|---|------|-----|
| 1 | `docs/operations/automation-work-queue.md` | Status board — what's done vs NOW |
| 2 | `docs/operations/clawx-mission.md` | Current directive |
| 3 | `docs/operations/deepseek-roadmap-to-completion.md` | Stack order + ENFORCEMENT block |
| 4 | `docs/codex-tasks/loom/MASTER-loom-codex.md` | Slice DAG |

**If source dump task:** also read `docs/operations/deepseek-source-dump-rules.md`

**Skills loaded:** `loom-codex-delegate`, `loom-intent-mapping-v2` (never v1)

---

## Step 2 — Sync repo

```bash
cd ~/Desktop/gaijinn
git checkout main
git pull origin main
git log --oneline -5
git status -sb
```

Report: branch, HEAD commit, clean or dirty.

---

## Step 3 — Verify environment (always .venv)

```bash
cd ~/Desktop/gaijinn
test -x .venv/bin/python || { echo "BLOCKER: no .venv"; exit 1; }
.venv/bin/python -m pytest --version
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
```

**Never use system `python` for pytest.** Always `.venv/bin/python`.

**Snap terminals** set `SNAP` globally — repo `.venv` must still be used for `gaijinn` subprocesses. If needed: `export GAIJINN_PYTHON=~/Desktop/gaijinn/.venv/bin/python`.

---

## Step 4 — Reconcile queue vs git

Compare `automation-work-queue.md` status board to:

- `git log --oneline -20`
- `.gaijinn/codex/loom-cNN-run.jsonl` presence
- `.venv/bin/python -m pytest <slice verify>` for anything marked NOW

If board is stale → **update the board in the same session** before running new slices.

---

## Step 5 — Report session brief (template)

```
SESSION BRIEF
- HEAD: <hash> <subject>
- Queue NOW row: <slices>
- Last verify: <command> → pass/fail
- Blockers: <none | list>
- Next action: <one slice id>
```

Wait for user green light only if mission says stop; otherwise execute NOW row.

---

## Failure modes you already hit (don't repeat)

| Mistake | Fix |
|---------|-----|
| Didn't read queue on start | This file |
| Stale "C05 NOW" when C08 on main | Step 4 reconcile |
| system python for pytest | Step 3 .venv |
| Improvised source dump | `scripts/dev/source-dump.sh` only |
| Loaded v1 + v2 intent skill | v2 only |