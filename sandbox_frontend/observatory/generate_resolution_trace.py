"""Generate a real resolution_v3 engine trace for the Resolution Observatory UI.

Runs the actual engine (no mocks) on a fixture that exercises A1, B1, B2,
a STUCK state, and the A3 proposal boundary prototype (speculative copy,
check gauntlet, deterministic selection). Emits resolution-trace.js so the
observatory page works over file:// with zero network dependencies.

The proposal evaluation implemented here is the working prototype of the
A3-D3 slice: the model proposes, the engine decides.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "aoc-cli"))

from aoc_cli.resolution_v3 import (  # noqa: E402
    ConstraintGraph,
    Edge,
    Locus,
    Modality,
    Node,
    ProposalDecisionStatus,
    ProposalKind,
    ResolutionProposal,
    Status,
    canonicalize_proposals,
    copy_graph_for_proposal,
    resolve,
)
from aoc_cli.resolution_v3.model import LABEL_TYPE_DOMAIN  # noqa: E402
from aoc_cli.resolution_v3.rules import _aggregate_target_domain  # noqa: E402


def build_fixture() -> ConstraintGraph:
    cg = ConstraintGraph()
    cg.add_node(Node(id="ingest_api", status=Status.KNOWN, type="service", layer=1, root_permitted=True))
    cg.add_node(Node(id="billing_core", status=Status.KNOWN, type="service", layer=1))
    cg.add_node(Node(id="retry_daemon", status=Status.KNOWN, type="service", layer=1))
    cg.add_node(Node(id="queue_mgr", status=Status.KNOWN, type="service", layer=1))

    cg.add_edge(Edge(u="ingest_api", v="billing_core", modality=Modality.REQ, label="calls"))
    cg.add_edge(Edge(u="ingest_api", v="billing_core", modality=Modality.FORBID, label="calls"))
    cg.add_edge(Edge(u="billing_core", v="audit_buffer", modality=Modality.REQ, label="flushes_to"))
    cg.add_edge(Edge(u="ingest_api", v="metrics_hub", modality=Modality.REQ, label="emits_to"))
    cg.add_edge(Edge(u="retry_daemon", v="queue_mgr", modality=Modality.REQ, label="calls"))
    cg.add_edge(Edge(u="queue_mgr", v="retry_daemon", modality=Modality.REQ, label="calls_back"))
    cg.add_edge(Edge(u="retry_daemon", v="billing_core", modality=Modality.REQ, label="calls"))
    return cg


def snapshot(cg: ConstraintGraph) -> dict:
    return {
        "nodes": [
            {
                "id": node.id,
                "status": node.status.name,
                "type": node.type,
                "layer": node.layer,
                "domain": sorted(node.domain),
                "root_permitted": node.root_permitted,
                "sink_permitted": node.sink_permitted,
            }
            for _, node in sorted(cg.nodes.items())
        ],
        "edges": [
            {
                "u": edge.u,
                "v": edge.v,
                "modality": edge.modality.name,
                "label": edge.label,
                "active": edge.active,
            }
            for edge in cg.edges
        ],
    }


def capture_resolution_steps() -> tuple[list[dict], ConstraintGraph, dict]:
    """Replay the deterministic run one step at a time via fresh rebuilds."""
    probe = build_fixture()
    final_report = resolve(probe)
    total_steps = final_report["steps"]

    steps: list[dict] = []
    prev_log_len = 0
    for k in range(total_steps + 1):
        cg = build_fixture()
        if k:
            resolve(cg, max_steps=k)
        entry = {
            "step": k,
            "psi": list(cg.psi()),
            "log": cg.log[prev_log_len:],
            "snapshot": snapshot(cg),
        }
        prev_log_len = len(cg.log)
        steps.append(entry)

    return steps, probe, final_report


CHECK_NAMES = (
    "well-formed payload",
    "kind completeness",
    "authority: declared scope",
    "target exists and is latent",
    "kind-specific legality",
    "no new validation errors",
    "psi strictly decreases",
)


def evaluate_proposal(cg: ConstraintGraph, proposal: ResolutionProposal) -> dict:
    """A3-D3 prototype: seven-check gauntlet on a speculative copy."""
    checks: list[dict] = []
    decision = {"proposal_id": proposal.proposal_id, "status": None, "reason": None,
                "psi_before": list(cg.psi()), "psi_after": None}

    def fail(index: int, reason: str, detail: str) -> dict:
        checks.append({"name": CHECK_NAMES[index], "pass": False, "detail": detail})
        for name in CHECK_NAMES[index + 1:]:
            checks.append({"name": name, "pass": None, "detail": "not reached"})
        decision["status"] = ProposalDecisionStatus.REJECTED.name
        decision["reason"] = reason
        return {"proposal": proposal_payload(proposal), "checks": checks, "decision": decision}

    def ok(index: int, detail: str) -> None:
        checks.append({"name": CHECK_NAMES[index], "pass": True, "detail": detail})

    ok(0, "frozen dataclass constructed; ids validated at boundary")

    if proposal.kind is ProposalKind.RESOLVE_LATENT_TYPE and proposal.selected_type is None:
        return fail(1, "malformed proposal: selected_type is required for RESOLVE_LATENT_TYPE",
                    "selected_type is None")
    if proposal.kind is ProposalKind.DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET and (
        proposal.label is None or not proposal.label_domain or proposal.selected_type is None
    ):
        return fail(1, "malformed proposal: label, label_domain, selected_type all required",
                    "incomplete declaration payload")
    ok(1, "kind-specific required fields present")

    if Locus.node(proposal.target_id) not in proposal.scope:
        return fail(2, f"authority violation: scope does not include node '{proposal.target_id}'",
                    "target locus missing from declared scope")
    ok(2, f"scope covers node '{proposal.target_id}'")

    target = cg.nodes.get(proposal.target_id)
    if target is None:
        return fail(3, f"unknown target: '{proposal.target_id}' not in graph", "no such node")
    if target.status is not Status.LATENT_UNRESOLVED:
        return fail(3, f"target '{proposal.target_id}' is not latent", f"status={target.status.name}")
    ok(3, f"'{proposal.target_id}' is LATENT_UNRESOLVED")

    spec = copy_graph_for_proposal(cg)
    spec_target = spec.nodes[proposal.target_id]

    if proposal.kind is ProposalKind.RESOLVE_LATENT_TYPE:
        if not spec_target.domain or proposal.selected_type not in spec_target.domain:
            return fail(4, f"selected type '{proposal.selected_type}' outside aggregated domain "
                           f"{sorted(spec_target.domain)}", "domain membership failed")
        ok(4, f"'{proposal.selected_type}' is in aggregated domain {sorted(spec_target.domain)}")
    else:
        if proposal.label in LABEL_TYPE_DOMAIN:
            return fail(4, f"label '{proposal.label}' is already declared; redefinition is forbidden",
                        "schema redefinition attempt")
        if proposal.selected_type not in proposal.label_domain:
            return fail(4, f"selected type '{proposal.selected_type}' outside proposed label domain",
                        "declaration is self-inconsistent")
        ok(4, f"new label '{proposal.label}' -> {sorted(proposal.label_domain)}")

    errors_before = set(spec.validation_errors())

    # Speculative application — the copy only. The canonical graph is untouched.
    if proposal.kind is ProposalKind.DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET:
        # Prototype note: schema is module-global today; D3a makes it graph-scoped.
        LABEL_TYPE_DOMAIN[proposal.label] = set(proposal.label_domain)
        try:
            aggregated = _aggregate_target_domain(spec, proposal.target_id)
            spec_target.domain = set(aggregated.domain)
            if proposal.selected_type not in spec_target.domain:
                return fail(5, f"selected type '{proposal.selected_type}' outside re-aggregated domain "
                               f"{sorted(spec_target.domain)}", "post-declaration membership failed")
            spec_target.type = proposal.selected_type
            spec_target.layer = proposal.layer if proposal.layer is not None else 1
            spec_target.status = Status.KNOWN
            errors_after = set(spec.validation_errors())
            psi_after = spec.psi()
        finally:
            del LABEL_TYPE_DOMAIN[proposal.label]
    else:
        spec_target.type = proposal.selected_type
        spec_target.layer = proposal.layer if proposal.layer is not None else 1
        spec_target.status = Status.KNOWN
        errors_after = set(spec.validation_errors())
        psi_after = spec.psi()

    new_errors = sorted(errors_after - errors_before)
    if new_errors:
        return fail(5, "structural/semantic regression: proposal introduces new validation errors",
                    "; ".join(new_errors))
    ok(5, f"errors {len(errors_before)} -> {len(errors_after)}, no new classes")

    psi_before = tuple(decision["psi_before"])
    if not (psi_after < psi_before):
        return fail(6, f"non-progress: Psi did not strictly decrease ({psi_before} -> {psi_after})",
                    "descent violated")
    ok(6, f"Psi {psi_before} -> {tuple(psi_after)}")

    decision["status"] = ProposalDecisionStatus.ACCEPTED.name
    decision["reason"] = f"accepted: Psi {psi_before} -> {tuple(psi_after)}"
    decision["psi_after"] = list(psi_after)
    return {"proposal": proposal_payload(proposal), "checks": checks, "decision": decision}


def apply_accepted(cg: ConstraintGraph, proposal: ResolutionProposal) -> None:
    """Engine-controlled acceptance: the only path that mutates the canonical graph."""
    target = cg.nodes[proposal.target_id]
    if proposal.kind is ProposalKind.DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET:
        LABEL_TYPE_DOMAIN[proposal.label] = set(proposal.label_domain)
        target.domain = set(_aggregate_target_domain(cg, proposal.target_id).domain)
    target.type = proposal.selected_type
    target.layer = proposal.layer if proposal.layer is not None else 1
    target.status = Status.KNOWN
    cg.log.append(
        f"[A3] llm proposal '{proposal.proposal_id}' resolved '{proposal.target_id}' "
        f"as type={proposal.selected_type} (source={proposal.source}; engine-accepted)"
    )


def proposal_payload(proposal: ResolutionProposal) -> dict:
    return {
        "proposal_id": proposal.proposal_id,
        "kind": proposal.kind.name,
        "target_id": proposal.target_id,
        "selected_type": proposal.selected_type,
        "label": proposal.label,
        "label_domain": sorted(proposal.label_domain),
        "scope": [f"{locus.kind.name}:{locus.identity}" for locus in proposal.sorted_scope()],
        "source": proposal.source,
    }


def main() -> None:
    steps, cg, stuck_report = capture_resolution_steps()

    proposals = canonicalize_proposals(
        [
            ResolutionProposal(
                proposal_id="P-001", kind=ProposalKind.RESOLVE_LATENT_TYPE,
                target_id="audit_buffer", selected_type="log_sink",
                scope=frozenset({Locus.node("audit_buffer")}),
            ),
            ResolutionProposal(
                proposal_id="P-002", kind=ProposalKind.RESOLVE_LATENT_TYPE,
                target_id="audit_buffer", selected_type="database",
                scope=frozenset({Locus.node("audit_buffer")}),
            ),
            ResolutionProposal(
                proposal_id="P-003", kind=ProposalKind.RESOLVE_LATENT_TYPE,
                target_id="metrics_hub", selected_type="service",
            ),
            ResolutionProposal(
                proposal_id="P-004", kind=ProposalKind.DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET,
                target_id="metrics_hub", label="emits_to",
                label_domain=frozenset({"log_sink"}), selected_type="log_sink",
                scope=frozenset({Locus.node("metrics_hub")}),
            ),
            ResolutionProposal(
                proposal_id="P-005", kind=ProposalKind.RESOLVE_LATENT_TYPE,
                target_id="audit_buffer",
                scope=frozenset({Locus.node("audit_buffer")}),
            ),
        ]
    )

    firings: list[dict] = []
    pending = list(proposals)
    firing_no = 0
    while True:
        firing_no += 1
        evaluations = [evaluate_proposal(cg, proposal) for proposal in pending]
        accepted = [
            (tuple(ev["decision"]["psi_after"]), proposal.sort_key(), proposal, ev)
            for proposal, ev in zip(pending, evaluations)
            if ev["decision"]["status"] == "ACCEPTED"
        ]
        if not accepted:
            firings.append({"firing": firing_no, "evaluations": evaluations, "selected": None,
                            "psi": list(cg.psi()), "snapshot": snapshot(cg), "log": []})
            break
        accepted.sort(key=lambda item: (item[0], item[1]))
        _, _, winner, winner_ev = accepted[0]
        for _, _, proposal, ev in accepted[1:]:
            ev["decision"]["status"] = "REJECTED"
            ev["decision"]["reason"] = (
                f"superseded: deterministic selection chose '{winner.proposal_id}' this firing"
            )
        log_before = len(cg.log)
        apply_accepted(cg, winner)
        firings.append({
            "firing": firing_no,
            "evaluations": evaluations,
            "selected": winner.proposal_id,
            "psi": list(cg.psi()),
            "snapshot": snapshot(cg),
            "log": cg.log[log_before:],
        })
        pending = [p for p in pending if p.proposal_id != winner.proposal_id]

    final_report = resolve(cg)

    trace = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "engine": "aoc_cli.resolution_v3 (real run, no mocks)",
            "fixture": "ingest/billing/retry demo — A1 x2, B1, B2 weld, STUCK, A3 boundary",
            "doctrine": "the model proposes, the engine decides",
        },
        "resolution": {
            "steps": steps,
            "status": stuck_report["status"].name,
            "errors": sorted(set(build_and_report_errors())),
        },
        "proposals": {"firings": firings},
        "final": {
            "status": final_report["status"].name,
            "psi": list(cg.psi()),
            "errors": cg.validation_errors(),
            "snapshot": snapshot(cg),
            "log_tail": cg.log[-3:],
        },
    }

    # Replay digest: hash everything except the wall-clock timestamp. Two runs
    # of this script must produce the same digest — that IS the replay guarantee.
    hashable = {key: value for key, value in trace.items() if key != "meta"}
    trace["meta"]["replay_digest"] = hashlib.sha256(
        json.dumps(hashable, sort_keys=True).encode()
    ).hexdigest()[:16]

    out = Path(__file__).with_name("resolution-trace.js")
    out.write_text("window.LOOM_TRACE = " + json.dumps(trace, indent=1) + ";\n")
    print(f"wrote {out}")
    print(f"replay digest: {trace['meta']['replay_digest']}")
    print(f"stuck status: {stuck_report['status']}  final status: {final_report['status']}")
    print(f"final psi: {cg.psi()}  firings: {len(firings)}")


def build_and_report_errors() -> list[str]:
    cg = build_fixture()
    resolve(cg)
    return cg.validation_errors()


if __name__ == "__main__":
    main()
