# worker-001 Work Units

## WU-001: Consolidate coupling review block (2 files)

Geometry-conditioned atomic block: coupling review weld binds aoc_supervisor/aoc_supervisor/intent_blueprint.py, aoc_supervisor/aoc_supervisor/prompt_coverage.py. Execute sequentially on one worker with strict scope lock.

- Estimated risk: high
- Allowed paths: aoc_supervisor/aoc_supervisor/intent_blueprint.py, aoc_supervisor/aoc_supervisor/prompt_coverage.py
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-003: markdown high-risk changes in repository root

Implement and validate the markdown files grouped by directory `.` and risk `high`.

- Estimated risk: high
- Allowed paths: 000_Brain_MOC.md, 010_Protocols_MOC.md, 020_Active_State_MOC.md, 030_Cold_Memories_MOC.md, CLAUDE.md, Current_Context.md, README.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-005: unknown medium-risk changes in repository root

Implement and validate the unknown files grouped by directory `.` and risk `medium`.

- Estimated risk: medium
- Allowed paths: .cursorrules
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - vault_linter

## WU-007: yaml high-risk changes in .agents

Implement and validate the yaml files grouped by directory `.agents` and risk `high`.

- Estimated risk: high
- Allowed paths: .agents/vault.yaml
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-009: markdown high-risk changes in 00_Brain/invariants

Implement and validate the markdown files grouped by directory `00_Brain/invariants` and risk `high`.

- Estimated risk: high
- Allowed paths: 00_Brain/invariants/INV-GAIJINN-BINDING.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-011: python medium-risk changes in 10_Operations

Implement and validate the python files grouped by directory `10_Operations` and risk `medium`.

- Estimated risk: medium
- Allowed paths: 10_Operations/knowledge-linter.py
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - vault_linter

## WU-013: shell high-risk changes in 10_Operations/agents/promoter

Implement and validate the shell files grouped by directory `10_Operations/agents/promoter` and risk `high`.

- Estimated risk: high
- Allowed paths: 10_Operations/agents/promoter/promote.sh
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-015: markdown medium-risk changes in 10_Operations/tasks

Implement and validate the markdown files grouped by directory `10_Operations/tasks` and risk `medium`.

- Estimated risk: medium
- Allowed paths: 10_Operations/tasks/OBSIDIAN-RUN-16.md, 10_Operations/tasks/VAULT-TOPOLOGY-SWARM.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - vault_linter

## WU-017: markdown medium-risk changes in 30_Decisions

Implement and validate the markdown files grouped by directory `30_Decisions` and risk `medium`.

- Estimated risk: medium
- Allowed paths: 30_Decisions/ADR-002-dual-invariant-domains.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - vault_linter

## WU-019: markdown medium-risk changes in 40_Concepts

Implement and validate the markdown files grouped by directory `40_Concepts` and risk `medium`.

- Estimated risk: medium
- Allowed paths: 40_Concepts/council-memory-cron-topology.md, 40_Concepts/council-memory-executor-stack.md, 40_Concepts/council-memory-ux-process-stage.md, 40_Concepts/council-memory-vault-artifacts-shipped.md, 40_Concepts/ingress-vault-civilization.md, 40_Concepts/linter-supervisor-api.md, 40_Concepts/metrics-dashboard.md, 40_Concepts/metrics-linter.md, 40_Concepts/vault-filesystem.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - vault_linter

## WU-021: markdown medium-risk changes in aoc_supervisor

Implement and validate the markdown files grouped by directory `aoc_supervisor` and risk `medium`.

- Estimated risk: medium
- Allowed paths: aoc_supervisor/README.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - vault_linter

## WU-023: markdown high-risk changes in raw

Implement and validate the markdown files grouped by directory `raw` and risk `high`.

- Estimated risk: high
- Allowed paths: raw/constitution-v0-section-xiii.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter

## WU-025: markdown high-risk changes in ui

Implement and validate the markdown files grouped by directory `ui` and risk `high`.

- Estimated risk: high
- Allowed paths: ui/WU-004-deploy-path-validation.md
- Denied paths: none
- Depends on: none
- Acceptance checks:
  - review metrics manifest for rejected nodes or Shadow Bridges
  - vault_linter
