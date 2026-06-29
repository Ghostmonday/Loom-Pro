# Backend-to-Frontend Traceability

## Canonical sources

- `ui/loom-system-intent-map.json` — master journey, surfaces, mandatory gates.
- `ui/loom-intent-forge-intent-map.json` — Vision Canvas elements, states, actions, and handoff.
- `ui/command-engine-ui-intent-map.json` — teleology, topology, prepare, swarm, and merge control contract.
- `ui/loom-ui-intent-map.json` — Terminal manufacturing state machine, worker grid, merge, and deliverable controls.
- `ui/loom-pipeline-intent-map.json` — canonical headless order and smoke flow.
- `ui/loom-continuation-intent-map.json` — repository attach, lineage, graph bootstrap, delta scope, and rejoin point.
- `ui/loom-deliverable-intent-map.json` — surface detection, launch presentation, run status, download, diff, and continuation lineage.
- `ui/process-stage-ux-map.json` — manufacturing stage order, risk gates, and control-point requirements.

## Derived surfaces

| Frontend Formation screen | Canonical source | Mission boundary |
|---|---|---|
| `loom.vision_canvas` | `loom-intent-forge-intent-map.json` | Vision, adaptive interrogation, readiness, confirm and accept handoff |
| `loom.command_engine` | `command-engine-ui-intent-map.json`, `loom-pipeline-intent-map.json` | Teleology, topology evidence, blueprint synthesis, approval and prepare |
| `loom.terminal` | `loom-ui-intent-map.json`, `process-stage-ux-map.json` | Swarm selection, atomic sprint, worker status, merge, retrieval |
| `loom.continuation` | `loom-continuation-intent-map.json` | Attach repository, preserve lineage, graph ingest, delta approval, handoff |
| `loom.deliverable_launch` | `loom-deliverable-intent-map.json` | Detect runnable surfaces, present product, launch, preserve lineage |

## Mandatory gates implemented by the deterministic fixture

- Handoff before teleology or prepare.
- Teleology before synthesis.
- Synthesis and user approval before prepare.
- Prepare before swarm assignment.
- Swarm assignment before sprint launch.
- Worker completion before merge.
- Clean completed merge before deliverable access or launch detection.
- Continuation graph readiness before delta scope approval.
- Continuation scope approval before handoff.
- Successful launch plus merge receipt before lineage registration.

## Action-specific projection

Every driver result returns an explicit `changed` contract-path list. Each screen controller projects only those paths. There is no global observer that refreshes every screen display after unrelated actions.

## Real versus contract-only behavior

The deterministic driver labels each result mode:

- `real_api_fixture` — fixture shaped around an existing backend endpoint.
- `real_sse_fixture` — fixture shaped around the shipped deliberation SSE contract.
- `real_api_sequence_fixture` — fixture shaped around quote, purchase, and spawn sequencing.
- `real_cli_fixture` — fixture shaped around the real graph scan/analyze CLI.
- `contract_fixture` — behavior exists in canonical Intent Mapping but the repository identifies the browser/API capability as contract-only or incomplete.

This prevents contract-only capabilities from being represented as shipped backend behavior.
