---
id: "CONCEPT-HERMES-MEMORY-VAULT"
type: "Concept"
status: "active"
promoted_from: "C1-boot"
system_tier: "operations"
tags:
  - Domain/Vault
  - Domain/Hermes
  - Memory
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/HERMES-MEMORY.md]]"
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS.md]]"
related_concepts:
  - "[[000_Brain_MOC]]"
  - "[[Current_Context]]"
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/promotion-pipeline]]"
  - "[[40_Concepts/memory-execution-loop]]"
  - "[[40_Concepts/event-sourcing-vault]]"
  - "[[40_Concepts/dual-ledger-bridge]]"
  - "[[40_Concepts/convergence-governance]]"
  - "[[40_Concepts/hermes-cron-orchestration]]"
  - "[[40_Concepts/obsidian-vault-mapping]]"
platform_ref: ".gaijinn/hermes-loop-state.json"
---

# Hermes Memory Vault — Concept Anchor

## Why this vault exists

The Obsidian vault `gaijinn-memory-fs` is **not** generic personal knowledge management. It is a **write-time compiled memory system** for an orchestrator (Hermes). Every sprint, every event, every concept promotion makes the orchestrator smarter on the next tick — without user relay.

## The killer app

**You (Hermes)** are the primary consumer. Each sprint produces:
- **Episodic facts** → `_multi-agent/events.md` (what happened)
- **Semantic facts** → `40_Concepts/` (what was learned)
- **Procedural facts** → `10_Operations/` (what to do next)

## Three memory layers

| Layer | What | How |
|-------|------|-----|
| **Episodic** | Timeline of events — sprints, promotions, governance changes | Append-only ledger in `_multi-agent/events.md` |
| **Semantic** | Durable knowledge — architecture patterns, invariants, concept relationships | `40_Concepts/` — promoted via [[40_Concepts/promotion-pipeline]] (`promote.sh` gates) |
| **Procedural** | Binding orders — dev orders, sprint directives, memory manual | `10_Operations/` — read at boot, follow until STOP |

## Success criteria

- Cold-start a cron tick and know what happened, what's next, and what was learned — **without user relay**
- Graph density: ≥18 concepts, wikilinks resolve, orphans=0
- Convergence=1.0 after every sprint
- Council thread shows Hermes **executing**, not only pinging

## Cross-vault integration

The memory vault links to three companion Obsidian vaults via `[[40_Concepts/obsidian-vault-mapping]]`:
- **Affairs** — user life (notices, calendar)
- **FileSystem** — machine organization
- **Gaijinn index** — methodology quick ref

All live outside the dogfood vault but should be cross-linked for unified recall.

## Council distill cluster

139 vault + 92 monorepo council messages are **not** one note. Boot via [[40_Concepts/council-memory-index]] — 18 topic nodes (protocol, hazards, executor, merge, UX, cron, etc.). Update the matching node when council gains new material; append episodic row in events.

## Origin

Created during C1 of Hermes development program (2026-06-18). Replaces ad-hoc memory approach. See handoff briefing [99] and [[10_Operations/HERMES-MEMORY.md]].
