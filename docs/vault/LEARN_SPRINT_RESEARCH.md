# LEARN SPRINT — Research Artifact
## Worker-009: Gaijinn-Obsidian Dogfooding Infrastructure Mapping

**Author:** Gaijinn worker-009 (handoff-only)
**Session:** 185cb702fb60
**Date:** 2026-06-17
**GIV:** `handoff_only: true`, `scope_strict: true`
**Status:** RESEARCH COMPLETE — see gaps and recommendations below

---

## 1. Research Objective

Map Affairs/FileSystem/Gaijinn Obsidian vaults to gaijinn-memory-fs and platform `.gaijinn/`. Analyze each of 6 slices for maturity, identify gaps, and surface concrete next steps for the next sprint.

---

## 2. Current Architecture — What Already Exists

The Gaijinn platform at repo root (`/home/ghost-monday/workspace/github.com/ghost-monday/Gaijinn/`) has a fully functioning dogfood loop via `vaults/gaijinn-memory-fs/` — a live Obsidian vault that is itself a Gaijinn-instrumented project with:

| Component | Location | Status |
|-----------|----------|--------|
| Vault deployment model | `aoc_supervisor/aoc_supervisor/vault_deploy.py` | Research artifact |
| Cross-vault link resolver | `aoc_supervisor/aoc_supervisor/vault_links.py` | Research artifact |
| Knowledge linter (platform) | `aoc_supervisor/aoc_supervisor/knowledge_linter.py` | Shipped + tested |
| Vault-level linter | `vaults/gaijinn-memory-fs/10_Operations/knowledge-linter.py` | Deployed |
| Dual governance constitution | `vaults/gaijinn-memory-fs/raw/constitution-v0-section-xiii.md` | Deployed |
| ADR-002 dual invariants | `vaults/gaijinn-memory-fs/30_Decisions/ADR-002-dual-invariant-domains.md` | Deployed |
| Memory-execution loop | `vaults/gaijinn-memory-fs/40_Concepts/memory-execution-loop.md` | Deployed |
| Event ledger (multi-agent) | `vaults/gaijinn-memory-fs/_multi-agent/events.md` | Deployed |
| Council bridge | `.gaijinn/bridge/` + `vaults/gaijinn-memory-fs/.gaijinn/bridge/` | Shipped + live |
| Worker orchestration | `aoc-cli/aoc_cli/helpers/workers.py` | Shipped |
| Handoff protocol | `aoc-cli/aoc_cli/helpers/handoff.py` | Shipped |
| Merge pipeline | `aoc-cli/aoc_cli/helpers/merge.py` | Shipped |
| GIV lifecycle | `aoc-cli/aoc_cli/giv.py` + per-worker giv.json | Shipped |

---

## 3. Six-Slice Maturity Assessment

### Slice 1: Constitution Alignment
**Status:** PARTIALLY DEPLOYED — gaijinn-memory-fs only

- Section XIII Constitution exists only in `vaults/gaijinn-memory-fs/raw/`
- No mechanism to apply constitution rules to the Affairs/FileSystem vaults
- No automatic constitution violation detection at the platform level
- **Gap:** Need platform-level `constitution_enforcer.py` that reads Section XIII rules and validates ALL vaults
- **Next step:** Extract Section XIII rules into structured `rules.json` in `aoc_supervisor/aoc_supervisor/constitution/`

### Slice 2: Knowledge Linter
**Status:** SHIPPED + TESTED

- `knowledge_linter.py` at platform level (415 lines, 18 test classes in `test_knowledge_linter.py`)
- Vault-level variant deployed in `gaijinn-memory-fs/10_Operations/`
- Checks: frontmatter, wiki-links, orphans, naming, empty notes, cross-vault links
- **Gap:** The platform linter has no CLI integration into the Gaijinn pipeline (no `gaijinn lint-vault --vault <name>` command)
- **Next step:** Add `lint-vault` CLI command to `aoc-cli/aoc_cli/cli.py` that wraps `knowledge_linter.lint_vault()`

### Slice 3: Ingress/Promotion Pipeline
**Status:** CONCEPTUAL ONLY

- `vault_deploy.py` has data model (VaultDeployment, VaultFile, deploy-manifest.json) but no full ingress pipeline
- `pending/` directory exists in gaijinn-memory-fs vault as a staging area
- No automated promotion gate: no pipeline from raw → pending → linter → concepts/
- 3-promotion-gate concept referenced in council but not implemented as code
- **Gap:** No `ingress.py` that watches a vault's `raw/` and `pending/` directories, lints them, and promotes to `40_Concepts/`
- **Next step:** Implement `aoc_supervisor/aoc_supervisor/ingress.py` with 3-stage pipeline (raw → lint → promote)

### Slice 4: GUI Deploy Path
**Status:** RESEARCH ARTIFACT

- `vault_deploy.py` has `discover_vault_deployment()` and `available_vault_deployments()`
- Deployment manifests go to `.gaijinn/vaults/<name>/deploy-manifest.json`
- No actual GUI deploy endpoint — no API, no web interface
- **Gap:** No deploy/serve command that exposes vault content as a browsable interface
- **Next step:** Create `aoc-cli/aoc_cli/commands/deploy_vault.py` with `gaijinn vault deploy --serve` command

### Slice 5: Cross-Vault Links
**Status:** RESEARCH ARTIFACT

- `vault_links.py` has `VaultLinkResolver` with `[[vault_name:Target]]` syntax support
- Lazy resolution at query time, manifest-based
- `memory_fs_lookup` hook point exists but no integration with actual Affairs/FileSystem vaults
- No actual vault manifests exist for Affairs or FileSystem vaults
- **Gap:** Three vault manifests need to be created. Affairs and FileSystem vaults at `~/Documents/Obsidian/Affairs/` and `~/Documents/Obsidian/FileSystem/` need to be scanned
- **Next step:** Run `discover_vault_deployment()` on Affairs and FileSystem vaults, deploy manifests

