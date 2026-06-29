---
id: "CONCEPT-COUNCIL-MEMORY-MONOREPO"
type: "Concept"
status: "active"
tags: [Domain/Platform, Integration]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/council-memory-merge-compounding]]"
  - "[[40_Concepts/council-memory-product-vision]]"
council_ref: "monorepo [39–45], vault [80], product [39]"
platform_ref: "/home/ghost-monday/Desktop/Gaijinn"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Monorepo state (distilled snapshot — 2026-06-18)

## Branch & hygiene

| Field | Value |
|-------|-------|
| Active branch | `gaijinn/integration` |
| Uncommitted WIP | ~97–106 tracked files (dogfood + merge-compounding slice) |
| Canonical root | `/home/ghost-monday/Desktop/Gaijinn` only |
| Project P3 | Monorepo integration commit — git must match disk |

## Test surface

| Suite | Status (distill) |
|-------|------------------|
| Merge-compounding slice | ~386 pytest when collection clean |
| Neural Draft UI | `tests/test_neural_draft_ui.py` — 5/5 |
| Fresh-clone gate | P3 blocker until PYTHONPATH + deps wired in CI |

**Note:** Collection errors (e.g. `test_prompt_coverage.py`) are monorepo hygiene — ping `@composer BLOCKED` per development program.

## Major WIP on disk (not yet committed)

### Merge compounding (Codex session)

`aoc-cli/aoc_cli/blueprint.py`, `plan.py`, `merge_grid.py`, `run_grid.py`, `validate_worker.py`, helpers: `merge.py`, `workers.py`, `hermes_spawn.py`, `hermes_development_loop.py`, `knowledge_linter.py`, `vault_deploy.py`, `vault_links.py`, `promote.py`

### UI / internal surfaces

- `ui/process-stage-ux-map.json` — 12 USER control points
- `ui/neural-draft/` — internal console at `/internal`
- `ui/blueprint-ui.json` — 12 WUs for Neural Draft

### Design packages

- `.gaijinn/design/merge-compounding/DECISIONS.md`
- `.gaijinn/design/neural-draft-internal-ui/`

## Hermes vs monorepo ownership

| Domain | Owner |
|--------|-------|
| Vault dogfood | Hermes (primary) |
| `aoc-cli` / platform bugs | Composer when `@composer BLOCKED` |
| Public GTM | USER gates (P6) |

## Convergence on monorepo

Monorepo dogfood hit **0.8889** honest no-op detection (Phase 2 complete). Vault converged **1.0** separately. Do not conflate the two governance files.