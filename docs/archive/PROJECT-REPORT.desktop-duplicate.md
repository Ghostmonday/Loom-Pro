# Gaijinn — Complete Project Report

**Repository:** github.com/Ghostmonday/Gaijinn (private)
**Current commit:** 61d2656 (2026-06-14)
**Version:** 0.1.0
**License:** MIT
**Python:** >=3.10
**Owner:** Neural Draft LLC (Amir)

---

## What Gaijinn Is

Gaijinn is a CLI tool that turns a project prompt and codebase scan into constrained, isolated worker handoffs for parallel AI coding agents. It uses a graph-theoretic gravity/curvature engine to detect risky coupling (Shadow Bridges), generates deterministic blueprints with non-overlapping work units, and creates isolated worker directories (git worktrees or copies) with hardened safety contracts.

Core philosophy: deterministic, explicit, offline, no LLM calls in core flow.

---

## CLI Commands (11 total)

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `activate` | Store hashed license key | `LICENSE_KEY` (arg) |
| `init` | Initialize .gaijinn project state | `--force`, `--blueprint-template`, `--no-agent-files` |
| `scan` | Walk directory → graph.json | `PATH` (arg) |
| `analyze` | Compute gravity/curvature metrics | `--graph`, `--output`, `--json`, `--fail-on-rejection`, `--fail-on-shadow-bridge` |
| `compile-prompt` | Parse prompt → GIV + intent | `--json` |
| `plan` | Generate blueprint from graph+metrics+GIV | `--workers N`, `--max-risk`, `--json` |
| `run-grid` | Create worker directories | `--workers N`, `--force` |
| `status` | Project state dashboard | `--json`, `--strict` |
| `doctor` | Diagnose installation | `--json`, `--strict` |
| `version` | Print version | `--json` |
| `monitor` | Watch metrics manifest | `--manifest`, `--poll-interval` |

---

## Architecture

```
aoc-cli/aoc_cli/
  cli.py                  — 11 @app.command() decorators + imports (~250 lines)
  __init__.py             — Re-exports + __version__
  __main__.py             — python -m aoc_cli entry
  
  commands/               — One file per command
    activate.py
    analyze_.py
    compile_prompt.py
    doctor.py
    init_.py
    monitor.py
    plan.py
    run_grid.py
    scan.py
    status.py
    version.py
  
  helpers/                — Shared utilities (~1,290 lines total)
    __init__.py           — Re-exports all helpers
    constants.py          — Paths, GAIJINN_DIR, etc.
    io.py                 — JSON loading, file validation
    scan.py               — Directory walking, Python import detection
    git.py                — Git worktree detection
    workers.py            — Worker grid, work units, path overlap
    diagnostics.py        — Status payload, doctor checks, analysis summaries
  
  gravity.py              — Gravity engine: structural gravity + Ollivier-Ricci curvature
  blueprint.py            — Blueprint/WorkUnit schema + deterministic generation
  giv.py                  — Agent Intent Vector dataclass + safety defaults
  moat.py                 — Keyword-based prompt parser
  state.py                — .gaijinn/project.json state model
  errors.py               — GaijinnError, ValidationError, SafetyError, etc.

aoc_supervisor/aoc_supervisor/  — Separate FastAPI gateway (not CLI-integrated)
  api.py                  — FastAPI app (/api/v1/analyze, /api/v1/health)
  billing.py              — Credit ledger, deduct_compute_costs, ledger storage provider
  enforcer.py             — validate_system_state()
  orchestrator.py         — ClusterOrchestrator, sandbox provisioning
```

---

## E2E Workflow

The golden path that acceptance.sh verifies:

1. `gaijinn init --no-agent-files "Build a backend API service with tests"` — creates .gaijinn/project.json
2. `gaijinn scan .` — walks directory, respects .gitignore, produces graph.json (Python import edges)
3. `gaijinn analyze` — computes gravity + curvature, writes metrics_manifest.json
4. `gaijinn compile-prompt` — parses prompt via MOAT, writes giv.json + intent.txt
5. `gaijinn plan --workers 2` — generates blueprint.json + blueprint.md with isolated work units
6. `gaijinn run-grid --workers 2` — creates .gaijinn/workers/worker-001..002 with intent, GIV, work units
7. `gaijinn status --strict` — reports state=ready, worker_grid count=2, no shadow bridges

