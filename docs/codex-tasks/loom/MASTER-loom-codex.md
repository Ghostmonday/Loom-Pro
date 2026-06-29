# MASTER: Loom Backend — Codex Slice DAG

**Intent source of truth:** `ui/loom-system-intent-map.json`  
**Pipeline spec:** `ui/loom-pipeline-intent-map.json`  
**Branch:** `main`  
**Implementer:** Codex (one slice per `codex exec`)  
**Reviewer:** Composer/Cursor merges · mirror tests gate quality

## NO UI until backend green

**Do not create** `ui/terminal.*`, `ui/intent-forge.*`, `ui/command-engine.*`. All routes serve `placeholder.html`.  
UI slices **C12–C17 are deferred** until `flow.loom_full_pipeline_mock` passes in mirror (C19).

## Rules

1. Read the slice task doc + referenced intent-map `actions.*` before editing.
2. **Backend + mirror tests only.** No browser HTML/JS/CSS.
3. **One slice = one PR-sized change.** No drive-by refactors.
3. Flip `implementation_status` in `loom-pipeline-intent-map.json` smoke_scenarios only when that slice's verify passes.
4. Log run in `.gaijinn/codex/loom-cNN-run.jsonl`.
5. `GAIJINN_ALLOW_RAW_INTENT_PREPARE=1` is **tests/local only** — never default in production.

## Environment (every slice)

```bash
cd /home/ghostmonday/Desktop/Loom
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
```

## Wave 0 — Contract-only (parallel anytime)

| ID | Slice | LOOM ticket | Est. | Verify |
|----|-------|-------------|------|--------|
| C21 | continuation-launch-intent-map | LOOM-210 | 60m | `pytest tests/test_loom_continuation_intent.py -q` |

## Slice DAG (parallel waves)

```
Wave 1 — BACKEND ONLY (parallel)
  C01 prepare-gate  C02 mirror-forge-actions  C03 adaptive-answer-ingest
  C04 synthesizer-scaffold  C09 teleology-mirror-receipt

Wave 2 (after Wave 1 merges)
  C05 synthesize-api-route  (needs C04)
  C10 slim-prepare-path     (needs C01)

Wave 3 (after Wave 2)
  C06 synthesis-forge-input     (needs C04,C05)
  C07 synthesis-gravity-fusion (needs C06)
  C08 synthesis-dark-bridge-min (needs C07)
  C11 teleology-after-handoff   (needs C09,C03)
  C18 mirror-handoff-prepare    (needs C02,C01)

Wave 4 — BACKEND INTEGRATION
  C19 mirror-full-pipeline      (needs C06–C11,C18)
  C20 contract-status-flip      (needs C19)

Wave 5 — GENERATOR (LOOM-211, after C07 + C11)
  C22 teleology-artifact-emitter  (needs C03)
  C23 loom-map-generator-scaffold (needs C22, C07)

Wave 6 — UI (DEFERRED until C19 green)
  C12 vision-canvas-shell  C13 vision-canvas-qa  C14 handoff
  C15 serve-vision-canvas  C16 command-engine  C17 terminal-forge-gate
```

## Slice index

