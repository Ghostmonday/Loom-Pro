# Code Hygiene Audit — DeepSeek Report

**Auditor:** DeepSeek (worktree: `Loom-deepseek`)
**Date:** 2026-06-30
**Base report:** `docs/audit/dry-run-report.md` (2026-06-30, 26.8 KB)
**Status:** Merge-captain-ready review

---

## 1. Branch and Worktree Confirmation

| Check | Status |
|---|---|
| `pwd` | `/home/ghostmonday/Desktop/Loom-deepseek` ✅ |
| `git status` | Clean — no tracked diff from `main`, no staged changes, no source files modified |
| `git diff --check` on audit docs | Clean |
| Branch | `audit/code-hygiene-pass` (based on current `main`) |
| `docs/audit/` contents | `dry-run-report.md` (pre-existing), `code-hygiene-deepseek-report.md` (this file) |
| Unexpected dirty files | None — only the two untracked audit docs |

> **Sandbox note:** The initial audit was run from a sandboxed terminal that could not see the parent repo at `/home/ghostmonday/Desktop/Loom`. Git operations are fully functional from the real environment. All findings below are based on direct file reads, `grep`/`rg` searches, and line-count analysis; no source files were modified.

---

## 2. Existing Report Summary

The dry-run report (`docs/audit/dry-run-report.md`) is a thorough 26.8 KB document covering ~90 source files across the `aoc_cli/`, `aoc_supervisor/`, `tests/`, and root-level directories. It is well-organized into 14 sections with executive summary and statistics.

### Top Findings Worth Acting On

| Priority | Finding | Est. Impact |
|---|---|---|
| **P1** | 7 orphan patch scripts in root (1,221 lines total) — patches already applied, excluded from ruff | ~1,221 lines removed |
| **P2** | Dead code: 9 unambiguous items (dead functions, unreachable branches, unused constants) | ~50 lines removed |
| **P3** | Inline imports at 9+ call sites in `merge_grid.py` — redundant `from ..state import transition_worker_state` | -8 lines net, consistency |
| **P4** | Misplaced imports (6 files: imports inside functions or at EOF instead of top-level) | 0 semantic change, convention |
| **P5** | Within-file duplicate logic (redundant loops, dedup sets over unique data) | ~7 lines removed |

### Items Too Broad or Risky for First Pass

- **Cross-file duplicate logic extraction** (Section 4). The 9 patterns require shared-utility extraction. Changes API boundaries and risks import cycles. Needs a dedicated refactoring pass.
- **Type-hint gaps across ~20 functions** (Section 9). Low individual risk, but touches 10+ files. Better as batch two.
- **`_process_is_running` bug fix** (8.1). Real bug (exit_code=0 treated as "running"), but touches spawn governance logic. Needs unit test verification before change.
- **`_assert_greenfield_blueprint` condition** (8.2). Medium confidence; needs human reading to confirm.
- **`_patch_testclient_for_httpx28`** (dry-run "uncertain" list). 270 lines of test monkey-patch loaded in production. Requires architectural decision.
- **`websocket_telemetry.py` session_overrides memory leak** (dry-run "uncertain" list). Requires design decision (LRU vs periodic cleanup).
- **Orphan patch script deletion.** Despite high confidence, 7 file deletions and `pyproject.toml` config cleanup is best done as a dedicated follow-up pass, not mixed with code changes.

### Line Number Corrections to Base Report

The dry-run report has minor line-number drift in `moat_authority.py`:
- `import hashlib` at line **837** (not 876)
- End-of-file imports (`import sys`, `import builtins`, `import subprocess`) at lines **984–986** (not 975–977)

These do not affect the validity of the findings.

---

## 3. Recommended First Cleanup Slice

**5 files, ~22 lines of change.** Zero semantic risk. All changes are mechanical deletions or top-level import consolidation.

