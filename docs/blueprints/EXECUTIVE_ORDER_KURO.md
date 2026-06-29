# Executive Order: Build Kuro — Gaijinn Blueprint Visualizer

## Mission

Build Kuro, a real-time desktop visualization companion for Gaijinn. As the Gaijinn pipeline runs (scan → analyze → curvature → dark bridge detection → weld → partition), Kuro displays the geometry being built on a live canvas. Nodes pulse in, edges change color by curvature, dark bridges glow red, welds animate, and final work units render as colored blocks.

## Architecture

Two components, communicating via WebSocket over localhost:

**Backend (Go, ~300 lines):** A lightweight bridge process that subscribes to Gaijinn's API endpoints and CLI output, normalizes the events into a structured JSON protocol, and streams them over a WebSocket server on localhost:9876.

**Frontend (Rust, ~800 lines):** A native desktop window using wgpu for rendering. Receives events from the Go bridge and renders the graph visualization in real-time. Force-directed layout. No web technologies — this is a compiled native app.

## Event Protocol

The Go bridge emits these event types over WebSocket:

```
node_added      → { id, gravity }                    — file scanned
edge_curvature  → { source, target, kappa }          — curvature computed
dark_bridge     → { source, target, kappa }           — κ < -0.30 detected
weld_begin      → { cluster: [nodes] }                — union-find starts welding
weld_complete   → { block_id, paths: [...] }          — weld finished
work_unit       → { id, files, risk, depends_on: [] } — final partitioning
phase_change    → { phase: "scan"|"curvature"|"weld"|"partition" }
```

## What to Build First

**Iteration 1 — Go bridge (can be built and tested alone):**
- WebSocket server on :9876
- Reads `gaijinn scan --json` output and emits `node_added` events
- Reads curvature_meta from metrics_manifest.json and emits `edge_curvature` events
- Simple test: pipe a saved Gaijinn output file through the bridge and verify events

**Iteration 2 — Rust canvas (render-only, no events yet):**
- Open a window with wgpu
- Render a dark background
- Accept hardcoded node/edge data, draw a force-directed graph
- Edges colored by kappa value (cyan > 0, white ≈ 0, amber < 0, red < -0.30)

**Iteration 3 — Connect them:**
- Rust connects to Go bridge at ws://localhost:9876
- Events stream in real-time, canvas updates as they arrive
- Nodes pulse in with a spawn animation
- Dark bridge edges pulse red with a glow effect

**Iteration 4 — Welding animation:**
- On `weld_begin`, the affected nodes' edges glow brighter
- A gold border line forms around the cluster
- The cluster compacts into a single highlighted block

**Iteration 5 — Work unit display:**
- Final work units render as colored blocks
- Green/yellow/red for risk level
- Arrows between blocks for dependencies
- Summary stats panel (node count, dark bridge count, weld count, WU count)

## Constraints

- Rust uses wgpu (not web, not electron). Window management via winit or pixels crate.
- Go bridge is a single binary, no dependencies beyond the standard library + gorilla/websocket.
- All rendering is 2D. No 3D, no camera orbits, no VR.
- The visualizer is a companion — it does not control Gaijinn. One-way data flow only.
- Color palette: background #06080b, cyan #22d3ee, violet #a78bfa, amber #fbbf24, red #f87171, green #4ade80, gold #fbbf24.

## Acceptance Criteria

1. Running `gaijinn scan .` with the Go bridge produces WebSocket events visible in the Rust canvas
2. The canvas shows nodes as cyan dots with labels, edges colored by curvature
3. Dark bridge edges pulse red
4. Welding animation shows nodes fusing into a gold-bordered block
5. Final view shows risk-colored work unit blocks with dependency arrows
6. All rendering is native (no browser, no webview)
7. Build: `cargo build --release` produces a single binary under 10MB

## Non-Goals

- Not a text editor
- Not a code browser
- No file system access
- No cloud connectivity
- No user accounts or auth
