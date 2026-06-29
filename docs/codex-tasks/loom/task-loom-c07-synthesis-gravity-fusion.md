# Loom C07 — Synthesis Gravity Fusion (LOOM-203)

**Depends on:** C06

## Objective

Fuse forge workstreams with `aoc_cli.blueprint.generate_blueprint` gravity/curvature output. Set `projection_mode=loom_synthesis` on merged artifact.

## MAY edit

- `aoc_supervisor/aoc_supervisor/loom_blueprint_synthesizer.py`
- `tests/test_loom_synthesizer.py::test_gravity_fusion`

## Algorithm refs

- `aoc-cli/aoc_cli/gravity.py` → `compute_gravity_and_curvature`
- `aoc-cli/aoc_cli/blueprint.py` → `generate_blueprint`

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_synthesizer.py::test_gravity_fusion -q --no-cov
```