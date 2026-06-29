"""Tests: P3 authority-moat vertical slice.

Existing deterministic tests (6) preserved at top.
Adversarial tests (10) + integration test (1) follow.
"""

from __future__ import annotations

import importlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from aoc_cli.errors import SafetyError
from aoc_cli.moat_authority import (
    PERMITTED_TAGS,
    OverrideRecord,
    ProvisionalTag,
    RawSemanticProposal,
    StaticNodeScope,
    VerifiedBoundaryDecision,
    ViolationRecord,
    build_static_scopes,
    classify_mutation_reachability,
    evaluate_boundary,
    ingest_raw_semantic_proposal,
    load_latest_decision,
    load_overrides,
    persist_override,
    refuse_worker_assignment,
    tag_restricted_paths,
)
from aoc_cli.semantic_moat import (
    _keyword_matches,
    enrich_intent_semantics,
    enrich_with_deterministic_tags,
    enrich_with_llm_tags,
)

# =========================================================================
# PRESERVED: 6 existing deterministic tests
# =========================================================================


def test_enrich_intent_semantics_adds_semantic_record_to_each_node() -> None:
    graph = [
        {"agent_intent": "token_create", "http_method": "POST"},
        {"agent_intent": "invoice_read", "http_method": "GET"},
    ]

    enriched = enrich_intent_semantics(graph)

    assert len(enriched) == 2
    assert all("semantic" in node for node in enriched)


def test_domain_classification_for_security_payments_and_orchestration() -> None:
    graph = [
        {"agent_intent": "tokens_rotate", "http_path": "/api/security/tokens"},
        {"agent_intent": "billing_checkout", "side_effects": ["create payment invoice"]},
        {"agent_intent": "grid_worker_spawn", "resource_cluster": "orchestration"},
    ]

    enriched = enrich_intent_semantics(graph)

    assert "security" in enriched[0]["semantic"]["domains"]
    assert "payments" in enriched[1]["semantic"]["domains"]
    assert "orchestration" in enriched[2]["semantic"]["domains"]


def test_impact_inference_by_http_method() -> None:
    graph = [
        {"agent_intent": "secret_delete", "http_method": "DELETE"},
        {"agent_intent": "secret_read", "http_method": "GET"},
        {"agent_intent": "secret_create", "http_method": "POST"},
        {"agent_intent": "secret_replace", "http_method": "PUT"},
        {"agent_intent": "secret_patch", "http_method": "PATCH"},
    ]

    impacts = [node["semantic"]["impact"] for node in enrich_intent_semantics(graph)]

    assert impacts == ["destructive", "read_only", "mutating", "mutating", "mutating"]


def test_scope_detection_uses_context_params() -> None:
    graph = [
        {"agent_intent": "org_secret_read", "context_params": ["orgID"]},
        {"agent_intent": "public_status_read"},
    ]

    enriched = enrich_intent_semantics(graph)

    assert enriched[0]["semantic"]["scope"] == "org_scoped"
    assert enriched[1]["semantic"]["scope"] == "public"


def test_edge_cases_empty_missing_fields_and_dataflow_puncture() -> None:
    assert enrich_intent_semantics([]) == []

    enriched = enrich_intent_semantics(
        [
            {},
            {
                "agent_intent": "secret_delete",
                "dataflow": {"has_dataflow_puncture": True},
            },
        ]
    )

    assert enriched[0]["semantic"]["domains"] == ["general"]
    assert enriched[1]["semantic"]["scope"] == "puncture_risk"


def test_keyword_matches_stems_without_short_substring_leaks() -> None:
    assert _keyword_matches({"tokens"}, "token")
    assert _keyword_matches({"payments"}, "payment")
    assert not _keyword_matches({"authentication"}, "tenant")
    assert not _keyword_matches({"gridlock"}, "grid")


# =========================================================================
# NEW: evaluate_boundary chokepoint — 6 checks
# =========================================================================


