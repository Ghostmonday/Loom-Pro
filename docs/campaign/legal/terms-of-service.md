# Terms of Service

**DRAFT — ATTORNEY REVIEW REQUIRED**

**Effective Date:** [To be determined upon publication]  
**Last Updated:** June 15, 2026

These Terms of Service ("**Terms**") constitute a binding agreement between you ("**you**," "**Customer**," or "**User**") and **Neural Draft LLC**, a limited liability company organized under the laws of the United States ("**Neural Draft**," "**we**," "**us**," or "**our**"), governing your access to and use of the Gaijinn software platform, including the CLI, APIs, supervisor services, web interfaces, documentation, and related offerings (collectively, the "**Service**").

**BY ACCESSING OR USING THE SERVICE, YOU AGREE TO THESE TERMS. IF YOU DO NOT AGREE, DO NOT USE THE SERVICE.**

If you use the Service on behalf of an organization, you represent that you have authority to bind that organization, and "you" refers to that organization.

---

## 1. The Service

Gaijinn provides tools for repository analysis, architectural risk assessment, deterministic blueprint generation, worker-grid orchestration, and atomic sprint execution. Features may vary by plan, license tier, and product version. We may modify, suspend, or discontinue features with reasonable notice where practicable.

---

## 2. Proprietary Software — Not Open Source

**The Service is proprietary commercial software licensed by Neural Draft LLC. It is NOT open source software**, notwithstanding any separate open-source components that may be identified in third-party notices.

Except as expressly permitted in these Terms or a written agreement signed by Neural Draft:

- You receive a limited, non-exclusive, non-transferable, revocable license to use the Service for your internal business purposes or personal development, subject to your plan limits;
- You may **not** copy, modify, adapt, translate, or create derivative works of the Service or any portion thereof;
- You may **not** reverse engineer, decompile, disassemble, or otherwise attempt to derive source code, algorithms, models, or trade secrets from the Service, except to the limited extent such restriction is prohibited by applicable law;
- You may **not** remove, obscure, or alter proprietary notices; and
- You may **not** sublicense, resell, host for third parties, or use the Service to build a competing product without our prior written consent.

No rights are granted except as expressly stated. All rights not granted are reserved by Neural Draft and its licensors.

---

## 3. Decomposition Kernel and Redistribution Restrictions

The Gaijinn **decomposition kernel**—including algorithms that partition work units, compute non-overlapping worker assignments, enforce safety contracts, and related orchestration logic—is confidential and proprietary.

You agree that you will **not**:

- Redistribute, publish, or disclose the decomposition kernel or any substantial portion of its logic;
- Extract kernel outputs for the purpose of reconstructing or replicating the kernel;
- Use the Service to develop or train a substitute decomposition or grid-orchestration product intended to replicate Gaijinn's core functionality; or
- Permit any third party to do any of the foregoing on your behalf.

Limited exports of your own project artifacts (for example, blueprints and metrics generated for your repositories) are permitted only where the Service explicitly provides export functionality and such exports do not include Neural Draft's proprietary software, object code, or confidential algorithms.

---

## 4. Accounts, Licenses, and Acceptable Use

You must provide accurate registration information and maintain the security of your credentials and license keys. You are responsible for all activity under your account.

You agree not to:

- Violate applicable law or third-party rights;
- Upload malware or attempt unauthorized access to our systems or other users' data;
- Interfere with Service integrity, rate limits, or security controls;
- Misrepresent entitlement to credits, plans, or enterprise features; or
- Use the Service in high-risk environments where failure could cause death, personal injury, or catastrophic physical damage without a separate written enterprise agreement.

We may suspend or terminate access for violations of these Terms or conduct that creates legal or security risk.

---

## 5. Credit-Based Billing and Integrity Score Pricing

The Service uses a **credit-based billing model**. Credits are consumed when you initiate billable operations, which may include repository analysis, blueprint compilation, grid orchestration, atomic sprint deployment, and related API calls as described in your plan documentation.

**Integrity score pricing** means that credit consumption may vary based on architectural complexity metrics, including indices such as the Architectural Complexity Index (ACI), curvature/gravity risk scores, worker count, and sprint scope. Pricing inputs are calculated from Service-generated artifacts and displayed or logged at or before the point of commitment where feasible.

By initiating a billable operation, you authorize Neural Draft to deduct the applicable credits or charge your payment method according to your plan. Credit balances are non-transferable except where we expressly allow otherwise. Unused credits may expire as stated in your plan terms.

Fees are exclusive of taxes unless stated otherwise. You are responsible for applicable sales, use, VAT, or similar taxes, excluding taxes based on Neural Draft's net income.

---

## 6. Atomic Deploy — No Refund Once Started

Certain Gaijinn operations constitute an **atomic deploy** or **atomic sprint**: once initiated, the operation allocates compute resources, provisions worker cells, writes orchestration state, and executes irreversible deployment steps as a single transactional unit.

**YOU ACKNOWLEDGE AND AGREE THAT FEES AND CREDITS ASSOCIATED WITH AN ATOMIC DEPLOY OR ATOMIC SPRINT ARE NON-REFUNDABLE ONCE THE OPERATION HAS STARTED**, including where:

- The sprint partially completes;
- Workers fail due to issues in your repository, environment, or third-party tooling;
- You abort or cancel after provisioning has begun; or
- Results do not meet your subjective expectations but the Service performed as documented.

Refunds or credit adjustments, if any, are provided only where required by law or expressly stated in a written enterprise agreement. Nothing in this section limits your rights under non-waivable consumer protections in your jurisdiction.

Before starting an atomic deploy, review displayed credit estimates, integrity scores, and scope confirmations.

---

## 7. Your Data and Projects

