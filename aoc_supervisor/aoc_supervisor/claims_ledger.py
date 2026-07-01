"""Deterministic Claims Ledger projection for Intent Forge state."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from aoc_supervisor.evidence_state import collect_evidence_items, compute_canonical_digest, normalize_session_state

CLAIMS_LEDGER_VERSION = 1

PROMOTED = "promoted"
BLOCKED = "blocked"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _claim_kind(classification: str) -> str:
    classification = classification.strip()
    return {
        "acceptance_criterion": "acceptance_criterion",
        "assumed": "assumption",
        "confirmed": "requirement",
        "constraint": "constraint",
        "decision": "decision",
        "deferred": "deferred",
        "inferred": "inference",
        "non_goal": "non_goal",
        "risk": "risk",
        "unresolved": "unresolved",
    }.get(classification, classification or "claim")


def _metadata(item: dict[str, Any]) -> dict[str, Any]:
    metadata = item.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _claim_subject(item: dict[str, Any]) -> str:
    metadata = _metadata(item)
    return (
        _clean(metadata.get("claim_subject"))
        or _clean(metadata.get("subject"))
        or _clean(item.get("domain"))
        or "session"
    )


def _claim_predicate(item: dict[str, Any]) -> str:
    metadata = _metadata(item)
    return (
        _clean(metadata.get("claim_predicate"))
        or _clean(metadata.get("predicate"))
        or _clean(item.get("classification"))
    )


def _claim_object(item: dict[str, Any]) -> str:
    metadata = _metadata(item)
    return _clean(metadata.get("claim_object")) or _clean(metadata.get("object")) or _clean(item.get("text"))


def _has_explicit_claim_key(item: dict[str, Any]) -> bool:
    metadata = _metadata(item)
    return bool(
        (_clean(metadata.get("claim_subject")) or _clean(metadata.get("subject")))
        and (_clean(metadata.get("claim_predicate")) or _clean(metadata.get("predicate")))
        and (_clean(metadata.get("claim_object")) or _clean(metadata.get("object")))
    )


def _evidence_ref(item: dict[str, Any]) -> dict[str, Any]:
    provenance = item.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    return {
        "evidence_id": _clean(item.get("evidence_id")),
        "source_kind": _clean(provenance.get("source_kind")) or "unknown",
        "source_id": _clean(provenance.get("source_id")),
        "source_label": _clean(provenance.get("source_label")),
    }


def _claim_from_evidence(item: dict[str, Any]) -> dict[str, Any] | None:
    text = _clean(item.get("text"))
    if not text:
        return None
    classification = _clean(item.get("classification"))
    kind = _claim_kind(classification)
    subject = _claim_subject(item)
    predicate = _claim_predicate(item)
    obj = _claim_object(item)
    active = not bool(item.get("stale") or item.get("superseded_by"))
    claim_core = {
        "kind": kind,
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "text": text,
        "domain": _clean(item.get("domain")),
        "evidence_id": _clean(item.get("evidence_id")),
    }
    claim_id = compute_canonical_digest(claim_core).replace("sha256:", "claim:")
    return {
        "id": claim_id,
        "kind": kind,
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "text": text,
        "domain": _clean(item.get("domain")),
        "classification": classification,
        "confidence": float(item.get("confidence", 0.0) or 0.0),
        "active": active,
        "explicit_claim_key": _has_explicit_claim_key(item),
        "evidence_refs": [_evidence_ref(item)],
        "promotion_status": PROMOTED if active else BLOCKED,
        "blocked_reasons": [] if active else ["stale_or_superseded"],
    }


def _claim_sort_key(claim: dict[str, Any]) -> tuple[Any, ...]:
    return (
        0 if claim.get("active") else 1,
        _clean(claim.get("kind")),
        _clean(claim.get("domain")),
        _clean(claim.get("subject")),
        _clean(claim.get("predicate")),
        _clean(claim.get("object")),
        _clean(claim.get("id")),
    )


def _detect_claim_contradictions(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comparable: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = {}
    for claim in claims:
        if not claim.get("active") or not claim.get("explicit_claim_key"):
            continue
        key = (_clean(claim.get("subject")).lower(), _clean(claim.get("predicate")).lower())
        obj = _clean(claim.get("object")).lower()
        if not key[0] or not key[1] or not obj:
            continue
        comparable.setdefault(key, {}).setdefault(obj, []).append(claim)

    contradictions: list[dict[str, Any]] = []
    for (subject, predicate), by_object in sorted(comparable.items()):
        if len(by_object) < 2:
            continue
        claim_ids = sorted(claim["id"] for claims_for_object in by_object.values() for claim in claims_for_object)
        contradiction_core = {
            "subject": subject,
            "predicate": predicate,
            "objects": sorted(by_object),
            "claim_ids": claim_ids,
        }
        contradictions.append(
            {
                "id": compute_canonical_digest(contradiction_core).replace("sha256:", "clash:"),
                "subject": subject,
                "predicate": predicate,
                "objects": sorted(by_object),
                "claim_ids": claim_ids,
                "description": f"Conflicting claims for {subject}.{predicate}: {sorted(by_object)}",
                "resolved": False,
                "blocking": True,
            }
        )
    return contradictions


def build_claim_ledger(state: dict[str, Any]) -> dict[str, Any]:
    """Build a stable claim ledger from session evidence without mutating state."""
    normalized = deepcopy(state)
    normalize_session_state(normalized)

    claims = [
        claim
        for item in collect_evidence_items(normalized)
        if isinstance(item, dict)
        for claim in [_claim_from_evidence(item)]
        if claim is not None
    ]
    claims.sort(key=_claim_sort_key)

    contradictions = _detect_claim_contradictions(claims)
    blocked_ids = {claim_id for contradiction in contradictions for claim_id in contradiction["claim_ids"]}
    contradiction_by_claim: dict[str, list[str]] = {}
    for contradiction in contradictions:
        for claim_id in contradiction["claim_ids"]:
            contradiction_by_claim.setdefault(claim_id, []).append(contradiction["id"])

    for claim in claims:
        claim_id = _clean(claim.get("id"))
        if claim_id in blocked_ids:
            claim["promotion_status"] = BLOCKED
            claim.setdefault("blocked_reasons", []).append("contradiction")
            claim["contradiction_ids"] = sorted(contradiction_by_claim.get(claim_id, []))

    promoted_claims = [claim for claim in claims if claim.get("promotion_status") == PROMOTED]
    blocked_claims = [claim for claim in claims if claim.get("promotion_status") == BLOCKED]
    packet_count = sum(len(claim.get("evidence_refs", [])) for claim in claims)
    ledger_without_digest = {
        "schema_version": CLAIMS_LEDGER_VERSION,
        "session_id": _clean(normalized.get("session_id")),
        "blueprint_version": int(normalized.get("blueprint_version", 0) or 0),
        "evidence_revision": int(normalized.get("evidence_revision", 0) or 0),
        "claim_count": len(claims),
        "evidence_packet_count": packet_count,
        "promoted_count": len(promoted_claims),
        "blocked_count": len(blocked_claims),
        "contradiction_count": len(contradictions),
        "claims": claims,
        "promoted_claims": promoted_claims,
        "blocked_claims": blocked_claims,
        "contradictions": contradictions,
        "promotion_gates": {
            "evidence_packet_received": packet_count > 0,
            "claims_extracted_with_provenance": bool(claims) and all(claim.get("evidence_refs") for claim in claims),
            "contradictions_resolved_or_blocked": not contradictions,
            "blueprint_influence_available": bool(promoted_claims) and not contradictions,
        },
    }
    return {
        **ledger_without_digest,
        "ledger_digest": compute_canonical_digest(ledger_without_digest),
    }