def _make_provisional(node_key: str, tag: str = "security", confidence: float = 0.95) -> ProvisionalTag:
    return ProvisionalTag(node_key=node_key, tag=tag, confidence=confidence, provenance="llm")


def _make_node(agent_intent: str, **overrides: Any) -> dict[str, Any]:
    n: dict[str, Any] = {
        "agent_intent": agent_intent,
        "http_method": "GET",
        "http_path": f"/api/{agent_intent}",
        "source_file": f"aoc-cli/aoc_cli/{agent_intent}.py",
    }
    n.update(overrides)
    return n


def _raw_from_tags(tags: dict[str, ProvisionalTag]) -> RawSemanticProposal:
    return RawSemanticProposal(
        source="llm",
        raw_payload=json.dumps([tag.to_dict() for tag in tags.values()], sort_keys=True),
        items=[tag.to_dict() for tag in tags.values()],
        malformed_count=0,
        unknown_node_count=0,
        dropped_keys=[],
    )


def _evaluate(
    tags: dict[str, ProvisionalTag],
    graph: list[dict[str, Any]],
    *,
    static_scopes: dict[str, StaticNodeScope] | None = None,
    raw: RawSemanticProposal | None = None,
):
    scopes = static_scopes or build_static_scopes(graph)
    return _evaluate_boundary_transient(
        raw_proposals=raw or _raw_from_tags(tags),
        canonical_graph=graph,
        static_scopes_by_node=scopes,
    )


def _evaluate_boundary_transient(**kwargs: Any) -> VerifiedBoundaryDecision:
    with tempfile.TemporaryDirectory(prefix="gaijinn-test-authority-") as tmp_dir:
        return evaluate_boundary(
            session_id="test-session",
            persist_path=Path(tmp_dir) / "latest-decision.json",
            **kwargs,
        )


def _checks(decision: VerifiedBoundaryDecision, check: str) -> list[ViolationRecord]:
    return [violation for violation in decision.violations if violation.check == check]


def test_raw_proposal_preserves_malformed_items() -> None:
    graph = [_make_node("node_a")]
    raw = ingest_raw_semantic_proposal(["not-a-dict"], graph)
    assert raw.malformed_count == 1
    assert raw.items[0]["_malformed"] is True


def test_raw_proposal_preserves_unknown_nodes() -> None:
    graph = [_make_node("node_a")]
    raw = ingest_raw_semantic_proposal(
        {"provisional_tags": [{"node_key": "ghost", "tag": "security", "confidence": 0.99}]},
        graph,
    )
    assert raw.unknown_node_count == 1
    assert raw.items[0]["node_key"] == "ghost"


def test_raw_proposal_preserves_unknown_tags() -> None:
    graph = [_make_node("node_a")]
    raw = ingest_raw_semantic_proposal(
        {"provisional_tags": [{"node_key": "node_a", "tag": "bogus", "confidence": 0.99}]},
        graph,
    )
    assert raw.items[0]["tag"] == "bogus"
    decision = _evaluate_boundary_transient(
        raw_proposals=raw,
        canonical_graph=graph,
        static_scopes_by_node=build_static_scopes(graph),
    )
    assert _checks(decision, "vocabulary")


def test_blocked_derived_from_violations() -> None:
    graph = [_make_node("node_a")]
    clean = _evaluate({"node_a": _make_provisional("node_a", tag="security")}, graph)
    blocked = _evaluate({"node_a": _make_provisional("node_a", tag="bogus")}, graph)
    assert clean.blocked is False
    assert blocked.blocked is True


def test_blocked_derived_from_malformed_raw() -> None:
    graph = [_make_node("node_a")]
    raw = RawSemanticProposal(
        source="llm",
        raw_payload="[]",
        items=[],
        malformed_count=1,
        unknown_node_count=0,
        dropped_keys=[],
    )
    decision = _evaluate({}, graph, raw=raw)
    assert decision.blocked is True
    assert _checks(decision, "raw_malformed")


