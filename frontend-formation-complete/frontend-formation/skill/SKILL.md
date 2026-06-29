# Frontend Formation

Use this skill whenever creating or modifying a Loom screen or workspace fragment.

## Authority order

1. Canonical JSON Schemas and rule taxonomy.
2. Validator diagnostics.
3. Scaffold generator output.
4. Agent reasoning and implementation choices.

Never weaken a validator rule to make implementation pass. Repair the implementation or amend the canonical specification through an explicit architecture decision.

## Required workflow

1. Read the action registry, knowledge registry, and target screen manifest.
2. Confirm the screen has one `screen`, one `mission`, and one `mission_id`.
3. Confirm every manifest element has exactly one classification.
4. Confirm every action, contract path, feedback target, knowledge binding, accessibility declaration, and smoke scenario is explicit.
5. Generate the scaffold:

```bash
frontend-formation-generate \
  --manifest path/to/screen.manifest.yaml \
  --actions path/to/actions.registry.yaml \
  --knowledge path/to/knowledge.registry.yaml \
  --output path/to/generated-screen
```

6. Implement styling or product-specific controller integration only within the generated contract boundaries.
7. Validate the complete project:

```bash
frontend-formation-validate --project path/to/frontend-formation.yaml
```

8. On failure, repair diagnostics and rerun validation.
9. Refuse to declare the screen complete until validation exits `0`.
10. Preserve generated semantic attributes and exact manifest parity during later edits.

## Prohibitions

- No inline event handlers.
- No inferred or undeclared action IDs.
- No display without a contract path.
- No action without a display-classified feedback target.
- No silent lifecycle outcome.
- No missing knowledge domain.
- No positive `tabindex`.
- No screen without a complete smoke scenario.
- No editing generated output in a way that causes validator drift.

## Static-analysis boundary

`FFM-R002-03`, `FFM-R003-04`, and `FFM-R004-04` remain reserved because they require intent review or JavaScript/runtime analysis. Do not claim these properties were proven by the static validator.
