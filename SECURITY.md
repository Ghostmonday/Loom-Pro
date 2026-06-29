# Security Policy — Gaijinn (Neural Draft LLC)

**Repository classification:** Private proprietary / trade secret  
**Do not report vulnerabilities via public GitHub Issues if you lack authorized access.**

## Supported versions

| Version | Supported |
|---------|-----------|
| `main` branch | Yes |
| Older tags / branches | Best effort |

## Reporting a vulnerability

If you are an **authorized** collaborator, contractor, or design partner:

1. **Do not** open a public issue, gist, or discussion describing exploit details.
2. Email **legal@neuraldraft.net** with subject `Gaijinn Security — [severity]`.
3. Include reproduction steps, affected paths, and impact assessment.
4. Allow up to **5 business days** for initial acknowledgment.

Unauthorized third parties without a signed NDA should not access this private repository. If you believe you received accidental access, delete local copies and notify **legal@neuraldraft.net**.

## Scope

In scope:

- Remote code execution, authentication bypass, or billing ledger tampering in `aoc_supervisor`
- GIV / preflight bypass allowing sibling trespass or out-of-scope writes
- Exposure of trade secrets (ACI weights, gravity engine constants) via API or logs
- Leakage of customer repository data or sprint tokens

Out of scope:

- Social engineering, physical access, or issues in third-party LLM providers
- Denial of service without demonstrated data impact

## Safe harbor

Good-faith reports from authorized parties will not be pursued legally when discovery rules in your agreement are followed. Public disclosure before remediation is prohibited.

## Trade secrets

This codebase contains patent-pending and trade-secret material. See `docs/campaign/legal/TRADE-SECRET-NOTICE.md` and `PROPRIETARY.md`.