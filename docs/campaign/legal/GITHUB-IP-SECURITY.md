# GitHub IP & Security Runbook — Gaijinn

**Owner:** Ghostmonday / Neural Draft LLC  
**Last updated:** 2026-06-18  
**Purpose:** Operational checklist for protecting Gaijinn and related patent collateral on GitHub.

---

## Current posture (verified 2026-06-18)

| Control | Gaijinn | Notes |
|---------|---------|-------|
| Repository visibility | **Private** | `Ghostmonday/Gaijinn` |
| Account 2FA | **Enabled** | Ghostmonday |
| Public repos on account | **0** | All 33 repos private |
| Collaborators | **Ghostmonday only** | No pending invitations |
| Deploy keys | **0** | |
| Webhooks | **0** | |
| `main` branch protection | **Enabled** | CI `test` required, linear history, no force-push |
| CODEOWNERS | **Enabled** | `.github/CODEOWNERS` |
| Dependabot security updates | **Enabled** | |
| Wiki | **Disabled** | Reduces accidental doc leakage |
| Web commit signoff | **Required** | DCO-style acknowledgment on web edits |
| Secret scanning (GitHub) | **Disabled** | Requires GitHub Advanced Security on private repos |
| CI secret scan (Gitleaks) | **Workflow added** | `.github/workflows/secret-scan.yml` |

---

## Patent filing workflow (GitHub)

The provisional technical spec lives at:

`docs/campaign/PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md`

### Do

- Keep patent drafts in this **private** repo until counsel approves public marking
- Tag attorney-reviewed snapshots: `git tag patent-spec-v1.0-DRAFT` (private remote only)
- Export PDF bundles from private repo for USPTO filing — never attach to public issues
- Use PRs to `main` for all spec changes (audit trail for inventorship dates)

### Do not

- Publish repo, gist, or release containing full gravity/ACI implementation
- Paste claim language into public README, conference slides, or NotebookLM sources without counsel review
- Add outside collaborators without signed NDA + need-to-know justification

### Filing checklist

See checklist section in `PROVISIONAL-PATENT-TECHNICAL-SPECIFICATION.md` and expanded steps in `PATENT-FILING-CHECKLIST.md`.

---

## Recommended next steps (account level)

These require manual action outside automated hardening:

1. **Create GitHub Organization** (`neuraldraft` or similar) and transfer `Gaijinn` — enables fork disabling and org-wide security policies on private repos.
2. **Rotate personal access tokens** — current token has broad scopes (`admin:enterprise`, `delete_repo`). Create a fine-scoped token for daily use; revoke over-privileged tokens.
3. **Enable signed commits** (SSH or GPG) for provenance on patent reduction-to-practice dates.
4. **Add trusted second reviewer** (co-inventor or counsel) for `required_approving_review_count: 1` if you want dual-control merges.
5. **File provisional patent** before any public demo, open-source subset, or customer repo export.
6. **Mark collateral "Patent Pending"** only after USPTO filing receipt — not before.

---

## Related repositories

Apply the same branch protection template to:

- `Ghostmonday/aoc-governance` (private, unprotected as of audit)
- Any repo containing gravity engine, GIV, or orchestration kernel forks

---

## Incident response

If a token, deploy key, or repo is exposed:

1. Revoke credential immediately in GitHub Settings → Developer settings
2. Rotate all secrets in `Actions` (repo has 2 configured)
3. Notify **legal@neuraldraft.net**
4. Review `git log` and GitHub audit log for unauthorized access

---

*Internal operations document — not legal advice.*