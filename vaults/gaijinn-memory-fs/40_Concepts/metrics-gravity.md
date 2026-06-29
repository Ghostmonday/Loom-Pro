---
id: "CONCEPT-METRICS-GRAVITY"
type: "Concept"
status: "active"
promoted_from: "split:metrics-dashboard"
system_tier: "governance"
tags: [Metrics, Topology, Gravity]
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
related_concepts:
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/vault-topology-and-density]]"
platform_ref: ".gaijinn/metrics_manifest.json"
---

# Metrics — Gravity & Graph Topology

Split from `metrics-dashboard`. Sources: `metrics_manifest.json`, `graph.json`.

## How to refresh

```bash
gaijinn scan .
gaijinn analyze -o .gaijinn/metrics_manifest.json
```

Scanner resolves extensionless wikilinks and frontmatter link arrays to file paths (fixed 2026-06-18).

## Key formulas

| Metric | Rule |
|--------|------|
| Gravity | 0.30·in + 0.25·out + 0.30·capability + 0.15·side_effect |
| Hard floor | 0.20 — automatic rejection below |
| Density target | ≥80 wikilink edges, ≥15 concepts |

## Recovery path for rejected nodes

1. Add inbound wikilinks from high-gravity concepts
2. Reduce side_effect_score on high-risk paths
3. Re-run scan + analyze

Config files (`.yaml`, `.json`, `.py`) may stay rejected — they are not semantic memory nodes.

Parent index: [[40_Concepts/metrics-dashboard]]. Mechanics: [[40_Concepts/vault-topology-and-density]].