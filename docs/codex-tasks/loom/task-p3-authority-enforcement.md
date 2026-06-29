# P3-Authority-Enforcement

**From:** Director (loom-project-manager) — code review of P3 commit `334a203`  
**Critique:** CRIT-D3 not closeable: the authority boundary is still bypassable and not wired into real worker-assignment path  
**Branch:** `p3-authority-enforcement` (from `main@334a203`)  
**Parent:** `334a203` (P3 on main)

---

## Goal

Replace the current bypassable `verify_semantic_boundary()` + separate `compose_allowed_paths()` with a single `evaluate_boundary()` function that produces a sealed `VerifiedBoundaryDecision`. That decision must gate actual worker assignment in `run_grid`. A hostile or malformed LLM proposal must be unreachable to `allowed_paths` even when a caller deliberately tries to bypass verification.

This is **not** a library exercise. Production wiring is deliberately included.

---

## Correction 1 — RawSemanticProposal sidecar

**Do not attach raw LLM output to the canonical graph as metadata.**

Create `RawSemanticProposal`:

```python
@dataclass(frozen=True)
class RawSemanticProposal:
    """Untrusted LLM output preserved as observable evidence."""
    source: str              # "llm" | "deterministic"
    raw_payload: str | None  # the original LLM response text (None for determ.)
    items: list[dict]        # each parsed item, preserving ALL fields even malformed ones
    malformed_count: int     # count of items that failed basic parse
    unknown_node_count: int  # count referencing node IDs absent from canonical graph
    dropped_keys: list[str]  # keys present in raw payload but not in expected schema
```

The `RawSemanticProposal` lives in `moat_authority.py` and is produced by:

```python
def ingest_raw_semantic_proposal(
    llm_response_body: Any,
    canonical_graph: Sequence[Mapping[str, Any]],
) -> RawSemanticProposal:
```

**Key behavior change:** The old `_parse_llm_tags` silently discarded unknowns and rewrote unknown tags to "general". The new `ingest_raw_semantic_proposal` preserves **everything** — malformed entries, unknown node IDs, unknown tags, missing fields — as observable evidence in `RawSemanticProposal.items`. The verifier checks these items; no pre-filtering happens.

---

## Correction 2 — VerifiedBoundaryDecision (internal sealed type)

**Do not let ordinary code construct an authorization-ready decision.**

```python
@dataclass(frozen=True)
class VerifiedBoundaryDecision:
    """The sole authority gate. Constructed ONLY by `evaluate_boundary()`."""
    session_id: str
    authorized_work_units: tuple[AuthorizedWorkUnit, ...]
    blocked: bool
    block_reasons: tuple[str, ...]
    violations: tuple[ViolationRecord, ...]
    raw_proposal: RawSemanticProposal
    policy_version: str
    deterministic_evidence: dict
    overrides_applied: tuple[OverrideRecord, ...]
    created_at: str

@dataclass(frozen=True)
class AuthorizedWorkUnit:
    work_unit_id: str
    node_key: str
    static_max_paths: tuple[str, ...]
    authorized_paths: tuple[str, ...]
    tag_applied: str | None
    verification_result: str  # "passed" | "blocked" | "warning"
    violations: tuple[ViolationRecord, ...]
```

The authorization consumer (`refuse_worker_assignment`, `_worker_giv`) accepts **only** `VerifiedBoundaryDecision`. No function accepts raw `ProvisionalTag` objects or manually assembled mappings for scope decisions.

The old `ProvisionalTag` + `ViolationRecord` dataclasses remain as supporting types but are **not** exported as public API for authorization purposes.

---

## Correction 3 — Single evaluate_boundary(), no separate composer

Replace the current `verify_semantic_boundary()` + `compose_allowed_paths()` split with:

