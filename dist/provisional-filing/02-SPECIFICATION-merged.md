% Gaijinn Provisional Patent Specification
% Neural Draft LLC
% 2026-06-19

# Provisional Application Cover Sheet (Transmittal)

**Use this as the first page of your uploaded PDF bundle, or enter equivalent fields in USPTO Patent Center.**

| Field | Value |
|-------|-------|
| Application type | Provisional Application for Patent |
| Title of invention | Systems and Methods for Governed Parallel Execution of Autonomous Software Agents Using Curvature-Based Repository Partitioning, Agent Intent Vectors, and an Asynchronous Transaction Bus |
| Inventor(s) | See INVENTOR-FIELDS.md |
| Applicant | [Individual inventor name] OR Neural Draft LLC |
| Correspondence address | See INVENTOR-FIELDS.md |
| Entity status | **Micro entity** (certification required — see 02-MICRO-ENTITY-DECLARATION.md) |
| U.S. government interest | No |
| Attorney docket number | GAIJINN-PROV-001 |
| Assignee (intended, post-filing) | Neural Draft LLC |

## Documents enclosed

1. Specification (technical disclosure + claims) — `02-SPECIFICATION.pdf`
2. Optional: Exhibit A — empirical evidence summary — included in specification § Reduction to Practice
3. Drawings — **none** (software method; figures listed as recommended for non-provisional follow-on)

## Fee

