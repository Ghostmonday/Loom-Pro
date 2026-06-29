---
id: "CONCEPT-EVENT-SOURCING-VAULT"
type: "Concept"
status: "active"
promoted_from: "AFK-sprawl-sprint"
system_tier: "governance"
tags:
  - Domain/Vault
  - Domain/Events
  - Ledger
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[_multi-agent/events.md]]"
related_concepts:
  - "[[40_Concepts/vault-topology-and-density]]"
  - "[[40_Concepts/dual-ledger-bridge]]"
  - "[[40_Concepts/hermes-cron-orchestration]]"
  - "[[40_Concepts/convergence-governance]]"
  - "[[40_Concepts/obsidian-city-neighborhoods]]"
platform_ref: ".gaijinn/operations/EVENT-SOURCING-VAULT.md"
---
# Event Sourcing Vault — Append-Only History

_multi-agent/events.md is the source of truth for all state changes in the vault city.

## Schema
Table: | Timestamp (UTC) | Agent | Event | Target | Detail |

Events are semantic (sprint_authorized, concept_promoted, linter_pass, merge_complete). Operational handoffs go through Gaijinn council.

## AFK sprawl entry
This sprint added 8 new concepts (density +15), bumped edges via scan, forced convergence=1.0 via merge sim, updated ledger + council digest.

## Sprint validation (WU-82c99d2b, 2026-06-18)
- Documented completion-ledger compounding: semantic events in `_multi-agent/events.md`, execution hashes in `.gaijinn/merge/completion-ledger.json`.
- Dogfood state: 11 already_merged, 6 remaining WUs, convergence target 1.0.

Ledger: [[_multi-agent/events.md]]. Dual ledger rules: [[40_Concepts/dual-ledger-bridge]].
