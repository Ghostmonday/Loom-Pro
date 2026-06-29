---
id: "MOC-BRAIN-ROUTER"
type: "Concept"
status: "active"
system_tier: "memory"
tags: [MOC, Router, Hermes]
related_concepts:
  - "[[40_Concepts/hermes-memory-vault]]"
  - "[[40_Concepts/council-memory-index]]"
  - "[[Current_Context]]"
linked_operations:
  - "[[10_Operations/HERMES-MEMORY.md]]"
---

# Brain MOC — Hermes memory router

Cold-boot entry. Read in order:

## 1. Swapping memory (session state)

| Node | Purpose |
|------|---------|
| [[Current_Context]] | What Hermes was doing last tick |
| [[40_Concepts/council-memory-index]] | Distilled council by topic |

## 2. Memory layers

| Layer | Location |
|-------|----------|
| Episodic | [[_multi-agent/events.md]] |
| Semantic | [[40_Concepts/hermes-memory-vault]] → `40_Concepts/` |
| Procedural | [[10_Operations/HERMES-MEMORY.md]] |

## 3. Sub-system MOCs

| MOC | Indexes |
|-----|---------|
| [[010_Protocols_MOC]] | AGENTS, constitution, ADR-002, promotion |
| [[020_Active_State_MOC]] | governance.json, loop-state, metrics |
| [[030_Cold_Memories_MOC]] | council-memory cluster, archived sprints |

## 4. Topology maintenance

| Node | Purpose |
|------|---------|
| [[40_Concepts/vault-topology-and-density]] | Merge/split/link rules |
| [[40_Concepts/metrics-dashboard]] | Health index |
| [[10_Operations/tasks/VAULT-TOPOLOGY-SWARM]] | Swarm work orders |