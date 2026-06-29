---
id: "CONCEPT-OBSIDIAN-VAULT-MAPPING"
type: "Concept"
status: "active"
promoted_from: "dogfood-sprint-2026-06-18"
system_tier: "governance"
tags:
  - Domain/Vault
  - Domain/Obsidian
  - City-Planning
  - Mapping
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS.md]]"
  - "[[.agents/vault.yaml]]"
related_concepts:
  - "[[40_Concepts/obsidian-city-neighborhoods]]"
  - "[[40_Concepts/vault-gaijinn]]"
  - "[[40_Concepts/vault-filesystem]]"
  - "[[40_Concepts/vault-affairs]]"
  - "[[40_Concepts/dual-ledger-bridge]]"
  - "[[40_Concepts/event-sourcing-vault]]"
  - "[[40_Concepts/memory-execution-loop]]"
platform_ref: "ui/vault-ui-intent-map.json"
obsidian_vault_path: "/home/ghost-monday/Desktop/Gaijinn/vaults/gaijinn-memory-fs"
---
# Obsidian Vault Mapping — gaijinn-memory-fs (canonical)

**Last updated:** 2026-06-18 · Dogfood **COMPLETE** (convergence 1.0, vault linter PASS)

## Open this vault in Obsidian

| Setting | Value |
|---------|-------|
| **Canonical path** | `/home/ghost-monday/Desktop/Gaijinn/vaults/gaijinn-memory-fs` |
| **Obsidian config** | `~/.config/obsidian/obsidian.json` → vault id `eeaac23c89a361ca` |
| **CLI open** | `obsidian "obsidian://open?path=/home/ghost-monday/Desktop/Gaijinn/vaults/gaijinn-memory-fs"` |

**Do not open** `~/Documents/Obsidian/Gaijinn/` for dogfood — that folder contains empty methodology stubs, not the live civilization.

## Three personal vaults vs dogfood vault

| System | Path | Role |
|--------|------|------|
| Affairs | `~/Documents/Obsidian/Affairs/` | User life — notices, calendar |
| FileSystem | `~/Documents/Obsidian/FileSystem/` | Machine organization |
| Gaijinn index | `~/Documents/Obsidian/Gaijinn/` | Methodology quick-ref (stubs only) |
| **Dogfood vault** | `vaults/gaijinn-memory-fs/` | **Live memory + Gaijinn execution** |
| Platform law | `Desktop/Gaijinn/.gaijinn/operations/` | Monorepo doctrine (not Obsidian-owned) |

Cross-link target for LEARN sprint: connect Affairs / FileSystem / Gaijinn index ↔ `gaijinn-memory-fs` via wikilinks in `40_Concepts/vault-affairs`, `vault-filesystem`, `vault-gaijinn`.

## Folder taxonomy (city neighborhoods)

See also [[40_Concepts/obsidian-city-neighborhoods]].

| Neighborhood | Path | Purpose |
|--------------|------|---------|
| Brain | `00_Brain/invariants/` | Hard invariants — council ratification only |
| Operations | `10_Operations/` | Agents, linter, promoter, tasks, Hermes orders |
| Projects | `20_Projects/` | Setup guides (Hermes, Codex) |
| Decisions | `30_Decisions/` | ADRs |
| Downtown | `40_Concepts/` | **18 concepts** (promoted knowledge) |
| Staging | `pending/` | Pre-promotion notes |
| Constitution | `raw/` | Immutable Section XIII |
| Event ledger | `_multi-agent/events.md` | Semantic append-only history |
| Agent config | `.agents/` | `vault.yaml`, executor templates |
| Runtime | `.gaijinn/` | Blueprint, council, merge, metrics |
| Deploy UI | `ui/` | `vault-ui-intent-map.json` |
| Supervisor | `aoc_supervisor/` | API stubs for vault dogfood |

**Promotion path:** `pending/` → `validate_promotion.py` + vault linter → `40_Concepts/`

## Dual ledgers (Section XIII)

| Layer | Artifact | Current state |
|-------|----------|---------------|
| Vault semantic | `_multi-agent/events.md` | Append-only sprint history |
| Gaijinn execution | `.gaijinn/bridge/council.md` | Operational handoffs |
| Merge QA | `.gaijinn/merge/governance.json` | convergence **1.0** |
| Sprint compounding | `.gaijinn/merge/completion-ledger.json` | **17** WU entries |

## Layer 1 graph (scan mirror)

| Metric | Value |
|--------|-------|
| Nodes | 43 |
| Edges | 328 |
| Interaction graph | 23 |
| Markdown notes (excl. workers) | 33 |
| Concepts in `40_Concepts/` | 18 |

## `vault-ui-intent-map.json` bindings

| Binding | Path |
|---------|------|
| Constitution | `raw/constitution-v0-section-xiii.md` |
| ADR | `30_Decisions/ADR-002-dual-invariant-domains.md` |
| Invariant | `00_Brain/invariants/INV-GAIJINN-BINDING.md` |
| Event ledger | `_multi-agent/events.md` |
| Council | `.gaijinn/bridge/council.md` |
| Agent config | `.agents/vault.yaml` |
| Convergence gate | `.gaijinn/merge/governance.json` ≥ 1.0 |
| Completion ledger | `.gaijinn/merge/completion-ledger.json` |

Executor default: `hermes` + `deepseek-v4-flash` per `project.executor-profile.json`.

## Dogfood status (2026-06-18)

- Plan backlog: **0** work units
- Vault linter: **PASS**
- Last merge: 6/6 workers (WU-5117f332 … WU-ec692d62)
- Merge compounding: live (`already_merged` via content_hash)

## Related

- [[README]] — vault entry point
- [[40_Concepts/obsidian-city-neighborhoods]] — neighborhood prose
- [[10_Operations/HERMES-DEVELOPMENT-ORDERS.md]] — orchestrator orders
- [[ui/vault-ui-intent-map.json]] — UI intent bindings
- Monorepo paper: `~/Desktop/GAIJINN-ASSEMBLY-LINE-TECHNICAL-PAPER.md` (rev 1.3)