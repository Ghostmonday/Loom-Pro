# Deep-Dive Appendix Drift Audit

**Source:** README.md appendix "Code Deep Dive — Hot Zones for Model Ingestion" (from line 440 onward)  
**Audited against:** `fable-work` branch working tree (2026-07-01)  
**Method:** For each quoted snippet, locate the claimed source file and compare function names, signatures, constants, and control flow. Exact formatting/comment drift is noted briefly; semantic drift (wrong names, missing logic, stale constants) is a finding.

---

## Snippet Audit Table

| Snippet (heading + claimed file) | Status | Evidence |
|---|---|---|
| **Wasserstein Computation** — `aoc-cli/aoc_cli/gravity.py` | MATCH | `_compute_ollivier_ricci_curvature` at `aoc-cli/aoc_cli/gravity.py:165-194`. Core loop (distance → distributions → cost matrix → `ot.emd2` → κ, shadow risk jump, `CURVATURE_HARD_FLOOR`) matches. Source adds diagnostic fields (`source`, `target`, `wasserstein_1`, etc.) not shown in README. |
| **Structural Gravity** — `aoc-cli/aoc_cli/gravity.py` | DRIFTED | `_compute_structural_gravity` at `aoc-cli/aoc_cli/gravity.py:129-162`. README uses undefined names `raw_capability` / `raw_side_effect` and literal `5.0` / `0.25`; source uses `raw_capability_level` / `raw_side_effect_score` with `SPARSE_HIGH_CAPABILITY_LEVEL` (5.0) and `LOW_CONTEXT_SIDE_EFFECT_SCORE` (0.25). Weighted-sum and floor logic otherwise match. |
| **Risk-Weighted Distributions** — `aoc-cli/aoc_cli/gravity.py` | MATCH | `_outgoing_distribution` at `aoc-cli/aoc_cli/gravity.py:197-204`, `_risk_weight` at `224-225`. Constants `CAPABILITY_RISK_ALPHA=0.70`, `SIDE_EFFECT_BETA=0.30` at lines 19-20. |
| **Atomic Block Welding** — `aoc-cli/aoc_cli/blueprint.py` | MATCH | `_UnionFind` at `aoc-cli/aoc_cli/blueprint.py:549-574`, `_atomic_blocks` at `628-643`. Union-Find and dark-edge welding logic match. Source additionally calls `dark_bridge_internal_log` on each weld (line 642); not shown in README. |
| **Convex Hull Over-Weld Prevention** — `aoc-cli/aoc_cli/blueprint.py` | MATCH | `_refine_grouped_blocks` at `aoc-cli/aoc_cli/blueprint.py:700-740`. SCC-aware chunking with `_convex_hull_welding_threshold()` (default 12) matches. README omits in-function `group_edges` construction (lines 710-714) but algorithm is the same. |
| **Cycle Weld Resolution** — `aoc-cli/aoc_cli/blueprint.py` | MATCH | `_resolve_work_units_and_dependencies` at `aoc-cli/aoc_cli/blueprint.py:789-809`. Fixpoint loop (dependencies → apply → cycle detect → `_weld_cycle_work_units`) matches. README snippet is truncated before `return _renumber_work_units(...)` but shown logic is correct. |
| **Engine Loop with Psi Descent Proof** — `aoc-cli/aoc_cli/resolution_v3/engine.py` | DRIFTED | `Engine.run` at `aoc-cli/aoc_cli/resolution_v3/engine.py:30-90`. README shows a simplified loop without try/except fault boundaries, uses bare `ENGINE_FAULT` and message `"Psi did not decrease"`. Source wraps psi init and each step in exception handlers, routes termination through `_check_termination` (lines 100-107) with `"Psi did not strictly decrease: …"`, and evaluates status with max-step budget handling. |
| **Psi Potential Function** — `aoc-cli/aoc_cli/resolution_v3/potential.py` | MATCH | `psi` at `potential.py:76-79`, `growth_debt` at `10-11`, `unresolved_debt` at `15-18`, `cyclic_debt` at `56-58`, `clash_pairs` at `61-73`. README abbreviates `clash_pairs` with `...` but semantics match the product-of-counts implementation. |
| **Rule Application (A1: Materialize Target)** — `aoc-cli/aoc_cli/resolution_v3/rules.py` | MATCH | `apply_a1` at `aoc-cli/aoc_cli/resolution_v3/rules.py:64-81`. Materialize latent node, domain aggregation, and `_requeue_target_closure` match. Log line in source includes full edge context (`required by {u} -[{label}]-> {v}`). |
| **B2: SCC Welding** — `aoc-cli/aoc_cli/resolution_v3/rules.py` | DRIFTED | `apply_b2` at `aoc-cli/aoc_cli/resolution_v3/rules.py:110-177`. README snippet has invalid `min(n.layer for n in cg.nodes[m] if n.layer)` and omits authority inheritance (`inherited_root`/`inherited_sink`, `external_in_req`/`external_out_req`) that source applies when creating the composite `Node` (lines 127-166). Source tracks `touched_indices` explicitly; README references it without defining it. |
| **Iterative Tarjan SCC** — `aoc-cli/aoc_cli/resolution_v3/scc.py` | DRIFTED | `tarjan_scc` at `aoc-cli/aoc_cli/resolution_v3/scc.py:15-72`. README inline version omits `push_frame` initialization (setting `index`, `lowlink`, `stack`, `on_stack`, incrementing `index_counter`) present in source lines 26-34, 57-58. Refactored into `_Frame` dataclass + `push_frame`/`emit_component` helpers; algorithm intent matches but README snippet would not run as written. |
| **Answer Processing with Analysis** — `aoc_supervisor/aoc_supervisor/intent_forge_service.py` | MATCH | `_apply_answer_to_state` at `intent_forge_service.py:83-103`. Call sequence (`_record_question_answer` → `_run_analysis_and_merge_claims` → `_update_domain_metrics_and_graph` → optional `_resolve_contradictions` → `_record_acceptance_decisions`) matches. |
| **Contradiction Detection & Merge** — `aoc_supervisor/aoc_supervisor/intent_forge_service.py` | DRIFTED | `_handle_contradictions` at `intent_forge_service.py:347-375`. README text template `Resolve contradiction: {description}` differs from source `Resolve contradiction {id}: {description}` (line 363). Source adds `save_on_conflict` parameter, `store.save`, and `_emit` on conflict (lines 354, 366-373). |
| **Strategy Selection** — `aoc_supervisor/aoc_supervisor/loom_blueprint_synthesizer.py` | MATCH | Dual-strategy loop at `loom_blueprint_synthesizer.py:276-285`. Atomic-weld vs handoff-partition candidate selection and `min(..., key=(dark_count, strategy))` match. Full `synthesize_blueprint` (lines 233-292) adds HANDED_OFF validation and post-update fields not in README excerpt. |
| **Topological Sort with Heap Tiebreaker** — `aoc_supervisor/aoc_supervisor/loom_map_generator.py` | DRIFTED | `_topological_order` at `loom_map_generator.py:164-193`. Heap-based Kahn's algorithm matches. README references undefined `cyclic` in `raise ValueError`; source defines it (line 191) and uses message `"capability dependency cycle detected"`. |
| **Keyword-to-Capability Mapping** — `aoc-cli/aoc_cli/moat.py` | DRIFTED | `CAPABILITY_KEYWORDS` at `moat.py:9-112`, `DANGEROUS_PHRASES` at `156-168`, `parse_prompt` at `196-220`. README shows only four capability buckets and four dangerous phrases; source has eight capability buckets plus `RECOMMENDED_PATHS`, `RISK_FLAGS`, `BASE_PROHIBITIONS`, and ten dangerous phrases. Core matching logic (`_contains_any`, normalization) is the same but documented maps are materially incomplete. |
| **GIV Schema & Enforcement** — `aoc-cli/aoc_cli/giv.py` | DRIFTED | `GIV` at `giv.py:58-102`, `HandoffTicket` at `29-54`. Field layout matches README except `HandoffTicket.timestamp: str` (line 39, default `_utc_now`) is absent from README. `__post_init__` validation is real in source (lines 77-102); README shows `...` placeholder only. |
| **Vocabulary Rewriting** — `aoc-cli/aoc_cli/helpers/stealth.py` | MATCH | `stealth_mode` at `stealth.py:16-18`, `sanitize_blocked_reason` at `25-44`. README uses `...` but described replacements ("shadow bridge" → "coupling review", "automatic rejection" → "integrity floor", etc.) match source `shadow_replacements` and `replacements` tuples. |
| **Runtime Pipeline (End-to-End Deterministic)** — `runtime_pipeline.py` (comment only; no `**File:**` header) | PATH-WRONG / DRIFTED | Actual path: `aoc-cli/aoc_cli/runtime_pipeline.py`. `run_pipeline` at lines 17-34. README return dict omits `pipeline_status` and `diagnostics`; uses pseudocode `hashlib.sha256(canonical_json)` instead of `_digest(normalized_input)` (lines 27, 174-176). Execution guard and unit derivation match conceptually. |

