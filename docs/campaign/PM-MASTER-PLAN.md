# Neural Draft LLC — Master Project Plan

**Owner:** Amir / Neural Draft LLC  
**Product:** Gaijinn (agent swarm command bridge)  
**Domain target:** neuraldraft.net (Namecheap — recovery in progress)  
**Last updated:** 2026-06-16

---

## Executive summary

Two parallel tracks:

1. **Product** — Gaijinn CLI + supervisor API + terminal (integrity-based billing, stealth positioning)
2. **Go-to-market** — Website, legal, LLC branding, domain recovery

Revenue model: **free preflight → quote → purchase deploy entitlement → pay sprint fee → atomic deploy**.

---

## Workstream status (2026-06-16)

| Stream | Status | Owner / Agent |
|--------|--------|---------------|
| ACI billing + quote/purchase/spawn gate | ✅ Done | Billing agent + orchestrator |
| Stealth vocabulary (CLI, terminal, prompts) | ✅ Done | Stealth agent |
| Proprietary LICENSE + vault docs | ✅ Done | Vault agent |
| External README rewrite | ✅ Updated Phase 2 | Vault + cursor |
| Website (`campaign/website/`) | ✅ Phase 2 metrics synced | Website agent |
| Case study + pitch deck | ✅ Done | `GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md`, `ENTERPRISE-PITCH-DECK.md` |
| Provisional patent spec (draft) | ✅ Draft — attorney review | `PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md` |
| Phase 2 monorepo dogfood | ✅ Done | 171 nodes · 4 workers · validation 1.0 · TX-HT-6D0B24 |
| CI preflight gate | ✅ Done | `gaijinn-gate.yml` + `/api/v1/preflight` |
| Privacy + Terms (`campaign/legal/`) | ✅ Draft — attorney review | Legal agent |
| Namecheap recovery playbook | ✅ Done | Ops agent |
| Terminal purchase flow wired | ✅ Done | PM pass |
| Analyze endpoint free (no N² charge) | ✅ Done | PM pass |
| Cloud kernel (SaaS-only decomposition) | 🔲 Phase 3 | Future |
| Stripe / production billing | 🔲 Phase 3 | Future |
| Provisional patent filed | 🔲 Blocked on counsel | Amir |
| Attorney review of legal | 🔲 Blocked on counsel | Amir |

---

## Phase 1 — Ship design partner offer (next 14 days)

### Week 1 — Product truth

- [ ] Record demo: tiny-python-service full `:swarm 2` with quote → purchase → deploy
- [ ] Fix API spawn lifecycle (manifest status updates on completion)
- [ ] Seed design partner ledger accounts in production DB
- [ ] Deploy website to temporary host (Cloudflare Pages / Netlify) while Namecheap locked

### Week 2 — First paid pilot

- [ ] 3–5 design partner conversations (teams hitting multi-agent merge pain)
- [ ] Offer: **$500–$2,000/mo** pilot — integrity preflight + 10 deploys
- [ ] NDA + trade secret addendum (`campaign/legal/TRADE-SECRET-NOTICE.md`)
- [ ] Collect sprint outcome corpus (every deploy logs integrity_score + result)

---

## Phase 2 — Domain + brand (parallel, blocked on Namecheap)

### Immediate (Amir actions)

1. Send escalation email per `campaign/ops/NAMECHEAP-RECOVERY.md` → `security@namecheap.com`
2. Live chat → ticket reference number same day
3. Fill `campaign/ops/DOMAINS-INVENTORY.md`
4. Pre-create Cloudflare zone for `neuraldraft.net` (DNS ready for cutover)

### When Namecheap unlocks

1. Point `neuraldraft.net` → Cloudflare
2. Deploy `campaign/website/` to production
3. Email: `hello@`, `privacy@`, `legal@` @neuraldraft.net (Google Workspace or Proton)
4. SSL + HSTS

### Backup if Namecheap >14 days

- Register `neuraldraft.io` or `getgaijinn.com` elsewhere
- Forward to primary when recovered

---

## Phase 3 — Campaign messaging (stealth)

**Say:** Preflight → Compose → Deploy. Integrity score pricing. Locked-scope swarms.

**Never say:** Blueprint, shadow bridge, curvature, collision prevention, GIV.

| Channel | Asset | Path |
|---------|-------|------|
| Website | Landing + pricing tiers | `campaign/website/index.html` |
| Legal | Privacy + Terms | `campaign/legal/*.md` |
| Pitch deck | Phase 2 telemetry | ✅ `docs/campaign/ENTERPRISE-PITCH-DECK.md` |
| Case study | Phase 1 + 2 whitepaper | ✅ `docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md` |
| Demo video | Terminal swarm deploy | TODO |

---

## Billing flow (implemented)

```
POST /api/v1/quote          → integrity_score, tier, deploy_fee, sprint_fee (no charge)
POST /api/v1/blueprint/purchase → deduct deploy_fee, return sprint_token
POST /api/v1/grid/spawn     → require sprint_token, deduct sprint_fee, spawn agents
POST /api/v1/analyze        → free preflight validation
```

**Ledger:** `.aoc/billing/accounts.json` (local dev). Production → Postgres + Stripe credits.

**Tier deploy fees (defaults):** Starter $5, Team $15, Pro $50, Enterprise $150 + $0.01 × integrity_score.

---

## IP protection checklist

- [x] Proprietary LICENSE (not MIT)
- [x] Internal docs vaulted (`docs/vault/`)
- [x] Customer API responses use integrity_score / tier only
- [x] Terms prohibit reverse engineering
- [x] Provisional patent technical spec drafted (`PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md`)
- [ ] Provisional patent filed (attorney)
- [ ] Move decomposition kernel to cloud-only API
- [ ] Employee/contractor IP assignment signed

---

## Agent roster (this session)

| Agent | Deliverable |
|-------|-------------|
| Billing | ACI pricing, quote/purchase/spawn gate, 63 supervisor tests |
| Stealth | CLI/terminal/prompt vocabulary |
| Website | neuraldraft.net landing page |
| Legal | Privacy, Terms, trade secret notice |
| Vault | LICENSE, README, docs/vault |
| Ops | Namecheap recovery playbook |

---

## Amir — top 3 actions today

1. **Legal:** Book attorney consult — file provisional patent from `PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md`
2. **Revenue:** Send `ENTERPRISE-PITCH-DECK.md` + case study to 2–3 design-partner prospects
3. **Namecheap:** Escalation email + live chat (see `campaign/ops/NAMECHEAP-RECOVERY.md`)

---

## Key paths

| What | Where |
|------|-------|
| Website | `docs/campaign/website/` |
| Case study | `docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md` |
| Pitch deck | `docs/campaign/ENTERPRISE-PITCH-DECK.md` |
| Patent spec (draft) | `docs/campaign/PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md` |
| Legal drafts | `campaign/legal/` |
| Namecheap playbook | `campaign/ops/NAMECHEAP-RECOVERY.md` |
| Internal IP docs | `docs/vault/` |
| Billing kernel | `aoc_supervisor/aoc_supervisor/billing.py`, `complexity.py` |
| Terminal UI | `gaijinn-terminal.html` |
| Dev ledger | `.aoc/billing/accounts.json` |