"""Semantic synthesis — deterministic domain mapping for Layer 1 Intent Nodes.

Translates syntactic tokens (method names, DB calls, path segments) into
ProvisionalTag records that sit parallel to the canonical interaction graph.

The canonical graph is NEVER mutated by LLM output.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from typing import Any

from aoc_cli.moat_authority import (
    ProvisionalTag,
    RawSemanticProposal,
    ingest_raw_semantic_proposal,
)

_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "security": ("secret", "auth", "permission", "credential", "token", "rbac", "tenant"),
    "payments": ("billing", "payment", "stripe", "invoice", "purchase", "checkout", "ledger"),
    "orchestration": ("grid", "worker", "spawn", "merge", "orchestrate", "swarm", "handoff"),
    "configuration": ("template", "config", "settings", "health", "telemetry", "status"),
    "destructive": ("delete", "remove", "drop", "purge", "truncate", "destroy"),
}
_IMPACT_BY_METHOD = {
    "DELETE": "destructive",
    "POST": "mutating",
    "PUT": "mutating",
    "PATCH": "mutating",
    "GET": "read_only",
    "CLI": "mutating",
}
_STEM_KEYWORDS = frozenset(
    {
        "auth",
        "credential",
        "encrypt",
        "orchestrate",
        "payment",
        "permission",
        "persist",
        "preserv",
        "purchase",
        "retriev",
        "secret",
        "token",
    }
)


# ---------------------------------------------------------------------------
# Primary entrypoint — returns (enriched_canonical_graph, ProvisionalTag list)
# ---------------------------------------------------------------------------
def enrich_intent_semantics(
    interaction_graph: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Attach semantic domain labels to each Layer 1 intent node and return
    the enriched canonical graph (deterministic-only; LLM enrichments stored
    as parallel ProvisionalTag records).

    The canonical graph semantic records are always deterministic.
    """
    enriched: list[dict[str, Any]] = []
    for raw in interaction_graph:
        if not isinstance(raw, Mapping):
            continue
        node = dict(raw)
        node["semantic"] = _semantic_record(node)
        enriched.append(node)
    return enriched


def enrich_with_deterministic_tags(
    interaction_graph: Sequence[Mapping[str, Any]],
) -> list[ProvisionalTag]:
    """Deterministic ProvisionalTags derived from keyword analysis.

    These run unconditionally regardless of LLM availability.
    """
    tags: list[ProvisionalTag] = []
    for raw in interaction_graph:
        if not isinstance(raw, Mapping):
            continue
        k = _node_key(raw)
        if not k:
            continue
        tokens = _collect_tokens(raw)
        domains = [
            domain
            for domain, keywords in _DOMAIN_KEYWORDS.items()
            if any(_keyword_matches(tokens, keyword) for keyword in keywords)
        ]
        tag = domains[0] if domains else "general"
        confidence = 0.95 if domains else 0.80  # deterministic = high confidence
        tags.append(
            ProvisionalTag(
                node_key=k,
                tag=tag,
                confidence=confidence,
                provenance="deterministic",
            )
        )
    return tags


def enrich_with_llm_tags(
    interaction_graph: Sequence[Mapping[str, Any]],
) -> RawSemanticProposal:
    """Optional LLM enrichment as an untrusted sidecar proposal.

    The canonical graph is NEVER mutated by this function.
    """
    if not _semantic_llm_enabled():
        return ingest_raw_semantic_proposal(None, interaction_graph)

    node_entries: list[dict[str, Any]] = []
    for raw in interaction_graph:
        if not isinstance(raw, Mapping):
            continue
        node = dict(raw)
        node.setdefault("semantic", _semantic_record(node))
        node_entries.append(node)

    endpoint = os.environ.get("GAIJINN_SEMANTIC_LLM_URL", "").strip()
    if not endpoint:
        return ingest_raw_semantic_proposal(None, interaction_graph)

    payload = json.dumps({"intent_nodes": node_entries}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return ingest_raw_semantic_proposal(None, interaction_graph)

    return ingest_raw_semantic_proposal(body, interaction_graph)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _semantic_record(node: Mapping[str, Any]) -> dict[str, Any]:
    """Build the deterministic semantic record attached to the canonical node."""
    tokens = _collect_tokens(node)
    domains = sorted(
        domain
        for domain, keywords in _DOMAIN_KEYWORDS.items()
        if any(_keyword_matches(tokens, keyword) for keyword in keywords)
    )
    method = str(node.get("http_method") or "CLI")
    impact = _IMPACT_BY_METHOD.get(method.upper(), "unknown")
    if "destructive" in domains or "delete" in tokens:
        impact = "destructive"
    scope: str = "org_scoped" if node.get("context_params") else "public"
    if node.get("dataflow", {}).get("has_dataflow_puncture"):
        scope = "puncture_risk"
    return {
        "domains": domains or ["general"],
        "impact": impact,
        "scope": scope,
        "synthesis": "deterministic_moat",
    }


def _collect_tokens(node: Mapping[str, Any]) -> set[str]:
    parts = [
        str(node.get("agent_intent", "")),
        str(node.get("http_path", "")),
        str(node.get("resource_cluster", "")),
        " ".join(node.get("side_effects", []) or []),
        " ".join(node.get("guard_conditions", []) or []),
    ]
    blob = " ".join(parts).lower()
    return {segment for segment in re.split(r"[^a-z0-9]+", blob) if segment}


def _keyword_matches(tokens: set[str], keyword: str) -> bool:
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    if keyword in _STEM_KEYWORDS:
        return any(token == keyword or token.startswith(keyword) for token in tokens)
    return keyword in tokens


def _node_key(node: Mapping[str, Any]) -> str:
    return str(node.get("agent_intent", node.get("key", node.get("id", ""))))


def _semantic_llm_enabled() -> bool:
    return os.environ.get("GAIJINN_SEMANTIC_LLM", "").strip().lower() in {"1", "true", "yes", "on"}
