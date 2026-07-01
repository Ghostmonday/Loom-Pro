"""Authority moat for semantic proposals and worker assignment.

LLM output is untrusted evidence.  The only supported path from semantic
proposal to worker scope is ``evaluate_boundary`` producing a
``VerifiedBoundaryDecision``.
"""

from __future__ import annotations

import builtins
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from aoc_cli.errors import SafetyError

POLICY_VERSION = "p3-authority-enforcement-v1"
AUTHORITY_DIR = Path(".gaijinn") / "authority"
LATEST_DECISION_PATH = AUTHORITY_DIR / "latest-decision.json"
OVERRIDES_PATH = AUTHORITY_DIR / "overrides.jsonl"

PERMITTED_TAGS: frozenset[str] = frozenset(
    {
        "security",
        "payments",
        "orchestration",
        "configuration",
        "destructive",
        "general",
    }
)

TAG_RESTRICTIONS: dict[str, tuple[str, ...]] = {
    "security": ("aoc-cli/aoc_cli/", "tests/", "docs/"),
    "payments": ("aoc_supervisor/aoc_supervisor/billing.py", "tests/", "docs/"),
    "orchestration": ("aoc-cli/aoc_cli/", "aoc_supervisor/aoc_supervisor/", "tests/"),
    "configuration": ("templates/", "config/", "tests/", "docs/"),
    "destructive": ("tests/", "docs/"),
    "general": (),
}

MUTATION_SAFE_TAGS: frozenset[str] = frozenset(
    {
        "security",
        "payments",
        "orchestration",
        "configuration",
        "general",
    }
)

_DECISION_TOKEN = object()


@dataclass(frozen=True)
class ProvisionalTag:
    """A parsed semantic tag candidate. It is never authorization-ready."""

    node_key: str
    tag: str
    confidence: float
    provenance: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_key": self.node_key,
            "tag": self.tag,
            "confidence": self.confidence,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ProvisionalTag:
        return cls(
            node_key=str(payload.get("node_key", "")),
            tag=str(payload.get("tag", "")),
            confidence=_coerce_confidence(payload.get("confidence", 0.0), clamp=False),
            provenance=str(payload.get("provenance", "llm")),
        )


@dataclass(frozen=True)
class RawSemanticProposal:
    """Untrusted semantic proposal preserved as observable evidence."""

    source: str
    raw_payload: str | None
    items: list[dict[str, Any]]
    malformed_count: int
    unknown_node_count: int
    dropped_keys: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "raw_payload": self.raw_payload,
            "items": list(self.items),
            "malformed_count": self.malformed_count,
            "unknown_node_count": self.unknown_node_count,
            "dropped_keys": list(self.dropped_keys),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> RawSemanticProposal:
        items = payload.get("items", [])
        raw_payload = payload.get("raw_payload")
        return cls(
            source=str(payload.get("source", "")),
            raw_payload=None if raw_payload is None else str(raw_payload),
            items=[dict(item) for item in items if isinstance(item, Mapping)],
            malformed_count=int(payload.get("malformed_count", 0)),
            unknown_node_count=int(payload.get("unknown_node_count", 0)),
            dropped_keys=[str(item) for item in payload.get("dropped_keys", [])],
        )


@dataclass(frozen=True)
class StaticNodeScope:
    node_key: str
    work_unit_id: str
    static_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_key": self.node_key,
            "work_unit_id": self.work_unit_id,
            "static_paths": list(self.static_paths),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> StaticNodeScope:
        return cls(
            node_key=str(payload.get("node_key", "")),
            work_unit_id=str(payload.get("work_unit_id", "")),
            static_paths=tuple(str(item) for item in payload.get("static_paths", [])),
        )


@dataclass(frozen=True)
class ViolationRecord:
    violation_id: str
    check: str
    node_key: str
    tag_attempted: str | None
    message: str
    severity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "check": self.check,
            "node_key": self.node_key,
            "tag_attempted": self.tag_attempted,
            "message": self.message,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ViolationRecord:
        tag_attempted = payload.get("tag_attempted")
        return cls(
            violation_id=str(payload.get("violation_id", "")),
            check=str(payload.get("check", "")),
            node_key=str(payload.get("node_key", "")),
            tag_attempted=None if tag_attempted is None else str(tag_attempted),
            message=str(payload.get("message", "")),
            severity=str(payload.get("severity", "")),
        )


