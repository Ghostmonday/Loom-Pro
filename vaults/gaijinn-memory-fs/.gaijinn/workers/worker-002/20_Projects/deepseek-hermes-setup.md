---
id: "PROJ-DEEPSEEK-HERMES-SETUP"
type: "Project"
status: "active"
date_created: "2026-06-17"
last_updated: "2026-06-18"
tags:
  - Project
  - Domain/Orchestration
  - Executor/DeepSeek
  - Executor/Hermes
linked_constitution: "[[raw/constitution-v0-section-xiii]]"
linked_adr: "[[30_Decisions/ADR-002-dual-invariant-domains]]"
linked_invariant: "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/tasks/OBSIDIAN-RUN-16]]"
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS]]"
---

# DeepSeek agent stack (Hermes) — gaijinn-memory-fs

This vault uses **DeepSeek as a first-class Gaijinn agent stack** — orchestrator and grid subagents run through **Hermes**, parallel to Grok. **Codex is not involved** in the DeepSeek path.

This project operates under the joint governance established by [[raw/constitution-v0-section-xiii]] (Section XIII) and [[30_Decisions/ADR-002-dual-invariant-domains]] (ADR-002). The [[00_Brain/invariants/INV-GAIJINN-BINDING]] hard invariant enforces dual-domain compliance — vault semantic integrity and Gaijinn execution integrity must both pass before promotion.

## Governance status

This note is the WU-008 high-risk project artifact for the DeepSeek/Hermes executor path. It is intentionally scoped to operator setup, auth propagation, autonomy loop configuration, OCC behavior, and verification commands for the `20_Projects` domain.

Current metrics-manifest review:

| Check | Current value | Operational meaning |
|-------|---------------|---------------------|
| Rejected node | `20_Projects/deepseek-hermes-setup.md` is listed in `gravity_meta.rejected_nodes` | High-capability project note remains below gravity floor until graph in-degree or gravity recovers |
| Shadow Bridges | `curvature_meta.shadow_bridge_count = 0` | No current cross-boundary write violation is reported for the manifest |
| Latest convergence | `merge_governance.latest.structural_score.convergence = 0.6667` | Latest production merge is below the Section XIII production threshold and relies on documented partial-state governance |
| Validation pass rate | `merge_governance.latest.structural_score.validation_pass_rate = 1.0` | Worker validation pass rate is clean in the latest embedded governance block |

Recovery path: keep this note linked from governance, README, and executor-profile surfaces through HANDOFF_ONLY requests to sibling owners. Do not directly edit those files from WU-008.

## Prerequisites

- `hermes` on PATH (`hermes --version`)
- DeepSeek API key configured via **one of** these methods:

### Option A: Environment file (recommended for grid workers)

Copy `.agents/hermes-deepseek.env.example` to `~/.hermes/.env`:

```bash
cp .agents/hermes-deepseek.env.example ~/.hermes/.env
# Edit ~/.hermes/.env and set:
#   DEEPSEEK_API_KEY="sk-..."   # https://platform.deepseek.com/api_keys
```

The template supports multiple auth methods in a **failover chain** (tried in order):

1. **DEEPSEEK_API_KEY** (env file) — simplest, used by grid worker spawns
2. **OAuth refresh token** (DEEPSEEK_REFRESH_TOKEN + DEEPSEEK_CLIENT_ID + DEEPSEEK_CLIENT_SECRET) — automated key rotation
3. **Hermes CLI login** (hermes login) — interactive, stores in config.yaml

> **Important:** Method 3 does NOT propagate to grid workers. Workers spawned by `gaijinn run-grid` read DEEPSEEK_API_KEY from the env file. Always set method 1 for automated worker execution.

### Option B: Hermes CLI login (recommended for interactive use)

```bash
hermes login
hermes model
# Interactive: select provider=deepseek, model=deepseek-v4-flash
```

The CLI stores credentials in `~/.hermes/config.yaml` automatically. No env file needed for basic interactive usage.

### Verify auth

```bash
hermes -m deepseek-v4-flash --provider deepseek -z "Reply OK only"
# Expected: OK
```

## Recommended Hermes config

`~/.hermes/config.yaml`:

```yaml
provider: deepseek
model: deepseek-v4-flash
base_url: https://api.deepseek.com
```

Smoke test:

```bash
hermes -m deepseek-v4-flash --provider deepseek -z "Reply OK only"
```

## Project executor profile

