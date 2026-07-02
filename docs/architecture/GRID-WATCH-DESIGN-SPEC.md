# Party (Grid Watch) — Design Specification

**Live mission control for parallel AI agent orchestration.**
Product name: **Party** (see `docs/reference/NAMING.md`); "Grid Watch" remains
the internal/engineering name used throughout this spec.
Companion surface to the Resolution Observatory: the Observatory replays a finished
engine run; Grid Watch shows the sprint *while it is happening* — nine or more
agents, one screen, zero mystery.

Status: design-complete, ready for build.
Palette: validated 2026-07-02 via the six-check dataviz validator
(7 categorical slots on dark surface `#1a1a19` — all checks pass; CVD floor band
mitigated by mandatory glyph + text token on every category).

---

## 1. Design doctrine

The watcher is technically sophisticated and skeptical. Every design decision
serves one of five questions they are silently asking:

| Question | Answering mechanism |
|---|---|
| "Is this real?" | Raw stdout/stderr always one click away from any abstraction; wall-clock timestamps; visible retries and stderr; no smoothing of the firehose |
| "Are they actually parallel?" | Per-agent activity sparklines; overlapping timeline blips; simultaneous pane motion |
| "Are collisions prevented?" | GIV scope badge on every pane; a trespass counter that stays at 0 *with provenance*; violations rendered loudly when they occur |
| "What does coupling cost?" | Dark-bridge markers drop full-height across all timeline lanes, vertically aligned with the system throughput band so dips are causally readable |
| "Do handoffs resolve?" | Ticket raise/receipt rendered as paired glyphs connected by a drawn arc between agent lanes; open tickets pulse until resolved |

**Core principle: abstraction with a receipt.** Every colored blip, chip, and
counter can be clicked to reveal the raw log line(s) that produced it, with
agent id, monotonic sequence number, and wall timestamp. If the UI ever shows
something the journal cannot prove, that is a defect.

---

## 2. Layout architecture

Three vertical zones on the page plane (`#0d0d0d`), panels on surface
(`#1a1a19`), 1px hairline borders `rgba(255,255,255,0.10)`, 10px radii.

```
┌────────────────────────────────────────────────────────────────────┐
│ ZONE A — STATUS RAIL (fixed, 64px)                                 │
│ sprint id · phase stepper · counters · convergence · transport     │
├────────────────────────────────────────────────────────────────────┤
│ ZONE B — THE GRID (flexible height)                                │
│ ┌──────┐ ┌──────┐ ┌──────┐                                         │
│ │ W-01 │ │ W-02 │ │ W-03 │   3×3 up to 9 agents,                   │
│ └──────┘ └──────┘ └──────┘   4×3 up to 12; ≥13 → pages             │
│ ┌──────┐ ┌──────┐ ┌──────┐   (never shrink below legibility)       │
│ │ W-04 │ │ ...  │ │ W-09 │                                         │
│ └──────┘ └──────┘ └──────┘                                         │
├────────────────────────────────────────────────────────────────────┤
│ FILTER BAR (36px) — category chips · focus presets · search        │
├────────────────────────────────────────────────────────────────────┤
│ ZONE C — THE CHRONICLE (220px default, drag-resizable 160–400px)   │
│  throughput band (24px, shared x-axis)                             │
│  SYSTEM lane · one lane per agent (14px each)                      │
│  time axis · playhead · brush layer                                │
└────────────────────────────────────────────────────────────────────┘
```

### Zone A — Status Rail
- **Sprint identity**: sprint id (mono), target repo, started-at, elapsed
  (tabular-nums, ticking).
- **Phase stepper**: SCAN → ANALYZE → PLAN → SPRINT → MERGE as a compact
  stepper; current phase in primary ink, completed in `--status-good`, future
  in muted. Mirrors the engine's actual state machine — never animated ahead
  of reality.
- **Global counters** (stat tiles, 20px/650): agents active `9/9`,
  tickets `2 open · 14 resolved`, **trespass `0`** (the flagship number;
  clicking opens the enforcement ledger), convergence (live composite,
  shown only once merge gates begin — never a fake 1.0).
- **Transport**: LIVE indicator; pause-follow; jump-to-now; session export.

### Zone B — Agent panes
Each pane is a bounded terminal with orchestration chrome:

- **Header (28px)**: state LED (see §4 status colors) · agent id `worker-004`
  (mono, 600) · model chip (`composer-2.5`) · **GIV scope badge** — hover
  reveals the full allowed/denied path contract; this badge is the visible
  containment guarantee · 60-second activity sparkline (events/s, single hue,
  no axis — a pulse, not a chart).