@dataclass(frozen=True)
class OverrideRecord:
    override_id: str
    session_id: str
    violation_id: str
    node_key: str
    reviewer_identity: str
    expiry: str
    reason: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "override_id": self.override_id,
            "session_id": self.session_id,
            "violation_id": self.violation_id,
            "node_key": self.node_key,
            "reviewer_identity": self.reviewer_identity,
            "expiry": self.expiry,
            "reason": self.reason,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> OverrideRecord:
        return cls(
            override_id=str(payload.get("override_id", "")),
            session_id=str(payload.get("session_id", "")),
            violation_id=str(payload.get("violation_id", "")),
            node_key=str(payload.get("node_key", "")),
            reviewer_identity=str(payload.get("reviewer_identity", "")),
            expiry=str(payload.get("expiry", "")),
            reason=str(payload.get("reason", "")),
            created_at=str(payload.get("created_at", "")),
        )


@dataclass(frozen=True)
class AuthorizedWorkUnit:
    work_unit_id: str
    node_key: str
    static_max_paths: tuple[str, ...]
    authorized_paths: tuple[str, ...]
    tag_applied: str | None
    verification_result: str
    violations: tuple[ViolationRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_unit_id": self.work_unit_id,
            "node_key": self.node_key,
            "static_max_paths": list(self.static_max_paths),
            "authorized_paths": list(self.authorized_paths),
            "tag_applied": self.tag_applied,
            "verification_result": self.verification_result,
            "violations": [violation.to_dict() for violation in self.violations],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AuthorizedWorkUnit:
        tag_applied = payload.get("tag_applied")
        return cls(
            work_unit_id=str(payload.get("work_unit_id", "")),
            node_key=str(payload.get("node_key", "")),
            static_max_paths=tuple(str(item) for item in payload.get("static_max_paths", [])),
            authorized_paths=tuple(str(item) for item in payload.get("authorized_paths", [])),
            tag_applied=None if tag_applied is None else str(tag_applied),
            verification_result=str(payload.get("verification_result", "")),
            violations=tuple(
                ViolationRecord.from_dict(item) for item in payload.get("violations", []) if isinstance(item, Mapping)
            ),
        )


class VerifiedBoundaryDecision:
    """Authorization-ready boundary decision, produced only by evaluate_boundary."""

    __slots__ = (
        "session_id",
        "authorized_work_units",
        "blocked",
        "block_reasons",
        "violations",
        "raw_proposal",
        "policy_version",
        "deterministic_evidence",
        "overrides_applied",
        "created_at",
    )

    def __init__(
        self,
        *,
        session_id: str,
        authorized_work_units: tuple[AuthorizedWorkUnit, ...],
        blocked: bool,
        block_reasons: tuple[str, ...],
        violations: tuple[ViolationRecord, ...],
        raw_proposal: RawSemanticProposal,
        policy_version: str,
        deterministic_evidence: dict[str, Any],
        overrides_applied: tuple[OverrideRecord, ...],
        created_at: str,
        _token: object | None = None,
    ) -> None:
        if _token is not _DECISION_TOKEN:
            raise TypeError("VerifiedBoundaryDecision is produced only by evaluate_boundary")
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "authorized_work_units", authorized_work_units)
        object.__setattr__(self, "blocked", blocked)
        object.__setattr__(self, "block_reasons", block_reasons)
        object.__setattr__(self, "violations", violations)
        object.__setattr__(self, "raw_proposal", raw_proposal)
        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(self, "deterministic_evidence", deterministic_evidence)
        object.__setattr__(self, "overrides_applied", overrides_applied)
        object.__setattr__(self, "created_at", created_at)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("VerifiedBoundaryDecision is immutable")

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "authorized_work_units": [unit.to_dict() for unit in self.authorized_work_units],
            "blocked": self.blocked,
            "block_reasons": list(self.block_reasons),
            "violations": [violation.to_dict() for violation in self.violations],
            "raw_proposal": self.raw_proposal.to_dict(),
            "policy_version": self.policy_version,
            "deterministic_evidence": self.deterministic_evidence,
            "overrides_applied": [override.to_dict() for override in self.overrides_applied],
            "created_at": self.created_at,
        }

    @classmethod
    def _from_dict(cls, payload: Mapping[str, Any]) -> VerifiedBoundaryDecision:
        raw_proposal = payload.get("raw_proposal", {})
        deterministic_evidence = payload.get("deterministic_evidence", {})
        return cls(
            session_id=str(payload.get("session_id", "")),
            authorized_work_units=tuple(
                AuthorizedWorkUnit.from_dict(item)
                for item in payload.get("authorized_work_units", [])
                if isinstance(item, Mapping)
            ),
            blocked=bool(payload.get("blocked", False)),
            block_reasons=tuple(str(item) for item in payload.get("block_reasons", [])),
            violations=tuple(
                ViolationRecord.from_dict(item) for item in payload.get("violations", []) if isinstance(item, Mapping)
            ),
            raw_proposal=RawSemanticProposal.from_dict(raw_proposal if isinstance(raw_proposal, Mapping) else {}),
            policy_version=str(payload.get("policy_version", "")),
            deterministic_evidence=dict(deterministic_evidence if isinstance(deterministic_evidence, Mapping) else {}),
            overrides_applied=tuple(
                OverrideRecord.from_dict(item)
                for item in payload.get("overrides_applied", [])
                if isinstance(item, Mapping)
            ),
            created_at=str(payload.get("created_at", "")),
            _token=_DECISION_TOKEN,
        )