```python
def evaluate_boundary(
    *,
    raw_proposals: RawSemanticProposal,
    canonical_graph: Sequence[Mapping[str, Any]],
    static_scopes_by_node: dict[str, StaticNodeScope],
    session_id: str,
    curvature_floor: float = -0.30,
    dark_bridge_min_confidence: float = 0.95,
    min_confidence: float = 0.60,
    overrides: Sequence[OverrideRecord] | None = None,
) -> VerifiedBoundaryDecision:
```

This single function:
1. Runs all verification checks against raw proposals (not pre-filtered tags)
2. Produces `VerifiedBoundaryDecision` with `blocked` automatically derived
3. Computes final per-work-unit scopes inside the decision
4. Applies any supplied overrides before computing the decision
5. Persists the full decision atomically to `.gaijinn/authority/`

There is **no** independently callable `compose_allowed_paths()`. The old one in both `moat.py` and `moat_authority.py` is removed. Final scopes live inside `AuthorizedWorkUnit.authorized_paths` on the decision.

---

## Correction 4 — Blocked is derived, not caller-settable

`VerifiedBoundaryDecision.blocked` is `True` when ANY of:

- At least one violation with severity `"blocked"` exists AND has not been resolved by an override
- Any unresolved `dataflow_puncture` warnings exist on nodes (punctures elevate to blocked unless overridden)
- `raw_proposal.malformed_count > 0` (malformed LLM output always blocks)

Callers do not set `blocked`. It is computed from the violations, raw proposal health, and overrides.

---

## Correction 5 — Per-work-unit scope composition

For each node:

```
node_max_scope  = static_node_scope          (from file-system analysis of the node's source_file)
tag_restriction  = TAG_RESTRICTIONS[tag]      (directory prefixes this tag permits)
verified_scope   = node_max_scope ∩ tag_restriction

If tag_restriction is empty (e.g. "general"):
    verified_scope = node_max_scope           (no narrowing)
```

For each work unit:

```
work_unit_max_scope  = ⋃ static_node_scope for all nodes in the unit
work_unit_scope      = ⋃ verified_scope for all verified nodes in the unit

assert work_unit_scope ⊆ work_unit_max_scope   (narrow-only invariant)
```

The `AuthorizedWorkUnit.authorized_paths` holds `work_unit_scope`. The `AuthorizedWorkUnit.static_max_paths` holds `work_unit_max_scope` for comparison.

**Implementation details:**

- `TAG_RESTRICTIONS` values are path prefixes, compared via `path.startswith(prefix)`. The old exact-string equality (`"aoc-cli/aoc_cli/" != "aoc-cli/aoc_cli/helpers"`) is wrong. Use `PurePosixPath` for normalized prefix matching.
- `static_node_scope` comes from the `source_file` field on each canonical graph node. The max scope is the set of directory ancestors up to the repo root. (Simplified for v1: the parent directory of `source_file`; more precise static analysis is a future improvement.)
- When a node lacks `source_file`, it gets the union scope of its work unit's peer nodes that do have `source_file`.

**Remove the old `compose_allowed_paths()` from both `moat.py` and `moat_authority.py`.** Replace with the per-work-unit logic inside `evaluate_boundary()`.

---

## Correction 6 — Real mutation reachability evidence

**Do not assume the existing scanner provides `has_mutation_reachability`.** Investigate and categorize:

### Direct mutation evidence
The existing `analyze_handler_dataflow()` in `dataflow.py` already produces `mutation_sinks` via AST analysis. A node with non-empty `mutation_sinks` in its `dataflow` field has **direct mutation evidence**.

### Transitively reachable mutation
A node's `side_effects` list (from `intent_scan.py`), combined with `http_method == "DELETE"` or intent keywords containing destructive stems, constitutes **transitive mutation evidence**.

### Unknown/unresolved reachability
A node with no `source_file` (e.g., synthesized or external nodes) and no `mutation_sinks` and no `side_effects` has **unknown reachability**.

### Enforcement rule
- `unknown` reachability with a tag claiming non-mutation safety (anything except `"destructive"`) → **blocked violation**
- `direct` or `transitive` reachability with a tag that has `can_widen_allowed_paths=False` and the tag is not `"destructive"` → **blocked violation** (misclassification)
- `direct` or `transitive` with tag `"destructive"` → allowed, with appropriate restriction narrowing

