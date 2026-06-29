---
id: "CONCEPT-PROMOTION-PIPELINE"
type: "Concept"
status: "active"
promoted_from: "AFK-sprawl-sprint"
system_tier: "operations"
tags:
  - Domain/Vault
  - Domain/Promotion
  - Governance
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/agents/promoter/promote.sh|promote.sh]]"
  - "[[10_Operations/agents/promoter/validate_promotion.py|validate_promotion]]"
  - "[[10_Operations/knowledge-linter.py|knowledge-linter]]"
related_concepts:
  - "[[40_Concepts/hermes-memory-vault]]"
  - "[[40_Concepts/vault-topology-and-density]]"
  - "[[40_Concepts/vault-gaijinn]]"
  - "[[40_Concepts/obsidian-city-neighborhoods]]"
  - "[[40_Concepts/event-sourcing-vault]]"
platform_ref: ".gaijinn/operations/PROMOTION-PIPELINE.md"
---
# Promotion Pipeline — Ingress to 40_Concepts/

The promotion pipeline is the **gatekeeper for Hermes semantic memory** — it moves draft content from `pending/` through validation gates into `40_Concepts/`. See [[40_Concepts/hermes-memory-vault]] for the three-layer memory model.

## Gates (enforced by promote.sh + validate_promotion.py)
1. YAML frontmatter: id, type=Concept, status, promoted_from, tags, linked_* arrays, related_concepts.
2. Wikilinks resolve: every link target must exist in vault (no orphans).
3. OCC compliance: provenance (linked_decisions, linked_invariants, linked_operations) verifiable; no stale quarantine.
4. Vault linter pre/post gate: --check must pass or promotion rejected.
5. Dual domain: vault-semantic + gaijinn-execution violations = 0 for promotion.

## AFK usage
During sprawl sprints, new concepts written to pending/ then `./10_Operations/agents/promoter/promote.sh --file pending/foo.md` or batch.

See also [[40_Concepts/linter-markdown-schema]], [[40_Concepts/knowledge-linter-architecture]], and [[40_Concepts/dual-ledger-bridge]].
