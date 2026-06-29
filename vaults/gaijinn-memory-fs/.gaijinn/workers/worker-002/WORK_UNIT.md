# worker-002 Work Units

## WU-002: json high-risk changes in repository root

Implement and validate the json files grouped by directory `.` and risk `high`.

- Estimated risk: high
- Allowed paths: project.executor-profile.json
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-004: markdown medium-risk changes in repository root

Implement and validate the markdown files grouped by directory `.` and risk `medium`.

- Estimated risk: medium
- Allowed paths: AGENTS.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - vault_linter

## WU-006: unknown high-risk changes in .agents

Implement and validate the unknown files grouped by directory `.agents` and risk `high`.

- Estimated risk: high
- Allowed paths: .agents/codex-deepseek.toml.example, .agents/hermes-deepseek.env.example
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-008: json high-risk changes in .obsidian

Implement and validate the json files grouped by directory `.obsidian` and risk `high`.

- Estimated risk: high
- Allowed paths: .obsidian/app.json, .obsidian/appearance.json, .obsidian/core-plugins.json, .obsidian/graph.json, .obsidian/workspace.json
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-010: markdown high-risk changes in 10_Operations

Implement and validate the markdown files grouped by directory `10_Operations` and risk `high`.

- Estimated risk: high
- Allowed paths: 10_Operations/HERMES-DEVELOPMENT-ORDERS.md, 10_Operations/HERMES-MEMORY.md, 10_Operations/HERMES-SPRINT-DIRECTIVE.md, 10_Operations/VAULT-GEMINI-SHARE.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-012: python high-risk changes in 10_Operations/agents/promoter

Implement and validate the python files grouped by directory `10_Operations/agents/promoter` and risk `high`.

- Estimated risk: high
- Allowed paths: 10_Operations/agents/promoter/validate_promotion.py
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-014: markdown high-risk changes in 10_Operations/tasks

Implement and validate the markdown files grouped by directory `10_Operations/tasks` and risk `high`.

- Estimated risk: high
- Allowed paths: 10_Operations/tasks/topology-merges.md, 10_Operations/tasks/topology-splits.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-016: markdown high-risk changes in 20_Projects

Implement and validate the markdown files grouped by directory `20_Projects` and risk `high`.

- Estimated risk: high
- Allowed paths: 20_Projects/deepseek-codex-setup.md, 20_Projects/deepseek-hermes-setup.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-018: markdown high-risk changes in 40_Concepts

Implement and validate the markdown files grouped by directory `40_Concepts` and risk `high`.

- Estimated risk: high
- Allowed paths: 40_Concepts/convergence-governance.md, 40_Concepts/council-memory-convergence-semantics.md, 40_Concepts/council-memory-development-program.md, 40_Concepts/council-memory-empty-spawn-crisis.md, 40_Concepts/council-memory-handoff-bus.md, 40_Concepts/council-memory-hermes-mandate.md, 40_Concepts/council-memory-index.md, 40_Concepts/council-memory-infrastructure-incidents.md, 40_Concepts/council-memory-merge-compounding.md, 40_Concepts/council-memory-monorepo-state.md, 40_Concepts/council-memory-operational-hazards.md, 40_Concepts/council-memory-product-vision.md, 40_Concepts/council-memory-protocol.md, 40_Concepts/council-memory-sprint-14w-arc.md, 40_Concepts/council-memory-vault-dogfood-arc.md, 40_Concepts/dual-ledger-bridge.md, 40_Concepts/event-sourcing-vault.md, 40_Concepts/hermes-cron-orchestration.md, 40_Concepts/hermes-memory-vault.md, 40_Concepts/knowledge-linter-architecture.md, 40_Concepts/linter-core-governance.md, 40_Concepts/linter-markdown-schema.md, 40_Concepts/memory-execution-loop.md, 40_Concepts/metrics-convergence.md, 40_Concepts/metrics-gravity.md, 40_Concepts/obsidian-city-neighborhoods.md, 40_Concepts/obsidian-vault-mapping.md, 40_Concepts/promotion-pipeline.md, 40_Concepts/test-promotion-concept.md, 40_Concepts/vault-affairs.md, 40_Concepts/vault-gaijinn.md, 40_Concepts/vault-topology-and-density.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-020: markdown high-risk changes in _multi-agent

Implement and validate the markdown files grouped by directory `_multi-agent` and risk `high`.

- Estimated risk: high
- Allowed paths: _multi-agent/events.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-022: python medium-risk changes in aoc_supervisor/aoc_supervisor

Implement and validate the python files grouped by directory `aoc_supervisor/aoc_supervisor` and risk `medium`.

- Estimated risk: medium
- Allowed paths: aoc_supervisor/aoc_supervisor/knowledge_linter.py, aoc_supervisor/aoc_supervisor/preflight.py, aoc_supervisor/aoc_supervisor/repo_paths.py
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - vault_linter

## WU-024: json high-risk changes in ui

Implement and validate the json files grouped by directory `ui` and risk `high`.

- Estimated risk: high
- Allowed paths: ui/vault-ui-intent-map.json
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-026: Dependency cycle atomic block (12 files)

Import-cycle weld binds 3 work units and 12 file(s). Cycle-participating paths must execute on one worker.

- Estimated risk: high
- Allowed paths: aoc_supervisor/__init__.py, aoc_supervisor/aoc_supervisor/__init__.py, aoc_supervisor/aoc_supervisor/api.py, aoc_supervisor/aoc_supervisor/billing.py, aoc_supervisor/aoc_supervisor/complexity.py, aoc_supervisor/aoc_supervisor/enforcer.py, aoc_supervisor/aoc_supervisor/orchestrate_session.py, aoc_supervisor/aoc_supervisor/orchestrator.py, aoc_supervisor/aoc_supervisor/ui_intent.py, aoc_supervisor/aoc_supervisor/vault_deploy.py, aoc_supervisor/aoc_supervisor/vault_links.py, aoc_supervisor/aoc_supervisor/workflow_evaluator.py
- Denied paths: none
- Depends on: WU-022
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter
