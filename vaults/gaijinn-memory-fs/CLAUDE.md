---
id: "CLAUDE"
type: "Guidance"
status: "active"
scope: "vault-global"
tags:
  - Guidance
  - Gaijinn
  - Domain/Orchestration
links:
  - "[[AGENTS]]"
  - "[[raw/constitution-v0-section-xiii]]"
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
  - "[[_multi-agent/events]]"
  - "[[10_Operations/tasks/OBSIDIAN-RUN-16]]"
---

<!-- BEGIN GAIJINN INIT -->
# Gaijinn Project Guidance — gaijinn-memory-fs (Obsidian Vault)

**Control chain:** USER (Amir) → Composer 2.5 → Hermes (DeepSeek Flash) → 16× DeepSeek Flash subagents  
**Mission:** Write-time compiled memory vault with joint governance per Section XIII + ADR-002.

## Governance overview

This vault operates under **joint governance**:

| Domain | Law | Enforcement |
|--------|-----|-------------|
| **Vault Law** | Sections III–VIII (semantic integrity) | Knowledge linter, OCC replay, provenance tracking |
| **Gaijinn Execution** | Section XIII + ADR-002 (execution integrity) | GIV allowed paths, validate-worker, governance.json |

Both apply simultaneously. Compliance in one does not excuse violation of the other. See [[AGENTS]] for full agent obligations.

## Workflow commands

```bash
# Compile prompt after changing project.json
gaijinn compile-prompt

# Scan before graph analysis when source files change
gaijinn scan .

# Analyze before creating worker directories
gaijinn analyze

# Run grid with N workers for isolated handoffs
gaijinn run-grid --workers 2

# Validate a worker before promotion
gaijinn validate-worker --worker worker-002

# Read and post to Council (shared thread — no human relay)
gaijinn council say --as cursor "message"
gaijinn council say --as cursor --id worker-002 "message"
```

## Hermes orchestrator usage

```bash
# Interactive council-backed session
gaijinn hermes -i

# One-shot query
gaijinn hermes "your query"
```

## Worker rules (binding)

1. **GIV enforcement:** Only write to files listed under `allowed_paths` in your WORK_UNIT.md. Sibling-owned paths require HANDOFF_ONLY tickets — never edit directly.
2. **Two ledgers:** Log material changes in **both** `_multi-agent/events.md` (vault semantic) and Council `.gaijinn/bridge/council.md` (gaijinn operational).
3. **No force-overwrites:** On merge failure, OCC replay then retry. Never bypass.
4. **Report convergence:** After completing assigned work, post governance.json structural_score to Council.
5. **Run pytest:** All 287 tests must pass before declaring work complete.

## Knowledge linter

Before promoting `/pending/` → `/40_Concepts/`:
1. Run vault knowledge linter (checks orphan links, provenance gaps, broken wikilinks)
2. Run `gaijinn validate-worker` (checks path scope, handoff isolation, test gates)
3. Only promote if both pass

## Convergence thresholds

| Gate | Threshold |
|------|-----------|
| Structural convergence (simulated) | ≥ 0.875 |
| Structural convergence (production) | = 1.0 |
| Vault knowledge linter | clean |
| Gaijinn validate-worker | passed |

## Coordination

- **Vault event ledger:** `_multi-agent/events.md` — semantic changes, ownership
- **Gaijinn Council:** `.gaijinn/bridge/council.md` — operational handoffs, sprint reports
- **Execution ledger:** `.gaijinn/merge/governance.json` — structural_score, binding

Never ask the human to relay messages between agents. Use `gaijinn council say` for all cross-agent communication.

<!-- END GAIJINN INIT -->
