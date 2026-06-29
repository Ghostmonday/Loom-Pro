---
id: "CONCEPT-MEMORY-EXECUTION-LOOP"
type: "Concept"
status: "active"
promoted_from: "platform-doctrine"
promoted_by: "worker-002"
promotion_date: "2026-06-17T22:10:00Z"
related_concepts:
  - "[[40_Concepts/ingress-vault-civilization]]"
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/promotion-pipeline]]"
  - "[[40_Concepts/vault-affairs]]"
  - "[[40_Concepts/vault-filesystem]]"
  - "[[40_Concepts/vault-gaijinn]]"
system_tier: "governance"
tags:
  - Domain/Governance
  - Domain/Gaijinn
  - Loop
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/tasks/OBSIDIAN-RUN-16]]"
  - "`aoc_supervisor/aoc_supervisor/api` (monorepo)"
  - "`aoc_supervisor/aoc_supervisor/billing` (monorepo)"
platform_ref: ".gaijinn/operations/MEMORY-EXECUTION-LOOP.md"
---

# Memory ↔ Execution Loop

Obsidian vault **fuel** and Gaijinn platform **capabilities** feed each other. The more we learn, the more action we can take; the more we measure, the more we learn.

## Cycle

1. **Learn** — `[[_multi-agent/events]]`, council, ADR-002, Section XIII constitution
2. **Act** — Gaijinn pipeline (scan → analyze → plan → GUI deploy)
3. **Measure** — `confusion_count`, three promotion gates, `governance.json`, vault linter
4. **Distill** — promote concepts here; platform doctrine in `.gaijinn/operations/`

## WU-009 gravity status

The latest metrics manifest still rejects this concept node:

| Metric | Value |
|--------|-------|
| `gravity` | `0.100` |
| `automatic_rejection` | `true` |
| `in_degree` | `0.0` |
| `out_degree` | `0.0` |
| `shadow_bridge_count` | `0` |

This is an execution-topology problem, not a content provenance problem. The concept is heavily linked in markdown, but the current metrics manifest is not crediting those wikilinks as graph edges. Recovery depends on the scan/analyze layer recognizing backlinks from [[40_Concepts/metrics-dashboard]], [[40_Concepts/dual-ledger-bridge]], [[40_Concepts/vault-gaijinn]], [[40_Concepts/vault-filesystem]], and [[40_Concepts/ingress-vault-civilization]].

## Worker-004 expansion (WU-009, WU-014) — COMPLETE

The supervisor API now feeds a **billing audit trail** into the Measure step:

| New Component | Endpoint | Purpose |
|---------------|----------|---------|
| Billing audit | `POST /api/v1/billing/audit` | Query billing event history |
| Account summary | `GET /api/v1/billing/summary` | Balance + status + recent activity |

These endpoints close the loop: every deployment fee, token issuance, and compute cost is recorded in `.aoc/billing/audit.jsonl` and queryable via the API. The metrics dashboard ([[40_Concepts/metrics-dashboard]]) now sources billing health from these endpoints.

**Validation**: All billing endpoints confirmed operational. aoc_supervisor `__init__.py` created as package entry point. Vault.yaml linter rules expanded with billing-specific checks (lint-billing-audit-completeness, lint-api-billing-endpoints).

## Dual law (non-substitutable)

| Domain | Law | Record |
|--------|-----|--------|
| Vault | Semantic integrity | Event ledger, knowledge linter |
| Gaijinn | Execution integrity | Council, merge governance.json |

See [[raw/constitution-v0-section-xiii]].

## Platform canonical spec

Monorepo: `.gaijinn/operations/MEMORY-EXECUTION-LOOP.md`  
Runner: `scripts/dev/memory-execution-loop.sh`

## GUI entry

Command Bridge only for sprints — not raw CLI grid-spawn. Executor: **DeepSeek V4 Flash**. Platform mirror doctrine: `.gaijinn/operations/GUI-MIRROR-PROMOTION-PIPELINE.md`.
