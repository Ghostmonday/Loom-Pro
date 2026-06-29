---
id: "CONCEPT-COUNCIL-MEMORY-HAZARDS"
type: "Concept"
status: "active"
tags: [Domain/Operations, Checklist]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/council-memory-infrastructure-incidents]]"
  - "[[40_Concepts/council-memory-empty-spawn-crisis]]"
council_ref: "vault [99] §8, [112–139]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Operational hazards (locked checklist)

Hermes boot: scan this list before any spawn. These failures already burned compute.

## Path & environment

| # | Hazard | Correct action |
|---|--------|----------------|
| 1 | Wrong Obsidian vault open | Always `vaults/gaijinn-memory-fs` — not workspace duplicate |
| 2 | Workspace vs Desktop desync | Canonical root: `/home/ghost-monday/Desktop/Gaijinn` |
| 3 | Cron scripts on wrong tree | `~/.hermes/scripts/` must point at Desktop/Gaijinn |
| 4 | `project.json` `project_root` mismatch | Must match Desktop path or plan/spawn desyncs |

## Executor & spawn

| # | Hazard | Correct action |
|---|--------|----------------|
| 5 | `codex exec -m deepseek-v4-flash` | Use `gaijinn grid-spawn --executor hermes -m deepseek-v4-flash` |
| 6 | Workers without `~/.hermes/.env` | `export GAIJINN_OPERATOR=1` + source env before spawn |
| 7 | Mixed models in one sprint | Single model per atomic sprint (blueprint drift) |
| 8 | Spawn when `work_units=[]` | **Pause grid-spawn** — fix plan first ([112–137]) |
| 9 | `composer-autonomy-loop` + Hermes cron | Check PIDs — duplicate spend |

## Planning & merge

| # | Hazard | Correct action |
|---|--------|----------------|
| 10 | Brownfield scan for **new** features | Design Layer 1 changes first, then code ([80]) |
| 11 | Re-merge zero-delta sprint | Check `completion-ledger.json` before re-spawn |
| 11b | ADAPT/Hermes wipes converged ledger | **Archive** `.gaijinn/merge/` first; **never** truncate `completion-ledger.json` when `convergence>=1.0` + `converged_at` set — run `scripts/ops/backfill-completion-ledger.py` to restore |
| 12 | Governance 0.6667 vs ledger 23 | Reconcile governance vs ledger — not duplicate WUs |
| 13 | Vault+code path in single WU | `gaijinn plan` straddle error — vault-only domain split |
| 14 | Stale 14-worker manifest | Clear manifest + worktrees before next layer1 |

## Ledger & linter

| # | Hazard | Correct action |
|---|--------|----------------|
| 15 | council.jsonl line prefixes | Rebuild jsonl from council.md |
| 16 | Root `WORK_UNIT.md` without frontmatter | Fix or remove — linter §6.1 ([132][136]) |
| 17 | Full linter fail mid-sprint | `--worker-gate` expected; global needs convergence 1.0 |

## Converged phase discipline

When `hermes-loop-state.json` → `phase=converged`:

- Do **not** auto-spawn without fresh plan backlog
- ADAPT cron may `[SILENT]` on log truncation only ([90])
- Three gates must PASS before promotion narrative