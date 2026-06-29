---
id: "CONCEPT-COUNCIL-MEMORY-INDEX"
type: "Concept"
status: "active"
system_tier: "memory"
tags:
  - Domain/Hermes
  - Memory
  - Council
promoted_from: "manual-distill-2026-06-18"
related_concepts:
  - "[[40_Concepts/hermes-memory-vault]]"
  - "[[40_Concepts/dual-ledger-bridge]]"
  - "[[40_Concepts/event-sourcing-vault]]"
linked_operations:
  - "[[10_Operations/HERMES-MEMORY.md]]"
  - "[[.gaijinn/bridge/council.md]]"
platform_ref: "vaults/gaijinn-memory-fs/.gaijinn/bridge/council.md"
coverage: "139 vault messages + 92 monorepo messages (through 2026-06-18)"
---

# Council Memory — Index (distilled nodes)

Hermes boot: read this index, then the nodes relevant to your current phase. Raw thread: `.gaijinn/bridge/council.md` (vault) and monorepo `.gaijinn/bridge/council.md`.

## Protocol & bus

| Node | What you learn |
|------|----------------|
| [[40_Concepts/council-memory-protocol]] | How council works; dual ledger with events.md |
| [[40_Concepts/council-memory-handoff-bus]] | TX-HT tickets, alerts, receipts |

## Authority & program

| Node | What you learn |
|------|----------------|
| [[40_Concepts/council-memory-hermes-mandate]] | USER handoff [99]; Hermes drives cycles; control chain |
| [[40_Concepts/council-memory-development-program]] | Projects P0–P6; cycles C1–C5 |
| [[40_Concepts/council-memory-product-vision]] | Layer A→D; blueprint-native IDE sequence |

## Execution & proof

| Node | What you learn |
|------|----------------|
| [[40_Concepts/council-memory-executor-stack]] | hermes + deepseek-v4-flash; NOT codex for DeepSeek |
| [[40_Concepts/council-memory-merge-compounding]] | Ledger, stable WU ids, already_merged, Q1–Q10 |
| [[40_Concepts/council-memory-vault-dogfood-arc]] | 0.6667 → 1.0 journey; 6-WU + 5-WU sprints |
| [[40_Concepts/council-memory-convergence-semantics]] | What scores mean; honest no-op vs failure |

## Failures we already paid for

| Node | What you learn |
|------|----------------|
| [[40_Concepts/council-memory-infrastructure-incidents]] | Dual-directory, spawn spiral, executor schema |
| [[40_Concepts/council-memory-empty-spawn-crisis]] | Plan straddling; 11 empty spawns; pause grid |
| [[40_Concepts/council-memory-operational-hazards]] | Locked checklist — do not repeat |

## Platform & UX

| Node | What you learn |
|------|----------------|
| [[40_Concepts/council-memory-monorepo-state]] | 97 WIP files; pytest 386; integration branch |
| [[40_Concepts/council-memory-cron-topology]] | dev-loop, adapt, gates, converged phase |
| [[40_Concepts/council-memory-ux-process-stage]] | 12 control points; Neural Draft /internal UI |

## Worker sprint themes (vault council)

| Node | What you learn |
|------|----------------|
| [[40_Concepts/council-memory-sprint-14w-arc]] | 14-worker era; governance sync WUs |
| [[40_Concepts/council-memory-vault-artifacts-shipped]] | What workers actually merged (linter, profiles, concepts) |

## Topology maintenance (swarm 2026-06-18)

- Router: [[000_Brain_MOC]] — brain entry before this index on cold boot
- Merge/split rules: [[40_Concepts/vault-topology-and-density]]
- Metrics health: [[40_Concepts/metrics-dashboard]] → convergence / gravity / linter sub-nodes

## Maintenance

- **Distill rule:** New material council posts → append episodic row in `_multi-agent/events.md` + update the matching node here (not a new megathread).
- **Node count:** 17 topic nodes + this index (18 files under `council-memory-*`).
- **Last full distill:** 2026-06-18 (manual; covers inception through council [139] vault / [92] monorepo).