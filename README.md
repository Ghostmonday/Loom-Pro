# Loom

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![Tests](https://img.shields.io/badge/tests-405%20collected-green)](#)
[![Ruff](https://img.shields.io/badge/lint-ruff-clean-brightgreen)](#)

**Geometric orchestration engine for parallel AI coding agents.**

Loom converts project intent and repository structure into bounded, enforceable work units for parallel coding agents. It detects hidden coupling, assigns each worker an explicit permission contract, runs workers in isolation, and validates every result before merge.

> Loom is an AI software-engineering orchestration system. It is not affiliated with Loom.com or any video-recording platform.

## How Loom Reads Code

Loom does not start with geometry. It starts by reading your codebase.

```
Source code
    ↓
AST parsing (structure)
    ↓
Type-flow / taint tracking (data movement)
    ↓
Reachability (Dijkstra paths)
    ↓
Graph (nodes + edges)
    ↓
Curvature analysis (κ)
```

A node is a file, function, or state boundary.
An edge is a data flow, call, or dependency.

Example:

```
user_id → db.execute()
```

This becomes a graph edge.
If it forms a bottleneck → κ < -0.30 → Dark Bridge.

Only after this does Loom assign workers and enforce constraints.

---

## Why Loom

Coding agents can edit different files and still collide through shared state, data flow, lifecycle assumptions, or hidden operational dependencies. Import graphs and directory boundaries do not reveal all of those relationships.

Loom determines what can run in parallel, what must remain together, what each worker may change, and which results are safe to merge.

## Core Architecture

```
Confirmed intent
      ↓
Intent Forge
      ↓
Handoff
      ↓
Teleology collection
      ↓
Blueprint synthesis
      ↓
Repository graph + structural analysis
      ↓
Gravity/curvature-conditioned work units
      ↓
GIV-bounded isolated workers
      ↓
Collect → validate → merge
      ↓
Governance and convergence report
```
Probabilistic agents may propose code, but structural authority, scope enforcement, handoff validation, and merge acceptance remain machine-checkable.

## Structural Gravity
Loom applies Ollivier-Ricci curvature to the repository graph to identify bottlenecks that ordinary dependency analysis can miss.

| Curvature | Meaning | Loom response |
|-----------|---------|---------------|
| `κ > 0` | Dense or redundant neighborhood | Strong parallelization candidate |
| `κ ≈ 0` | Stable path | Standard partitioning |
| `κ < 0` | Structural bottleneck | Increased collision risk |
| `κ < -0.30` | Critical **Dark Bridge** | Atomic weld or governed handoff gateway |

A Dark Bridge can be assigned to one worker as an atomic unit or preserved as separate lanes with a validated handoff requirement.

> If the geometry says two regions cannot be changed independently, directory layout and agent confidence do not overrule it.

## GIV Enforcement
Each work unit receives a **GIV**, or Agent Intent Vector — enforced runtime RBAC for autonomous agents. A GIV can define allowed and denied paths, command boundaries, capabilities, prohibitions, invariants, and handoff requirements.

The GIV is not advisory. Worker output is checked against it before merge.

## Merge Integrity

```
collect → validate-worker → merge-grid → structural scoring
```
A worker may finish its task and still be blocked for scope trespass, a missing handoff, a broken invariant, failed validation, or the absence of a fresh delta. Only compliant output enters the integration branch.

Loom reports validation and convergence separately. A fully valid run may still have convergence below `1.0` when work is already integrated and there is nothing new to merge.

## Blueprint Model

| Layer | Purpose | Artifact |
|-------|---------|----------|
| **Layer 0 — Domain Rules** | Domains, invariants, and system constraints | `blueprint.json` |
| **Layer 1 — Reactive Structure** | Endpoints, commands, mutations, guards, and state transitions | `graph.json` |
| **Layer 2 — Reflective Structure** | Lifecycles, dependency contracts, and capability ceilings | `inferred.json` |

- **Greenfield:** Layer 0 → Layer 2 → Layer 1
- **Brownfield:** source scan → Layer 1 → Layer 2

Semantic classification may enrich structured artifacts, but it does not overrule deterministic graph, permission, or merge gates.

## Requirements

- Python 3.10+
- Git
- A Python-compatible operating system
- A supported coding-agent CLI for live worker execution
- Optional FastAPI dependencies for the hosted service

## Installation

```
git clone https://github.com/Ghostmonday/Loom.git
cd Loom

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[api,dev]"

loom version
```
Core CLI only:

```
python -m pip install -e .
```

## Quick Start

```
loom audit .
loom init "Build a production-ready API"
loom scan .
loom analyze
loom plan --workers 4
loom run-grid --workers 4
loom grid-spawn --workers 4 --executor auto
loom collect
loom validate-worker
loom merge-grid --dry-run
loom merge-grid
loom status --strict
```
Use `loom --help` or any command's `--help` option for the authoritative interface.

## Primary Commands

| Command | Purpose |
|---------|---------|
| `loom init` | Initialize project state and seed the build manifest |
| `loom audit` | Evaluate structural readiness without modifying source files |
| `loom scan` | Produce the repository graph |
| `loom analyze` | Run integrity preflight and write structural metrics |
| `loom plan` | Generate the blueprint and worker assignments |
| `loom run-grid` | Create isolated worker directories |
| `loom grid-spawn` | Launch coding workers |
| `loom collect` | Gather worker state and deltas |
| `loom validate-worker` | Apply scope, handoff, invariant, and test gates |
| `loom merge-grid` | Merge validated output into `loom/integration` |
| `loom status` | Summarize orchestration state |
| `loom doctor` | Check installation and project artifacts |
| `loom serve` | Run the hosted Loom service |
| `loom council` | Use the shared agent council thread |

## Repository Structure

```
.
├── aoc-cli/aoc_cli/                 # CLI, graph analysis, planning, and merge commands
├── aoc_supervisor/aoc_supervisor/   # API, Intent Forge, synthesis, and governance
├── docs/                            # Architecture, operations, and case studies
├── examples/                        # Example targets and demonstrations
├── tests/                           # Unit, integration, contract, and end-to-end tests
├── ui/                              # Intent maps and command-bridge assets
├── pyproject.toml
└── README.md
```
Key implementation files:

- `aoc-cli/aoc_cli/cli.py` — `loom` CLI entrypoint
- `aoc_supervisor/aoc_supervisor/loom_pipeline.py` — handoff and teleology sequencing
- `aoc_supervisor/aoc_supervisor/loom_blueprint_synthesizer.py` — curvature-conditioned synthesis
- `aoc_supervisor/aoc_supervisor/loom_map_generator.py` — deterministic contract generation
- `aoc_supervisor/aoc_supervisor/api.py` — hosted service boundary

## Runtime State
The product and CLI are named **Loom**. During migration, legacy `.gaijinn/` state is mirrored into `.loom/`, while some current command paths retain the older directory name for compatibility.

These compatibility paths do not represent separate products. **Loom is the sole current product identity.**

## Verification

```
python -m pytest
ruff check .
ruff format --check .
```

## Demonstrated Results
Documented live-worker runs include a two-worker gateway run with `1.0` final convergence and zero merge conflicts, and a four-worker monorepo run with a `1.0` validation pass rate, zero sibling trespass, synchronized handoffs, zero merge conflicts, and `0.8889` convergence due to honest no-op detection.

The retained historical case study is at [`docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md`](https://chatgpt.com/c/docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md).

## Status
Loom is under active development and is currently classified as alpha software. The Gaijinn-to-Loom migration remains visible in compatibility paths, fallback environment variables, internal names, and historical documentation filenames.

## License
Copyright © 2026 Neural Draft LLC. All rights reserved.

This repository is proprietary software. Unauthorized copying, modification, distribution, sublicensing, or use is prohibited without prior written consent from Neural Draft LLC. See [`LICENSE`](https://chatgpt.com/c/LICENSE) for the complete terms.
