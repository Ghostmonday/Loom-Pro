# DeepSeek roadmap — Loom to project complete

**For:** Claw X (DeepSeek v4) + Codex (+ optional second Codex instance)  
**Repo:** `/home/ghostmonday/Desktop/gaijinn`  
**Branch:** `main`  
**Composer:** gates only — user escalates on blockers

**→ Live work queue:** `docs/operations/automation-work-queue.md` (status board + waves)

## Stack order

```
1. teleology.json     (truth — LOOM-211 C22)
2. topology + graph   (curvature — C07/C08)
3. loom-*.json        (contracts — C23 generator + skill-v2)
4. Codex slices       (C05–C20)
5. UI                 (C12–C17 after C19)
```

---

## Intent map inventory (source of truth)

| Map | Path | Role |
|-----|------|------|
| **Master** | `ui/loom-system-intent-map.json` | Journey, gates, child_maps, LOOM tickets, codex slices |
| **Pipeline** | `ui/loom-pipeline-intent-map.json` | Headless backend flow, actions, smoke_scenarios |
| **Vision Canvas** | `ui/loom-intent-forge-intent-map.json` | Genesis Q&A at `/` |
| **Continuation** | `ui/loom-continuation-intent-map.json` | Brownfield/v2/hotfix attach — **NEW C21** |
| **Launch** | `ui/loom-deliverable-intent-map.json` | Post-merge terminal/web/native — **NEW C21** |
| **Command Engine** | `ui/command-engine-ui-intent-map.json` | Teleology + blueprint approval |
| **Terminal** | `ui/gaijinn-ui-intent-map.json` | Sprint/deploy surface (rebuild after C19) |
| **Process UX** | `ui/process-stage-ux-map.json` | User control points across pipeline |

**Codex master DAG:** `docs/codex-tasks/loom/MASTER-loom-codex.md`

**Intent mapping skill:** `loom-intent-mapping-v2` (`~/.openclaw/skills/loom-intent-mapping-v2/` + `references/*.md`). Do not load v1 `loom-intent-mapping` alongside v2. Teleology slices: also read `references/backend.md` + `teleology.deliberate` / `blueprint.synthesize` in `loom-pipeline-intent-map.json`.

---

## How Codex must include everything (enforcement contract)

Codex does **not** improvise architecture. Each slice implements **one** declared action (or wiring between declared actions). The maps are law; pytest is the judge.

### Preflight (Claw X runs before every `codex exec`)

```bash
cd /home/ghostmonday/Desktop/gaijinn
git checkout main && git pull
# 1. Read task doc + the action(s) it references in loom-pipeline-intent-map.json
# 2. Read algorithm_binding module/entrypoint — open that file in repo
# 3. Confirm slice MAY/MUST NOT file list — no UI, no drive-by refactors
```

**Append to every Codex prompt** (after the task doc body):

```text
ENFORCEMENT (non-negotiable):
- Implement only actions in ui/loom-pipeline-intent-map.json referenced by this task.
- Wire algorithm_binding to real module+entrypoint; if missing, leave spec_only + gap in map.
- Do NOT skip teleology.deliberate, blueprint.synthesize, or handoff gates on the Loom path.
- Do NOT call generate_blueprint / compute_gravity_and_curvature from a shortcut that bypasses teleology receipt on paid Loom path.
- Mirror (UiIntentDriver) must dispatch the same semantic action as the API — no mirror-only shortcuts.
- Run the task doc verify command; commit only when green.
- Flip implementation_status in loom-pipeline-intent-map.json ONLY for scenarios this slice owns, and only when verify passes.
```

### Four layers Codex must satisfy per slice

| Layer | What Codex delivers | Proof |
|-------|---------------------|-------|
| **Map** | Action fields match code (request, returns, postconditions, binding) | `jq empty ui/loom-*.json` + contract tests |
| **Algorithm** | Calls real `algorithm_binding` entrypoint | Import/call path exists; test mocks only via declared env flags |
| **Mirror** | `UiIntentDriver` dispatches same action id | `test_loom_mirror_forge.py` / teleology / synthesizer tests |
| **Gate** | Illegal paths return 409/422, not silent fallback | `test_loom_c01_prepare_gate`, synthesis without receipt fails |

### Ollivier-Ricci curvature + architectural teleology (mandatory chain)

These are **not** optional narrative. They are sewn in through subphases, a receipt object, and numeric tests.

```
handoff.accept
  → teleology.deliberate (SSE, 7 subphases)
       curvature_compute  → aoc_cli/gravity.py :: compute_gravity_and_curvature
                            CURVATURE_HARD_FLOOR = -0.30
       weld_plan          → aoc_cli/blueprint.py :: generate_blueprint
  → teleology_receipt stored on IntentMirrorState.teleology
  → blueprint.synthesize (requires teleology_receipt in body)
       fuse executable_projection + gravity_plan + curvature_metrics
       postcondition: dark_bridge_count <= graph_only_baseline
       projection_mode: loom_synthesis
  → orchestrate.prepare (intent_forge_session_id + synthesized artifact)
```

