---
id: "CONCEPT-LINTER-MARKDOWN-SCHEMA"
type: "Concept"
status: "active"
promoted_from: "split:knowledge-linter-architecture"
system_tier: "operations"
tags:
  - Domain/Vault
  - Domain/Linter
  - Markdown
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py|knowledge-linter]]"
  - "[[.agents/vault.yaml]]"
related_concepts:
  - "[[40_Concepts/linter-core-governance]]"
  - "[[40_Concepts/promotion-pipeline]]"
  - "[[40_Concepts/vault-topology-and-density]]"
platform_ref: ".agents/vault.yaml"
---

# Linter — Markdown Schema

Markdown parsing and vault.yaml frontmatter validation. Split from `knowledge-linter-architecture`.

## Checks

- Required base fields: `id`, `type`, `status`, `tags`
- Type-specific schema per `.agents/vault.yaml` (Concept, Decision, Invariant, …)
- Wikilink resolution — no dangling wikilinks to non-existent targets
- Orphan detection — nodes with no in/out graph edges
- `exclude-dirs` for fixtures (e.g. `pending/broken-*.md`)

## Invocation

```bash
python3 10_Operations/knowledge-linter.py --check
python3 10_Operations/knowledge-linter.py --worker-gate
```

Parent index: [[40_Concepts/knowledge-linter-architecture]].