- **Body**: virtualized log stream, `12px/17.4px` JetBrains Mono, max ~120
  visible lines, 100k-line ring buffer per agent. Each line carries a **3px
  category rail** on its left edge (category color) plus the category's glyph
  token at line start (see §5). Uncategorized/raw lines: no rail, secondary
  ink — the firehose stays visible and honest.
- **Scroll gutter ticks**: when filters hide lines, each hidden line leaves a
  2px tick in the scrollbar gutter — filtered means *muted, never silently
  erased*.
- **Footer (22px)**: current file being written (mono, middle-truncated),
  last-event age (`2.1s ago`, goes `--status-warning` past 30s of silence,
  `--status-serious` past 120s — silence is a signal).
- **Focus mode**: click a header → that pane FLIP-expands to a 2×2 cell area;
  the others compress but remain live (parallelism must never be hidden to
  showcase one agent). Esc restores. Double-click → full-height solo with the
  other panes as a thumbnail rail.

### Zone C — The Chronicle (persistent timeline)
Top-to-bottom, all sharing one x-axis (time — one axis, always):

1. **Throughput band (24px)**: system-wide events/sec as a filled step-area,
   neutral gray fill (`#383835` at 60%), no second scale. Its only job is
   shape: when a dark bridge lands or a weld serializes work, the dip is
   *visible at the same x-position as the cause marker below*.
2. **SYSTEM lane**: orchestrator-level events — curvature analysis runs,
   dark-bridge detections, weld decisions, merge-gate verdicts, git commits.
3. **Agent lanes**: one 14px lane per agent, same vertical order as the grid
   panes (spatial correspondence is load-bearing — lane 4 is pane 4).
4. **Time axis**: 10.5px mono tabular-nums ticks; adaptive granularity
   (1s / 5s / 30s / 5m) chosen so tick density stays 6–10 per viewport.

---

## 3. Component hierarchy

```
GridWatchApp
├─ StatusRail
│  ├─ SprintIdentity · PhaseStepper · GlobalCounters(StatTile×4) · Transport
├─ AgentGrid
│  └─ AgentPane ×N
│     ├─ PaneHeader (StateLED, AgentChip, ModelChip, GivScopeBadge, ActivitySpark)
│     ├─ LogViewport (LogLine×∞ virtualized, CategoryRail, GutterTicks)
│     └─ PaneFooter (CurrentFile, LastEventAge)
├─ FilterBar
│  ├─ CategoryChip ×7 (+ StatusChip group) · FocusPresetMenu · EventSearch
├─ Chronicle
│  ├─ ThroughputBand
│  ├─ SystemLane · AgentLane ×N (EventBlip×∞, HandoffArc×open)
│  ├─ TimeAxis · Playhead · BrushLayer
│  └─ EventInspector (popover)
└─ Shared: TooltipLayer · CommandPalette(⌘K) · ReducedMotionGate
```

---

## 4. Color system

Defined as CSS custom properties; chart/category colors are **validated**, not
eyeballed. Dark-native (product family standard).

### Surfaces & ink
| Role | Value |
|---|---|
| Page plane | `#0d0d0d` |
| Panel surface | `#1a1a19` |
| Inset surface (pane bodies) | `#141413` |
| Primary ink | `#ffffff` |
| Secondary ink | `#c3c2b7` |
| Muted (axis, timestamps) | `#898781` |
| Hairline grid | `#2c2c2a` · baseline `#383835` |
| Border | `rgba(255,255,255,0.10)` |

### Content categories (categorical palette — identity, fixed slot order)
Seven semantic buckets. The categorical **red slot is deliberately unassigned**
so no neutral category can impersonate an error in a skeptic's peripheral
vision. Every category = color + glyph token + label; color is never the sole
carrier (validator floor-band requirement).

| # | Category | Color | Glyph token | Meaning |
|---|----------|-------|-------------|---------|
| 1 | `agent_reasoning` | `#3987e5` blue | `∴` | model deliberation, plans, tool choices |
| 2 | `file_write` | `#199e70` aqua | `✎` | file creation/modification events |
| 3 | `dependency_resolution` | `#c98500` yellow | `⛓` | package installs, import graph work |
| 4 | `architecture_decision` | `#008300` green | `◆` | structural choices, blueprint references |
| 5 | `handoff_ticket` | `#9085e9` violet | `⇄` | HANDOFF_TRANSACTION raise/receipt traffic |
| 6 | `curvature_analysis` | `#d55181` magenta | `κ` | gravity engine output, κ values, bridges under review |
| 7 | `merge_gate_event` | `#d95926` orange | `⊞` | collect/validate/merge pipeline events |

