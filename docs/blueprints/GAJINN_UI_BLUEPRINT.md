# GAIJINN INTERFACE BLUEPRINT: THE BRUTALIST COMMAND ENGINE

**Blueprint ID:** gaijinn-ui-v1
**Generated:** 2026-06-16
**Target:** Single-page real-time command dashboard for Gaijinn orchestration engine
**Intended for:** Composer 2.5 / Codex implementation

---

## Overview

Four functional modules mapping to the four execution phases of the Gaijinn core.
The interface is high-density, dark-themed, and optimized for information density over decorative whitespace.
Every visual element corresponds to a live engine process — nothing is mock.

---

## PHASE 1: THE INTAKE VENT (Prompt & MOAT Profiler)

Where the operation begins. Translates natural language into rigid execution constraints before agents spin up.

### Components

**A. Split Input Window**
- Left: clean text input area for the user's intent prompt
- Right: real-time reactive card panel titled `MOAT_CAPABILITY_PROHIBITION_GRID`

**B. Keyword Badge System**
- As the user types, backend tokenizes keywords against MOAT profiles
- UI panel instantly highlights active safety constants:
  - `SCOPE_STRICT` — Blue badge
  - `NO_SIBLING_TRESPASS` — Violet badge
  - `HANDOFF_ONLY` — Amber badge
- Sensitive domain keywords (e.g., "billing", "database", "auth") flash a warning indicator

**C. Phase Transition**
- A "BEGIN ORCHESTRATION" button activates only when the prompt passes MOAT validation
- Button transitions to "ANALYZING TOPOLOGY" → redirects to Phase 2

### States

| State | Visual |
|-------|--------|
| Empty | Dim placeholder text, inactive grid |
| Typing | Badges populate/react in real-time |
| Validated | Green border, "BEGIN ORCHESTRATION" active |
| Rejected | Red border, specific prohibition highlighted |

---

## PHASE 2: THE CURVATURE TOPOLOGY SCREEN (Gravity Engine)

Before AI workers are spawned, the user visually inspects the repository risk profile.

### Components

**A. Directory Node Network**
- Localized node layout using CSS grid rows or canvas rendering
- Each file/subdirectory is a node
- Nodes connected by edges representing structural relationships

**B. Curvature Visualization**
- Files with structural gravity below threshold: grayed out, labeled `DISCONNECTED_CONTEXT_BLOCKED`
- Edges where κ < threshold: glow deep crimson, flash `DARK_BRIDGE_DETECTED` warning
- Normal edges: cyan, stable

**C. The Interactive Controls**
- `ENFORCE_SURGERY_RULE` toggle switch
  - When ON: visually merges dark bridge endpoints into a single highlighted execution block (WorkUnit)
  - Shows exact count: "X files welded into N atomic work units"
- Zoom controls for the node network
- Toggle between "Risk View" and "Work Unit View"

**D. Work Unit Summary Panel**
- Card showing total work units, welded blocks, parallelizable units
- Estimated agent count recommendation

### States

| State | Visual |
|-------|--------|
| Analyzing | Loading spinner over node network |
| Complete | Full interactive graph rendered |
| Surgery ON | Welded blocks highlighted in gold |
| Surgery OFF | Dark bridges shown as red edges |

---

## PHASE 3: THE LIVE COUNCIL TRACKER (Synchronization Bus)

The heart of the execution loop while agents are active inside their worktree sandboxes.

### Components

**A. Agent Grid**
- Card per agent worker, arranged in a grid
- Each card shows:
  - Worker ID (e.g., `worker-001`)
  - Current status (Running / Awaiting Handoff / Complete / Blocked)
  - Assigned work units
  - Elapsed time
  - Live log preview (last 3 lines)

**B. Council Bus Ledger**
- Chronological, vertical transaction ledger panel titled `COUNCIL_BUS_LEDGER`
- Real-time tail of the council.jsonl log
- Displays entries with dual timestamps:
  - User-local timezone (primary)
  - UTC canonical (secondary, smaller)
- Entry types:
  - `[WORKER_ID] started work unit [WU-XXX]`
  - `[WORKER_ID] → BUS: RAISED TICKET TX-HT-[HASH]` (amber pulse)
  - `[WORKER_ID] ← BUS: RECEIPT TX-HT-[HASH]` (green confirm)
  - `[WORKER_ID] completed work unit [WU-XXX]` (dim)

**C. Sprint Progress**
- Progress bar: `Work Units Complete / Total`
- Estimated time remaining
- Structural score (live-updating)

### States

| State | Visual |
|-------|--------|
| Spawning | Agent cards populate one by one |
| Running | Cards cyan, logs streaming |
| Handoff pending | Specific card pulses amber, ticket row pulses |
| Handoff resolved | Ticket row turns green, card resumes cyan |
| Blocked | Card turns red, log shows trespass details |
| Complete | All cards dim to completed state |

