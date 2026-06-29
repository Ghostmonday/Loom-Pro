"""Immutable analysis receipts for auditable whole-state interrogation passes."""

from __future__ import annotations

import time
import uuid
from typing import Any

from aoc_supervisor.spec_analysis_types import AnalysisValidationResult, is_valid_digest

RECEIPT_SCHEMA_VERSION = 1


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_receipt_id() -> str:
    return f"rcpt_{uuid.uuid4().hex[:12]}"


def build_analysis_receipt(
    *,
    input_digest: str,
    output_digest: str,
    provider_id: str,
    model_id: str,
    policy_version: str,
    analysis_revision: int,
    evidence_revision: int,
    next_action: str,
    readiness_score: float,
    ready_to_finalize: bool,
    timestamp: str | None = None,
    receipt_id: str | None = None,
    status: str = "completed",
    error_code: str | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    """Create a concise receipt without hidden reasoning content."""
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "receipt_id": receipt_id or new_receipt_id(),
        "timestamp": timestamp or _now_iso(),
        "status": status,
        "input_digest": input_digest,
        "output_digest": output_digest,
        "provider_id": provider_id,
        "model_id": model_id,
        "policy_version": policy_version,
        "analysis_revision": int(analysis_revision),
        "evidence_revision": int(evidence_revision),
        "next_action": str(next_action),
        "readiness_score": float(readiness_score),
        "ready_to_finalize": bool(ready_to_finalize),
        "error_code": error_code,
        "error_message": error_message,
    }


def public_receipt_view(receipt: dict[str, Any]) -> dict[str, Any]:
    """Safe receipt projection for session/API surfaces."""
    allowed = {
        "schema_version",
        "receipt_id",
        "timestamp",
        "status",
        "input_digest",
        "output_digest",
        "provider_id",
        "model_id",
        "policy_version",
        "analysis_revision",
        "evidence_revision",
        "next_action",
        "readiness_score",
        "ready_to_finalize",
        "error_code",
        "error_message",
    }
    return {key: receipt[key] for key in allowed if key in receipt}


def append_analysis_receipt(state: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    """Append a receipt and return the stored public view."""
    validation = validate_receipt(receipt)
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))
    stored = public_receipt_view(receipt)
    state.setdefault("analysis_receipts", []).append(stored)
    return stored


def latest_analysis_receipt(state: dict[str, Any]) -> dict[str, Any] | None:
    receipts = state.get("analysis_receipts", [])
    if not isinstance(receipts, list) or not receipts:
        return None
    last = receipts[-1]
    return last if isinstance(last, dict) else None


def validate_receipt(receipt: Any) -> AnalysisValidationResult:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return AnalysisValidationResult(ok=False, errors=["receipt must be an object"])

    for field_name in ("receipt_id", "timestamp", "provider_id", "model_id", "policy_version", "next_action"):
        if not str(receipt.get(field_name, "")).strip():
            errors.append(f"receipt missing {field_name}")

    for digest_field in ("input_digest", "output_digest"):
        if not is_valid_digest(receipt.get(digest_field)):
            errors.append(f"receipt has invalid {digest_field}")

    status = str(receipt.get("status", "completed"))
    if status not in {"completed", "failed"}:
        errors.append(f"receipt status invalid: {status}")

    for numeric_field in ("analysis_revision", "evidence_revision"):
        try:
            value = int(receipt.get(numeric_field, -1))
        except (TypeError, ValueError):
            errors.append(f"receipt {numeric_field} must be an integer")
            continue
        if value < 0:
            errors.append(f"receipt {numeric_field} must be non-negative")

    try:
        float(receipt.get("readiness_score", 0.0))
    except (TypeError, ValueError):
        errors.append("receipt readiness_score must be numeric")

    hidden_fields = {"chain_of_thought", "raw_model_output", "private_reasoning"}
    for hidden in hidden_fields:
        if hidden in receipt:
            errors.append(f"receipt must not contain hidden field: {hidden}")

    return AnalysisValidationResult(ok=not errors, errors=errors)


def summarize_receipts_for_snapshot(receipts: list[Any]) -> list[dict[str, Any]]:
    """Expose receipt summaries for analysis input without hidden content."""
    summaries: list[dict[str, Any]] = []
    for item in receipts:
        if not isinstance(item, dict):
            continue
        summaries.append(public_receipt_view(item))
    return summaries


def persist_analysis_receipt(
    state: dict[str, Any],
    *,
    snapshot_digest: str,
    output: dict[str, Any],
    provider_id: str = "unknown",
) -> dict[str, Any]:
    import hashlib
    import json

    clean_digest = snapshot_digest
    if clean_digest.startswith("sha256:"):
        hex_part = clean_digest[7:]
        if len(hex_part) < 64:
            clean_digest = "sha256:" + hex_part.ljust(64, "0")

    output_clean = {
        k: v for k, v in output.items() if k not in ("chain_of_thought", "raw_model_output", "private_reasoning")
    }
    canonical = json.dumps(output_clean, sort_keys=True, separators=(",", ":"), default=str)
    output_digest = f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"

    readiness = output.get("readiness") or {}
    readiness_score = float(readiness.get("score", 0.0)) if isinstance(readiness, dict) else 0.0
    ready_to_finalize = bool(readiness.get("ready_to_finalize", False)) if isinstance(readiness, dict) else False

    receipt = build_analysis_receipt(
        input_digest=clean_digest,
        output_digest=output_digest,
        provider_id=provider_id,
        model_id=output.get("model_id", "unknown"),
        policy_version="2.0.0-adaptive",
        analysis_revision=output.get("analysis_revision", 1),
        evidence_revision=output.get("evidence_revision", 1),
        next_action=output.get("next_action", "ASK"),
        readiness_score=readiness_score,
        ready_to_finalize=ready_to_finalize,
    )
    append_analysis_receipt(state, receipt)
    return receipt
