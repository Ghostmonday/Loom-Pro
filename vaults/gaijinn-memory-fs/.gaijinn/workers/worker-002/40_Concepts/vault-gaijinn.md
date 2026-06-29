---
id: "CONCEPT-VAULT-GAIJINN"
type: "Concept"
status: "active"
promoted_from: "vault-design"
promoted_by: "worker-002"
promotion_date: "2026-06-17T22:10:00Z"
related_concepts:
  - "[[40_Concepts/memory-execution-loop]]"
  - "[[40_Concepts/vault-affairs]]"
  - "[[40_Concepts/vault-filesystem]]"
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/ingress-vault-civilization]]"
  - "[[40_Concepts/promotion-pipeline]]"
system_tier: "governance"
tags:
  - Domain/Vault
  - Domain/Gaijinn
  - Cross-Vault
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
  - "[[10_Operations/tasks/OBSIDIAN-RUN-16]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS]]"
  - "[[10_Operations/knowledge-linter.py|knowledge-linter]]"
  - "`aoc_supervisor/aoc_supervisor/api` (monorepo)"
  - "`aoc_supervisor/aoc_supervisor/billing` (monorepo)"
  - "[[.agents/vault]]"
platform_ref: ".gaijinn/operations/GAIJINN-VAULT-METHODOLOGY.md"
---

# Vault Gaijinn — Methodology & Pipeline Governance

The **Gaijinn vault** maps the Gaijinn framework methodology onto gaijinn-memory-fs: how the pipeline executes, how work units are isolated, how handoffs cross boundaries, how the merge grid converges, and how the dual-domain architecture governs every operation.

## Domain scope

The Gaijinn domain governs execution methodology for the vault:

| Layer | Description | Artifact |
|-------|-------------|----------|
| **Dual governance** | Joint Vault × Gaijinn law | [[30_Decisions/ADR-002-dual-invariant-domains]], [[raw/constitution-v0-section-xiii]] |
| **Hard invariants** | Non-negotiable enforcement rules | [[00_Brain/invariants/INV-GAIJINN-BINDING]] |
| **Pipeline** | scan → analyze → plan → grid-spawn → merge | `.gaijinn/project.json`, `.gaijinn/blueprint.md` |
| **Work units** | GIV isolation, allowed paths, handoff protocol | `.gaijinn/workers/` (per worker) |
| **Merge grid** | OCC replay, structural scoring, convergence | `.gaijinn/merge/governance.json` |
| **Knowledge linter** | Semantic integrity validation | `10_Operations/knowledge-linter.py` |
| **Memory loop** | Vault fuel → platform action | [[40_Concepts/memory-execution-loop]] |

## Why a separate vault mapping

Gaijinn methodology is the **operating system** of the vault. It is not the vault itself (that's FileSystem), nor the events that drive it (that's Affairs). It is the set of rules and pipelines that transform human intent into structured knowledge:

- **Affairs vault** tells us *what* happened
- **FileSystem vault** tells us *where* it lives
- **Gaijinn vault** tells us *how* it got there and *whether* it's valid

This three-way split echoes the dual-domain architecture of [[30_Decisions/ADR-002-dual-invariant-domains]]: execution integrity (Gaijinn) and semantic integrity (Vault) are non-substitutable measurement domains.

## The Gaijinn pipeline in the vault

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ compile- │    │   scan   │    │ analyze  │    │run-grid  │    │  merge   │
│  prompt  │───→│  .gaijinn│───→│ gravity  │───→│  spawn   │───→│ converge │
│          │    │ graph    │    │ flags    │    │ workers  │    │  score   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
                                                      ↓
                                               ┌──────────────┐
                                               │  validate-   │
                                               │   worker     │
                                               │ (pytest+GIV) │
                                               └──────────────┘