---

## PHASE 4: PREFLIGHT INTEGRATION FIREWALL (The Enforcer Gate)

The final validation before code enters the main branch.

### Components

**A. Convergence Score Banner**
- Massive, high-contrast header displaying: `CONVERGENCE_SCORE: 0.XXXX`
- Color-coded:
  - ≥ 0.90: Green
  - ≥ 0.70: Amber
  - < 0.70: Red

**B. Worker Validation Matrix**
- Table with all workers as rows
- Columns per worker:
  - Status icon (Pass / Fail / Partial)
  - Trespass detection count
  - Invariant violations count
  - Protected path clearance (CLAUDE.md, .gaijinn, .cursorrules)
  - Files merged / blocked

**C. Merge Summary**
- Total files merged
- Total files blocked
- Total files conflicted
- Structural governance score breakdown

**D. Deliverable Panel**
- "View Diff" button — shows diff of merged files
- "Download ZIP" button — exports merged deliverable
- "Copy Path" for each merged file
- "Start New Session" button

### States

| State | Visual |
|-------|--------|
| Validating | Spinner, partial checkmarks populating |
| Pass | Green banner, all checkmarks, CONVERGENCE_SCORE displayed |
| Partial | Amber banner, some workers blocked, explanation |
| Fail | Red banner, `IMPERMISSIBLE_MUTATION_HALT` frozen state |

---

## Full Flow: User Journey

```
┌──────────────────────────────────────────────────────────────┐
│  PHASE 1: INTAKE                                             │
│  User types intent → MOAT validates → "BEGIN ORCHESTRATION"  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  PHASE 2: TOPOLOGY                                           │
│  Graph renders → dark bridges detected → surgery toggle      │
│  → User reviews → "DEPLOY AGENTS"                           │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  PHASE 3: COUNCIL                                            │
│  Agents spawn → work units processing → handoffs resolve     │
│  → Live ledger streaming → sprint completes                 │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  PHASE 4: FIREWALL                                           │
│  Validation runs → score calculated → merge executed         │
│  → Deliverable panel shown                                   │
└──────────────────────────────────────────────────────────────┘
```

---

## Navigation

- **Top bar:** Current phase indicator (1-4) with phase name
- **Sidebar (collapsible):** Jump to any past session's results
- **Keyboard shortcuts:**
  - `Ctrl+Enter` — Submit intent / begin phase
  - `Esc` — Cancel current operation
  - `S` — Toggle surgery rule
  - `L` — Focus council ledger

---

## Visual Design Tokens

```css
:root {
  /* Colors */
  --bg-deep: #06080b;
  --bg-surface: #0c1016;
  --bg-panel: #10151c;
  --bg-hover: #161d27;
  --border: rgba(255,255,255,0.06);
  --border-strong: rgba(255,255,255,0.12);
  --cyan: #22d3ee;
  --cyan-dim: rgba(34,211,238,0.15);
  --violet: #a78bfa;
  --violet-dim: rgba(167,139,250,0.12);
  --green: #4ade80;
  --green-dim: rgba(74,222,128,0.12);
  --amber: #fbbf24;
  --red: #f87171;
  --gold: #fbbf24;
  --text: #e8edf4;
  --text-muted: #8b95a8;
  --text-faint: #5c6678;

  /* Typography */
  --font-display: 'Outfit', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

---

## Implementation Priority

1. Phase 4 — Convergence score banner + worker validation matrix (the result screen is the most demo-able)
2. Phase 1 — Intake vent with MOAT keyword badges
3. Phase 3 — Council bus ledger (live log streaming)
4. Phase 2 — Node network topology visualization (most complex rendering)
5. Full flow wiring — Phase transitions, navigation, keyboard shortcuts
6. Polish — Dark bridge animation, handoff pulse effects, merge convergence glow

---

## Data Sources (API Endpoints)

Each phase maps to existing API endpoints in `aoc_supervisor/api.py`:

| Phase | Endpoint | Purpose |
|-------|----------|---------|
| 1 | `POST /api/v1/orchestrate/prepare` | Submit intent, get MOAT validation |
| 2 | `POST /api/v1/orchestrate/swarm` | Plan with worker count |
| 2 | `GET /api/v1/analyze` | Get curvature / topology data |
| 3 | `POST /api/v1/grid/spawn` | Launch agents |
| 3 | `GET /api/v1/grid/status` | Poll agent status |
| 3 | `GET /api/v1/grid/merge/status` | Poll merge progress |
| 4 | `POST /api/v1/grid/merge` | Execute merge |
| 4 | `GET /api/v1/grid/deliverable` | Get merge results |
