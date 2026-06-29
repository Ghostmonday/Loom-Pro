---
id: "CONCEPT-OBSIDIAN-CITY-NEIGHBORHOODS"
type: "Concept"
status: "active"
promoted_from: "AFK-sprawl-sprint"
system_tier: "governance"
tags:
  - Domain/Vault
  - Domain/Obsidian
  - City-Planning
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS.md]]"
  - "[[10_Operations/knowledge-linter.py|knowledge-linter]]"
related_concepts:
  - "[[40_Concepts/obsidian-vault-mapping]]"
  - "[[40_Concepts/vault-topology-and-density]]"
  - "[[40_Concepts/vault-filesystem]]"
  - "[[40_Concepts/vault-affairs]]"
  - "[[40_Concepts/event-sourcing-vault]]"
platform_ref: ".gaijinn/operations/OBSIDIAN-NEIGHBORHOODS.md"
---
# Obsidian City Neighborhoods — Folder Taxonomy & Cross-Links

gaijinn-memory-fs organizes as a living city:

- 00_Brain/invariants/ — core rules that never change
- 10_Operations/ — agents, linter, promoter, tasks, orders
- 20_Projects/ — deepseek-hermes-setup etc.
- 30_Decisions/ — ADRs
- 40_Concepts/ — the dense, cross-linked downtown (18 concepts; see [[40_Concepts/obsidian-vault-mapping]])
- _multi-agent/events.md — append-only ledger
- pending/ — staging for promotion
- raw/ — source constitution
- ui/ — vault-ui-intent-map.json

Neighborhoods are linked via wikilinks in frontmatter (related_concepts, linked_*) and body prose. Graph edges from scan turn links into traversable streets.

New neighborhoods added during AFK sprints increase connectivity, raising node gravity and enabling green governance.
