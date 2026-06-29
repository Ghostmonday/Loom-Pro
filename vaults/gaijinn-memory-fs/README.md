# gaijinn-memory-fs — Vault 1 (Filesystem Civilization)

**Location:** `vaults/gaijinn-memory-fs/` inside the Gaijinn monorepo  
**Separate Gaijinn project:** own `.gaijinn/project.json`, isolated from monorepo dogfood at repo root.

An Obsidian vault civilization with write-time compiled memory: folder taxonomy, YAML frontmatter, wikilinks, event ledger, and knowledge linter enforcing Section XIII joint governance.

## Status (2026-06-18)

| Metric | Value |
|--------|-------|
| Production convergence | **1.0** |
| Vault linter | **PASS** |
| Plan backlog | **0** work units |
| Completion ledger | **23** entries |
| Concepts | **19** in `40_Concepts/` |
| Last merge | 6/6 workers merged (2026-06-18T07:20:02Z) |
| Hermes mode | **active** — orchestrator driving development cycles |

Merge compounding is live: sprints consult `.gaijinn/merge/completion-ledger.json`; zero-delta workers with matching `content_hash` become `already_merged`, not `blocked`.

## Two Gaijinn projects

| Project | Path | Executor default |
|---------|------|------------------|
| **Gaijinn platform** (monorepo) | repo root | Auto → Codex / Grok |
| **Obsidian vault** (this) | `vaults/gaijinn-memory-fs/` | **DeepSeek** orchestrator + workers |

```bash
# Work on the vault civilization
cd vaults/gaijinn-memory-fs
gaijinn compile-prompt && gaijinn scan . && gaijinn analyze && gaijinn plan --workers 6
```

Terminal UI: Advanced → Executor **DeepSeek**, Model **DeepSeek V4 Flash** (or use project defaults).

**Obsidian path:** `/home/ghost-monday/Desktop/Gaijinn/vaults/gaijinn-memory-fs` — not `~/Documents/Obsidian/Gaijinn` (empty stubs). Full map: `40_Concepts/obsidian-vault-mapping.md`

## Vault Infrastructure

| Artifact | Path | Status |
|----------|------|--------|
| Project config | `.gaijinn/project.json` | Active |
| Blueprint (intent map) | `.gaijinn/blueprint.json` | Active (0 WUs — converged) |
| Completion ledger | `.gaijinn/merge/completion-ledger.json` | Active (17 entries) |
| Execution governance | `.gaijinn/merge/governance.json` | convergence **1.0** |
| Intent constraints | `.gaijinn/intent.txt` | Active |
| GIV (governance) | `.gaijinn/giv.json` | Active |
| Worker manifest | `.gaijinn/workers/manifest.json` | 6-worker sprint complete |
| Metrics manifest | `.gaijinn/metrics_manifest.json` | Active |
| Council bridge | `.gaijinn/bridge/council.md` | Active |
| Section XIII (vault law) | `raw/constitution-v0-section-xiii.md` | Immutable |
| ADR-002 (dual invariants) | `30_Decisions/ADR-002-dual-invariant-domains.md` | Active |
| Hard invariant pointer | `00_Brain/invariants/INV-GAIJINN-BINDING.md` | Active |
| Vault semantic ledger | `_multi-agent/events.md` | Active |
| Write path permissions | `.agents/vault.yaml` | Active |
| Executor profile | `project.executor-profile.json` | Active |
| DeepSeek env template | `.agents/hermes-deepseek.env.example` | Active (Desktop path) |
| DeepSeek setup docs | `20_Projects/deepseek-hermes-setup.md`, `deepseek-codex-setup.md` | Active |

## Executor configuration

- **Grid workers:** `hermes` (`hermes -m deepseek-v4-flash --provider deepseek --yolo`)
- **Orchestrator (Hermes):** `deepseek-v4-flash`
- Configured in `project.executor-profile.json` (schema v5)
- **Canonical monorepo path:** `/home/ghost-monday/Desktop/Gaijinn` (not workspace duplicate)

## Dogfood pipeline (brownfield)

```
compile-prompt → scan → analyze → plan → run-grid → [agent work] → collect → validate-worker → merge-grid
```

**Latest sprint (2026-06-18):** 6 ledger-filtered work units shipped after 11 prior `already_merged` entries from completion-ledger backfill.

| Worker | WU | Scope |
|--------|-----|-------|
| worker-001 | WU-5117f332 | `.agents/` examples |
| worker-002 | WU-82c99d2b | HERMES-DEVELOPMENT-ORDERS + event-sourcing-vault |
| worker-003 | WU-90ed6cbb | `preflight.py` |
| worker-004 | WU-d50925f6 | `api.py`, `billing.py`, `__init__.py` |
| worker-005 | WU-eacc7320 | `.cursorrules` |
| worker-006 | WU-ec692d62 | `deepseek-codex-setup.md` |

## Governance rules

- **Scope lock:** `.gaijinn/intent.txt` — deterministic output, no `git push`, no edits outside assigned paths
- **Coordination:** `.gaijinn/bridge/council.md` via `gaijinn council say`
- **Handoff protocol:** Cross-worker files use HANDOFF_ONLY transaction tickets
- **Dual validation:** Vault knowledge linter + Gaijinn `validate-worker` before promotion
- **Convergence thresholds:** simulated ≥ 0.875, production **1.0** (Section XIII §3)

## Product thesis

| Layer | Role |
|-------|------|
| **Obsidian (this vault)** | Human/agent memory — taxonomy, wikilinks, Section XIII semantic law |
| **Gaijinn CLI** | Executable architecture planning — scan → plan → grid → merge with ledger compounding |
| **Endgame** | Blueprint-native IDE when dogfood proves repeatable |

## Related docs

- Monorepo assembly-line paper: `~/Desktop/GAIJINN-ASSEMBLY-LINE-TECHNICAL-PAPER.md`
- Merge compounding design: `Desktop/Gaijinn/.gaijinn/design/merge-compounding/`
- Full source dump: `~/Desktop/gaijinn_source.txt`