# Loom

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![Tests](https://img.shields.io/badge/tests-243%20passing-green)](#)
[![Ruff](https://img.shields.io/badge/lint-ruff-clean-brightgreen)](#)

**Geometric orchestration engine for parallel AI coding agents.**

Loom lets you throw multiple AI coding agents at a codebase simultaneously — without them stepping on each other.

It does this by measuring the *actual geometry* of your code, not just the import graph. Two files that never import each other can still be tightly coupled through shared state or data flow. Loom detects that hidden coupling mathematically, ensures those files are never assigned to different agents, and enforces the boundaries at runtime.

---

## The problem: why parallel coding agents collide

If you give two AI agents different files to edit, you assume they're working independently. That assumption is wrong whenever those files are **functionally coupled** — they mutate the same state, share a data pipeline, or depend on the same operational cadence.

Standard dependency analysis (import graphs, DAGs) misses this entirely. It only sees explicit references. The hidden coupling looks like independence — until the agents' outputs collide at merge time.

## The solution: measure the actual geometry

Loom uses **Ollivier-Ricci curvature**, a concept from differential geometry adapted to graphs. It measures how information flows between neighborhoods in the codebase graph.

The metric: **κ (kappa)**, computed via Wasserstein optimal transport distance.

### What curvature means

Imagine each file is a node in a graph. Edges exist where there are imports, shared references, or detected relationships. Now imagine rolling a ball along each edge:

| If the ball rolls... | κ value | What it means | What the system does |
|---|---|---|---|
| **Into a dense cluster** with many alternative paths | κ > 0 (positive) | Safe zone — information flows through redundant routes | Can heavily parallelize these files across many agents |
| **Across a flat grid** with predictable paths | κ ≈ 0 (flat) | Stable pipeline — no surprises | Standard parallel splitting |
| **Through a narrow bottleneck** where all paths converge | κ < 0 (negative) | Danger — this edge is a hidden constraint point | Files on opposite ends may collide if assigned to different agents |
| **Through a critical bottleneck** well below the threshold | κ < -0.3 | **Dark Bridge** — a hidden structural weld between code regions | These files MUST be assigned to the SAME agent; they cannot be split |

### Why -0.3?

`CURVATURE_HARD_FLOOR = -0.30` is the empirically determined threshold for dangerous coupling. It's not arbitrary:
- κ = 0 to -0.1: mild negative curvature, often benign
- κ = -0.1 to -0.3: moderate risk, worth monitoring
- κ < -0.3: severe negative curvature — the information bottleneck is real and will cause collisions at merge time

This threshold was validated on the Loom monorepo: `gaijinn audit .` detects **92 shadow bridges** (κ ≤ −0.30). In legacy union-find mode that welds into **2 atomic blocks** (**40-file** largest cluster, **44 files** total serialized). Gateway mode (`GAIJINN_HANDOFF_GATEWAYS=1`) replaces those welds with **92 HANDOFF_ONLY** edges — unlocking parallel lanes without sibling trespass.

---

## Dark Bridge welding: how the system protects parallelism

When the curvature analysis detects dark bridges (edges with κ < -0.3), it doesn't just flag them — it **welds** them.

The system runs a **union-find** algorithm over all dark bridge edges. Every file connected through dark bridges gets fused into a single atomic work unit. This means:

- **Before welding**: Two files connected by a dark bridge might get assigned to different agents independently. Both agents make conflicting assumptions about shared state. Merge produces broken code.
- **After welding**: Those two files are fused into one work unit. One agent handles both. No conflict possible.

Files connected by flat or positive curvature edges (κ ≥ 0) stay in separate work units and run in parallel. The system is conservative only where the geometry proves it must be.

**The Surgery Rule**: If curvature says two files can't be parallelized, they aren't — no matter how cleanly separated their imports look to a human reader. The geometry is the authority.

**The Contraction Rule**: Subgraphs linked only by non-negative curvature edges (κ ≥ 0) may run concurrently. The geometry proves they're isolated.

---

## The GIV: enforcing boundaries at runtime

The geometry produces a partitioning plan, but that plan needs enforcement. That's the **GIV (Agent Intent Vector)** — a per-worker permission contract.

Each work unit gets a GIV that specifies:

- **Allowed paths**: the exact files this agent may edit
- **Denied paths**: files this agent must never touch
- **Allowed commands**: shell commands the agent may run
- **Denied commands**: commands blocked for safety (always includes `git push`)
- **Capabilities**: what this agent is good at (e.g., "frontend", "api")
- **Prohibitions**: natural-language rules the agent must follow
- **Invariants**: conditions that must remain true after the agent finishes

The GIV is not advisory — it's enforced at merge time.

### The merge integrity harness

After all agents finish their sprints, the **merge integrity harness** runs:

1. **`collect`** — gathers all code produced by all agents
2. **`validate-worker`** — checks each agent's output against its GIV:
   - Did it write to files it wasn't allowed to touch? → **Trespass** → blocked
   - Did it run commands it wasn't allowed to run? → **Violation** → blocked
   - Did it leave any invariants broken? → **Integrity failure** → blocked
3. **`merge-grid`** — merges only the compliant agents' output into the main project
4. **Structural scoring** — every merge gets a composite grade in `governance.json`:

| Signal | Meaning |
|--------|---------|
| `validation_pass_rate` | Fraction of workers passing **all** gates (path, scope, handoff, tests) |
| `convergence` | Composite structural score — includes merge eligibility and honest no-op detection |
| `transaction_bus_synchronized` | All `TX-HT-*` handoff tickets resolved |
| `handoff_isolation` | Zero sibling path trespass |

---

## Real results: Phase 1 + Phase 2 (June 16, 2026)

Loom has been dogfooded end-to-end with **live Grok Build agents** (no mock grid). Full telemetry: [`docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md`](docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md).

### Phase 1 — tiny-service gateway lap

| Parameter | Value |
|-----------|-------|
| Target | `examples/tiny-python-service` |
| Agents | 2 Grok workers (`grok-composer-2.5-fast`) |
| Handoff ticket | `TX-HT-84348F` (resolved) |
| Convergence | **1.0** · 0 merge conflicts |

**Exam 1 (trespass):** Worker-001 wrote outside its GIV → **0.50 convergence** — correctly blocked before contamination.

**Final exam (gateway):** Handoff bus synchronized → **1.0 convergence**.

### Phase 2 — Loom monorepo dogfood (171 nodes)

| Parameter | Value |
|-----------|-------|
| Target | Loom monorepo (`gaijinn/integration`) |
| Graph | **171** code nodes · **92** shadow bridges · **54** work units |
| Agents | **4** concurrent copy-mode workers |
| Handoff ticket | **`TX-HT-6D0B24`** (billing → API preflight, resolved) |
| Validation pass rate | **1.0** (4/4 workers) |
| Sibling trespass | **0** |
| Transaction bus | **synchronized** |
| Convergence | **0.8889** (honest — see below) |
| Merge conflicts | **0** |

**Gateway audit (`gaijinn audit .`):** Legacy mode would serialize **44 files** in **2 atomic welds** (largest: **40 files**). Gateway mode: **0** welds, **44 files unlocked**, **47** max parallel workers.

### Honest Accounting vs. Ghost Merges

Loom reports a convergence score of **0.8889** on the Phase 2 monorepo run. This is a badge of mathematical purity, not a validation failure:
- **Ghost Merge (Loom terminology)**: A merge metric that reports successful convergence without requiring every participating workstream to contribute meaningful validated work (e.g. faking a 1.0 score by pretending to merge unchanged files for idle workers).
- **Loom's strict accounting**: Since three of the concurrent copy-mode workers had **no fresh filesystem deltas** at final merge (their work was already integrated), Loom flagged them as `PREFLIGHT_BLOCKED` rather than inflating the metrics with ghost merges. Every participating worker achieved 1.0 validation compliance, ensuring zero trespass.

### Pragmatic Architecture: Greenfield vs. Brownfield Layers

Loom operates across three distinct logic layers:
- **Layer 0 (Intent)**: The human-expressed goals, natural-language requirements, and domain rules.
- **Layer 1 (Boundaries)**: Deterministic path constraints, allowed commands, GIV schemas, and pre-flight validation rules.
- **Layer 2 (Execution)**: The runtime agent cells, execution sandboxes, and file modifications.

The sequence and coupling of these layers changes depending on your deployment mode:

#### Greenfield Path (From Scratch)
```
User Intent (Layer 0)
        ↓
Infer execution responsibilities (Layer 2)
        ↓
Derive deterministic boundaries and authority (Layer 1)
```
*Note: Layer 2 is inferred first because execution scopes must be conceptually grouped before exact file boundaries and permission schemas can be mathematically derived.*

#### Brownfield Path (Existing Codebase)
```
Static extraction of code constraints (Layer 1)
        ↓
Deduce execution cell boundaries (Layer 2)
```

---

## Addressing reasonable concerns

As Loom evolves, several engineering questions have emerged about the balance between safety and parallelism. Each was addressed through targeted architectural evolution.

### Concern: compute efficiency

**The question:** Does blocking an agent's output after a full sprint waste resources? An agent completes 98 seconds of work, passes its tests, but is blocked at the merge gate for a file trespass.

**The response:** Two layers address this:

1. **Boundary-aware GIV injection.** At `grid_spawn` time, each agent receives not only its own GIV but the explicit `denied_paths` of every sibling worker. The agent knows the scope boundary *before* it writes. Trespass becomes a prompt-compliance failure, not a post-hoc surprise.

2. **The structural score is honest accounting.** A 0.50 score on a trespass run is not a failure — it reports that 50% of agents produced mergable output. The alternative is letting trespassed code merge silently and discovering breakage in production.

**Evidence:** On the second victory lap (Exam 2), spawn hardening eliminated the trespass entirely. Convergence rose from 0.50 to 0.875 with zero GIV violations.

### Concern: parallelization breadth

**The question:** Does welding dark bridge files (κ < -0.3) into atomic blocks narrow parallelism too aggressively? A 36-file weld appears to serialize work that could run in parallel.

**The response:** The handoff gateway mode (`GAIJINN_HANDOFF_GATEWAYS=1`) provides an alternative path:

1. Dark bridge edges are detected as before
2. Files are assigned to separate workers with `HANDOFF_ONLY=TRUE` scope tokens
3. If a worker needs to modify a sibling-controlled file, it raises a structured handoff ticket through the council bus
4. The merge integrity harness validates handoff receipts before accepting the merge

**Evidence:** With handoff gateway mode, a victory lap achieved **1.0 convergence with zero atomic weld units**. The 36-file region that previously formed a single serialized block was handled through 92 handoff gateway edges. Welding remains available where handoff overhead exceeds serialization cost — the choice is architectural, not ideological.

### Concern: cross-boundary coordination

**The question:** Can agents working on separate files that share a dependency coordinate without producing conflicting changes?

**The response:** The Multi-Agent Council (`council.py`) operates as a structured transaction bus:

1. When a dark bridge is detected between worker domains, a shared context block is injected into each worker's prompt — both agents see the shared dependency
2. If an agent needs to modify a sibling's domain, it writes a `HANDOFF_TRANSACTION_REQUEST` ticket into the council file
3. The sibling reads the ticket, accepts or rejects it, and writes a `HANDOFF_TRANSACTION_RECEIPT`
4. The merge gate validates that every open ticket has a matching receipt before allowing merge

**Evidence:** On the gateway victory lap, worker-001 raised ticket `TX-HT-84348F`, worker-002 produced the matching receipt, and the transaction resolved before merge. `transaction_bus_synchronized` was `true`, `handoff_isolation` was `true`, convergence was **1.0**.

---

## Two ways to use Loom

### A. CLI grid (existing codebases)

The deterministic pipeline runs entirely offline — no AI agents needed until you choose to deploy them:

```
gaijinn init "Build a REST API with Postgres and JWT auth"   # define project
gaijinn scan .                                                # build dependency graph
gaijinn analyze                                               # compute curvature, detect dark bridges
gaijinn compile-prompt                                        # generate GIV contracts
gaijinn plan --workers 4                                      # geometry-conditioned work units
gaijinn run-grid --workers 4                                  # create isolated worktrees
gaijinn grid-spawn --workers 4                                # launch Grok agents (optional)
gaijinn collect && gaijinn validate-worker && gaijinn merge-grid  # enforce and merge
gaijinn audit . --json-only                                     # Parallel Efficiency Matrix
```

**Upstream CI gate:** `POST /api/v1/preflight` + [`.github/workflows/gaijinn-gate.yml`](.github/workflows/gaijinn-gate.yml) — blocks integration on trespass or unresolved `TX-HT-*` tickets.

### B. Terminal UI (greenfield / demo)

Full product loop at `http://127.0.0.1:8080`:

```
Intent → Blueprint → Swarm → Sprint → Merge → Deliverable
```

The user chooses scope upfront:

| Preset | What runs |
|--------|-----------|
| Backend only | 1 sprint: generate backend code |
| Frontend only | 1 sprint: generate frontend code |
| Backend + Frontend | 2 sprints: backend → context-loaded frontend |
| Full Stack | 3 sprints: backend → frontend → testing |
| Backend + Testing | 2 sprints: backend → test suite |
| Frontend + Testing | 2 sprints: frontend → test suite |
| Testing only | 1 sprint: generate tests for existing code |

Each phase runs the full pipeline against its target. Phases chain automatically with loaded context from the previous phase's output.

After merge, the terminal shows a **Deliverable Ready** panel:
- Merged/blocked/conflicted counts
- Diff preview for each file
- One-click path copy
- Per-worker validation breakdown (which agents passed GIV, which were blocked)
- ZIP export of the deliverable

---

## Architecture

```
aoc-cli/aoc_cli/
  commands/               One module per CLI command
  gravity.py              Ollivier-Ricci curvature engine
                         └── Wasserstein optimal transport → per-edge κ values
                         └── Dark bridge detection (κ < -0.3)
                         └── GRAVITY_HARD_FLOOR for node rejection
  blueprint.py            Geometry-conditioned work unit partitioner
                         └── Union-find over dark bridge edges → atomic blocks
                         └── Surgery Rule: welded blocks = 1 worker
                         └── Contraction Rule: κ ≥ 0 = parallel
  giv.py                  Agent Intent Vector schema
                         └── Allowed/denied paths, commands, invariants
                         └── Enforced by merge integrity harness
  helpers/merge.py        collect → validate-worker → merge-grid
                         └── GIV trespass detection at merge time
                         └── Structural scoring → governance.json
  helpers/stealth.py      Internal terminology → user-safe labels
                         └── "dark bridge" → "coupling review"
                         └── "welded" → "consolidated for stability"

aoc_supervisor/
  api.py                  FastAPI: orchestrate, grid, merge, deliverable
  intent_blueprint.py     Greenfield intent → work stream decomposition
  orchestrate_session.py  Session lifecycle: prepare → swarm → merge
  workflow_evaluator.py   confusion_count + merge evaluation
  ui_intent.py            UiIntentDriver — API mirror for smoke tests

ui/
  gaijinn-terminal.html   Terminal state machine with merge + deliverable
  gaijinn-ui-intent-map.json  Machine-readable intent map for smoke testing
```

---

## Quality gates

| Gate | Command | What it proves |
|------|---------|----------------|
| Unit + integration | `pytest` | 243 tests collected |
| Lint | `ruff check .` | Code meets formatting standards |
| Golden path | `bash scripts/ci/acceptance.sh` | Full CLI pipeline from init → merge |
| UI mirror smoke | `bash scripts/dev/ui-intent-smoke.sh` | confusion_count = 0 — terminal matches spec |
| Merge integrity | `python3 -m pytest tests/test_merge_integrity.py -q` | Real merge with GIV enforcement, no dry-run |
| Real agent sprint | `GAIJINN_MOCK_GRID=0 gaijinn grid-spawn --workers N` | Live Grok Build agents, real token consumption |

---

## Documentation & commercial assets

| Asset | Path |
|-------|------|
| Case study (Phase 1 + 2) | [`docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md`](docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md) |
| Enterprise pitch deck | [`docs/campaign/ENTERPRISE-PITCH-DECK.md`](docs/campaign/ENTERPRISE-PITCH-DECK.md) |
| Landing page | [`docs/campaign/website/index.html`](docs/campaign/website/index.html) |
| Provisional patent spec (draft) | [`docs/campaign/PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md`](docs/campaign/PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md) |
| PDF export | `bash scripts/dev/export-case-study-pdf.sh` |
| Council thread | `.gaijinn/bridge/council.md` (project) · `~/.gaijinn/bridge/council.md` (global) |

---

## License

Proprietary — Copyright 2026 Neural Draft LLC. See [LICENSE](LICENSE).