| Item | Amount (verify at filing) |
|------|---------------------------|
| Basic filing fee — micro entity | **$80** (USPTO fee code 3001/3002 — confirm on [fee schedule](https://www.uspto.gov/learning-and-resources/fees-and-payment/uspto-fee-schedule)) |

Pay via Patent Center at time of submission.

## Priority date

The **filing date** stamped by USPTO on this provisional becomes your priority date for subject matter adequately described in the specification. Calendar **12 months** for non-provisional conversion.

---

*Pro se filing — not legal advice.*
\newpage

# Gaijinn — Provisional Patent Technical Specification Addendum

| Field | Value |
|-------|-------|
| Document class | Provisional patent disclosure support (technical specification) |
| Version | 1.0 |
| Date | 2026-06-16 |
| Assignee (intended) | Neural Draft LLC |
| Inventor(s) | See `legal/provisional-filing/INVENTOR-FIELDS.md` |
| Status | Pro se filing package ready — **not filed** |

---

## Notice

This document is a **technical specification addendum** intended to support a U.S. Provisional Patent Application. It is **not legal advice** and does not constitute filed claims. A registered patent attorney should review, amend, and file before any public disclosure beyond controlled design-partner distribution.

---

## Field of the Invention

Systems and methods for **governed parallel execution of autonomous software agents** over multi-module code repositories, comprising: (1) differential-geometry partitioning of repository import graphs; (2) per-agent write-scope contracts enforced at merge time; (3) an append-only asynchronous transaction bus for cross-boundary mutations; and (4) upstream preflight gating that blocks integration when isolation or bus synchronization invariants fail.

---

## Background and Problem Statement

Conventional multi-agent coding frameworks partition tasks by prompt or file tree heuristics. Version control systems track file history but do not model implicit functional coupling across modules. When N autonomous agents execute concurrently:

- Agents satisfy local tests by writing into sibling-owned paths (trespass).
- Union-find or directory-based partitioning creates **atomic weld blocks** that serialize large file clusters (e.g., 40+ files), destroying parallel ROI.
- Cross-boundary dependencies are resolved by direct sibling writes or human merge recovery.

No prior system combines **Ollivier-Ricci curvature** on a repository interaction graph with **runtime-enforced Agent Intent Vectors (GIV)** and an **immutable handoff transaction bus** synchronized before merge.

---

## Summary of the Invention

The disclosed Gaijinn system executes a closed loop:

```
scan → analyze (curvature) → plan (GIV + blueprint) → isolated workers →
collect → validate-worker → merge-grid → governance score → CI preflight
```

Empirical validation on a 171-node monorepo demonstrates: **4 concurrent workers**, **0 sibling trespass violations**, **1.0 validation pass rate**, **transaction bus synchronized**, and elimination of a **40-file atomic serialization trap** via 92 handoff gateway edges.

---

## Detailed Technical Disclosure

### System 1: Ollivier-Ricci Graph Curvature Repository Partitioning Engine

**Reference implementation:** `aoc-cli/aoc_cli/gravity.py`, `aoc-cli/aoc_cli/helpers/audit.py`, `aoc-cli/aoc_cli/commands/analyze_.py`

#### 1.1 Graph construction

The system ingests a repository interaction graph `G = (V, E)` where:

- Vertices `V` represent code modules (files or logical nodes).
- Directed edges `E` represent import or invocation dependencies.
- Each vertex `v ∈ V` carries optional metadata: `capability_level`, `side_effect_score`.

#### 1.2 Structural gravity computation

For each node, the system computes a normalized **structural gravity** score combining capability risk and side-effect weighting against hard floors (`GRAVITY_HARD_FLOOR = 0.20`). Nodes below the floor are flagged for automatic rejection from autonomous write assignment.

#### 1.3 Ollivier-Ricci curvature on directed edges

For each directed edge `(u → v) ∈ E`, the system computes **Ollivier-Ricci curvature** κ using optimal transport over neighborhood measures on the underlying graph (implementation via earth-mover distance on discrete distributions).

Edges with κ ≤ `CURVATURE_HARD_FLOOR` (−0.30) are classified as **Shadow Bridges** — high-risk couplings invisible to flat module boundaries or union-find clustering.

#### 1.4 Partitioning modes

**Legacy mode (union-find weld):** Shadow Bridge-connected components are merged into atomic weld blocks. All files in a block receive a single work unit; parallel agent assignment to distinct files within the block is forbidden.

**Gateway mode (`GAIJINN_HANDOFF_GATEWAYS=1`):** Shadow Bridges become **HANDOFF_ONLY gateway edges** rather than atomic welds. Work units retain non-overlapping `allowed_paths`; cross-boundary mutations must traverse the transaction bus (System 3).

#### 1.5 Parallel Efficiency Matrix output

The audit subsystem emits a comparative matrix quantifying:

- `atomic_weld_blocks` (legacy vs gateway)
- `largest_atomic_weld_file_count`
- `files_unlocked_from_atomic_welds`
- `handoff_gateway_count`
- `max_parallel_workers`

**Measured result (Gaijinn monorepo, 2026-06-16):** Legacy: 2 weld blocks, 40-file largest cluster, 44 files serialized. Gateway: 0 weld blocks, 44 files unlocked, 92 handoff gateways, 171 code nodes partitioned into 54 work units.

---

### System 2: GIV Strict Boundary Isolation Tokens

**Reference implementation:** `aoc-cli/aoc_cli/giv.py`, `aoc-cli/aoc_cli/helpers/merge.py` (`detect_trespasses`, `classify_worker_status`), `aoc-cli/aoc_cli/commands/validate_worker.py`

#### 2.1 Agent Intent Vector (GIV) schema

Each worker `w` receives a frozen **Agent Intent Vector** comprising:

| Field | Semantics |
|-------|-----------|
| `worker_id` | Unique worker identifier |
| `allowed_paths` | Posix-relative paths the worker may mutate |
| `denied_paths` | Explicit write prohibitions |
| `sibling_denied_paths` | Paths owned by sibling workers (derived from blueprint) |
| `denied_commands` | Shell commands forbidden in `output.log` audit (e.g., `git push`) |
| `structural_tokens` | Boolean enforcement flags: `SCOPE_STRICT`, `NO_SIBLING_TRESPASS`, `HANDOFF_ONLY` |

Construction validates non-empty `allowed_paths` and canonical deterministic serialization.

#### 2.2 Isolation substrates

Workers execute in one of:

- **Git worktree isolation** — disposable branch with path-scoped writes.
- **Filesystem copy fallback** — directory copy without `.git`; deltas detected via `changed_files_filesystem()` comparing worker sandbox to session baseline using `filecmp` and content hash.

#### 2.3 Merge-time trespass detection

At `validate-worker`, the system computes `changed_files(worker_dir, base_ref, baseline_dir, scope_paths)` and invokes `detect_trespasses(changed, giv)`. Any changed path not matching `allowed_paths` and not denied-only constitutes a **trespass**. Trespass is merge-blocking, not advisory.

#### 2.4 Governance invariants

Protected invariant paths (e.g., `.gaijinn/project.json`, merge governance artifacts) cannot be modified by workers unless explicitly allowlisted. Violations surface in `invariant_violations()` and block merge.

**Measured result:** 4 concurrent workers on 171-node graph; **0 trespass violations**.

---

### System 3: Asynchronous Multi-Agent Runtime Council Transaction Bus

**Reference implementation:** `aoc-cli/aoc_cli/helpers/handoff.py`, `aoc-cli/aoc_cli/helpers/council.py`, `.gaijinn/merge/handoff-queue.json`

#### 3.1 Handoff ticket emission

When a worker requires a mutation in a sibling-owned path, it emits a delimited **HANDOFF_TRANSACTION_REQUEST** block in `output.log`:

```
++++ GAIJINN_HANDOFF_TICKET_START ++++
{ JSON payload }
++++ GAIJINN_HANDOFF_TICKET_END ++++
```

Payload schema (`HandoffTicket`):

- `ticket_id` — deterministic identifier (prefix `TX-HT-`)
- `source_worker_id`
- `target_work_unit_id`
- `target_file`
- `required_mutation_context` — semantic specification of required sibling mutation
- `status`, `timestamp`, optional `resolution_commit`

#### 3.2 Bus ingest and scaffold hardening

`sync_handoff_queue_at_collect()` parses worker logs, ingests tickets into `handoff-queue.json`, and applies **scaffold token filtering** to discard template echoes (`<PATH_TO_FILE>`, etc.) that would otherwise pollute the bus.

**Measured result:** 4 scaffold tickets dropped; 1 legitimate ticket (`TX-HT-6D0B24`) raised and resolved.

#### 3.3 Receipt and synchronization

Upon sibling completion, the target worker posts a **HANDOFF_TRANSACTION_RECEIPT** to the append-only council ledger. The bus computes:

```
transaction_bus_synchronized = (handoff_tickets_resolved == handoff_tickets_raised) ∧ (pending_tickets == ∅)
```

#### 3.4 Cross-cutting transaction exemplar (TX-HT-6D0B24)

| Field | Value |
|-------|-------|
| Source | worker-001 (billing.py scope only) |
| Target | WU-PH2-002 → api.py |
| Mutation | Import settlement localization APIs; extend POST /api/v1/preflight; idempotent deployment fee deduction |
| Outcome | Resolved; bus synchronized; zero sibling file writes by source worker |

---

### System 4: Merge Pipeline Governance and Upstream Preflight Gate

**Reference implementation:** `aoc-cli/aoc_cli/commands/collect.py`, `validate_worker.py`, `merge_grid.py`, `aoc_supervisor/aoc_supervisor/preflight.py`, `.github/workflows/gaijinn-gate.yml`

#### 4.1 Pipeline phases

1. **collect** — Per-worker status, `changed_files`, `diff_summary`, handoff queue sync.
2. **validate-worker** — Gates: path allowlist, scope isolation, denied commands, handoff protocol, scoped acceptance tests, invariants, handoff bus integrity.
3. **merge-grid** — Topological merge order respecting blueprint `depends_on`; copy-mode file application or git branch merge.
4. **governance.json** — Structural convergence score with invariant breakdown.

#### 4.2 Structural convergence scoring

Convergence aggregates:

- `validation_pass_rate`
- `handoff_isolation`
- `transaction_bus_synchronized`
- `merge.no_blocked`, `merge.no_conflicted`
- Worker merge counts

The system **does not pad** convergence when validation passes but merge detects zero fresh deltas (already-integrated work). Copy-mode workers with no filesystem changes receive `PREFLIGHT_BLOCKED` at merge, yielding honest partial convergence (e.g., **0.8889**) rather than vanity **1.0**.

#### 4.3 CI preflight endpoint

`POST /api/v1/preflight` evaluates `validated.json` and `handoff-queue.json`:

- `PREFLIGHT_CLEARED` (200) — safe to integrate
- `PREFLIGHT_REJECTED` (422) — trespass or unresolved TX-HT tickets

---

## PART XI — Claim Structure (Draft — for attorney conversion)

Nine independent claims form the foundation of invention protection. Claims use brand-neutral terminology; implementation references appear in the Detailed Technical Disclosure above.

---

### Independent Claim 1 — Operational Contract Compilation

**1.** A computer-implemented method for transforming a probabilistic software-agent orchestration environment into a machine-readable, enforceable operational contract, comprising:

(a) discovering, by a capability inventory module, operational capabilities of a target software system without requiring modification of host-system source code;

(b) constructing, by a topology compiler, a strongly typed multi-layer interaction graph comprising a domain-rules layer, a reactive layer mapping physical endpoints to intent nodes, and a reflective layer inferring emergent lifecycle chains between said intent nodes;

(c) compiling, by a blueprint compiler, a Certified Operational Contract (COC) comprising partitioned work units, non-overlapping write-scope assignments, structural invariants, and per-agent permission vectors derived from said interaction graph; and

(d) enforcing, by a merge integrity harness, agent-generated file deltas against said COC at integration time to block non-compliant mutations prior to repository merge.

**2.** The method of claim 1, wherein compiling the COC further comprises embedding domain invariants and risk flags parsed from a natural-language project prompt into a Layer 0 rules record within said interaction graph.

**3.** The method of claim 1, wherein the reflective layer deduces valid operational transitions by performing reachability analysis over state-transition paths in the reactive layer topology.

**4.** The method of claim 1, wherein each per-agent permission vector comprises an allowed write-path whitelist, a sibling-denied-path blocklist, a denied-command blocklist, and boolean structural enforcement tokens.

---

### Independent Claim 2 — Non-Invasive Capability Extraction

**5.** A non-invasive capability extraction system for inventorying application boundaries of a host software system, comprising:

(a) a processor configured to select an extraction modality from the group consisting of: abstract-syntax-tree parsing of source files, OpenAPI or Swagger specification ingestion, and Model Context Protocol (MCP) manifest parsing;

(b) a scanner module that traverses a target repository filesystem while honoring ignore patterns, emitting file nodes annotated with capability level and side-effect score metadata without writing to or mutating host-system source code;

(c) an intent-node extractor that maps HTTP routes, CLI commands, database mutations, and inline guard conditions to discrete capability records in a Layer 1 reactive graph; and

(d) a serialized graph artifact writer that persists said capability records and structural reference edges to a machine-readable interaction graph file.

**6.** The system of claim 5, wherein abstract-syntax-tree parsing identifies import edges and invocation dependencies between code modules to populate directed edges in said interaction graph.

**7.** The system of claim 5, wherein capability level is computed from path-segment keywords, entry-point decorators, and side-effect heuristics detected in file content.

**8.** The system of claim 5, further comprising a semantic enrichment pass that classifies intent nodes into domain resource clusters using a local language-model mapping over structured Layer 1 JSON.

---

### Independent Claim 3 — Capability Topology Governance

**9.** A computer-implemented method for governing system operations as a strongly typed capability topology, comprising:

(a) representing each operational capability as a typed node in a directed graph, each node carrying a capability identifier, a resource cluster designation, and a normalized risk score;

(b) representing each valid operational transition as a directed edge between a source capability node and a target capability node, each edge annotated with a transition classification;

(c) validating, by a blueprint validator, that work-unit write scopes assigned to concurrent execution lanes are pairwise non-overlapping; and

(d) rejecting blueprint compilation when any pair of work units would mutate overlapping filesystem paths, thereby preventing ambiguous agent ownership of shared resources.

**10.** The method of claim 9, wherein work units further specify a dependency directed acyclic graph (`depends_on`) governing topological merge order among concurrent execution lanes.

**11.** The method of claim 9, wherein transition classification distinguishes lifecycle chains, disconnected gaps, and shadow-bridge couplings inferred from reflective-layer reachability analysis.

**12.** The method of claim 9, further comprising rendering a human-readable blueprint document and a canonical JSON blueprint artifact from a single validated topology partition.

---

### Independent Claim 4 — Structural Gravity Certification *(Ricci Curvature & Shadow Bridge Core)*

**13.** A computer-implemented method for determining architectural criticality, risk sequencing rules, and parallel execution constraints based on graph geometry, comprising:

(a) computing, for each node in an interaction graph, a normalized structural gravity score combining in-degree connectivity, out-degree connectivity, capability risk weight, and side-effect weight against a gravity hard floor;

(b) for each directed edge (u → v), generating outgoing target probability distributions over neighborhood nodes of u and v using weighted risk scores combining capability level α and side-effect profile β;

(c) constructing a cost matrix between neighborhood supports by measuring shortest-path lengths on an undirected projection of the graph, substituting a total-node-count fallback distance when neighborhoods are disconnected;

(d) computing a Wasserstein optimal transport distance between said probability distributions via earth-mover distance;

(e) evaluating an information-flow curvature metric κ for each edge as one minus the ratio of said Wasserstein distance to the directed graph distance between u and v;

(f) identifying edges whose curvature metric falls below a predetermined negative risk threshold as structural bottleneck constraints designated shadow bridges or dark bridges; and

(g) partitioning the target software codebase into isolated work units by applying a union-find clustering pass that fuses files bound by said structural bottleneck constraints into atomic single-worker units while allocating uncoupled subgraphs with non-negative curvature into separate concurrent execution blocks.

**14.** The method of claim 13, wherein the information-flow curvature metric is an Ollivier-Ricci curvature value and the predetermined negative risk threshold is a hard floor of κ = −0.30.

**15.** The method of claim 13, further comprising classifying risk-jump shadow bridges when a source node exhibits low-context capability and a target node exhibits high-capability, high-side-effect profiles regardless of geometric curvature.

**16.** The method of claim 13, wherein nodes whose structural gravity score falls below the gravity hard floor are automatically rejected from autonomous write assignment.

**17.** The method of claim 13, further comprising, in a gateway processing mode, converting dark-bridge edges into non-overlapping transactional handoff boundaries designated `HANDOFF_ONLY` rather than atomic weld blocks, and emitting a parallel efficiency matrix quantifying files unlocked from atomic serialization.

---

### Independent Claim 5 — Runtime Enforcement of Certified Agent Boundaries

**18.** A runtime security system for enforcing certified agent boundaries during parallel autonomous software engineering, comprising:

(a) a supervisory daemon configured to poll a metrics manifest and validate structural safety state at line rate upon each manifest write;

(b) an authorization gate matcher that, for each agent workspace, loads an immutable Agent Intent Vector specifying allowed paths, denied paths, sibling-denied paths, denied commands, and structural enforcement tokens;

(c) a drift detection module that compares agent-generated file deltas against said Agent Intent Vector using git diff when version-control metadata is present or filesystem baseline comparison when version-control metadata is absent;

(d) a trespass classifier that blocks integration of any workspace whose changed paths fall outside the allowed write-path whitelist; and

(e) an automated circuit breaker that halts grid-sprint readiness when the supervisory daemon detects tripped safety markers including automatic rejection flags, unresolved shadow-bridge counts, or missing worker manifests.

**19.** The system of claim 18, wherein the isolation substrate for each agent workspace is selected from a git worktree branch or a filesystem copy sandbox.

**20.** The system of claim 18, wherein structural enforcement tokens include `SCOPE_STRICT`, `NO_SIBLING_TRESPASS`, and `HANDOFF_ONLY`.

**21.** The system of claim 18, further comprising a denied-command scanner that inspects agent output logs for occurrences of blocked shell commands including repository push operations.

**22.** The system of claim 18, further comprising an upstream preflight API that returns a merge-cleared status only when trespass violations are empty and a transaction bus synchronization invariant is satisfied.

---

### Independent Claim 6 — Self-Certifying Software Architecture

**23.** A computer-implemented method for continuous self-certification of a software system undergoing autonomous agent modification, comprising:

(a) scanning, after each agent sprint, a target codebase to regenerate an interaction graph and curvature metrics manifest reflecting current architectural surface;

(b) comparing agent-generated file deltas against a Certified Operational Contract and a completion ledger recording prior work-unit content hashes;

(c) classifying workers with zero filesystem delta whose assigned work units match completion-ledger entries as already-integrated rather than merge-blocked, thereby preventing redundant merge attempts;

(d) computing a structural convergence score from validation pass rate, handoff isolation, transaction-bus synchronization, and merge disposition without padding the score when validation passes but no fresh deltas exist; and

(e) triggering a dynamic re-certification event when convergence falls below a certification threshold or when newly detected shadow bridges exceed a prior baseline count.

**24.** The method of claim 23, wherein content hashes are computed over post-weld file contents within each work unit's allowed paths.

**25.** The method of claim 23, wherein the completion ledger is an append-only JSON artifact keyed by stable work-unit identifiers.

**26.** The method of claim 23, further comprising filtering completed work units from subsequent blueprint plans by consulting said completion ledger before spawning new agent workspaces.

---

### Independent Claim 7 — Federated Operational Contract Governance

**27.** A computer-implemented method for federated governance of operational contracts across organizational or multi-system boundaries, comprising:

(a) deploying a plurality of software-system instances each maintaining a local Certified Operational Contract and a deploy manifest under a shared vault root;

(b) parsing cross-system reference links encoded in a federated link syntax specifying a remote vault identifier and a target capability record;

(c) resolving said cross-system links lazily at query time against remote deploy manifests without requiring redeployment of the linking system when a remote vault changes;

(d) publishing structured handoff transaction tickets from a first system's agent workspace to a shared append-only council transaction bus accessible by a second system's agent workspace; and

(e) validating, prior to cross-system integration, that raised transaction tickets equal resolved tickets and that no pending tickets remain in the shared bus.

**28.** The method of claim 27, wherein unresolved cross-system links are reported as broken-link records without halting local certification of the linking system.

**29.** The method of claim 27, wherein handoff transaction tickets comprise a deterministic identifier, a source worker identifier, a target work-unit identifier, a target file path, and a required mutation context.

**30.** The method of claim 27, further comprising filtering scaffold template tokens from handoff ticket parse results prior to bus ingestion.

---

### Independent Claim 8 — Observable Read Isolation (ORI)

**31.** A concurrency coordination system for multi-agent software engineering, comprising:

(a) a delivery log recording, for each shared resource, a monotonically increasing resource version and a read timestamp per agent workspace;

(b) an observable-read tracker that, upon each agent read operation against a shared resource, appends an entry to said delivery log binding the agent identifier, the resource path, the observed version, and a UTC read timestamp;

(c) a stale-mutation gate that, prior to committing an agent write operation, compares the agent's last observed version against a current resource version in the delivery log; and

(d) a rejection module that blocks commit of any write operation whose last observed version is strictly less than the current resource version, thereby preventing lost-update anomalies across parallel agent workspaces.

**32.** The system of claim 31, wherein shared resources include filesystem paths listed in sibling-denied-path blocklists of concurrently executing agent workspaces.

**33.** The system of claim 31, further comprising coordinating stale-mutation rejection with handoff-only gateway edges such that cross-boundary writes require publication of a serialized transaction ticket to a council bus rather than direct sibling file mutation.

**34.** The system of claim 31, wherein the delivery log is an append-only artifact persisted alongside merge governance records.

---

### Independent Claim 9 — Runtime Constraint Synthesis

**35.** A computer-implemented method for dynamically synthesizing global contract invariants with runtime execution context to govern multi-agent workflow paths, comprising:

(a) loading a Certified Operational Contract comprising static structural invariants, domain rules, and per-agent permission vectors;

(b) ingesting runtime context signals including current metrics-manifest safety state, pending handoff ticket count, worker output-log error patterns, and session-scoped project root overrides;

(c) synthesizing, by a constraint evaluator, a runtime constraint envelope that suspends or rejects workflow paths violating any combination of static invariants and runtime context thresholds;

(d) applying said runtime constraint envelope at each pipeline phase selected from the group consisting of: grid spawn, worker validation, merge integration, and upstream preflight; and

(e) emitting a deterministic rejection-reason list and a status code selected from merge-cleared and merge-rejected when any synthesized constraint is violated.

**36.** The method of claim 35, wherein synthesizing the runtime constraint envelope comprises evaluating a linear-time temporal logic monitor over a finite-state automaton of permitted orchestration subphases.

**37.** The method of claim 35, wherein runtime context signals further include a structural convergence score and a validation pass rate from a governance artifact.

**38.** The method of claim 35, further comprising overriding a localized project root for sandbox acceptance testing when an agent workspace executes in filesystem copy mode without git metadata.

---

### Cross-Cutting Dependent Claims (Representative)

**39.** The method of claim 13, wherein gateway processing mode is activated by a configuration flag designating handoff gateways in lieu of union-find atomic welds.

**40.** The method of claim 18, wherein copy-mode changed-file detection uses byte-level file comparison between an agent sandbox and a session baseline directory.

**41.** The system of claim 18, wherein protected invariant paths comprising project governance artifacts are excluded from agent merge propagation regardless of allowlist membership.

**42.** The method of claim 1, further comprising computing an Architectural Complexity Index from node count, shadow-bridge count, work-unit count, and mean negative curvature severity for pricing-tier classification.

**43.** A non-transitory computer-readable medium storing instructions that, when executed by one or more processors, cause the processors to perform the method of any of claims 1, 9, 13, 23, 27, 31, or 35.

**44.** A system comprising one or more processors and a memory storing instructions that, when executed, implement operations of any of claims 5, 18, or 31.

---

## Reduction to Practice — Empirical Evidence

| Metric | Phase 1 (tiny-service) | Phase 2 (Gaijinn monorepo) |
|--------|------------------------|----------------------------|
| Code nodes | 12 | **171** |
| Shadow bridges / gateways | — | **92** |
| Concurrent workers | 2 | **4** |
| Atomic weld blocks (gateway audit) | 0 | **0** |
| Largest legacy weld (files) | 40 | **40** |
| Files unlocked | 44 | **44** |
| Handoff ticket | TX-HT-84348F | **TX-HT-6D0B24** |
| Validation pass rate | 1.0 | **1.0** |
| Trespass violations | 0 | **0** |
| Transaction bus synchronized | true | **true** |
| Convergence | 1.0 | **0.8889** (honest no-op detection) |

Artifacts: `.gaijinn/merge/governance.json`, `handoff-queue.json`, `validated.json`, `audit-report.json`, `docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md` Section 5.

---

## Figures (Recommended for Non-Provisional Follow-On)

1. Closed infrastructure loop (scan → audit → plan → workers → merge → preflight).
2. Legacy union-find weld vs gateway HANDOFF_ONLY edge transformation.
3. HANDOFF ticket lifecycle (request → queue → receipt → bus sync).
4. Parallel Efficiency Matrix tabular output.
5. Phase 2 governance score JSON with invariant breakdown.

---

## Filing Checklist (Assignee Action Items)

- [ ] Engage registered patent attorney (software / AI systems experience).
- [ ] Complete inventor assignment and entity status (Neural Draft LLC).
- [ ] Convert independent claims to USPTO provisional format.
- [ ] Attach this specification + selected code excerpts as PDF bundle.
- [ ] File USPTO Form SB/16 provisional application ($ micro/small entity fee tier).
- [ ] Mark product and collateral **Patent Pending** upon receipt of filing date.
- [ ] Calendar 12-month non-provisional conversion deadline.

---

*Neural Draft LLC — Gaijinn. Trade secret notice applies. Do not distribute externally without NDA and attorney approval.*
\newpage

# Filing addendum — reduction to practice update

**Append to specification for filing bundle** (merged by `build-provisional-pdf.sh`)

## Additional empirical validation (2026-06-18 — 2026-06-19)

### Vault dogfood sprint (Obsidian memory vault)

| Metric | Result |
|--------|--------|
| Workers merged | 6/6 (dogfood sprint) |
| Stable work-unit IDs | Content-addressed `WU-{sha256(paths+checks)[:8]}` |
| Completion ledger | 22 entries after ADAPT recovery backfill |
| Convergence | 1.0 (production threshold) |
| Vault linter | PASS |
| Plan backlog post-ledger | 0 work units |

### Merge compounding (Claim 6 support)

Mechanisms shipped and dogfooded:

- `completion-ledger.json` — append-only, keyed by stable WU id, post-weld `content_hash`
- `already_merged` disposition in `merge-grid` (not collect) for zero-delta workers
- Ledger-aware `plan` filter excluding completed scopes
- Governance invariant `merge.merged_work` with honest convergence (no vanity 1.0 on empty merge)

Artifacts: `vaults/gaijinn-memory-fs/.gaijinn/merge/completion-ledger.json`, `governance.json`, `_multi-agent/events.md` event [63], [79].

### Monorepo Phase 2 (unchanged baseline)

171 code nodes · 4 concurrent workers · validation pass rate 1.0 · TX-HT-6D0B24 · transaction bus synchronized · convergence 0.8889 (honest no-op detection).

---

*This addendum strengthens reduction-to-practice for independent claim 6 without altering claim numbering in PART XI.*