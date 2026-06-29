---
name: loom-session-start
description: Mandatory Loom/Gaijinn session start for Grok and Composer. Read ops docs, sync main, use .venv only, reconcile automation-work-queue.md to git log. Use when starting Loom work, asking what's next, delegating Codex, or pasting Claw X missions.
---

# Loom session start

Execute before any slice, status answer, or source dump.

## Step 0

Reply first line:

```
SESSION START: reading ops docs + syncing main
```

## Read (in order)

1. `docs/operations/automation-work-queue.md`
2. `docs/operations/clawx-mission.md`
3. `docs/operations/deepseek-roadmap-to-completion.md`
4. `docs/codex-tasks/loom/MASTER-loom-codex.md`

Source dump tasks: also `docs/operations/deepseek-source-dump-rules.md` and `loom-codex-delegate/SOURCE-DUMP.md`.

## Sync

```bash
cd ~/Desktop/gaijinn
git checkout main && git pull origin main
git log --oneline -5
git status -sb
```

## Verify (.venv only)

```bash
test -x .venv/bin/python
.venv/bin/python -m pytest --version
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
```

Never use system `python` for pytest.

## Reconcile

Compare queue status board to `git log -20` and slice verify pytest. Update the queue in-session if stale.

## Report

```
SESSION BRIEF
- HEAD: <hash> <subject>
- Queue NOW row: <slices>
- Last verify: <command> → pass/fail
- Blockers: <none | list>
- Next action: <one item>
```

## Stale path trap

Do **not** trust `.gaijinn/clawx-mission.md` or `.gaijinn/deepseek-roadmap-to-completion.md` for status — they redirect to `docs/operations/`.