| ID | Task doc | LOOM ticket | Est. | Verify |
|----|----------|-------------|------|--------|
| C01 | `task-loom-c01-prepare-gate.md` | LOOM-201 | 30m | `pytest tests/test_loom_pipeline_intent.py::test_loom_c01_prepare_gate -q` |
| C02 | `task-loom-c02-mirror-forge-actions.md` | LOOM-209 | 45m | `pytest tests/test_loom_mirror_forge.py -q` |
| C03 | `task-loom-c03-adaptive-answer-ingest.md` | LOOM-202 | 60m | `pytest tests/test_intent_forge.py -q -k adaptive` |
| C04 | `task-loom-c04-synthesizer-scaffold.md` | LOOM-203 | 30m | `pytest tests/test_loom_synthesizer.py -q` |
| C05 | `task-loom-c05-synthesize-api-route.md` | LOOM-203 | 30m | `pytest tests/test_loom_synthesizer.py::test_synthesize_endpoint -q` |
| C06 | `task-loom-c06-synthesis-forge-input.md` | LOOM-203 | 45m | `pytest tests/test_loom_synthesizer.py::test_forge_projection_input -q` |
| C07 | `task-loom-c07-synthesis-gravity-fusion.md` | LOOM-203 | 60m | `pytest tests/test_loom_synthesizer.py::test_gravity_fusion -q` |
| C08 | `task-loom-c08-synthesis-dark-bridge-min.md` | LOOM-203 | 60m | `pytest tests/test_loom_synthesizer.py::test_min_dark_bridges -q` |
| C09 | `task-loom-c09-teleology-mirror-receipt.md` | LOOM-204 | 45m | `pytest tests/test_loom_teleology.py -q` |
| C10 | `task-loom-c10-slim-prepare-path.md` | LOOM-205 | 45m | `pytest tests/test_orchestrate_session.py -q -k slim` |
| C11 | `task-loom-c11-teleology-after-handoff.md` | LOOM-204 | 45m | `pytest tests/test_loom_teleology.py::test_after_handoff -q` |
| C12 | `task-loom-c12-vision-canvas-shell.md` | LOOM-207 | 30m | `pytest tests/test_loom_pipeline_intent.py::test_loom_intent_forge_blocks_raw_prepare -q` |
| C13 | `task-loom-c13-vision-canvas-qa.md` | LOOM-207 | 60m | manual + `tests/test_loom_ui_contract.py` |
| C14 | `task-loom-c14-vision-canvas-handoff.md` | LOOM-207 | 45m | `tests/test_loom_ui_contract.py` |
| C15 | `task-loom-c15-serve-vision-canvas.md` | LOOM-207 | 20m | `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/` |
| C16 | `task-loom-c16-command-engine-deliberate.md` | LOOM-206 | 60m | `tests/test_loom_ui_contract.py::test_command_engine` |
| C17 | `task-loom-c17-terminal-forge-gate.md` | LOOM-208 | 30m | `pytest tests/test_ui_intent_smoke.py -q -k handoff` |
| C18 | `task-loom-c18-mirror-handoff-prepare.md` | LOOM-209 | 45m | `pytest tests/test_loom_mirror_forge.py::test_handoff_to_prepare -q` |
| C19 | `task-loom-c19-mirror-full-pipeline.md` | LOOM-209 | 90m | `pytest tests/test_loom_mirror_forge.py::test_full_pipeline_mock -q` |
| C20 | `task-loom-c20-contract-status-flip.md` | — | 15m | `pytest tests/test_loom_pipeline_intent.py -q` |
| C22 | `task-loom-c22-teleology-artifact.md` | LOOM-211 | 45m | `pytest tests/test_teleology_artifact.py -q` |
| C23 | `task-loom-c23-loom-map-generator.md` | LOOM-211 | 60m | `pytest tests/test_loom_map_generator.py -q` |

**Automation queue:** `docs/operations/automation-work-queue.md`

## End-state verify (after C20)

```bash
.venv/bin/python -m pytest tests/test_loom_pipeline_intent.py tests/test_loom_mirror_forge.py tests/test_loom_synthesizer.py tests/test_loom_teleology.py -q --no-cov
bash scripts/dev/ui-intent-smoke.sh
```

## Codex exec template

```bash
codex exec --full-auto "$(cat docs/codex-tasks/loom/task-loom-c01-prepare-gate.md)"
```

## Parallel independence

| Slice | Primary touch | Safe parallel with |
|-------|---------------|-------------------|
| C01,C03,C04,C09,C12 | disjoint backend/UI scaffold files | each other in Wave 1 |
| C06,C07,C08 | same `loom_blueprint_synthesizer.py` | **serial** within C06→C07→C08 |
| C13,C16,C17 | different UI files | each other in Wave 3 |
| C19 | reads many modules | **last** integration slice |
