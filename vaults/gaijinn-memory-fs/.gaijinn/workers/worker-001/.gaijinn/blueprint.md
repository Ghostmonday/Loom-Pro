# Gaijinn Blueprint

## Project Goal

Deliver isolated work units for constitution, knowledge, metrics, vault while preserving GIV invariants.

## Assumptions
- Allowed paths are write scopes; workers may read broader project context as needed.
- Negative-curvature coupling welds are consolidated into atomic work units before parallel dispatch.
- Optimizing pipeline: Consolidating local coupling reviews for execution stabilization.
- Work units are generated from the scanned graph, integrity preflight, and scope lock.

## Work Units

### WU-001: Consolidate coupling review block (2 files)

Geometry-conditioned atomic block: coupling review weld binds aoc_supervisor/aoc_supervisor/intent_blueprint.py, aoc_supervisor/aoc_supervisor/prompt_coverage.py. Execute sequentially on one worker with strict scope lock.

- Estimated risk: high
- Allowed paths: aoc_supervisor/aoc_supervisor/intent_blueprint.py, aoc_supervisor/aoc_supervisor/prompt_coverage.py
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-002: json high-risk changes in repository root

Implement and validate the json files grouped by directory `.` and risk `high`.

- Estimated risk: high
- Allowed paths: project.executor-profile.json
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-003: markdown high-risk changes in repository root

Implement and validate the markdown files grouped by directory `.` and risk `high`.

- Estimated risk: high
- Allowed paths: 000_Brain_MOC.md, 010_Protocols_MOC.md, 020_Active_State_MOC.md, 030_Cold_Memories_MOC.md, CLAUDE.md, Current_Context.md, README.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-004: markdown medium-risk changes in repository root

Implement and validate the markdown files grouped by directory `.` and risk `medium`.

- Estimated risk: medium
- Allowed paths: AGENTS.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- vault_linter

### WU-005: unknown medium-risk changes in repository root

Implement and validate the unknown files grouped by directory `.` and risk `medium`.

- Estimated risk: medium
- Allowed paths: .cursorrules
- Denied paths: none
- Depends on: none
- Acceptance checks:
- vault_linter

### WU-006: unknown high-risk changes in .agents

Implement and validate the unknown files grouped by directory `.agents` and risk `high`.

- Estimated risk: high
- Allowed paths: .agents/codex-deepseek.toml.example, .agents/hermes-deepseek.env.example
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-007: yaml high-risk changes in .agents

Implement and validate the yaml files grouped by directory `.agents` and risk `high`.

- Estimated risk: high
- Allowed paths: .agents/vault.yaml
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-008: json high-risk changes in .obsidian

Implement and validate the json files grouped by directory `.obsidian` and risk `high`.

- Estimated risk: high
- Allowed paths: .obsidian/app.json, .obsidian/appearance.json, .obsidian/core-plugins.json, .obsidian/graph.json, .obsidian/workspace.json
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-009: markdown high-risk changes in 00_Brain/invariants

Implement and validate the markdown files grouped by directory `00_Brain/invariants` and risk `high`.

- Estimated risk: high
- Allowed paths: 00_Brain/invariants/INV-GAIJINN-BINDING.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-010: markdown high-risk changes in 10_Operations

Implement and validate the markdown files grouped by directory `10_Operations` and risk `high`.

- Estimated risk: high
- Allowed paths: 10_Operations/HERMES-DEVELOPMENT-ORDERS.md, 10_Operations/HERMES-MEMORY.md, 10_Operations/HERMES-SPRINT-DIRECTIVE.md, 10_Operations/VAULT-GEMINI-SHARE.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-011: python medium-risk changes in 10_Operations

Implement and validate the python files grouped by directory `10_Operations` and risk `medium`.

- Estimated risk: medium
- Allowed paths: 10_Operations/knowledge-linter.py
- Denied paths: none
- Depends on: none
- Acceptance checks:
- vault_linter

### WU-012: python high-risk changes in 10_Operations/agents/promoter

Implement and validate the python files grouped by directory `10_Operations/agents/promoter` and risk `high`.

