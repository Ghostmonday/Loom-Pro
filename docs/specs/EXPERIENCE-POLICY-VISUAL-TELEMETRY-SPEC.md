# Gaijinn Experience Policy + Visual Telemetry Specification

**Status:** Proposed normative contract  
**Version:** 1  
**Policy:** `ui/experience-policy.json`  
**Event schema:** `ui/orchestration-event.schema.json`  
**Snapshot schema:** `ui/orchestration-snapshot.schema.json`  
**Visual grammar:** `ui/orchestration-visual-grammar.json`

## 1. Core principle

Gaijinn has one engine and one canonical state machine. Guided, Builder, and Operator are experience projections over that engine—not separate products, state stores, or orchestration implementations.

```text
source + graph + metrics + blueprint + GIV + runtime + governance
                              |
                              v
                    canonical session state
                              |
                              v
                    canonical event journal
                              |
                              v
                 server-side policy projection
                    /          |          \
               Guided       Builder      Operator
```

Changing experience mode changes visibility and authorized controls only. It must never mutate topology, blueprint, worker ownership, handoff, merge, or governance state.

## 2. Sources of truth

The interface projects existing engine truth from these artifacts and modules:

- `aoc-cli/aoc_cli/gravity.py`: local structural gravity and directed Ollivier-Ricci edge curvature.
- `aoc-cli/aoc_cli/blueprint.py`: work-unit schema, path isolation, dependencies, risk, and deterministic ids.
- `.gaijinn/graph.json`: extracted interaction graph.
- `.gaijinn/metrics_manifest.json`: gravity and curvature analysis.
- `.gaijinn/blueprint.json`: compiled work units.
- Worker `giv.json` files: jurisdiction, capabilities, prohibitions, and invariants.
- Council/handoff records: cross-jurisdiction ticket state and receipts.
- `.gaijinn/merge/governance.json`: validation, convergence, handoff isolation, and transaction-bus state.
- `aoc_supervisor/aoc_supervisor/api.py`: current API and real SSE deliberation stages.
- `ui/gaijinn-ui-intent-map.json`: canonical browser workflow state machine.

`validate_promotion.py` is a vault-promotion overlay. It contributes promotion and convergence gates for vault projects, but it is not the universal state machine for all Gaijinn code projects.

## 3. Experience policy model

`ui/experience-policy.json` is deny-by-default. The backend resolves an actor's maximum authorized mode from authenticated account and organization policy. A client request may lower the presentation mode but may never raise it.

The effective capability set is independent of:

- project complexity class;
- billing price tier;
- current convergence;
- visual controls currently rendered by the browser.

Hidden controls are not authorization.

### 3.1 Guided

Guided is prompt-first, compiler-directed, and safety-maximal.

It may show:

- macro work-unit blocks;
- a linear stage rail;
- recommended swarm size and rationale;
- aggregate coupling-constraint counts;
- simplified isolation and handoff status;
- governance summary;
- deliverable state.

It may perform:

- blueprint approval;
- recommended swarm acceptance;
- atomic sprint launch;
- merge request;
- deliverable download.

It does not receive raw path scopes, raw curvature transport data, AST extraction diffs, full GIV clauses, raw command logs, or stack traces.

Guided must not make hidden constraints look nonexistent. It should render “12 coupling constraints handled” rather than an artificially empty graph.

### 3.2 Builder

Builder adds full inspection and safe, compiler-mediated customization.

It may additionally show:

- file/work-unit topology;
- Shadow Bridge and Dark Bridge classification;
- weld and handoff-gateway structures;
- GIV jurisdiction boundaries;
- acceptance checks;
- structured validation failures;
- handoff ticket lifecycle.

It may request:

- acceptance-check changes;
- phase-scope changes before freeze;
- swarm size and approved executor profile changes;
- a preferred weld or governed-handoff strategy.

A Builder weld/handoff choice is a request to the compiler. The compiler may accept, reject, or replace the preference. Builder never directly changes the curvature floor, absolute invariants, or path ownership.

### 3.3 Operator

Operator adds controlled structural authority.

It may additionally show:

- raw blueprint representation;
- source/AST extraction diffs;
- raw edge transport telemetry;
- full audit records;
- raw crash output after secret redaction.

It may request:

- raw blueprint patching;
- GIV path-boundary rebinding;
- absolute invariant injection;
- geometry-threshold preview and commit;
- promotion waivers where supported.

Critical mutations require reauthentication, explicit reason, optimistic concurrency, validation, and immutable audit evidence.

