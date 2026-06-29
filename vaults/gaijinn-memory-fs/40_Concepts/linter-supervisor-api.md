---
id: "CONCEPT-LINTER-SUPERVISOR-API"
type: "Concept"
status: "active"
promoted_from: "split:knowledge-linter-architecture"
system_tier: "operations"
tags:
  - Domain/Vault
  - Domain/Linter
  - Supervisor
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[aoc_supervisor/aoc_supervisor/api.py]]"
  - "[[aoc_supervisor/aoc_supervisor/preflight.py]]"
related_concepts:
  - "[[40_Concepts/linter-core-governance]]"
  - "[[40_Concepts/linter-markdown-schema]]"
  - "[[40_Concepts/memory-execution-loop]]"
platform_ref: "aoc_supervisor/aoc_supervisor/"
---

# Linter — Supervisor API (Python boundary)

Python `aoc_supervisor` stubs in the vault dogfood tree. Split from `knowledge-linter-architecture`.

## Scope

- `api.py` — FastAPI gateway import guards, `/internal` routes
- `preflight.py` — project root resolution, `--check` CLI
- `billing.py` — ledger integrity when present
- Syntax + `__all__` export validation on worker completion

## Not in this node

Markdown frontmatter, convergence gates, or vault promotion — see [[40_Concepts/linter-markdown-schema]] and [[40_Concepts/linter-core-governance]].

Parent index: [[40_Concepts/knowledge-linter-architecture]].