- Estimated risk: high
- Allowed paths: 10_Operations/agents/promoter/validate_promotion.py
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-013: shell high-risk changes in 10_Operations/agents/promoter

Implement and validate the shell files grouped by directory `10_Operations/agents/promoter` and risk `high`.

- Estimated risk: high
- Allowed paths: 10_Operations/agents/promoter/promote.sh
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-014: markdown high-risk changes in 10_Operations/tasks

Implement and validate the markdown files grouped by directory `10_Operations/tasks` and risk `high`.

- Estimated risk: high
- Allowed paths: 10_Operations/tasks/topology-merges.md, 10_Operations/tasks/topology-splits.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-015: markdown medium-risk changes in 10_Operations/tasks

Implement and validate the markdown files grouped by directory `10_Operations/tasks` and risk `medium`.

- Estimated risk: medium
- Allowed paths: 10_Operations/tasks/OBSIDIAN-RUN-16.md, 10_Operations/tasks/VAULT-TOPOLOGY-SWARM.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- vault_linter

### WU-016: markdown high-risk changes in 20_Projects

Implement and validate the markdown files grouped by directory `20_Projects` and risk `high`.

- Estimated risk: high
- Allowed paths: 20_Projects/deepseek-codex-setup.md, 20_Projects/deepseek-hermes-setup.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-017: markdown medium-risk changes in 30_Decisions

Implement and validate the markdown files grouped by directory `30_Decisions` and risk `medium`.

- Estimated risk: medium
- Allowed paths: 30_Decisions/ADR-002-dual-invariant-domains.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- vault_linter

### WU-018: markdown high-risk changes in 40_Concepts

Implement and validate the markdown files grouped by directory `40_Concepts` and risk `high`.

- Estimated risk: high
- Allowed paths: 40_Concepts/convergence-governance.md, 40_Concepts/council-memory-convergence-semantics.md, 40_Concepts/council-memory-development-program.md, 40_Concepts/council-memory-empty-spawn-crisis.md, 40_Concepts/council-memory-handoff-bus.md, 40_Concepts/council-memory-hermes-mandate.md, 40_Concepts/council-memory-index.md, 40_Concepts/council-memory-infrastructure-incidents.md, 40_Concepts/council-memory-merge-compounding.md, 40_Concepts/council-memory-monorepo-state.md, 40_Concepts/council-memory-operational-hazards.md, 40_Concepts/council-memory-product-vision.md, 40_Concepts/council-memory-protocol.md, 40_Concepts/council-memory-sprint-14w-arc.md, 40_Concepts/council-memory-vault-dogfood-arc.md, 40_Concepts/dual-ledger-bridge.md, 40_Concepts/event-sourcing-vault.md, 40_Concepts/hermes-cron-orchestration.md, 40_Concepts/hermes-memory-vault.md, 40_Concepts/knowledge-linter-architecture.md, 40_Concepts/linter-core-governance.md, 40_Concepts/linter-markdown-schema.md, 40_Concepts/memory-execution-loop.md, 40_Concepts/metrics-convergence.md, 40_Concepts/metrics-gravity.md, 40_Concepts/obsidian-city-neighborhoods.md, 40_Concepts/obsidian-vault-mapping.md, 40_Concepts/promotion-pipeline.md, 40_Concepts/test-promotion-concept.md, 40_Concepts/vault-affairs.md, 40_Concepts/vault-gaijinn.md, 40_Concepts/vault-topology-and-density.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-019: markdown medium-risk changes in 40_Concepts

Implement and validate the markdown files grouped by directory `40_Concepts` and risk `medium`.

- Estimated risk: medium
- Allowed paths: 40_Concepts/council-memory-cron-topology.md, 40_Concepts/council-memory-executor-stack.md, 40_Concepts/council-memory-ux-process-stage.md, 40_Concepts/council-memory-vault-artifacts-shipped.md, 40_Concepts/ingress-vault-civilization.md, 40_Concepts/linter-supervisor-api.md, 40_Concepts/metrics-dashboard.md, 40_Concepts/metrics-linter.md, 40_Concepts/vault-filesystem.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- vault_linter

### WU-020: markdown high-risk changes in _multi-agent

Implement and validate the markdown files grouped by directory `_multi-agent` and risk `high`.

