# Loom Screen Naming

Product-facing screen names, renamed 2026-07-02 for clarity. Display layer
only: internal ids, file names, URLs, and API routes keep their original
identifiers (same pattern as the Gaijinn → Loom migration — the UI speaks the
new language, the plumbing stays stable).

| New name | Old name | Internal id / route | What it is |
|---|---|---|---|
| **Build** | Intent Forge | `intent-forge` | Capture intent, run a build session |
| **Receipts** | Claims Ledger | `claims-ledger` | Session-backed evidence and claims |
| **Plan** | Blueprint Ratification | `blueprint-ratification` | Review and approve the blueprint |
| **X-Ray** | Curvature Analysis | `curvature-analysis` | Ollivier-Ricci curvature read of the code |
| **Map** | Topological Observatory | `topological-observatory` | Topology and FRG inspection |
| **Drift** | Drift Monitor | `drift-monitor` | Baseline-vs-now topology drift |
| **Ship** | Packet Export | `packet-export` | Deliverable packaging and export |
| **Replay** | Resolution Observatory | `observatory/resolution-observatory` | Flight-recorder replay of a resolution_v3 run |
| **Party** | Grid Watch / agent parallelization | (design spec; unbuilt) | Live mission control for parallel agents — see `docs/architecture/GRID-WATCH-DESIGN-SPEC.md` |
| Hub | Project Hub | `hub` | Entry point |

The product loop reads: **Build → Receipts → Plan → X-Ray → Map → Drift → Ship**,
with **Replay** and **Party** as instruments over any run.

When renaming anything else, follow the same rules: short, one word if
possible, describes what the user *does* there — and never rename an internal
identifier just to match the label.
