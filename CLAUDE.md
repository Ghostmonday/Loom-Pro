<!-- BEGIN LOOM INIT -->
# LooM Project Guidance

- **Status:** Phase 2 complete (2026-06-16) — 171-node monorepo dogfood, validation 1.0, TX-HT-6D0B24 synced, convergence 0.8889 (honest no-op detection). Shipped: case study v2, enterprise pitch deck, provisional patent spec draft (`main` a50d150).
- **Blueprint Architecture — 2 Layers + 3 Engineering Pipelines:**
  - **Layer 0 (Domain Rules):** blueprint.json — functional domains (Locker Management, Payments, Auditing), core invariants (no two active rentals on one locker), system-level constraints.
  - **Layer 1 (Reactive):** graph.json — 1:1 physical mirror. Every endpoint, route, or CLI command maps to an Intent Node (HTTP method+path, direct DB mutations, inline guard conditions, state transitions). Statically extracted via AST/regex scanners.
  - **Layer 2 (Reflective):** inferred.json — emergent behavior between Layer 1 nodes: lifecycle chains (Create→Activate→Trigger→Cancel), dependency contracts, capability ceilings (what the system deliberately cannot do). Deduced by analyzing Layer 1's graph topology.
  - **The 3 Non-Sentient Engineering Pipelines** (replace "reasoning" with formal math):
    1. **Topological Inference (Graph Theory)** — DFS/Dijkstra reachability on state transitions. Lifecycle chain = path in topology. Missing path = disconnected lifecycle. No "reasoning" — pure reachability math.
    2. **Type-Flow Analysis (Dataflow Tracking)** — Taint analysis: mark user identity (org_id/user_id) as Source, DB mutations (db.Exec) as Sink. Trace AST paths from Source to Sink. Any path to Sink without Source = data-flow puncture = Shadowbridge. No business logic knowledge needed.
    3. **Semantic Synthesis (Local LLM Moat)** — Takes structured Layer 1 JSON, maps tokens to domain concepts via local LLM pass. Handles what static analysis cannot: naming intent, domain classification.
- **Two-Stage Compiler:**
  - **Stage 1 (Blueprint Compiler, Intent→Schema):** User prompt → Layer 0 (rules/invariants) → Layer 2 (lifecycle chains) → Layer 1 (concrete endpoints).
  - **Stage 2 (Parallel Replicator, Schema→Code):** Load blueprint → spawn isolated worktrees per workflow → GIV enforcement per agent → LTL DFA monitor + circuit breaker → cleanup.
  - **Greenfield order:** Layer 0 → Layer 2 → Layer 1. **Brownfield order:** Scan code → Layer 1 → Layer 2 inference.
- Keep generated LooM artifacts under `.loom/`.
- Run `loom compile-prompt` after changing `.loom/project.json`.
- Run `loom scan .` before graph analysis when source files change.
- Run `loom analyze` before creating worker directories.
- Run `loom run-grid --workers 2` to create isolated worker handoffs.
- **Council (required):** Read `.loom/bridge/council.md` (project) or `~/.loom/bridge/council.md` (global/Hermes). Post with `loom council say --as cursor "..."` (user: `--as user`). One shared thread — never ask the human to relay messages between agents.
- **Hermes:** `loom hermes` or `loom hermes -i` from terminal (council-backed).
<!-- END LOOM INIT -->