---

## Summary Counts

| Metric | Count |
|---|---|
| Snippets checked | 19 |
| MATCH | 9 |
| DRIFTED | 9 |
| PATH-WRONG | 1 |
| FABRICATED | 0 |

---

## Prioritized Fix List

1. **P0 — `apply_b2` and Tarjan snippets (resolution_v3):** Replace README excerpts with current `rules.py:110-177` and `scc.py:15-72` (or a runnable condensation that preserves `push_frame` index/stack initialization and composite `root_permitted`/`sink_permitted` inheritance). These are the highest-risk snippets for model ingestion: wrong variable names and missing init steps teach incorrect algorithms.

2. **P1 — `Engine.run` and `run_pipeline`:** Update engine-loop snippet to reflect try/except fault boundaries and `_check_termination` messaging; add full path `aoc-cli/aoc_cli/runtime_pipeline.py` and accurate return payload (`pipeline_status`, `diagnostics`, `_digest`).

3. **P1 — `gravity.py` structural gravity:** Rename `raw_capability`/`raw_side_effect` to `raw_capability_level`/`raw_side_effect_score` and reference named constants instead of magic numbers.

4. **P2 — `moat.py` keyword maps:** Expand README `CAPABILITY_KEYWORDS` / `DANGEROUS_PHRASES` to match source or add an explicit "subset shown" note pointing to `moat.py:9-168`.

5. **P2 — `giv.py` HandoffTicket:** Add `timestamp` field to the documented schema.

6. **P3 — Minor text drift:** `_handle_contradictions` prompt template (include contradiction `id`), `_topological_order` cycle error message, and optional logging call in `_atomic_blocks`.