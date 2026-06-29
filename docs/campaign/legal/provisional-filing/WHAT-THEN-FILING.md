# What then? — Pro se provisional filing (Amir Khodabakhsh)

**Inventor:** Amir Khodabakhsh · California, United States  
**Assignee (post-filing):** Neural Draft LLC via assignment  
**Fee:** ~$80 micro entity (verify at [USPTO fee schedule](https://www.uspto.gov/learning-and-resources/fees-and-payment/uspto-fee-schedule))

---

## You are here

| Done | Item |
|------|------|
| ✅ | Technical spec v2.0 (`~/Desktop/USPTO-PATENT-APPLICATION-DRAFT.md`) |
| ✅ | Inventor filled in |
| ✅ | GIV terminology corrected (supersedes `patentvisuals.jpeg` **Grit** typo) |
| ✅ | Mermaid figures (`PATENT-FIGURES-MERMAID.md`) |
| ✅ | Filing SVGs (`figures/fig01-deployment-loop.svg`, `fig04-giv-envelope.svg`) |
| ⬜ | USPTO.gov account |
| ⬜ | PDF bundle upload |
| ⬜ | $80 payment |
| ⬜ | Filing receipt saved |

---

## Step 1 — Build PDFs (10 min)

```bash
cd /home/ghost-monday/Desktop/Gaijinn

# Specification PDF (from Desktop draft)
pandoc /home/ghost-monday/Desktop/USPTO-PATENT-APPLICATION-DRAFT.md \
  -o dist/provisional-filing/01-SPECIFICATION.pdf \
  --pdf-engine=pdflatex -V geometry:margin=1in -V fontsize=11pt 2>/dev/null \
  || pandoc /home/ghost-monday/Desktop/USPTO-PATENT-APPLICATION-DRAFT.md \
       -o dist/provisional-filing/01-SPECIFICATION.html --standalone

# Drawings PDF — open SVGs in browser → Print → Save as PDF
#   figures/fig01-deployment-loop.svg
#   figures/fig04-giv-envelope.svg
# Merge into 02-DRAWINGS.pdf (or upload each page in Patent Center)
```

If `pdflatex` missing: open the `.html` in Chrome → Print → Save as PDF.

---

## Step 2 — USPTO Patent Center (30 min)

1. [patentcenter.uspto.gov](https://patentcenter.uspto.gov) → sign in / create account
2. **File new** → **Provisional application**
3. **Title:** copy from spec header
4. **Inventor:** Amir Khodabakhsh, residence California, US
5. **Applicant:** Amir Khodabakhsh (individual) — assign to Neural Draft LLC after filing
6. **Entity:** Micro entity (certify per `02-MICRO-ENTITY-DECLARATION.md`)
7. **Upload:**
   - `01-SPECIFICATION.pdf` (required)
   - `02-DRAWINGS.pdf` (recommended — FIG. 1 + FIG. 4 minimum; add more before non-provisional)
8. **Pay** ~$80 → **Submit**
9. **Download filing receipt** immediately — note **application number** and **filing date**

---

## Step 3 — Same day after receipt

| Action | Why |
|--------|-----|
| Save receipt PDF to `docs/campaign/legal/provisional-filing/receipts/` (private) | Proof of priority date |
| `git tag patent-provisional-filed-YYYY-MM-DD` on private repo | Reduction-to-practice anchor |
| One-page **assignment** inventor → Neural Draft LLC | Company owns application |
| Update `PROPRIETARY.md`: "Patent Pending" | Only **after** receipt |
| Calendar **12 months** for non-provisional | Provisional expires |
| Optional: attorney consult for non-provisional claims polish | Not required for provisional |

---

## Step 4 — What you can do after filing

- Mark website / pitch deck **Patent Pending**
- Run design-partner conversations under NDA
- Keep repo private; continue committing to `main` for priority chain evidence
- Public demo / open-source subset — safer after filing receipt

---

## Do not use

- `~/Desktop/patentvisuals.jpeg` — contains **Grit** mislabel; use repo `figures/*.svg` instead

---

## Optional next (Composer)

- Generate remaining FIG. 5–13 SVGs from mermaid spec
- Single `build-provisional-pdf.sh` that bundles spec + all figures
- Copy Desktop draft into repo as canonical `USPTO-PATENT-APPLICATION-DRAFT.md`