## 4. Non-negotiable semantic distinctions

### 4.1 Source topology is not assumed to be a DAG

The source interaction graph may contain cycles. A compiled execution plan may be acyclic, but the UI must not call the underlying code graph a DAG unless that representation has actually been verified as acyclic.

### 4.2 Project ACI is not node mass

Architectural Complexity Index is project-level pricing and receipt telemetry. It belongs in the project HUD.

A component node's visual mass is derived from local signals such as structural gravity and optional local size metadata. A work-unit block may also communicate path count and risk.

### 4.3 Edge curvature is not a Ricci-flow tensor

The current engine computes directed Ollivier-Ricci curvature for edges using neighborhood distributions and Wasserstein transport, with a risk-jump adjustment. Operator mode may expose those inputs and outputs.

The UI must not claim to expose a tensor breakdown or Ricci flow unless those computations are later implemented.

### 4.4 Dark Bridges are coupling constraints

A Dark Bridge is a severe negative-curvature edge under the active floor. It indicates a structural coupling risk requiring a weld or governed handoff. It is not automatically a circular dependency, and it should not be labeled “nondeterministic” unless a separate runtime analysis proves nondeterminism.

### 4.5 Validation and convergence are distinct

The HUD must render `validation_pass_rate` and `convergence` separately. A run may achieve complete validation with lower convergence because compliant workers had no fresh delta remaining to merge.

### 4.6 Custom geometry remains hashed

An Operator override produces `UNSAFE_GEOMETRY`, but never an “un-hashed” state. It must record baseline hash, preview id, proposed state hash, resulting hash, actor, reason, timestamp, and parent audit hash.

## 5. Transport-neutral data model

The canonical contract is transport-neutral. It may be serialized over:

- current Server-Sent Events;
- a future WebSocket endpoint;
- append-only event logs;
- deterministic replay tests;
- UI smoke-test fixtures.

The frontend consumes the same envelope regardless of transport.

### 5.1 Event envelope

Every delta validates against `ui/orchestration-event.schema.json` and includes:

```json
{
  "schema_version": 1,
  "event_id": "evt_01J...",
  "sequence": 482,
  "emitted_at": "2026-06-18T22:15:30Z",
  "session_id": "sess_abc123",
  "correlation_id": "cmd_123",
  "causation_id": "evt_01J_previous",
  "phase": "sprinting",
  "subphase": "workers_running",
  "classification": "builder",
  "event_type": "handoff.ticket.opened",
  "data": {}
}
```

`classification` is the minimum clearance needed to receive the unaggregated event. Guided may receive an aggregate replacement rather than the raw event.

### 5.2 Snapshot

Initial load, reconnect, and sequence-gap recovery use `ui/orchestration-snapshot.schema.json`.

A snapshot includes:

- effective mode and policy hash;
- canonical state hash;
- last event sequence;
- phase and subphase;
- projected topology;
- work units;
- projected GIV jurisdictions;
- workers;
- handoffs;
- governance;
- optional audit tail;
- currently available actions.

The snapshot is projected server-side. It is not the raw canonical artifact bundle.

### 5.3 Event journal behavior

Required behavior:

- Sequence increases monotonically per session.
- Delivery is at-least-once.
- Clients deduplicate by `event_id`.
- Events are applied in canonical sequence order, not animation order.
- Reconnect uses `after=<sequence>`.
- A retention miss instructs the client to fetch a fresh snapshot.
- Redaction and aggregation happen before serialization.
- Raw secrets never enter an event payload.

## 6. Proposed API surface

### 6.1 Policy discovery

```http
GET /api/v1/experience/policy
```

Example:

```json
{
  "policy_id": "gaijinn.experience-policy.v1",
  "effective_mode": "builder",
  "maximum_mode": "builder",
  "capabilities": [
    "view.graph.full",
    "view.giv.scope",
    "mutate.acceptance_checks"
  ],
  "policy_hash": "sha256:..."
}
```

### 6.2 Projected snapshot

```http
GET /api/v1/orchestrate/session/{session_id}/snapshot?mode=builder
```

The server clamps the requested mode to the actor's maximum authorization.

### 6.3 Event stream

**Pre-session deliberation (live today):**

```http
GET /api/v1/blueprint/deliberate?intent=...&stream_format=canonical
Accept: text/event-stream
```

- Before `prepare()` finishes, events use a provisional `session_id` equal to `correlation_id` (`delib-<uuid>`).
- On `phase.complete` with `phase=awaiting_swarm`, the envelope binds the real `session_id` from `prepare()`.
- `stream_format` values: `canonical` (default), `legacy`, `dual`.

