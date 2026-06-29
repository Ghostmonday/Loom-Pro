---
id: "CONCEPT-COUNCIL-MEMORY-DEV-PROGRAM"
type: "Concept"
status: "active"
tags: [Domain/Hermes, Operations]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/council-memory-hermes-mandate]]"
council_ref: "vault [99]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Development program (distilled from [99])

## Projects (priority order)

| ID | Priority | Name | Success signal |
|----|----------|------|----------------|
| P1 | P0 | Hermes Memory Vault | Cold-start without USER relay |
| P2 | P0 | Vault execution hygiene | Honest convergence; no empty-spawn burn |
| P3 | P1 | Monorepo integration commit | Git matches disk; pytest fresh-clone |
| P4 | P1 | Design-partner demo | DEMO-PATH.md + recorded 5–8 min flow |
| P5 | P2 | Blueprint viewer MVP | viz-engine + live blueprint.json |
| P6 | P2 | GTM Phase 1 | USER gates legal/domain/billing |

## Suggested cycles

| Cycle | Focus | Workers |
|-------|-------|---------|
| C1 | Governance reconcile + memory scaffold | 3–5 |
| C2 | Memory distill + cross-vault links | 5 |
| C3 | Monorepo hygiene (if unblocked) | 2–4 |
| C4 | Demo path doc + dry-run | 1–2 |
| C5 | Blueprint viewer | 3–5 |

**Rule:** Do not run 14-worker sprints unless blueprint warrants it. Use `recommended_swarm`.

## When to ping Composer

- validate-worker wrong for vault domain
- merge-grid platform bug (not zero-delta semantics)
- pytest/PYTHONPATH broken on fresh clone
- `gaijinn plan` straddling vault+code paths
- `gaijinn serve` broken when needed

## When NOT to ping Composer

- Grid work you can run
- Council posts, events append, concept promotion