#!/usr/bin/env bash
# Export gaijinn-memory-fs for external review (Gemini / swarm topology pass).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VAULT="$ROOT/vaults/gaijinn-memory-fs"
OUT="$VAULT/.gaijinn/exports/gemini-bundle-$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$OUT.tar.gz"

mkdir -p "$OUT"

echo "Exporting vault → $OUT"

# 1. Folder tree (no .obsidian, no binary noise)
(
  cd "$VAULT"
  find . \( -path './.obsidian' -o -path './.git' \) -prune -o -type f -print \
    | grep -vE '\.(png|jpg|gif|webp)$' \
    | sort
) > "$OUT/vault-tree.txt"

# 2. Topology manifest (Python)
python3 - "$VAULT" "$OUT" << 'PY'
import json, re, sys
from pathlib import Path
from collections import defaultdict

vault = Path(sys.argv[1])
out = Path(sys.argv[2])

def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    block = m.group(1)
    for line in block.splitlines():
        s = line.strip()
        if not s or s.startswith("-") or ":" not in s:
            continue
        k, _, v = s.partition(":")
        fm[k.strip()] = v.strip().strip('"')
    return fm, text[m.end():]

def wikilinks(text):
    return sorted(set(re.findall(r"\[\[([^\]|#]+)", text)))

nodes, edges = [], []
for p in sorted(vault.rglob("*.md")):
    if ".obsidian" in p.parts:
        continue
    rel = p.relative_to(vault).as_posix()
    text = p.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    links = wikilinks(text)
    nodes.append({
        "path": rel,
        "id": fm.get("id", ""),
        "type": fm.get("type", ""),
        "status": fm.get("status", ""),
        "tags": fm.get("tags", ""),
        "word_count": len(body.split()),
        "wikilinks_out": links,
        "cluster": (
            "council-memory" if "council-memory" in rel
            else rel.split("/")[0] if "/" in rel else "root"
        ),
    })
    for t in links:
        edges.append({"source": rel, "target": t, "kind": "wikilink"})

manifest = {
    "vault_id": "gaijinn-memory-fs",
    "exported_at_utc": out.name.replace("gemini-bundle-", "").rstrip("Z") + "Z",
    "node_count": len(nodes),
    "edge_count": len(edges),
    "nodes": nodes,
    "edges": edges,
}
(out / "topology-manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
)

# Merge/split heuristics for swarm seed
merge_candidates, split_candidates, overlap = [], [], []
by_path = {n["path"]: n for n in nodes}
concept_nodes = [n for n in nodes if n["path"].startswith("40_Concepts/")]

for n in concept_nodes:
    wc = n["word_count"]
    stem = Path(n["path"]).stem
    if wc < 130 and "index" not in stem and "test-" not in stem:
        merge_candidates.append({"path": n["path"], "words": wc, "reason": "thin concept note"})
    if wc > 450:
        split_candidates.append({"path": n["path"], "words": wc, "reason": "dense — consider sub-nodes"})

# council vs core overlap
council = [n for n in concept_nodes if "council-memory" in n["path"]]
core = [n for n in concept_nodes if "council-memory" not in n["path"]]

def tokens(s):
    return set(re.findall(r"[a-z]{4,}", s.lower()))

for c in council:
    ct = tokens(c["path"] + " " + c.get("id", ""))
    for k in core:
        kt = tokens(k["path"] + " " + k.get("id", ""))
        shared = sorted(ct & kt - {"concept", "council", "memory"})
        if len(shared) >= 2:
            overlap.append({
                "council": c["path"],
                "core": k["path"],
                "shared_tokens": shared,
                "action": "review_merge_or_crosslink",
            })

heuristics = {
    "merge_candidates": merge_candidates,
    "split_candidates": split_candidates,
    "council_core_overlap": overlap[:30],
    "swarm_prompt": "See GEMINI-REVIEW-PROMPT.md in this bundle",
}
(out / "topology-heuristics.json").write_text(
    json.dumps(heuristics, indent=2) + "\n", encoding="utf-8"
)
print(f"Wrote manifest: {len(nodes)} nodes, {len(edges)} edges")
PY

# 3. Protocol pack (what Hermes reads at boot)
PROTOCOLS=(
  "AGENTS.md"
  "CLAUDE.md"
  "10_Operations/HERMES-MEMORY.md"
  "10_Operations/HERMES-DEVELOPMENT-ORDERS.md"
  "40_Concepts/council-memory-index.md"
  "40_Concepts/hermes-memory-vault.md"
  "40_Concepts/obsidian-city-neighborhoods.md"
  ".agents/vault.yaml"
  "_multi-agent/events.md"
)
mkdir -p "$OUT/protocols"
for f in "${PROTOCOLS[@]}"; do
  if [[ -f "$VAULT/$f" ]]; then
    cp "$VAULT/$f" "$OUT/protocols/$(echo "$f" | tr '/' '_')"
  fi