@dataclass(frozen=True)
class DecisionAuditRecord:
    session_id: str
    decision: VerifiedBoundaryDecision
    policy_version: str
    created_at: str
    override_provenance: list[OverrideRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "decision": self.decision.to_dict(),
            "policy_version": self.policy_version,
            "created_at": self.created_at,
            "override_provenance": [override.to_dict() for override in self.override_provenance],
        }


def ingest_raw_semantic_proposal(
    llm_response_body: Any,
    canonical_graph: Sequence[Mapping[str, Any]],
) -> RawSemanticProposal:
    """Preserve untrusted LLM output without pre-filtering hostile entries."""

    canonical_keys = {_node_key(node) for node in canonical_graph if _node_key(node)}
    source = "deterministic" if llm_response_body is None else "llm"
    raw_payload = None if llm_response_body is None else _json_dumps_lossy(llm_response_body)
    raw_items = _extract_raw_items(llm_response_body)

    if llm_response_body is None:
        raw_items = [
            {
                "node_key": _node_key(node),
                "tag": _deterministic_tag(node),
                "confidence": 0.95,
                "provenance": "deterministic",
            }
            for node in canonical_graph
            if _node_key(node)
        ]

    items: list[dict[str, Any]] = []
    malformed_count = 0
    unknown_node_count = 0
    dropped_keys: set[str] = set()
    expected_keys = {"node_key", "tag", "confidence", "provenance"}

    for raw_item in raw_items:
        if not isinstance(raw_item, Mapping):
            malformed_count += 1
            items.append({"_malformed": True, "raw": repr(raw_item)})
            continue
        item = _normalize_llm_item(raw_item)
        for key in item:
            if key not in expected_keys:
                dropped_keys.add(str(key))
        preserved = dict(item)
        missing = [key for key in ("node_key", "tag", "confidence") if key not in preserved]
        if missing:
            preserved["_missing_fields"] = missing
            malformed_count += 1
        node_key = str(preserved.get("node_key", ""))
        if node_key and node_key not in canonical_keys:
            unknown_node_count += 1
        items.append(preserved)

    return RawSemanticProposal(
        source=source,
        raw_payload=raw_payload,
        items=items,
        malformed_count=malformed_count,
        unknown_node_count=unknown_node_count,
        dropped_keys=sorted(dropped_keys),
    )


