---
id: "CONCEPT-COUNCIL-MEMORY-14W"
type: "Concept"
status: "active"
tags: [Domain/Vault, Sprint]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/council-memory-vault-dogfood-arc]]"
  - "[[40_Concepts/council-memory-convergence-semantics]]"
council_ref: "vault [34–199], [71–139]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# 14-worker sprint arc (distilled)

## Era definition

**When:** 2026-06-17 PM through early 2026-06-18 AM  
**Pattern:** Repeated `grid-spawn --workers 14 --executor deepseek|hermes -m deepseek-v4-flash`  
**Outcome:** High worker completion rate, **low merge success** — convergence stuck 0.55–0.89

## Why 14 workers

OBSIDIAN RUN 16 authorized 16-agent swarm; practical blueprint targeted **14 WUs** across vault slices (governance, concepts, UI JSON, promoter tooling, aoc_supervisor stubs).

## Recurring WU triple (governance sync)

Workers 003/013 repeatedly owned the **atomic governance block**:

| WU | Path | Role |
|----|------|------|
| WU-003 | `.agents/hermes-deepseek.env.example` | Executor env template |
| WU-008 | `20_Projects/deepseek-hermes-setup.md` | Setup + auth docs |
| WU-013 | 9 governance files | AGENTS, CLAUDE, README, ADR-002, events, constitution, orders |

Sprints 7–13 show **re-validation churn** — same WUs re-run while global convergence blocked.

## Other high-traffic WUs (14-worker grid)

| WU | Domain |
|----|--------|
| WU-001 | `project.executor-profile.json` (schema v2→v5) |
| WU-002 | `.cursorrules` wikilink expansion |
| WU-005 | `knowledge-linter.py` v2.0.0 |
| WU-006 | `validate_promotion.py` (+convergence gate) |
| WU-007 | `promote.sh` (--linter gate) |
| WU-009 | 17× `40_Concepts/` high-risk markdown |
| WU-010 | `_multi-agent/events.md` |
| WU-011 | `preflight.py` v1.3.0 + `vault-ui-intent-map.json` |
| WU-012 | `ui/vault-ui-intent-map.json` |
| WU-013 | `ui/WU-004-deploy-path-validation.md` |
| WU-014 | Governance dependency-cycle atomic review |

## Convergence trajectory

| Phase | Score | Cause |
|-------|-------|-------|
| Empty merge | 0.5556 | merged_workers=0 latched |
| Partial | 0.6667 | 14 blocked, 0 merged |
| Near-miss | 0.8889 | validation 1.0, zero-delta copy-mode |
| Production | 1.0 | After merge-compounding + 6-WU manual sprint |

## Lessons → program change

1. **Do not default to 14** — use `recommended_swarm` ([99])
2. **Worker-gate PASS ≠ sprint done** — global linter needs merges
3. **Codex+DeepSeek mismatch** killed first 14-worker cycle — fixed to hermes executor [87]
4. **Stale manifest** blocked layer1 forever until manual cleanup

## Successor sprints

- **6-WU Cursor sprint** → 6/6 merged, 1.0 [82]
- **5-WU DeepSeek sprint** → 5/5 pass, 277s [97–98]
- Stable WU ids + completion ledger ended re-block loop