| # | File | Change | Lines Delta |
|---|---|---|---|
| 1 | `aoc_supervisor/aoc_supervisor/billing.py` | Remove 3 dead ledger wrapper functions (`_locked_ledger`, `_read_ledger`, `_write_ledger`, lines 390–404) | **−13** |
| 2 | `aoc_supervisor/aoc_supervisor/question_policy.py` | Remove dead `rank_candidate_domains` (line 153) and `_answered_domains` (line 61); remove both from `__all__` | **−16** |
| 3 | `aoc-cli/aoc_cli/commands/merge_grid.py` | Consolidate 9× inline `from ..state import transition_worker_state` → single top-level import (net −8 lines) | **−8** |
| 4 | `aoc-cli/aoc_cli/commands/council.py` | Move `import json` from inside function (line 53) to module-level | **0** |
| 5 | `aoc-cli/aoc_cli/blueprint.py` | Move `from pathlib import Path` from inside 2 functions (lines 234, 1000) to module-level | **−4** |

**Why these five:** All are pure deletions or top-level consolidations. No control flow changes. No new dependencies. No risk of regression. Can be verified by `pytest collection`, `ruff check`, and a smoke-test import.

---

## 4. Findings Table

All findings below are **verified by direct source inspection**. Risk: L=Low, M=Medium, H=High.

### 4.1 Dead Code

| File | Line(s) | Issue | Proposed Fix | Risk | Verification |
|---|---|---|---|---|---|
| `aoc_supervisor/billing.py` | 390–404 | `_locked_ledger`, `_read_ledger`, `_write_ledger` — zero callers (grep confirms) | Remove 3 functions | L | `pytest` collection, `ruff` |
| `aoc_supervisor/question_policy.py` | 61–68, 153–164 | `_answered_domains` and `rank_candidate_domains` — zero external callers. Docstring of `rank_candidate_domains` says "not used for questioning" | Remove both + `__all__` entries | L | `pytest` collection, `ruff`, `rg` for remaining refs |
| `aoc-cli/state.py` | 170 | `"schema_version": schema_version` in dict — constructor ignores it and hardcodes `SCHEMA_VERSION` | Remove dict entry | L | `pytest` collection |
| `aoc_supervisor/complexity.py` | 54–55 | `compute_complexity_index(snapshot)` — trivial wrapper returning `snapshot.integrity_score`, zero callers | Remove function | L | `pytest` collection, `rg` |
| `aoc_supervisor/workflow_evaluator.py` | 41–44 | `PKM_INTENT` multi-line constant — zero references outside definition | Remove constant | L | `pytest` collection, `rg` |
| `aoc_supervisor/intent_blueprint_state.py` | 163–167 | `assert_status()` — zero callers | Remove function | L | `pytest` collection |
| `aoc-cli/moat_authority.py` | 221–229 | Unreachable `RuntimeError` in `_acquire_handle_lock` — guarded by `_locking_available()` check above | Remove `raise` block | L | `pytest` collection |
| `aoc-cli/commands/monitor.py` | 51, 54 | `last_signature = None` in `except`/`finally` — function exits before value is read | Remove 2 dead assignments | L | `pytest` collection |

### 4.2 Unused Imports & Re-exports

| File | Line(s) | Issue | Proposed Fix | Risk | Verification |
|---|---|---|---|---|---|
| `aoc-cli/helpers/diagnostics.py` | 18 | `from ..blueprint import Blueprint` — symbol never used in file body | Remove import | L | `ruff check`, `pytest` |
| `aoc-cli/helpers/constants.py` | 82, 83, 98 | `COUNCIL_MD_PATH`, `MANIFEST_PATH`, `HERMES_BINARY` — zero consumers in live code | Remove 3 constants | L | `rg`, `pytest` |
| `aoc-cli/helpers/__init__.py` | multiple | 17+ dead private re-exports from `.scan` and `.workers` modules — zero external importers | Remove from `__all__` and import statements | L | `rg` for cross-module usage |
| `aoc_supervisor/question_policy.py` | 9, 197 | `get_analysis_recovery` imported + exported — function defined elsewhere, zero callers | Remove import + `__all__` entry | L | `rg` |
| `tests/fixtures/contract_imports.py` | 13, 20 | Unused `TypeVar` and `T` | Remove | L | `pytest` collection |

