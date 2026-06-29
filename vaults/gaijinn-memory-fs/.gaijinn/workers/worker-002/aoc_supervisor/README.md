# Supervisor API (vault mirror)

Canonical implementation lives in the monorepo root:

```
../../../../aoc_supervisor/
```

This directory is a **synced mirror** for vault taxonomy and linter scope (`lint-supervisor-api-imports`, billing endpoints). Do not edit here — change `aoc_supervisor/` at repo root and re-sync:

```bash
rsync -a --delete --exclude '__pycache__' aoc_supervisor/ vaults/gaijinn-memory-fs/aoc_supervisor/
```

Runtime `PYTHONPATH` and `pyproject.toml` resolve the monorepo package.