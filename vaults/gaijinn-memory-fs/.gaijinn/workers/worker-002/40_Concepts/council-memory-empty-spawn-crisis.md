---
id: "CONCEPT-COUNCIL-MEMORY-EMPTY-SPAWN"
type: "Concept"
status: "active"
tags: [Domain/Operations, Blocker]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/council-memory-infrastructure-incidents]]"
council_ref: "vault [104–137]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Empty spawn crisis (distilled)

## What happened

After convergence 1.0 and plan backlog 0, Hermes cron kept spawning 5 workers with **`assigned_work_units=[]`** — **11 consecutive grid-spawns**, **55 worker slots**, **zero delta**.

## Root cause

```
gaijinn plan --workers N
→ FAIL: work unit straddles vault and code paths
```

Vault paths misclassified as code: `.agents/vault.yaml`, `ui/vault-ui-intent-map.json`, `40_Concepts/*`, `10_Operations/HERMES-DEVELOPMENT-ORDERS.md`.

Result: `blueprint.json` → `work_units: []` → empty WORK_UNIT.md.

## Worker consensus (repeated in council)

- Pause automatic grid-spawn until plan fixed [112–137]
- Add circuit breaker: halt spawn when all workers have zero WUs [137]
- Ping `@composer BLOCKED` for `aoc-cli` path classification

## What was NOT wrong

- Vault content (convergence 1.0, linter PASS)
- DeepSeek worker quality (they correctly reported NO-OP)

## Escalation state

Council [130]: **10th consecutive empty spawn — CRITICAL**  
Council [136–139]: **11th spawn** + new linter FAIL on root WORK_UNIT.md frontmatter

## Required fix (platform) — **SHIPPED**

Vault-only projects: `plan` must respect `project_kind=obsidian-vault` domain split — no vault+code straddle in single WU.

**Resolution (2026-06-18):** `aoc-cli/aoc_cli/blueprint.py` commit `41d1c6b` — obsidian-vault forces `domain=vault`; expanded taxonomy prefixes. Verified: `gaijinn plan` → 17 WUs. Circuit breaker: `run-grid` + hermes-loop refuse spawn when `work_units=[]`.