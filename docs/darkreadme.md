# Gaijinn

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![Tests](https://img.shields.io/badge/tests-200%20passing-green)](#)

**Geometric orchestration for parallel AI coding agents.**

Gaijinn lets you run multiple AI coding agents on the same codebase simultaneously — without them overwriting each other's work.

---

## The problem

When two AI agents edit different files, you assume they're independent. That assumption fails whenever those files share hidden dependencies — the same data pipeline, overlapping state mutations, or implicit coupling that no import graph shows.

Standard dependency analysis (DAGs, import trees) only captures explicit references. Hidden coupling looks like independence — until merge produces broken code.

## The approach

Gaijinn measures the **topology** of your codebase — how information actually flows between files — rather than just reading import statements. This reveals hidden structural constraints that determine which files can safely be edited by different agents simultaneously and which must be handled by a single agent to avoid conflict.

The system enforces these boundaries through:

1. **Per-worker permission contracts** — each agent receives a scope definition specifying exactly which files it may modify, which are off-limits, and what invariants must hold
2. **Filesystem isolation** — each agent works in its own directory, unable to see or modify other agents' files
3. **A merge enforcement gate** — after agents finish, their output is validated against the scope definitions before any code enters the main project

---

## What it produces

The system assigns each file to a work unit. Work units are distributed across agents. The merge gate validates compliance and produces a structural score.

On a live two-worker sprint against a real project using production AI agents:

| Metric | Result |
|--------|--------|
| Worker validation pass rate | 100% |
| Scope compliance | Zero violations |
| Merge conflicts | Zero |
| Structural convergence | 0.89 |

A structural convergence score of 0.89 means 89% of agent output was successfully merged. The remaining 11% was correctly held back by the enforcement gate — not merged in error.

---

## Addressing common questions

### Does blocking agent output waste compute?

Each agent receives its scope boundary *before* starting work. Violations are prompt-compliance failures, not surprises. The enforcement score is honest accounting — it reports exactly what happened rather than hiding partial results. As scope definitions improve, compliance converges toward 100%.

### Does safe parallelization limit throughput?

The system offers two modes. In the default mode, structurally entangled files are grouped into the same work unit to guarantee conflict-free execution. In the advanced mode, agents working on adjacent files can request coordinated changes through a structured handoff protocol — enabling parallel execution even across shared dependencies. The appropriate mode depends on the codebase and performance requirements.

### Can agents coordinate on shared resources?

When agents need to modify files that share underlying dependencies, a coordination bus allows them to request and acknowledge changes through a structured ticket system. The merge gate validates that every request has been resolved before accepting output. This has been proven in production with real AI agents operating on separate but coupled files.

---

## Quickstart

```bash
pip install -e ".[api,dev]"

gaijinn init "Build a REST API"
gaijinn scan .           # analyze codebase topology
gaijinn analyze           # compute structural metrics
gaijinn compile-prompt    # generate scope contracts
gaijinn plan --workers 2  # partition work
gaijinn run-grid          # create isolated worktrees
gaijinn grid-spawn        # launch agents
gaijinn collect && gaijinn validate-worker && gaijinn merge-grid  # enforce and merge
```

Or serve the terminal UI:

```bash
./scripts/dev/phase0-demo.sh
# Open http://127.0.0.1:8080
```

---

## Architecture

```
CLI layer:
  scan        Build dependency graph
  analyze     Compute structural topology
  plan        Geometry-informed work partitioning
  run-grid    Create isolated worktrees
  grid-spawn  Launch AI agents
  merge-grid  Validate and merge agent output

API layer:
  orchestrate    Session lifecycle management
  merge          Post-sprint enforcement gate
  deliverable    Output packaging and export

UI layer:
  Terminal       Intent → blueprint → sprint → merge → deliverable
  Scope selector Backend / Frontend / Full Stack presets
```

---

## Status

200 tests. Production agent sprint completed with real AI workers. Structural convergence verified across multiple runs with varying worker counts. Available for evaluation on request.

---

## License

Proprietary — Copyright 2026 Neural Draft LLC.
