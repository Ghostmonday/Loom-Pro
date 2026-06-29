---
id: "OBSIDIAN-RUN-16"
type: "Task"
status: "active"
scope: "vault-tasks"
assigned_to: "hermes"
tags:
  - Task
  - Sprint
links:
  - "[[AGENTS]]"
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS]]"
  - "[[_multi-agent/events]]"
---
# OBSIDIAN RUN — 16-agent sprint

**Control chain:** USER → Composer 2.5 → Hermes (DeepSeek Flash) → 16× DeepSeek Flash subagents

**Mission:** Write-time compiled memory vault per Section XIII + ADR-002.

## Deliverables (this sprint)

1. **Folder taxonomy** — `00_Brain/`, `10_Operations/`, `20_Projects/`, `30_Decisions/`, `40_Concepts/`, `pending/`
2. **YAML frontmatter** on all concept notes
3. **Wikilinks** between constitution, ADR-002, invariants, events
4. **Event ledger** entries in `_multi-agent/events.md`
5. **Knowledge linter** stub under `10_Operations/` (vault law checks)

## Orchestrator (Hermes) duties

- Assign WU-001..WU-011 across 16 workers per manifest
- Enforce GIV allowed_paths per worker
- Post handoffs to `.gaijinn/bridge/council.md`
- Run merge after all workers terminal; report `governance.json` convergence

## WU-014 acceptance status

`worker-014` owns the dependency-cycle atomic block for nine governance paths under `SCOPE_STRICT`, `NO_SIBLING_TRESPASS`, and `HANDOFF_ONLY`.

Metrics manifest review (`.gaijinn/metrics_manifest.json`):

- Shadow Bridges: `0`
- Rejected nodes: `13`
- Latest production convergence: `0.6667`
- Validation pass rate: `1.0`
- Blocked workers: `14`
- Merged workers: `0`
- Conflict state: `conflict_free=true`, `conflicted_workers=0`

Vault linter status:

- `python 10_Operations/knowledge-linter.py --check` failed because production convergence is `0.667`, below the Section XIII production threshold of `1.0`.
- `python 10_Operations/knowledge-linter.py --worker-gate --check` passed.
- `gaijinn validate-worker worker-014` could not run because `.gaijinn/merge/collected.json` is missing; Gaijinn requested `gaijinn collect` first.

## User intent (binding)

Build an Obsidian vault civilization with write-time compiled memory. Joint governance: vault law + Gaijinn execution law.

## Platform doctrine (not vault-owned)

GUI mirror + promotion pipeline: monorepo `.gaijinn/operations/GUI-MIRROR-PROMOTION-PIPELINE.md`