**`teleology_receipt` minimum fields** (mirror + synthesizer must produce/consume):

```json
{
  "subphases_completed": ["intent_parse", "graph_ingest", "curvature_compute", "bridge_detect", "weld_plan", "partition", "blueprint_freeze"],
  "curvature_floor": -0.30,
  "edge_curvatures": [],
  "dark_bridge_count": 0,
  "weld_count": 0,
  "handoff_gateway_count": 0,
  "blueprint_freeze": {}
}
```

**Continuation brownfield:** teleology hero subphase must be `graph_ingest` first (see `loom-continuation-intent-map.json` confusion signals).

### Per-slice: what Codex must include

| Slice | Intent / geometry obligations |
|-------|------------------------------|
| **C03** | Adaptive answer ingest before `select_next`; evidence reanalysis per `question.submit_answer` |
| **C04** | `loom_blueprint_synthesizer.py` scaffold; `synthesize_blueprint()` stub; types for receipt + result |
| **C09** | `collect_teleology_receipt()` — all 7 subphases; `curvature_floor`; `edge_curvatures`; mirror.teleology populated |
| **C05** | `POST /api/v1/loom/blueprint/synthesize` route; body requires `teleology_receipt` |
| **C10** | Slim prepare when `executable_blueprint` / synthesis artifact injected; skip redundant scan when projection present |
| **C06** | Synthesizer reads forge `executable_projection` + **teleology_receipt**; reject if receipt missing |
| **C07** | Call `compute_gravity_and_curvature` + `generate_blueprint`; attach curvature_metrics to result |
| **C08** | Enforce `dark_bridge_count <= graph_only_baseline`; `projection_mode == loom_synthesis` |
| **C11** | Auto-invoke `teleology.deliberate` after `HANDED_OFF` before prepare/synthesis |
| **C18** | Mirror: handoff → prepare with `intent_forge_session_id`; no raw prepare |
| **C19** | `test_full_pipeline_mock`: full chain including teleology → synthesis → prepare; assert curvature + dark bridges |
| **C20** | Flip smoke `implementation_status` only where tests pass; confusion_signals stay zero |

### After every wave — Claw X confusion check

```bash
cd /home/ghostmonday/Desktop/gaijinn
.venv/bin/python -m pytest tests/test_loom_pipeline_intent.py tests/test_loom_teleology.py \
  tests/test_loom_synthesizer.py tests/test_loom_mirror_forge.py -q --no-cov
```

**Stop and escalate if any of these are true:**

| Confusion signal | Meaning |
|------------------|---------|
| `prepare` without `HANDED_OFF` + session id | Handoff gate bypassed |
| `blueprint.synthesize` without `teleology_receipt` | Teleology skipped |
| `curvature_floor != -0.30` on Loom path | Gravity floor not wired |
| `dark_bridge_count > baseline` after synthesis | C08 optimization failed |
| `projection_mode != loom_synthesis` on paid path | Synthesis bypassed for graph-only |
| Teleology receipt missing `curvature_compute` subphase | SSE wiring incomplete |
| Continuation teleology starts `intent_parse` not `graph_ingest` | Brownfield hero wrong |

### C16 UI note (Wave 5)

Command engine must **display** teleology SSE (display/presentation elements) but **must not** reimplement curvature math in the browser. UI dispatches `teleology.deliberate`; receipt lives on mirror/backend per map.

---

## Done (do not redo)

| Slice | Commit | What |
|-------|--------|------|
| C01 | `b72339e` | Prepare handoff gate LOOM-201 |
| C02 | `c41ac02` | Mirror forge actions LOOM-209 |
| C21 | `130e1d7` | Continuation + Launch intent maps LOOM-210 |
| C03 | merged | Adaptive answer ingest LOOM-202 |
| C04 | merged | Synthesizer scaffold LOOM-203 |
| C09 | merged | Teleology mirror receipt LOOM-204 |

---

## Dual Codex parallelism (user has 2 instances)

| Instance | Use for | Never |
|----------|---------|-------|
| **Codex A** | C03, C06, C07, C08, C11, C19 | C06–C08 same time as each other |
| **Codex B** | C04, C09, C05, C10, C18, C20 | Same file as Codex A on same slice |

**Wave 1 now:** Codex A = C03, Codex B = C04 + C09 (parallel)

---

## Phase 1 — Backend Waves 1–4 (no UI)

