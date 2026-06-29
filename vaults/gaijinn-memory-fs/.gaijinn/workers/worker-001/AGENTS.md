---
id: "AGENTS"
type: "Governance"
status: "active"
scope: "vault-global"
last_updated: "2026-06-19T23:30:00Z"
worker_provenance: "worker-002 atomic sprint grid-spawn-1196463 (WUs 002, 004, 006, 008, 010, 012, 014, 016, 018, 020, 022, 024, 026)"
tags:
  - Governance
  - Agent-Rules
  - Domain/Governance
links:
  - "[[raw/constitution-v0-section-xiii]]"
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
  - "[[CLAUDE]]"
  - "[[_multi-agent/events]]"
  - "[[10_Operations/tasks/OBSIDIAN-RUN-16]]"
---

# Agent Rules — gaijinn-memory-fs (Obsidian Vault Civilization)

You operate inside an Obsidian vault under **joint governance**: Vault Law + Gaijinn execution law. Both apply simultaneously; neither substitutes for the other per Section XIII.

## Read first (every session)

1. [[raw/constitution-v0-section-xiii]] — Section XIII obligations (binding constitutional text)
2. [[30_Decisions/ADR-002-dual-invariant-domains]] — implementation bindings, metrics keys, convergence thresholds
3. [[00_Brain/invariants/INV-GAIJINN-BINDING]] — hard invariant pointer
4. [[CLAUDE]] — Gaijinn project guidance for Cursor/Claude agents
5. `_multi-agent/events.md` — append-only event ledger (vault semantic)
6. `.gaijinn/bridge/council.md` — Gaijinn Council (operational handoffs)
7. `.gaijinn/merge/governance.json` — execution ledger (structural_score binding)

## Agent obligations (binding — per Section XIII §4)

1. **Declare** the active work unit + GIV scope before writing outside `10_Operations/agents/<your-id>/`.
2. **Run** vault knowledge linter + Gaijinn `validate-worker` before promoting `/pending/` → `/40_Concepts/`.
3. **On merge failure:** no force-overwrites — OCC replay, then re-merge. Do not bypass the merge process.
4. **Log material changes** in **both** `_multi-agent/events.md` (vault semantic) AND Gaijinn Council (`.gaijinn/bridge/council.md`) — one ledger is not enough.
5. **Report sprint results** to the Council, including governance.json convergence score and any vault linter violations.
6. **Maintain separate evaluation** of vault metrics and Gaijinn metrics. Failure in one domain cannot be offset by success in the other.
7. **Respect convergence thresholds:** simulated ≥ 0.875, production = 1.0 (unless ADR-waived with documented partial state).

## Write paths

- **Synthesizer:** `/pending/`, `/40_Concepts/` (when GIV permits)
- **Coder:** `/20_Projects/`, agent scratch under `10_Operations/agents/`
- **Orchestrator:** `10_Operations/tasks/`, leases in events ledger — not `/40_Concepts/`

GIV (Gaijinn Invariant Verification) enforces allowed paths per work unit. An agent may only modify files outside its private workspace if its assigned work unit's GIV explicitly permits those paths. Both vault OCC checks and Gaijinn handoff validation must pass before any change is committed.

## Convergence gates

| Gate | Threshold | Artifact |
|------|-----------|----------|
| Vault knowledge linter | clean (no orphan links, full provenance) | `knowledge_linter.py` |
| Gaijinn validate-worker | passed (path, scope, handoff, test gates) | `.gaijinn/merge/governance.json` |
| Structural convergence (sim) | ≥ 0.875 | `structural_score` in governance.json |
| Structural convergence (prod) | = 1.0 | `structural_score` in governance.json |

## Executor profile (this project)

- Grid workers: **deepseek** (`hermes -m deepseek-v4-flash --provider deepseek --yolo`)
- Orchestrator (Hermes): **deepseek-v4-flash** (`gaijinn hermes` / API hermes chat)

Configured in [[project.executor-profile.json]] (.gaijinn/project.json → `executor_profile`).

## Coordination ledgers

| Domain | Ledger | Purpose |
|--------|--------|---------|
| Vault semantic | `_multi-agent/events.md` | Semantic intent, ownership changes, concept promotion |
| Gaijinn operational | `.gaijinn/bridge/council.md` | Work unit handoffs, execution decisions, sprint reports |

Both must be updated on material changes. Neither substitutes for the other.

## Related

- [[raw/constitution-v0-section-xiii]] — constitutional foundation
- [[30_Decisions/ADR-002-dual-invariant-domains]] — technical binding
- [[00_Brain/invariants/INV-GAIJINN-BINDING]] — hard invariant
- [[CLAUDE]] — Cursor/Claude context file
- [[10_Operations/tasks/OBSIDIAN-RUN-16]] — active sprint manifest

## Worker-002 atomic sprint (2026-06-19)

This file carries the governance contract for all Gaijinn workers, including
worker-002 atomic sprint grid-spawn-1196463. Worker-002 owns 13 work units
covering json/markdown/python artifacts across the vault surface area:

- **WU-002** json high-risk at repo root — `project.executor-profile.json`
- **WU-004** markdown medium-risk at repo root — this file
- **WU-006** unknown high-risk under `.agents/` — codex + hermes env templates
- **WU-008** json high-risk under `.obsidian/` — Obsidian UI config
- **WU-010** markdown high-risk under `10_Operations/` — Hermes ops manuals
- **WU-012** python high-risk under `10_Operations/agents/promoter/` — promotion validator
- **WU-014** markdown high-risk under `10_Operations/tasks/` — topology task briefs
- **WU-016** markdown high-risk under `20_Projects/` — DeepSeek setup guides
- **WU-018** markdown high-risk under `40_Concepts/` — concept corpus (33 notes)
- **WU-020** markdown high-risk under `_multi-agent/` — events ledger
- **WU-022** python medium-risk under `aoc_supervisor/aoc_supervisor/` — linter + preflight + repo_paths
- **WU-024** json high-risk under `ui/` — vault UI intent map
- **WU-026** import-cycle atomic block — 12-file aoc_supervisor weld

Every WU completes its acceptance gates (`vault_linter` + metrics manifest
review) before the merge pipeline records a completion-ledger entry.
