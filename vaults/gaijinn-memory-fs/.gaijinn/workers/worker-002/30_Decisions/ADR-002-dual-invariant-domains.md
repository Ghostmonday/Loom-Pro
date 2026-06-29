---
id: "ADR-002"
type: "Decision"
status: "accepted"
date_decided: "2026-06-17"
deciders: ["amir", "cursor"]
supersedes: []
superseded_by: null
linked_constitution: "[[raw/constitution-v0-section-xiii]]"
system_tier: "governance"
tags:
  - Decision
  - Domain/Governance
  - Pipeline/ShadowBridge
  - Protocol/Handoff
  - Merge/Grid
---

# ADR-002 — Dual Invariant Domains (Vault Law × Gaijinn Execution)

## Status

Accepted — ratifies Section XIII and defines implementation bindings that may evolve without amending constitutional text.

## Context

The Repository Civilization Constitution (v0.1.0) governs **semantic integrity** inside an Obsidian vault: links, provenance, promotion, and graph coherence. Gaijinn governs **execution integrity** when parallel agents modify a repository: work-unit isolation, merge correctness, and structural convergence.

These are not the same invariant set. Vault orphans and dead wikilinks are knowledge-graph failures. GIV trespass and sub-threshold convergence are execution-pipeline failures. Treating them as interchangeable would let one domain mask failure in the other.

Section XIII establishes joint governance. This ADR supplies the legal-technical foundation, the **implementation appendix** (canonical paths and metric names as they exist today), and the **operational protocols** — Shadow Bridge detection, rejected node governance, handoff transactions, merge grid convergence, and OCC replay.

## Decision

1. **Two domains, one operation.** Any sprint that writes to the vault under Gaijinn must pass vault linter checks *and* Gaijinn worker validation before promotion to `/40_Concepts/`.
2. **Non-Substitution Invariant.** Vault structural health (orphan count, dead links, provenance gaps) and Gaijinn execution health (convergence, validation pass rate) are reported on separate dashboards. Success in one never waives failure in the other.
3. **Implementation bindings** (below) are versioned here. When ledger paths or metric keys change, amend this ADR — not Section XIII.
4. **Operational protocols** (below) are binding on all workers. Deviations require a new ADR or formal Council ratification.

## Consequences

- Agents have executable rules in Section XIII plus findable artifacts in this appendix.
- Refactors to `.gaijinn/` layout update ADR-002 only.
- Dogfood Vault 1 (`gaijinn-memory-fs`) is the first repository operating under dual governance.
- Shadow Bridge violations trigger automatic block-on-merge; the violating worker's output is quarantined until the Council resolves the boundary breach.
- Rejected nodes (gravity < hard floor) are tracked in the metrics manifest and follow the gravity-recovery path defined below.

---

## Operational Protocol A: Shadow Bridge Detection

A **Shadow Bridge** is a write or read that crosses a declared worker boundary without an explicit handoff ticket. It represents a failure of GIV (Gaijinn Invariant Verification) isolation.

### Detection Mechanism

The Gaijinn pipeline runs a **type-flow analysis** at two layers:

1. **Scope analysis (pre-merge):** Each worker's `allowed_paths` form a write-scope boundary. Any file write outside `allowed_paths` is a trespass. Trespass without a corresponding handoff ticket in `.gaijinn/bridge/council.jsonl` is a Shadow Bridge.
2. **Gravity analysis (post-merge):** The metrics manifest computes `gravity = raw_capability_level * side_effect_score / max_gravity`. A node with `gravity < hard_floor (0.2)` triggers automatic rejection. Nodes with `side_effect_score > 0` AND `automatic_rejection: true` are flagged for Council review.
3. **Curvature analysis:** The pipeline measures curvature between capability weights (alpha=0.7) and side effect weights (beta=0.3). A `shadow_bridge_count > 0` in `curvature_meta` blocks merge until resolved.

### Resolution

| Shadow Bridge Type | Resolution Path |
|--------------------|-----------------|
| Read trespass (agent read sibling file) | Council note — informational |
| Write trespass (agent modified sibling file) | Revert change, file handoff ticket, re-merge |
| Write trespass with worker terminal | Quarantine worker output. Council votes: adopt ± handoff or discard |
| Puncture (write to ungoverned path) | Block merge. File belongs to nobody — allocate via ADR or Council |

### Current Status

- `shadow_bridge_count: 0` — all workers within GIV scope (clean).

---

## Operational Protocol B: Rejected Node Governance

### Definition

A **rejected node** is any file in the metrics manifest whose `gravity < hard_floor (0.2)` AND `automatic_rejection: true`. These files are declared valid existentially (they belong to the project) but are excluded from the merge grid's structural scoring — they contribute zero to convergence until their gravity recovers.