### Slice 6: Metrics Targets
**Status:** ZEROED OUT

- `metrics_manifest.json` in gaijinn-memory-fs vault: `convergence: 0`, `validation_pass_rate: 0`, `handoff_isolation: 0`, `shadow_bridge_count: 0`
- `.gaijinn/sessions/185cb702fb60/.gaijinn/metrics_manifest.json` exists at session level
- Metrics collection exists via `audit.py` but session-level convergence scoring is not operationalized
- **Gap:** No `gaijinn metrics report` command, no convergence targets defined per sprint
- **Next step:** Define minimum convergence targets (e.g., `convergence >= 0.7`, `validation_pass_rate >= 0.8`) and add `metrics-report` to CLI

---

## 4. Three-Vault Mapping Analysis

| Property | Affairs | FileSystem | Gaijinn (Obsidian) | gaijinn-memory-fs |
|----------|---------|------------|-------------------|-------------------|
| **Path** | `~/Documents/Obsidian/Affairs/` | `~/Documents/Obsidian/FileSystem/` | `~/Documents/Obsidian/Gaijinn/` | `vaults/gaijinn-memory-fs/` |
| **Gaijinn-instrumented** | No | No | No | Yes |
| **Dual governance** | No | No | No | Yes |
| **Vault manifest** | None | None | None | Deployed |
| **Constitution** | None | None | None | Section XIII |
| **Knowledge linter** | None | None | None | Deployed |
| **Purpose** | USER life semantics | Machine organization | Methodology quick-ref | Gaijinn dogfood + memory loop |

**Critical insight:** Affairs, FileSystem, and Gaijinn Obsidian vaults are the *source* content vaults. gaijinn-memory-fs is the *sink* — the platform-instrumented vault where promoted knowledge converges. The pipeline must flow:

```
Affairs ──┐
FileSystem┤──→ [cross-vault links] ──→ gaijinn-memory-fs ──→ [Gaijinn platform execution]
Gaijinn ──┘
                                          ↑
                                    constitution linter
                                    ingress/promotion
                                    metrics monitoring
```

---

## 5. Blocker Report

The following blockers prevent this LEARN SPRINT from completing:

1. **NO_SIBLING_TRESPASS restriction on worker-009:** GIV has `no_sibling_trespass: true` but the `aoc-cli/aoc_cli/` and `aoc_supervisor/aoc_supervisor/` allowed paths already have committed code. Writing to them requires coordination with workers 001-003 who own the code-level work.

2. **CROSS-VAULT DISCOVERY blocked by no-network rule:** `discover_vault_deployment()` must scan `~/Documents/Obsidian/Affairs/`, `~/Documents/Obsidian/FileSystem/`, and `~/Documents/Obsidian/Gaijinn/` — but the GIV prohibits filesystem traversal outside the allowed paths (`no destructive cleanup outside workspace` + allowed paths are Gaijinn repo paths only).

3. **NEXT SPRINT MUST RESPECT WORKTREE BOUNDARIES:** The existing gaijinn-memory-fs vault is a separate Gaijinn project with its own `.gaijinn/`. Any cross-vault work should spawn workers from THAT project root, not the monorepo root.

---

## 6. Concrete Recommendations

### For the Council / Next Sprint Planner

1. **Respawn from `vaults/gaijinn-memory-fs/`** — that vault already has `.gaijinn/project.json`, blueprint.json, and council history. The next sprint should use `gaijinn plan --workers 6 --from vaults/gaijinn-memory-fs` targeting exactly these 6 slices.

2. **Three new supervisor modules needed:**
   - `aoc_supervisor/aoc_supervisor/constitution_enforcer.py` — structured constitution validation
   - `aoc_supervisor/aoc_supervisor/ingress.py` — 3-stage promotion pipeline
   - `aoc_supervisor/aoc_supervisor/metrics_report.py` — convergence scoring + CLI

3. **Two new CLI commands needed:**
   - `gaijinn vault deploy --serve` — GUI deploy path
   - `gaijinn vault lint --vault <name>` — cross-vault linting
   - `gaijinn metrics report` — sprint health dashboard

4. **Vault manifest discovery for Affairs/FileSystem:** Lift the no-network restriction for a dedicated `discover-vaults` worker that can scan `~/Documents/Obsidian/`.

5. **Promotion gate automation:** Wire `knowledge_linter.lint_vault()` as a blocking gate in the merge pipeline (currently only structural score checks exist at merge time).

### Immediate Actions

| Action | Priority | Owner |
|--------|----------|-------|
| Enable vault deploy > council: propose respawn from gaijinn-memory-fs | P0 | Council (this worker) |
| Add CLI entry for `lint-vault` | P1 | worker-001 or worker-002 |
| Create `constitution_enforcer.py` | P1 | New worker in next sprint |
| Scan Affairs/FileSystem vaults | P2 | Dedicated worker with filesystem access |

---

## 7. Handoff Ticket

```
++++ GAIJINN_HANDOFF_TICKET_START ++++
ticket_id: LEARN-009-001
source_worker_id: worker-009
target_work_unit_id: council
target_file: .gaijinn/bridge/council.md
required_mutation_context: |
  Append blocker report to council. Recommend respawn from
  vaults/gaijinn-memory-fs/ with 6 dedicated workers.
  Allowed paths must include ~/Documents/Obsidian/ for
  vault discovery.
status: OPEN
++++ GAIJINN_HANDOFF_TICKET_END ++++
```

---

*Worker-009 completing handoff-only research cycle. No code was modified. Python package structure preserved. All findings documented for council consumption.*
