---
id: "CONCEPT-KNOWLEDGE-LINTER-ARCHITECTURE"
type: "Concept"
status: "active"
promoted_from: "AFK-sprawl-sprint"
system_tier: "operations"
tags:
  - Domain/Vault
  - Domain/Linter
  - Index
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py|knowledge-linter]]"
related_concepts:
  - "[[40_Concepts/linter-core-governance]]"
  - "[[40_Concepts/linter-markdown-schema]]"
  - "[[40_Concepts/linter-supervisor-api]]"
  - "[[40_Concepts/promotion-pipeline]]"
  - "[[40_Concepts/vault-topology-and-density]]"
platform_ref: ".gaijinn/operations/KNOWLEDGE-LINTER.md"
---

# Knowledge Linter Architecture — Index

Router only. Atomic linter domains split 2026-06-18 (Gemini topology review).

| Node | Domain |
|------|--------|
| [[40_Concepts/linter-core-governance]] | Section XIII, OCC, GIV, convergence gate |
| [[40_Concepts/linter-markdown-schema]] | Frontmatter, vault.yaml, orphans, wikilinks |
| [[40_Concepts/linter-supervisor-api]] | `aoc_supervisor` Python boundary |

`knowledge-linter.py` implements all three layers. Linter PASS required for promotion and sprint merge.