### Gravity Recovery Path

A rejected node recovers when:

1. **In-degree increases:** Other nodes reference it (wikilinks, imports, config includes), raising its graph centrality.
2. **Side effect score decreases:** The file's edits become more isolated — lower boundary-crossing impact.
3. **Content maturity:** The file reaches a stable, non-draft state (production or accepted status).

### Current Rejected Nodes

All 13 files below the gravity hard floor are tracked in `.gaijinn/metrics_manifest.json > gravity_meta > rejected_nodes`:

- `.agents/vault.yaml` — gravity 0.200, automatic_rejection: true, side_effect_score 0.25
- `.cursorrules` — gravity 0.137, automatic_rejection: true
- `00_Brain/invariants/INV-GAIJINN-BINDING.md` — gravity 0.100, automatic_rejection: true
- `10_Operations/knowledge-linter.py` — gravity 0.125, automatic_rejection: true
- `10_Operations/tasks/OBSIDIAN-RUN-16.md` — gravity 0.175, automatic_rejection: true
- `20_Projects/deepseek-hermes-setup.md` — gravity 0.075, sparse_high_capability 6.0 raw — recovery expected
- `40_Concepts/memory-execution-loop.md` — gravity 0.100, automatic_rejection: true
- `CLAUDE.md` — gravity 0.200, automatic_rejection: true, side_effect_score 0.25
- `README.md` — gravity 0.066, sparse_high_capability 5.25 raw — recovery expected
- `_multi-agent/events.md` — gravity 0.175, automatic_rejection: true
- `project.executor-profile.json` — gravity 0.050, automatic_rejection: true
- `raw/constitution-v0-section-xiii.md` — gravity 0.088, automatic_rejection: true
- `ui/vault-ui-intent-map.json` — gravity 0.137, automatic_rejection: true

**Notes:**
- Files removed from the rejected list since previous ADR edition: `.agents/hermes-deepseek.env.example` (gravity now 0.225, above floor), `30_Decisions/ADR-002-dual-invariant-domains.md` (gravity now 0.238, above floor), `AGENTS.md` (gravity now 0.250, above floor).
- `.agents/hermes-deepseek.env.example`, `30_Decisions/ADR-002-dual-invariant-domains.md`, and `AGENTS.md` are no longer rejected due to increased in-degree or decreased side-effect scores from cross-linking during the sprint.
- **Policy:** No rejected node is eligible for the merge grid's structural_score until at least one other node references it (in_degree > 0) OR its gravity exceeds 0.2.

---

## Operational Protocol C: Handoff Transactions

### Definition

A **handoff ticket** is a structured JSON payload written to `.gaijinn/bridge/council.jsonl` when a worker requires mutation of a sibling-owned path. It follows this schema:

```json
{
  "type": "handoff",
  "source_worker": "worker-NNN",
  "target_work_unit_id": "WU-NNN",
  "target_file": "path/to/file",
  "required_mutation_context": "What the source worker needs",
  "status": "open|fulfilled|rejected",
  "timestamp": "2026-06-17T19:40:00Z"
}
```

### Lifecycle

1. **OPEN** — Source worker emits ticket. Merge grid pauses on this path.
2. **FULFILLED** — Target worker writes approved content. Council marks ticket resolved.
3. **REJECTED** — Council determines the request is out of scope. Source worker must find alternative approach.
4. **EXPIRED** — Ticket open past the sprint window (30 min default). Merge grid auto-blocks.

### Enforcement

- The handoff gateway operates in dark-bridge mode: handoff tickets are transaction boundaries, not atomic welds.
- If a worker writes to a sibling path without a FULFILLED handoff ticket, the write is a trespass (see Protocol A).
- The coordination ledger (`council.md`) and the vault event log (`events.md`) both record material handoff state changes.

---

## Operational Protocol D: Merge Grid Convergence

### Structural Scoring

The **merge grid** evaluates sprint convergence via a composite `structural_score`:

```
structural_score = Σ(worker_convergence_i × weight_i) / Σ(weight_i)
```

Where each worker's convergence is:

```
worker_convergence = pass_rate(path_scope_valid, handoff_fresh, lint_clean, test_pass)
```

### Convergence Thresholds

| Mode | Threshold | Waivable? |
|------|-----------|-----------|
| Simulated (mock grid / dry run) | ≥ 0.875 | No — hard gate |
| Production | 1.000 | Yes — by ADR with documented partial state |

### Merge Failures

On merge failure (structural_score below threshold OR any worker fails validation):

