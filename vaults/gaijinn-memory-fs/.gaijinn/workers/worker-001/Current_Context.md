---
id: "CURRENT-CONTEXT"
type: "Concept"
status: "active"
system_tier: "memory"
tags: [Hermes, Session, Swapping]
last_mutated: "2026-06-19T12:31:11Z"
related_concepts:
  - "[[000_Brain_MOC]]"
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/council-memory-empty-spawn-crisis]]"
dependencies:
  - "[[10_Operations/HERMES-MEMORY.md]]"
  - "[[.gaijinn/hermes-loop-state.json]]"
---

# Current Context — Hermes swapping memory

Updated end of each substantive session. Read **first** on cold boot (before council tail).

## Cold-boot contract (Hermes, 2026-06-18)

**Yes:** With vault current, Hermes can cold-start — playbook, recovery, council formats, architecture live in `council-memory-*` nodes + global council [1150].

**No:** Mid-stream context not yet written to vault is lost on reset.

**Before any context reset, write these three:**

1. `_multi-agent/events.md` — episodic row(s)
2. `.gaijinn/bridge/council.md` — operational digest
3. `Current_Context.md` — this file (phase, blocker, next actions)

Boot chain: **Current_Context → 000_Brain_MOC → council-memory-index → events last 10 → council tail → hermes-loop-state.json**

## Last session (2026-06-19, DeepSeek worker-001 grid-spawn PID 1112736 — re-execution)

- **Phase:** Worker-001 re-executed — 13 WUs validated (zero-delta, vault already converged)
- **Done:** All 13 WUs re-validated. Python syntax PASS all 3 files. Shell syntax PASS promote.sh. YAML syntax PASS vault.yaml (8 keys). Coupling: prompt_coverage imports intent_blueprint (1 class IntentStream, 8 functions + 3 functions). Markdown frontmatter valid in 25/27 files (README.md + aoc_supervisor/README.md intentionally no-frontmatter).
- **Blocker:** None — vault linter PASS, 0 Shadow Bridges, 13 rejected nodes (known stale), convergence 1.0 (last merge score)

## Vault health

| Beat | Files | Concepts | Pending | Links | Graph | Bridges | Rejected | WUs | Conv | Linter |
|------|-------|----------|---------|-------|-------|---------|----------|-----|------|--------|
| 2026-06-19T11:57:40Z | 65 files | 41 concepts | 0 pending | 70 links | graph 96n/13e | 150 bridges | 18 rejected | 22 work units | conv 1.0 | linter PASS |
| 2026-06-19 worker-001 PID 1105441 (re-exec) | 65 files | 41 concepts | 0 pending | 70 links | graph 96n/13e | 0 bridges | 13 rejected | 13 WUs verified | conv 1.0 | linter PASS |
| 2026-06-19T12:36Z re-exec worker-001 PID 1112736 | 65 files | 41 concepts | 0 pending | 70 links | graph 96n/13e | 0 bridges | 13 rejected | 13 WUs verified (zero-delta) | conv 1.0 | linter PASS |

## Next actions

1. Hermes: vault sprint when USER/Hermes authorizes — layer1 → run-grid → grid-spawn
2. Deferred: vault-gaijinn split (user **go**); design-partner demo
3. Keep vault current — append events + council on every material action

## Failure modes (resolved this session)

| Was | Fix |
|-----|-----|
| `work_units=[]` empty spawns | blueprint obsidian-vault domain + circuit breaker |
| Vault-root worker artifact leaks | deleted + gitignore |
| Stale duplicate ui/ + docs at repo root | moved/deduped to docs/vault + vault ui/ |

## Quick links

- Router: [[000_Brain_MOC]]
- Council index: [[40_Concepts/council-memory-index]]
- Playbook answer: global council [1150]
- Empty-spawn: [[40_Concepts/council-memory-empty-spawn-crisis]] (SHIPPED)
- Health: [[40_Concepts/metrics-dashboard]]