def _validate_proposal_items(
    raw_proposals: RawSemanticProposal,
    node_by_key: Mapping[str, Mapping[str, Any]],
    min_confidence: float,
) -> list[ViolationRecord]:
    violations: list[ViolationRecord] = []
    for item in raw_proposals.items:
        if item.get("_malformed"):
            continue
        node_key = str(item.get("node_key", ""))
        tag = str(item.get("tag", ""))
        confidence = _coerce_confidence(item.get("confidence", 0.0), clamp=False)

        if not node_key:
            violations.append(_violation("node_identity", "", tag or None, "proposal item missing node_key", "blocked"))
            continue
        if node_key not in node_by_key:
            violations.append(
                _violation(
                    "node_identity",
                    node_key,
                    tag or None,
                    f"node_key {node_key!r} is absent from canonical graph",
                    "blocked",
                )
            )
            continue
        if tag not in PERMITTED_TAGS:
            violations.append(_violation("vocabulary", node_key, tag, f"tag {tag!r} is not permitted", "blocked"))
            continue
        if confidence < min_confidence:
            violations.append(
                _violation(
                    "confidence",
                    node_key,
                    tag,
                    f"confidence {confidence:.3f} below minimum {min_confidence:.3f}",
                    "blocked",
                )
            )
            continue

        node = node_by_key[node_key]
        reachability = classify_mutation_reachability(node)
        if reachability == "unknown" and tag in MUTATION_SAFE_TAGS:
            violations.append(
                _violation(
                    "mutation_reachability",
                    node_key,
                    tag,
                    "mutation reachability is unknown for non-destructive tag",
                    "blocked",
                )
            )
        elif reachability in {"direct", "transitive"} and tag != "destructive":
            violations.append(
                _violation(
                    "mutation_reachability",
                    node_key,
                    tag,
                    f"{reachability} mutation evidence cannot be tagged as non-destructive",
                    "blocked",
                )
            )

        dataflow = node.get("dataflow", {})
        if isinstance(dataflow, Mapping) and dataflow.get("has_dataflow_puncture"):
            violations.append(
                _violation(
                    "dataflow_puncture",
                    node_key,
                    tag,
                    "unresolved dataflow puncture requires explicit override",
                    "blocked",
                )
            )
    return violations


def _check_omitted_nodes(
    raw_proposals: RawSemanticProposal,
    node_by_key: Mapping[str, Mapping[str, Any]],
    proposal_tags: Mapping[str, ProvisionalTag],
) -> list[ViolationRecord]:
    violations: list[ViolationRecord] = []
    # P1: Fail closed on omitted nodes — any canonical node absent from the LLM
    # proposal must generate a blocked violation rather than silently granting its
    # full static scope.  Deterministic proposals (source != "llm") are exempt.
    if raw_proposals.source == "llm":
        for canonical_key in node_by_key:
            if canonical_key not in proposal_tags:
                violations.append(
                    _violation(
                        "node_identity",
                        canonical_key,
                        None,
                        f"canonical node {canonical_key!r} was omitted from the LLM semantic proposal",
                        "blocked",
                    )
                )
    return violations


def _check_dark_bridges(
    canonical_graph: Sequence[Mapping[str, Any]],
    proposal_tags: Mapping[str, ProvisionalTag],
    curvature_floor: float,
    dark_bridge_min_confidence: float,
) -> list[ViolationRecord]:
    violations: list[ViolationRecord] = []
    for edge in _dark_edges(canonical_graph):
        src = str(edge.get("source", edge.get("from", "")))
        dst = str(edge.get("target", edge.get("to", "")))
        kappa = _coerce_float(edge.get("kappa", edge.get("curvature", 0.0)), 0.0)
        if kappa >= curvature_floor:
            continue
        for node_key in (src, dst):
            tag = proposal_tags.get(node_key)
            if tag is not None and tag.confidence < dark_bridge_min_confidence:
                violations.append(
                    _violation(
                        "dark_bridge",
                        node_key,
                        tag.tag,
                        (
                            f"dark bridge curvature {kappa:.4f} below floor {curvature_floor:.2f} "
                            f"requires confidence >= {dark_bridge_min_confidence:.2f}"
                        ),
                        "blocked",
                    )
                )
    return violations


