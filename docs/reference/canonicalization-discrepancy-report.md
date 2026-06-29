# Canonicalization Discrepancy and Classification Report

## Evidence traced before editing

- Runtime package identity is `loom`; the `loom` console script enters `aoc_cli.cli:app` while `aoc_cli` and `aoc_supervisor` remain compatibility package names.
- Runtime path authority is `aoc_supervisor/aoc_supervisor/repo_paths.py`; static UI routing imports its paths rather than scanning duplicate UI trees.
- Runtime frontend authority is `sandbox_frontend/`. The old `ui/` implementation is not the served HTML/CSS/JS surface; `ui/` remains the JSON contract authority.
- API routes are declared in `aoc_supervisor/aoc_supervisor/api.py`; static frontend and contract routes are delegated to `aoc_supervisor/aoc_supervisor/routers/static_ui.py`.
- Overlay v2 authority is `.loom/overlays/policy.json` plus `.loom/overlays/registry.json`, enforced fail-closed by `overlay_system.py`.
- Workflow evaluation authority is `workflow_evaluator.py`, including Perfect SPEC interrogation metrics.
- Frontend Formation has two near-identical trees. `loom-frontend-base/` has the active API driver and is mounted by runtime generated-screen fallback; `frontend-formation-complete/` is not imported by runtime and is classified inactive duplicate/reference material.
- `vaults/gaijinn-memory-fs/` contains worker/checkpoint copies with its own AGENTS scope and is excluded by Ruff; it is inactive for root runtime authority.

## Classification

| Area | Classification | Authority / disposition |
| --- | --- | --- |
| `pyproject.toml` | canonical runtime authority | Package name, dependency extras, CLI entry point. |
| `aoc-cli/aoc_cli/` | canonical runtime authority with compatibility name | Loom CLI implementation. |
| `aoc_supervisor/aoc_supervisor/api.py` | canonical runtime authority | FastAPI boundary and API route declarations. |
| `aoc_supervisor/aoc_supervisor/routers/static_ui.py` | canonical runtime authority | Static UI and contract routes. |
| `aoc_supervisor/aoc_supervisor/repo_paths.py` | canonical runtime authority | Single path map for UI contracts and sandbox frontend. |
| `ui/*.json` intent maps | canonical contract authority | Intent, workflow, UX, and contract maps. |
| `ui/*.html` | inactive duplicate | Not served by `repo_paths.py`/`static_ui.py`; preserved for now, guarded against resurrection. |
| `sandbox_frontend/` | canonical frontend runtime | Served shell, pages, shared assets, fragments. |
| `loom-frontend-base/frontend-formation/` | canonical compiler authority | Active compiler/schema/validator/generator tree. |
| `loom-frontend-base/examples/loom-source/` | canonical generated-input authority | Declarative source for generated screens. |
| `loom-frontend-base/.generated/loom/` | generated artifact | Must be regenerated from canonical sources; now marker-guarded. |
| `frontend-formation-complete/` | inactive duplicate | Preserved as historical/reference duplicate; no runtime imports allowed. |
| `.loom/overlays/policy.json`, `.loom/overlays/registry.json` | canonical overlay authority | Overlay v2 policy and registry. |
| `aoc_supervisor/aoc_supervisor/workflow_evaluator.py` | canonical workflow evaluation authority | Confusion and promotion gate evaluator. |
| `docs/specs/PERFECT-SPEC-INTERROGATION.md` | canonical specification | Active subsystem spec. |
| `docs/archive/perfect-spec/COMPOSER-START-HERE-PERFECT-SPEC.md` | historical documentation | Archived composer orchestration plan, not active authority. |
| `vaults/gaijinn-memory-fs/` | historical/generated workspace | Excluded from root runtime authority and lint. |

## Discrepancies resolved

1. Added a machine-readable authority registry so tests can enforce the intended single source of truth.
2. Archived the root-level Perfect SPEC composer plan into `docs/archive/perfect-spec/` to keep active repository root authority uncluttered.
3. Marked generated Frontend Formation outputs with a deterministic generated-file banner.
4. Added canonicalization tests preventing inactive duplicate imports, obsolete route resurrection, generated-source editing, and canonical-path drift.

## Naming overlap resolution

Loom is the product and package identity. `Gaijinn` and `AOC` names remain only as compatibility aliases in module/package paths, environment-variable aliases, historical docs, and user-facing legacy text where runtime still depends on them. No broad unsafe rename was performed.

## Perfect SPEC Interrogation status

Perfect SPEC Interrogation is an active, runtime-canonical optional subsystem driven by Intent Forge contracts and paid/adaptive session behavior. Its canonical spec is `docs/specs/PERFECT-SPEC-INTERROGATION.md`; implementation evidence is in the adaptive question engine, typed reasoning schemas, analysis types, Intent Forge service, and workflow evaluator metrics. The composer launch plan is historical and archived.
