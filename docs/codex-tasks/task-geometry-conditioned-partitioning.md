# Codex Task — Geometry-Conditioned Task Isolation (DCOE Blueprint Compiler)

## Objective
Rewrite blueprint work-unit partitioning from naive directory grouping to **geometry-conditioned atomic blocks** driven by Ollivier-Ricci curvature from `gravity.py`.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Compiler rules (non-negotiable)

1. **Dark Bridge** — edge with `kappa < CURVATURE_HARD_FLOOR` (-0.3), or legacy `is_shadow_bridge` with κ < 0
2. **Surgery rule** — Dark Bridge endpoints MUST share one `WorkUnit` (union-find binding)
3. **Contraction rule** — subgraphs linked only by κ ≥ 0 edges MAY run in parallel work units
4. **Stealth** — forced serialization uses `helpers.stealth.dark_bridge_*` messages

## Files
- `aoc-cli/aoc_cli/gravity.py` — `CURVATURE_HARD_FLOOR`, `is_dark_bridge` on edges
- `aoc-cli/aoc_cli/blueprint.py` — `generate_blueprint()`, `_atomic_blocks()`, `_dark_bridge_edges()`
- `aoc-cli/aoc_cli/helpers/stealth.py` — logging sanitization

## Verification
```bash
.venv/bin/python -m pytest tests/test_blueprint.py tests/test_stealth.py -q
.venv/bin/python -m pytest -q
```