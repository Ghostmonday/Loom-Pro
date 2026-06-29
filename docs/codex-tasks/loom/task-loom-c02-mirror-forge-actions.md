# Loom C02 — Mirror Intent Forge Actions (LOOM-209 partial)

**MASTER:** `docs/codex-tasks/loom/MASTER-loom-codex.md`  
**Intent:** `ui/loom-intent-forge-intent-map.json` → `actions.*`  
**Depends on:** none (Wave 1)

## Objective

Extend `UiIntentDriver` with `dispatch_loom_forge_action()` for: `intake.start_session`, `question.submit_answer`, `handoff.confirm`, `handoff.accept`. Sync `IntentMirrorState` fields `session_status`, `artifact`, `intent_forge`.

## MAY edit

- `aoc_supervisor/aoc_supervisor/ui_intent.py`
- `aoc_supervisor/aoc_supervisor/intent_mirror.py`
- `tests/test_loom_mirror_forge.py` (new)

## MUST NOT edit

- `intent_forge_service.py` business logic (C03)

## Steps

1. Add mirror context keys: `readiness`, `current_question`, `executable_projection`.
2. Implement dispatch methods calling existing intent-forge API routes with `X-User-Id`.
3. `handoff.confirm` stores `executable_projection` on mirror.
4. Tests: create paid session → submit one answer → confirm → accept → assert `HANDED_OFF`.

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_mirror_forge.py -q --no-cov
```