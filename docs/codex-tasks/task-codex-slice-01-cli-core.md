# Codex Slice 1 — CLI Core & Analysis

**MASTER:** `docs/codex-tasks/MASTER-codex-fullpass.md`
**Baseline:** `pre-codex-fullpass-6361ad5`

## Objective

Audit and harden CLI core + analysis entrypoints. Small focused diffs only.

## Setup

```bash
cd /home/ghostmonday/Desktop/Loom
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
python -m pytest tests/test_cli.py tests/test_gravity.py tests/test_blueprint.py tests/test_moat.py -q
```

## MAY edit

- `aoc-cli/aoc_cli/{cli,gravity,giv,moat,blueprint,state,errors}.py`
- `aoc-cli/aoc_cli/commands/{scan,analyze_,plan,compile_prompt,init_,status,doctor,version}.py`
- `tests/test_cli.py`, `tests/test_gravity.py`, `tests/test_blueprint.py`, `tests/test_moat.py`, `tests/test_giv.py`

## MUST NOT edit

- `ui/**`, `aoc_supervisor/**`, merge/grid commands, inference modules (`inferring.py`, etc.)

## Work

1. Read slice files; note gaps (TODOs, partial status comments, missing tests).
2. Fix only bugs or clear robustness gaps found in audit.
3. Write `.gaijinn/codex/slice-01-report.md` (findings + changes).
4. Slice acceptance + full `pytest tests/ -q` must pass.

## Acceptance

- Slice tests green
- Report at `.gaijinn/codex/slice-01-report.md`
- Council-ready one-line summary in report header