Raw/uncategorized: no color, secondary ink. `shell_exec` output folds into
raw (a command's *interesting* consequences get categorized; its noise stays
noise-colored but visible).

### Status events (reserved status palette — state, never identity)
Always icon + label; distinct from all categorical slots.

| Event class | Color | Icon | Notes |
|---|---|---|---|
| test/gate pass, receipt matched | `#0ca30c` good | ✓ | |
| retry, degraded, agent silent >30s | `#fab219` warning | ⚠ | |
| **dark_bridge_detected** | `#ec835a` serious | `◢◣` | signature event — see §7 |
| test_failure, validation failure, trespass attempt | `#d03b3b` critical | ✕ / 🛡 | trespass additionally locks a persistent marker into the SYSTEM lane |

### State LEDs (pane headers)
`working` = pulsing good · `waiting_on_handoff` = steady violet ·
`validating` = steady blue · `blocked` = warning · `violation` = critical ·
`done` = steady good, pane header dims to 80%.

---

## 5. Typography

| Context | Face | Size/leading | Weight |
|---|---|---|---|
| UI chrome, labels | Geist, fallback `system-ui` | 13/1.4 | 400–650 |
| Terminal/log lines | JetBrains Mono, fallback `ui-monospace` | 12/17.4 | 400; **only** the leading glyph token is 600 |
| Counters (Status Rail) | Geist | 20 | 650, `tabular-nums` |
| Timeline ticks, timestamps, seq ids | JetBrains Mono | 10.5 | 500, `tabular-nums` |
| Pane headers | Geist | 11 | 600, letter-spacing .04em |

Weight discipline: **color carries category, weight carries hierarchy.** Whole
log lines are never bold; nothing shouts unless it is a status event.

---

## 6. Timeline interaction model

Two modes with an explicit, visible boundary:

- **LIVE** (default): playhead pinned at right edge; content scrolls
  left-to-right past it; throughput band and lanes stream. LIVE chip in the
  Status Rail glows steady.
- **REVIEW**: entered by any backward navigation (drag-pan, wheel-zoom, blip
  click, brush). The playhead detaches; live data *keeps buffering* and a
  `⟶ LIVE` return chip appears, pulsing gently. Nothing is lost while
  reviewing — return snaps forward in 260ms.

Interactions:
| Gesture | Effect |
|---|---|
| wheel / pinch | zoom time around cursor (50ms floor → full-session ceiling) |
| drag on lanes | pan (enters REVIEW) |
| click blip | EventInspector popover **and all agent panes scrub to that instant** — every pane shows its log as-of that timestamp, with the produced line highlighted. Cross-agent simultaneous rewind is the credibility centerpiece; it is powered by per-line `(agent, seq, wall_ts, journal_offset)` provenance |
| brush-drag (shift) | select a window → zoom + window stats card: events by category, agents involved, tickets opened/closed, throughput delta vs session mean |
| `←`/`→` | step event-by-event within visible categories |
| `L` | return to LIVE |

**EventInspector** (max 360px popover): event title + category chip · wall
time + seq · agent(s) involved · *raw log excerpt that produced the event*
(mono, scrollable, copyable) · for handoffs: full ticket payload and its
matching receipt; for gates: verdict payload; for dark bridges: κ value, the
edge, and the decision taken (weld vs gateway).

---

## 7. Causality & performance visibility

The requirement: *when a dark bridge is detected, does throughput drop?* must
be answerable by looking, not by querying.

Mechanics:
1. **Full-height event markers.** Dark-bridge detections (and merge-gate
   blocks) render a 1px hairline in `--status-serious` from the top of the
   throughput band to the bottom lane — one vertical line crossing every
   agent's timeline at that instant. The eye reads coincidence for free.
2. **Shared x-axis, stacked bands** — never a dual axis. The throughput dip
   and the marker align by construction.
3. **Aftermath shading.** From a dark-bridge marker until the corresponding
   weld/gateway decision event, the affected agents' lanes get a 6% serious-
   tinted wash — "these two lanes were coupled during this span." Hovering
   the wash names the file pair and κ value.
4. **Window stats** (brush) quantify it: throughput −38% vs session mean,
   2 agents serialized, 1 ticket raised — the skeptic gets numbers where the
   eye saw shape.

Handoff lifecycle rendering: raise = open violet ring on agent A's lane;
receipt = filled violet dot on agent B's lane; a quadratic arc connects them
across the intervening lanes while open (drawn in 300ms, dash-animated at
0.5px/s — slow enough to be calm). On receipt the arc solidifies, then fades
to 40% and persists as history. Unresolved tickets pulse (opacity 0.6↔1.0,
1.6s ease) — an open transaction is visually unfinished business.

---

## 8. Filter UI

