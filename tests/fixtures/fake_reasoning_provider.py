"""Deterministic fake reasoning provider for Perfect SPEC contract tests.

Never calls a live model. Scripts keyed by analysis turn or snapshot digest.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from aoc_supervisor.reasoning_provider import ProviderFailureError as ProductionProviderFailureError


class ReasoningProviderProtocol(Protocol):
    """Minimal provider protocol expected from production reasoning_provider.py."""

    provider_id: str

    def analyze(self, snapshot: dict[str, Any]) -> dict[str, Any]: ...


def snapshot_digest(snapshot: dict[str, Any]) -> str:
    snap_copy = copy.deepcopy(snapshot)
    snap_copy.pop("state_digest", None)
    canonical = json.dumps(snap_copy, sort_keys=True, separators=(",", ":"), default=str)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _base_output(
    *, revision: int = 1, next_action: str = "ASK", question: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "analysis_revision": revision,
        "evidence_revision": revision,
        "state_digest": "",
        "facts": [],
        "inferences": [],
        "assumptions": [],
        "contradictions": [],
        "resolved_without_user": [],
        "unresolved": [],
        "readiness": {
            "score": 0.0,
            "blocking_count": 0,
            "high_value_unknown_count": 1 if question else 0,
            "ready_to_finalize": next_action == "FINALIZE",
            "reason": "",
        },
        "next_action": next_action,
        "next_question": question,
    }


@dataclass
class ScriptedFakeReasoningProvider:
    """Injected test double that records every snapshot and returns scripted outputs."""

    provider_id: str = "fake-deterministic-v1"
    script: list[dict[str, Any]] = field(default_factory=list)
    recorded_snapshots: list[dict[str, Any]] = field(default_factory=list)
    fail_on_calls: set[int] = field(default_factory=set)
    _call_index: int = 0

    def analyze(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        self.recorded_snapshots.append(copy.deepcopy(snapshot))
        call_no = self._call_index
        self._call_index += 1
        if call_no in self.fail_on_calls:
            raise ProviderFailureError("simulated provider failure")

        if call_no >= len(self.script):
            res = _base_output(revision=call_no + 1, next_action="FINALIZE", question=None)
            res["state_digest"] = snapshot_digest(snapshot)
            return res

        payload = copy.deepcopy(self.script[call_no])
        payload.setdefault("analysis_revision", call_no + 1)
        payload.setdefault("evidence_revision", call_no + 1)
        payload["state_digest"] = snapshot_digest(snapshot)
        return payload

    @property
    def call_count(self) -> int:
        return self._call_index

    def last_snapshot(self) -> dict[str, Any]:
        if not self.recorded_snapshots:
            raise AssertionError("provider received no snapshots")
        return self.recorded_snapshots[-1]


class ProviderFailureError(ProductionProviderFailureError):
    """Typed recoverable provider failure expected from production."""

    def __init__(self, message: str = "simulated provider failure"):
        super().__init__(code="provider_failure", message=message, retryable=True)


def question_payload(
    *,
    question_id: str,
    text: str,
    decision_target: str,
    evidence_used: list[str] | None = None,
    recommended_default: str | None = None,
    risk_if_wrong: str = "low",
) -> dict[str, Any]:
    return {
        "question_id": question_id,
        "text": text,
        "decision_target": decision_target,
        "why_it_matters": "Reduces implementation risk for the SPEC.",
        "evidence_used": evidence_used or ["original_prompt"],
        "alternatives_considered": [],
        "recommended_default": recommended_default,
        "risk_if_wrong": risk_if_wrong,
        "answer_mode": "freeform",
    }


def divergence_script() -> list[dict[str, Any]]:
    """Two answers to the same decision target produce different next questions."""
    return [
        _base_output(
            revision=1,
            next_action="ASK",
            question=question_payload(
                question_id="q_authz",
                text="How should authentication work for external API consumers?",
                decision_target="authz_model",
            ),
        ),
        _base_output(
            revision=2,
            next_action="ASK",
            question=question_payload(
                question_id="q_storage_a",
                text="Should audit logs be retained for 30 or 90 days?",
                decision_target="audit_retention",
                evidence_used=["answer:oauth2"],
            ),
        ),
        _base_output(
            revision=3,
            next_action="ASK",
            question=question_payload(
                question_id="q_storage_b",
                text="Do you need immutable write-once audit storage?",
                decision_target="audit_immutability",
                evidence_used=["answer:api_keys"],
            ),
        ),
    ]


def contradiction_script() -> list[dict[str, Any]]:
    return [
        _base_output(
            revision=1,
            next_action="ASK",
            question=question_payload(
                question_id="q_latency",
                text="What latency target matters for dashboard reads?",
                decision_target="read_latency",
            ),
        ),
        {
            **_base_output(revision=2, next_action="CONFLICT_RESOLUTION", question=None),
            "contradictions": [
                {
                    "id": "ctr-001",
                    "description": "Zero-latency reads conflict with write validation window.",
                    "element_a_id": "REQ-A",
                    "element_b_id": "REQ-B",
                }
            ],
            "unresolved": [{"id": "u_ctr", "decision_target": "read_write_consistency", "blocking": True}],
        },
        _base_output(
            revision=3,
            next_action="ASK",
            question=question_payload(
                question_id="q_after_conflict",
                text="Confirm eventual consistency for writes while keeping read cache hot?",
                decision_target="consistency_model",
            ),
        ),
    ]


def default_resolution_script() -> list[dict[str, Any]]:
    return [
        _base_output(
            revision=1,
            next_action="ASK",
            question=question_payload(
                question_id="q_theme",
                text="Any strong preference for light vs dark default theme?",
                decision_target="ui_theme",
                recommended_default="dark",
                risk_if_wrong="low",
            ),
        ),
        {
            **_base_output(revision=2, next_action="DEFAULT", question=None),
            "resolved_without_user": [
                {
                    "decision_target": "ui_theme",
                    "resolution_method": "DEFAULT",
                    "value": "dark",
                    "risk_if_wrong": "low",
                }
            ],
        },
        _base_output(revision=3, next_action="FINALIZE", question=None),
    ]


def high_impact_script() -> list[dict[str, Any]]:
    return [
        {
            **_base_output(
                revision=1,
                next_action="CONFIRM",
                question=question_payload(
                    question_id="q_delete",
                    text="Confirm permanent deletion of all customer data on account closure?",
                    decision_target="data_deletion_policy",
                    risk_if_wrong="high",
                ),
            ),
            "readiness": {
                "score": 0.2,
                "blocking_count": 1,
                "high_value_unknown_count": 1,
                "ready_to_finalize": False,
                "reason": "irreversible data lifecycle decision",
            },
        }
    ]


def early_finalize_script() -> list[dict[str, Any]]:
    return [
        _base_output(
            revision=1,
            next_action="ASK",
            question=question_payload(
                question_id="q_scope",
                text="What is explicitly out of scope for V1?",
                decision_target="product_scope",
            ),
        ),
        {
            **_base_output(revision=2, next_action="FINALIZE", question=None),
            "readiness": {
                "score": 0.95,
                "blocking_count": 0,
                "high_value_unknown_count": 0,
                "ready_to_finalize": True,
                "reason": "blocking uncertainties resolved; untouched domains are low-risk",
            },
        },
    ]
