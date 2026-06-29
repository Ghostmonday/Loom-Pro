# Loom C23 — Loom Map Generator Scaffold (LOOM-211 part 2)

**MASTER:** `docs/codex-tasks/loom/MASTER-loom-codex.md`  
**Schemas:** `docs/schemas/teleology-output.schema.json`, `docs/schemas/topology-output.schema.json`  
**Depends on:** C22 (teleology artifact), C07 (gravity fusion — for topology shape)  
**Stack layer:** 3 — Loom contracts generated from layers 1+2

## Objective

Deterministic **`loom_map_generator`** — input teleology + topology → draft map fragments (actions, flow, smoke_scenarios). Not LLM freestyle.

## Hierarchy (enforce)

```
teleology.json (truth) → topology.json (structure) → generator → loom map drafts
```

## MAY edit

- `aoc_supervisor/aoc_supervisor/loom_map_generator.py` (new)
- `tests/fixtures/teleology_pipeline_executor.json`
- `tests/fixtures/topology_pipeline_executor.json` (new)
- `tests/test_loom_map_generator.py` (new)

## MUST NOT edit

- Ship generated maps to `ui/` without test approval (return dict only in v1)
- UI files

## Steps

1. `generate_map_draft(teleology: dict, topology: dict) -> dict` returning:
   - `actions` — one per `required_capabilities` id
   - `flow` — topological order from capability `depends_on`
   - `smoke_scenarios` — one per `success_criteria` (spec_only)
   - `state_machine.transitions` — from teleology `states`
2. Each action includes `algorithm_binding` with `mode: spec_only` + `gap` until C05–C08 wire real entrypoints
3. Test: fixture teleology + topology → assert `actions.prepare` exists, flow order respects deps

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_map_generator.py -q --no-cov
```