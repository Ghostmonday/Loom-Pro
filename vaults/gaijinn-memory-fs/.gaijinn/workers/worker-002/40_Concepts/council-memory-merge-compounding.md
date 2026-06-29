---
id: "CONCEPT-COUNCIL-MEMORY-MERGE-COMPOUNDING"
type: "Concept"
status: "active"
tags: [Domain/Gaijinn, Merge]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/convergence-governance]]"
linked_operations:
  - "Desktop/Gaijinn/.gaijinn/design/merge-compounding/DECISIONS.md"
council_ref: "monorepo [39–45], vault [80]"
---

# Merge compounding (distilled Q1–Q10)

## Problem solved

Re-running sprints re-blocked **zero-delta** workers that already shipped → convergence stuck, wasted compute.

## Locked mechanics

| Mechanism | Rule |
|-----------|------|
| **Stable WU ids** | `WU-{sha256(sorted paths + checks)[:8]}` |
| **completion-ledger.json** | Records first-ship content_hash per WU |
| **already_merged** | Disposition in **merge_grid only** — not collect |
| **content_hash** | Post-weld file contents under allowed_paths |
| **Plan filter** | Vault: emit WUs only for files not in ledger |
| **merge.merged_work** | `(merged+already_merged≥1) OR backlog_pre_sprint==0` |
| **merge.no_blocked** | `already_merged` ≠ blocked |

## Hermes decide tree (post-Codex)

- `backlog==0` → converged
- ledger grew → plan_next_sprint
- else → stuck (council post)

## Shipped by Codex (~386 pytest)

`blueprint.py`, `plan.py`, `merge_grid.py`, `run_grid.py`, `validate_worker.py`, `merge.py`, `workers.py`, `hermes_development_loop.py`

## Dogfood proof

- Ledger backfill: 11 historical merges
- Replay: 11 already_merged → convergence climbed
- Live sprint: 6/6 merged → **1.0** (vault [82])