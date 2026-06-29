---
id: "CONCEPT-VAULT-FILESYSTEM"
type: "Concept"
status: "active"
promoted_from: "vault-design"
promoted_by: "worker-002"
promotion_date: "2026-06-17T22:10:00Z"
related_concepts:
  - "[[40_Concepts/memory-execution-loop]]"
  - "[[40_Concepts/vault-affairs]]"
  - "[[40_Concepts/vault-gaijinn]]"
  - "[[40_Concepts/metrics-dashboard]]"
  - "[[40_Concepts/ingress-vault-civilization]]"
  - "[[40_Concepts/promotion-pipeline]]"
system_tier: "semantic"
tags:
  - Domain/Vault
  - Domain/FileSystem
  - Cross-Vault
linked_decisions:
  - "[[30_Decisions/ADR-002-dual-invariant-domains]]"
  - "[[10_Operations/tasks/OBSIDIAN-RUN-16]]"
linked_invariants:
  - "[[00_Brain/invariants/INV-GAIJINN-BINDING]]"
linked_operations:
  - "[[10_Operations/HERMES-DEVELOPMENT-ORDERS]]"
  - "`aoc_supervisor/aoc_supervisor/api` (monorepo)"
  - "`aoc_supervisor/aoc_supervisor/billing` (monorepo)"
platform_ref: ".gaijinn/operations/FILESYSTEM-VAULT-TAXONOMY.md"
---

# Vault FileSystem — Machine Organization & Folder Taxonomy

The **FileSystem vault** defines the deterministic machine organization of gaijinn-memory-fs: folder taxonomy, naming conventions, file-type boundaries, and the structural skeleton that makes the vault navigable by agents and humans alike.

## Domain scope

The FileSystem domain governs how files are arranged, named, and partitioned:

| Layer | Description | Artifact |
|-------|-------------|----------|
| **Root** | Vault identity & entry points | [[README]], [[AGENTS]], [[CLAUDE]] |
| **Governance** | Constitution, decisions, invariants | `raw/`, `30_Decisions/`, `00_Brain/invariants/` |
| **Operations** | Tasks, orders, linter | `10_Operations/` |
| **Knowledge** | Concepts, projects, events | `40_Concepts/`, `20_Projects/`, `_multi-agent/` |
| **Config** | Gaijinn integration | `.gaijinn/project.json`, `.gaijinn/blueprint.md` |

## Taxonomy invariant

The vault follows a **strict folder taxonomy** inherited from the Gaijinn framework's write-time compiled memory pattern:

```
gaijinn-memory-fs/
├── 00_Brain/invariants/       # Hard invariants (immutable once accepted)
├── 10_Operations/             # Tasks, orders, linter scripts
│   ├── tasks/                 # Sprint manifests
├── 20_Projects/               # Project documentation
├── 30_Decisions/              # ADRs and ratified decisions
├── 40_Concepts/               # Promoted concepts (write-time compiled)
├── _multi-agent/              # Agent coordination artifacts
├── aoc_supervisor/            # Supervisor API (boundary gateway + billing)
├── raw/                       # Constitutional text (immutable)
├── .gaijinn/                  # Gaijinn platform integration
│   ├── bridge/                # Council coordination
│   ├── workers/               # Active work unit isolation
│   ├── merge/                 # Merge grid artifacts
│   └── ...                    # Pipeline configuration
└── ui/                        # Vault GUI intent maps
```

This taxonomy is enforced by the [[00_Brain/invariants/INV-GAIJINN-BINDING]] invariant and validated by the knowledge linter at `10_Operations/knowledge-linter.py`.

## Why separate from the vault

gaijinn-memory-fs **is** the FileSystem vault — it is the instantiation of this taxonomy. This concept note makes the taxonomy explicit so it can be reasoned about, evolved, and cross-linked to the other vault domains. Affairs ([[40_Concepts/vault-affairs]]) drives *what* goes where; Gaijinn ([[40_Concepts/vault-gaijinn]]) drives *how* it gets there.

## Naming conventions

| Rule | Requirement |
|------|-------------|
| Allowed characters | `a-z`, `0-9`, hyphens, underscores |
| Case | Lowercase only |
| Extensions | `.md` for knowledge, `.py` for tools, `.json`/`.yaml`/`.toml` for config |
| Frontmatter | YAML `---` required on all `.md` files: `id`, `type`, `status` |
| Wikilinks | Relative from vault root, no absolute paths |

## Cross-vault links

| Direction | Link |
|-----------|------|
| FileSystem → gaijinn-memory-fs identity | [[README]] (vault overview) |
| FileSystem → agent bootstrap | [[AGENTS]] (agent obligations reference taxonomy) |
| FileSystem → guidance | [[CLAUDE]] (workflow commands and governance) |
| FileSystem → Affairs | [[40_Concepts/vault-affairs]] (events produce files in taxonomy) |
| FileSystem → Gaijinn method | [[40_Concepts/vault-gaijinn]] (methodology determines taxonomy rules) |
| FileSystem → Memory Loop | [[40_Concepts/memory-execution-loop]] (loop traverses taxonomy) |

### Worker-004 validation (WU-014)

Sprint 6 confirmed the aoc_supervisor taxonomy entry in vault.yaml. The supervisor directory (`aoc_supervisor/aoc_supervisor/`) is now registered with `__init__.py` package entry, and vault.yaml linter enforces the `lint-docstring-consistency` and `lint-python-frontmatter` rules on all Python files in the taxonomy. No taxonomy violations detected.

## Orbit link (read-only)

> **Gaijinn Invariant Verification note:** This concept is a FileSystem vault mapping. Related platform artifact: `.gaijinn/operations/FILESYSTEM-VAULT-TAXONOMY.md` (owned by platform worker — see handoff ticket WU-002-002).

## Related

- [[README]] — vault overview and infrastructure table
- [[AGENTS]] — agent rules referencing write-path taxonomy
- [[CLAUDE]] — guidance for navigating the vault
- [[30_Decisions/ADR-002-dual-invariant-domains]] — dual-domain architecture binding
- [[00_Brain/invariants/INV-GAIJINN-BINDING]] — invariant enforcing taxonomy compliance
- [[40_Concepts/vault-affairs]] — sibling vault: life events
- [[40_Concepts/vault-gaijinn]] — sibling vault: methodology
