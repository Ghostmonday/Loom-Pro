# Loom completion hierarchy — pennies-scale delegation

**Goal:** Finish Loom backend (C20 green) then UI (C17) with minimal Composer spend.

## Chain of command

```
YOU          → decisions, AFK, approve merges, vision changes
COMPOSER     → architecture, task specs, gate reviews, unblock (expensive — use sparingly)
CLAW X       → wave orchestration, Codex dispatch, commit, report (DeepSeek — cheap)
CODEX        → one slice = one implementation (cheapest bulk coding)
```

## Who does what

| Layer | Cost | Do | Don't |
|-------|------|-----|-------|
| **You** | time only | Paste Claw X missions, go AFK, say "ship wave N" | Micromanage slices |
| **Composer** | $$$ | Write/fix task docs, review failed slices, intent-map gaps, merge conflicts | Run every codex exec |
| **Claw X** | ¢ | Read MASTER, run slices in DAG order, pytest verify, git commit, log `.gaijinn/codex/` | Invent architecture |
| **Codex** | ¢ | Implement exactly one `task-loom-cNN-*.md` | Skip gates or add UI early |

## Cost rules

1. **Composer only on gates:** wave complete, C19 integration fail, new LOOM ticket, intent-map hole.
2. **Claw X runs everything else:** parallel Wave 1, serial C06→C07→C08, wave handoffs.
3. **One slice per Codex exec** — never batch multiple task docs in one run.
4. **Tests are the manager** — green verify = commit; red = Claw X retries once, then escalate to Composer.
5. **No UI until C19 green** — saves expensive rework.

## Progress tracker (update after each wave)

| Wave | Slices | Status |
|------|--------|--------|
| 0 | C21 continuation+launch maps | ✅ `130e1d7` |
| 1 | C01,C02,C03,C04,C09 | C01✅ C02✅ C03⏳ C04⏳ C09⏳ |
| 2 | C05,C10 | pending |
| 3 | C06,C07,C08,C11,C18 | pending (C06→C07→C08 serial) |
| 4 | C19,C20 | pending — **backend done when C20 green** |
| 5 | C12–C17 | blocked until C19 |
| Post | LOOM-210 implementation | blocked until C20 |

## Claw X standard loop (every slice)

```bash
cd /home/ghostmonday/Desktop/gaijinn
git pull --rebase 2>/dev/null || true
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
mkdir -p .gaijinn/codex
codex exec --full-auto "$(cat docs/codex-tasks/loom/task-loom-cNN-....md)" \
  2>&1 | tee -a .gaijinn/codex/loom-cNN-run.jsonl
# run verify from task doc
git add -A && git commit -m "Cnn: <title> (LOOM-xxx)"
```

## Composer escalation triggers

Claw X stops and pings Composer when:

- Same slice fails verify **twice**
- Git merge conflict across waves
- Task doc ambiguous / missing action in intent map
- C19 `flow.loom_full_pipeline_mock` fails after C18 all green
- Codex tries to create `ui/terminal.*` or bypass handoff gate

## End-state definition (project complete v1)

```bash
.venv/bin/python -m pytest tests/test_loom_pipeline_intent.py tests/test_loom_mirror_forge.py \
  tests/test_loom_synthesizer.py tests/test_loom_teleology.py -q --no-cov
# C19: test_full_pipeline_mock green
# C20: all smoke_scenarios implementation_status flipped
# C12–C17: UI rebuilt from intent maps
bash scripts/dev/ui-intent-smoke.sh
```

## Active mission file

**Session start (mandatory):** `docs/operations/clawx-session-start.md`  
**Mission:** `docs/operations/clawx-mission.md`  
**Queue:** `docs/operations/automation-work-queue.md`

`.gaijinn/clawx-mission.md` is a redirect stub only — never edit or trust it for status.