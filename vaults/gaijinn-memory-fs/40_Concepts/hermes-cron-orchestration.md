---
id: "CONCEPT-HERMES-CRON-ORCHESTRATION"
type: "Concept"
status: "active"
promoted_from: "AFK-sprawl-sprint"
system_tier: "operations"
tags:
  - Domain/Vault
  - Domain/Hermes
  - Automation
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS.md]]"
related_concepts:
  - "[[40_Concepts/memory-execution-loop]]"
  - "[[40_Concepts/dual-ledger-bridge]]"
  - "[[40_Concepts/convergence-governance]]"
  - "[[40_Concepts/event-sourcing-vault]]"
platform_ref: ".gaijinn/hermes-loop-state.json"
---
# Hermes Cron Orchestration — 15min Dev Loop

Hermes (via hermes-development-loop.py + cron */15) complements AFK mode:

1. Read council + hermes-loop-state.json
2. If sprint terminal → collect + validate-worker + merge-grid --strategy sequential
3. Run vault linter (with --exclude-dirs pending)
4. If clean after merge → reset stale workers/manifest → new run-grid + grid-spawn cycle
5. Post to council (ACTION:loop|health|sprint.status)

AFK cursor (grok) runs in parallel: grid-spawn, grow concepts, fix linter/merge blocks, post AFK: notes.

Do not fight the cron; the two agents keep the city sprawling + green.