### 4.3 Misplaced Imports

| File | Line(s) | Issue | Proposed Fix | Risk | Verification |
|---|---|---|---|---|---|
| `aoc-cli/moat_authority.py` | 984–986 | `import sys`, `import builtins`, `import subprocess` after all function definitions | Move to top-level | L | `pytest` collection |
| `aoc-cli/moat_authority.py` | 837 | `import hashlib` inside `_violation()` | Move to top-level | L | `pytest` collection |
| `aoc-cli/commands/council.py` | 53 | `import json` inside function gated by `json_output` flag | Move to top-level | L | `pytest` collection |
| `aoc-cli/commands/merge_grid.py` | 156–240 | 9× inline `from ..state import transition_worker_state` | Single top-level import | L | `pytest` collection, verify all 9 call sites resolve |
| `aoc-cli/blueprint.py` | 234, 1000 | `from pathlib import Path` inside 2 functions | Move to top-level | L | `pytest` collection |
| `aoc_supervisor/teleology_artifact.py` | 349 | `import re` inside function | Move to top-level | L | `pytest` collection |
| `aoc_supervisor/adaptive_question_engine.py` | 154, 395 | `import uuid` inside 2 functions | Single top-level `import uuid` | L | `pytest` collection |

### 4.4 Redundant / Duplicate Logic (Within-File)

| File | Line(s) | Issue | Proposed Fix | Risk | Verification |
|---|---|---|---|---|---|
| `aoc_supervisor/intent_forge_service.py` | 75–78 | Redundant node loop — first loop marks stale nodes, second loop (84–87) covers same IDs with identical body | Remove first loop (75–78) | L | `pytest`, verify stale-node marking moves to second loop |
| `aoc_supervisor/teleology_artifact.py` | 240–255 | Redundant `seen` set filtering hardcoded tuple of unique values — all elements unique by construction | Replace with `phases = list(statuses)` | L | `pytest` collection |
| `aoc-cli/commands/analyze_.py` | 107–139 | 6 function calls with same args repeated in `json_output` and non-`json_output` branches | Compute summary once before branch | L-M | Review: same calls, same args, different output format |
| `aoc-cli/blueprint.py` | 614 | `_ = dark_bridge_internal_log(source, target)` — unnecessary discard | Remove `_ = ` prefix | L | `pytest` collection |

### 4.5 Overly Broad Exception Handlers

| File | Line(s) | Issue | Proposed Fix | Risk | Verification |
|---|---|---|---|---|---|
| `aoc-cli/state.py` | 120, 379 | `except Exception: temp_path.unlink(...); raise` in temp-file cleanup | Narrow to `except OSError` | L | `pytest` collection, verify cleanup still fires |
| `aoc-cli/moat_authority.py` | 1053, 1068 | `except Exception: pass` in containment hooks | Catch `(ValueError, OSError)` | L-M | Review containment semantics |
| `aoc_supervisor/reasoning_provider.py` | 648–649 | `except Exception: pass` in cache write | Catch `(OSError, json.JSONDecodeError)` | L | `pytest` collection |

### 4.6 Logic Inconsistencies (Review Before Action)

| File | Line(s) | Issue | Proposed Fix | Risk | Verification |
|---|---|---|---|---|---|
| `aoc_supervisor/spawn_governance.py` | 485–501 | `_process_is_running` treats `exit_code=0` (success) as "running" because `0` is falsy | Check `exit_code is not None` before status fallback | M | Needs targeted unit test |
| `aoc_supervisor/orchestrate_session.py` | 354–367 | Inconsistent condition: `keyword_mode=False` + `mode="intent"` allows `"keyword"` as valid projection | Restructure condition | M | Needs human review |
| `aoc_supervisor/conflict_resolver.py` | 64–65 | `state` parameter stored to `_` (unused) — silently ignored | Remove param or implement | M | Check all callers |