- Estimated risk: high
- Allowed paths: _multi-agent/events.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-021: markdown medium-risk changes in aoc_supervisor

Implement and validate the markdown files grouped by directory `aoc_supervisor` and risk `medium`.

- Estimated risk: medium
- Allowed paths: aoc_supervisor/README.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- vault_linter

### WU-022: python medium-risk changes in aoc_supervisor/aoc_supervisor

Implement and validate the python files grouped by directory `aoc_supervisor/aoc_supervisor` and risk `medium`.

- Estimated risk: medium
- Allowed paths: aoc_supervisor/aoc_supervisor/knowledge_linter.py, aoc_supervisor/aoc_supervisor/preflight.py, aoc_supervisor/aoc_supervisor/repo_paths.py
- Denied paths: none
- Depends on: none
- Acceptance checks:
- vault_linter

### WU-023: markdown high-risk changes in raw

Implement and validate the markdown files grouped by directory `raw` and risk `high`.

- Estimated risk: high
- Allowed paths: raw/constitution-v0-section-xiii.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-024: json high-risk changes in ui

Implement and validate the json files grouped by directory `ui` and risk `high`.

- Estimated risk: high
- Allowed paths: ui/vault-ui-intent-map.json
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-025: markdown high-risk changes in ui

Implement and validate the markdown files grouped by directory `ui` and risk `high`.

- Estimated risk: high
- Allowed paths: ui/WU-004-deploy-path-validation.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

### WU-026: Dependency cycle atomic block (12 files)

Import-cycle weld binds 3 work units and 12 file(s). Cycle-participating paths must execute on one worker.

- Estimated risk: high
- Allowed paths: aoc_supervisor/__init__.py, aoc_supervisor/aoc_supervisor/__init__.py, aoc_supervisor/aoc_supervisor/api.py, aoc_supervisor/aoc_supervisor/billing.py, aoc_supervisor/aoc_supervisor/complexity.py, aoc_supervisor/aoc_supervisor/enforcer.py, aoc_supervisor/aoc_supervisor/orchestrate_session.py, aoc_supervisor/aoc_supervisor/orchestrator.py, aoc_supervisor/aoc_supervisor/ui_intent.py, aoc_supervisor/aoc_supervisor/vault_deploy.py, aoc_supervisor/aoc_supervisor/vault_links.py, aoc_supervisor/aoc_supervisor/workflow_evaluator.py
- Denied paths: none
- Depends on: WU-022
- Acceptance checks:
- review metrics manifest for rejected nodes or Shadow Bridges
- vault_linter

## Dependencies
- WU-001: none
- WU-002: none
- WU-003: none
- WU-004: none
- WU-005: none
- WU-006: none
- WU-007: none
- WU-008: none
- WU-009: none
- WU-010: none
- WU-011: none
- WU-012: none
- WU-013: none
- WU-014: none
- WU-015: none
- WU-016: none
- WU-017: none
- WU-018: none
- WU-019: none
- WU-020: none
- WU-021: none
- WU-022: none
- WU-023: none
- WU-024: none
- WU-025: none
- WU-026: WU-022

## Risks
- 6 coupling review edge(s) detected in preflight
- One or more graph nodes are below the gravity hard floor
- Optimizing pipeline: Consolidating local coupling reviews for execution stabilization.
- WU-001: estimated high risk
- WU-002: estimated high risk
- WU-003: estimated high risk
- WU-004: estimated medium risk
- WU-005: estimated medium risk
- WU-006: estimated high risk
- WU-007: estimated high risk
- WU-008: estimated high risk
- WU-009: estimated high risk
- WU-010: estimated high risk
- WU-011: estimated medium risk
- WU-012: estimated high risk
- WU-013: estimated high risk
- WU-014: estimated high risk
- WU-015: estimated medium risk
- WU-016: estimated high risk
- WU-017: estimated medium risk
- WU-018: estimated high risk
- WU-019: estimated medium risk
- WU-020: estimated high risk
- WU-021: estimated medium risk
- WU-022: estimated medium risk
- WU-023: estimated high risk
- WU-024: estimated high risk
- WU-025: estimated high risk
- WU-026: estimated high risk
