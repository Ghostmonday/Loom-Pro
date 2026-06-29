---
id: "CONCEPT-LINTER-CORE-GOVERNANCE"
type: "Concept"
status: "active"
promoted_from: "split:knowledge-linter-architecture"
system_tier: "operations"
tags:
  - Domain/Vault
  - Domain/Linter
  - Section-XIII
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py|knowledge-linter]]"
related_concepts:
  - "[[40_Concepts/linter-markdown-schema]]"
  - "[[40_Concepts/linter-supervisor-api]]"
  - "[[40_Concepts/convergence-governance]]"
  - "[[40_Concepts/dual-ledger-bridge]]"
platform_ref: "raw/constitution-v0-section-xiii.md"
---

# Linter — Core Governance (Section XIII)

Constitutional and execution-domain checks. Split from `knowledge-linter-architecture`.

## Checks

- Dual-domain invariants (vault semantic + Gaijinn execution — neither offsets the other)
- OCC compliance: no force-overwrites, quarantine replay before re-merge
- GIV allowlist: workers stay in `allowed_paths`
- **Convergence ≥ 1.0** production gate (reads `.gaijinn/merge/governance.json`)
- Simulated threshold 0.875 for dry-run only

## When this layer runs

- Full `knowledge-linter.py --check` (post-merge, pre-promotion)
- `validate-worker` worker-gate mode skips convergence when mid-sprint

Parent index: [[40_Concepts/knowledge-linter-architecture]].