### 4.7 Stale / Misleading Comments

| File | Line(s) | Issue | Proposed Fix | Risk | Verification |
|---|---|---|---|---|---|
| `aoc-cli/commands/promote.py` | 29 | Docstring references `.gaijinn/merge/governance.json`; code checks `.gaijinn/bridge/council.md` | Update docstring | L | Read |
| `aoc_supervisor/question_policy.py` | 1 | Module docstring says "Impact-ranked question selection"; actual role is compatibility layer | Rewrite docstring | L | Read |
| `aoc_supervisor/repo_paths.py` | 28–31 | `INTENT_FORGE_CSS_PATH` etc. point to `.html` files | Rename to `INTENT_FORGE_UI_FALLBACK` | L | `rg` for consumers |
| `aoc_supervisor/orchestrate_session.py` | 1–37 | AI behavioral directives ("AI agents — DO/DON'T") mixed into module docstring | Extract to `.instructions.md` | L | Read |

### 4.8 Naming & Convention

| File | Line(s) | Issue | Proposed Fix | Risk | Verification |
|---|---|---|---|---|---|
| `aoc-cli/commands/promote.py` | 40–43 | Hardcoded user-specific vault path (`Path.home() / "workspace" / "github.com" / "ghost-monday" / ...`) | Replace with env var or remove | L-M | Check if used by anyone else |
| `aoc-cli/helpers/merge.py` | ~485 | `del scope_paths` anti-pattern | `scope_paths` → `_scope_paths` | L | `pytest` |
| `aoc-cli/gravity.py` | — | Missing `__all__` | Add `__all__` with 3 public exports | L | `pytest` |
| `aoc-cli/blueprint.py` | 1082–1088 | Incomplete `__all__` — 3 missing public symbols | Add `handoff_gateway_mode_enabled`, `handoff_gateway_records`, `dependencies_from_work_units` | L | `pytest` |

---

## 5. Do-Not-Touch List

The following are explicitly excluded from any code-hygiene change. These are known-sensitive areas where a hygiene pass could introduce subtle regressions.

| Item | File / Area | Reason |
|---|---|---|
| **Psi tuple/order** | `aoc-cli/aoc_cli/resolution_v3/potential.py` | Tuple order encodes semantic meaning — changing it silently changes solver behavior |
| **`cyclic_debt()` formula** | `resolution_v3/` | Computes cyclic dependency debt in the constraint graph — any change affects resolution ordering |
| **B1 semantics** | `aoc-cli/aoc_cli/resolution_v3/rules.py` | FORBID wins and conflicting REQ is deactivated; code hygiene must not alter rule behavior |
| **B2 global fallback** | Resolution pipeline | Fallback behavior is intentionally broad; narrowing it changes error-handling surface |
| **Worklist urgent priority** | `resolution_v3/worklist/` | Priority ordering is architecturally significant |
| **STUCK vs ENGINE_FAULT** | Validation | State distinction is load-bearing in worker lifecycle |
| **Package/shim parity** | `aoc_cli.resolution_v3` and `loom_resolution_engine_v3.py` | Package exports and compatibility shim must expose the same public API and behavior |
| **`main` worktree** | `/home/ghostmonday/Desktop/Loom` | Not this worktree's responsibility — never touch |
| **`Loom-codex` worktree** | `/home/ghostmonday/Desktop/Loom-codex` | Not this worktree's responsibility — never touch |

---

## 6. Proposed Commit Sequence

Three commits for the first pass. Each is bisectable and independently verifiable.

### Commit 1: `cleanup: remove dead code (billing.py, question_policy.py, complexity.py, ...)`

