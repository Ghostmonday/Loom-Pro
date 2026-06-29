---
id: "CONCEPT-COUNCIL-MEMORY-HANDOFF-BUS"
type: "Concept"
status: "active"
tags: [Domain/Governance, Handoff]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/dual-ledger-bridge]]"
  - "[[40_Concepts/event-sourcing-vault]]"
council_ref: "vault [50–54], [521–529]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Handoff bus (distilled — TX-HT tickets)

## What it is

When a worker completes a WU but **cannot write** to a sibling-owned path (GIV allowlist), merge-governance raises a **handoff transaction** on council. The owning worker resolves it and posts a receipt.

## Message shapes

| Tag | Meaning |
|-----|---------|
| `[HANDOFF_TRANSACTION_ALERT]` | Ticket raised — lists target WU + required edit |
| `[HANDOFF_TRANSACTION_RECEIPT]` | Ticket resolved — names resolver + path |

Ticket id format: `TX-HT-{6hex}` (e.g. `TX-HT-5DE6B3`).

## Proven examples (vault council)

### TX-HT-5DE6B3 → WU-014

- **Alert [50]:** worker-005 completed WU-005 but `_multi-agent/events.md` is owned by WU-014
- **Required:** Append WU-005 completion row to events ledger
- **Receipt [54]:** worker-014 resolved for `WU-014`

### TX-HT-0B7173 → WU-0f079424

- **Alert [521]:** events append needed after stable-id sprint merge
- **Receipt [529]:** worker-001 resolved for `WU-0f079424`

## Rules

1. **Zero handoff tickets** is the default success signal in worker completion posts
2. If alert raised → **do not merge** until receipt or explicit orchestrator collect
3. Episodic truth lives in `_multi-agent/events.md`; council carries the **operational** alert/receipt pair
4. Worker posts `HANDOFF — worker-NNN requested …` when they cannot self-resolve (see events [48])

## When to use vs council say

| Situation | Channel |
|-----------|---------|
| Cross-worker file dependency | TX-HT on council + events append on resolve |
| Sprint status / BLOCKED | `gaijinn council say` |
| Concept promotion | events.md + optional council digest |