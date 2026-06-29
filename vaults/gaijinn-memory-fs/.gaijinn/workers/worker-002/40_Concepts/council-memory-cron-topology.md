---
id: "CONCEPT-COUNCIL-MEMORY-CRON"
type: "Concept"
status: "active"
tags: [Domain/Hermes, Automation]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/hermes-cron-orchestration]]"
  - "[[40_Concepts/memory-execution-loop]]"
platform_ref: "scripts/dev/hermes_development_loop.py"
council_ref: "vault [87][862], monorepo [89–90]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Cron topology (distilled)

## Primary loop — Hermes dev loop

**Script:** `scripts/dev/hermes_development_loop.py`  
**Schedule:** `*/15` cron (one action per tick)  
**State:** `.gaijinn/hermes-loop-state.json` (project root)  
**Vault overlay:** `vaults/gaijinn-memory-fs/.gaijinn/hermes-loop-state.json`

### Phase machine (one step per tick)

```
idle → layer1 (compile-prompt, scan, analyze)
     → run-grid → spawn → terminal
     → collect → validate-worker → merge-grid
     → linter → converged | plan_next_sprint | stuck
```

**Vault intent:** preserve vault blueprint — skip graph-derived plan when configured.

## Companion crons (~5 jobs, monorepo [89])

| Job | Role |
|-----|------|
| `gaijinn-adapt` | Light maintenance in converged phase; log truncation; loop fixes |
| `gaijinn-dev-loop` | Parent project layer1 progression |
| `perf-bench.sh` | Gate 2 — API latency; skips gracefully if API offline [93] |
| `composer-autonomy-loop` | **Hazard:** duplicate spend if parallel to Hermes |
| Council composer-watcher | `@composer` lines only — not vault executor |

## Three gates (converged health)

1. **Confusion count** — doc/ops consistency
2. **perf-bench.sh** — endpoint SLOs (or skipped if no server)
3. **Human signoff** — promotion narrative approval

All three PASS → safe to claim stable converged phase.

## ADAPT behavior in converged phase

- Truncate `~/.hermes/logs/agent.log` when >500 lines
- Post council only for **non-trivial** changes ([90])
- Routine truncation → `[SILENT]` (reduced spam)

## Throttle & stuck patterns

| Symptom | Cron behavior | Fix |
|---------|---------------|-----|
| Dead spawn PID | Stuck in spawn throttle | Clear PID file + stale workers [862] |
| `_worker_count()==14` + all failed | Idle forever | Remove stale manifest [87] |
| `work_units=[]` | Repeated empty spawns | **Pause spawn** — plan fix |
| Convergence <1.0 post-merge | Linter blocks cleanup | Replay ledger / already_merged |

## Parallel agents

- **Hermes cron:** vault pipeline + council digest
- **AFK Cursor/Grok:** concept sprawl, merge blocks, `AFK:` council notes
- **Rule:** Do not fight cron; coordinate via council + loop-state