def _collect_deterministic_evidence(
    node_by_key: Mapping[str, Mapping[str, Any]],
    static_scopes_by_node: Mapping[str, StaticNodeScope],
    curvature_floor: float,
    dark_bridge_min_confidence: float,
    min_confidence: float,
) -> dict[str, Any]:
    return {
        "node_count": len(node_by_key),
        "static_scope_count": len(static_scopes_by_node),
        "curvature_floor": curvature_floor,
        "dark_bridge_min_confidence": dark_bridge_min_confidence,
        "min_confidence": min_confidence,
        "mutation_reachability": {
            key: classify_mutation_reachability(node) for key, node in sorted(node_by_key.items())
        },
    }


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
    persist_path: Path | None = None,
) -> VerifiedBoundaryDecision:
    """Verify untrusted proposals and derive final worker scopes atomically."""

    now = _utc_now()
    node_by_key = {_node_key(node): node for node in canonical_graph if _node_key(node)}
    proposal_tags = _proposal_tags(raw_proposals)
    violations: list[ViolationRecord] = []

    if raw_proposals.malformed_count > 0:
        violations.append(
            _violation(
                "raw_malformed",
                "__raw__",
                None,
                f"raw semantic proposal contains {raw_proposals.malformed_count} malformed item(s)",
                "blocked",
            )
        )

    violations.extend(_validate_proposal_items(raw_proposals, node_by_key, min_confidence))
    violations.extend(_check_omitted_nodes(raw_proposals, node_by_key, proposal_tags))
    violations.extend(_check_dark_bridges(canonical_graph, proposal_tags, curvature_floor, dark_bridge_min_confidence))

    applied_overrides = _matching_overrides(violations, overrides or (), session_id=session_id, now=now)
    unresolved_violations = [
        violation for violation in violations if not _is_overridden(violation, applied_overrides, session_id=session_id)
    ]
    blocked = (
        any(violation.severity == "blocked" for violation in unresolved_violations) or raw_proposals.malformed_count > 0
    )

    authorized_units = _build_authorized_work_units(
        proposal_tags=proposal_tags,
        static_scopes_by_node=static_scopes_by_node,
        violations=violations,
        applied_overrides=applied_overrides,
        session_id=session_id,
    )
    decision = VerifiedBoundaryDecision(
        session_id=session_id,
        authorized_work_units=authorized_units,
        blocked=blocked,
        block_reasons=tuple(
            violation.message for violation in unresolved_violations if violation.severity == "blocked"
        ),
        violations=tuple(violations),
        raw_proposal=raw_proposals,
        policy_version=POLICY_VERSION,
        deterministic_evidence=_collect_deterministic_evidence(
            node_by_key,
            static_scopes_by_node,
            curvature_floor,
            dark_bridge_min_confidence,
            min_confidence,
        ),
        overrides_applied=tuple(applied_overrides),
        created_at=now,
        _token=_DECISION_TOKEN,
    )
    persist_decision(decision, path=persist_path)
    return decision


def classify_mutation_reachability(node: Mapping[str, Any]) -> str:
    """Return direct, transitive, none, or unknown mutation reachability."""

    dataflow = node.get("dataflow", {})
    if isinstance(dataflow, Mapping) and dataflow.get("mutation_sinks"):
        return "direct"

    side_effects = node.get("side_effects", [])
    if isinstance(side_effects, Sequence) and not isinstance(side_effects, (str, bytes)):
        side_effect_blob = " ".join(str(item).lower() for item in side_effects)
    else:
        side_effect_blob = str(side_effects).lower()
    method = str(node.get("http_method", "")).upper()
    intent = str(node.get("agent_intent", "")).lower()
    destructive_stems = (
        "delete",
        "remove",
        "drop",
        "purge",
        "truncate",
        "destroy",
        "mutate",
        "write",
        "create",
        "update",
    )
    if side_effect_blob.strip() or method == "DELETE" or any(stem in intent for stem in destructive_stems):
        return "transitive"

    if not str(node.get("source_file", "")).strip():
        return "unknown"

    return "none"


def build_static_scopes(canonical_graph: Sequence[Mapping[str, Any]]) -> dict[str, StaticNodeScope]:
    scopes: dict[str, StaticNodeScope] = {}
    peer_paths = [_source_parent(node) for node in canonical_graph if _source_parent(node)]
    fallback = tuple(sorted(set(peer_paths))) or (".",)
    for node in canonical_graph:
        node_key = _node_key(node)
        if not node_key:
            continue
        parent = _source_parent(node)
        static_paths = (parent,) if parent else fallback
        scopes[node_key] = StaticNodeScope(
            node_key=node_key,
            work_unit_id=str(node.get("work_unit_id", node.get("work_unit", node_key))),
            static_paths=tuple(sorted(set(static_paths))),
        )
    return scopes


