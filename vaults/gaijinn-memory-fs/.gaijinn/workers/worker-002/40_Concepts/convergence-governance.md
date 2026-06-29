---
id: "CONCEPT-CONVERGENCE-GOVERNANCE"
type: "Concept"
status: "active"
promoted_from: "AFK-sprawl-sprint"
system_tier: "governance"
tags:
  - Domain/Vault
  - Domain/Metrics
  - Convergence
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py|knowledge-linter]]"
related_concepts:
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/metrics-convergence]]"
  - "[[40_Concepts/council-memory-convergence-semantics]]"
  - "[[40_Concepts/vault-topology-and-density]]"
  - "[[40_Concepts/linter-core-governance]]"
  - "[[40_Concepts/dual-ledger-bridge]]"
platform_ref: ".gaijinn/merge/governance.json"
---
# Convergence Governance — Merge Success Metric

Convergence = (validation_pass_rate + structural invariants + no blocked/conflicted) normalized. Target >=1.0 for sprint merged gate.

## WU-009 current manifest review

The current metrics manifest records the latest merge governance snapshot under `.gaijinn/metrics_manifest.json > merge_governance.latest` because the canonical `.gaijinn/merge/governance.json` artifact is absent in this checkout.

| Field | Current value | Gate |
|-------|---------------|------|
| `convergence` | `0.6667` | FAIL for production `1.000` |
| `validation_pass_rate` | `1.0` | PASS |
| `merged_workers` | `0` | FAIL: no merged work |
| `blocked_workers` | `14` | FAIL: blocked work remains |
| `handoff_isolation` | `true` | PASS |
| `transaction_bus_synchronized` | `true` | PASS |
| `conflict_free` | `true` | PASS |
| `shadow_bridge_count` | `0` | PASS |

Interpretation: Gaijinn isolation is clean, but production convergence is not. Vault semantic health cannot offset this execution failure under Section XIII and ADR-002.

## In vault
- .gaijinn/merge/governance.json records convergence + validation_pass_rate + invariants map.
- Linter enforces convergence >=1.0 (Section XIII §3).
- After collect/validate-worker/merge-grid --strategy sequential, governance updated by pipeline.
- AFK: when Hermes detects sprint terminal, runs merge; cursor (this) ensures post-merge linter + growth.

## Relation to density
Higher concept count + wikilinks → higher graph density → better structural_score → easier 1.0 convergence on next sprint.

See [[40_Concepts/metrics-dashboard]] for full scorecard and [[40_Concepts/vault-topology-and-density]].
