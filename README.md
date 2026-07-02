# Loom

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-940%20passing-green)
![Ruff](https://img.shields.io/badge/lint-ruff-clean-brightgreen)

**Geometric orchestration engine for parallel AI coding agents.**

Loom lets you throw multiple AI coding agents at a codebase simultaneously — without them stepping on each other.

It works by measuring the *actual geometry* of your code, not just the import graph. Two files that never import each other can still be tightly coupled through shared state or data flow. Loom detects that hidden coupling mathematically, ensures those files are never assigned to different agents, and enforces the boundaries at runtime.

> Loom is an AI software-engineering orchestration system. It is not affiliated with Loom.com or any video-recording platform.

---

## Table of Contents

- [Why Loom Exists](#why-loom-exists)
- [The Problem: Hidden Coupling](#the-problem-hidden-coupling)
- [The Solution: Geometric Analysis](#the-solution-geometric-analysis)
- [Dark Bridges & Atomic Welds](#dark-bridges--atomic-welds)
- [Multi-Agent Council](#multi-agent-council)
- [Architecture](#architecture)
- [Commands](#commands)
- [Real Results](#real-results)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Runtime Pipeline](#runtime-pipeline)
- [Source Dump Workflow](#source-dump-workflow)
- [Repository Structure](#repository-structure)
- [Tests](#tests)
- [Runtime State](#runtime-state)
- [Status](#status)
- [License](#license)

---

## Why Loom Exists

Modern AI-assisted software engineering has moved beyond single-file autocomplete toward multi-agent systems executing parallel development plans. Parallel execution introduces three fundamental problems:

1. **Shared Context Degradation** — As worker count increases, implicit context needed to prevent overlap degrades. Agents make disjoint assumptions about shared state and APIs.
2. **Implicit vs. Explicit Intent** — ASTs and import DAGs do not capture high-level architectural intent. They show *how* code is wired, not *why* it was designed that way or what constraints must govern changes.
3. **Post-Hoc Verification vs. Runtime Constraints** — Most safety tools validate *after* generation. When an agent breaks an invariant or writes to unauthorized files, the compute is wasted and code review becomes the bottleneck.

Loom addresses these by making intent, authority, and validation explicit, machine-checkable contracts.

---

## The Problem: Hidden Coupling

If you give two AI agents different files to edit, you assume they're working independently. That assumption is wrong whenever those files are **functionally coupled** — they mutate the same state, share a data pipeline, or depend on the same operational cadence.

Standard dependency analysis (import graphs, DAGs) misses this entirely. It only sees explicit references. The hidden coupling looks like independence — until the agents' outputs collide at merge time.

---

## The Solution: Geometric Analysis

Loom uses **Ollivier-Ricci curvature**, a concept from differential geometry adapted to graphs. It measures how information flows between neighborhoods in the codebase graph.

The metric: **κ (kappa)**, computed via Wasserstein optimal transport distance.

### How Loom Reads Code

```text
Source code
    ↓
AST parsing (structure)
    ↓
Type-flow / taint tracking (data movement)
    ↓
Reachability (Dijkstra paths)
    ↓
FRG (Function-Realization Graph)
    ↓
Curvature analysis (κ)
```

### What Curvature Means

| Curvature | Meaning | What the system does |
| ----------- | --------- | ---------------------- |
| `κ > 0` | Dense cluster — redundant paths | Heavy parallelization |
| `κ ≈ 0` | Stable pipeline — predictable | Standard splitting |
| `κ < 0` | Narrow bottleneck — hidden constraint | Increased collision risk |
| `κ < -0.30` | **Dark Bridge** — critical weld | Atomic unit or governed handoff |

---

## Dark Bridges & Atomic Welds

When curvature analysis detects dark bridges (edges with `κ < -0.30`), the system **welds** them via a union-find algorithm. Every file connected through dark bridges is fused into a single atomic work unit:

- **Before welding**: Two files connected by a dark bridge could be assigned to different agents. Both make conflicting assumptions. Merge produces broken code.
- **After welding**: Those files are fused into one work unit. One agent handles both. No conflict possible.

**The Surgery Rule**: If curvature says two files can't be parallelized, they aren't — no matter how cleanly separated their imports look. The geometry is the authority.

### Handoff Gateway Mode

Set `GAIJINN_HANDOFF_GATEWAYS=1` to replace atomic welds with structured handoff tickets. Dark bridge files stay in separate workers, but when an agent needs to modify a sibling-controlled file, it raises a structured handoff ticket through the [Multi-Agent Council](#multi-agent-council) bus. The merge gate validates every ticket before accepting output.

The environment flag uses the legacy `GAIJINN_*` prefix while Loom migration compatibility remains active.

---

## Multi-Agent Council

When agents on separate files share a dependency, the **Multi-Agent Council** (`council.py`) operates as a structured transaction bus:

1. A shared context block is injected into each worker's prompt
2. An agent writes a `HANDOFF_TRANSACTION_REQUEST` ticket into the council file
3. The sibling reads, accepts, or rejects — writing a `HANDOFF_TRANSACTION_RECEIPT`
4. The merge gate validates that every open ticket has a matching receipt

On the gateway victory lap, worker-001 raised ticket `TX-HT-84348F`, worker-002 produced the matching receipt, and convergence was **1.0** with **zero atomic weld units** and **92 handoff gateway edges**.

---

## Architecture

```text
CLI layer:
  scan          Build dependency graph
  analyze       Compute curvature, detect dark bridges
  plan          Geometry-conditioned work partitioning
  run-grid      Create isolated worktrees
  grid-spawn    Launch AI agents with GIV contracts
  collect       Gather worker output
  validate      GIV compliance + handoff + invariants
  merge-grid    Validate and merge compliant output

API layer:
  orchestrate        Session lifecycle management
  preflight          Upstream CI gate
  intent-forge       Intent → blueprint synthesis
  deliverable        Output packaging and export

UI layer:
  Terminal            Intent → blueprint → sprint → merge → deliverable
  Council bus         Cross-worker handoff coordination
  Intent maps         FRG, curvature, and boundary visualization
```

### Blueprint Model

| Layer | Purpose | Artifact |
| ------- | --------- | ---------- |
| **Layer 0 — Domain Rules** | Functional domains, invariants, system constraints | `blueprint.json` |
| **Layer 1 — Reactive Structure** | Endpoints, commands, mutations, guards, state transitions | `graph.json` |
| **Layer 2 — Reflective Structure** | Lifecycles, dependency contracts, capability ceilings | `inferred.json` |

- **Greenfield:** Layer 0 → Layer 2 → Layer 1
- **Brownfield:** source scan → Layer 1 → Layer 2

### GIV Enforcement

Each work unit receives a **GIV (Agent Intent Vector)** — an enforced runtime RBAC contract defining:

- **Allowed paths** — exact files this agent may edit
- **Denied paths** — files this agent must never touch
- **Allowed/denied commands** — shell permissions
- **Capabilities** — what this agent is good at
- **Invariants** — conditions that must remain true after the agent finishes

The GIV is not advisory. Worker output is checked against it before merge.

### Merge Integrity

```text
collect → validate-worker → merge-grid → structural scoring
```

Every merge gets a composite grade:

| Signal | Meaning |
| -------- | --------- |
| `validation_pass_rate` | Fraction of workers passing all gates |
| `convergence` | Composite structural score (honest — no ghost merges) |
| `transaction_bus_synchronized` | All handoff tickets resolved |
| `handoff_isolation` | Zero sibling path trespass |

---

## Commands

| Command | Purpose |
| --------- | --------- |
| `loom init` | Initialize project state and seed the build manifest |
| `loom audit` | Evaluate structural readiness without modifying source files |
| `loom scan` | Produce the repository graph |
| `loom analyze` | Run integrity preflight and write structural metrics |
| `loom plan` | Generate the blueprint and worker assignments |
| `loom run-grid` | Create isolated worker directories |
| `loom grid-spawn` | Launch coding workers with GIV injection |
| `loom collect` | Gather worker state and deltas |
| `loom validate-worker` | Apply scope, handoff, invariant, and test gates |
| `loom merge-grid` | Merge validated output into `loom/integration` |
| `loom status` | Summarize orchestration state |
| `loom doctor` | Check installation and project artifacts |
| `loom serve` | Run the hosted Loom service (FastAPI) |
| `loom council` | Use the shared agent council thread |
| `loom hermes` | Launch the interactive council-backed Hermes interface |

---

## Real Results

Loom has been dogfooded end-to-end with **live Grok Build agents** on the Loom monorepo itself.

### Phase 2 — Monorepo Dogfood (171 nodes, June 16 2026)

| Parameter | Value |
| ----------- | ------- |
| Target | Loom monorepo (171 code nodes) |
| Graph | 171 nodes · 92 dark bridges (handoff gateway edges) · 54 work units |
| Agents | 4 concurrent copy-mode Grok workers |
| Handoff ticket | `TX-HT-6D0B24` (resolved) |
| Validation pass rate | **1.0** (4/4 workers) |
| Sibling trespass | **0** |
| Transaction bus | **synchronized** |
| Convergence | **0.8889** (honest — see below) |
| Merge conflicts | **0** |

**Gateway audit:** Legacy mode serializes **44 files** in **2 atomic welds**. Gateway mode: **0** welds, **44 files unlocked**, **47** max parallel workers.

### Honest Accounting

Loom's convergence score of **0.8889** is a badge of mathematical purity — three copy-mode workers had no fresh filesystem deltas at final merge (their work was already integrated). Loom flagged them as `PREFLIGHT_BLOCKED` rather than inflating metrics with ghost merges. Every participating worker achieved **1.0 validation compliance**, ensuring zero trespass.

### Wave 1 — Multi-Agent Dogfood (Grok Composer 2.5, July 2026)

A second live dogfood run, this time coordinated by Claude directing four parallel headless Grok Composer workers, each independently validated against its brief before merge:

| Worker | Task | Result |
| -------- | ------ | -------- |
| 101 | Lint cleanup of `loom-frontend-base/` + `frontend-formation-complete/` | 33 files fixed, only intentional `S101` (test asserts) remain |
| 102 | Test coverage for `websocket_telemetry.py` | 44% → **93%** coverage, 32 new tests |
| 103 | Audit README code-deep-dive snippets against live source | 19 snippets checked, 9 drifted, 1 path-wrong, 0 fabricated — see `docs/reference/deep-dive-appendix-drift.md` |
| 104 | Test coverage for `ui_intent.py` | 65% → **75%** coverage, 26 new tests |

Full suite re-verified independently after each worker's commit — **940 passed, 1 skipped, 0 failures.** The same sprint also shipped the **Resolution Observatory** (`sandbox_frontend/observatory/`), a replay UI driven by a real, non-mocked `resolution_v3` engine run — see [Runtime Pipeline](#runtime-pipeline) below.

---

## Installation

```bash
git clone https://github.com/Ghostmonday/Loom.git
cd Loom

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[api,dev]"

loom version
```

Core CLI only:

```bash
python -m pip install -e .
```

### Requirements

- Python 3.10+
- Git
- Linux, macOS, or WSL2
- Optional: FastAPI dependencies for the hosted service (`pip install -e ".[api]"`)

---

## Quick Start

```bash
# Audit an existing codebase
loom audit .

# Initialize a new project from intent
loom init "Build a production-ready REST API with Postgres"

# Scan and analyze the repository graph
loom scan .
loom analyze

# Plan and execute parallel work
loom plan --workers 4
loom run-grid --workers 4
loom grid-spawn --workers 4 --executor auto

# Collect, validate, and merge
loom collect
loom validate-worker
loom merge-grid --dry-run
loom merge-grid

# Check the result
loom status --strict
```

Use `loom --help` or any subcommand's `--help` for the authoritative interface.

## Runtime Pipeline

Loom now has a minimal deterministic end-to-end runtime path wired through the hardened `resolution_v3` engine:

```bash
loom run-pipeline examples/runtime-pipeline-minimal.json
```

That path covers:

```text
input -> constraint graph -> resolution_v3 -> work unit extraction -> execution -> ordered result aggregation
```

It is intentionally narrow and boring in the good way: one input, one deterministic output shape, no scheduler cleverness yet.

### Resolution Observatory

A replay UI for watching `resolution_v3` govern a run frame by frame:

```bash
python3 sandbox_frontend/observatory/generate_resolution_trace.py
# then open sandbox_frontend/observatory/resolution-observatory.html
```

The generator executes the real engine and rule set (A1/B1/B2, Ψ, validation) against a fixture that exercises a growth-debt materialization, a REQ/FORBID clash, a B2 SCC weld, a STUCK state, and a working prototype of the A3 proposal-boundary evaluation — the speculative copy, the seven-check gauntlet, and engine-controlled acceptance. It writes a `replay_digest` hash into the trace; regenerating from the same fixture reproduces that hash exactly, which is the practical proof that the run is replayable, not just logged.

The page itself is a scrubbable timeline: drag through the run and watch the constraint graph, the Ψ-descent chart, the evidence log, and the proposal ledger all advance together. Nothing in it is mocked or hand-animated.

## Source Dump Workflow

For handing context to another model or starting a fresh session, generate the curated knowledge pack:

```bash
bash scripts/dev/source-dump.sh
```

That writes `~/Desktop/LOOMFILES2.md` plus `~/Desktop/LOOMFILES2.md.gz`.

Use full archival mode only when you truly need byte-heavy completeness:

```bash
bash scripts/dev/source-dump.sh --full /home/ghostmonday/Desktop/Loom-source-dump.txt
```

Curated mode deduplicates content-identical text files, skips empty scratch JSON, records recent commits and git status, and keeps the dump focused on files a new model can absorb quickly.

### Terminal UI (Greenfield / Demo)

```bash
bash scripts/dev/phase0-demo.sh
# Open http://127.0.0.1:8080
```

The terminal presents a full product loop:

```text
Intent → Blueprint → Swarm → Sprint → Merge → Deliverable
```

Scope presets:

| Preset | What runs |
| -------- | ----------- |
| Backend only | 1 sprint: generate backend code |
| Frontend only | 1 sprint: generate frontend code |
| Backend + Frontend | 2 sprints: backend → context-loaded frontend |
| Full Stack | 3 sprints: backend → frontend → testing |
| Backend + Testing | 2 sprints: backend → test suite |

---

## Repository Structure

```text
.
├── aoc-cli/aoc_cli/                  # CLI, graph analysis, planning, merge commands
├── aoc_supervisor/aoc_supervisor/    # API, Intent Forge, synthesis, governance
├── docs/                             # Architecture, guides, case studies, specs
│   ├── architecture/                 # Architecture decision records and blueprints
│   ├── guides/                       # How Loom thinks, why Loom exists
│   ├── reference/                    # Reference documentation
│   ├── specs/                        # Technical specifications
│   └── campaign/                     # Case studies, legal, patent materials
├── examples/                         # Example targets and demonstrations
│   └── tiny-python-service/          # Reference target for gateway testing
├── tests/                            # 795+ tests: unit, integration, contract, E2E
│   ├── conftest.py                   # Pytest fixtures (mock grid, fake reasoning)
│   └── test_*.py                     # Per-module test suites
├── scripts/                          # CI, development, and demo scripts
│   ├── ci/                           # CI pipeline scripts
│   ├── dev/                          # Development helpers and demos
│   └── ops/                          # Operational maintenance scripts
├── ui/                               # Intent maps, FRG visualizations, terminal assets
├── sandbox_frontend/                 # Standalone frontend sandbox and observatory pages
├── vaults/                           # Legacy memory FS and vault storage
├── pyproject.toml                    # Project build, linting, and test configuration
└── README.md
```

Key implementation files:

- `aoc-cli/aoc_cli/cli.py` — `loom` CLI entrypoint (Typer)
- `aoc-cli/aoc_cli/gravity.py` — Ollivier-Ricci curvature computation engine
- `aoc-cli/aoc_cli/giv.py` — Agent Intent Vector schema and enforcement
- `aoc_supervisor/aoc_supervisor/loom_pipeline.py` — Handoff and teleology sequencing
- `aoc_supervisor/aoc_supervisor/intent_forge_service.py` — Intent → blueprint synthesis
- `aoc-cli/aoc_cli/helpers/council.py` — Multi-agent handoff transaction bus
- `aoc_supervisor/aoc_supervisor/loom_blueprint_synthesizer.py` — Curvature-conditioned synthesis
- `aoc_supervisor/aoc_supervisor/loom_map_generator.py` — Deterministic contract generation
- `aoc_supervisor/aoc_supervisor/api.py` — Hosted service boundary

---

## Tests

```bash
# Run the full suite (795+ tests)
pytest

# With coverage
pytest --cov --cov-report=term-missing

# E2E golden-path validation
bash scripts/ci/acceptance.sh

# Lint
ruff check .
ruff format --check .
```

---

## Runtime State

The product and CLI are named **Loom**. During migration, legacy `.gaijinn/` state is mirrored into `.loom/`, while some current command paths retain the older directory name for compatibility.

These compatibility paths do not represent separate products. **Loom is the sole current product identity.**

The retained historical case study is at [docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md](./docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md).

---

## Status

Loom is under active development and is currently classified as alpha software. The Gaijinn-to-Loom migration remains visible in compatibility paths, fallback environment variables, internal names, and historical documentation filenames.

---

## License

Copyright © 2026 Neural Draft LLC. All Rights Reserved.

Proprietary software. See [LICENSE](./LICENSE), [PROPRIETARY.md](./PROPRIETARY.md), and [SECURITY.md](./SECURITY.md) for details.

This repository contains patent-pending and trade-secret material. Unauthorized copying, distribution, or public disclosure is prohibited.

---

## Code Deep Dive — Hot Zones for Model Ingestion

> This section collects the most algorithmically dense code in the system.
> If a model understands these zones + the connective tissue between them,
> it can reliably reconstruct the rest of the architecture.

---

## Hot Zone 1: Gravity Engine — Ollivier-Ricci Curvature

**File:** `aoc-cli/aoc_cli/gravity.py`

This is the mathematical core. It computes **directed Ollivier-Ricci curvature** on a codebase graph using Wasserstein-1 optimal transport distance (Earth Mover's Distance). Negative curvature edges (`κ < -0.30`) are "Dark Bridges" — latent couplings that standard import analysis misses.

### The Curvature Formula

```text
κ(x, y) = 1 − W₁(μ_x, μ_y) / d(x, y)
```

Where `W₁` is the 1-Wasserstein distance between probability distributions `μ_x` and `μ_y`
(risk-weighted outgoing edge distributions), and `d(x, y)` is the shortest-path distance.

### Key Snippet — Wasserstein Computation

```python
# gravity.py — core curvature engine

def _compute_ollivier_ricci_curvature(graph: nx.DiGraph) -> dict:
    curvature = {}
    for source, target in sorted(graph.edges, key=lambda e: (str(e[0]), str(e[1]))):
        # 1. Shortest path distance between source and target
        distance = nx.shortest_path_length(graph, source=source, target=target)

        # 2. Build risk-weighted probability distributions over outgoing neighbors
        support_u, prob_u = _outgoing_distribution(graph, source)
        support_v, prob_v = _outgoing_distribution(graph, target)

        # 3. Cost matrix: pairwise shortest paths between all support nodes
        cost = _cost_matrix(graph, support_u, support_v)

        # 4. Wasserstein-1 distance via optimal transport (POT library)
        wasserstein = float(ot.emd2(prob_u, prob_v, cost))

        # 5. Ollivier-Ricci curvature: 1 - (W₁ / d)
        geometric_kappa = float(1.0 - (wasserstein / distance))

        # 6. Shadow bridge detection: low-capability source → high-capability target = risk jump
        risk_jump = _is_shadow_risk_jump(graph, source, target)
        kappa = min(geometric_kappa, -1.0) if risk_jump else geometric_kappa

        curvature[f"{source}->{target}"] = {
            "curvature": kappa,
            "is_dark_bridge": bool(kappa < CURVATURE_HARD_FLOOR),  # κ < -0.30
            "is_shadow_bridge": bool(kappa < 0.0),
        }
    return curvature
```

### Explainer — Wasserstein Computation

The function visits every directed edge in the codebase graph. For each edge `(source → target)`:

1. **Distance** — How far apart are the two nodes in the directed graph? (Shortest path)
2. **Distributions** — For each node, build a probability distribution over its outgoing neighbors, weighted by `capability_level` and `side_effect_score`. A node that calls powerful (high-capability) side-effect-heavy functions gets a "riskier" distribution.
3. **Cost matrix** — Pairwise shortest-path distances between all nodes in the two distributions' supports, treating edges as undirected for connectivity.
4. **Wasserstein-1** — How much "probability mass" must be moved to transform one distribution into the other, multiplied by the distance it travels. Solved via `ot.emd2` (the POT library's Earth Mover's Distance solver).
5. **Curvature** — If `W₁` is small relative to the edge distance, the neighborhoods look similar → positive curvature (redundant paths, safe to parallelize). If `W₁` is large → negative curvature (a bottleneck/bridge, risky to split).
6. **Risk jumps** — A special case: a low-capability node calling a high-capability high-side-effect node gets curvature floored to `-1.0`, marking it as a "Shadow Bridge."

### Key Snippet — Structural Gravity

```python
# gravity.py — node gravity scoring

def _compute_structural_gravity(graph: nx.DiGraph) -> dict:
    node_count = max(graph.number_of_nodes() - 1, 1)
    gravity = {}

    for node in sorted(graph.nodes, key=str):
        in_degree = graph.in_degree(node) / node_count
        out_degree = graph.out_degree(node) / node_count
        capability_level = _node_capability(graph, node)
        side_effect_score = _node_side_effect(graph, node)

        # Weighted sum of four structural signals
        score = (0.30 * in_degree + 0.25 * out_degree +
                 0.30 * capability_level + 0.15 * side_effect_score)

        # Sparse high-capability penalty: isolated powerful nodes get ×0.25
        if (graph.degree(node) <= 1 and raw_capability >= 5.0
                and raw_side_effect <= 0.25):
            score *= 0.25
        # Outgoing-degree floor: nodes with out-edges never fall below threshold
        elif score < GRAVITY_HARD_FLOOR and graph.out_degree(node) > 0:
            score = GRAVITY_HARD_FLOOR

        gravity[str(node)] = {
            "gravity": float(score),
            "automatic_rejection": bool(score < GRAVITY_HARD_FLOOR),
        }
    return gravity
```

### Explainer — Structural Gravity

"Gravity" is a composite per-node score that answers: *how structurally important is this node in the codebase?* It's a weighted combination of:

- **In-degree** (30%) — How many other files depend on it
- **Out-degree** (25%) — How many files it depends on
- **Capability** (30%) — Its domain power level (e.g., a billing handler scores higher than a utility)
- **Side-effect score** (15%) — How many mutations/writes it performs

Two special cases: isolated high-capability nodes (sleeper agents) get penalized 75%, and nodes with outgoing edges that somehow scored below 0.20 get clamped up (they clearly have influence, so the floor is a safety net).

### Key Snippet — Risk-Weighted Distributions

```python
# gravity.py — probability distribution over outgoing neighbors

def _outgoing_distribution(graph, node):
    neighbors = sorted(graph.successors(node), key=str)
    support = neighbors if neighbors else [node]  # self-loop if isolated
    weights = np.array([_risk_weight(graph, item) for item in support], dtype=float)
    total = float(weights.sum())
    if total <= 0.0:
        return support, np.full(len(support), 1.0 / len(support), dtype=float)
    return support, weights / total

def _risk_weight(graph, node):
    # Risk = α · capability + β · side_effect
    return (CAPABILITY_RISK_ALPHA * _node_capability(graph, node)
            + SIDE_EFFECT_BETA * _node_side_effect(graph, node))
```

### Explainer — Risk-Weighted Distributions

The outgoing distribution from a node is not uniform — it's weighted by the "risk" of each neighbor. Risk = `0.70 × capability + 0.30 × side_effect`. This means the Wasserstein distance will be *more sensitive* to edges that connect high-risk nodes. A low-risk node with neighbors that are all low-risk has a very different distribution from a low-risk node that calls into a high-risk subsystem — and curvature will catch that difference.

---

## Hot Zone 2: Blueprint Planner — Dark Bridge Welds

**File:** `aoc-cli/aoc_cli/blueprint.py`

This transforms the curvature metrics into executable work units. The critical operation is **atomic block formation** via Union-Find: every pair of files connected by a Dark Bridge must be welded into a single work unit so no two agents ever work on them in parallel.

### Key Snippet — Atomic Block Welding

```python
# blueprint.py — Union-Find & dark bridge welding

class _UnionFind:
    def __init__(self, items):
        self._parent = {item: item for item in items}

    def find(self, item):
        parent = self._parent[item]
        if parent != item:
            self._parent[item] = self.find(parent)  # path compression
        return self._parent[item]

    def union(self, left, right):
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        # Deterministic: smaller root wins (lexicographic string sort)
        if root_left < root_right:
            self._parent[root_right] = root_left
        else:
            self._parent[root_left] = root_right

    def components(self):
        buckets = {}
        for item in sorted(self._parent):
            root = self.find(item)
            buckets.setdefault(root, set()).add(item)
        return [frozenset(bucket) for bucket in buckets.values()]


def _atomic_blocks(node_paths, dark_edges):
    union = _UnionFind(node_paths)
    serialization_events = []
    for source, target in dark_edges:
        if source not in node_paths or target not in node_paths:
            continue
        if union.find(source) != union.find(target):
            union.union(source, target)
            serialization_events.append((source, target))
    components = sorted(union.components(),
                        key=lambda block: sorted(block)[0])
    return components, serialization_events
```

### Explainer — Atomic Block Welding

**Union-Find** groups connected components in the graph through Dark Bridge edges. Every dark bridge between two files forces them into the same equivalence class. Once all dark edges are processed, each connected component becomes an **atomic work unit** — single-threaded, never parallel-split.

The critical point: if file A has a dark bridge to B, and B has a dark bridge to C, then A, B, and C are all welded into one block — even if A and C have no direct dark bridge. This captures transitive coupling that a pairwise analysis would miss.

### Key Snippet — Convex Hull Over-Weld Prevention

```python
# blueprint.py — SCC-aware chunking to prevent over-welding

def _refine_grouped_blocks(grouped, graph):
    """Prevent Cascading Convex Hull Over-Welding by capping parallel group sizes."""
    refined = []
    threshold = _convex_hull_welding_threshold()  # default 12

    for key, paths in sorted(grouped.items()):
        if len(paths) <= threshold:
            refined.append((key, paths))
            continue

        # Build sub-graph and find SCCs to avoid slicing cycles
        sub_g = nx.DiGraph()
        sub_g.add_nodes_from(paths)
        sub_g.add_edges_from([(s, t) for s, t in group_edges
                              if s in paths and t in paths])

        sccs = sorted([sorted(list(scc)) for scc in nx.strongly_connected_components(sub_g)],
                      key=lambda x: x[0])

        current_chunk = []
        for scc in sccs:
            if len(current_chunk) + len(scc) > threshold and current_chunk:
                refined.append((key, current_chunk))
                current_chunk = list(scc)
            else:
                current_chunk.extend(scc)
        if current_chunk:
            refined.append((key, current_chunk))
    return refined
```

### Explainer — Convex Hull Over-Weld Prevention

When many files with similar risk/language/directory are grouped together, the group can become too large for a single agent. But you can't just chunk them arbitrarily — that could slice through a cyclic dependency group. This function uses **Tarjan's SCC decomposition** to find the atomic cycle clusters, then chunks *between* them at the threshold boundary, preserving all intra-cycle integrity.

### Key Snippet — Cycle Weld Resolution

```python
# blueprint.py — dependency cycle welding

def _resolve_work_units_and_dependencies(work_units, graph, metrics, giv, node_risks, *, handoff_gateways):
    units = list(work_units)
    while True:
        dependencies = _dependencies(units, graph, metrics, handoff_gateways=handoff_gateways)
        units = _apply_dependencies_to_units(units, dependencies)
        dep_graph = _dependency_graph_from_mapping(dependencies, [u.id for u in units])

        # Check for cycles — if found, weld the cycle participants into one block
        cycle = _find_dependency_cycle(dep_graph, [u.id for u in units])
        if cycle is None:
            return _renumber_work_units(units, dependencies)

        # Merge all cycle participants into one atomic work unit
        units = _weld_cycle_work_units(units, set(cycle), giv, node_risks)
        # Loop: recompute dependencies on the reduced set — may expose new cycles
```

### Explainer — Cycle Weld Resolution

This is the **cycle resolution fixpoint**. After computing the dependency DAG between work units, any cycle means those units cannot be ordered — so they get welded into one atomic block. This process iterates: welding may reduce the graph enough that a new cycle is exposed, which gets welded in turn, until the graph is acyclic. Each iteration is guaranteed to strictly decrease the number of work units, so it terminates.

---

## Hot Zone 3: Resolution Engine v3 — Deterministic Constraint Resolution

**Files:** `aoc-cli/aoc_cli/resolution_v3/` (engine.py, graph.py, potential.py, rules.py, scc.py)

The resolution engine is a **deterministic rewrite system** for constraint graphs. It takes a graph of nodes (with status: KNOWN, LATENT_UNRESOLVED, REJECTED) and edges (with modality: REQ, FORBID, PARTIAL) and applies rewrite rules until it reaches a **canonical** (valid + stable) state or faults.

### Key Snippet — The Engine Loop with Psi Descent Proof

```python
# resolution_v3/engine.py — main resolution loop

class Engine:
    def run(self, max_steps=200):
        self._seed_worklist()

        step = 0
        trace = []

        # Compute initial Psi (termination metric)
        psi_previous = self.cg.psi()
        trace.append((0, psi_previous))

        while step < max_steps:
            locus = self.worklist.pop()
            if locus is not None:
                match = self.applicable_rule(locus)
                if match is None:
                    continue
                kind, payload = match
                self._apply_local_rule(kind, payload)
            # B2 (global) runs only after local worklist drains
            elif not apply_b2(self.cg, self.worklist):
                break

            step += 1
            psi_new = self.cg.psi()

            # TERMINATION PROOF: each rewrite must strictly lower Psi
            if not (psi_new < psi_previous):
                return self._report(ENGINE_FAULT, step, trace,
                                    fault_detail=f"Psi did not decrease")

            trace.append((step, psi_new))
            psi_previous = psi_new

        return self._report(
            self._evaluate_status(self.cg.is_valid(), self.cg.is_stable(self)),
            step, trace
        )
```

### Explainer — The Engine Loop with Psi Descent Proof

The engine is a **priority-ordered rewrite system** with a lexicographic termination proof:

1. **Seed** the worklist with all nodes and edges (sorted deterministically)
2. **Pop** a locus (node or edge) from the worklist
3. **Match** the applicable rule: A1 (growth → instantiate), A2/D1 (singleton → KNOWN), B1 (clash detection)
4. **Apply** the rule, which may enqueue new loci
5. **When local worklist drains**, run B2 (global SCC violation welding)
6. **Check Psi decreased** strictly — if not, fault (means a rewrite didn't make progress)

Psi is a 4-tuple `(growth_debt, unresolved_debt, cyclic_debt, clash_pairs)` — a lexicographic measure of "how unresolved the graph is." The proof that the engine terminates depends on every rewrite strictly lowering at least one component without raising earlier ones.

### Key Snippet — Psi Potential Function

```python
# resolution_v3/potential.py — lexicographic termination metric

def psi(cg) -> tuple[int, int, int, int]:
    # TERMINATION CONTRACT: tuple order is part of the proof.
    return (growth_debt(cg), unresolved_debt(cg), cyclic_debt(cg), clash_pairs(cg))

def growth_debt(cg):
    # Component 1: active REQ edges whose target doesn't exist yet
    return sum(1 for edge in cg.active_edges()
               if edge.modality == Modality.REQ and edge.v not in cg.nodes)

def unresolved_debt(cg):
    # Component 2: LATENT_UNRESOLVED nodes + active PARTIAL obligations
    latent = sum(1 for node in cg.nodes.values()
                 if node.status == Status.LATENT_UNRESOLVED)
    partial = sum(1 for edge in cg.active_edges()
                  if edge.modality == Modality.PARTIAL)
    return latent + partial

def cyclic_debt(cg):
    # Component 3: quadratic mass of acyclicity-violating SCCs
    return sum(len(scc) ** 2 for scc in find_violating_sccs(cg))

def clash_pairs(cg):
    # Component 4: each REQ/FORBID pair on the same (u, v, label) is independent debt
    ...
    return sum(req_count * forbid_count for each (u, v, label) pair)
```

### Explainer — Psi Potential Function

Psi is a **lexicographic well-order** — the engine can't loop forever because:

- **A1** (materialize a missing target node) reduces `growth_debt` (component 1)
- **A2/D1** (resolve a singleton-domain LATENT node to KNOWN) reduces `unresolved_debt` (component 2)
- **B1** (deactivate a REQ that clashes with a FORBID) may reduce `clash_pairs` (component 4)
- **B2** (weld an SCC) reduces `cyclic_debt` (component 3)

If a rewrite doesn't lower Psi, the engine faults intentionally — it's a proof failure, not a silent hang.

### Key Snippet — Rule Application (A1: Materialize Target)

```python
# resolution_v3/rules.py — A1: materialize a required but absent node

def apply_a1(cg, worklist, edge):
    # Aggregate target domain from all active incoming REQ edges
    target_domain = _aggregate_target_domain(cg, edge.v)

    # Materialize the target (always — this lowers growth_debt)
    cg.add_node(Node(id=edge.v, status=Status.LATENT_UNRESOLVED,
                     domain=target_domain.domain))

    if target_domain.undeclared_labels:
        detail = f"undeclared labels={list(target_domain.undeclared_labels)}"
    elif target_domain.domain:
        detail = f"intersected domain={sorted(target_domain.domain)}"
    else:
        detail = "contradictory declared domains"  # will get stuck later

    cg.log.append(f"[A1] introduced latent node '{edge.v}'...; {detail}")

    # Requeue closure: target may now be resolvable, and edges may expose clashes
    _requeue_target_closure(cg, worklist, edge.v)
```

### Explainer — Rule Application (A1: Materialize Target)

When a REQ edge references a target that doesn't exist in the graph, A1 creates it as a `LATENT_UNRESOLVED` node. The domain is the **intersection** of all incoming REQ edge labels' type constraints. For example, if one edge says `edge.v` "writes_to" a `log_sink`, and another says it "calls" a `service`, the intersection is empty → contradictory → the node will remain STUCK. If the labels are undeclared in the schema, that's tracked separately.

### Key Snippet — B2: SCC Welding

```python
# resolution_v3/rules.py — B2: weld a cycle into a composite node

def apply_b2(cg, worklist):
    violating = cg.find_violating_sccs()
    if not violating:
        return False

    scc = violating[0]  # canonical: first violating SCC
    members = sorted(scc)

    if len(members) == 1:
        _remove_singleton_self_loop(cg, worklist, members[0])
        return True

    composite_id = cg.allocate_composite_id(members)
    composite_layer = min(n.layer for n in cg.nodes[m] if n.layer)

    # Rewire all edges: endpoints in SCC → point to composite
    for edge in cg.edges:
        if edge.u in scc: edge.u = composite_id
        if edge.v in scc: edge.v = composite_id

    # Internal REQ edges are absorbed (active → False)
    for edge in cg.edges:
        if (edge.u == composite_id and edge.v == composite_id
                and edge.modality == Modality.REQ):
            edge.active = False

    # Remove member nodes, add composite
    for member in members:
        del cg.nodes[member]
    cg.add_node(Node(id=composite_id, status=Status.KNOWN,
                     type="composite", layer=composite_layer))

    cg.watch.rebuild()  # invalidated by endpoint rewrites

    worklist.push(Locus.node(composite_id), URGENT)
    for index in touched_indices:
        worklist.push(Locus.edge(index), URGENT)
    return True
```

### Explainer — B2: SCC Welding

When SCCs violate an acyclic layer constraint, B2 welds them. The operation: all member nodes are replaced with a single `composite` node, all edges are rewired, internal REQ edges are absorbed, and the watch index is rebuilt. The composite inherits the minimum layer and any ROOT/SINK authority from its members. After B2, the engine re-checks stability — welding may expose new violations in the reduced graph.

### Key Snippet — Iterative Tarjan SCC (Deterministic)

```python
# resolution_v3/scc.py — iterative Tarjan (no recursion depth issues)

def tarjan_scc(adj, all_nodes):
    index_counter = 0
    stack = []
    lowlink = {}
    index = {}
    on_stack = set()
    result = []

    for node_id in sorted(all_nodes):  # deterministic root order
        if node_id in index:
            continue
        frames = []
        frames.append(_Frame(node_id, sorted(adj.get(node_id, []))))

        while frames:
            frame = frames[-1]
            if frame.next_neighbor < len(frame.neighbors):
                neighbor = frame.neighbors[frame.next_neighbor]
                frame.next_neighbor += 1
                if neighbor not in index:
                    frames.append(_Frame(neighbor, sorted(adj.get(neighbor, []))))
                elif neighbor in on_stack:
                    lowlink[frame.node_id] = min(lowlink[frame.node_id], index[neighbor])
                continue

            frames.pop()
            if lowlink[frame.node_id] == index[frame.node_id]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.remove(member)
                    component.append(member)
                    if member == frame.node_id:
                        break
                result.append(frozenset(component))
            if frames:
                parent = frames[-1].node_id
                lowlink[parent] = min(lowlink[parent], lowlink[frame.node_id])
    return result
```

### Explainer — Iterative Tarjan SCC (Deterministic)

This is an **iterative** Tarjan SCC algorithm — no recursion, so no Python recursion limit issues even on very large graphs. Critical design choices for determinism:

- Nodes are visited in **sorted order** (canonical root order)
- Neighbors are **sorted** before traversal (adjacency order doesn't depend on insertion)
- SCCs are returned in **discovery order**, which is deterministic given the above

Iterative Tarjan uses an explicit frame stack with an index into each node's neighbor list, mirroring the recursive version's behavior exactly but without function call overhead or depth limits.

---

## Hot Zone 4: Intent Forge — Session Orchestration

**File:** `aoc_supervisor/aoc_supervisor/intent_forge_service.py`

The Intent Forge manages the **intent→blueprint pipeline**: asking adaptive questions, analyzing answers, detecting contradictions, and compiling the final executable blueprint. It's a state machine with idempotent operations.

### Key Snippet — Answer Processing with Analysis

```python
# intent_forge_service.py — processing a user answer

def _apply_answer_to_state(self, state, *, question_id, answer, domain, conflict_resolution=False):
    self._record_question_answer(state, question_id=question_id,
                                 answer=answer, domain=domain)

    # Run LLM analysis to extract claims from the answer
    claim_ids = self._run_analysis_and_merge_claims(
        state, question_id=question_id, answer=answer, domain=domain
    )

    # Update confidence metrics and blueprint graph
    self._update_domain_metrics_and_graph(state, answer=answer,
                                          domain=domain, claim_ids=claim_ids)

    # Auto-resolve contradictions if in conflict resolution mode
    if conflict_resolution:
        self._resolve_contradictions(state, answer=answer)

    self._record_acceptance_decisions(state, answer=answer, domain=domain)
    state["current_question"] = None
```

### Key Snippet — Contradiction Detection & Merge

```python
# intent_forge_service.py — hands off to conflict_resolver module

def _handle_contradictions(self, session_id, state, question_id, expected_version):
    merge_contradictions(state, detect_contradictions(state))
    unresolved = [c for c in state.get("contradictions", [])
                  if isinstance(c, dict) and not c.get("resolved")]
    if unresolved:
        state["session_status"] = "CONFLICT_RESOLUTION"
        primary = unresolved[0]
        # Present the contradiction back to the user for resolution
        state["current_question"] = {
            "question_id": question_id,
            "domain": "conflict_resolution",
            "text": f"Resolve contradiction: {primary.get('description')}",
            "options": resolution_options(primary, state),
        }
        return public_session_view(state)
    return None
```

### Explainer — Contradiction Detection & Merge

The forge session lifecycle: `CREATED → QUESTIONING → CONFLICT_RESOLUTION → VALIDATING → FINAL_CONFIRMATION → FINALIZING → FINALIZED → HANDED_OFF`. Each answer triggers LLM-powered analysis that extracts `facts`, `inferences`, and `assumptions` as structured claims. Detected contradictions pause the session and present resolution options. The entire state machine is idempotency-keyed, so replaying a request returns the existing result.

---

## Hot Zone 5: Blueprint Synthesizer — Gravity + Projection Fusion

**File:** `aoc_supervisor/aoc_supervisor/loom_blueprint_synthesizer.py`

Bridge between the API-level Intent Forge and the CLI-level blueprint planner. Takes a forged session's executable projection, runs gravity curvature on it, then tries **two strategies** — atomic weld vs. handoff partition — and picks the one with fewer residual dark bridges.

### Key Snippet — Strategy Selection

```python
# loom_blueprint_synthesizer.py — dual-strategy synthesis

def synthesize_blueprint(request, *, forge_service=None):
    # ...load forge state, verify HANDED_OFF status...

    graph = _projection_graph(executable_projection)
    metrics = compute_gravity_and_curvature(graph)

    # Try both strategies, pick the one with fewer remaining dark bridges
    candidates = []
    for strategy, handoff_gateways in [("atomic_weld", False),
                                        ("handoff_partition", True)]:
        plan = generate_blueprint(graph, metrics, giv,
                                  handoff_gateways=handoff_gateways).to_dict()
        candidates.append((_remaining_dark_bridge_count(plan, dark_edges),
                          strategy, plan))

    # Pick the strategy that minimizes residual dark bridges
    dark_bridge_count, strategy, gravity_plan = min(
        candidates, key=lambda c: (c[0], c[1])
    )

    executable_projection.update(gravity_plan)
    executable_projection["synthesis_strategy"] = strategy
```

### Explainer — Strategy Selection

The synthesizer doesn't guess which strategy to use — it runs **both** and picks the one that leaves fewer dark bridges uncontained. Atomic weld fuses dark bridge pairs into single work units (serializes them). Handoff partition keeps them separate but inserts a governance handoff ticket requirement. The metric `_remaining_dark_bridge_count` counts how many dark bridge pairs cross work unit boundaries after partitioning — lower is better.

---

## Hot Zone 6: Map Generator — Topological Action Ordering

**File:** `aoc_supervisor/aoc_supervisor/loom_map_generator.py`

Generates a deterministic action execution order from teleology + topology data using **heap-based Kahn's algorithm** with structural rank as tiebreaker.

### Key Snippet — Topological Sort with Heap Tiebreaker

```python
# loom_map_generator.py — topological ordering with structural rank

def _topological_order(capabilities, structural_rank):
    indegree = {cid: len(c["depends_on"]) for cid, c in capabilities.items()}
    dependents = {cid: [] for cid in capabilities}
    for cid, c in capabilities.items():
        for dep in c["depends_on"]:
            dependents[dep].append(cid)

    # Ready set as heap: (structural_rank, capability_id)
    ready = [(structural_rank[cid], cid)
             for cid, deg in indegree.items() if deg == 0]
    heapq.heapify(ready)

    ordered = []
    while ready:
        _, cid = heapq.heappop(ready)
        ordered.append(cid)
        for dep in dependents[cid]:
            indegree[dep] -= 1
            if indegree[dep] == 0:
                heapq.heappush(ready, (structural_rank[dep], dep))

    if len(ordered) != len(capabilities):
        raise ValueError(f"dependency cycle detected: {cyclic}")
    return ordered
```

### Explainer — Topological Sort with Heap Tiebreaker

Kahn's algorithm with a **heap** instead of a simple queue ensures determinism: when multiple capabilities become ready simultaneously, the one with better structural rank (derived from topology placement in the codebase graph) executes first. This guarantees reproducible ordering regardless of dict iteration order.

---

## Hot Zone 7: MOAT — Static Prompt Profiler

**File:** `aoc-cli/aoc_cli/moat.py`

The MOAT (Model Output Adversarial Testing) profiler parses a natural language prompt using **only static keyword maps** — no ML, no LLM calls. Maps prompts to capabilities, risk flags, prohibitions, and recommended file paths.

### Key Snippet — Keyword-to-Capability Mapping

```python
# moat.py — deterministic capability profiling

CAPABILITY_KEYWORDS = {
    "auth_security": ("auth", "authentication", "jwt", "oauth",
                      "permission", "rbac", "session", "sso"),
    "billing_payment": ("billing", "checkout", "invoice", "payment",
                        "stripe", "subscription", "refund"),
    "destructive_operations": ("delete", "destroy", "drop", "force push",
                               "git reset", "purge", "rm -rf", "truncate", "wipe"),
    "frontend": ("css", "html", "react", "vue", "tailwind", "ui", "ux",
                 "terminal", "streaming", "sse"),
}

DANGEROUS_PHRASES = {
    "rm -rf": ("no recursive force deletion",),
    "drop database": ("no database dropping",),
    "git reset --hard": ("no hard reset",),
    "force push": ("no force push",),
}

def parse_prompt(prompt):
    normalized = re.sub(r"\s+", " ", prompt.casefold()).strip()
    capabilities = set()
    for capability, keywords in CAPABILITY_KEYWORDS.items():
        if _contains_any(normalized, keywords):
            capabilities.add(capability)
    # ... build MoatProfile with capabilities, risk_flags, prohibitions, paths
```

### Explainer — Keyword-to-Capability Mapping

Pure static analysis. No API calls, no embeddings, no model inference. The profiler normalizes the prompt, checks each word against fixed keyword tuples, and builds a capability profile. Dangerous phrases attach additional prohibitions (e.g., "rm -rf" triggers "no recursive force deletion"). This runs in microseconds and is fully deterministic — used for early guard binding before any work begins.

---

## Hot Zone 8: GIV — Agent Intent Vector Schema

**File:** `aoc-cli/aoc_cli/giv.py`

The GIV is a **worker-scoped RBAC contract** enforced at runtime. Every AI agent receives one, and the merge gate checks every filesystem mutation against it.

### Key Snippet — GIV Schema & Enforcement

```python
# giv.py — Agent Intent Vector

@dataclass(frozen=True)
class GIV:
    worker_id: str
    allowed_paths: tuple[str, ...]        # exactly these files
    denied_paths: tuple[str, ...]         # never touch these
    allowed_commands: tuple[str, ...]      # permitted shell commands
    denied_commands: tuple[str, ...]       # forbidden shell commands
    capabilities: tuple[str, ...]          # domain strengths
    prohibitions: tuple[str, ...]          # safety rules
    invariants: tuple[str, ...]            # post-conditions to preserve
    structural_tokens: Mapping[str, bool]  # scope_strict, no_sibling_trespass, handoff_only
    sibling_denied_paths: tuple[str, ...]  # paths owned by other workers

    def __post_init__(self):
        # Validate: worker_id required, allowed_paths non-empty
        # git push is ALWAYS denied (structural invariant)
        # Merge with DEFAULT_PROHIBITIONS safety floor
        ...

@dataclass(frozen=True)
class HandoffTicket:
    """Cross-boundary mutation request between workers."""
    ticket_id: str
    source_worker_id: str
    target_work_unit_id: str
    target_file: str
    required_mutation_context: str
    status: str = "pending"        # pending → accepted/rejected
    resolution_commit: str | None = None
```

### Explainer — GIV Schema & Enforcement

The GIV is not just data — it's a **boundary object** with defined semantics:

- `allowed_paths` is the exclusive write scope. Workers cannot touch any file outside it.
- `denied_commands` always includes `git push` (structural invariant against force-push contamination).
- `structural_tokens` controls `scope_strict` (reject changes outside allowed paths), `no_sibling_trespass` (never cross into sibling paths), and `handoff_only` (only communicate via tickets).
- `HandoffTicket` is how a worker requests a controlled mutation on a sibling's territory.

---

## Hot Zone 9: Stealth Layer — Customer vs. Operator Mode

**File:** `aoc-cli/aoc_cli/helpers/stealth.py`

Controls the **surface vocabulary** presented to users. In "stealth mode" (default), proprietary math terminology is translated to safe customer language. In "operator mode," the raw curvature/gravity artifacts are exposed.

### Key Snippet — Vocabulary Rewriting

```python
# helpers/stealth.py — terminology sanitization

def stealth_mode():
    return not operator_mode()

def sanitize_blocked_reason(reason):
    if not stealth_mode():
        return reason
    # "shadow bridge" → "coupling review"
    # "automatic rejection" → "integrity floor"
    # "rejected node" → "flagged file"
    ...
```

### Explainer — Vocabulary Rewriting

The entire customer-facing surface is filtered through this layer. "Shadow Bridge" becomes "Coupling Review," "Dark Bridge" becomes "Structural Weld," "automatic rejection" becomes "integrity floor trip." The underlying math doesn't change — just the vocabulary. This lets operators use the full technical vocabulary while customers get plain language.

---

## Connective Tissue: How the Hot Zones Wire Together

### End-to-End Pipeline Flow

```text
User prompt
    │
    ▼
[MOAT Profile] ───────────────── static keyword → capability, risk, prohibition
    │
    ▼
[Intent Forge] ───────────────── adaptive Q&A → claims/requirements → blueprint graph
    │ session state machine
    ▼
[Intent Blueprint] ───────────── greenfield keyword stream → layer 0 domain rules
    │
    ▼
[Scan] ───────────────────────── AST extraction → layer 1 reactive structure
    │
    ▼
[Gravity Engine] ─────────────── κ curvature computation → dark bridge detection
    │
    ▼
[Blueprint Planner] ──────────── Union-Find welding → work unit partitioning
    │
    ▼
[Synthesizer] ────────────────── dual-strategy (weld vs handoff) → executable projection
    │
    ▼
[GIV Assignment] ─────────────── worker-scoped RBAC contracts
    │
    ▼
[Run Grid / Grid Spawn] ──────── isolated worktrees + agent injection
    │
    ▼
[Collect / Validate / Merge] ─── GIV enforcement, scope check, governance scoring
    │
    ▼
[Continuation Handoff] ───────── handoff.json + handoff.md for next session
```

### Key Snippet — Runtime Pipeline (End-to-End Deterministic)

```python
# runtime_pipeline.py — minimal deterministic pipeline

def run_pipeline(payload):
    normalized_input = _normalize_input(payload)
    graph = build_constraint_graph(normalized_input)
    resolution = resolve(graph)  # engine.run()
    units = derive_work_units(resolution)
    executions = (execute_units(units)
                  if resolution["status"] == EngineStatus.CANONICAL else [])
    return {
        "input_digest": hashlib.sha256(canonical_json),
        "resolution": serialized,
        "work_units": units,
        "executions": executions,
        "valid": resolution["valid"],
        "stable": resolution["stable"],
    }
```

### Explainer — Runtime Pipeline (End-to-End Deterministic)

This is the **narrow deterministic path** through the system: normalize input (sorting all dicts, enforcing schemas) → build constraint graph → resolve (deterministic engine loop) → extract work units → execute mock steps. One input always produces one output — no randomness, no LLM calls, no scheduler cleverness. This path is the "boring correct core" that the rest of the system builds around.

---

## Summary: What Fable Needs

| Knowledge Area | Files | What It Encodes |
| --- | --- | --- |
| **Gravity math** | `gravity.py` | Ollivier-Ricci curvature, Wasserstein-1 OT, risk-weighted distributions, Dark Bridge detection |
| **Blueprint partitioning** | `blueprint.py` | Union-Find atomic welds, SCC-aware chunking, cycle resolution fixpoint, convex hull prevention |
| **Constraint resolution** | `resolution_v3/*.py` | Deterministic rewrite system, Psi lexicographic termination proof, A1/A2/B1/B2 rules, iterative Tarjan |
| **Intent forge** | `intent_forge_service.py` | Adaptive Q&A state machine, contradiction detection & resolution, idempotent session store |
| **Synthesis** | `loom_blueprint_synthesizer.py` | Dual-strategy selection (weld vs. handoff), curvature + projection fusion |
| **Map generation** | `loom_map_generator.py` | Heap-based topological ordering, structural rank tiebreaking |
| **GIV contracts** | `giv.py` | Worker-scoped RBAC, handoff tickets, structural token enforcement |
| **MOAT profiling** | `moat.py` | Static keyword-to-capability mapping, dangerous phrase detection |
| **Stealth layer** | `helpers/stealth.py` | Customer-safe vocabulary rewriting, operator/stealth mode toggle |
| **Merge pipeline** | `helpers/merge.py` | GIV enforcement, trespass detection, worker merge ordering, governance scoring |
| **Handoff** | `helpers/continuation_handoff.py` | Continuation artifact generation, `handoff.json` + `handoff.md` contract schema |

The system is **internally consistent** — if Fable understands the hot zones above and the pipeline flow between them, it can infer the purpose and behavior of every other file in the repository. The interfaces are the contracts; the hot zones are the intelligence.