def persist_decision(decision: VerifiedBoundaryDecision, path: Path | None = None) -> Path:
    """Atomically write the full authority decision."""

    authority_dir = AUTHORITY_DIR if path is None else path.parent
    authority_dir.mkdir(parents=True, exist_ok=True)
    target = path or authority_dir / f"{_timestamp_for_path(decision.created_at)}-decision.json"
    record = DecisionAuditRecord(
        session_id=decision.session_id,
        decision=decision,
        policy_version=decision.policy_version,
        created_at=decision.created_at,
        override_provenance=list(decision.overrides_applied),
    )
    _atomic_write_json(target, record.to_dict())
    if target != LATEST_DECISION_PATH:
        _atomic_write_json(LATEST_DECISION_PATH, record.to_dict())
    return target


def load_latest_decision(path: Path | None = None) -> VerifiedBoundaryDecision | None:
    target = path or LATEST_DECISION_PATH
    if not target.exists():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping) and isinstance(payload.get("decision"), Mapping):
        payload = payload["decision"]
    if not isinstance(payload, Mapping):
        raise SafetyError("authority decision is malformed")
    return VerifiedBoundaryDecision._from_dict(payload)


def persist_override(override: OverrideRecord, path: Path | None = None) -> Path:
    target = path or OVERRIDES_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(override.to_dict(), sort_keys=True) + "\n")
    return target


def load_overrides(path: Path | None = None) -> list[OverrideRecord]:
    target = path or OVERRIDES_PATH
    if not target.exists():
        return []
    overrides: list[OverrideRecord] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            overrides.append(OverrideRecord.from_dict(payload))
    return overrides


def refuse_worker_assignment(decision: VerifiedBoundaryDecision) -> None:
    if not isinstance(decision, VerifiedBoundaryDecision):
        raise TypeError("refuse_worker_assignment requires VerifiedBoundaryDecision")
    if decision.blocked:
        reason = "; ".join(decision.block_reasons) or "authority boundary blocked worker assignment"
        raise SafetyError(
            "authority boundary blocked worker assignment",
            cause=reason,
            fix_command="review .gaijinn/authority/latest-decision.json and apply a scoped override if appropriate",
        )


def tag_restricted_paths(tag: str) -> tuple[str, ...]:
    return TAG_RESTRICTIONS.get(tag, ())


def _proposal_tags(raw_proposals: RawSemanticProposal) -> dict[str, ProvisionalTag]:
    tags: dict[str, ProvisionalTag] = {}
    for item in raw_proposals.items:
        if item.get("_malformed"):
            continue
        node_key = str(item.get("node_key", ""))
        if not node_key:
            continue
        tags[node_key] = ProvisionalTag(
            node_key=node_key,
            tag=str(item.get("tag", "")),
            confidence=_coerce_confidence(item.get("confidence", 0.0), clamp=True),
            provenance=str(item.get("provenance", raw_proposals.source)),
        )
    return tags


def _build_authorized_work_units(
    *,
    proposal_tags: Mapping[str, ProvisionalTag],
    static_scopes_by_node: Mapping[str, StaticNodeScope],
    violations: Sequence[ViolationRecord],
    applied_overrides: Sequence[OverrideRecord],
    session_id: str,
) -> tuple[AuthorizedWorkUnit, ...]:
    units: list[AuthorizedWorkUnit] = []
    for node_key, static_scope in sorted(static_scopes_by_node.items()):
        tag = proposal_tags.get(node_key)
        node_violations = [violation for violation in violations if violation.node_key == node_key]
        unresolved = [
            violation
            for violation in node_violations
            if not _is_overridden(violation, applied_overrides, session_id=session_id)
        ]
        static_paths = tuple(sorted(set(static_scope.static_paths)))
        if any(violation.severity == "blocked" for violation in unresolved):
            authorized_paths = ()
            result = "blocked"
        elif tag is None:
            authorized_paths = static_paths
            result = "warning"
        else:
            authorized_paths = _authorized_paths_for_tag(static_paths, tag.tag)
            result = "passed" if not unresolved else "warning"
        if not set(authorized_paths).issubset(set(static_paths)):
            raise SafetyError(
                "authority decision attempted to widen scope",
                cause=f"{node_key} authorized_paths not subset of static max",
            )
        units.append(
            AuthorizedWorkUnit(
                work_unit_id=static_scope.work_unit_id,
                node_key=node_key,
                static_max_paths=static_paths,
                authorized_paths=authorized_paths,
                tag_applied=tag.tag if tag else None,
                verification_result=result,
                violations=tuple(node_violations),
            )
        )
    return tuple(units)