def test_decision_cannot_be_constructed_manually() -> None:
    with pytest.raises(TypeError):
        VerifiedBoundaryDecision(
            session_id="manual",
            authorized_work_units=(),
            blocked=False,
            block_reasons=(),
            violations=(),
            raw_proposal=RawSemanticProposal(
                source="llm",
                raw_payload=None,
                items=[],
                malformed_count=0,
                unknown_node_count=0,
                dropped_keys=[],
            ),
            policy_version="test",
            deterministic_evidence={},
            overrides_applied=(),
            created_at="2026-01-01T00:00:00Z",
        )


# --- Check 1: Vocabulary -------------------------------------------------
def test_check_1_vocabulary_rejects_unknown_tag() -> None:
    """Unknown tag is blocked."""
    tags = {"node_a": _make_provisional("node_a", tag="nonsense")}
    graph = [_make_node("node_a")]
    decision = _evaluate(tags, graph)
    vocab = _checks(decision, "vocabulary")
    assert decision.blocked
    assert len(vocab) == 1
    assert vocab[0].severity == "blocked"


def test_check_1_vocabulary_accepts_permitted_tag() -> None:
    tags = {"node_a": _make_provisional("node_a", tag="security")}
    graph = [_make_node("node_a")]
    decision = _evaluate(tags, graph)
    vocab = _checks(decision, "vocabulary")
    assert not decision.blocked
    assert len(vocab) == 0


# --- Check 2: Confidence -------------------------------------------------
def test_check_2_confidence_blocks_below_threshold() -> None:
    tags = {"node_a": _make_provisional("node_a", confidence=0.3)}
    graph = [_make_node("node_a")]
    decision = _evaluate(tags, graph)
    conf = _checks(decision, "confidence")
    assert decision.blocked
    assert len(conf) == 1
    assert conf[0].severity == "blocked"


def test_check_2_confidence_accepts_at_threshold() -> None:
    tags = {"node_a": _make_provisional("node_a", confidence=0.6)}
    graph = [_make_node("node_a")]
    decision = _evaluate(tags, graph)
    conf = _checks(decision, "confidence")
    assert not decision.blocked
    assert len(conf) == 0


# --- Check 3: Mutation reachability --------------------------------------
def test_check_3_mutation_reachability_blocks_destructive_misclassification() -> None:
    """Mutating evidence cannot be authorized under a non-destructive tag."""
    tags = {"node_a": _make_provisional("node_a", tag="security")}
    graph = [_make_node("node_a", http_method="DELETE", source_file="src/prod/delete_stuff.py")]
    decision = _evaluate(tags, graph)
    mutation = _checks(decision, "mutation_reachability")
    assert decision.blocked
    assert len(mutation) == 1
    assert mutation[0].severity == "blocked"


def test_check_3_mutation_reachability_allows_destructive_tag() -> None:
    """Destructive mutation evidence is allowed, then narrowed by tag restrictions."""
    tags = {"node_a": _make_provisional("node_a", tag="destructive")}
    graph = [_make_node("node_a", http_method="DELETE", source_file="tests/test_delete.py")]
    decision = _evaluate(tags, graph)
    mutation = _checks(decision, "mutation_reachability")
    assert not decision.blocked
    assert len(mutation) == 0


def test_mutation_reachability_direct_blocks_non_destructive_tag() -> None:
    tags = {"node_a": _make_provisional("node_a", tag="security")}
    graph = [_make_node("node_a", dataflow={"mutation_sinks": ["db.users.delete"]})]
    decision = _evaluate(tags, graph)
    mutation = _checks(decision, "mutation_reachability")
    assert classify_mutation_reachability(graph[0]) == "direct"
    assert decision.blocked
    assert mutation[0].message.startswith("direct mutation evidence")


def test_mutation_reachability_unknown_blocks_safety_claiming_tag() -> None:
    tags = {"node_a": _make_provisional("node_a", tag="security")}
    graph = [_make_node("node_a", source_file="")]
    decision = _evaluate(tags, graph)
    mutation = _checks(decision, "mutation_reachability")
    assert classify_mutation_reachability(graph[0]) == "unknown"
    assert decision.blocked
    assert mutation[0].message == "mutation reachability is unknown for non-destructive tag"


