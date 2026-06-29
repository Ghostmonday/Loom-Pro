---
id: "CONCEPT-VAULT-AFFAIRS"
type: "Concept"
status: "active"
promoted_from: "vault-design"
promoted_by: "worker-002"
promotion_date: "2026-06-17T22:10:00Z"
related_concepts:
  - "[[40_Concepts/memory-execution-loop]]"
  - "[[40_Concepts/vault-filesystem]]"
  - "[[40_Concepts/vault-gaijinn]]"
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/ingress-vault-civilization]]"
  - "[[40_Concepts/promotion-pipeline]]"
system_tier: "semantic"
tags:
  - Domain/Vault
  - Domain/Affairs
  - Cross-Vault
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/tasks/OBSIDIAN-RUN-16]]"
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS]]"
  - "`aoc_supervisor/aoc_supervisor/api` (monorepo)"
linked_ledgers:
  - "[[_multi-agent/events]]"
platform_ref: ".gaijinn/operations/AFFAIRS-VAULT-MAPPING.md"
sprint_merge: "2026-06-17T22:10:00Z"
---

# Vault Affairs — Life Events, Calendar, Ledger

The **Affairs vault** tracks the human and organizational timeline: what happened, when, and who decided. It is the semantic record of real-world events that drive vault evolution — sprint authorizations, constitution ratifications, binding orders, and termination events.

## Domain scope

The Affairs domain captures three classes of temporal data:

| Class | Description | Artifact |
|-------|-------------|----------|
| **Life events** | Real-world decisions & ratifications | [[30_Decisions/ADR-002-dual-invariant-domains]], [[raw/constitution-v0-section-xiii]] |
| **Calendar** | Sprint timelines, walk-away windows, dead zones | [[10_Operations/tasks/OBSIDIAN-RUN-16]] |
| **Ledger** | Append-only event log | [[_multi-agent/events]] |

## Why separate from the vault

gaijinn-memory-fs is the **system vault** — the filesystem civilization that organizes machine knowledge. Affairs is the **human vault** — the record of why and when things happened. They serve different masters:

- **System vault** (gaijinn-memory-fs): machine organization, folder taxonomy, deterministic structure
- **Affairs vault** (this concept): human intent, temporal ordering, decision provenance

This separation is a first-level partition in the dual-domain architecture [[30_Decisions/ADR-002-dual-invariant-domains|ADR-002]]. Events drive execution; execution produces knowledge; knowledge lives in the system vault.

## Governance under joint law

Affairs events trigger Gaijinn execution law. When a binding order is logged in the events ledger ([[_multi-agent/events]]), Gaijinn pipeline must act on it. The [[00_Brain/invariants/INV-GAIJINN-BINDING]] invariant ensures this coupling is hard: event → pipeline → merge → concept promotion.

### Billing integration (WU-009)

The supervisor API (`aoc_supervisor/aoc_supervisor/api` monorepo) now records billing events alongside the affairs ledger. Every `deployment_fee`, `sprint_token_issued`, and `compute_cost` event is logged to `.aoc/billing/audit.jsonl` and queryable via `POST /api/v1/billing/audit`. Billing health is published to the metrics dashboard ([[40_Concepts/metrics-dashboard]]).

See [[raw/constitution-v0-section-xiii]] for the constitutional foundation of this temporal → execution binding.

### Worker-004 validation (WU-009, WU-014)

Sprint 6 confirmed billing integration: `.aoc/billing/audit.jsonl` records every deployment_fee, sprint_token_issued, and compute_cost event. The `POST /api/v1/billing/audit` and `GET /api/v1/billing/summary` endpoints are operational. Vault.yaml linter expanded with billing-specific rules (lint-billing-audit-completeness, lint-api-billing-endpoints). The billing audit trail now feeds directly into the affairs-ledger temporal record.

## Cross-vault links

| Direction | Link |
|-----------|------|
|| Affairs → gaijinn-memory-fs (vault root) | [[README]] (vault overview — Affairs maps human timeline onto machine taxonomy) |
|| Affairs → gaijinn-memory-fs (agent bootstrap) | [[AGENTS]] (agent bootstrap reads affairs for context) |
|| Affairs → gaijinn-memory-fs (execution guidance) | [[CLAUDE]] (agent rules reference affairs-driven execution) |
|| Affairs → Gaijinn method | [[40_Concepts/vault-gaijinn]] (methodological interpretation of events) |
|| Affairs → FileSystem | [[40_Concepts/vault-filesystem]] (events produce file-level changes) |
|| Affairs → Memory Loop | [[40_Concepts/memory-execution-loop]] (the loop that turns events into action) |

## Orbit link (read-only)

> **Gaijinn Invariant Verification note:** This concept is an Affairs vault mapping. Related platform artifact: `.gaijinn/operations/AFFAIRS-VAULT-MAPPING.md` (owned by platform worker — see handoff ticket WU-002-001).

## Related

- [[README]] — gaijinn-memory-fs vault overview and infrastructure table
- [[AGENTS]] — agent bootstrap and joint governance rules
- [[CLAUDE]] — execution guidance for agents operating in the vault
- [[raw/constitution-v0-section-xiii]] — constitutional foundation for temporal governance
- [[30_Decisions/ADR-002-dual-invariant-domains]] — dual-domain architecture binding
- [[00_Brain/invariants/INV-GAIJINN-BINDING]] — invariant coupling events to execution
- [[40_Concepts/memory-execution-loop]] — the loop that cycles event → action → concept
- [[40_Concepts/vault-filesystem]] — sibling vault: machine organization
- [[40_Concepts/vault-gaijinn]] — sibling vault: methodology
