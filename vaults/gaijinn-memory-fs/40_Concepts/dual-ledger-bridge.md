---
id: "CONCEPT-DUAL-LEDGER-BRIDGE"
type: "Concept"
status: "active"
promoted_from: "AFK-sprawl-sprint"
system_tier: "governance"
tags:
  - Domain/Vault
  - Domain/Platform
  - Dual-Ledger
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS.md]]"
  - "[[.gaijinn/operations/MEMORY-EXECUTION-LOOP.md|memory-execution-loop]]"
related_concepts:
  - "[[40_Concepts/memory-execution-loop]]"
  - "[[40_Concepts/vault-gaijinn]]"
  - "[[40_Concepts/convergence-governance]]"
  - "[[40_Concepts/event-sourcing-vault]]"
platform_ref: ".gaijinn/operations/DUAL-LEDGER-BRIDGE.md"
---
# Dual Ledger Bridge — Vault ↔ Platform Sync

Every vault concept must have a corresponding platform artifact in monorepo .gaijinn/ or operations/, and vice-versa (INV-DUAL-BRIDGE).

## Vault side (this city)
- 40_Concepts/* → ideas, patterns discovered in dogfood
- _multi-agent/events.md → sprint history

## Platform side (monorepo)
- .gaijinn/operations/*.md
- .gaijinn/blueprint.json , graph.json
- hermes-development-loop.py etc.

The memory-execution-loop runs the bridge: vault insights → platform fixes → new vault concepts.

AFK sprawl populates vault side; Hermes cron + composer keep platform side in sync.
