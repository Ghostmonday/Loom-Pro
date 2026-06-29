---
id: "CONCEPT-METRICS-CONVERGENCE"
type: "Concept"
status: "active"
promoted_from: "split:metrics-dashboard"
system_tier: "governance"
tags: [Metrics, Convergence, Domain/Governance]
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[.gaijinn/merge/governance.json]]"
related_concepts:
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/convergence-governance]]"
  - "[[40_Concepts/metrics-linter]]"
platform_ref: ".gaijinn/merge/governance.json"
---

# Metrics — Convergence (Gaijinn execution health)

Split from `metrics-dashboard`. Sources: `governance.json`, ADR-002.

## Current snapshot (post-topology sprint)

| Metric | Value | Threshold | Pass? |
|--------|-------|-----------|-------|
| Convergence | **1.0** | = 1.0 (prod) | ✓ |
| Validation pass rate | **1.0** | 1.0 | ✓ |
| Blocked workers | **0** | 0 | ✓ |
| Handoff isolation | true | true | ✓ |
| Transaction bus sync | true | true | ✓ |

## Score interpretation

| Score | Meaning |
|-------|---------|
| **1.0** | All fresh deltas merged |
| **~0.89** | Validation 1.0, zero-delta copy-mode — honest block |
| **0.67** | Partial merge / blocked workers |
| **0.55** | Empty merge latched |

## Invariants (merge.*)

All nine merge invariants must pass for production. See [[40_Concepts/convergence-governance]] for semantics; council distill: [[40_Concepts/council-memory-convergence-semantics]].

Parent index: [[40_Concepts/metrics-dashboard]].