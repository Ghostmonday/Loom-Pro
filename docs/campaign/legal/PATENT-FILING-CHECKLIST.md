# U.S. Provisional Patent Filing Checklist — Gaijinn

**Assignee (intended):** Neural Draft LLC  
**Technical spec:** `../PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md`  
**Status:** Draft — **not filed** as of 2026-06-19  
**Pro se package:** `legal/provisional-filing/` + `scripts/ops/build-provisional-pdf.sh` → `dist/provisional-filing/`

---

## Phase 1 — Inventorship & entity (before filing)

- [ ] List all inventors with legal names and contribution dates
- [ ] Execute inventor assignment agreements to Neural Draft LLC
- [ ] Confirm entity status (micro / small / large) for USPTO fees
- [ ] Engage registered patent attorney (software + AI systems)
- [ ] Provide attorney private access to `Ghostmonday/Gaijinn` under NDA

## Phase 2 — Disclosure package (GitHub → counsel)

- [ ] Attorney reviews `PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md`
- [ ] Select code excerpts (gravity, GIV, transaction bus, preflight) — redact trade-secret constants if counsel advises separate exhibit
- [ ] Attach empirical evidence: case study, governance JSON artifacts, audit reports
- [ ] Convert independent claims to USPTO provisional format
- [ ] Confirm no **public** disclosure occurred before filing date (talks, posts, open repos, customer exports)

## Phase 3 — USPTO filing

- [ ] Prepare provisional application PDF bundle
- [ ] File via USPTO Patent Center (Form SB/16)
- [ ] Pay fee tier matching entity status
- [ ] Record **filing date** and application number in private repo issue or secure ledger
- [ ] Tag repo snapshot: `patent-provisional-filed-YYYY-MM-DD` (private)

## Phase 4 — Post-filing (12-month clock)

- [ ] Mark approved collateral **Patent Pending** (website, pitch deck, enterprise materials)
- [ ] Calendar **12-month** non-provisional conversion deadline
- [ ] Track continued development in private repo for priority chain
- [ ] Do not publicly describe new claims without counsel review

## Phase 5 — GitHub hygiene (ongoing)

- [ ] Keep repository **private** until counsel approves any public component
- [ ] Merge patent-relevant changes via PR to `main` (timestamped audit trail)
- [ ] Never commit: attorney emails with strategy, USPTO filing receipts in public paths, unredacted ACI weight tables
- [ ] Annual review of collaborators, tokens, and branch protection

---

## Claim themes — PART XI (9 independent claims)

| # | Theme | Core mechanism |
|---|-------|----------------|
| 1 | Operational Contract Compilation | Prompt → multi-layer graph → COC → merge enforcement |
| 2 | Non-Invasive Capability Extraction | AST / OpenAPI / MCP scan without host mutation |
| 3 | Capability Topology Governance | Typed nodes, valid transitions, non-overlapping scopes |
| 4 | Structural Gravity Certification | Ollivier-Ricci κ, Wasserstein transport, shadow/dark bridges |
| 5 | Runtime Enforcement of Agent Boundaries | Supervisor daemon, GIV gate, drift detection, circuit breaker |
| 6 | Self-Certifying Software Architecture | Completion ledger, convergence scoring, re-certification |
| 7 | Federated Operational Contract Governance | Cross-vault links, council bus, trust-negotiated contracts |
| 8 | Observable Read Isolation (ORI) | Delivery log, read timestamps, stale-mutation rejection |
| 9 | Runtime Constraint Synthesis | Static invariants + runtime context → suspend/reject paths |

Full claim text: `../PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md` → PART XI (claims 1–44).

---

## Contacts

| Role | Contact |
|------|---------|
| Legal / trade secrets | legal@neuraldraft.net |
| Technical spec location | `docs/campaign/PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md` |
| GitHub security runbook | `GITHUB-IP-SECURITY.md` |

---

*Checklist for internal tracking. Not legal advice. Attorney must review before filing.*