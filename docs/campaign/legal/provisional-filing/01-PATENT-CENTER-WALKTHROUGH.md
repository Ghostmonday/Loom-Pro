# USPTO Patent Center — pro se provisional filing

**Estimated time:** 30–45 minutes (account + upload + pay)

## Before you start

- [ ] `INVENTOR-FIELDS.md` completed
- [ ] `bash scripts/ops/build-provisional-pdf.sh` produced `dist/provisional-filing/02-SPECIFICATION.pdf`
- [ ] Repo still **private** — no public disclosure of claim substance before filing
- [ ] USPTO.gov account created (or login ready)
- [ ] Payment method for ~$80 micro-entity fee

## Step 1 — Account

1. Go to [https://patentcenter.uspto.gov](https://patentcenter.uspto.gov)
2. Sign in with USPTO.gov account (create at [https://www.uspto.gov](https://www.uspto.gov) if needed)
3. Complete two-factor authentication

## Step 2 — New provisional

1. **File a new application** → **Provisional**
2. **Applicant:** individual inventor (recommended for pro se) or organization (Neural Draft LLC)
3. **Title:** copy from `00-COVER-SHEET.md`
4. **Inventor:** legal name, residence, citizenship
5. **Correspondence:** email + mailing address for USPTO mail

## Step 3 — Entity status

1. Select **Micro entity**
2. Certify eligibility (see `02-MICRO-ENTITY-DECLARATION.md`):
   - Fewer than 5 prior US patent applications (excluding provisional) as named inventor
   - Gross income below micro-entity threshold OR employed by institution of higher education (if applicable)
   - Not obligated to assign to large entity
3. If Neural Draft LLC is applicant, confirm LLC qualifies as small/micro entity per USPTO rules

## Step 4 — Upload documents

1. **Specification PDF** — upload `dist/provisional-filing/02-SPECIFICATION.pdf`
   - Must include: title, field, background, summary, detailed description, claims
   - Your spec already contains all of these
2. **Drawings** — skip (none required for this filing)
3. **Cover sheet** — Patent Center collects metadata; optional to merge `00-COVER-SHEET.md` as page 1 of PDF

## Step 5 — Review and pay

1. Review application data summary
2. Pay basic filing fee (micro entity tier)
3. Submit — save **confirmation number** and **filing receipt**

## Step 6 — After filing (same day)

- [ ] Record application number + filing date in private issue or `PROPRIETARY.md`
- [ ] Tag repo: `git tag patent-provisional-filed-YYYY-MM-DD` (private remote only)
- [ ] Mark collateral **Patent Pending** on website/deck (only after receipt)
- [ ] Execute **inventor → Neural Draft LLC assignment** (simple one-page form; record if non-provisional)
- [ ] Calendar **12-month** non-provisional deadline
- [ ] Update `PATENT-FILING-CHECKLIST.md` Phase 3 items

## Common pro se mistakes to avoid

| Mistake | Fix |
|---------|-----|
| Public GitHub / demo before filing | File first |
| Spec missing claims | Your spec includes PART XI — good |
| Wrong entity fee tier | Micro vs small vs large — double-check income |
| Losing filing receipt | Download PDF receipt immediately |
| Forgetting assignment to LLC | Assign within days of filing; keep signed PDF in `docs/campaign/legal/` (private) |

---

*Internal runbook. USPTO rules change — verify fee schedule at filing time.*