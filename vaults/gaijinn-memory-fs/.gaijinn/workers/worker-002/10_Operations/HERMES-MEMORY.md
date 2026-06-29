---
id: "HERMES-MEMORY"
type: "Operations"
status: "active"
scope: "vault-operations"
tags:
  - Operations
  - Memory
  - Agent-Rules
links:
  - "[[AGENTS]]"
  - "[[40_Concepts/hermes-memory-vault]]"
  - "[[40_Concepts/council-memory-index]]"
  - "[[10_Operations/VAULT-GEMINI-SHARE]]"
  - "[[40_Concepts/memory-execution-loop]]"
  - "[[40_Concepts/event-sourcing-vault]]"
---

# Hermes Memory Vault — Operations Manual

**Purpose:** This vault (`gaijinn-memory-fs`) is **Hermes's operational memory**. Not generic PKM. Every sprint should make you smarter on the next tick without user relay.

---

## Memory systems (three layers)

| Layer | Vault location | What it stores | How you use it |
|-------|---------------|----------------|----------------|
| **Episodic** | `_multi-agent/events.md` | Sprint outcomes, concept promotions, governance changes | Append after every action. Read last 10 rows at boot. |
| **Semantic** | `40_Concepts/` | Durable knowledge — architecture, patterns, invariants | Promote from `/pending/` when knowledge is stable and reusable. |
| **Procedural** | `10_Operations/` | Orders (HERMES-DEVELOPMENT-ORDERS.md), sprint directives, memory manual (this file) | Read at boot. Follow as binding unless overridden by user STOP. |

---

## Your memory loop (boot sequence, every session/cron tick)

```
Learn → Act → Measure → Distill
```

1. **Learn:** Read [[Current_Context]] → [[000_Brain_MOC]] → [[40_Concepts/council-memory-index]] (phase nodes), council tail, events.md last 10, hermes-loop-state.json, governance.json
2. **Act:** Execute Gaijinn pipeline (scan → analyze → plan → run-grid → grid-spawn → collect → validate → merge)
3. **Measure:** Check governance.json convergence, run vault linter
4. **Distill:** Append events, post council digest, promote concepts from lingering learnings

---

## Cross-vault links

| Vault | Path | Purpose |
|-------|------|---------|
| **Affairs** | `~/Documents/Obsidian/Affairs/` | User life — notices, calendar, ledger |
| **FileSystem** | `~/Documents/Obsidian/FileSystem/` | Machine organization |
| **Gaijinn (Obsidian index)** | `~/Documents/Obsidian/Gaijinn/` | Methodology quick ref (stubs) |
| **Dogfood (THIS)** | `~/Desktop/Gaijinn/vaults/gaijinn-memory-fs` | Live civilization — the one that matters |

---

## Key paths

| Path | Purpose |
|------|---------|
| `_multi-agent/events.md` | Episodic event ledger (append-only) |
| `.gaijinn/bridge/council.md` | Execution handoffs, decisions, sprint reports |
| `40_Concepts/council-memory-index.md` | Distilled council — many nodes, not one megathread |
| `.gaijinn/merge/governance.json` | Convergence score (target 1.0) |
| `.gaijinn/hermes-loop-state.json` | Hermes dev loop phase machine |
| `10_Operations/knowledge-linter.py` | Vault integrity checker |

---

## Rules

1. **Both ledgers** on material changes: `_multi-agent/events.md` (semantic) + council.md (operational). Neither substitutes for the other.
2. **Post council before and after** every non-trivial action.
3. **If stuck** (backlog>0, nothing merged): council post with root cause. Do not idle-loop.
4. **Honor STOP** from user/amir immediately (kill sprints, no merge).

## Before context reset (mandatory)

Hermes survives cold boot only when the vault is current. Unsaved mid-stream context is the real loss mode.

Write **all three** before end of session or reset:

| # | Target | What to capture |
|---|--------|-----------------|
| 1 | `_multi-agent/events.md` | What happened, who, outcome |
| 2 | `.gaijinn/bridge/council.md` | Handoffs, blockers, next step |
| 3 | `[[Current_Context]]` | Phase, blocker, next actions, boot notes |

Then boot: Current_Context → Brain MOC → council-memory-index → events tail → council tail.
