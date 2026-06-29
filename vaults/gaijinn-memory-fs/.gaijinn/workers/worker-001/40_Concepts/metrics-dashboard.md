---
id: "CONCEPT-METRICS-DASHBOARD"
type: "Concept"
status: "active"
promoted_from: "split:metrics-dashboard-index"
system_tier: "governance"
tags: [Metrics, Index, Domain/Governance]
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
related_concepts:
  - "[[40_Concepts/metrics-convergence]]"
  - "[[40_Concepts/metrics-gravity]]"
  - "[[40_Concepts/metrics-linter]]"
  - "[[40_Concepts/convergence-governance]]"
  - "[[40_Concepts/vault-topology-and-density]]"
platform_ref: ".gaijinn/metrics_manifest.json"
---

# Metrics Dashboard — Index

Router only. Split 2026-06-18 (topology swarm). Historical WU-009 snapshot decomposed into atomic nodes.

| Node | Domain |
|------|--------|
| [[40_Concepts/metrics-convergence]] | structural_score, merge invariants, convergence semantics |
| [[40_Concepts/metrics-gravity]] | graph density, gravity floor, rejected-node recovery |
| [[40_Concepts/metrics-linter]] | vault linter gates, billing API health |

## Refresh cadence

After every sprint merge: `gaijinn scan .` → `gaijinn analyze` → `knowledge-linter.py --check`.

## Related governance

- [[30_Decisions/ADR-002-dual-invariant-domains]]
- [[AGENTS.md]]
- [[.gaijinn/merge/governance.json]]