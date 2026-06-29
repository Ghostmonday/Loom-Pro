# Loom C21 — Continuation + Launch Intent Maps (LOOM-210)

**MASTER:** `docs/codex-tasks/loom/MASTER-loom-codex.md`  
**Parent:** `ui/loom-system-intent-map.json`  
**Depends on:** none (contract-only; safe parallel with backend slices C03–C20)  
**Mode:** SPEC ONLY — no Python business logic, no UI HTML/JS/CSS

## Objective

Author **complete Intent Mapping contracts** for the major Loom surface we have NOT started:

1. **Continuation** — brownfield / v2 / update / hotfix on existing repos (NOT greenfield genesis)
2. **Launch** — present the finished product to the user (terminal, browser, native)

Genesis (Vision Canvas → full pipeline) is specced. Continuation and Launch are the product gap discussed in LOOM-210.

## Context (read before writing)

| File | Why |
|------|-----|
| `ui/loom-system-intent-map.json` | Master journey, gates, child_maps pattern |
| `ui/loom-pipeline-intent-map.json` | Headless flow, actions, smoke_scenarios pattern |
| `ui/loom-intent-forge-intent-map.json` | Child map depth: elements, states, algorithm_binding |
| `ui/process-stage-ux-map.json` | `merge.deliverable_retrieval` — launch UX hooks |
| `aoc_supervisor/orchestrate_session.py` | Gap: "Brownfield intent that blends graph plan + intent streams" |
| `aoc-cli/aoc_cli/blueprint.py` | Graph planner — brownfield + greenfield |
| `tests/test_loom_pipeline_intent.py` | Contract test patterns |

## Product semantics (must encode in maps)

### Genesis vs Continuation

| | Genesis | Continuation |
|---|---------|--------------|
| User arrives with | Idea only | Repo path + delta goal (v2, feature, fix, refactor) |
| Interrogation | Full adaptive Q&A | **Delta Q&A** — shortened; skip when graph + prior blueprint ready |
| Teleology hero phase | intent_parse | **graph_ingest** (scan existing structure) |
| Blueprint scope | `greenfield_scaffold` | `delta_patch` or `refactor_partition` |
| Synthesis input | forge projection only | forge delta + existing `.gaijinn/blueprint.json` lineage |
| End moment | **Launch** — show finished product | **Evolution** — show diff, tests, updated app |

Loom must **NOT** require restart for non-Loom repos. Graph ingest is source of truth; interrogation depth adapts.

### Launch surfaces

After `merge.poll_status` completes, user sees **Launch Presentation**:

- `deliverable.present` with `surface: terminal | web | native`
- Terminal: run command / open REPL / `uvicorn` URL printed
- Web: open browser to served URL
- Native: open binary / `.desktop` / app bundle path
- Always offer `deliverable.download` and `deliverable.view_diff` as secondary

Genesis ends in Launch. Continuation ends in Evolution (same actions, different copy + default surface).

## Deliverables

### 1. `ui/loom-continuation-intent-map.json` (NEW)

Must include at minimum:

- `schema_version`, `system: loom`, `surface: loom-continuation`, `parent_spec`
- `session_kinds`: `genesis | continuation | hotfix | v2 | refactor`
- `entry_routes`: attach existing project vs start fresh (links to vision canvas)
- `states` and `ui_phases` for continuation-specific flow
- `elements` — attach UI contract (repo picker, session kind, parent lineage display, delta scope)
- `flow` — ordered phases from attach through handoff (rejoins pipeline at teleology)
- `actions` with full contract per action:
  - `intake.attach_project` — body: repo_path, optional parent_session_id, session_kind
  - `intake.resume_session` — load `.gaijinn/sessions/{id}/session.json`
  - `intake.session_kind_select`
  - `graph.bootstrap` — run scan/analyze if no graph.json; idempotent
  - `interrogation.set_mode` — `full | delta | skip_if_graph_ready`
  - `continuation.confirm_scope` — user approves MODIFY / ADD / DEPRECATE work units preview
  - Reuse forge actions where isomorphic: `question.submit_answer`, `handoff.confirm`, `handoff.accept`
