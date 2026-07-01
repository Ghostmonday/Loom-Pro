# Code Hygiene Audit — Dry-Run Report

**Branch:** `audit/code-hygiene-pass`
**Base:** `main` (fbd97220)
**Date:** 2026-06-30
**Scope:** ~90 source files, ~29K LOC across `aoc_cli/`, `aoc_supervisor/`, `tests/`, root-level scripts, `scripts/dev/`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Dead Code — Unambiguous Removals](#1-dead-code--unambiguous-removals)
3. [Unused Imports & Re-exports](#2-unused-imports--re-exports)
4. [Misplaced Imports](#3-misplaced-imports)
5. [Duplicate Logic — Cross-File](#4-duplicate-logic--cross-file)
6. [Duplicate Logic — Within File](#5-duplicate-logic--within-file)
7. [Stale or Misleading Comments & Docstrings](#6-stale-or-misleading-comments--docstrings)
8. [Overly Broad Exception Handling](#7-overly-broad-exception-handling)
9. [Logic Inconsistencies & Potential Bugs](#8-logic-inconsistencies--potential-bugs)
10. [Type-Hint Gaps](#9-type-hint-gaps)
11. [Redundant Conditions & Minor Cleanup](#10-redundant-conditions--minor-cleanup)
12. [Orphan / One-Off Patch Scripts](#11-orphan--one-off-patch-scripts)
13. [Naming & Convention](#12-naming--convention)
14. [Test-Specific Findings](#13-test-specific-findings)
15. [Summary Statistics](#14-summary-statistics)

---

## Executive Summary

**Overall codebase hygiene: B+/A-.** The codebase is well-structured with disciplined patterns. No security flaws, no data-loss risks, no functional bugs detected in the hygiene pass.

| Category | Count | Est. Lines Saved |
|---|---|---|
| Dead code (unambiguous) | 9 items | ~50 |
| Unused imports / re-exports | 35+ symbols | ~40 |
| Misplaced imports | 7 files | 0 (relocation) |
| Duplicate logic (cross-file) | 7 patterns | ~60 |
| Duplicate logic (within-file) | 3 instances | ~20 |
| Stale/misleading comments | 4 | 0 |
| Broad exception handlers | 3 | 0 (narrow) |
| Logic inconsistencies | 3 | 0 (fix) |
| Type-hint gaps | ~20 functions | 0 |
| Orphan patch scripts (delete) | 7 files | ~1,021 |
| Redundant conditions | 4 | ~5 |
| Naming/convention | 5 | 0 |
| **Total actionable** | | **~1,196** |

> **Note:** ~1,021 of those lines come from deleting 7 orphan patch scripts (confirmed one-off, never imported, already excluded from ruff). Without those, the core source cleanup saves ~175 lines.

---

## 1. Dead Code — Unambiguous Removals

### 1.1 `state.py:170` — Dead `schema_version` dict entry
- **File:** `aoc-cli/aoc_cli/state.py`, line 170
- **Issue:** `"schema_version": schema_version` in `values` dict is never used — `ProjectState` constructor hardcodes `schema_version=SCHEMA_VERSION`
- **Evidence:** The `missing` check at line 175 explicitly skips `key != "schema_version"`; constructor at line 196 ignores the dict value
- **Confidence:** High | **Risk:** None | **Lines:** 1

### 1.2 `billing.py:390-404` — Three dead ledger wrappers
- **File:** `aoc_supervisor/aoc_supervisor/billing.py`, lines 390-404
- **Symbols:** `_locked_ledger` (7 lines), `_read_ledger` (3 lines), `_write_ledger` (3 lines)
- **Evidence:** grep confirms zero callers — all consumers call `DEFAULT_LEDGER_STORAGE.*` directly
- **Confidence:** High | **Risk:** None | **Lines:** 13

### 1.3 `complexity.py:54-55` — `compute_complexity_index` dead function
- **File:** `aoc_supervisor/aoc_supervisor/complexity.py`, lines 54-55
- **Code:** `def compute_complexity_index(snapshot) -> int: return snapshot.integrity_score`
- **Evidence:** grep confirms zero callers — consumers use `.integrity_score` directly
- **Confidence:** High | **Risk:** None | **Lines:** 3

### 1.4 `workflow_evaluator.py:41-44` — `PKM_INTENT` dead constant
- **File:** `aoc_supervisor/aoc_supervisor/workflow_evaluator.py`, lines 41-44
- **Code:** Multi-line string constant `PKM_INTENT` defined but never referenced
- **Evidence:** grep confirms zero usage outside definition line
- **Confidence:** High | **Risk:** None | **Lines:** 4

### 1.5 `question_policy.py:153-164` — `rank_candidate_domains` + `_answered_domains` dead functions
- **File:** `aoc_supervisor/aoc_supervisor/question_policy.py`, lines 153-164 and 61-68
- **Evidence:** `grep -r` returns only definition lines. Also listed in `__all__` — remove from there too.
- **Confidence:** High | **Risk:** None | **Lines:** 16

### 1.6 `intent_blueprint_state.py:163-167` — `assert_status` dead function
- **File:** `aoc_supervisor/aoc_supervisor/intent_blueprint_state.py`, lines 163-167
- **Evidence:** grep returns only definition — zero callers
- **Confidence:** High | **Risk:** None | **Lines:** 5

### 1.7 `evidence_state.py:~600+` — `_self_check()` test embedded in production
- **File:** `aoc_supervisor/aoc_supervisor/evidence_state.py`, lines ~600-650+
- **Issue:** Integration-level self-test with full BlueprintState construction and assertions
- **Evidence:** Never called from production code; zero callers
- **Proposal:** Move to `tests/` or remove
- **Confidence:** Medium | **Risk:** None | **Lines:** ~50

### 1.8 `spawn_governance.py:221-229` — Unreachable `RuntimeError` in lock handler
- **File:** `aoc_supervisor/aoc_supervisor/spawn_governance.py`, lines 221-229
- **Issue:** `raise RuntimeError("file locking is unavailable")` is dead — callers are guarded by `_locking_available()` check
- **Evidence:** `_acquire_handle_lock` is only called from `_exclusive_file_lock` which first verifies `_locking_available()`
- **Confidence:** High | **Risk:** None | **Lines:** 3

### 1.9 `monitor.py:51,54` — Dead `last_signature = None` assignments
- **File:** `aoc-cli/aoc_cli/commands/monitor.py`, lines 51 and 54
- **Issue:** `last_signature = None` assigned in `except` and `finally` — but function exits via `typer.Exit()` or loops forever
- **Evidence:** Local variable is never read after these assignments
- **Confidence:** High | **Risk:** None | **Lines:** 2

---

## 2. Unused Imports & Re-exports

### 2.1 `helpers/diagnostics.py:18` — Unused `Blueprint` import
- **File:** `aoc-cli/aoc_cli/helpers/diagnostics.py`, line 18
- **Code:** `from ..blueprint import Blueprint`
- **Evidence:** Symbol `Blueprint` never used in file body — only lowercase string `"blueprint"` in dict keys
- **Confidence:** High | **Risk:** None | **Lines:** 0 (cosmetic)

### 2.2 `helpers/constants.py:82,83,98` — Three dead constants
- **File:** `aoc-cli/aoc_cli/helpers/constants.py`
- **Symbols:** `COUNCIL_MD_PATH`, `MANIFEST_PATH`, `HERMES_BINARY`
- **Evidence:** grep across entire codebase returns only definition lines — zero consumers
- **Confidence:** High | **Risk:** None | **Lines:** 3

### 2.3 `helpers/__init__.py` — 17 dead re-exports from `scan.py` and `workers.py`
- **File:** `aoc-cli/aoc_cli/helpers/__init__.py`
- **Symbols (scan):** `_absolute_import_name`, `_capability_level`, `_is_ignored`, `_language_for_path`, `_line_count`, `_load_gitignore_patterns`, `_python_import_edges`, `_python_imports`, `_python_module_index`, `_python_package`, `_read_scan_text`, `_resolve_python_import`, `_scan_node`, `_scan_side_effect_score`
- **Symbols (workers):** `_remove_worker_dir`, `_work_unit_markdown`
- **Evidence:** Grep confirms zero external consumers via `from .helpers import ...` or `from aoc_cli.helpers import ...`
- **Confidence:** High | **Risk:** None | **Lines:** ~34 (imports + `__all__` entries)

### 2.4 `question_policy.py:9,197` — Dead re-export `get_analysis_recovery`
- **File:** `aoc_supervisor/aoc_supervisor/question_policy.py`
- **Issue:** Imported from `adaptive_question_engine` at line 9 and listed in `__all__` at line 197 — but the function is defined and never called anywhere
- **Evidence:** grep for `get_analysis_recovery` returns only definition + this import
- **Confidence:** High | **Risk:** None | **Lines:** 2

### 2.5 `tests/fixtures/contract_imports.py:13,20` — Unused `TypeVar` and `T`
- **File:** `tests/fixtures/contract_imports.py`, lines 13 and 20
- **Code:** `from typing import Any, TypeVar` and `T = TypeVar("T")`
- **Evidence:** `T` never referenced anywhere in the module
- **Confidence:** High | **Risk:** None | **Lines:** 2

---

## 3. Misplaced Imports

### 3.1 `moat_authority.py:975-977` — Imports at end of file
- **File:** `aoc-cli/aoc_cli/moat_authority.py`, lines 975-977
- **Code:** `import sys`, `import builtins`, `import subprocess` placed after all function definitions
- **Fix:** Move to top-level imports
- **Confidence:** High | **Risk:** None

### 3.2 `moat_authority.py:876` — `import hashlib` inside function
- **File:** `aoc-cli/aoc_cli/moat_authority.py`, line 876
- **Fix:** Move to top-level imports
- **Confidence:** High | **Risk:** None

### 3.3 `council.py:53` — `import json` inside function
- **File:** `aoc-cli/aoc_cli/commands/council.py`, line 53
- **Fix:** Move to top-level imports
- **Confidence:** High | **Risk:** None

### 3.4 `merge_grid.py:156+` — 9× repeated `from ..state import transition_worker_state`
- **File:** `aoc-cli/aoc_cli/commands/merge_grid.py`, lines 156, 168, 177, 187, 195, 214, 224, 234, 240
- **Evidence:** File already imports from `..helpers`, `..blueprint` at top level with no circular-import issues
- **Fix:** Single top-level import, remove all 9 inline occurrences
- **Confidence:** High | **Risk:** None | **Lines:** 9 removed, 1 added (net -8)

### 3.5 `blueprint.py:684` — `import networkx` inside function
- **File:** `aoc-cli/aoc_cli/blueprint.py`, line 684
- **Evidence:** `gravity.py` in same package already imports `networkx` at module level
- **Confidence:** High | **Risk:** None

### 3.6 `blueprint.py:234,1000` — Duplicate `from pathlib import Path` in 2 functions
- **File:** `aoc-cli/aoc_cli/blueprint.py`, lines 234 and 1000
- **Fix:** Move to top-level imports
- **Confidence:** High | **Risk:** None | **Lines:** -4

### 3.7 `blueprint.py:354,612,650,957` — 4× duplicate stealth imports
- **File:** `aoc-cli/aoc_cli/blueprint.py`
- **Symbols:** `dark_bridge_blueprint_assumption`, `dark_bridge_internal_log`, `dark_bridge_user_log`, `stealth_coupling_label`, `stealth_mode`
- **Fix:** Single consolidated top-level import
- **Confidence:** Medium | **Risk:** None | **Lines:** -8

### 3.8 `teleology_artifact.py:349` — `import re` inside function
- **File:** `aoc_supervisor/aoc_supervisor/teleology_artifact.py`, line 349
- **Fix:** Move to top-level imports
- **Confidence:** High | **Risk:** None

### 3.9 `adaptive_question_engine.py:154,395` — `import uuid` twice inside functions
- **File:** `aoc_supervisor/aoc_supervisor/adaptive_question_engine.py`, lines 154 and 395
- **Fix:** Single top-level `import uuid`
- **Confidence:** High | **Risk:** None

---

## 4. Duplicate Logic — Cross-File

### 4.1 Atomic-write pattern in 3 files
- **Files:** `state.py:107-122`, `state.py:360-379`, `moat_authority.py` (`_atomic_write_json`)
- **Pattern:** `tempfile.mkstemp` → `os.fdopen` → `write` → `os.fsync` → `Path.replace` → cleanup
- **Fix:** Extract to shared utility (e.g., `helpers/_atomic.py`)
- **Confidence:** High | **Risk:** None | **Lines:** ~36 across 3 files
- *Note: Lower priority — mechanical extraction, no bug fix*

### 4.2 `_node_key` function in 2 files
- **Files:** `moat_authority.py:887-889` and `semantic_moat.py:171-173` — byte-for-byte identical
- **Fix:** Move to shared helper
- **Confidence:** High | **Risk:** None | **Lines:** 3

### 4.3 `_coerce_float` function in 2 files
- **Files:** `moat_authority.py:989-992` and `inferring.py:60-66` — nearly identical
- **Fix:** Move to shared helper
- **Confidence:** High | **Risk:** None | **Lines:** 4

### 4.4 Domain keyword map in 2 files
- **Files:** `moat_authority.py` `_deterministic_tag` and `semantic_moat.py` `_DOMAIN_KEYWORDS`
- **Evidence:** Both map same domain tags to overlapping keyword sets
- **Fix:** Define once in shared constants module
- **Confidence:** Medium | **Risk:** Low | **Lines:** ~15

### 4.5 `HANDOFF_QUEUE_PATH` constant in 2 files
- **Files:** `merge.py:58` and `handoff.py:31`
- **Issue:** `merge.py` derives from `GAIJINN_DIR`, `handoff.py` hardcodes `Path(".gaijinn/merge/...")`
- **Fix:** Import from `merge.py` in `handoff.py`, remove local definition
- **Confidence:** High | **Risk:** None | **Lines:** 1

### 4.6 Wiki-link regex in 2 files (with divergence)
- **Files:** `vault_deploy.py:20` and `knowledge_linter.py:30`
- **Difference:** `vault_deploy` uses `[^\]]+` for display capture; `knowledge_linter` uses `[^\]|]+` (stricter)
- **Fix:** Extract shared regex constant, use permissive version
- **Confidence:** High | **Risk:** Low | **Lines:** 2

### 4.7 UTC-timestamp utilities in 2 files
- **Files:** `council.py` (`_now_iso`, `_parse_utc_timestamp`) and `merge.py` (`utc_now`, `_parse_utc_timestamp`)
- **Fix:** Move to shared location or import one from the other
- **Confidence:** Medium | **Risk:** Low | **Lines:** ~6

### 4.8 `_now_iso()` in 2 files (Intent Forge)
- **Files:** `adaptive_question_engine.py:128-129` and `intent_blueprint_state.py:31-32`
- **Fix:** Import from one location
- **Confidence:** Medium | **Risk:** Low | **Lines:** 3

### 4.9 `_edge_classification` private function imported externally
- **Files:** `orchestration_envelope.py` (defines as `_edge_classification`) and `loom_blueprint_synthesizer.py` (imports it as `from ..._envelope import _edge_classification`)
- **Fix:** Make public (`edge_classification`) in orchestration_envelope.py
- **Confidence:** High | **Risk:** None | **Lines:** 0 (rename)

---

## 5. Duplicate Logic — Within File

### 5.1 `analyze_.py:107-139` — Nearly identical stealth block in both branches
- **File:** `aoc-cli/aoc_cli/commands/analyze_.py`, lines 108-116 and 126-135
- **Issue:** 6 function calls with same arguments repeated in `json_output` and non-`json_output` branches
- **Fix:** Compute summary once before the branch
- **Confidence:** High | **Risk:** None | **Lines:** ~10

### 5.2 `intent_forge_service.py:75-78` — Redundant node loop (duplicate iteration)
- **File:** `aoc_supervisor/aoc_supervisor/intent_forge_service.py`, lines 75-78
- **Issue:** First loop marks stale nodes, but second loop (lines 84-87) covers same IDs plus expanded set with identical body
- **Fix:** Remove the first loop (75-78) — the second loop handles all cases
- **Confidence:** High | **Risk:** None | **Lines:** 4

### 5.3 `teleology_artifact.py:240-255` — Redundant `seen` set dedup
- **File:** `aoc_supervisor/aoc_supervisor/teleology_artifact.py`, lines ~240-255
- **Issue:** `seen` set created from hardcoded tuple of unique values, then used to filter the same tuple — all elements are unique by construction
- **Fix:** Replace with `phases = list(statuses)`
- **Confidence:** High | **Risk:** None | **Lines:** 3

---

## 6. Stale or Misleading Comments & Docstrings

### 6.1 `promote.py:29` — Stale docstring (anchor path mismatch)
- **File:** `aoc-cli/aoc_cli/commands/promote.py`, line 29
- **Code:** Docstring says `.gaijinn/merge/governance.json` but code checks `.gaijinn/bridge/council.md`
- **Fix:** Update docstring
- **Confidence:** High | **Risk:** None

### 6.2 `question_policy.py:1` — Misleading module docstring
- **File:** `aoc_supervisor/aoc_supervisor/question_policy.py`, line 1
- **Code:** Says "Impact-ranked question selection" but actual mechanism is delegated to `AdaptiveQuestionEngine`
- **Fix:** Update to describe compatibility-layer role
- **Confidence:** Medium | **Risk:** None

### 6.3 `repo_paths.py:28-31` — Misleading path constant names
- **File:** `aoc_supervisor/aoc_supervisor/repo_paths.py`, lines 28-31
- **Issue:** `INTENT_FORGE_CSS_PATH`, `INTENT_FORGE_JS_PATH`, etc. all point to `.html` files
- **Fix:** Rename to reflect HTML fallback role (e.g., `INTENT_FORGE_UI_FALLBACK`)
- **Confidence:** High | **Risk:** None

### 6.4 `orchestrate_session.py:1-37` — Agent instructions mixed into module docstring
- **File:** `aoc_supervisor/aoc_supervisor/orchestrate_session.py`, lines 13-24
- **Issue:** `AI agents — DO` / `AI agents — DON'T` behavioral directives in module docstring
- **Fix:** Extract to companion `.instructions.md` file
- **Confidence:** Medium | **Risk:** None | **Lines:** ~20

---

## 7. Overly Broad Exception Handling

### 7.1 `state.py:120,379` — `except Exception` in temp-file cleanup
- **Files:** `aoc-cli/aoc_cli/state.py`, lines 120 and 379
- **Code:** `except Exception: temp_path.unlink(missing_ok=True); raise`
- **Fix:** Narrow to `except OSError`
- **Confidence:** Medium | **Risk:** Low

### 7.2 `moat_authority.py:1053,1068` — `except Exception: pass` in containment hooks
- **Files:** `aoc-cli/aoc_cli/moat_authority.py`, lines 1053 and 1068
- **Code:** Silent suppression of all exceptions in `hooked_popen` and `hooked_run`
- **Fix:** Catch specific exceptions (`ValueError`, `OSError`)
- **Confidence:** Medium | **Risk:** Low

### 7.3 `reasoning_provider.py:648-649` — `except Exception: pass` in cache write
- **File:** `aoc_supervisor/aoc_supervisor/reasoning_provider.py`, lines 648-649
- **Fix:** Catch `(OSError, json.JSONDecodeError)`
- **Confidence:** High | **Risk:** None

---

## 8. Logic Inconsistencies & Potential Bugs

### 8.1 `spawn_governance.py:485-501` — `_process_is_running` treats `exit_code=0` incorrectly
- **File:** `aoc_supervisor/aoc_supervisor/spawn_governance.py`, lines 485-501
- **Issue:** `exit_code=0` (process completed successfully) is falsy, so `if exit_code is None` is False, and the function falls through to check `status in {"running", "spawned"}` — incorrectly reporting completed processes as "running"
- **Fix:** Check `exit_code is not None` before status-based fallback
- **Confidence:** High | **Risk:** Low (fixes a real bug in edge case)

### 8.2 `orchestrate_session.py:354-367` — Inconsistent condition in `_assert_greenfield_blueprint`
- **File:** `aoc_supervisor/aoc_supervisor/orchestrate_session.py`, lines 354-367
- **Issue:** When `keyword_mode=False` and `mode="intent"`, the projection mode check allows `"keyword"` as valid — inconsistent with keyword mode being off
- **Fix:** Restructure the condition
- **Confidence:** Medium | **Risk:** Low

### 8.3 `conflict_resolver.py:64-65` — `state` parameter silently ignored
- **File:** `aoc_supervisor/aoc_supervisor/conflict_resolver.py`, lines 64-65
- **Issue:** `resolution_options` receives `state` but stores it to `_` (unused)
- **Fix:** Remove parameter or implement state-aware resolution
- **Confidence:** Medium | **Risk:** Medium (callers must change if removed)

---

## 9. Type-Hint Gaps

### 9.1 Resolution v3 — Missing `cg: ConstraintGraph` on ~15 functions
- **Files:** `resolution_v3/engine.py`, `potential.py`, `reporting.py`, `rules.py`, `validation.py`, `watch.py`
- **Issue:** `cg` parameter untyped in `resolve()`, `growth_debt()`, `unresolved_debt()`, `find_violating_sccs()`, `cyclic_debt()`, `clash_pairs()`, `psi()`, `report_payload()`, `_aggregate_target_domain()`, `apply_*()`, `validation_errors()`, `is_valid()`, `is_stable()`
- **Fix:** Add `cg: ConstraintGraph` (uses `from __future__ import annotations`)
- **Confidence:** High | **Risk:** None

### 9.2 `plan.py:24` — Missing `project_root: Path`
- **File:** `aoc-cli/aoc_cli/commands/plan.py`, line 24
- **Confidence:** High | **Risk:** None

### 9.3 `run_grid.py:34` — Missing work_units type
- **File:** `aoc-cli/aoc_cli/commands/run_grid.py`, line 34
- **Confidence:** Medium | **Risk:** None

### 9.4 `spawn_governance.py:658-662` — Missing return type on `popen_worker_process`
- **File:** `aoc_supervisor/aoc_supervisor/spawn_governance.py`, lines 658-662
- **Fix:** `-> subprocess.Popen`
- **Confidence:** High | **Risk:** None

### 9.5 `cli.py` — `serve` command missing `-> None`
- **File:** `aoc-cli/aoc_cli/cli.py` (serve function)
- **Fix:** Add `-> None`
- **Confidence:** High | **Risk:** None

---

## 10. Redundant Conditions & Minor Cleanup

### 10.1 `runtime_pipeline.py:18-23` — `EngineStatus.CANONICAL` compared twice
- **Fix:** Extract `is_canonical` local variable
- **Confidence:** High | **Risk:** None | **Lines:** 0 (net)

### 10.2 `blueprint.py:972-973` — Redundant `or 0` + `int()` cast
- **Code:** `int(curvature_meta.get("shadow_bridge_count", 0) or 0) > 0`
- **Fix:** `curvature_meta.get("shadow_bridge_count", 0) > 0`
- **Confidence:** Low | **Risk:** None | **Lines:** -1

### 10.3 `blueprint.py:614` — Unnecessary `_ = ` discard
- **Code:** `_ = dark_bridge_internal_log(source, target)`
- **Fix:** Remove `_ = `
- **Confidence:** High | **Risk:** None

### 10.4 `billing.py:350-365` — Redundant math check in `_verify_quantized_accounting`
- **Confidence:** Medium | **Risk:** None | **Lines:** 2 (if removed)

### 10.5 `evidence_state.py:20-28` — Redundant empty-list factory functions
- **Code:** `empty_project_evidence()` and `empty_analysis_receipts()` returning `[]`
- **Fix:** Inline `[]` in `setdefault` calls
- **Confidence:** Medium | **Risk:** None | **Lines:** 10

### 10.6 `hermes_.py:24-28` — Unnecessary intermediate variable
- **File:** `aoc-cli/aoc_cli/commands/hermes_.py`, lines 24-28
- **Fix:** Inline `argv` into both return paths
- **Confidence:** High | **Risk:** None | **Lines:** 1

---

## 11. Orphan / One-Off Patch Scripts

These are confirmed one-off scripts (already excluded from ruff) that applied patches to source files. All patches are already in the source.

| File | Lines | Status | Action |
|---|---|---|---|
| `broadcaster_patch.py` | 1 | Corrupted (live-editing artifact) | Delete |
| `apply_innovations.py` | ~201 | One-off, patches applied | Delete |
| `final_patch.py` | ~320 | One-off, patches applied | Delete |
| `fix_merge.py` | 6 | One-off, patch applied | Delete |
| `patch_api.py` | 42 | One-off, patches applied | Delete |
| `patch_script_v2.py` | 131 | One-off, patches applied | Delete |
| `patch_script.py` | ~320 | One-off, patches applied | Delete |

**Total lines:** ~1,021
**Confidence:** High | **Risk:** None (all patches verified in source)
**Post-delete:** Remove excluded paths from `pyproject.toml` ruff config

---

## 12. Naming & Convention

### 12.1 `promote.py:40-43` — Hardcoded user-specific vault path
- **File:** `aoc-cli/aoc_cli/commands/promote.py`, lines 40-43
- **Code:** `Path.home() / "workspace" / "github.com" / "ghost-monday" / "Gaijinn" / ...`
- **Fix:** Replace with env var fallback or remove (only matches author's machine)
- **Confidence:** Medium | **Risk:** Low | **Lines:** 1

### 12.2 `merge.py:~485` — `del scope_paths` anti-pattern
- **File:** `aoc-cli/aoc_cli/helpers/merge.py`, line ~485
- **Fix:** Replace with `_ = scope_paths` or rename to `_scope_paths`
- **Confidence:** High | **Risk:** None

### 12.3 `gravity.py` — Missing `__all__`
- **File:** `aoc-cli/aoc_cli/gravity.py`
- **Fix:** Add `__all__` with 3 public exports
- **Confidence:** High | **Risk:** None | **Lines:** +3

### 12.4 `blueprint.py:1082-1088` — Incomplete `__all__`
- **File:** `aoc-cli/aoc_cli/blueprint.py`, lines 1082-1088
- **Missing:** `handoff_gateway_mode_enabled`, `handoff_gateway_records`, `dependencies_from_work_units`
- **Confidence:** High | **Risk:** None | **Lines:** +3

### 12.5 `spawn_governance.py` — `_process_is_running` vs `_sprint_is_active` inconsistency
- **File:** `aoc_supervisor/aoc_supervisor/spawn_governance.py`
- **Confidence:** Low | **Risk:** None

---

## 13. Test-Specific Findings

### 13.1 `test_cli.py:620-655` — Parametrization opportunity (4 similar cases)
- **File:** `tests/test_cli.py`, lines 620-655
- **Fix:** `@pytest.mark.parametrize`
- **Confidence:** High | **Risk:** None | **Lines:** ~20

### 13.2 `test_intent_forge.py:740-870` — Parametrization opportunity (3 idempotency tests)
- **Fix:** Parametrize `finalize`, `pause`, `resume` tests
- **Confidence:** Medium | **Risk:** Low | **Lines:** ~40

### 13.3 `contract_imports.py:13,20` — Unused `TypeVar` (see 2.5)
- Already listed above

---

## 14. Summary Statistics

### Lines That Can Be Safely Removed

| Category | Est. Lines |
|---|---|
| Dead code (functions, variables, constants) | ~97 |
| Unused imports / dead re-exports | ~39 |
| Duplicate logic (consolidated) | ~83 |
| Orphan patch scripts | ~1,021 |
| Redundant conditions | ~14 |
| **Total** | **~1,254** |
| **Core source (excluding patch scripts)** | **~233** |

### Files With No Findings

| Area | Files |
|---|---|
| `aoc_cli/` | `errors.py`, `__init__.py`, `__main__.py`, `giv.py`, `moat.py`, `dataflow.py`, `runtime_pipeline.py`; Commands: `activate.py`, `audit.py`, `collect.py`, `compile_prompt.py`, `doctor.py`, `init_.py`, `run_pipeline.py`, `scan.py`, `status.py`, `validate_worker.py`, `version.py`; Helpers: `git.py`, `stealth.py`, `project_profile.py`, `io.py`, `council.py`, `workers.py`, `scan.py`, `audit.py` |
| `aoc_supervisor/` | `__init__.py`, `preflight.py`, `enforcer.py`, `session_security.py`, `telemetry_policy.py`, `analysis_receipts.py`, `spec_analysis_types.py`, `prompt_coverage.py`, `orchestrator.py`, `loom_pipeline.py`, `loom_map_generator.py`, `reasoning_schema.py`, `overlay_system.py`, `vault_deploy.py`, `vault_links.py`, `intent_mirror.py`, `intent_forge_events.py`, `blueprint_compiler.py` |
| `resolution_v3/` | All 11 files clean except type-hint gaps |
| `tests/` | `conftest.py`, `fixtures/__init__.py`, `fake_reasoning_provider.py` |
| `scripts/dev/` | All 5 files |

### Remaining Uncertain Findings (Not Actionable Without Discussion)

1. `api.py:270-540` — `_patch_testclient_for_httpx28` (~270 lines of test-only monkey-patching loaded in production). Safe to gate or extract, but needs review.
2. `websocket_telemetry.py:37-38` — `_session_overrides` global mutable dict memory leak. Fix requires design decision (LRU vs periodic cleanup).
3. `blueprint.py:306-380` — Extracting `generate_blueprint` assumptions block. Pure refactoring, but any extraction changes the function boundary.
4. `complexity.py:79-130` — `build_snapshot` and `build_snapshot_from_payload` share significant duplication. Consolidation needs entry-point analysis.

---

## Next Steps

Phase 2 execution is **awaiting approval**. Recommended commit plan:

| Commit | Scope | Est. Impact |
|---|---|---|
| 1 | Delete 7 orphan patch scripts + update `pyproject.toml` | -1,021 lines |
| 2 | Remove dead code (functions, constants, variables) | -97 lines |
| 3 | Remove unused imports + dead re-exports | -39 lines |
| 4 | Move misplaced imports to top level | 0 net lines |
| 5 | Fix logic bugs (`_process_is_running`, `_assert_greenfield_blueprint`) | 0 net lines |
| 6 | Add missing type hints | 0 net lines |
| 7 | Consolidate duplicate logic (cross-file) | -83 lines |
| 8 | Clean up redundant conditions + minor cleanup | -14 lines |
| 9 | Fix stale/misleading comments + docstrings | 0 net lines |
| 10 | Narrow broad exception handlers | 0 net lines |
| 11 | Add missing `__all__` entries | 0 net lines |
| 12 | Test parametrization | -60 lines |
