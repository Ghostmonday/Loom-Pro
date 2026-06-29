---
id: "CONCEPT-COUNCIL-MEMORY-UX"
type: "Concept"
status: "active"
tags: [Domain/UI, Product]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/council-memory-product-vision]]"
  - "[[40_Concepts/council-memory-monorepo-state]]"
linked_operations:
  - "ui/process-stage-ux-map.json"
  - "ui/gaijinn-ui-intent-map.json"
council_ref: "monorepo [91–92]"
---

# UX & process stage (distilled)

## USER control-point table → intent map

**Source:** USER process-stage table (2026-06-18)  
**Artifact:** `ui/process-stage-ux-map.json`  
**Parent:** `ui/gaijinn-ui-intent-map.json` v4  
**Vault overlay:** `ui/vault-ui-intent-map.json`

**Stage rail order:** initialization → planning → analysis → execution → merge

## 12 control points (summary)

| ID | Stage | Control point | Risk |
|----|-------|---------------|------|
| `init.project_configuration` | Init | Project goal + scan params | low |
| `init.phase_scope_selection` | Init | Backend / full-stack presets | low |
| `plan.model_parameter_control` | Plan | Executor + model uniformity | low_medium |
| `plan.blueprint_approval` | Plan | Approve work units | medium |
| `plan.swarm_size_selection` | Plan | Worker count vs blueprint | medium |
| `analysis.graph_review` | Analysis | Layer 1 graph inspection | medium |
| `analysis.inferred_review` | Analysis | Layer 2 lifecycle chains | medium |
| `execution.atomic_deploy` | Execution | grid-spawn atomic sprint | high |
| `execution.worker_monitor` | Execution | Per-worker status | medium |
| `merge.validation_review` | Merge | validate-worker gates | high |
| `merge.sequential_merge` | Merge | merge-grid strategy | high |
| `merge.convergence_gate` | Merge | Production 1.0 threshold | high |

Full field mapping (API, CLI, gaps) lives in the JSON — not duplicated here.

## Defaults by domain

| Surface | Executor | Model |
|---------|----------|-------|
| Vault dogfood | `hermes` | `deepseek-v4-flash` |
| Monorepo dev | `auto` | `grok-composer-2.5-fast` |

## Neural Draft internal UI (not public GTM)

**Council [92]:** Internal-only console for dogfooding blueprint-native UX.

| Piece | Path |
|-------|------|
| Design package | `.gaijinn/design/neural-draft-internal-ui/` |
| Blueprint WUs | `ui/blueprint-ui.json` (12 control points) |
| Static UI | `ui/neural-draft/` (vanilla JS + CSS) |
| Serve route | `/internal` via `aoc_supervisor/api.py` |
| Tests | `tests/test_neural_draft_ui.py` |

**Stack choice:** FastAPI + vanilla JS — performance and blueprint alignment over React churn.

## Daemon waker (scope boundary)

Agent wake operations only — **not** coupled to Tauri/public UI. Separate from Neural Draft internal surface.

## Drives which projects

- **P4** — design-partner demo (5–8 min recorded flow)
- **P5** — blueprint viewer MVP (viz-engine + live `blueprint.json`)