---

## Key Engineering Decisions

- **Deterministic scan:** Uses AST parsing for Python import detection. No LLM calls. Output is byte-identical on repeated runs.
- **Gravity engine:** Structural gravity = weighted sum of in_degree, out_degree, capability_level, side_effect_score. Ollivier-Ricci curvature via Wasserstein-1 distance (POT library). Hard floor at 0.20.
- **Shadow bridges:** Edges with negative curvature or risk jumps (low-context→high-capability transitions). Automatically isolated into single-file work units during planning.
- **GIV safety defaults:** `denied_commands` always includes `git push`. `prohibitions` always include `no secret exfiltration`, `no edits outside assigned paths`, `no destructive cleanup`.
- **Worker isolation:** Git worktree mode when in a clean git repo; directory copy mode otherwise. Workers never push, never write outside assigned paths.
- **Activation keys:** Stored as SHA-256 hash + masked preview only. No plaintext on disk.
- **Error hierarchy:** GaijinnError → StateError, ValidationError, PrerequisiteError, SafetyError. Every error includes a cause and a `fix_command` string.

---

## Quality Metrics

- **Tests:** 102 passing (pytest, 0.7s)
- **Coverage:** 84% on aoc_cli (1,768 lines, 287 uncovered)
- **Lint:** Ruff-clean (line-length=120, target=py310, pre-commit hooks)
- **CI:** GitHub Actions — install, pytest, ruff check, ruff format --check

### Test Breakdown

| Test file | Tests | What it covers |
|-----------|-------|----------------|
| test_cli.py | 33 | Every CLI command, help text, E2E workflow, edge cases, error messages |
| test_supervisor.py | 52 | Enforcer, billing ledger, account verification, orchestration, FastAPI |
| test_gravity.py | 3 | Gravity engine valid/invalid/shadow bridge |
| test_giv.py | 7 | GIV schema, defaults, validation, JSON serialization |
| test_moat.py | 5 | MOAT keyword parsing, determinism, dangerous phrases |
| test_blueprint.py | 3 | Blueprint generation, shadow bridge isolation, overlap detection |
| test_e2e_golden_path.py | 2 | Full E2E against example project, acceptance.sh failure regression |

---

## Documentation

- `README.md` — 5-minute quickstart with full workflow
- `docs/cli-reference.md` — Every command with syntax, options, artifacts, examples
- `docs/concepts.md` — Blueprint, GIV, MOAT, gravity/curvature, shadow bridge, worker grid, worktree isolation (with Mermaid diagram)
- `docs/troubleshooting.md` — 13 common issues with symptom, cause, fix, prevention
- `docs/product-readiness-audit.md` — Historical audit (outdated, kept for reference)
- `CHANGELOG.md` — Version 0.1.0 release notes
- `CONTRIBUTING.md` — Contribution guidelines

---

## Infrastructure

- **Scripts:** `scripts/acceptance.sh` (full E2E + pytest + PASS/FAIL), `scripts/demo-local.sh` (walkthrough demo)
- **CI:** `.github/workflows/ci.yml` — push/PR triggers, installs dev deps, runs tests + ruff + acceptance
- **Pre-commit:** Ruff lint + format hooks (v0.15.17)
- **Example project:** `examples/tiny-python-service/` — 3-module task service with tests, used by E2E test
- **.gitignore:** Covers pycache, pytest_cache, .venv, .ruff_cache, .coverage, egg-info, .gaijinn/

---

## Remaining Gaps (Not in Roadmap)

| Item | Priority |
|------|----------|
| FastAPI gateway alignment with CLI (12.1/12.2) | Low — separate concern |
| F/S/G metrics surfaced as named CLI values | Low — computed but not labeled |
| Demo artifacts page showing example outputs | Low — cosmetic |
| Release checklist doc | Low — lightweight need |
| aoc_supervisor has no CLI commands | By design — separate entry point |
