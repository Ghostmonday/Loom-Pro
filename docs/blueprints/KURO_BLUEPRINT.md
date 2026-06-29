# KURO BLUEPRINT: Gaijinn Blueprint Visualizer

**Project:** Kuro (黒 — Japanese for "black" or "dark")
**Type:** Gaijinn add-on / companion desktop application
**Purpose:** Real-time visualization of Gaijinn's blueprint generation pipeline
**Tech stack:** Rust (core rendering engine) + Go (backend bridge to Gaijinn API)

---

## Vision

Kuro is a real-time canvas that shows Gaijinn's invisible geometry being built. As the pipeline runs — scan → analyze → compute curvature → detect dark bridges → weld → partition — Kuro visualizes each step as it happens.

It is NOT a text editor. It is a **design surface** for parallelization strategy.

---

## Phases

### Phase 1: Graph Ingestion (gaijinn scan)

Display the raw dependency graph as nodes and edges. Nodes pulse in as files are scanned. Edges form between nodes as imports are detected. The graph grows organically.

- Rust: render engine using wgpu or pixels crate
- Go: bridge process tails gaijinn scan output, sends node/edge events over WebSocket or Unix socket
- Visual: force-directed graph layout, dark background, cyan nodes

### Phase 2: Curvature Computation (gaijinn analyze)

As the gravity engine computes Ollivier-Ricci curvature, edges change color:
- κ > 0: cyan (redundant paths, safe)
- κ ≈ 0: white/gray (stable)
- κ < 0: amber (risky)
- κ < -0.30: pulsing red (DARK BRIDGE DETECTED)

Gravity floor (g < 0.20) nodes gray out and disconnect visually.

- Rust: per-edge color interpolation based on curvature values
- Go: streams curvature_meta from gravity.py output
- Visual: edges transition color smoothly, red edges pulse

### Phase 3: Dark Bridge Welding (gaijinn plan)

When the surgery rule activates, the union-find algorithm visibly fuses dark bridge endpoints:
- Red edges glow brighter
- A gold "weld" line forms around the cluster boundary
- The cluster compacts into a single highlighted block
- Watch the weld happen in real-time

- Rust: weld animation (edges pull together, gold border forms)
- Go: streams plan output, union-find steps
- Visual: nodes physically move together, gold glow appears

### Phase 4: Work Unit Assignment (gaijinn plan → run-grid)

Final work units render as distinct colored blocks:
- Each block = one work unit
- Block color = estimated risk level (green/yellow/red)
- Block size = number of files in the unit
- Arrows between blocks show dependencies

- Rust: block layout, dependency arrows
- Go: streams final blueprint.json
- Visual: risk-colored blocks with dependency arrows

### Phase 5: History & Comparison

- Save blueprint snapshots as the user iterates
- Compare two blueprints side-by-side to see how refactoring changed the geometry
- Highlight what changed (new dark bridges, resolved dark bridges, different work unit boundaries)

---

## UI Layout

```
┌──────────────────────────────────────────────────────────┐
│  KURO — Blueprint Visualizer                    [R] [S]  │
├──────────────────────────────────────────────────────────┤
│  ● Phase 1: Scan    ● Phase 2: Curvature                │
│  ● Phase 3: Welding  ○ Phase 4: Partition  (live)      │
├──────────────────┬───────────────────────────────────────┤
│  Blueprint List  │     [Main Visualization Canvas]      │
│  ─────────────── │                                       │
│  ├─ Gaijinn v2   │    Nodes pulse, edges glow,          │
│  ├─ tiny-python  │    dark bridges fade to red,         │
│  └─ system-one   │    weld animation plays...            │
│                  │                                       │
│  [New Blueprint] │                                       │
├──────────────────┴───────────────────────────────────────┤
│  Stats: 171 nodes | 81 dark bridges | 2 welds | 53 WUs  │
└──────────────────────────────────────────────────────────┘
```

---

## Architecture

```
┌─────────────┐     WebSocket     ┌────────────────────┐
│  Gaijinn    │ ────────────────→ │  Kuro Backend (Go) │
│  CLI/API    │   events stream   │  - event router     │
│             │                   │  - state manager    │
│             │                   │  - snapshot store   │
└─────────────┘                   └────────┬───────────┘
                                          │ IPC / socket
                                          ▼
                                 ┌────────────────────┐
                                 │ Kuro Frontend (Rust)│
                                 │  - wgpu renderer    │
                                 │  - force layout     │
                                 │  - animation engine │
                                 │  - TUI or native win│
                                 └────────────────────┘
```

---

## Work Units

| WU | Scope | Risk | Depends On |
|----|-------|------|------------|
| 01 | Rust render engine (wgpu canvas, node/edge render, color system) | High | — |
| 02 | Go event bridge (WebSocket server, Gaijinn API client, event schema) | High | — |
| 03 | Force-directed graph layout algorithm | Medium | WU-01 |
| 04 | Curvature color interpolation + dark bridge pulse animation | Medium | WU-01, WU-03 |
| 05 | Weld animation sequence (edge pull, gold border, cluster compaction) | Medium | WU-01, WU-03 |
| 06 | Work unit block renderer (risk colors, size, dependency arrows) | Low | WU-01, WU-03 |
| 07 | Blueprint snapshot save/compare (diff engine, visual diff) | Low | WU-06 |
| 08 | Phase progress indicator + status bar | Low | WU-01 |
| 09 | Integration test suite (mock gaijinn events → verify rendering) | Medium | All |

---

## Event Protocol (Go ↔ Rust)

```json
{
  "type": "node_added",
  "data": { "id": "billing.py", "gravity": 0.42 }
}
{
  "type": "edge_curvature",
  "data": { "source": "api.py", "target": "billing.py", "kappa": -0.36 }
}
{
  "type": "dark_bridge_detected",
  "data": { "source": "...", "target": "...", "kappa": -0.36 }
}
{
  "type": "weld_start",
  "data": { "cluster": ["billing", "api", "merge", "handoff"] }
}
{
  "type": "weld_complete",
  "data": { "block_id": "wu-02", "paths": ["..."] }
}
{
  "type": "work_unit_assigned",
  "data": { "id": "WU-02", "files": 4, "risk": "high", "depends_on": ["WU-01"] }
}
```

---

## Next Steps

1. Generate this blueprint with `gaijinn plan --workers 4`
2. Write detailed executive order for Composer 2.5 based on WU breakdown
3. Build: Go bridge first (simplest, enables testing), then Rust renderer
4. Iterate: connect to live Gaijinn pipeline, watch the first visualization