A single row between grid and Chronicle. **Filters mute, never erase.**

- **CategoryChip** ×7: swatch dot (10px, 3px radius) + glyph + label + live
  count. Count keeps incrementing while toggled off (`muted, not blind`).
  Click = toggle; **alt-click = solo**; second alt-click restores all.
  Off-state: chip at 40% opacity, count still ticking.
- **Status group**: pass/warn/serious/critical as a separate chip cluster —
  status can be filtered *in* (e.g., failures only) but a trespass event
  overrides all filters and renders regardless. Safety events are
  non-suppressible by design.
- **Focus presets** (dropdown): `Merge integrity` (merge_gate + handoff +
  status) · `Geometry` (curvature + dark bridges + welds) · `Reasoning only`
  · `Raw firehose` (everything, including uncategorized). Presets are
  shareable via URL hash — a reviewer can send a colleague the exact lens.
- **Event search**: substring/regex across the journal; matches paint
  temporary white ticks on all lanes and gutters.

Effects propagate everywhere at once: pane lines collapse (leaving gutter
ticks), timeline blips dim to 15% (never removed — context persists), counts
restyle. One filter model, three synchronized views.

---

## 9. Motion design

Motion answers "what changed?" — it never decorates. All timings on
`cubic-bezier(0.2, 0, 0, 1)`.

| Moment | Motion | Duration |
|---|---|---|
| New log line (≤20 lines/s) | background tint fade-out | 300ms |
| New log line (>20 lines/s) | none — the firehose must feel raw; per-line effects disable above the motion budget | — |
| Blip enter | scale 0.85→1, fade | 150ms |
| Dark-bridge marker | hairline draws top→bottom, single throughput-band pulse | 240ms + 400ms |
| Handoff arc | stroke draw on raise; solidify-then-fade on receipt | 300ms / 1s |
| Focus mode reflow | FLIP transforms | 220ms |
| REVIEW→LIVE snap | playhead glide | 260ms |
| Open ticket pulse | opacity 0.6↔1.0 loop | 1.6s |
| State LED `working` | soft pulse | 2s |

`prefers-reduced-motion`: every animation above becomes an instant state
change; the open-ticket pulse becomes a static double-ring.

---

## 10. Data contract & credibility mechanics

- **Transport**: existing API surface — `WS /api/v1/grid/stream/{cell}` per
  agent, `WS` telemetry channel for orchestrator events, `GET
  /api/v1/grid/status` for reconciliation. Auth via `X-Loom-Api-Key` /
  `localStorage["loom.api_key"]` (existing convention).
- **Event schema** (journal line): `{seq, wall_ts, agent, category | status,
  glyph, summary, raw_offset, raw_len, payload?}`. Categorization happens
  server-side in one place; the UI never invents categories.
- **Session journal**: append-only JSONL on disk (the evidence ledger). The
  ring buffer serves the live view; the journal serves rewind. On session
  end, the journal is content-hashed → **session digest**, same replay-proof
  story as the Observatory's `replay_digest`. Grid Watch can reopen any past
  journal in REVIEW mode — the live tool *is* the forensics tool.
- **Honesty rules**: no synthetic smoothing of throughput; no progress bars
  that are not backed by counted work units; convergence displays only once
  computable; agent silence is surfaced (footer age), not hidden.

---

## 11. Accessibility

- Category identity = color + glyph + label (triple encoding); status = color
  + icon + label. Nothing is color-alone (CVD floor-band mitigation, required
  by validator result).
- Full keyboard model: pane focus (1–9), filter toggles (⌘1–⌘7), timeline
  step (←/→), LIVE (L), search (/), command palette (⌘K).
- Journal table view: a `⊞ Table` toggle renders the visible timeline window
  as a sortable table (time, agent, category, summary) — the screen-reader
  path and the "export to spreadsheet" path are the same feature.
- Contrast: all inks and category colors ≥3:1 on their surfaces (validated);
  10.5px is the floor and appears only in mono tabular contexts.

---

## 12. Build plan (next step, not this document)

1. **Trace-driven first**: like the Observatory, build against a recorded
   journal (fixture: the Wave-1 four-worker sprint replayed at 10×) so every
   component is testable without live agents.
2. Wire `grid/stream/{cell}` WebSockets behind the same event schema.
3. Categorizer service in `aoc_supervisor` (single source of category truth).
4. Ship inside `sandbox_frontend/` beside the observatory, sharing
   `shared/shell.css` chrome.

File plan: `sandbox_frontend/grid-watch.html` + `sandbox_frontend/shared/grid-watch/`
(es modules: `journal.js`, `chronicle.js`, `panes.js`, `filters.js`).
