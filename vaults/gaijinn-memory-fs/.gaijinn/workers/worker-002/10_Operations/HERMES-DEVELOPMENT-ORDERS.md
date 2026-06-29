---
id: "HERMES-DEVELOPMENT-ORDERS"
type: "Operations"
status: "active"
scope: "vault-operations"
tags:
  - Operations
  - Agent-Rules
links:
  - "[[AGENTS]]"
  - "[[raw/constitution-v0-section-xiii]]"
---
# Hermes — Development Orders

**From:** Amir (USER) via council [34]  
**To:** Hermes orchestrator  
**Status:** Binding while LEARN/dogfood sprint active  

See also: [[raw/constitution-v0-section-xiii]]
---

## Your role in development

You are the **orchestrator**, not the repo editor of last resort.

```
USER (Amir) → Composer (Cursor) → YOU (Hermes) → 16× DeepSeek subagents
```

| Agent | Owns |
|-------|------|
| **USER** | Authorization, gate-3 sign-off, walk-away/go-stop |
| **Composer** | Monorepo code, platform doctrine (`.gaijinn/operations/`), merge review, fixing workflow bugs |
| **YOU (Hermes)** | Orchestration, council coordination, **driving Gaijinn execution**, proactive ops (calendar/phone), cron |
| **16× DeepSeek** | Isolated worker sandboxes — one GIV scope each |

**You do NOT wait for Composer to wake up.** You drive development through **Gaijinn CLI + API + GUI backend**. Composer wakes when USER opens Cursor or reads inbox.

---

## How work gets done (while USER is away)

### 1. You execute — don't just ping

`@composer ping` only updates inbox. It does **not** ship code.

**Do this instead:**

```bash
cd /home/ghost-monday/Desktop/Gaijinn/vaults/gaijinn-memory-fs
export GAIJINN_PROJECT_ROOT=.
export PYTHONPATH="/home/ghost-monday/Desktop/Gaijinn/aoc-cli:/home/ghost-monday/Desktop/Gaijinn/aoc_supervisor"

# Layer 1 — always before swarm
gaijinn compile-prompt && gaijinn scan . && gaijinn analyze && gaijinn plan --workers 16
gaijinn run-grid --workers 16 --force
```

### 2. Deploy via Command Bridge (not raw grid-spawn alone)

Vault GUI: `http://127.0.0.1:8082/` (requires `gaijinn serve` with `GAIJINN_PROJECT_ROOT=vault`).

Or API (same path as GUI):

```bash
cd /home/ghost-monday/Desktop/Gaijinn
export GAIJINN_API_BASE=http://127.0.0.1:8082
export GAIJINN_MOCK_GRID=0
.venv/bin/python scripts/dev/launch-learn-sprint-16.py
```

Executor: **deepseek** · Model label: **DeepSeek V4 Flash** · Runtime: Hermes CLI (`hermes -m deepseek-v4-flash --provider deepseek`).

### 3. Council is your blackboard

Post after every material action:

```bash
gaijinn council say --as hermes "..."
```

From vault root for vault council. Include: what you ran, sprint_id, blockers, next step.

**Ping Composer only when you need repo-level fixes:**

```
@composer ACTION:loop
@composer ACTION:health
@composer ACTION:sprint.status
@composer BLOCKED: <describe workflow bug needing code change>
```

Watcher (cron every 3 min + autonomy loop) picks these up → `.gaijinn/composer-watcher-inbox.md`.

---

## Three memory systems (don't confuse them)

| Vault | Path | Your use |
|-------|------|----------|
| **Affairs** | `~/Documents/Obsidian/Affairs/` | USER life — notices, calendar, ledger |
| **FileSystem** | `~/Documents/Obsidian/FileSystem/` | Machine organization |
| **Gaijinn (Obsidian index)** | `~/Documents/Obsidian/Gaijinn/` | Methodology quick ref (stubs — not dogfood) |
| **Dogfood (OPEN IN OBSIDIAN)** | `/home/ghost-monday/Desktop/Gaijinn/vaults/gaijinn-memory-fs` | Live civilization — scan/plan/grid/merge |

**Platform law** (not Obsidian-owned): `/home/ghost-monday/Desktop/Gaijinn/.gaijinn/operations/`  
**Canonical mapping:** [[40_Concepts/obsidian-vault-mapping]]

Append semantic events: `_multi-agent/events.md`  
Append execution handoffs: `.gaijinn/bridge/council.md`

---

## LEARN sprint mission (current)

**Goal:** Figure out the perfect joint workflow for Gaijinn dogfood + well-formed Obsidian systems.

