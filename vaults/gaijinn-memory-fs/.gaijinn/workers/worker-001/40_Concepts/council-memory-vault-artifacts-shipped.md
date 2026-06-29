---
id: "CONCEPT-COUNCIL-MEMORY-SHIPPED"
type: "Concept"
status: "active"
tags: [Domain/Vault, Artifacts]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/council-memory-sprint-14w-arc]]"
  - "[[40_Concepts/council-memory-vault-dogfood-arc]]"
council_ref: "vault [34–82], events.md"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Vault artifacts shipped (distilled)

What actually landed in `gaijinn-memory-fs` — not aspirational backlog.

## Governance & binding

| Artifact | Shipped by | Notes |
|----------|------------|-------|
| `AGENTS.md`, `CLAUDE.md`, `README.md` | WU-013 cycles | Sprint state synced |
| `00_Brain/invariants/INV-GAIJINN-BINDING.md` | WU-013 | Immutable constitution link |
| `30_Decisions/ADR-002-dual-invariant-domains.md` | WU-013 | Rejected nodes reconciled |
| `raw/constitution-v0-section-xiii.md` | Seeded | Linter §3 convergence rule |
| `_multi-agent/events.md` | WU-010, TX-HT resolves | 60+ episodic rows |

## Executor & agent config

| Artifact | Shipped by |
|----------|------------|
| `.agents/hermes-deepseek.env.example` | WU-003 (dual-auth, cron section) |
| `.agents/vault.yaml` | WU-004 era — 14 linter rules |
| `.agents/codex-deepseek.toml.example` | Scaffold |
| `project.executor-profile.json` | WU-001 schema v5 |
| `20_Projects/deepseek-hermes-setup.md` | WU-008 |
| `20_Projects/deepseek-codex-setup.md` | Prior sprint |

## Promotion pipeline

| Artifact | Shipped by |
|----------|------------|
| `10_Operations/agents/promoter/promote.sh` | WU-007 (--linter gate) |
| `10_Operations/agents/promoter/validate_promotion.py` | WU-006 (+4 checks) |
| `10_Operations/knowledge-linter.py` | WU-005 v2.0.0, 16 checks |

## Concepts cluster (40_Concepts/)

**17+ concepts** after AFK sprawl [events 32–42], including:

- `convergence-governance`, `dual-ledger-bridge`, `event-sourcing-vault`
- `hermes-cron-orchestration`, `memory-execution-loop`, `vault-topology-and-density`
- `obsidian-vault-mapping`, `promotion-pipeline`, `linter-core-governance`
- **Council memory cluster** (18 nodes via `council-memory-index`)

WU-009 validated all high-risk concept frontmatter.

## UI & intent maps

| Artifact | Shipped by |
|----------|------------|
| `ui/vault-ui-intent-map.json` | WU-011/012 schema v5 |
| `ui/WU-004-deploy-path-validation.md` | WU-004 deploy path proof |
| `.gaijinn/blueprint.json`, `giv.json`, `graph.json` | scan/analyze cycles |

## Platform stubs (vault-owned aoc_supervisor)

| Artifact | Shipped by |
|----------|------------|
| `aoc_supervisor/__init__.py` | WU-010 graceful imports |
| `aoc_supervisor/api.py` | Import guards |
| `aoc_supervisor/preflight.py` | WU-011 v1.3.0 |

## Merge / governance JSON

| Artifact | When |
|----------|------|
| `.gaijinn/merge/governance.json` | C1-boot [107] — was absent |
| `.gaijinn/merge/completion-ledger.json` | Merge-compounding + backfill |
| `.gaijinn/hermes-loop-state.json` | phase=converged @ 1.0 |

## Stable-id sprint merges (6/6)

Events [63]: `WU-5117f332`, `WU-82c99d2b`, `WU-90ed6cbb`, `WU-d50925f6`, `WU-eacc7320`, `WU-ec692d62` — convergence 1.0, linter PASS.

## Hermes memory scaffold (C1)

| Artifact | Purpose |
|----------|---------|
| `10_Operations/HERMES-MEMORY.md` | Boot manual |
| `40_Concepts/hermes-memory-vault.md` | Concept anchor |
| `40_Concepts/council-memory-*.md` | Distilled council nodes |

## Not shipped (blockers)

- Automatic plan for vault-only WUs (straddle bug)
- Root `WORK_UNIT.md` frontmatter fix (outside worker allowlists)
- Monorepo git commit of platform WIP (P3)