Replace the old `_has_destructive_keywords()` with this three-category function:

```python
def classify_mutation_reachability(node: Mapping[str, Any]) -> str:
    """Returns 'direct' | 'transitive' | 'none' | 'unknown'."""
```

---

## Correction 7 — Override binds to a specific violation

Remove the process-global `HUMAN_OVERRIDE_TOKEN`. Replace with:

```python
@dataclass(frozen=True)
class OverrideRecord:
    override_id: str
    session_id: str
    violation_id: str       # references specific ViolationRecord
    node_key: str
    reviewer_identity: str  # "amir" | "ops-director" | etc.
    expiry: str             # ISO-8601
    reason: str
    created_at: str
```

Override:
- Binds to `session_id + node_key + violation_id` — cannot authorize a different run
- Generates a new audit event (does not rewrite the original LLM proposal)
- Expires — after `expiry`, the override is void
- Stored in `.gaijinn/authority/overrides.jsonl`
- Applied in `evaluate_boundary()` when overrides are passed and match

---

## Correction 8 — Atomic decision audit

Replace the old violation-only `write_audit_entry()`. Write one record per `evaluate_boundary()` call:

```python
@dataclass
class DecisionAuditRecord:
    session_id: str
    decision: VerifiedBoundaryDecision    # full decision, including raw proposal
    policy_version: str
    created_at: str
    override_provenance: list[OverrideRecord]

def persist_decision(decision: VerifiedBoundaryDecision, path: Path | None = None) -> Path:
    """Write the full decision to `.gaijinn/authority/YYYYMMDDTHHMMSSZ-decision.json`.

    Records: raw proposal, deterministic evidence, verification outcome,
    final scopes, policy version, override provenance.
    """
```

**Remove the old `write_audit_entry()`. There is only one audit path.**

---

## Production wiring

### `analyze_cmd()` — after `compile_inferred_json()`

```python
# After compile_inferred_json(...) completes
from aoc_cli.moat_authority import ingest_raw_semantic_proposal, evaluate_boundary

# Build RawSemanticProposal from LLM response (or empty for determ. only)
raw = ingest_raw_semantic_proposal(
    llm_response_body=_load_llm_response(),  # or None for deterministic
    canonical_graph=interaction_graph,
)

# Build static scopes from interaction_graph nodes
static_scopes = _build_static_scopes(interaction_graph)

# Evaluate
decision = evaluate_boundary(
    raw_proposals=raw,
    canonical_graph=interaction_graph,
    static_scopes_by_node=static_scopes,
    session_id=metrics.get("session_id", ""),
)

# Persist decision sidecar
persist_decision(decision, path=state.authority_path / "latest-decision.json")
```

### `run_grid_cmd()` — before worker assignment

```python
from aoc_cli.moat_authority import load_latest_decision, refuse_worker_assignment

decision = load_latest_decision()
if decision.blocked:
    refuse_worker_assignment(decision)  # raises SafetyError with details
    # never reaches worker creation
```

Old `run_grid` code path after the check is unchanged — the decision's authorized scopes are not yet consumed by `_worker_giv()` in this sprint (that's P3-Production-Wiring). **But** the gate must exist and block: if `decision.blocked`, `run_grid` must refuse to create workers.

---

## Tests

### Acceptance test (new)

```python
def test_hostile_llm_cannot_reach_worker_assignment(monkeypatch, tmp_path):
    """A hostile or malformed semantic proposal cannot reach worker assignment,
    even when a caller deliberately tries to bypass verification."""

    # Arrange: create a canonical graph + a hostile RawSemanticProposal
    #   (node injection, unknown tags, missing confidence)
    #   + a direct call to evaluate_boundary()
    #   + a caller who bypasses evaluation and tries to build
    #     a `VerifiedBoundaryDecision` manually

    # Act:
    decision = evaluate_boundary(
        raw_proposals=hostile_proposal,
        canonical_graph=graph,
        static_scopes_by_node=scopes,
        session_id="test-hostile",
    )

    # Assert:
    assert decision.blocked is True
    assert len(decision.violations) > 0

    # Attempted bypass: manually constructing VerifiedBoundaryDecision should fail
    # Verify the old compose_allowed_paths is removed
    with pytest.raises((AttributeError, ImportError)):
        from aoc_cli.moat_authority import compose_allowed_paths
```

