---
id: "RAW-CONSTITUTION-XIII"
type: "Raw"
status: "immutable"
source: "constitution-v0.1.0"
ratified: "2026-06-17"
system_tier: "governance"
aliases:
  - "Section XIII"
  - "Joint Governance Constitution"
tags:
  - Raw
  - Domain/Governance
  - Domain/Constitution
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
---

# Section XIII — Integration with the Gaijinn Orchestration Engine

This section governs all vault operations that invoke parallel agent execution. It was ratified as part of Constitution v0.1.0.

When a vault project activates multi-agent execution, two distinct systems of law apply simultaneously. Vault Law (Sections III through VIII) governs semantic integrity: knowledge structure, provenance, concept promotion, and graph coherence. Gaijinn governs execution integrity: work unit isolation, merge correctness, and structural convergence. These domains are complementary and non-substitutable. Compliance in one does not excuse violation of the other.

The canonical record of execution integrity is `.gaijinn/merge/governance.json`. Upon completion of any merge cycle, agents must consult this file before declaring work complete. The `structural_score` block is binding.

Agents must respect the following convergence thresholds:

- Simulated runs require structural convergence of at least 0.875.
- Production merges require structural convergence of 1.0, unless explicitly waived by an approved ADR.

Gaijinn's allowed paths serve as the execution-layer enforcement of vault write permissions. An agent may only modify files outside its private workspace if its assigned work unit's GIV explicitly permits those paths. Both vault OCC checks and Gaijinn handoff validation must pass before any change is committed.

Coordination occurs through two separate ledgers. The vault event log (`[[_multi-agent/events]]`) records semantic and ownership changes. The Gaijinn Council (`[[.gaijinn/bridge/council]]`) records operational handoffs and execution decisions. Material changes must be noted in both.

**Agent Obligations under Joint Governance:**

1. Declare the active work unit and its GIV scope before writing to any non-private directory.
2. Run both the vault knowledge linter and Gaijinn's worker validation before promoting any note from `/pending/` to `/40_Concepts/`.
3. On merge failure, agents must not force changes. They must replay according to OCC rules and re-trigger the merge process.
4. Report final sprint results to the Council, including the governance.json convergence score and any vault linter violations.
5. Maintain separate evaluation of vault metrics and Gaijinn metrics. Failure in one domain cannot be offset by success in the other.

Amendments to this section require both an Architectural Decision Record and formal ratification by the Council. See [[30_Decisions/ADR-002-dual-invariant-domains]].

---

## Related Documents

| Document | Path | Relationship |
|---|---|---|
| ADR-002: Dual Invariant Domains | [[30_Decisions/ADR-002-dual-invariant-domains]] | Technical binding — implementation appendix for Section XIII |
| INV-GAIJINN-BINDING | [[00_Brain/invariants/INV-GAIJINN-BINDING]] | Hard invariant pointer — enforces joint governance at runtime |
| Vault Event Ledger | [[_multi-agent/events]] | Semantic and ownership changes (vault layer) |
| Gaijinn Council | [[.gaijinn/bridge/council]] | Operational handoffs and execution decisions (Gaijinn layer) |
| OBSIDIAN RUN 16 | [[10_Operations/tasks/OBSIDIAN-RUN-16]] | Sprint task — first vault build under Section XIII |
