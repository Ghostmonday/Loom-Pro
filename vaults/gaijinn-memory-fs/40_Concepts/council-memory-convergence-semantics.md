---
id: "CONCEPT-COUNCIL-MEMORY-CONVERGENCE"
type: "Concept"
status: "active"
tags: [Domain/Governance, Metrics]
related_concepts:
  - "[[40_Concepts/convergence-governance]]"
  - "[[40_Concepts/council-memory-index]]"
council_ref: "vault [5–6], monorepo [19–24]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Convergence semantics (distilled)

## Two different scores

| Metric | Meaning |
|--------|---------|
| **validation_pass_rate** | Workers passing all gates |
| **convergence (structural_score)** | Merge eligibility + honest no-op detection |

## Interpreting values

| Score | Meaning |
|-------|---------|
| **1.0** | All fresh deltas merged; production threshold (Section XIII §3) |
| **~0.89** | Often validation 1.0 but copy-mode workers had **no new deltas** — honest block, not failure |
| **0.67–0.78** | Partial merge or many blocked workers |
| **0.55** | Empty merge (`merged_workers=0`) latched in governance |

## Vault linter coupling

Full `knowledge-linter.py --check` **fails** if convergence < 1.0 production. `--worker-gate` can PASS while global fails (expected mid-sprint).

## Governance desync hazard

Hermes re-merge on zero-delta sprint can report 0.6667 while ledger shows 23 completed WUs. **First action:** reconcile governance.json vs completion-ledger.json — do not re-spawn duplicate WUs.

## Simulated threshold

0.875 for dry-run / simulated; 1.0 for production vault promotion.