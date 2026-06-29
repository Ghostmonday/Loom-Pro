# Loom C01 — Prepare Handoff Gate (LOOM-201)

**MASTER:** `docs/codex-tasks/loom/MASTER-loom-codex.md`  
**Intent:** `ui/loom-pipeline-intent-map.json` → `actions.orchestrate.prepare.preconditions`  
**Smoke:** `flow.loom_reject_raw_prepare`

## Objective

Reject `POST /api/v1/orchestrate/prepare` when `intent_forge_session_id` is missing, unless `GAIJINN_ALLOW_RAW_INTENT_PREPARE=1`.

## MAY edit

- `aoc_supervisor/aoc_supervisor/api.py` (`orchestrate_prepare` handler)
- `tests/test_loom_pipeline_intent.py` (add `test_loom_c01_prepare_gate`)
- `ui/loom-pipeline-intent-map.json` (flip smoke `implementation_status` when green)

## MUST NOT edit

- `ui/terminal.js` (C17)
- `loom_blueprint_synthesizer.py` (C04+)

## Steps

1. In `orchestrate_prepare`, before calling `prepare()`: if env `GAIJINN_ALLOW_RAW_INTENT_PREPARE` unset and body lacks non-empty `intent_forge_session_id` → HTTP 409 with detail citing Loom gate.
2. Existing tests that call prepare without forge id must set `GAIJINN_ALLOW_RAW_INTENT_PREPARE=1` in fixture/monkeypatch.
3. Add test: without bypass → 409; with bypass → 200 (mock grid).

## Verify

```bash
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
.venv/bin/python -m pytest tests/test_loom_pipeline_intent.py::test_loom_c01_prepare_gate tests/test_ui_intent_smoke.py -q --no-cov
```

## Acceptance

- `flow.loom_reject_raw_prepare` steps pass in mirror or API test
- No regression: existing smoke tests pass with bypass env in `conftest.py` or per-test