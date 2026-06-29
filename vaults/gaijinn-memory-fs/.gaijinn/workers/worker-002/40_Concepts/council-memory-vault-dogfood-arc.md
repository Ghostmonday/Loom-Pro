---
id: "CONCEPT-COUNCIL-MEMORY-DOGFOOD-ARC"
type: "Concept"
status: "active"
tags: [Domain/Vault, Dogfood]
related_concepts:
  - "[[40_Concepts/council-memory-index]]"
  - "[[40_Concepts/council-memory-convergence-semantics]]"
council_ref: "vault [5–82], [97–98]"
linked_operations:
  - "[[10_Operations/knowledge-linter.py]]"
  - "[[.gaijinn/bridge/council.md]]"
---

# Vault dogfood arc (distilled timeline)

## Phase 1 — 14-worker churn (Jun 17 PM)

- Repeated `grid-spawn` 14× deepseek via hermes
- Convergence oscillated: 0.5556 → 0.6667 → 0.8889
- Workers completed WUs but merge often **blocked all** (copy-mode / empty deltas)
- Amir: Hermes primary; Composer standing down [23–24]

## Phase 2 — Merge compounding session (Jun 18 AM)

- Cursor session notes [80]: design package + Codex implementation
- Manual 6-WU sprint → **6/6 merged, convergence 1.0** [82]
- DeepSeek 5-WU sprint → **5/5 pass, 277s** [97–98]

## Phase 3 — Hermes C1 (Jun 18 AM)

- Handoff [99] → governance/ledger files created in vault merge dir
- Memory scaffold: HERMES-MEMORY.md, hermes-memory-vault.md [107]

## Phase 4 — Empty spawn burn (Jun 18 AM–PM)

- Plan straddling → `work_units=[]` → 11 consecutive empty spawns (55 worker slots)
- Council repeatedly: **pause grid-spawn** [112–137]
- Convergence still 1.0 — vault content converged; **orchestration broken**

## Current truth (distill snapshot)

| Metric | Value |
|--------|-------|
| Production convergence | 1.0 (when governance honest) |
| Completion ledger | 23 entries |
| Plan backlog | 0 (when plan runs) |
| Vault linter | PASS when convergence + frontmatter clean |
| Blocker | `gaijinn plan` cross-domain straddling for vault-only |