def _authorized_paths_for_tag(static_paths: Sequence[str], tag: str) -> tuple[str, ...]:
    restrictions = tag_restricted_paths(tag)
    static = tuple(sorted(set(static_paths)))
    if not restrictions:
        return static
    allowed = [path for path in static if any(_path_matches_prefix(path, prefix) for prefix in restrictions)]
    return tuple(sorted(set(allowed)))


def _path_matches_prefix(path: str, prefix: str) -> bool:
    normalized_path = _normalize_posix(path)
    normalized_prefix = _normalize_posix(prefix)
    if normalized_prefix == ".":
        return True
    return normalized_path == normalized_prefix or normalized_path.startswith(f"{normalized_prefix}/")


def _normalize_posix(path: str) -> str:
    value = PurePosixPath(str(path).replace("\\", "/")).as_posix().rstrip("/")
    return value or "."


def _matching_overrides(
    violations: Sequence[ViolationRecord],
    overrides: Sequence[OverrideRecord],
    *,
    session_id: str,
    now: str,
) -> list[OverrideRecord]:
    violation_keys = {(session_id, violation.node_key, violation.violation_id) for violation in violations}
    matched: list[OverrideRecord] = []
    for override in overrides:
        key = (override.session_id, override.node_key, override.violation_id)
        if key not in violation_keys:
            continue
        if _iso_expired(override.expiry, now):
            continue
        matched.append(override)
    return matched


def _is_overridden(violation: ViolationRecord, overrides: Sequence[OverrideRecord], *, session_id: str) -> bool:
    return any(
        override.session_id == session_id
        and override.node_key == violation.node_key
        and override.violation_id == violation.violation_id
        for override in overrides
    )


def _violation(check: str, node_key: str, tag_attempted: str | None, message: str, severity: str) -> ViolationRecord:
    basis = f"{check}:{node_key}:{tag_attempted or ''}:{message}"
    import hashlib

    return ViolationRecord(
        violation_id=f"vio_{hashlib.sha256(basis.encode('utf-8')).hexdigest()[:16]}",
        check=check,
        node_key=node_key,
        tag_attempted=tag_attempted,
        message=message,
        severity=severity,
    )


def _node_key(node: Mapping[str, Any]) -> str:
    return str(node.get("agent_intent", node.get("key", node.get("id", ""))))


def _source_parent(node: Mapping[str, Any]) -> str:
    source_file = str(node.get("source_file", "")).strip()
    if not source_file:
        return ""
    parent = PurePosixPath(source_file.replace("\\", "/")).parent.as_posix()
    return parent if parent and parent != "." else "."


def _deterministic_tag(node: Mapping[str, Any]) -> str:
    tokens = " ".join(
        [
            str(node.get("agent_intent", "")),
            str(node.get("http_path", "")),
            str(node.get("resource_cluster", "")),
            " ".join(str(item) for item in node.get("side_effects", []) or []),
        ]
    ).lower()
    for tag, keywords in {
        "security": ("secret", "auth", "permission", "credential", "token", "rbac", "tenant"),
        "payments": ("billing", "payment", "stripe", "invoice", "purchase", "checkout", "ledger"),
        "orchestration": ("grid", "worker", "spawn", "merge", "orchestrate", "swarm", "handoff"),
        "configuration": ("template", "config", "settings", "health", "telemetry", "status"),
        "destructive": ("delete", "remove", "drop", "purge", "truncate", "destroy"),
    }.items():
        if any(keyword in tokens for keyword in keywords):
            return tag
    return "general"


