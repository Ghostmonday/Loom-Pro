# Loom UI contracts

**JSON only.** Runtime HTML/CSS/JS is served from `sandbox_frontend/` (see `aoc_supervisor/repo_paths.py`).

## Contract files (source of truth)

| File | Role |
|------|------|
| `loom-ui-intent-map.json` | Primary surface: phases, elements, API actions, smoke scenarios |
| `loom-system-intent-map.json` | Master journey, layers, LOOM tickets |
| `loom-pipeline-intent-map.json` | Headless backend pipeline + mirror smoke scenarios |
| `loom-intent-forge-intent-map.json` | Vision canvas / adaptive interrogation |
| `command-engine-ui-intent-map.json` | Command engine stepper and controls |
| `process-stage-ux-map.json` | Unified workflow steps across surfaces |
| `blueprint-ui.json` | Neural-draft / internal UI blueprint linkage |
| `experience-policy.json` | Deny-by-default capabilities, redaction, aggregation |
| `orchestration-*.schema.json` | SSE/WebSocket event + snapshot contracts |

Legacy `ui/*.html` pages were removed; do not re-add HTML here.

## Dev server

```bash
cd /home/ghostmonday/Desktop/Loom
.venv/bin/pip install -e ".[api]"
.venv/bin/uvicorn aoc_supervisor.api:app --reload --port 8080
# http://127.0.0.1:8080/  — sandbox_frontend shell
```

## Verify without a browser

```bash
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
.venv/bin/python -m pytest tests/test_loom_ui_contract.py tests/test_canonical_authority_registry.py -q --no-cov
```

Paths resolve from `aoc_supervisor.repo_paths`. Mirror tests use `UiIntentDriver` against intent maps.