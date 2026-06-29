# Gaijinn Terminal for Grok Build — Design Notes

## Core Architecture Decisions

### 1. Model Uniformity for Execution Agents
**CONFIRMED: All coding agents MUST use the SAME model.**

Rationale:
- Blueprint interpretation must remain consistent across all parallel agents
- If agents use different models, each interprets the blueprint differently → drift → merge conflicts
- Same model = same tokenization = same structural understanding of the intent maps

### 2. Intent Map Formation
The agents that do the coding should **also** form the intent maps — UNLESS the blueprint formation is perfected to a purely algorithmic intent map.

**User's assessment:** This is NOT a good idea yet. It "is probably going to crash." The blueprint-to-intent pipeline needs to be purely algorithmic (deterministic) before agents can be trusted to form their own intent maps. Currently, that level of perfection hasn't been reached.

### 3. Model Selection UI
One global dropdown at the orchestrator level. All agents run the same model. Not per-agent.

### 4. Data-Driven Display Design (The Genius Move)
**Do NOT design the terminal output display format upfront.**

Instead:
1. First, capture RAW terminal output from every subagent cell over time
2. Aggregate the corpus — accumulate real Grok Build stdout/stderr from real sessions
3. Parse and filter — identify signal vs noise patterns
4. Design the display FROM the data — build a pure-signal view

### 5. Dynamic Grid Layout
The terminal grid adapts to agent count:

| Agent Count | Layout | Type |
|------------|--------|------|
| 1-3 | 1×N list | List view (side-scrolling single line each) |
| 4 | 2×2 grid | Square |
| 5-8 | List view (1×N) | List |
| 9 | 3×3 grid | Square |
| 10-15 | List view (1×N) | List |
| 16 | 4×4 grid | Square |
| General rule | sqrt(N) is integer → grid; else → list | Auto-detect |

**List view**: each agent occupies ONE line that side-scrolls horizontally.

### 6. The Atomic Sprint (CRITICAL — Business Model)
**Build sprints are UNSTOPPABLE once started.**

This is a product and billing constraint:
- The user pays for the **blueprint** (priced by mathematical complexity)
- Once paid, the sprint deploys agents and they run to completion
- **No cancel. No pause. No stop.** The sprint is atomic.
- The guarantee is: "architectural integrity + working code" — stopping mid-sprint breaks that guarantee

This means:
- No "cancel" button during an active sprint
- Blueprint is the contract — payment happens BEFORE agent deployment
- The sprint is a fire-and-forget transaction
- Output is delivered when all agents complete

### 7. The Stealth Math Layer
**The mathematics is INVISIBLE to the user.**

- gravity.py (Ollivier-Ricci curvature) — hidden
- moat.py (intent taxonomy parsing) — hidden  
- blueprint.py (work unit generation from topology) — hidden
- All curvature mapping, Wasserstein distances, shadow bridge detection — hidden

The user sees:
- Blueprint output (the plan — but not how it was computed)
- Agent grid (live execution)
- Final output (compiled, working code)