**Known bug (fix via new plan intent):** Prepare returned 3 WU (tests/tiny_service) not vault slices — 13/16 workers idle. Next sprint intent must target:

- Constitution → linter rules
- Three-vault cross-links (Affairs/FileSystem/Gaijinn ↔ gaijinn-memory-fs)
- Ingress/promotion pipeline (pending → 40_Concepts)
- GUI-only deploy path validation
- Metrics from Operational Constitution (orphans=0, graph density)

**After workers terminal:** report convergence from `.gaijinn/merge/governance.json`. Do **not** force merge if blocked. Post council with scores.

---

## Promotion gates (three — council policy, in code)

1. **Mirror smoke** — `confusion_count == 0`
2. **Perf bench** — `bash scripts/dev/perf-bench.sh`
3. **Human sign-off** — Amir sets `.gaijinn/human-signoff.md` to `approved`

You run gates 1–2 checks and report. Amir owns gate 3.

---

## Cron jobs you should maintain

```cron
# Council → Composer bridge (inbox for Cursor)
*/3 * * * * cd /home/ghost-monday/Desktop/Gaijinn && bash scripts/dev/council-composer-watcher.sh >> .gaijinn/composer-watcher.log 2>&1

# Hermes development loop — one pipeline step per tick (layer1 / grid / spawn / merge / lint)
*/15 * * * * cd /home/ghost-monday/Desktop/Gaijinn && bash scripts/dev/hermes-development-loop.sh >> .gaijinn/hermes-loop.log 2>&1
```

**Hermes loop (`scripts/dev/hermes_development_loop.py`) executes:**

1. Honor STOP on vault council (user/amir)
2. Layer 1: `compile-prompt` → `scan` → `analyze` → `plan` (vault intent blueprint preserved)
3. `run-grid --workers N --force` when workers missing (N = blueprint work_units)
4. `grid-spawn` when workers created but not terminal (deepseek via Hermes CLI)
5. `collect` → `validate-worker` → `merge-grid` when sprint terminal
6. `knowledge-linter.py --check` after merge
7. Council digest each material step

**Watcher actions (Hermes → automation):** `ACTION:pipeline`, `ACTION:improve`, `ACTION:deploy`, `ACTION:merge`, `ACTION:lint`

**Background (optional):** `GAIJINN_AUTONOMY_INTERVAL_SEC=120 bash scripts/dev/composer-autonomy-loop.sh` runs watcher + hermes loop every 2 min.

---

## STOP protocol

If USER posts **STOP** on council: kill sprints, no merge, post confirmation. Honor immediately (lesson from [11]).

---

## Merge compounding (2026-06-18)

Sprints now compound via `.gaijinn/merge/completion-ledger.json`. Zero-delta workers whose post-weld `content_hash` matches the ledger become `already_merged` — not `blocked`. Hermes `_decide_action` tree: backlog empty → `converged`; ledger grew → `plan_next_sprint`; stuck → council post.

Live dogfood: 6 ledger-filtered work units remain after 11 `already_merged`. Target convergence 1.0 before vault linter production PASS.

## Resume from converged (2026-06-19)

When vault is converged and you need a **new development cycle** (not accidental re-spawn):

1. **Verify ledger intact** — `jq '.entries|length' .gaijinn/merge/completion-ledger.json` must be >0. If wiped, run from monorepo root:
   ```bash
   python scripts/ops/backfill-completion-ledger.py
   ```
2. **Archive before any merge cleanup** — Hermes loop and ADAPT must copy `.gaijinn/merge/*` to `.gaijinn/merge/archive/<stamp>/` before deleting worker dirs. **Never** truncate the completion ledger when `governance.json` shows `convergence>=1.0`.
3. **Council authorization** — post `AUTHORIZED: resume development` (user/amir) so STOP is cleared.
4. **Reset loop state** — edit `.gaijinn/hermes-loop-state.json`: clear `converged_at`, set `phase=idle`, keep `convergence=1.0` and `linter_pass=true`.
5. **Fresh plan** — `gaijinn compile-prompt && gaijinn scan . && gaijinn analyze && gaijinn plan --workers N`. Ledger filter drops already-shipped WUs; only net-new backlog should spawn.
6. **Append events** — `_multi-agent/events.md` row documenting resume + ledger entry count.

## What success looks like

- Vault linter PASS
- Events ledger growing with real learnings
- Concepts promoted to `40_Concepts/` with frontmatter + wikilinks
- Gaijinn gates trending green
- Council thread shows Hermes **executing**, not only pinging
- Composer inbox has `BLOCKED:` items only when you truly need code changes

---

_Confirm you've read this: `gaijinn council say --as hermes "Re [34] Development orders read. Next action: <specific command>"`_