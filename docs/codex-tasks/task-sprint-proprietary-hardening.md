# Codex Sprint Task — Secure & Hardened Proprietary Gaijinn

This task hardens the security, licensing, testing coverage, and architecture boundaries of Gaijinn under a strictly proprietary model.

## Component 1: Governance & Licensing (Proprietary Alignment)
1. In `LICENSE`, ensure the proprietary notice is clean, and explicitly prohibits copying, modifications, distribution, or sublicensing by unauthorized parties. Keep the "Copyright (c) 2026 Neural Draft LLC. All Rights Reserved." and "PROPRIETARY SOFTWARE LICENSE".
2. In `PROPRIETARY.md`, re-affirm repository visibility status as Private/Proprietary and make sure there are no references to open-source or public contributions.
3. In `SECURITY.md`, reinforce the private proprietary / trade secret classification. Specify that reports are restricted exclusively to authorized design partners under NDA.
4. In `README.md`, remove any badges or language that implies open source or public PR/issues. Update the top section to clear onboarding/developer instructions for authorized Neural Draft LLC collaborators.

## Component 2: CLI & Security Hardening
1. In `aoc-cli/aoc_cli/cli.py`, find the `@app.command() def serve` command. Change the default `host` option value from `"0.0.0.0"` to `"127.0.0.1"`.
2. In `aoc_supervisor/aoc_supervisor/session_security.py`:
   - Define a security dependency/helper that checks for the API key in the header `X-Gaijinn-Api-Key`.
   - The API key to validate against is defined by the `GAIJINN_API_KEY` environment variable.
   - If the environment variable `GAIJINN_ALLOW_INSECURE_LOCAL` is set to `"1"`, `"true"`, `"yes"`, or `"on"`, or if `GAIJINN_API_KEY` is not configured and `GAIJINN_ALLOW_INSECURE_LOCAL` is set, allow the request to proceed without the API key.
   - If `GAIJINN_API_KEY` is not configured and `GAIJINN_ALLOW_INSECURE_LOCAL` is NOT set, the app should raise a 401 HTTPException with detail `"Invalid or missing API key"`.
3. In `aoc_supervisor/aoc_supervisor/api.py`:
   - Apply the new API key security dependency to all mutating API endpoints (`POST`, `PUT`, `DELETE` methods) under `/api/v1/...` and both websocket paths (`/ws/intent-forge` and `/ws/telemetry`).
   - For endpoints where the client is already verified (such as internal endpoints or read-only/dev-mode local tools), auth is optional or checked against loopback source address.
   - Ensure the FastAPI `app` has a lifespan or startup sequence that prints the active `GAIJINN_API_KEY` (or warns if insecure local mode is active).

## Component 3: Quality & Testing Gates
1. In `pyproject.toml`:
   - Change `tool.coverage.run.source` to include both `"aoc_cli"` and `"aoc_supervisor"`.
   - Set branch coverage to `true`.
   - Set the pytest `addopts` configuration to fail if coverage is under `70%`.
2. In `.github/workflows/ci.yml`:
   - Update the step running pytest to set `GAIJINN_ALLOW_INSECURE_LOCAL=1` in the environment so the existing test suite continues to pass without needing API keys.
   - Expand the setup-python step to support python-versions `3.10`, `3.11`, `3.12`, `3.13` in a matrix format.

## Component 4: Static UI Serving Seam
1. Create a new file `aoc_supervisor/aoc_supervisor/routers/static_ui.py`.
2. Move static UI serving routes (e.g. `/`, `/terminal`, `/command-engine`, `/command-engine.css`, `/command-engine.js`, `/blueprint-viz-engine.js`, `/orchestration-event-adapter.js`, `/workflow-chrome.css`, `/workflow-chrome.js`, `/structural-canvas`, `/intent-forge.css`, `/intent-forge.js`, `/intent-forge-canvas.js`, `/intent-forge-shader.js`, `/structural-canvas.css`, `/structural-canvas.js`, `/experience-projection.js`) from `aoc_supervisor/aoc_supervisor/api.py` into `aoc_supervisor/aoc_supervisor/routers/static_ui.py`.
3. In `api.py`, import and include the static UI router using `app.include_router(static_ui.router)`.

## Verification
1. Run `PYTHONPATH=. pytest` to ensure everything passes and code coverage measurement includes `aoc_supervisor` with coverage report.