**Files:**
- `aoc_supervisor/aoc_supervisor/billing.py` — remove `_locked_ledger`, `_read_ledger`, `_write_ledger` (lines 390–404)
- `aoc_supervisor/aoc_supervisor/question_policy.py` — remove `_answered_domains`, `rank_candidate_domains`, update `__all__`
- `aoc_supervisor/aoc_supervisor/complexity.py` — remove `compute_complexity_index`
- `aoc_supervisor/aoc_supervisor/workflow_evaluator.py` — remove `PKM_INTENT`
- `aoc_supervisor/aoc_supervisor/intent_blueprint_state.py` — remove `assert_status()`
- `aoc-cli/aoc_cli/state.py` — remove `schema_version` dict entry
- `aoc-cli/aoc_cli/commands/monitor.py` — remove dead `last_signature = None` assignments

**Verification:**
- [ ] `pytest --collect-only` — no collection errors
- [ ] `ruff check` on changed files
- [ ] `rg -rn "_locked_ledger\|_read_ledger\|_write_ledger" aoc_supervisor/` — only definitions removed
- [ ] `rg -rn "compute_complexity_index"` — only definition removed
- [ ] `rg -rn "rank_candidate_domains\|_answered_domains"` — only definition removed

### Commit 2: `cleanup: consolidate misplaced imports to module level`

**Files:**
- `aoc-cli/aoc_cli/commands/merge_grid.py` — 9× inline → 1 top-level import
- `aoc-cli/aoc_cli/commands/council.py` — `import json` to top-level
- `aoc-cli/aoc_cli/blueprint.py` — `from pathlib import Path` to top-level (2 occurences)
- `aoc-cli/aoc_cli/moat_authority.py` — end-of-file imports + `import hashlib` to top-level
- `aoc_supervisor/aoc_supervisor/teleology_artifact.py` — `import re` to top-level
- `aoc_supervisor/aoc_supervisor/adaptive_question_engine.py` — `import uuid` to top-level

**Verification:**
- [ ] `pytest --collect-only` — no collection errors
- [ ] `ruff check` on changed files
- [ ] `python -c "from aoc_cli.commands.merge_grid import ..."` — import resolves
- [ ] `python -c "from aoc_cli.moat_authority import ..."` — import resolves

### Commit 3: `cleanup: narrow overbroad exception handlers`

**Files:**
- `aoc-cli/aoc_cli/state.py` — lines 120, 379: `except Exception` → `except OSError`
- `aoc_supervisor/aoc_supervisor/reasoning_provider.py` — line 648: `except Exception` → `except (OSError, json.JSONDecodeError)`

**Verification:**
- [ ] `pytest` runs on relevant test modules
- [ ] `ruff check` on changed files
- [ ] Manual review that `OSError` covers the expected failures (file not found, permission denied, disk full)

---

## 7. Final Recommendation

**Ready for approval to implement Slice 1** (the 5-file slice in Section 3).

### Rationale

- All 5 changes in Slice 1 are **mechanical**: deletions or top-level import consolidations.
- Zero control-flow changes. Zero new dependencies. Zero risk of runtime regression.
- Each change is independently verifiable by `pytest --collect-only`, `ruff check`, and `rg` for residual references.
- The 22 lines of change eliminate **dead code that has zero callers** and **redundant imports that add no value**.

### What is NOT in Slice 1 (and why)

| Excluded | Reason |
|---|---|
| 7 orphan patch scripts (1,221 lines) | 7 files exceeds the 5-file slice limit; better as dedicated follow-up |
| Cross-file duplicate logic extraction | Changes API boundaries; needs dedicated refactoring pass |
| Type-hint gaps (~20 functions, 10+ files) | Exceeds slice scope; batch for pass 2 |
| `_process_is_running` bug fix | Touches production logic; needs unit test before change |
| `_assert_greenfield_blueprint` condition | Needs human review to confirm intent |
| Broad formatting sweeps | Excluded per hard rules |

### Next Action

Merge captain approval to implement the 5-file Slice 1 described in Section 3.
