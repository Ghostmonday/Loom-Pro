---
id: "CONCEPT-VAULT-TOPOLOGY-DENSITY"
type: "Concept"
status: "active"
promoted_from: "merge:vault-concepts-density+wikilink-topology"
system_tier: "governance"
tags:
  - Domain/Vault
  - Domain/Graph
  - Topology
  - Density
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py|knowledge-linter]]"
  - "[[10_Operations/agents/promoter/promote.sh|promote.sh]]"
related_concepts:
  - "[[40_Concepts/obsidian-city-neighborhoods]]"
  - "[[40_Concepts/convergence-governance]]"
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/memory-execution-loop]]"
platform_ref: ".gaijinn/graph.json"
---

# Vault Topology & Density

Merged from `vault-concepts-density` + `wikilink-topology` (Gemini topology review 2026-06-18). One node for graph mechanics and growth rules.

## Parsing mechanics (`gaijinn scan .`)

- Parses wikilinks in **body + frontmatter** (`related_concepts`, `linked_*` arrays).
- Resolves extensionless targets (e.g. `40_Concepts/foo.md` resolves from `40_Concepts/foo`).
- Drops self-referential edges (no gravity inflation).
- Writes edges to `.gaijinn/graph.json` with `kind: wikilink`.

## Density targets

| Metric | Target |
|--------|--------|
| Core concepts in `40_Concepts/` | ≥15 |
| Wikilink edges in graph.json | ≥80 |
| Links per new concept | ≥3 existing nodes |
| Production convergence | 1.0 |

Density drives gravity above hard floor **0.20** — nodes below are rejected for `grid_spawn`.

## Gravity & curvature

- `node gravity = 0.30·in + 0.25·out + 0.30·capability + 0.15·side_effect`
- Hard floor 0.20 — automatic rejection below
- Shadow bridges: negative Ollivier-Ricci curvature (fragile coupling)

## Growth rule

Each new concept must add ≥2 net edges (outgoing + incoming backlinks). Run `gaijinn scan .` then `gaijinn analyze` after every edit batch so `metrics_manifest.json` credits in-degree.

## Manifest desync (fixed)

Prior bug: wikilink targets without `.md` were not resolved to file node IDs, so in-degree read as zero. Scanner now normalizes targets before edge emission.

## AFK sprawl acceptance (episodic → events)

AFK mode grows the city: concepts added, wikilinks wired, governance → 1.0, linter PASS. Targets: ≥15 concepts, ≥80 edges, events + council digest updated. Episodic record in `_multi-agent/events.md` — not a standalone concept stub.