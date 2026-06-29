---
id: "CONCEPT-COUNCIL-MEMORY-EXECUTOR"
type: "Concept"
status: "active"
tags: [Domain/Orchestration, Executor/DeepSeek]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[20_Projects/deepseek-hermes-setup]]"
council_ref: "vault [4–26], monorepo [31–37]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Executor stack (distilled)

## Proven production command (2026-06-18)

```bash
gaijinn grid-spawn --workers N --executor hermes -m deepseek-v4-flash
export GAIJINN_OPERATOR=1
set -a && source ~/.hermes/.env && set +a
```

## Locked decisions

| Use | Do NOT use (for DeepSeek) |
|-----|---------------------------|
| `hermes` executor | `codex exec -m deepseek-v4-flash` (400 on ChatGPT account) |
| `deepseek-v4-flash` model | Grok grid on vault unless USER orders |
| `~/.hermes/.env` for workers | `hermes login` alone (workers don't inherit) |

## Schema v5 fix (monorepo [34])

`hermes_development_loop.py` was reading wrong profile key → defaulted to `deepseek` → **codex** binary. Fixed to read `profiles[default_profile].executor` → **hermes**.

## Executor profile (vault)

`project.executor-profile.json`: default `deepseek-grid` + `deepseek-orchestrator`. Command template: `hermes -m {model} --provider {provider} --yolo`.

## Model uniformity

All workers in one sprint **same model** — blueprint interpretation drift otherwise (terminal-bridge design).