You retain ownership of your repositories, prompts, and project materials. You grant Neural Draft a limited license to host, process, transmit, and display your content solely to provide and improve the Service, secure our systems, and comply with law, as further described in our Privacy Policy.

You represent that you have all rights necessary to submit project data to the Service and that your use does not infringe third-party intellectual property or confidentiality obligations.

---

## 8. Confidentiality and Trade Secrets

Each party may receive confidential information from the other. Neural Draft's confidential information includes the Service's unpublished features, pricing algorithms, decomposition kernel, gravity engine weighting, ACI models, and non-public documentation.

You agree to protect our confidential information using at least reasonable care and to use it only as permitted by these Terms. Trade secret protections survive termination.

---

## 9. Third-Party Services

The Service may interoperate with third-party tools, including AI coding agents, version control platforms, and payment processors. Third-party services are governed by their own terms. Neural Draft is not responsible for third-party outages, data handling, or model behavior outside our control.

---

## 10. Disclaimers

**THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE."** TO THE MAXIMUM EXTENT PERMITTED BY LAW, NEURAL DRAFT DISCLAIMS ALL WARRANTIES, WHETHER EXPRESS, IMPLIED, OR STATUTORY, INCLUDING IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT.

We do not warrant that the Service will be uninterrupted, error-free, or free of harmful components, or that analysis results, blueprints, or sprint outcomes will be correct, complete, or suitable for production deployment without your independent verification.

Gaijinn assists with orchestration and architectural analysis; **you remain solely responsible** for code review, testing, security assessment, and deployment decisions.

---

## 11. Limitation of Liability

**TO THE MAXIMUM EXTENT PERMITTED BY LAW:**

- NEURAL DRAFT AND ITS AFFILIATES, OFFICERS, MEMBERS, EMPLOYEES, AND AGENTS WILL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES, OR FOR ANY LOSS OF PROFITS, REVENUE, DATA, GOODWILL, OR BUSINESS INTERRUPTION, ARISING OUT OF OR RELATED TO THE SERVICE OR THESE TERMS, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES; AND

- NEURAL DRAFT'S TOTAL AGGREGATE LIABILITY FOR ALL CLAIMS ARISING OUT OF OR RELATED TO THE SERVICE OR THESE TERMS WILL NOT EXCEED THE GREATER OF (A) THE AMOUNTS YOU PAID TO NEURAL DRAFT FOR THE SERVICE IN THE TWELVE (12) MONTHS PRECEDING THE EVENT GIVING RISE TO THE CLAIM, OR (B) ONE HUNDRED U.S. DOLLARS (US $100).

These limitations apply regardless of the theory of liability and even if any remedy fails of its essential purpose. Some jurisdictions do not allow certain limitations; in those cases, our liability is limited to the fullest extent permitted by law.

---

## 12. Indemnification

You will defend, indemnify, and hold harmless Neural Draft and its affiliates, officers, members, employees, and agents from and against claims, damages, losses, and expenses (including reasonable attorneys' fees) arising out of or related to: (a) your content or projects; (b) your use of the Service in violation of these Terms or law; or (c) your violation of third-party rights.

---

## 13. Term and Termination

These Terms remain in effect while you use the Service. You may stop using the Service at any time. We may suspend or terminate your access for material breach, non-payment, security risk, or discontinuation of the Service.

Upon termination, your license ends and you must cease use of the Service. Sections that by their nature should survive (including proprietary rights, payment obligations, disclaimers, limitation of liability, indemnification, and dispute resolution) will survive termination.

---

## 14. Dispute Resolution and Arbitration (Optional)

**Informal resolution.** Before initiating formal proceedings, you agree to contact **legal@neuraldraft.net** and attempt to resolve disputes informally for at least thirty (30) days.

**Optional arbitration.** Except for claims seeking injunctive relief for misuse of intellectual property or unauthorized access, either party **may elect** to resolve disputes arising out of these Terms through binding individual arbitration administered by a recognized arbitration provider under its consumer or commercial rules, as applicable. Arbitration will take place in the state where you reside or another mutually agreed location, in English.

**Class action waiver.** To the extent arbitration applies, proceedings will be conducted only on an individual basis, not as a class, collective, or representative action.

**Jury trial waiver.** Where arbitration does not apply and waivers are enforceable, each party waives any right to a jury trial for disputes arising from these Terms.

**Governing law.** These Terms are governed by the laws of the United States and the state in which you reside, without regard to conflict-of-law rules, except where preempted by federal law.

**Venue.** If arbitration does not apply, exclusive jurisdiction for permitted court proceedings will lie in the state and federal courts located in your state of residence, and you consent to personal jurisdiction there.

Nothing in this section prevents either party from seeking relief in small claims court for qualifying disputes.

---

## 15. Export and Compliance

You agree to comply with U.S. export control and sanctions laws and not to use the Service in embargoed jurisdictions or for prohibited end uses.

---

## 16. General

- **Entire agreement.** These Terms, together with the Privacy Policy and any order form or enterprise agreement, constitute the entire agreement regarding the Service.
- **Order of precedence.** Signed enterprise agreements control over conflicting Terms provisions.
- **Assignment.** You may not assign these Terms without our consent. We may assign these Terms in connection with a merger, acquisition, or asset sale.
- **Severability.** If any provision is unenforceable, the remainder remains in effect.
- **No waiver.** Failure to enforce a provision is not a waiver.
- **Notices.** We may provide notices via email, in-product messages, or posting on our website.

---

## 17. Contact

**Neural Draft LLC**  
Legal: **legal@neuraldraft.net**  
Privacy: **privacy@neuraldraft.net**  
Product: Gaijinn

---

*This document is a draft prepared for internal review and publication planning. It does not constitute legal advice. Engage qualified counsel before relying on or publishing these Terms.*