# --- Check 4: Dataflow puncture ------------------------------------------
def test_check_4_dataflow_puncture_warns_on_flagged_node() -> None:
    tags = {"node_a": _make_provisional("node_a")}
    graph = [_make_node("node_a", dataflow={"has_dataflow_puncture": True})]
    decision = _evaluate(tags, graph)
    puncture = _checks(decision, "dataflow_puncture")
    assert decision.blocked
    assert len(puncture) == 1
    assert puncture[0].severity == "blocked"


# --- Check 5: Dark bridge ------------------------------------------------
def test_check_5_dark_bridge_blocks_low_confidence_across_negative_kappa_edge() -> None:
    tags = {
        "node_a": _make_provisional("node_a", confidence=0.6),
        "node_b": _make_provisional("node_b", confidence=0.99),
    }
    graph = [
        _make_node("node_a", edges=[{"source": "node_a", "target": "node_b", "kappa": -0.5}]),
        _make_node("node_b"),
    ]
    decision = _evaluate(tags, graph)
    dark = _checks(decision, "dark_bridge")
    assert decision.blocked
    assert len(dark) == 1
    assert dark[0].severity == "blocked"


def test_check_5_dark_bridge_allows_high_confidence_across_negative_edge() -> None:
    tags = {
        "node_a": _make_provisional("node_a", confidence=0.99),
        "node_b": _make_provisional("node_b", confidence=0.99),
    }
    graph = [
        _make_node("node_a", edges=[{"source": "node_a", "target": "node_b", "kappa": -0.5}]),
        _make_node("node_b"),
    ]
    decision = _evaluate(tags, graph)
    dark = _checks(decision, "dark_bridge")
    assert not decision.blocked
    assert len(dark) == 0


# --- Check 6: Node identity ----------------------------------------------
def test_check_6_node_identity_rejects_nonexistent_node() -> None:
    tags = {"ghost_node": _make_provisional("ghost_node")}
    graph = [_make_node("real_node")]
    decision = _evaluate(tags, graph)
    identity = _checks(decision, "node_identity")
    assert decision.blocked
    assert len(identity) == 2
    assert identity[0].severity == "blocked"
    assert identity[1].severity == "blocked"


# =========================================================================
# ProvisionalTag — never replaces canonical graph
# =========================================================================


def test_provisional_tag_never_mutates_canonical_graph() -> None:
    """LLM tags are stored as ProvisionalTag records; canonical graph untouched."""
    graph = [
        {"agent_intent": "secret_delete", "http_method": "DELETE"},
        {"agent_intent": "billing_charge", "http_method": "POST"},
    ]
    canonical_before = json.dumps(graph, sort_keys=True)

    _ = enrich_with_llm_tags(graph)
    canonical_after = json.dumps(graph, sort_keys=True)

    assert canonical_before == canonical_after
    assert graph[0].get("semantic") is None  # semantic only added by enrich_intent_semantics


def test_deterministic_tags_have_high_confidence() -> None:
    graph = [{"agent_intent": "token_create"}]
    tags = enrich_with_deterministic_tags(graph)
    assert all(t.confidence >= 0.8 for t in tags)
    assert all(t.provenance == "deterministic" for t in tags)


# =========================================================================
# Narrow-only scope composition
# =========================================================================


def test_authorized_work_unit_paths_are_narrow_only() -> None:
    """Tags only remove paths from the static max scope, never add them."""
    static = ("aoc-cli/aoc_cli", "src", "templates", "tests")
    tags = {"node_a": _make_provisional("node_a", tag="configuration")}
    graph = [_make_node("node_a", source_file="src/node_a.py")]
    decision = _evaluate(
        tags,
        graph,
        static_scopes={
            "node_a": StaticNodeScope(
                node_key="node_a",
                work_unit_id="unit-a",
                static_paths=static,
            )
        },
    )
    allowed = set(decision.authorized_work_units[0].authorized_paths)
    assert not decision.blocked
    # configuration restriction = templates/, config/, tests/, docs/
    assert "src" not in allowed
    assert "templates" in allowed
    assert "tests" in allowed
    # Nothing outside static is added
    assert "docs" not in allowed  # docs/ not in static scope


