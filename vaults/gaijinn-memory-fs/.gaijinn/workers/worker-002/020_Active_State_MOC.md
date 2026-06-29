---
id: "MOC-ACTIVE-STATE"
type: "Concept"
status: "active"
tags: [MOC, Operations]
related_concepts:
  - "[[000_Brain_MOC]]"
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/hermes-cron-orchestration]]"
platform_ref: ".gaijinn/hermes-loop-state.json"
---

# Active State MOC

Live execution state — read every cron tick.

| Artifact | Field |
|----------|-------|
| [[.gaijinn/hermes-loop-state.json]] | phase, convergence, blockers |
| [[.gaijinn/merge/governance.json]] | structural_score |
| [[.gaijinn/metrics_manifest.json]] | gravity, rejected nodes |
| [[.gaijinn/bridge/council.md]] | operational handoffs |
| [[_multi-agent/events.md]] | episodic ledger |
| [[40_Concepts/metrics-dashboard]] | health index |
| [[10_Operations/HERMES-DEVELOPMENT-ORDERS.md]] | binding orders |