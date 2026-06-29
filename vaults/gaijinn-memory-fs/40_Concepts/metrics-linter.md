---
id: "CONCEPT-METRICS-LINTER"
type: "Concept"
status: "active"
promoted_from: "split:metrics-dashboard"
system_tier: "operations"
tags: [Metrics, Linter, Billing]
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[aoc_supervisor/aoc_supervisor/api.py]]"
related_concepts:
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/linter-core-governance]]"
  - "[[40_Concepts/linter-markdown-schema]]"
  - "[[40_Concepts/memory-execution-loop]]"
platform_ref: "10_Operations/knowledge-linter.py"
---

# Metrics — Vault Linter & Billing Health

Split from `metrics-dashboard`.

## Vault linter gates

| Check | Target |
|-------|--------|
| Semantic pass | clean |
| Orphan links | 0 |
| Convergence gate | 1.0 production |
| Worker-gate | mid-sprint partial OK |

```bash
python3 10_Operations/knowledge-linter.py --check
```

## Billing health (supervisor API)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/billing/audit` | Query audit trail |
| `GET /api/v1/billing/summary` | Account summary |
| `.aoc/billing/audit.jsonl` | Event log |

Closes the **Measure** step in [[40_Concepts/memory-execution-loop]].

Parent index: [[40_Concepts/metrics-dashboard]]. Linter atoms: [[40_Concepts/linter-core-governance]], [[40_Concepts/linter-markdown-schema]].