def test_general_tag_returns_full_static_scope() -> None:
    static = ("aoc-cli/aoc_cli", "tests")
    tags = {"node_a": _make_provisional("node_a", tag="general")}
    graph = [_make_node("node_a")]
    decision = _evaluate(
        tags,
        graph,
        static_scopes={
            "node_a": StaticNodeScope(
                node_key="node_a",
                work_unit_id="unit-a",
                static_paths=static,
            )
        },
    )
    assert decision.authorized_work_units[0].authorized_paths == tuple(sorted(static))


# =========================================================================
# Audit persistence
# =========================================================================


def test_audit_write_and_read(tmp_path: Path) -> None:
    """Persistent decision records round-trip correctly."""
    tags = {"node_a": _make_provisional("node_a", tag="nonsense")}
    graph = [_make_node("node_a")]
    path = tmp_path / ".gaijinn" / "authority" / "latest-decision.json"
    decision = evaluate_boundary(
        raw_proposals=_raw_from_tags(tags),
        canonical_graph=graph,
        static_scopes_by_node=build_static_scopes(graph),
        session_id="sess-test",
        persist_path=path,
    )

    loaded = load_latest_decision(path)
    assert loaded is not None
    assert loaded.session_id == decision.session_id
    assert loaded.blocked
    assert loaded.violations[0].check == "vocabulary"


