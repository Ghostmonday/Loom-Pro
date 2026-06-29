# Loom C08 — Minimize Dark Bridges (LOOM-203)

**Depends on:** C07

## Objective

Choose partition/weld plan with minimum `dark_bridge_count` vs graph-only baseline. Attach `teleology_receipt` and `dark_bridge_count` to result. Write `.gaijinn/blueprint.json` on session root.

## MAY edit

- `aoc_supervisor/aoc_supervisor/loom_blueprint_synthesizer.py`
- `aoc_supervisor/aoc_supervisor/orchestration_envelope.py` (reuse `_edge_classification` if needed)
- `tests/test_loom_synthesizer.py::test_min_dark_bridges`

## Verify

```bash
.venv/bin/python -m pytest tests/test_loom_synthesizer.py::test_min_dark_bridges -q --no-cov
```

## Acceptance

- `flow.loom_synthesis_min_dark_bridges` mirror scenario passes when wired in C19