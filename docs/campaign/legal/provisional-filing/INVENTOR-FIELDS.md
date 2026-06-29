# Inventor fields — fill before PDF build

**Do not commit this file with real PII unless the repo stays private.**

| Field | Your value |
|-------|------------|
| Inventor legal name (First Middle Last) | `________________________` |
| Residence city | `________________________` |
| Residence state (US) | `________________________` |
| Country | United States |
| Citizenship | United States |
| Correspondence email | `________________________` |
| Correspondence street address | `________________________` |
| Correspondence city, state, ZIP | `________________________` |

**Applicant (who owns the application):**

- [ ] **Individual inventor** (simplest pro se path — assign to Neural Draft LLC after filing via separate assignment)
- [ ] **Neural Draft LLC** as applicant (requires entity address + signer with authority)

**Title of invention (default — edit if counsel advises):**

> Systems and Methods for Governed Parallel Execution of Autonomous Software Agents Using Curvature-Based Repository Partitioning, Agent Intent Vectors, and an Asynchronous Transaction Bus

After filling, run:

```bash
bash scripts/ops/build-provisional-pdf.sh
```