**Post-freeze session replay (Phase C target):**

```http
GET /api/v1/orchestrate/session/{session_id}/events?after=482&mode=builder
Accept: text/event-stream
```

Future WebSocket form:

```text
WS /api/v1/orchestrate/session/{session_id}/events?after=482&mode=builder
```

Both carry identical event envelopes.

### 6.4 Mutations

Suggested endpoints:

```http
POST /api/v1/orchestrate/session/{session_id}/work-units/{work_unit_id}/acceptance-checks
POST /api/v1/orchestrate/session/{session_id}/topology/strategy-requests
POST /api/v1/orchestrate/session/{session_id}/blueprint/patches
POST /api/v1/orchestrate/session/{session_id}/giv/rebind
POST /api/v1/orchestrate/session/{session_id}/geometry/overrides/preview
POST /api/v1/orchestrate/session/{session_id}/geometry/overrides/commit
```

Every state-changing request includes:

```json
{
  "expected_state_hash": "sha256:...",
  "idempotency_key": "client-generated-uuid",
  "reason": "Why this change is necessary",
  "payload": {}
}
```

A stale `expected_state_hash` returns `409 Conflict`.

## 7. Geometry override protocol

A curvature-floor override is always two-stage.

### 7.1 Preview

Preview changes no canonical state.

```json
{
  "baseline_floor": -0.30,
  "proposed_floor": -0.50,
  "reason": "Controlled experiment for repository X"
}
```

The response includes:

- changed edge classifications;
- changed weld count;
- changed gateway count;
- changed work-unit count;
- newly unsafe edges;
- short-lived `preview_id` bound to the baseline hash.

### 7.2 Commit

```json
{
  "preview_id": "preview_123",
  "baseline_hash": "sha256:...",
  "impact_acknowledged": true,
  "confirmation": "COMMIT UNSAFE GEOMETRY",
  "reason": "Controlled experiment for repository X"
}
```

Commit effects:

1. Mark the session `UNSAFE_GEOMETRY`.
2. Persist a custom geometry hash.
3. Invalidate the previous partition.
4. Recompile the blueprint.
5. Regenerate GIV scopes.
6. Rerun preflight.
7. Append an audit record.

A custom floor never silently becomes the product default.

## 8. Canonical event families

### Lifecycle

- `session.snapshot`
- `phase.begin`
- `phase.progress`
- `phase.complete`
- `phase.failed`

### Topology

- `topology.node.upsert`
- `topology.edge.curvature`
- `topology.bridge.detected`
- `topology.constraints.summary`
- `topology.weld.created`
- `topology.gateway.created`
- `topology.strategy.requested`
- `topology.strategy.resolved`

### Work and jurisdiction

- `work_unit.upsert`
- `work_unit.acceptance_checks.updated`
- `work_unit.isolation.summary`
- `giv.scope.bound`
- `giv.scope.rebound`
- `worker.state.changed`

### Handoff

- `handoff.ticket.opened`
- `handoff.ticket.accepted`
- `handoff.ticket.resolved`
- `handoff.ticket.failed`

### Governance and merge

- `validation.gate.updated`
- `governance.summary.updated`
- `governance.score.updated`
- `merge.state.updated`

### Override and audit

- `blueprint.patch.applied`
- `geometry.override.previewed`
- `geometry.override.committed`
- `audit.record.created`

### Errors

- `error.summary`
- `error.detail`
- `error.raw`

Aggregation may reduce detail but may never change counts, severity, pass/fail state, or required user action.

## 9. Visual language

`ui/orchestration-visual-grammar.json` is the machine-readable visual authority.

### 9.1 Nodes

Nodes are structural blocks representing files, endpoints, states, work units, workers, or gateways.

- Mass: local structural gravity plus optional local size.
- Border: risk.
- Fill: lifecycle state.
- Halo/badge: canonical worker ownership.
- Global project ACI: separate HUD metric.

### 9.2 Parallel lanes

A green validated lane appears only after the engine has compiled non-overlapping scopes and preflight has not rejected them.

Suggested states:

- Candidate: neutral dashed corridor.
- Validated: steady corridor.
- Running: directional particles.
- Blocked: stop boundary.
- Complete: quiet solid corridor.

Non-negative curvature alone is insufficient to declare a safe lane.

### 9.3 Dark Bridges

Render as tension cables.

