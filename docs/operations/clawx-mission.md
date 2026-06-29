# Claw X active mission

**Every session:** read `clawx-session-start.md` first — no exceptions.

**Queue:** `automation-work-queue.md`  
**Skills:** `loom-intent-mapping-v2`, `loom-codex-delegate`

## Current priority

1. **SESSION START ritual** (sync main, .venv, reconcile queue)
2. **UI wave C12–C17** — backend FIX green (`test_full_pipeline_mock` + teleology 7/7)
3. Report SESSION BRIEF; escalate to Composer only on critique maps or double-failed slice

## Done (do not redo)

C01–C11, C18–C23, C21 — see queue for verify notes

## Environment

```bash
cd ~/Desktop/gaijinn
.venv/bin/python -m pytest ...
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
```