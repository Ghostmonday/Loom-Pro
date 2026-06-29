---
id: "HERMES-SPRINT-DIRECTIVE"
type: "Operations"
status: "active"
scope: "vault-operations"
tags:
  - Operations
  - Agent-Rules
  - Sprint
---

# Hermes Sprint Directive — Obsidian + Gaijinn (Composer standing down)

**From:** Composer (relay for Amir) · council #692  
**Authority:** Hermes owns execution; Composer tokens last resort only.

## Objective

Run **gaijinn-memory-fs** vault civilization sprint: DeepSeek grid on Obsidian content, merge compounds, linter PASS, convergence ≥ 0.875.

## Execute now (Hermes / cron / `hermes-development-loop`)

```bash
cd /home/ghost-monday/Desktop/Gaijinn/vaults/gaijinn-memory-fs
export GAIJINN_PROJECT_ROOT=.
export PYTHONPATH="/home/ghost-monday/Desktop/Gaijinn/aoc-cli:/home/ghost-monday/Desktop/Gaijinn/aoc_supervisor"
export GAIJINN_OPERATOR=1
```

1. **Diagnose** — `gaijinn status` + `gaijinn collect` (if 0 completed and workers `running` >30m → stale sprint)
2. **Recover stale** — `gaijinn run-grid --workers 14 --force` then `grid-spawn --executor deepseek --model deepseek-v4-flash --workers 14`
3. **Monitor** — `gaijinn monitor` until terminal
4. **Weld** — `gaijinn collect && gaijinn validate-worker && gaijinn merge-grid --strategy sequential`
5. **Lint** — `python3 10_Operations/knowledge-linter.py --check --exclude-dirs pending`
6. **Council** — post sprint_id, merged count, convergence, next WU

## Ping Composer ONLY if

- `validate-worker` gate wrong for vault (pytest vs vault_linter)
- `merge-grid` platform bug
- `gaijinn serve :8082` required and broken

Use: `@composer BLOCKED: <one line>`

## Do NOT

- Wait for Amir to open Composer
- Re-run WU-013 governance sync unless merge compounds new work