1. **No force-overwrites.** All changes are retained in worker scratch space.
2. **OCC replay.** Workers re-apply their changes against the current merge base, resolving conflicts per Optimistic Concurrency Control rules:
   - Conflicts are detected by content hash, not line position.
   - The worker that wrote first in the sprint wins priority.
   - The losing worker's change is quarantined and flagged to the Council.
3. **Re-trigger.** Merge grid recomputes structural_score with resolved conflicts.
4. **Circuit breaker.** If 3 consecutive merges fail, the sprint halts. Council must approve a waive or rollback.

### Current Metrics

From `.gaijinn/metrics_manifest.json > merge_governance > latest` (production run scored `2026-06-18T02:45:03Z`):
- `convergence: 0.6667` (below production threshold 1.0)
- `validation_pass_rate: 1.0`
- `handoff_isolation: true`
- `transaction_bus_synchronized: true`
- `blocked_workers: 14`
- `merged_workers: 0`
- `merge_order_valid: false`
- `conflict_free: true`
- `conflicted_workers: 0`

The canonical `.gaijinn/merge/governance.json` artifact is currently absent in the vault root. The metrics manifest mirrors the latest merge-governance block, and the current full knowledge-linter gate fails on sub-threshold production convergence.

---

## Operational Protocol E: OCC Replay Mechanics

### Rules

1. **Content-hash conflict detection.** Two workers conflict iff the same file's content hash differs in their isolated copies AND both wrote to it.
2. **Timestamp priority.** The worker whose write timestamp is earlier in the sprint window wins.
3. **Quarantine.** The losing worker's change is moved to `.gaijinn/merge/quarantine/<worker-id>/` for Council review.
4. **Structural score drain.** Each unresolved conflict deducts 0.05 from the structural_score.
5. **GIV re-validation.** After conflict resolution, the winning worker's entire output is re-validated against GIV (all paths, no handoff trespass).

### Quarantine Path

```
.gaijinn/merge/quarantine/
  worker-00N/
    <file>.<hash>.conflict
```

---

## Implementation Appendix (current bindings)

*These paths and keys are operational facts, not constitutional law. Update via ADR amendment.*

```yaml
Current Execution Ledger:
  path: .gaijinn/merge/governance.json
  writer: merge-grid structural scoring (idempotent)

Current Health Block:
  key: structural_score

Binding Metrics:
  validation_pass_rate:
    meaning: Fraction of workers passing path, scope, handoff, and test gates
  convergence:
    meaning: Composite structural score — merge eligibility, topological order,
             transactional concurrency synchronization, idempotent validation routing
  handoff_isolation:
    meaning: Zero sibling-path trespass across validated workers
  transaction_bus_synchronized:
    meaning: All handoff tickets resolved before merge completion

Convergence Thresholds:
  simulated: 0.875   # mock-grid / dry-run evaluation
  production: 1.000  # unless waived by ADR with documented partial state

Coordination Ledgers:
  vault_semantic: _multi-agent/events.md
  gaijinn_operational: .gaijinn/bridge/council.md

Namespace Enforcement:
  vault_write_paths: .agents/vault.yaml
  gaijinn_allowed_paths: work unit GIV (blueprint allowed_paths)

Promotion Gate:
  vault: knowledge_linter.py clean
  gaijinn: validate-worker passed
  target: /pending/ → /40_Concepts/
```

## Metrics Manifest Bindings

The metrics manifest (`.gaijinn/metrics_manifest.json`) is the **sole source of truth** for pipeline health. Its structure mirrors the dual domains:

| Section | Domain | Purpose |
|---------|--------|---------|
| `gravity_meta` | Gaijinn | File-level gravity, capability, side effects, rejection status |
| `curvature_meta` | Gaijinn | Cross-boundary curvature, Shadow Bridge detection |
| `reflective_meta` | Gaijinn | Topological inference, type-flow analysis, lifecycle chains |
| `inferred_path` | Gaijinn | Layer 2 inferred model path |

All five operational protocols in this ADR read from or write to the metrics manifest. The manifest is produced by `gaijinn grid spawn` and consumed by the merge grid.

---

## Dogfood waiver (LEARN sprint)

Documented partial state: copy-mode vault workers may validate with no filesystem delta when
artifacts were promoted inline. Governance treats validation-pass + idle-no-change workers as
non-blocking; convergence may read &lt; 1.0 until all slices produce mergeable deltas.

## Related

- [[raw/constitution-v0-section-xiii]] — Section XIII (constitutional text)
- [[00_Brain/invariants/INV-GAIJINN-BINDING]] — hard invariant pointer
- [[.gaijinn/metrics_manifest.json]] — pipeline health source of truth
- [[.gaijinn/merge/governance.json]] — execution ledger
