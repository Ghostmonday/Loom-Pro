# GAIJINN: Deterministic Orchestration for Autonomous Engineering Swarms

## Executive Briefing & Design Partner Framework

| Field | Value |
|-------|-------|
| Version | 2.0 |
| Date | 2026-06-16 |
| Audience | CTO · VP Engineering · Principal Architect |
| Telemetry source | `.gaijinn/merge/governance.json` · `report.json` · `handoff-queue.json` · `audit-report.json` |
| Companion brief | `GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md` Section 5 |

---

### Slide 1: The Multi-Agent Velocity Lie

* **The Promise:** Deploying swarms of AI agents (CrewAI, AutoGen, or native LLM extensions) will yield exponential feature velocity.
* **The Reality:** Standard agents are structurally blind to hidden architectural coupling. They write over each other's code paths, causing silent behavioral regressions and catastrophic git merge hell.
* **The Industry Cop-Out:** Forcing agents to execute sequentially (one at a time). It stops the crashes, but it completely destroys your engineering parallelism.

**Gaijinn counter-position:** Measure coupling before spend. Enforce lane discipline at merge. Coordinate cross-boundary work through an immutable transaction bus — not sibling trespass.

---

### Slide 2: The Economics of the Bottleneck (The Legacy Weld)

* When standard frameworks analyze a complex, multi-module corporate repository, their only safety mechanism is to **weld** dependent modules together.
* **The Core Data (Our Monorepo Baseline — `gaijinn audit .`):**
  * **171** complex code nodes (`audit-report.json` → `metrics.total_code_nodes`).
  * **92** crucial intersections — Shadow Bridges at curvature κ ≤ −0.30 (`metrics.shadow_bridge_count`).
  * **Legacy Mode Penalty:** Fuses architecture into **2 atomic weld blocks**; largest cluster = **40 files** (`legacy_mode.largest_atomic_weld_file_count`). **44 files** trapped inside atomic welds (`legacy_mode.total_files_in_atomic_welds`).
  * **The Impact:** Within each weld block, safe parallel concurrency collapses to **1 worker per block** — your multi-agent swarm is forced into single-threaded serialization across the highest-coupling surfaces of your codebase.

| Legacy mode (union-find weld) | Value |
|-------------------------------|-------|
| Atomic weld blocks | **2** |
| Largest weld cluster | **40 files** |
| Total files in atomic welds | **44** |
| Work units partitioned | **54** |

---

### Slide 3: Shifting the Geometry (The Gateway Advantage)

* Gaijinn applies topological graph analysis to calculate repository curvature risk (κ ≤ −0.30) **before** a single line of code is written.
* Instead of welding files, Gaijinn establishes **GIV Strict Boundary Sandboxes** and an asynchronous **Council Transaction Bus** (`TX-HT-*` tickets on an append-only ledger).
* **The Gateway Mode Metrics (`GAIJINN_HANDOFF_GATEWAYS=1`):**
  * **Atomic Welds:** Reduced from **2** to **0** (`gateway_mode.atomic_weld_blocks`).
  * **Unlocked Files from Welds:** **44 files** instantly freed for parallel access (`efficiency_delta.files_unlocked_from_atomic_welds`).
  * **Handoff Gateway Edges:** **92** HANDOFF_ONLY couplings replace blunt serialization (`handoff_gateway_count`).
  * **Max Safe Parallel Concurrency:** **47 workers** executing simultaneously with mathematically bounded scope isolation (`gateway_mode.max_parallel_workers`).

| Gateway mode | Value |
|--------------|-------|
| Atomic weld blocks | **0** |
| Files unlocked | **44** |
| Handoff gateways | **92** |
| Max parallel workers | **47** |

---

### Slide 4: Real Telemetry Under Corporate Strain

* We stress-tested this architecture by forcing **4 concurrent AI workers** to execute a highly complex, cross-cutting refactor across our own **171-node** system (Billing ↔ API Router ↔ Merge Pipeline ↔ Tests).
* **Sprint profile:** Copy-mode filesystem isolation · `grok-composer-2.5-fast` · ~163s wall per worker · 4/4 sprint completion (`workers/manifest.json`).

**The Audit Trail (ledger: `.gaijinn/merge/governance.json`, scored 2026-06-16T21:26:11Z):**

