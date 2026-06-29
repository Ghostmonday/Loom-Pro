# Loom Frontend Formation — Corrected Backend-Grounded Package

This package transforms the supplied three-screen draft into a compiler-valid Loom frontend contract package grounded in the repository's canonical Intent Maps.

## What changed

The draft's invented `loom.intake`, `loom.refinement`, and `loom.execution` model was replaced by the five actual user-facing Loom surfaces:

1. `loom.vision_canvas`
2. `loom.command_engine`
3. `loom.terminal`
4. `loom.continuation`
5. `loom.deliverable_launch`

The headless `loom-backend-pipeline` remains a mirror specification, not a browser screen.

Canonical actions replace invented names. The package uses actions such as `intake.start_session`, `question.submit_answer`, `handoff.confirm`, `teleology.deliberate`, `blueprint.synthesize`, `orchestrate.prepare`, `orchestrate.swarm`, `deploy.sprint`, `merge.run`, and the Continuation and Deliverable contracts.

## Verified results

The included build was executed against the bundled `frontend-formation` toolchain.

```json
{
  "checked_screens": 5,
  "error_count": 0,
  "passed": true,
  "violations": [],
  "warning_count": 0
}
```

Additional checks:

- Frontend Formation toolchain tests: 5 passed.
- JavaScript syntax: 15 files passed `node --check`.
- CSS syntax: 10 files parsed with zero errors.
- Chromium runtime: 11 checks passed; zero console errors and zero page errors.
- Gate proof: Terminal rejects swarm assignment before Command Engine preparation.
- Contract proof: action execution did not mutate `data-classification`, `data-action`, `data-contract-path`, or `data-feedback-target`.

Reports are under `reports/`.

## Build

```bash
python scripts/create_sources.py
python scripts/create_extensions.py
python scripts/build.py
python scripts/browser_check.py
```

The aggregate compiler project is:

```text
.generated/loom/frontend-formation.all.yaml
```

## Package layout

```text
examples/loom-source/        Declarative source registries and five manifests
extension-src/               Deterministic driver and preserved screen extensions
frontend-formation/          Bundled compiler toolchain
.generated/loom/             Generated and assembled screen projects
reports/                     Actual validation, syntax, CSS, and Chromium results
scripts/                     Reproducible source, build, CSS, and browser checks
```

## Important boundary

This is the strongest correct artifact possible without changing Frontend Formation v1. The current screen schema cannot express textareas, text inputs, selects, navigation links, dynamic agent grids, SVG/canvas topology, or arbitrary ARIA attributes. Consequently this package is a validated semantic shell and deterministic backend-contract simulator, not yet the final production browser client. See `LIMITATIONS.md`.
