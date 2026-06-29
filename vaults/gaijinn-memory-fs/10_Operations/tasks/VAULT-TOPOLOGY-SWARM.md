---
id: "TASK-VAULT-TOPOLOGY-SWARM"
type: "Operations"
status: "active"
scope: "vault-optimization"
tags:
  - Operations
  - Swarm
  - Topology
links:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/vault-topology-and-density]]"
  - "[[10_Operations/HERMES-MEMORY]]"
---

# Vault Topology Optimization — Swarm Task

**Goal:** Use the swarm to decide which concept nodes **merge**, which **split**, and which **MOCs** to add — without collapsing council memory into one megathread.

## Prerequisite

```bash
cd /home/ghost-monday/Desktop/Gaijinn
bash scripts/dev/export-vault-gemini-bundle.sh
```

Upload `.gaijinn/exports/gemini-bundle-latest.tar.gz` to Gemini with `GEMINI-REVIEW-PROMPT.md`. Paste Gemini's JSON output into `pending/vault-topology-gemini-review.json`.

## Swarm work units (5 workers)

| WU | Owner focus | Deliverable |
|----|-------------|-------------|
| **WU-TOPO-001** | Merge audit | `pending/topology-merges.md` — pairs from heuristics + Gemini |
| **WU-TOPO-002** | Split audit | `pending/topology-splits.md` — especially metrics-dashboard, vault-gaijinn |
| **WU-TOPO-003** | MOC layer | `000_Brain_MOC.md`, `030_Cold_Memories_MOC.md`, `Current_Context.md` scaffold |
| **WU-TOPO-004** | Frontmatter unify | Patch drift across 54 `.md` files per schema in `.agents/vault.yaml` |
| **WU-TOPO-005** | Edge rewire | Apply merges/splits; `gaijinn scan .`; linter PASS |

## Seed heuristics (verify, do not trust blindly)

### Likely merges (thin or duplicate semantics)

| From | Into | Why |
|------|------|-----|
| `council-memory-convergence-semantics` | `convergence-governance` | Same domain — keep council as `council_ref` appendix or alias |
| `council-memory-cron-topology` | `hermes-cron-orchestration` | Cron doc split across two nodes |
| `vault-sprawl-sprint` | `vault-topology-and-density` | 62-word stub; episodic fact belongs in events |
| `test-promotion-concept` | DELETE or `pending/` | Test artifact not production concept |
| `dual-ledger-bridge` + `event-sourcing-vault` | single `ledger-architecture` | Both describe dual-ledger — review overlap |

### Likely splits (dense / mixed concern)

| Node | Split into |
|------|------------|
| `metrics-dashboard.md` (1499w) | `metrics-convergence`, `metrics-gravity`, `metrics-linter` |
| `vault-gaijinn.md` (772w) | methodology vs dogfood vs cross-vault |
| `obsidian-vault-mapping.md` (517w) | per-vault notes already exist — mapping table only |
| `council-memory-operational-hazards` + `council-memory-infrastructure-incidents` | keep separate OR merge into `council-memory-hazards` with sections — swarm decides |

### Keep separate (do NOT merge)

- `council-memory-index` hub — always index, never absorb children
- `council-memory-empty-spawn-crisis` — episodic blocker, distinct from generic hazards
- `hermes-memory-vault` — concept anchor vs `council-memory-hermes-mandate` (authority vs architecture)

## Acceptance

- [x] Gemini JSON reviewed and work units updated
- [x] Concept count net change documented in `events.md`
- [x] `gaijinn scan .` → graph edges ≥ prior count
- [x] `knowledge-linter.py --check` PASS (convergence 1.0)
- [x] `council-memory-index` updated with any renames
- [x] Council post: merge/split summary

## Executor

```bash
gaijinn grid-spawn --workers 5 --executor hermes -m deepseek-v4-flash
```

Scope: `40_Concepts/`, `pending/`, `000_Brain_MOC.md`, `Current_Context.md` only — no monorepo code.