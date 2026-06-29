# Loom C22 — Teleology Artifact Emitter (LOOM-211 part 1)

**MASTER:** `docs/codex-tasks/loom/MASTER-loom-codex.md`  
**Schema:** `docs/schemas/teleology-output.schema.json`  
**Depends on:** C03 (adaptive ingest), C02 (handoff mirror)  
**Stack layer:** 1 — Teleology truth (before curvature, before Loom map generation)

## Objective

Emit canonical **`teleology.json`** when forge handoff confirms. Teleology is source of truth; Loom JSON maps express it later.

## MAY edit

- `aoc_supervisor/aoc_supervisor/teleology_artifact.py` (new)
- `aoc_supervisor/aoc_supervisor/intent_forge_service.py` (handoff.confirm hook only)
- `aoc_supervisor/aoc_supervisor/blueprint_compiler.py` (write artifact alongside executable_projection)
- `tests/fixtures/teleology_pipeline_executor.json` (new — minimal valid fixture)
- `tests/test_teleology_artifact.py` (new)

## MUST NOT edit

- `ui/loom-*.json` (generator comes in C23)
- `loom_map_generator.py` (C23)

## Steps

1. Add `build_teleology_artifact(session) -> dict` mapping forge evidence to schema fields:
   - `goal`, `constraints`, `success_criteria`, `domains`, `required_capabilities`, `invariants`, `states`
2. On `handoff.confirm`, write `.gaijinn/sessions/{id}/teleology.json`
3. Validate output against `docs/schemas/teleology-output.schema.json` (jsonschema or manual required-key test)
4. `required_capabilities` ids must be dot-namespaced (`prepare`, `spawn`, `merge` style)

## Verify

```bash
.venv/bin/python -m pytest tests/test_teleology_artifact.py -q --no-cov
```

## Postconditions

- Handoff confirm creates `teleology.json` next to session artifact
- Fixture validates against schema
- No Loom map files modified