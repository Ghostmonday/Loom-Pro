# Trade Secret and Confidential Information Notice

**DRAFT — ATTORNEY REVIEW REQUIRED**

**Internal Use Only — Neural Draft LLC Employees, Contractors, and Approved Consultants**

**Product:** Gaijinn  
**Company:** Neural Draft LLC  
**Last Updated:** June 15, 2026

---

## Purpose

This notice identifies categories of confidential information and trade secrets belonging to Neural Draft LLC in connection with the Gaijinn platform. All personnel with access to Gaijinn source code, models, infrastructure, documentation, or customer environments must treat the materials described below as strictly confidential unless expressly authorized otherwise in writing by Neural Draft management or legal counsel.

Unauthorized use or disclosure may result in disciplinary action, termination of engagement, and civil or criminal liability under applicable trade secret and confidentiality laws.

---

## Who Must Follow This Notice

This checklist applies to:

- Full-time and part-time employees of Neural Draft LLC;
- Contractors, consultants, and advisors with access to Gaijinn systems or repositories;
- Interns, beta testers with internal access, and subprocessors bound by confidentiality agreements; and
- Any individual who receives marked or unmarked confidential information relating to Gaijinn.

If you are uncertain whether information is confidential, **assume it is confidential** and consult **legal@neuraldraft.net** before disclosure.

---

## What Is Confidential

The following categories are trade secrets or confidential proprietary information of Neural Draft LLC. This list is illustrative, not exhaustive.

### 1. Architectural Complexity Index (ACI) Weights and Models

- Weight vectors, coefficients, normalization constants, and calibration tables used to compute ACI and related complexity scores;
- Training or tuning methodologies, benchmark datasets, and validation pipelines used to derive or adjust ACI inputs;
- Feature extraction logic that maps repository graphs and metrics into pricing or risk inputs;
- Any documentation, spreadsheets, notebooks, or configuration files describing ACI internals; and
- Experimental or deprecated ACI variants not released publicly.

**Do not:** share ACI weights with customers, publish them in marketing materials, commit them to public repositories, or discuss specific numeric values outside need-to-know channels.

### 2. Gravity Engine

- Source code, pseudocode, and design documents for structural gravity computation and Ollivier-Ricci curvature analysis;
- Graph preprocessing steps, edge weighting schemes, shadow-bridge detection heuristics, and rejection thresholds;
- Performance optimizations, caching strategies, and numerical methods proprietary to Neural Draft;
- Internal test fixtures, golden outputs, and regression suites revealing engine behavior; and
- Roadmap documents describing unpublished gravity-engine capabilities.

**Do not:** demonstrate unreleased engine internals in public talks, export engine modules to personal devices without authorization, or use engine artifacts to build non-Gaijinn products.

### 3. Decomposition Algorithm and Orchestration Kernel

- Algorithms that partition prompts and repository state into non-overlapping work units;
- Worker-grid assignment logic, safety contracts, path-overlap enforcement, and atomic sprint state machines;
- Blueprint compilation rules, GIV (Agent Intent Vector) defaults, and deterministic planning heuristics;
- Supervisor API orchestration flows, spawn logic, and integration boundaries with external agent runtimes; and
- Any "moat" parsing, keyword routing, or intent-compilation logic not documented for public release.

**Do not:** redistribute decomposition kernel code, describe step-by-step replication procedures in external forums, or provide kernel access to third parties without a signed agreement.

### 4. Additional Confidential Categories

Also treat as confidential unless explicitly cleared for release:

- Unreleased product designs, pricing formulas, credit-consumption rules, and integrity-score billing logic;
- Customer non-public data, repository snapshots, and sprint logs;
- Security architecture, vulnerability reports, and incident response playbooks;
- Private repository locations, credentials, license-key validation schemes, and anti-abuse mechanisms; and
- Business plans, fundraising materials, partnership terms, and M&A discussions.

---

## Employee and Contractor Checklist

Complete this checklist at onboarding and review it periodically. Mark each item when understood and compliant.

| # | Requirement | Acknowledged |
|---|-------------|--------------|
| 1 | I have read and understand this Trade Secret Notice and my confidentiality agreement. | ☐ |
| 2 | I will access Gaijinn trade secrets only on approved devices and approved accounts. | ☐ |
| 3 | I will not copy proprietary code, weights, or algorithms to personal cloud storage, public repos, or unsecured media. | ☐ |
| 4 | I understand that **ACI weights**, the **gravity engine**, and the **decomposition algorithm** are core trade secrets. | ☐ |
| 5 | I will mark drafts and exports "Confidential — Neural Draft LLC" when sharing internally on a need-to-know basis. | ☐ |
| 6 | I will not discuss unreleased technical details in public Slack/Discord, social media, conferences, or podcasts. | ☐ |
| 7 | I will report suspected leaks, lost devices, or unauthorized access immediately to **legal@neuraldraft.net**. | ☐ |
| 8 | I will return or destroy confidential materials upon termination of my engagement. | ☐ |
| 9 | I will not assist any third party in reverse engineering, cloning, or replicating Gaijinn core systems. | ☐ |
| 10 | I will confirm public documentation or demos with engineering and legal before external release. | ☐ |

**Signature:** _________________________ **Date:** _____________  
**Printed Name:** _________________________ **Role:** _____________

---

## Handling Guidelines

### Access Control

- Use company-managed hardware and MFA-enabled accounts for production and source access.
- Grant repository and production access on a least-privilege, need-to-know basis.
- Revoke access promptly when roles change or engagements end.

### Development and Testing

- Use synthetic or anonymized fixtures for public examples whenever possible.
- Do not embed ACI weights, kernel constants, or production secrets in client-side code or public CI logs.
- Scrub trade-secret values from crash reports and support bundles before external transmission.

### Communications

- In customer conversations, describe outcomes and user-facing behavior; avoid revealing proprietary algorithms or weights.
- NDAs are required before sharing roadmap details, kernel architecture, or pricing models with prospects or partners.

### Incidents

If you believe confidential information has been disclosed or exfiltrated:

1. Notify **legal@neuraldraft.net** immediately;
2. Preserve relevant logs without altering evidence;
3. Do not discuss the incident publicly until cleared by legal; and
4. Cooperate with containment and remediation steps.

---

## Marking and Classification

Materials that contain trade secrets should be labeled where practicable:

> **CONFIDENTIAL — TRADE SECRET — NEURAL DRAFT LLC — GAIJINN**

Digital assets should reside in private repositories and access-controlled storage. Public open-source releases require explicit legal and engineering approval and a review for accidental inclusion of confidential components.

---

## Relationship to Other Agreements

This notice supplements, and does not replace:

- Employment or contractor agreements;
- Mutual or unilateral non-disclosure agreements;
- Terms of Service and Privacy Policy published to customers; and
- Export control, security, and acceptable-use policies.

In the event of conflict, signed individual agreements and written direction from Neural Draft legal counsel control.

---

## Contacts

| Matter | Contact |
|--------|---------|
| Trade secret questions | **legal@neuraldraft.net** |
| Security incidents | **legal@neuraldraft.net** |
| Privacy and customer data | **privacy@neuraldraft.net** |

---

*This document is a draft internal policy prepared for operational use pending attorney review. It is not legal advice.*