- Thickness reflects severity from `abs(kappa)` relative to the active floor.
- Builder sees exact κ and classification.
- Operator may inspect Wasserstein distance, neighborhood distributions, geometric curvature, and risk-jump adjustment.
- Guided sees aggregate coupling constraints.

### 9.4 Welds

A compiled weld becomes a solid enclosing bracket around paths owned by one atomic work unit.

The authoritative boundary appears only after `topology.weld.created`. A preview may be ghosted but must be visually labeled as proposed.

### 9.5 GIV jurisdictions

Jurisdictions render as semi-transparent perimeters around worker-owned scope.

- Guided: isolation badge.
- Builder: full boundary and path counts.
- Operator: exact clauses and gated rebind control.

Overlapping write jurisdiction is always an error state.

### 9.6 Handoff transactions

A handoff is a ticket, not ambient flowing context.

```text
opened -> accepted -> resolved
                \-> rejected / failed
```

The packet animation completes only when the canonical resolved event includes a receipt hash.

### 9.7 Governance HUD

Render separate instruments for:

- validation pass rate;
- convergence;
- transaction-bus synchronization;
- handoff isolation;
- merged, blocked, conflicted, and already-merged counts;
- project ACI and complexity class;
- baseline versus unsafe custom geometry.

Targets come from server configuration. Historical values such as `0.875` and `1.0` must not be hard-coded as universal gates.

A celebration effect may occur only when all configured promotion gates pass—not merely when convergence reaches 1.0.

## 10. Frontend reducer rules

The projection store is keyed by canonical ids.

Required rules:

- Upsert nodes by `node_id`.
- Upsert edges by `edge_id`.
- Upsert work units by `work_unit_id`.
- Replace a jurisdiction only when `scope_hash` changes.
- Advance handoff lifecycle monotonically unless an explicit correction event exists.
- Update governance fields independently.
- Deduplicate exact repeated `event_id` deliveries.
- Reject stale out-of-order events.
- Fetch a new snapshot after an unfillable sequence gap.
- Never derive authoritative phase from animation or worker count.

## 11. Accessibility

- Do not encode risk, status, or worker identity by color alone.
- Every animation has a static text equivalent.
- Reduced-motion mode replaces particles and vibration with strokes, badges, and text.
- Tooltips are keyboard reachable and mirrored in an inspector.
- Critical warnings remain persistent until resolved or acknowledged.

## 12. Migration from current SSE

Gaijinn already emits real deliberation events. Migration is additive.

Suggested mapping:

```text
deliberation_start      -> phase.begin (provisional_session=true)
deliberation_heartbeat  -> phase.progress
step_progress           -> phase.progress
phase_begin             -> phase.begin
phase_complete          -> phase.complete
node_added              -> topology.node.upsert
edge_curvature          -> topology.edge.curvature
dark_bridge_detected    -> topology.bridge.detected
weld_start/complete     -> topology.weld.created
handoff_gateway         -> topology.gateway.created
work_unit_assigned      -> work_unit.upsert (preview=true -> state=proposed)
deliberation_complete   -> phase.complete (phase=awaiting_swarm)
deliberation_error      -> error.summary (phase=failed)
```

### Phase A — normalize

Wrap current SSE messages in the canonical envelope and validate them against the event schema.

**Shipped in runtime:** `aoc_supervisor/orchestration_envelope.py` validates every deliberation event before serialization. Tests live in `tests/test_orchestration_envelope.py` with fixtures under `tests/fixtures/`.

### Phase B — project

Load `ui/experience-policy.json`, resolve effective mode, and redact or aggregate server-side.

### Phase C — persist

Add per-session event journal, sequence, state hash, audit head hash, snapshot, and replay.

### Phase D — mutate safely

Add Builder mutation requests and Operator preview/commit protocols.

### Phase E — WebSocket transport

Add WebSockets only when bidirectional control or reduced polling justifies it. The contract itself must not change.

## 13. Acceptance criteria

The specification is implemented when:

1. The same canonical session can be opened in all three modes without changing its state hash.
2. Client-side mode escalation does not expose a higher projection.
3. Guided receives truthful aggregates for hidden structural events.
4. Builder cannot force a threshold or path-boundary change.
5. Operator geometry changes require preview, confirmation, recompilation, GIV regeneration, preflight, and audit.
6. Event and snapshot payloads validate against their schemas.
7. A reconnect can restore state from snapshot plus replayed events.
8. Validation and convergence remain independently visible.
9. Dark Bridges, welds, jurisdictions, and handoffs are driven by canonical events rather than decorative frontend inference.
10. No projected payload contains secret material.
