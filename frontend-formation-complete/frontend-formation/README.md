# Loom Frontend Formation

A deterministic frontend-formation compiler toolchain for contract-bound Loom interfaces.

It turns the seven Lean Core Rules into executable authority:

```text
Canonical schemas
      ↓
Static validator
      ↓
Deterministic scaffold generator
      ↓
SKILL.md orchestration
```

The generator produces a screen scaffold. The validator rejects contract drift across HTML, screen manifests, action registries, knowledge registries, accessibility requirements, and smoke scenarios.

## What is included

- Canonical JSON Schemas for projects, screens, actions, knowledge bindings, and smoke scenarios.
- Stable `FFM-R0XX-YY` diagnostic taxonomy.
- Project-level and single-screen validator CLI.
- Text and JSON diagnostics.
- Deterministic scaffold generator.
- Exact DOM ↔ manifest binding checks.
- Duplicate DOM and manifest ID detection.
- Screen and mission identity checks.
- Full canonical action-lifecycle declaration checks.
- Five-domain knowledge-registry resolution.
- Accessibility-safe static checks.
- Smoke-scenario structure and reference verification.
- Passing and deliberately failing fixtures.
- Pytest suite proving validation, failure behavior, deterministic generation, and regeneration safety.
- `skill/SKILL.md` for agent orchestration.

## Install

```bash
cd frontend-formation-complete
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The editable install creates:

```text
frontend-formation-validate
frontend-formation-generate
```

Generated packaging artifacts such as `*.egg-info/` are ignored and are not source files.

## Generate a screen

Start from:

- `screen.manifest.yaml`
- `actions.registry.yaml`
- `knowledge.registry.yaml`

Then run:

```bash
frontend-formation-generate \
  --manifest examples/source/screen.manifest.yaml \
  --actions examples/source/actions.registry.yaml \
  --knowledge examples/source/knowledge.registry.yaml \
  --output .generated/ratification
```

Generation is closed under validation:

```text
valid manifest + valid registries
        → generate
        → validate Rules 1–7
        → zero violations
```

The generator refuses to overwrite a nonempty output directory unless `--force` is supplied. During forced regeneration it preserves:

- `screen.custom.css`
- `screen.custom.js`

Generated semantic files remain generator-owned; product-specific extensions belong in those two preserved files.

## Validate a project

```bash
frontend-formation-validate \
  --project examples/passing/frontend-formation.yaml
```

Machine-readable output:

```bash
frontend-formation-validate \
  --project examples/passing/frontend-formation.yaml \
  --format json
```

A clean project exits `0`. Any hard violation exits `1`.

Single-screen mode is also available:

```bash
frontend-formation-validate \
  --manifest examples/passing/screen.manifest.yaml \
  --html examples/passing/index.html \
  --actions examples/passing/actions.registry.yaml \
  --knowledge examples/passing/knowledge.registry.yaml
```

## Run verification

```bash
./scripts/verify.sh
```

The verification script:

1. runs all tests;
2. confirms the passing project exits `0`;
3. confirms the failing project exits `1`.

## Repository layout

```text
frontend-formation-complete/
├── specification/
│   ├── frontend-formation.schema.json
│   ├── screen-manifest.schema.json
│   ├── action-registry.schema.json
│   ├── knowledge-registry.schema.json
│   ├── smoke-scenario.schema.json
│   └── rule-taxonomy.md
├── validator/
│   ├── engine.py
│   ├── core.py
│   ├── parser/
│   ├── rules/r001_... through r007_...
│   └── cli/main.py
├── generator/
│   ├── core.py
│   └── cli/main.py
├── skill/SKILL.md
├── examples/
│   ├── source/
│   ├── passing/
│   └── failing/
├── tests/
├── scripts/verify.sh
├── pyproject.toml
└── requirements.txt
```

## Enforced rule families

### R001 — Contract Anchoring

Rejects unclassified interactive elements, undeclared actions, displays without contract paths, semantic leakage from presentation nodes, inline handlers, and unstable semantic nodes without IDs.

### R002 — Screen Mission Singularity

Rejects missing or multiple screen roots, screen identity drift, missing DOM mission declarations, and mission identity drift.

### R003 — Strict Element Mapping

Enforces bidirectional DOM/manifest completeness and exact equality for:

- classification;
- action ID;
- contract path;
- feedback target.

It also rejects duplicate IDs on either side.

### R004 — Guaranteed Feedback Loop

Requires every action control to resolve to a DOM and manifest display target. Every declared action must include the full canonical lifecycle:

- accepted;
- pending;
- succeeded;
- rejected;
- failed;
- cancelled;
- timed out.

### R005 — Five-Domain Knowledge Binding

Requires all five domains and resolves each identifier against `knowledge.registry.yaml`:

- design intent;
- behavioral;
- operational;
- governance;
- institutional.

A domain may be declared not applicable only through an explicit justified object allowed by the schema.

### R006 — Accessibility-Safe Defaults

Rejects positive `tabindex`, redundant native roles, unnamed action controls, incomplete custom interactive semantics, and feedback displays without live-region behavior.

### R007 — Continuous Smoke Verification

Requires loadable smoke scenarios with all seven step categories and validates screen IDs, action targets, element targets, contract paths, and unique scenario IDs.

## Static-analysis boundary

Three checks remain deliberately reserved rather than falsely claimed:

- `FFM-R002-03`: deciding whether one surface contains competing user workflows requires intent-level review.
- `FFM-R003-04`: proving classification is never mutated at runtime requires JavaScript analysis or instrumentation.
- `FFM-R004-04`: proving every runtime lifecycle state is actually projected requires controller analysis or behavioral execution.

The static validator does not pretend to prove those properties. They are explicit future runtime-analysis boundaries.
