# Structural audit test baseline (pre-P0 stack)

Evidence captured before opening the runtime-containment PR stack.

## Exact failing test

```text
tests/test_audit.py::test_run_structural_audit_on_gaijinn_repo
```

## Failure on base commit (`0e0eeae`)

```text
aoc_cli.blueprint.BlueprintValidationError: work unit straddles vault and code paths:
  aoc-cli/... (monorepo code tree)
  aoc_supervisor/aoc_supervisor/ui_intent.py
  vaults/gaijinn-memory-fs/aoc_supervisor/aoc_supervisor/ui_intent.py
```

Command:

```bash
git checkout 0e0eeae
PYTHONPATH=aoc-cli:aoc_supervisor .venv/bin/python3.11 -m pytest \
  tests/test_audit.py::test_run_structural_audit_on_gaijinn_repo -q
# exit code 1
```

## Failure on patched commit (full P0 stack working tree)

Same test, same `BlueprintValidationError`, same vault/code straddle path list.

```bash
# with P0 stack changes applied (pre-merge working tree)
PYTHONPATH=aoc-cli:aoc_supervisor .venv/bin/python3.11 -m pytest \
  tests/test_audit.py::test_run_structural_audit_on_gaijinn_repo -q
# exit code 1
```

## Reason it is unrelated

The P0 stack does not modify `aoc_cli/blueprint.py`, `generate_blueprint()`, or vault mirror layout. The failure is triggered when `run_structural_audit()` scans the **whole monorepo** (including `vaults/gaijinn-memory-fs/` mirrors of `aoc_supervisor/`) and blueprint generation groups vault + code paths into one work unit. That violates `resolve_work_unit_domain()` — a **brownfield graph topology / vault mirror** issue, not executor isolation, assignment, preflight, or billing.

Full suite with stack applied: **417 passed**, this test failed, 1 skipped (`test_preflight victory lap`).

## Tracking issue

Track under P3 architecture cleanup: exclude generated vault mirrors from structural audit scope, or dedupe mirror paths before blueprint generation. Do not block the P0 containment stack on this test.