def _dark_edges(canonical_graph: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    edges: list[Mapping[str, Any]] = []
    for node in canonical_graph:
        raw_edges = node.get("edges", [])
        if isinstance(raw_edges, Sequence) and not isinstance(raw_edges, (str, bytes)):
            edges.extend(edge for edge in raw_edges if isinstance(edge, Mapping))
    return edges


def _extract_raw_items(payload: Any) -> list[Any]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return list(payload)
    if isinstance(payload, Mapping):
        for key in ("provisional_tags", "intent_nodes", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return list(value)
        return [dict(payload)]
    return [payload]


def _normalize_llm_item(item: Mapping[str, Any]) -> dict[str, Any]:
    mapping = {
        "key": "node_key",
        "id": "node_key",
        "intent": "node_key",
        "agent_intent": "node_key",
        "domain": "tag",
        "classification": "tag",
        "label": "tag",
    }
    normalized = dict(item)
    for old_key, new_key in mapping.items():
        if old_key in normalized and new_key not in normalized:
            normalized[new_key] = normalized[old_key]
    return normalized


def _coerce_confidence(value: Any, *, clamp: bool) -> float:
    confidence = _coerce_float(value, 0.0)
    if clamp:
        return max(0.0, min(1.0, confidence))
    return confidence


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _iso_expired(expiry: str, now: str) -> bool:
    try:
        return _parse_iso(expiry) <= _parse_iso(now)
    except ValueError:
        return True


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_for_path(value: str) -> str:
    return value.replace("-", "").replace(":", "").replace("+00:00", "Z")


def _json_dumps_lossy(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return repr(value)


def _atomic_write_json(target: Path, payload: Mapping[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(target)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


# dynamic filesystem boundary containment


class MoatContainmentError(SafetyError):
    """Raised when a file system or boundary containment violation is detected."""

    pass


_allowed_roots: list[Path] = []
_original_open = builtins.open
_original_os_open = os.open
_original_popen = subprocess.Popen
_original_run = subprocess.run


def set_allowed_roots(roots: Sequence[str | Path]) -> None:
    global _allowed_roots
    _allowed_roots = [Path(r).resolve() for r in roots]


def validate_path_containment(path: str | Path) -> None:
    if not _allowed_roots:
        return
    try:
        resolved_path = Path(path).resolve()
    except Exception:
        resolved_path = Path(path).absolute()

    is_contained = False
    for root in _allowed_roots:
        try:
            common = os.path.commonpath([str(root), str(resolved_path)])
            if common == str(root):
                is_contained = True
                break
        except ValueError:
            continue

    if not is_contained:
        error_msg = (
            f"Containment breach: path {path} (resolved: {resolved_path}) "
            f"escapes allowed workspace bounds {_allowed_roots}"
        )
        if "PYTEST_CURRENT_TEST" not in os.environ:
            sys.stderr.write(f"CONTAINMENT BREACH: {error_msg}\n")
            sys.stderr.flush()
            os._exit(1)
        raise MoatContainmentError(error_msg)


def patch_file_operations(roots: Sequence[str | Path]) -> None:
    set_allowed_roots(roots)

    def hooked_open(file, *args, **kwargs):
        if isinstance(file, (str, Path)):
            validate_path_containment(file)
        return _original_open(file, *args, **kwargs)

    builtins.open = hooked_open

    def hooked_os_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)):
            validate_path_containment(path)
        return _original_os_open(path, *args, **kwargs)

    os.open = hooked_os_open

    def hooked_popen(args, *pargs, **kwargs):
        cmd_args = args if isinstance(args, list) else [args]
        for arg in cmd_args:
            if isinstance(arg, (str, Path)):
                arg_str = str(arg)
                if "/" in arg_str or "\\" in arg_str or arg_str.startswith(".") or arg_str.startswith("/"):
                    try:
                        validate_path_containment(arg_str)
                    except MoatContainmentError:
                        raise
                    except Exception:  # noqa: S112 - non-path argv fragments are ignored by the containment hook.
                        continue
        return _original_popen(args, *pargs, **kwargs)

    subprocess.Popen = hooked_popen

    def hooked_run(args, *pargs, **kwargs):
        cmd_args = args if isinstance(args, list) else [args]
        for arg in cmd_args:
            if isinstance(arg, (str, Path)):
                arg_str = str(arg)
                if "/" in arg_str or "\\" in arg_str or arg_str.startswith(".") or arg_str.startswith("/"):
                    try:
                        validate_path_containment(arg_str)
                    except MoatContainmentError:
                        raise
                    except Exception:  # noqa: S112 - non-path argv fragments are ignored by the containment hook.
                        continue
        return _original_run(args, *pargs, **kwargs)

    subprocess.run = hooked_run


def unpatch_file_operations() -> None:
    global _allowed_roots
    _allowed_roots = []
    builtins.open = _original_open
    os.open = _original_os_open
    subprocess.Popen = _original_popen
    subprocess.run = _original_run