def test_decision_audit_contains_all_fields(tmp_path: Path) -> None:
    tags = {"node_a": _make_provisional("node_a", tag="nonsense")}
    graph = [_make_node("node_a")]
    path = tmp_path / ".gaijinn" / "authority" / "latest-decision.json"
    decision = evaluate_boundary(
        raw_proposals=_raw_from_tags(tags),
        canonical_graph=graph,
        static_scopes_by_node=build_static_scopes(graph),
        session_id="audit-fields",
        persist_path=path,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["session_id"] == "audit-fields"
    assert payload["policy_version"] == decision.policy_version
    assert payload["decision"]["raw_proposal"]["items"][0]["tag"] == "nonsense"
    assert payload["decision"]["deterministic_evidence"]["node_count"] == 1
    assert payload["decision"]["authorized_work_units"][0]["static_max_paths"]


def test_override_records_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "overrides.jsonl"
    override = OverrideRecord(
        override_id="ovr-file",
        session_id="sess",
        violation_id="vio",
        node_key="node",
        reviewer_identity="test",
        expiry="2999-01-01T00:00:00Z",
        reason="round trip",
        created_at="2026-01-01T00:00:00Z",
    )
    persist_override(override, path=path)
    assert load_overrides(path=path) == [override]


# =========================================================================
# Human override
# =========================================================================


def test_refuse_worker_assignment_blocks_without_override() -> None:
    tags = {"node_a": _make_provisional("node_a", tag="nonsense")}
    graph = [_make_node("node_a")]
    decision = _evaluate(tags, graph)
    with pytest.raises(SafetyError):
        refuse_worker_assignment(decision)


def test_override_allows_specific_violation() -> None:
    tags = {"node_a": _make_provisional("node_a", tag="nonsense")}
    graph = [_make_node("node_a")]
    blocked = _evaluate(tags, graph)
    violation = blocked.violations[0]
    override = OverrideRecord(
        override_id="ovr-test",
        session_id="test-session",
        violation_id=violation.violation_id,
        node_key=violation.node_key,
        reviewer_identity="test",
        expiry="2999-01-01T00:00:00Z",
        reason="test scoped override",
        created_at="2026-01-01T00:00:00Z",
    )

    decision = _evaluate_boundary_transient(
        raw_proposals=_raw_from_tags(tags),
        canonical_graph=graph,
        static_scopes_by_node=build_static_scopes(graph),
        overrides=[override],
    )
    assert not decision.blocked
    assert decision.overrides_applied == (override,)


def test_override_binds_to_specific_violation() -> None:
    tags = {
        "node_a": _make_provisional("node_a", tag="nonsense"),
        "node_b": _make_provisional("node_b", confidence=0.2),
    }
    graph = [_make_node("node_a"), _make_node("node_b")]
    blocked = _evaluate(tags, graph)
    first = blocked.violations[0]
    override = OverrideRecord(
        override_id="ovr-specific",
        session_id="test-session",
        violation_id=first.violation_id,
        node_key=first.node_key,
        reviewer_identity="test",
        expiry="2999-01-01T00:00:00Z",
        reason="test scoped override",
        created_at="2026-01-01T00:00:00Z",
    )

    decision = _evaluate_boundary_transient(
        raw_proposals=_raw_from_tags(tags),
        canonical_graph=graph,
        static_scopes_by_node=build_static_scopes(graph),
        overrides=[override],
    )
    assert decision.blocked
    assert decision.overrides_applied == (override,)
    assert any(violation.violation_id != first.violation_id for violation in decision.violations)


def test_override_expiry() -> None:
    tags = {"node_a": _make_provisional("node_a", tag="nonsense")}
    graph = [_make_node("node_a")]
    blocked = _evaluate(tags, graph)
    violation = blocked.violations[0]
    override = OverrideRecord(
        override_id="ovr-expired",
        session_id="test-session",
        violation_id=violation.violation_id,
        node_key=violation.node_key,
        reviewer_identity="test",
        expiry="2000-01-01T00:00:00Z",
        reason="expired",
        created_at="1999-01-01T00:00:00Z",
    )

    decision = _evaluate_boundary_transient(
        raw_proposals=_raw_from_tags(tags),
        canonical_graph=graph,
        static_scopes_by_node=build_static_scopes(graph),
        overrides=[override],
    )
    assert decision.blocked
    assert decision.overrides_applied == ()


def test_override_does_not_rewrite_raw_proposal() -> None:
    tags = {"node_a": _make_provisional("node_a", tag="nonsense")}
    graph = [_make_node("node_a")]
    blocked = _evaluate(tags, graph)
    override = OverrideRecord(
        override_id="ovr-raw",
        session_id="test-session",
        violation_id=blocked.violations[0].violation_id,
        node_key="node_a",
        reviewer_identity="test",
        expiry="2999-01-01T00:00:00Z",
        reason="preserve raw",
        created_at="2026-01-01T00:00:00Z",
    )
    raw = _raw_from_tags(tags)
    decision = _evaluate_boundary_transient(
        raw_proposals=raw,
        canonical_graph=graph,
        static_scopes_by_node=build_static_scopes(graph),
        overrides=[override],
    )
    assert decision.raw_proposal.items == raw.items
    assert decision.raw_proposal.items[0]["tag"] == "nonsense"


# =========================================================================
# Tag restrictions
# =========================================================================


def test_tag_restrictions_match_permitted() -> None:
    for tag in PERMITTED_TAGS:
        restricted = tag_restricted_paths(tag)
        assert isinstance(restricted, tuple)


def test_old_compose_allowed_paths_removed() -> None:
    moat = importlib.import_module("aoc_cli.moat")
    authority = importlib.import_module("aoc_cli.moat_authority")

    assert not hasattr(moat, "compose_allowed_paths")
    assert not hasattr(authority, "compose_allowed_paths")


def test_production_run_grid_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    from aoc_cli.commands import run_grid as run_grid_module

    tags = {"node_a": _make_provisional("node_a", tag="nonsense")}
    graph = [_make_node("node_a")]
    decision = _evaluate(tags, graph)
    monkeypatch.setattr(
        run_grid_module,
        "_require_project_state",
        lambda: SimpleNamespace(intent_path=Path("intent.json")),
    )
    monkeypatch.setattr(run_grid_module, "load_latest_decision", lambda: decision)

    with pytest.raises(SafetyError):
        run_grid_module.run_grid_cmd(workers=1, force=False)


# =========================================================================
# Integration test: scan → ProvisionalTag → verify → compose → audit
# =========================================================================


def test_full_vertical_slice(tmp_path: Path) -> None:
    """End-to-end: deterministic scan, raw proposal, decision, audit."""
    graph = [
        {
            "agent_intent": "rotate_secrets",
            "http_method": "POST",
            "http_path": "/api/security/secrets",
            "source_file": "aoc-cli/aoc_cli/security.py",
        },
        {
            "agent_intent": "list_invoices",
            "http_method": "GET",
            "http_path": "/api/billing/invoices",
            "source_file": "aoc_supervisor/aoc_supervisor/billing.py",
        },
        {
            "agent_intent": "delete_user",
            "http_method": "DELETE",
            "http_path": "/api/admin/users",
            "source_file": "aoc-cli/aoc_cli/admin.py",
        },
    ]

    enriched = enrich_intent_semantics(graph)
    assert len(enriched) == 3

    raw = ingest_raw_semantic_proposal(None, enriched)
    decision_path = tmp_path / ".gaijinn" / "authority" / "latest-decision.json"
    decision = evaluate_boundary(
        raw_proposals=raw,
        canonical_graph=enriched,
        static_scopes_by_node=build_static_scopes(enriched),
        session_id="integ-test",
        persist_path=decision_path,
    )

    assert isinstance(decision, VerifiedBoundaryDecision)
    assert decision.raw_proposal.source == "deterministic"
    assert all(
        set(unit.authorized_paths).issubset(set(unit.static_max_paths)) for unit in decision.authorized_work_units
    )
    assert load_latest_decision(decision_path).session_id == "integ-test"


# =========================================================================
# State Matrix Invariant Transition Tests
# =========================================================================

def test_allowed_state_transitions() -> None:
    from aoc_cli.state import validate_worker_state_transition

    # Valid tracking path
    validate_worker_state_transition("spawning", "executing")
    validate_worker_state_transition("executing", "completed")
    validate_worker_state_transition("completed", "merged")

    # Copy-mode path
    validate_worker_state_transition("created", "merged")
    validate_worker_state_transition("pending", "already_merged")


def test_forbidden_state_hops() -> None:
    from aoc_cli.state import validate_worker_state_transition
    from aoc_cli.errors import StateError

    # Attempting to bypass execution loops must fail closed
    with pytest.raises(StateError, match="Illegal state jump attempted"):
        validate_worker_state_transition("spawning", "merged")

    with pytest.raises(StateError, match="Illegal state jump attempted"):
        validate_worker_state_transition("executing", "merged")

    with pytest.raises(StateError, match="Illegal state jump attempted"):
        validate_worker_state_transition("completed", "spawning")

    # Terminals
    with pytest.raises(StateError, match="Illegal state jump attempted"):
        validate_worker_state_transition("failed", "spawning")

    with pytest.raises(StateError, match="Illegal state jump attempted"):
        validate_worker_state_transition("timed_out", "executing")


def test_transition_worker_state_mutations(tmp_path: Path) -> None:
    from aoc_cli.state import transition_worker_state
    from aoc_cli.errors import StateError

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "workers": ["worker-001"],
                "worker_details": [
                    {"worker_id": "worker-001", "status": "spawning"}
                ],
            }
        ),
        encoding="utf-8",
    )

    # Valid transition: spawning -> executing
    transition_worker_state(manifest_path, "worker-001", "executing")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["worker_details"][0]["status"] == "executing"

    # Illegal transition: executing -> merged
    with pytest.raises(StateError, match="Illegal state jump attempted"):
        transition_worker_state(manifest_path, "worker-001", "merged")