| Metric | Value | Source |
|--------|-------|--------|
| Sibling trespass violations | **0** | Absolute sandbox lane discipline |
| Handoff tickets raised / resolved | **1 / 1** | `handoff-queue.json` |
| Pending TX-HT tickets | **0** | `handoff-queue.json` |
| Scaffold echoes discarded | **4** | Hardened regex ingest filter |
| Cross-boundary ticket | **`TX-HT-6D0B24`** | Billing → API preflight (resolved mid-flight) |
| `transaction_bus_synchronized` | **true** | Append-only council ledger |
| Validation pass rate | **1.0** (4/4 workers) | `governance.json` → `validation_pass_rate` |
| `merge.validation_pass_rate_full` | **true** | All localized test gates green |
| Convergence score | **0.8889** | Transparent gate — blocks redundant merge attempts |
| Merge conflicts | **0** | `conflict_free: true` |
| Handoff isolation | **true** | Zero sibling path writes |

**Merge report (`.gaijinn/merge/report.json`):**

| Worker | Status | Detail |
|--------|--------|--------|
| worker-001 | blocked (no-op) | Copy-mode · zero fresh deltas (billing already integrated) |
| worker-002 | blocked (no-op) | Copy-mode · api/preflight already mirrored |
| worker-003 | **merged** | `handoff.py` applied · copy-mode |
| worker-004 | blocked (no-op) | Copy-mode · tests already synchronized |

**Why 0.8889 is a feature, not a bug:** Three workers returned `PREFLIGHT_BLOCKED` because their filesystem deltas were already structurally integrated. Gaijinn refuses to pad convergence to 1.0. The gate evaluates every influencing factor — including redundant merge attempts.

---

### Slide 5: Upstream Code Base Immunity

* How do we protect your production main branch from agent anomalies? **The Upstream Firewall.**
* Gaijinn exposes a lightweight REST Preflight Hook (`POST /api/v1/preflight`) wired directly into a plug-and-play GitHub Action gate (`.github/workflows/gaijinn-gate.yml`).
* If a concurrent agent workspace attempts an unauthorized path trespass or leaves an unresolved transaction on the bus, the pipeline **instantly blocks the pull request upstream**.

| HTTP | Status | Trigger |
|------|--------|---------|
| 200 | `PREFLIGHT_CLEARED` | Isolation clean · bus synchronized |
| 422 | `PREFLIGHT_REJECTED` | Trespass in `validated.json` · pending `TX-HT-*` tickets |

**Checks evaluated:** `path_allowlist.trespasses` · `handoff-queue.json.transaction_bus_synchronized` · `pending_tickets`.

---

### Slide 6: The Design Partner Engagement

* We are currently locking down **3 exclusive corporate design partners** for our private alpha cohort.
* **What We Provide:**
  * Full local deployment of the Gaijinn/AOC runtime engine
  * Customized repository topological audits (`gaijinn audit .` → Parallel Efficiency Matrix)
  * Zero-trust CI pipeline guardrails (preflight hook + governance scoring)
  * GIV contract templates and gateway-mode blueprint partitioning
* **The Goal:** Turn your engineering team into a mathematically secure, high-concurrency automated engine.

**90-day engagement arc:**

| Week | Deliverable |
|------|-------------|
| 1 | Parallel Efficiency Matrix on your monorepo |
| 2 | 4-worker pilot sprint on highest-coupling module cluster |
| 3 | `gaijinn-gate.yml` wired to integration branch |
| 4 | Governance score review + expansion roadmap |

**Contact:** hello@neuraldraft.net

**Collateral:** `GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md` · `GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.html` · `docs/campaign/website/enterprise-pitch.html`

---

## Appendix A — The Hook (verbatim for outbound)

> *"Your engineering team is waiting on a 40-file serialization bottleneck. Gaijinn unlocks 44 files instantly, running 4 concurrent workers with 1.0 validation and 0 git merge conflicts."*

---

## Appendix B — Objection Handling

| Objection | Response |
|-----------|----------|
| "We use git worktrees already" | Git tracks files. Gaijinn computes **κ curvature** coupling and enforces **GIV trespass** at merge. |
| "Our agents don't collide" | Phase 1 Exam 1: **0.50 convergence** on a 12-node repo with a single trespass. |
| "Another orchestration wrapper" | Show **TX-HT-6D0B24** bus sync and **0.8889** honest convergence on 171 nodes. |
| "Security / IP" | On-prem enterprise tier. NDA-gated audit. `no secret exfiltration` in GIV prohibitions. |

---

*Neural Draft LLC · Gaijinn · Council #11 · Patent specification in preparation*