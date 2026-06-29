# Codex Slice 4 — Intent Blueprint & Inference Pipelines

**Status:** ✅ Complete — report: `.gaijinn/codex/slice-04-report.md`

**Objective:** Complete intent→blueprint compiler path. Extend gold fixtures. Add missing tests for semantic_moat and analyze→inferred.json end-to-end.

## Context

This is Slice 4 of the Codex Full-Codebase Pass. The intent→blueprint pipeline is:
```
User prompt → intent_scan (Layer 1 nodes) → inferring (Layer 2 reflective)
→ blueprint_compiler (inferred.json) → intent_blueprint (STREAM_SPECS → work units)
```

Cursor already pre-wired STREAM_SPECS for editor/Rust/Go/dark-ui. Your job: validate, extend, and test.

## Files you MAY edit

- `tests/test_intent_blueprint.py` — add tic-tac-toe gold fixture
- `tests/test_inferring.py` — add edge-case tests if gaps found
- `tests/test_dataflow.py` — add edge-case tests
- `tests/test_blueprint_compiler.py` — add analyze→inferred.json end-to-end test
- Create `tests/test_semantic_moat.py` — NEW file for semantic_moat coverage
- `aoc-cli/aoc_cli/semantic_moat.py` — only if bugs found (unlikely)
- `aoc-cli/aoc_cli/intent_blueprint.py` — STREAM_SPECS review only
- `aoc-cli/aoc_cli/blueprint_compiler.py` — only if bugs found

## What to do

### 1. Add tic-tac-toe + CLI + unit tests gold fixture to test_intent_blueprint.py

Add to `tests/test_intent_blueprint.py`:
- A `TIC_TAC_TOE_INTENT` string: `"Build a tic-tac-toe game with a CLI interface and unit tests."`
- A test `test_tictactoe_decomposition()` that verifies `detect_intent_streams()` returns `game_logic`, `cli`, and `tests` streams
- A test `test_tictactoe_blueprint()` that verifies `build_intent_blueprint()` produces work units for game, cli, and tests, with correct paths `src/game/`, `src/cli/`, `tests/`

### 2. Add analyze→inferred.json end-to-end test to test_blueprint_compiler.py

Add a test that simulates the full pipeline:
- Create realistic interaction_graph with 3+ nodes (create→activate→trigger pattern)
- Create a mock `reflective_meta` dict matching the inferring output format
- Call `compile_inferred_json()` with both output_path and without
- Verify: schema_version, layer=2, workflows list, disconnected_gaps, shadowbridges, layer0 domains

### 3. Create tests/test_semantic_moat.py — full coverage for semantic_moat

Create a new test file covering:
- `enrich_intent_semantics()` adds `semantic` key to each node
- Domain classification: security tokens → "security" domain, billing tokens → "payments" domain, grid/orchestration tokens → "orchestration" domain
- Impact inference: DELETE method → "destructive", GET → "read_only", POST/PUT/PATCH → "mutating"
- Scope detection: nodes with context_params → "org_scoped", without → "public"
- Edge cases: empty graph returns empty list, missing fields don't crash, node with dataflow puncture → "puncture_risk"
- _keyword_matches: stem keywords match partial, short tokens don't leak through substrings

### 4. Review STREAM_SPECS completeness

The following streams already exist: foundation, storage, indexing, search, desktop_ui, transcript, privacy, api, game_logic, cli, editor_core, rust_core, go_bridge, editor_ui, tests.

Verify these cover the three gold prompts:
- PKM intent → indexing, search, desktop_ui, transcript, privacy ✓ (already tested)
- Tic-tac-toe skill → game_logic, cli, tests
- Editor intent → editor_core, rust_core, go_bridge, editor_ui, tests

No changes needed unless a keyword is clearly missing — but don't add anything speculative.

## Notes

- Cursor is FROZEN on aoc-cli/ and aoc_supervisor/ — DO NOT edit those unless fixing a clear bug
- Small focused diffs only — no drive-by refactors
- Do NOT re-implement what's already shipped
- Gold prompts are for test fixtures only, not production code

## Acceptance

```bash
pytest tests/test_intent_blueprint.py tests/test_inferring.py tests/test_dataflow.py tests/test_blueprint_compiler.py tests/test_semantic_moat.py -q
```
