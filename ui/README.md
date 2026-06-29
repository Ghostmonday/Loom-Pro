# Gaijinn UI contracts

Implementation was removed for a clean rebuild. **Contracts below are the source of truth** for the new frontend.

## Retained build contracts

| File | Role |
|------|------|
| `gaijinn-ui-intent-map.json` | Primary surface: phases, elements, API actions, smoke scenarios |
| `command-engine-ui-intent-map.json` | Command engine stepper and controls |
| `process-stage-ux-map.json` | Unified workflow steps across surfaces |
| `blueprint-ui.json` | Neural-draft / internal UI blueprint linkage |
| `experience-policy.json` | Deny-by-default capabilities, redaction, aggregation |
| `orchestration-event.schema.json` | Canonical SSE/WebSocket event envelope |
| `orchestration-snapshot.schema.json` | Reconnect/recovery projection |
| `orchestration-visual-grammar.json` | Truthful visual semantics for assembly panel |

Vault overlay: `vaults/gaijinn-memory-fs/ui/vault-ui-intent-map.json`

## Dev server

```bash
cd /path/to/gaijinn && .venv/bin/pip install -e ".[api]"
.venv/bin/uvicorn aoc_supervisor.api:app --reload --port 8080
# http://127.0.0.1:8080/          — rebuild placeholder
# http://127.0.0.1:8080/ui/contracts/gaijinn-ui-intent-map.json
```

## Verify without a browser

```bash
./scripts/dev/ui-intent-smoke.sh
./scripts/ci/algorithm-wiring.sh
./scripts/ci/validate-orchestration-schemas.sh
```

Paths are resolved from `aoc_supervisor.repo_paths`. API mirror tests use `UiIntentDriver` against the intent map — no HTML required.

`algorithm-wiring.sh` runs `tests/test_algorithm_wiring.py` with production-like provider config (HTTP reasoning URL set; `GAIJINN_FAKE_REASONING` and `GAIJINN_MOCK_GRID` unset). Intent map `_ai_blueprint.verification.non_production_flags` documents those test-only env vars.

### Reasoning provider env (API startup)

Production interrogation uses the HTTP reasoning boundary wired in `aoc_supervisor.api` lifespan:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GAIJINN_REASONING_PROVIDER` | `http` | Provider kind (`http` in production) |
| `GAIJINN_REASONING_URL` | *(required for prod)* | POST endpoint that accepts `{ "snapshot": ... }` and returns analysis JSON |
| `GAIJINN_REASONING_TIMEOUT` | `60` | Request timeout in seconds |
| `GAIJINN_FAKE_REASONING` | unset | Set to `1` for deterministic offline interrogation (tests/local only) |

Do not set `GAIJINN_FAKE_REASONING=1` in production. Provider failures surface `analysis_recovery` retry state — there is no silent fallback to canned questions.