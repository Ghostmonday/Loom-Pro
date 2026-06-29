---
id: "VAULT-GEMINI-SHARE"
type: "Operations"
status: "active"
tags: [Operations, Export, Topology]
links:
  - "[[10_Operations/tasks/VAULT-TOPOLOGY-SWARM]]"
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/hermes-memory-vault]]"
---

# Share the entire vault with Gemini

One command builds everything Gemini needs. You do not paste 54 files by hand.

## Step 1 — Generate bundle

```bash
cd /home/ghost-monday/Desktop/Gaijinn
bash scripts/dev/export-vault-gemini-bundle.sh
```

Output:

| Artifact | Path |
|----------|------|
| **Upload this** | `vaults/gaijinn-memory-fs/.gaijinn/exports/gemini-bundle-latest.tar.gz` |
| Unpacked dir | `vaults/gaijinn-memory-fs/.gaijinn/exports/gemini-bundle-<timestamp>/` |

## Step 2 — Upload to Gemini

1. Open Gemini (1.5 Pro or later — needs file + long context).
2. Attach **`gemini-bundle-latest.tar.gz`** (or upload unpacked folder to Drive and attach).
3. Paste the contents of **`GEMINI-REVIEW-PROMPT.md`** from inside the bundle as your first message.

## What is inside the bundle

| File | What Gemini learns |
|------|-------------------|
| `vault-tree.txt` | Full sidebar / folder structure |
| `topology-manifest.json` | Every note: `id`, `type`, `tags`, word count, outbound wikilinks |
| `topology-heuristics.json` | Pre-computed merge/split/council-overlap seeds |
| `graph.json` | 320+ wikilink edges from `gaijinn scan` |
| `metrics_manifest.json` | Gravity, rejected nodes, shadow bridges |
| `protocols/` | AGENTS, HERMES-MEMORY, council index, vault.yaml, events tail |
| `40_Concepts/*.md` | Full text of all 37 concept files |
| `vault-ui-intent-map.json` | Machine intent overlay |
| `GEMINI-REVIEW-PROMPT.md` | Structured review instructions + JSON output schema |

## Step 3 — Bring Gemini output back

Ask Gemini to return **`vault-topology-review.json`** with merges, splits, MOCs, and swarm work units.

Save to:

```
vaults/gaijinn-memory-fs/pending/vault-topology-gemini-review.json
```

Then run the swarm task: [[10_Operations/tasks/VAULT-TOPOLOGY-SWARM]].

## If you cannot upload archives

Paste in **three messages** (in order):

1. **`GEMINI-REVIEW-PROMPT.md`** + **`topology-heuristics.json`**
2. **`topology-manifest.json`** (single JSON — 54 nodes)
3. **`protocols/`** files concatenated (AGENTS + HERMES-MEMORY + council-memory-index)

Skip binary; concepts are the critical layer.

## Current vault snapshot (2026-06-18)

| Metric | Value |
|--------|-------|
| Markdown files | 54 |
| `40_Concepts/` | 37 (18 council-memory + 19 core) |
| Wikilink edges | ~320 |
| Episodic ledger | `_multi-agent/events.md` (append-only) |
| Boot router | `40_Concepts/council-memory-index.md` |

## Gemini blueprint alignment

| Your blueprint | Our vault today | Swarm action |
|----------------|-----------------|--------------|
| Journal stream / daily notes | `_multi-agent/events.md` | Add `Current_Context.md` + optional `journal/YYYY-MM-DD.md` |
| Frontmatter over folders | `.agents/vault.yaml` taxonomy | WU-TOPO-004 unify drift |
| MOC router | `council-memory-index` only | WU-TOPO-003 add `000_Brain_MOC.md` |
| Bi-directional edges | wikilink linter + graph.json | WU-TOPO-005 rewire after merges |

## After Gemini review

```bash
gaijinn council say --as cursor "Vault topology: Gemini review ingested. Starting WU-TOPOO swarm."
gaijinn grid-spawn --workers 5 --executor hermes -m deepseek-v4-flash
```