done

# 4. Graph snapshot
cp "$VAULT/.gaijinn/graph.json" "$OUT/graph.json" 2>/dev/null || true
cp "$VAULT/.gaijinn/metrics_manifest.json" "$OUT/metrics_manifest.json" 2>/dev/null || true
cp "$VAULT/ui/vault-ui-intent-map.json" "$OUT/vault-ui-intent-map.json" 2>/dev/null || true

# 5. All concept bodies (for Gemini full read)
mkdir -p "$OUT/40_Concepts"
cp "$VAULT"/40_Concepts/*.md "$OUT/40_Concepts/" 2>/dev/null || true

# 6. Review prompt
cat > "$OUT/GEMINI-REVIEW-PROMPT.md" << 'PROMPT'
# Gemini Vault Topology Review — gaijinn-memory-fs

You are reviewing an **agent-operated Obsidian memory vault** (Hermes orchestrator). Humans do not relay memory; the vault must be machine-readable, topologically stable, and bootable in one pass.

## Bundle contents

| File | Purpose |
|------|---------|
| `vault-tree.txt` | Full file tree |
| `topology-manifest.json` | Every `.md` node: frontmatter, word count, outbound wikilinks |
| `topology-heuristics.json` | Seed merge/split/overlap candidates (verify and extend) |
| `graph.json` | Gaijinn scan output (wikilink + code edges) |
| `metrics_manifest.json` | Gravity, rejected nodes, shadow bridges |
| `protocols/` | Boot sequence: AGENTS, HERMES-MEMORY, council-memory-index, vault.yaml |
| `40_Concepts/` | All promoted concept notes (full text) |
| `vault-ui-intent-map.json` | UI intent overlay |

## Your tasks

1. **Merge audit** — Which nodes should become ONE note? (duplicate semantics, thin stubs, council distill ↔ core concept overlap)
2. **Split audit** — Which nodes should become MANY? (oversized MOCs, mixed concerns, metrics-dashboard-style megnotes)
3. **MOC redesign** — Propose `000_Brain_MOC` router + journal stream (`_multi-agent/` vs daily notes) aligned with existing `events.md`
4. **Frontmatter schema** — Unify `id`, `type`, `status`, `dependencies` across 54 files; flag drift
5. **Edge plan** — Min edges per concept, kill orphan risk, reduce shadow-bridge coupling
6. **Output format** — Return JSON:
   ```json
   {
     "merges": [{"into": "path", "from": ["path", ...], "rationale": "..."}],
     "splits": [{"from": "path", "into": ["path", ...], "rationale": "..."}],
     "new_mocs": [{"path": "...", "indexes": ["..."]}],
     "frontmatter_patches": [{"path": "...", "add": {}, "remove": []}],
     "swarm_work_units": [{"id": "WU-...", "paths": [], "action": "merge|split|rewire"}]
   }
   ```

## Constraints (do not violate)

- Section XIII: dual ledger (`events.md` + `council.md`) stays separate
- `council-memory-*` is distilled episodic council — do not collapse into one file; merge only true duplicates with core concepts
- `40_Concepts/metrics-dashboard.md` is intentionally dense — split by metric domain if needed
- Vault paths in taxonomy: `00_Brain`, `10_Operations`, `20_Projects`, `30_Decisions`, `40_Concepts`, `_multi-agent`, `pending/`

## Context

Hermes boot: `council-memory-index` → phase nodes → `HERMES-MEMORY.md` loop.
Target: cold-start without user relay; ≥18 concepts with honest graph gravity.
PROMPT

# 7. Tarball for upload
tar -czf "$ARCHIVE" -C "$(dirname "$OUT")" "$(basename "$OUT")"

echo ""
echo "=== GEMINI EXPORT READY ==="
echo "Directory: $OUT"
echo "Archive:   $ARCHIVE"
echo "Size:      $(du -h "$ARCHIVE" | cut -f1)"
echo ""
echo "Upload $ARCHIVE to Gemini (or paste GEMINI-REVIEW-PROMPT.md + topology-manifest.json)"
echo "Latest symlink: $VAULT/.gaijinn/exports/gemini-bundle-latest.tar.gz"
ln -sfn "$ARCHIVE" "$VAULT/.gaijinn/exports/gemini-bundle-latest.tar.gz"