- `algorithm_binding` on every action (module + entrypoint + mode + gaps)
- `gates` — continuation-specific (e.g. require graph.json OR bootstrap complete before teleology)
- `lineage` — `parent_session_id`, `blueprint_version`, `projection_mode` inheritance rules
- `smoke_scenarios` (at least 3):
  - `flow.loom_continuation_attach_brownfield` — attach gaijinn repo, delta intent, handoff
  - `flow.loom_continuation_v2_lineage` — parent session → v2 session → delta blueprint scope
  - `flow.loom_continuation_skip_interrogation` — graph ready + prior blueprint → skip to teleology
- `confusion_signals` — e.g. genesis path used when repo has .gaijinn/, full Q&A on hotfix, etc.

### 2. `ui/loom-deliverable-intent-map.json` (NEW)

Must include:

- `surface: loom-deliverable-launch`
- `parent_spec`: `ui/loom-system-intent-map.json`
- Phases: `merge_complete`, `presenting`, `running`, `evolution_complete`
- `actions`:
  - `deliverable.detect_surfaces` — infer terminal/web/native from blueprint artifacts
  - `deliverable.present` — primary launch moment
  - `deliverable.download`, `deliverable.view_diff` (cross-ref process-stage-ux-map)
  - `deliverable.open_terminal`, `deliverable.open_browser`, `deliverable.open_native`
  - `project.register_for_continuation` — write lineage so next session is Continuation not Genesis
- `elements` — launch card, surface picker, run status, changelog summary
- `api` bindings to existing routes where possible (`GET /api/v1/grid/deliverable`, etc.)
- `smoke_scenarios`:
  - `flow.loom_launch_terminal`
  - `flow.loom_launch_web`
  - `flow.loom_reentry_after_launch` — register → attach on return
- `genesis_vs_continuation_copy` — different user-facing strings, same actions

### 3. Update `ui/loom-system-intent-map.json`

- Add both maps to `child_maps`
- Add `surfaces.continuation` and `surfaces.deliverable_launch` entries (`status: contract_only`)
- Extend `canonical_user_journey.narrative` with Continuation branch (do not remove genesis)
- Add `mandatory_gates` for continuation if needed
- Add `_ai_blueprint.implementation_tickets` entry **LOOM-210** with acceptance + smoke ids
- Add `codex_slices` entry C21 pointing to this task doc

### 4. `tests/test_loom_continuation_intent.py` (NEW)

Contract tests only (no API implementation required):

- All new JSON files parse; `system == loom` where applicable
- Required actions exist in continuation map
- Required smoke_scenarios exist with `implementation_status: spec_only`
- `loom-system-intent-map.json` lists new child_maps
- LOOM-210 ticket present
- `jq`-equivalent: no duplicate action ids within a map

### 5. Update `docs/codex-tasks/loom/MASTER-loom-codex.md`

Add C21 row under a new section **Wave 0 — Contract-only (parallel anytime)**:

| C21 | continuation-launch-intent-map | LOOM-210 | 60m | `pytest tests/test_loom_continuation_intent.py -q` |

## MAY edit

- `ui/loom-continuation-intent-map.json` (new)
- `ui/loom-deliverable-intent-map.json` (new)
- `ui/loom-system-intent-map.json` (child_maps + surfaces + LOOM-210 ticket only)
- `tests/test_loom_continuation_intent.py` (new)
- `docs/codex-tasks/loom/MASTER-loom-codex.md` (C21 index row only)

## MUST NOT edit

- `ui/terminal.*`, `ui/intent-forge.*`, `ui/command-engine.*` (no UI implementation)
- `aoc_supervisor/*.py` business logic (implementation is a later wave)
- Existing smoke_scenarios `implementation_status` values (do not flip to implemented)

## Style rules

- Match depth and field names of `loom-intent-forge-intent-map.json` and `loom-pipeline-intent-map.json`
- Every `action` needs `algorithm_binding` with `gap` field when not shipped
- `implementation_status: spec_only` on all new smoke_scenarios
- Use `contract_only` for surface status
- Determinism: phase order rigid; interrogation path adaptive; graph math deterministic

## Verify

```bash
cd /home/ghostmonday/Desktop/Loom
jq empty ui/loom-continuation-intent-map.json ui/loom-deliverable-intent-map.json ui/loom-system-intent-map.json
.venv/bin/python -m pytest tests/test_loom_continuation_intent.py tests/test_loom_pipeline_intent.py -q --no-cov
```

All must pass. Commit when green:

```
docs(intent): LOOM-210 continuation + launch intent maps (C21)
```

Log run to `.gaijinn/codex/loom-c21-run.jsonl`