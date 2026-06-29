---
id: "INV-GAIJINN-BINDING"
type: "Invariant"
status: "accepted"
enforcement_level: "hard"
scope: "global"
tags:
  - Invariant
  - Domain/Governance
---

# INV-GAIJINN-BINDING — Joint Vault × Gaijinn Governance

When parallel agent execution is active, vault operations are bound by Section XIII and ADR-002.

## Hard Rules

1. Vault Law and Gaijinn execution law apply simultaneously; neither substitutes for the other.
2. Consult the execution ledger before declaring any sprint complete.
3. Respect convergence thresholds (simulated ≥ 0.875, production = 1.0 unless ADR-waived).
4. Material changes require notation in both `_multi-agent/events.md` and Council.

## Authority

- Constitutional: [[raw/constitution-v0-section-xiii]]
- Technical binding: [[30_Decisions/ADR-002-dual-invariant-domains]]