`.gaijinn/project.json` → `executor_profile`:

```json
{
  "grid_executor": "deepseek",
  "grid_model": "deepseek-v4-flash",
  "hermes_model": "deepseek-v4-flash",
  "deepseek_provider": "deepseek"
}
```

- **Grid spawn:** `hermes -z <prompt> -m deepseek-v4-flash --provider deepseek --yolo` (cwd = worker dir)
- **Orchestrator:** `gaijinn hermes` reads `hermes_model` + `deepseek_provider` from the same profile

Override provider for one session: `export GAIJINN_DEEPSEEK_PROVIDER=deepseek`

## API key rotation

When rotating the DeepSeek API key, update all locations:

| Location | Method |
|----------|--------|
| `~/.hermes/.env` | Edit `DEEPSEEK_API_KEY` — grid workers read from here |
| `~/.hermes/config.yaml` | Re-run `hermes login` to update CLI credentials |
| `.gaijinn/project.json` | If `deepseek_provider` contains embedded keys |

Grid worker spawns pick up the new key from `.env` immediately — no restart required.

## Gaijinn terminal UI

Advanced -> Executor: **DeepSeek (Hermes)**. Model dropdown filters to DeepSeek models when that executor is selected.

## Gaijinn project configuration

The vault's `.gaijinn/project.json` must declare DeepSeek as the executor:

```json
{
  "project_prompt": "LEARN SPRINT: Discover the perfect joint workflow for Gaijinn dogfooding and well-formed Obsidian vault systems.",
  "capabilities": ["vault", "constitution", "knowledge", "metrics"],
  "executor_profile": {
    "grid_executor": "deepseek",
    "grid_model": "deepseek-v4-flash",
    "hermes_model": "deepseek-v4-flash",
    "deepseek_provider": "deepseek"
  }
}
```

Override provider for one session: `export GAIJINN_DEEPSEEK_PROVIDER=deepseek`

## Cron and gateway configuration

For unattended pipeline execution, the env template (`.agents/hermes-deepseek.env.example`) has a dedicated **CRON & GATEWAY** section. Key settings:

| Variable | Purpose | Default |
|----------|---------|---------|
| `GATEWAY_ENABLED` | Enable API gateway for grid-spawn triggers | `false` |
| `GATEWAY_PORT` | Port for the gateway | `7377` |
| `CRON_ENABLED` | Enable autonomous pipeline timer | `false` |
| `GAIJINN_AUTONOMY_INTERVAL_SEC` | Loop polling interval | `120` |
| `GAIJINN_AUTONOMY_DAEMON` | Run as background process | `false` |

To enable the full unattended pipeline:

```bash
# In ~/.hermes/.env:
GATEWAY_ENABLED=true
GATEWAY_PORT=7377
CRON_ENABLED=true
GAIJINN_AUTONOMY_INTERVAL_SEC=120
```

The cron jobs are maintained in [[10_Operations/HERMES-DEVELOPMENT-ORDERS]]:

```cron
*/3 * * * * cd /home/ghost-monday/Desktop/Gaijinn && bash scripts/dev/council-composer-watcher.sh
*/15 * * * * cd /home/ghost-monday/Desktop/Gaijinn && bash scripts/dev/hermes-development-loop.sh
```

## Config precedence and env var cascading

When the same parameter is set in multiple places, Gaijinn uses a 6-rank overlay system (highest rank wins). The full table is documented in `.agents/hermes-deepseek.env.example` under **CONFIG PRECEDENCE**. Key takeaways:

- CLI flags (--model, --provider) override everything for one-shot invocations
- Shell exports (`export DEEPSEEK_API_KEY=...`) apply for the duration of a terminal session
- `~/.hermes/.env` is the persistent source — grid worker spawns resolve from here
- `~/.hermes/config.yaml` (from `hermes login`) is for interactive use only — does NOT propagate to workers
- `.gaijinn/project.json` executor_profile provides project-level defaults

For grid workers, the effective auth chain is: env file → OAuth refresh → project.json defaults. If none succeed, the worker fails with an auth error.

## Autonomy loop configuration

The development loop (`.gaijinn/operations/hermes-development-loop.py` via `scripts/dev/hermes-development-loop.sh`) orchestrates the unattended pipeline. Its configuration is split across:

| Config source | Variables | Effect |
|---------------|-----------|--------|
| `~/.hermes/.env` | GATEWAY_ENABLED, CRON_ENABLED | Master switch for API gateway and cron timer |
| `~/.hermes/.env` | GAIJINN_AUTONOMY_INTERVAL_SEC | Loop polling interval (default 120s, min 60s) |
| `~/.hermes/.env` | GAIJINN_AUTONOMY_DAEMON | Background daemon mode toggle |
| `.gaijinn/project.json` | executor_profile | Grid model, provider, model name |
| `.gaijinn/intent.txt` | work_units, scope | Number of workers, allowed paths |
| Cron tab | council-composer-watcher | Composer inbox bridge (every 3 min) |
| Cron tab | hermes-development-loop | Pipeline: compile → scan → analyze → plan → grid → spawn → collect → validate → merge (every 15 min) |

Each cron tick executes exactly one pipeline step. The complete cycle takes 7 ticks × 15 min = ~105 min in normal operation, shorter if the grid-spawn sub-agent finishes early.

## OCC replay and merge protocol

When multiple workers modify the same vault file, the system uses **Optimistic Concurrency Control (OCC)**:

1. **Content-hash detection** — conflicts are detected by file content hash, not line position
2. **Timestamp priority** — the earliest writer in the sprint window wins the conflict
3. **Quarantine** — the losing worker's change moves to `.gaijinn/merge/quarantine/<worker-id>/`
4. **Structural drain** — each unresolved conflict deducts 0.05 from the structural_score
5. **GIV re-validation** — after resolution, the winner's output is re-checked against allowed paths

On merge failure, do NOT force-overwrite. Replay via OCC, then re-trigger merge. Three consecutive merge failures halt the sprint — Council must approve a waive or rollback.

See [[30_Decisions/ADR-002-dual-invariant-domains]] for full protocol documentation.

## Verify

```bash
cd vaults/gaijinn-memory-fs
python -m pytest ../../tests/test_grid_executor.py -q -k deepseek
python 10_Operations/knowledge-linter.py --worker-gate --check
gaijinn hermes -i
```

For worker-gated validation, use `--worker-gate` so the local setup note can be checked before the merge-grid writes the canonical `.gaijinn/merge/governance.json` execution ledger.

## Troubleshooting

| Symptom | Fix |
|---------|------|
| `hermes executable not found` | Install Hermes Agent; ensure `hermes` on PATH |
| Auth / 401 | Check `~/.hermes/.env` or run `hermes login` |
| Auth / 401 (grid workers) | Workers need DEEPSEEK_API_KEY in env file — CLI login credentials do NOT propagate to workers |
| Auth / 401 (OAuth) | Verify DEEPSEEK_REFRESH_TOKEN + DEEPSEEK_CLIENT_ID + DEEPSEEK_CLIENT_SECRET all set |
| Wrong model | Use `deepseek-v4-flash`; run `hermes model`  Verify: DEEPSEEK_MODEL not set to stale value |
| Grid still uses Grok/Codex | Set `grid_executor: deepseek` or pick DeepSeek in UI; verify `.gaijinn/project.json` executor_profile |
| Orchestrator works, workers fail | DEEPSEEK_API_KEY not in env — see auth failover note in Option A above |
| Merge failure / OCC conflict | No force-overwrite. Replay per OCC rules: content-hash detect -> timestamp priority -> re-merge. See ADR-002 Protocol D |
| Convergence below threshold | Check governance.json structural_score. Simulated >=0.875, production 1.0. Waivable by ADR with partial state |
| Gateway port in use | Change GATEWAY_PORT to an unused value (e.g., 7378) |
| Autonomy loop not firing | Check GATEWAY_ENABLED and CRON_ENABLED are both true. Verify GAIJINN_AUTONOMY_INTERVAL_SEC >= 60 |
| Config/precedence confusion | See CONFIG PRECEDENCE in `.agents/hermes-deepseek.env.example`. Grid workers ignore `config.yaml` credentials. CLI flags override everything. |

Example env snippet: `.agents/hermes-deepseek.env.example`

## Related

- [[raw/constitution-v0-section-xiii]]
- [[30_Decisions/ADR-002-dual-invariant-domains]]
- [[00_Brain/invariants/INV-GAIJINN-BINDING]]
- [[10_Operations/tasks/OBSIDIAN-RUN-16]]
- [[10_Operations/HERMES-DEVELOPMENT-ORDERS]]
- [[40_Concepts/metrics-dashboard]]
- [[40_Concepts/hermes-cron-orchestration]]