### Wave 1 — parallel
```
C03 adaptive-answer-ingest     → pytest tests/test_intent_forge.py -q -k adaptive
C04 synthesizer-scaffold       → pytest tests/test_loom_synthesizer.py -q
C09 teleology-mirror-receipt    → pytest tests/test_loom_teleology.py -q
```
**Gate:** all 3 committed before Wave 2

### Wave 2
```
C05 synthesize-api-route       (needs C04)
C10 slim-prepare-path          (needs C01)
```
Can run in parallel on two Codex instances.

### Wave 3
```
SERIAL:  C06 → C07 → C08  (loom_blueprint_synthesizer.py — one instance only)
PARALLEL after C06 starts C07: C11 (needs C09,C03), C18 (needs C02,C01)
```
C11 and C18 can run on Codex B while Codex A does C06→C07→C08.

### Wave 4 — integration
```
C19 mirror-full-pipeline       (needs C06–C11,C18) — ONE instance, last backend code
C20 contract-status-flip       (needs C19)
```

**Backend complete when:**
```bash
.venv/bin/python -m pytest tests/test_loom_pipeline_intent.py tests/test_loom_mirror_forge.py \
  tests/test_loom_synthesizer.py tests/test_loom_teleology.py -q --no-cov
# test_full_pipeline_mock GREEN
```

**STOP — no UI until above passes.**

---

## Phase 2 — UI Wave 5 (C12–C17)

Only after C19 green. Maps already exist.

| Slice | Surface | Task doc |
|-------|---------|----------|
| C12 | Vision canvas shell | `task-loom-c12-vision-canvas-shell.md` |
| C13 | Vision Q&A | `task-loom-c13-vision-canvas-qa.md` |
| C14 | Handoff UI | `task-loom-c14-vision-canvas-handoff.md` |
| C15 | Serve `/` | `task-loom-c15-serve-vision-canvas.md` |
| C16 | Command engine | `task-loom-c16-command-engine-deliberate.md` |
| C17 | Terminal forge gate | `task-loom-c17-terminal-forge-gate.md` |

**UI verify:**
```bash
bash scripts/dev/ui-intent-smoke.sh
pytest tests/test_loom_ui_contract.py -q
```

---

## Phase 3 — LOOM-210 implementation (post-C20)

Maps exist (C21). Code does not. New slices TBD — Composer writes task docs on user request.

| Area | Map | Key actions to implement |
|------|-----|--------------------------|
| Continuation | `loom-continuation-intent-map.json` | `intake.attach_project`, `graph.bootstrap`, `continuation.confirm_scope` |
| Launch | `loom-deliverable-intent-map.json` | `deliverable.detect_surfaces`, `deliverable.present`, `project.register_for_continuation` |

Smoke targets:
- `flow.loom_continuation_attach_brownfield`
- `flow.loom_launch_terminal`
- `flow.loom_reentry_after_launch`

---

## Standard Codex loop (every slice)

```bash
cd /home/ghostmonday/Desktop/gaijinn
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
mkdir -p .gaijinn/codex
codex exec --full-auto "$(cat docs/codex-tasks/loom/task-loom-cNN-....md)" \
  2>&1 | tee -a .gaijinn/codex/loom-cNN-run.jsonl
# run verify from task doc
git add -A && git commit -m "Cnn: <title> (LOOM-xxx)"
```

---

## Escalate to Composer (user pings only when)

- Same slice fails verify **twice**
- C19 `test_full_pipeline_mock` fails with all deps green
- Git merge conflict
- Task doc missing / intent map contradiction

---

## Wave report template (DeepSeek → user)

```
## Wave N report
- C03: PASS/FAIL | commit | verify output one line
- C04: ...
Blockers: ...
Commits ahead of origin: N
Next wave: N+1
Composer needed: yes/no
```

---

## Project complete definition (v1)

- [ ] C20 — all `loom-pipeline-intent-map.json` smoke_scenarios implemented
- [ ] C19 — `test_full_pipeline_mock` green with teleology receipt + `loom_synthesis` + dark_bridge baseline
- [ ] `curvature_floor == -0.30` asserted in teleology tests on Loom path
- [ ] C17 — terminal requires handoff
- [ ] `ui-intent-smoke.sh` green
- [ ] Genesis path: vision → teleology → synthesis → build → launch presentation
- [ ] Continuation maps ready for Phase 3 implementation

---

## Claw X paste (start any session)

```
Load loom-codex-delegate, loom-intent-mapping-v2.
Read ~/Desktop/gaijinn/docs/operations/deepseek-roadmap-to-completion.md
Follow "Preflight" + append ENFORCEMENT block to every codex exec.
Continue from first incomplete wave. Use both Codex instances for parallel slices.
After each wave run confusion check. Commit when verify green. Report wave template.
```