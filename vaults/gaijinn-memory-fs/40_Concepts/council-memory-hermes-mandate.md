---
id: "CONCEPT-COUNCIL-MEMORY-HERMES-MANDATE"
type: "Concept"
status: "active"
tags: [Domain/Hermes, Governance]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/hermes-memory-vault]]"
  - "[[40_Concepts/council-memory-development-program]]"
council_ref: "vault [99], monorepo [51]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Hermes mandate (distilled from handoff [99])

## Executive shift (2026-06-18)

Amir transferred **primary driver** of development cycles to Hermes until USER posts **STOP** on council.

| Role | Responsibility |
|------|----------------|
| **USER** | STOP/GO, gate-3, scope authorization |
| **Hermes** | Execute pipeline, council, cron, **memory distill** |
| **DeepSeek workers** | GIV-scoped implementation |
| **Composer/Cursor** | Monorepo bugs only when Hermes posts `@composer BLOCKED:` |

## What Hermes is NOT

- Ping daemon or inbox updater only
- Human relay between agents
- Default owner of monorepo commit (P1 — Composer unless assigned WUs)

## Memory loop (binding)

**Learn → Act → Measure → Distill**

- Learn: council tail, events last 10, `hermes-loop-state.json`, governance
- Act: compile-prompt → scan → analyze → plan → grid → merge
- Measure: convergence, vault linter, promotion gates
- Distill: events + council + concept promotion

## Amir directive on vault purpose

> Develop the superb Obsidian vault for the most useful purpose — **Hermes memory**. Execution proves memory; distillation compounds it.

## C1 outcome (council [107])

Governance + ledger files created in vault `.gaijinn/merge/`; `HERMES-MEMORY.md` + `hermes-memory-vault.md` scaffolded; convergence artifact set to 1.0. Plan blocker documented separately.