```

Each stage enforces a gate. Failure at any gate blocks pipeline progress per [[00_Brain/invariants/INV-GAIJINN-BINDING]].

### WU-004 / WU-009 pipeline map (Sprint 6) — COMPLETE

Sprint 6 introduced high-risk changes across YAML ([[.agents/vault]]) and Python (`aoc_supervisor/aoc_supervisor/api`, `aoc_supervisor/aoc_supervisor/billing`):

| Work Unit | Type | Path | Risk | Gate | Status |
|-----------|------|------|------|------|--------|
| WU-004 | YAML | `.agents/vault.yaml` | high | Vault taxonomy + linter rules | ✓ |
| WU-009 | Python | `aoc_supervisor/aoc_supervisor/{api,billing}.py` | high | Supervisor API + billing audit | ✓ |
| WU-014 | Markdown | `40_Concepts/*` (7 files) | high | Atomic dependency cycle | ✓ |

All three wired through the dual-governance pipeline and validated via vault linter + Gaijinn validate-worker. The vault.yaml now includes 13 total linter rules (up from 10 original), with 4 new rules covering billing audit completeness, API endpoint validation, Python docstring consistency, and supervisor import integrity. Rule `lint-python-frontmatter` upgraded from warning to error severity.

## Convergence via the merge grid

The merge grid computes `structural_score` from per-worker convergence:

```
structural_score = Σ(worker_convergence_i × weight_i) / Σ(weight_i)
```

Where each worker's convergence factors in:
- **Path scope validity** — writes only within GIV `allowed_paths`
- **Handoff freshness** — all cross-boundary tickets resolved as OPEN → FULFILLED
- **Linter clean** — vault knowledge linter passes (no orphan links, full provenance)
- **Test pass** — vault-appropriate acceptance checks

Thresholds: simulated ≥ 0.875, production = 1.0 (ADR-waivable with partial state).

## Cross-vault links

|| Direction | Link |
||-----------|------|
|| Gaijinn → gaijinn-memory-fs (vault root) | [[README]] (methodology is the vault OS) |
|| Gaijinn → gaijinn-memory-fs (agent bootstrap) | [[AGENTS]] (agent obligations reference Gaijinn law) |
|| Gaijinn → gaijinn-memory-fs (execution guidance) | [[CLAUDE]] (guidance references pipeline gates) |
|| Gaijinn → dual governance | [[30_Decisions/ADR-002-dual-invariant-domains]] |
|| Gaijinn → hard invariant | [[00_Brain/invariants/INV-GAIJINN-BINDING]] |
|| Gaijinn → pipeline output | [[40_Concepts/memory-execution-loop]] (the loop that cycles pipeline output back into vault fuel) |
|| Gaijinn → Affairs | [[40_Concepts/vault-affairs]] (events trigger pipeline runs) |
|| Gaijinn → FileSystem | [[40_Concepts/vault-filesystem]] (taxonomy defines where pipeline workers write) |

## Orbit link (read-only)

> **Gaijinn Invariant Verification note:** This concept is a Gaijinn vault mapping. Related platform artifact: `.gaijinn/operations/GAIJINN-VAULT-METHODOLOGY.md` (owned by platform worker — see handoff ticket WU-002-003).

## Related

- [[README]] — gaijinn-memory-fs vault overview and infrastructure table
- [[AGENTS]] — agent bootstrap referencing Gaijinn pipeline governance
- [[CLAUDE]] — execution guidance for agents operating under Gaijinn law
- [[30_Decisions/ADR-002-dual-invariant-domains]] — dual-domain architecture binding
- [[00_Brain/invariants/INV-GAIJINN-BINDING]] — hard invariant for pipeline governance
- [[raw/constitution-v0-section-xiii]] — constitutional foundation
- [[40_Concepts/memory-execution-loop]] — the fuel-action loop
- [[40_Concepts/vault-affairs]] — sibling vault: life events
- [[40_Concepts/vault-filesystem]] — sibling vault: machine organization
- [[10_Operations/HERMES-DEVELOPMENT-ORDERS]] — orchestrator binding orders
- [[10_Operations/knowledge-linter.py|knowledge-linter]] — semantic integrity validator