The user does NOT see:
- How the blueprint was formed
- The curvature values
- The AST graph topology
- The GIV contract internals
- The mathematical complexity score (that's used for pricing)

### 8. Billing Model: Mathematical Complexity
**Price is determined by mathematical complexity, NOT by tokens or time.**

The complexity metric is derived from:
- Curvature analysis of the codebase graph (κ values)
- Number of shadow bridges detected
- Number of non-overlapping work units required
- Topological complexity of the dependency graph

This means:
- Simple project (low complexity) = lower price
- Complex enterprise codebase (high curvature, many shadow bridges) = higher price
- Price is determined algorithmically, not by guessing
- The math IS the pricing engine

### 9. Terminal Constraints
- Do NOT build anything from this terminal without explicit direction
- Gaijinn is the system, Grok Build is the execution layer, not the reverse

## Grok Build Integration Points

### CLI Flags to Wire Into the Terminal

Each grid cell needs to spawn a Grok Build instance with controlled parameters:

| Parameter | Control | Notes |
|-----------|---------|-------|
| Model | Global dropdown | `grok-build` (512K) vs `grok-composer-2.5-fast` (200K) |
| Max turns | Per-agent or global | Should be generous — don't cap prematurely |
| Working directory | Auto-assigned | Each agent gets its own git worktree |
| Always approve | Global toggle | `--always-approve` for fully autonomous mode |
| Sandbox profile | Global dropdown | Execution isolation level |
| Reasoning effort | Global dropdown | low/medium/high/xhigh/max |

### Grid Cell Layout (Per-Agent View)

```
┌─────────────────────────────────────┐
│ agent: 01  [grok-build]       ●  ✔  │
├─────────────────────────────────────┤
│ worktree: ../w001                    │
│ task: api/routes.py refactor         │
│─────────────────────────────────────│
│ [live terminal output stream]        │
│                                      │
│ > Scanning files...                   │
│ > AST parsed: 47 nodes               │
│ > Writing routes...                   │
│ > Build: PASS                        │
└─────────────────────────────────────┘
```

### Orchestrator Pane (Left Side)

```
┌─────────────────────────────────────┐
│ GAIJINN COMMAND BRIDGE              │
│                                      │
│ [Global Model: grok-build        ▼] │
│ [Sandbox: default                ▼] │
│ [Reasoning: high                 ▼] │
│ [Always Approve: ☑]                │
│                                      │
│ ──── SWARM STATUS ────              │
│ Without Gaijinn: 47 merge conflicts  │
│ With Gaijinn:   0 merge conflicts    │
│                                      │
│ Sprint: ACTIVE [████████░░] 80%      │
│ (No cancel — atomic transaction)     │
│                                      │
│ [chat input...                  [➤]]│
└─────────────────────────────────────┘
```

## Composer 2.5 Fast — Architectural Recommendation

From actual Composer 2.5 Fast session (June 15, 2026):

### 3 Files to Build (In Order)

**File 1: `aoc_cli/commands/grid_spawn.py`** — ✅ PARTIAL
- ✅ Bridge that spawns Grok Build per cell (`gaijinn grid-spawn`)
- ✅ `_grid_mode(n)` function: auto-layout
- ✅ Reads worker handoffs (GIV + WORK_UNIT) → launches Grok per cell
- ✅ Saves raw output to `.gaijinn/workers/worker-NNN/output.log`
- ✅ No cancel mechanism — atomic sprint runs to completion
- 🚧 Sandbox/reasoning/always_approve CLI flags not yet exposed

**File 2: `aoc_supervisor/api.py`** — ✅ PARTIAL
- ✅ Endpoints: `/api/v1/grid/spawn`, `/api/v1/grid/stream/{cell}`, `/api/v1/grid/status`, `/api/v1/grid/logs`
- ✅ NO kill/stop endpoint — sprints are atomic
- 🚧 Request body params (sandbox, reasoning, always_approve) parsed but not yet wired into spawn
- 🚧 SSE streaming needs hardening for production load

**File 3: `gaijinn-terminal.html`** — 🚧 WIP
- 🚧 Dynamic layout engine (design complete, implementation in progress)
- 🚧 Replace demo timers with live SSE streams
- 🚧 List view: side-scrolling single-line per agent
- 🚧 Grid view: full cell per agent
- 🚧 Sprint progress bar (no cancel button)

### Output Collection Pipeline

```
Raw Grok stdout per cell
  → saved to .gaijinn/workers/worker-NNN/output.log
  → accumulated over time
  → batch analysis script finds signal patterns
  → display format optimized from real data
```

## What's Already Built

- `~/Desktop/Gaijinn/gaijinn-terminal.html` — 3x3 grid dashboard with voice input (demo timers, SSE WIP)
- `~/Desktop/Gaijinn/` — Gaijinn repo (git, commit cb76a07)
- `gravity.py` — Ollivier-Ricci curvature engine (HIDDEN from user)
- `moat.py` — Taxonomy parser (HIDDEN from user)
- `giv.py` — Agent Intent Vector contracts (HIDDEN from user)
- `blueprint.py` — Work unit generator (user sees output, not math)
- `run_grid.py` — Multi-agent handoff deployment
- `grid_spawn.py` — Grok Build bridge CLI (PARTIAL — core spawn path works)
- `aoc_supervisor/` — API gateway with grid endpoints (PARTIAL), enforcer, orchestrator
- 103 tests, 79% `aoc_cli` coverage, full E2E acceptance pipeline

## Remaining Build Order

1. ~~`aoc_cli/commands/grid_spawn.py`~~ — core done; expose sandbox/reasoning flags
2. ~~`aoc_supervisor/api.py`~~ — endpoints exist; wire request params + harden SSE
3. `gaijinn-terminal.html` — dynamic grid UI with live SSE streams

Design doc saved at: ~/Desktop/Gaijinn/grok-build-terminal-design.md
