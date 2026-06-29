---
id: "CONCEPT-COUNCIL-MEMORY-PROTOCOL"
type: "Concept"
status: "active"
tags: [Domain/Governance, Council, Memory]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/dual-ledger-bridge]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
---

# Council — protocol (distilled)

## What council is

Single shared thread for humans and agents. **No relay through Amir.** Machine address (vault): `vaults/gaijinn-memory-fs/.gaijinn/bridge/council.md`.

## Binding rules (from thread + Section XIII)

1. **Read** council at session start and before substantive work.
2. **Post** after decisions, handoffs, sprint complete/fail: `gaijinn council say --as <author> "..."`
3. **USER** posts `--as user`. Workers: `--as deepseek --id worker-NNN` or `--as hermes`.
4. Blueprint = intent map of the environment — disputes about scope belong on council.

## Dual ledger (never substitute)

| Ledger | Role |
|--------|------|
| `.gaijinn/bridge/council.md` | Operational — handoffs, BLOCKED, spawn/merge status |
| `_multi-agent/events.md` | Episodic semantic — promotions, sprint outcomes |

Material changes → **both**.

## Council corruption incident (monorepo [56–57])

`council.jsonl` gained line-number prefixes (`56|{...}`) → `gaijinn council say` broke. **Fix:** rebuild jsonl from council.md. Hermes documented this; verify jsonl parses after manual edits.

## Composer watcher

`composer-watcher` auto-processes `@composer` / ACTION lines — not a substitute for Hermes executing vault work. Amir directive [23]: **Hermes owns vault + grid**; Composer last resort / `@composer BLOCKED` only.