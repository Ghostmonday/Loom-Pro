# Changelog

## Unreleased

- Repo layout: `ui/` for terminal assets, `scripts/{ci,dev,codex}/`, `docs/{reference,guides,architecture,codex-tasks}/`
- Intent-driven orchestrate: `intent_blueprint`, `orchestrate_session`, `workflow_evaluator`, UI intent map v3
- Terminal v2: phase/subphase state machine, mirror smoke tests, Codex parallel task contracts
- 171 tests passing; README and doc index refreshed

## 0.1.0 (2026-06-14)

- Initial public CLI surface: activate, init, scan, analyze, compile-prompt, plan, run-grid, status, doctor, version, monitor
- Gravity/curvature engine with shadow bridge detection and hard-floor rejection
- MOAT prompt parser for deterministic capability profiling
- GIV (Agent Intent Vector) schema with safety defaults (no git push, no secret exfiltration)
- Blueprint generation with non-overlapping work units and shadow bridge isolation
- Worker grid with git worktree and copy modes
- Centralized error hierarchy with actionable fix commands
- E2E golden path test, acceptance script, and CI workflow
- 79% test coverage on `aoc_cli`, 103 tests, Ruff-clean
- Terminal bridge WIP: `grid-spawn` CLI command, supervisor grid API endpoints
