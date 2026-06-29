# Cursor Task — Terminal Blueprint Review Surface (Pre-Dogfood)

## Objective

When Amir runs `prepare`, the terminal must show **everything the blueprint contains** so he can conclude compiler correctness before deploy — without opening JSON.

**Not a user quality gate.** Creator visibility during dogfood.

## Working directory

`/home/ghostmonday/Desktop/Loom`

## Files you MAY edit

- `ui/gaijinn-terminal.html`
- `ui/views/command-engine.{html,js,css}` (if blueprint panel lives there)
- `ui/loom-ui-intent-map.json` (add display invariants only — do not break smoke_scenario steps)
- `tests/test_ui_intent_smoke.py` (assertions on new fields only)

## Files you MUST NOT edit

- `aoc-cli/**`, `aoc_supervisor/**` (request backend fields via API contract — coordinate with Codex)
- `docs/codex-tasks/task-backend-gears.md`

---

## Requirements

### After `orchestrate.prepare` succeeds

Show in terminal (dark elegant styling — match existing command engine):

1. **Project goal** (full intent text, truncated with expand)
2. **Work streams table:** `WU-ID | title | allowed_paths | depends_on | risk`
3. **Blueprint mode** (`intent` vs `graph`)
4. **Swarm recommendation** + rationale (already partial — make complete)

### Styling

- Dark workstation aesthetic: existing palette, no new theme fork
- Readable monospace for paths
- High-risk units visually distinct (privacy, security streams)

### API contract

Consume existing prepare response fields:

- `work_stream_titles`, `work_units` (if exposed), `blueprint_mode`, `recommended_swarm`, `swarm_rationale`

If `work_units` detail not in API, add **read-only** field to prepare response (coordinate — backend task) or fetch from session blueprint endpoint.

### Smoke

- `test_prepare_returns_session_stats` still passes
- New assertion: prepare payload includes stream titles visible in driver response

---

## Acceptance

1. Prepare PKM intent in terminal shows 7+ work streams with paths
2. Prepare test-editor intent shows editor/rust/go/ui streams (after backend STREAM_SPECS)
3. `python -m pytest tests/test_ui_intent_smoke.py -q` green
4. Council post as cursor with screenshot description or field list

## Not in scope

- Building the Rust/Go editor (dogfood comes after gears are oiled)
- User-facing "quality score" or coverage percentage