### Existing tests preserved

Keep all 25 tests from P3. Update the ones that reference removed functions to use the new `evaluate_boundary()` API.

### New tests

1. `test_raw_proposal_preserves_malformed_items` — malformed LLM response yields `malformed_count > 0`, items preserved
2. `test_raw_proposal_preserves_unknown_nodes` — node IDs not in canonical graph counted in `unknown_node_count`
3. `test_raw_proposal_preserves_unknown_tags` — tags outside PERMITTED_TAGS preserved as items (not rewritten)
4. `test_blocked_derived_from_violations` — no violations → `blocked=False`; blocked violation → `blocked=True`
5. `test_blocked_derived_from_malformed_raw` — `malformed_count > 0` → `blocked=True` even with zero violations
6. `test_per_work_unit_scope_narrow_only` — per-node intersection + per-work-unit union, result always subset of static max
7. `test_mutation_reachability_direct` — node with `mutation_sinks` + non-destructive tag → blocked
8. `test_mutation_reachability_unknown` — unknown reachability + safety-claiming tag → blocked
9. `test_override_binds_to_specific_violation` — override for violation A does not clear violation B
10. `test_override_expiry` — expired override is not applied
11. `test_override_does_not_rewrite_raw_proposal` — raw proposal unchanged after override application
12. `test_decision_audit_contains_all_fields` — persisted decision includes raw proposal, evidence, scopes, overrides
13. `test_production_run_grid_blocked` — `load_latest_decision().blocked=True` → `run_grid_cmd()` raises `SafetyError`
14. `test_old_compose_allowed_paths_removed` — import from both `moat.py` and `moat_authority.py` raises

---

## Files to touch

| File | Change |
|------|--------|
| `aoc-cli/aoc_cli/moat_authority.py` | Rewrite — `RawSemanticProposal`, `evaluate_boundary()`, `VerifiedBoundaryDecision`, `AuthorizedWorkUnit`, `OverrideRecord`, `persist_decision()`, `load_latest_decision()`, `refuse_worker_assignment()`, `classify_mutation_reachability()` |
| `aoc-cli/aoc_cli/semantic_moat.py` | Remove `_parse_llm_tags()` — replaced by `ingest_raw_semantic_proposal()` in moat_authority. Remove `LLM_RESPONSE_EXPECTED_KEYS`. Simplify `enrich_with_llm_tags()` to call `ingest_raw_semantic_proposal()` and return a `RawSemanticProposal` alongside the enriched graph. |
| `aoc-cli/aoc_cli/moat.py` | Remove `compose_allowed_paths()` — it was a parallel duplicate. |
| `aoc-cli/aoc_cli/commands/run_grid.py` | Add `load_latest_decision()` call before worker creation; `if blocked: raise SafetyError`. |
| `aoc-cli/aoc_cli/commands/analyze_.py` | Add `evaluate_boundary()` call after `compile_inferred_json()`. Build static scopes from interaction_graph. Persist decision. |
| `tests/test_semantic_moat.py` | Add 14 new tests; update ~5 existing tests that reference removed functions. Keep total test count ≥ 36. |

---

## Verification

```bash
cd ~/Desktop/Loom
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
export GAIJINN_MOCK_GRID=1 GAIJINN_FAKE_REASONING=1 GAIJINN_ALLOW_INSECURE_LOCAL=1
.venv/bin/python -m pytest tests/test_semantic_moat.py -q --no-cov
```

All tests green + no regressions in loom suite = deliverable accepted.
