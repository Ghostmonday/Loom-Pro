from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "examples" / "loom-source"
SRC.mkdir(parents=True, exist_ok=True)

states = ["accepted", "pending", "succeeded", "rejected", "failed", "cancelled", "timed_out"]


def action(description, endpoint):
    return {"description": description, "lifecycle_states": states, "backend_endpoint": endpoint}


actions = {
    "actions": {
        "intake.start_session": action(
            "Create a paid Intent Forge session from the user vision.", "POST /api/v1/intent-forge/sessions"
        ),
        "question.submit_answer": action(
            "Submit an answer and trigger complete evidence-state reanalysis before selecting the next question.",
            "POST /api/v1/intent-forge/sessions/{session_id}/answers",
        ),
        "question.revise_answer": action(
            "Revise a previous answer while preserving session version and idempotency guarantees.",
            "POST /api/v1/intent-forge/sessions/{session_id}/revise",
        ),
        "handoff.confirm": action(
            "Compile the executable projection and confirm that the session is ready for handoff.",
            "POST /api/v1/intent-forge/sessions/{session_id}/handoff?action=confirm",
        ),
        "handoff.accept": action(
            "Accept the confirmed handoff and move the session to HANDED_OFF.",
            "POST /api/v1/intent-forge/sessions/{session_id}/handoff?action=accept",
        ),
        "teleology.deliberate": action(
            "Stream architectural teleology through intent parse, graph ingest, curvature, bridge detection, weld planning, partition, and blueprint freeze.",
            "GET /api/v1/blueprint/deliberate",
        ),
        "blueprint.synthesize": action(
            "Fuse the Intent Forge executable projection with teleology and curvature artifacts into the canonical Loom blueprint.",
            "POST /api/v1/loom/blueprint/synthesize",
        ),
        "orchestrate.prepare": action(
            "Prepare an orchestration session from a handed-off Forge session and approved synthesized blueprint.",
            "POST /api/v1/orchestrate/prepare",
        ),
        "orchestrate.swarm": action(
            "Assign a worker count to a prepared orchestration session.", "POST /api/v1/orchestrate/swarm"
        ),
        "deploy.sprint": action(
            "Quote, purchase, and atomically spawn the multi-agent sprint.",
            "POST /api/v1/quote -> POST /api/v1/blueprint/purchase -> POST /api/v1/grid/spawn",
        ),
        "grid.poll_status": action(
            "Poll worker state until every assigned worker reaches a terminal status.", "GET /api/v1/grid/status"
        ),
        "merge.run": action("Run collect, worker validation, and merge-grid governance.", "POST /api/v1/grid/merge"),
        "merge.poll_status": action(
            "Poll the merge pipeline until completed or blocked.", "GET /api/v1/grid/merge/status"
        ),
        "deliverable.download": action(
            "Retrieve the merged deliverable archive after a clean merge.", "GET /api/v1/grid/deliverable"
        ),
        "deliverable.view_diff": action(
            "Retrieve the merged project diff and merge report.",
            "GET /api/v1/grid/diff and GET /api/v1/grid/merge/report",
        ),
        "intake.attach_project": action(
            "Attach an existing repository for Continuation without restarting Genesis.",
            "CONTRACT ONLY: POST /api/v1/loom/continuation/attach",
        ),
        "intake.resume_session": action(
            "Load existing Loom lineage for the attached repository.", "CONTRACT ONLY: IntentSessionStore.load"
        ),
        "intake.session_kind_select": action(
            "Select continuation, hotfix, v2, or refactor policy.", "CONTRACT ONLY: continuation session policy"
        ),
        "graph.bootstrap": action(
            "Create or reuse graph and metric artifacts for the attached repository snapshot.",
            "aoc-cli scan -> analyze",
        ),
        "interrogation.set_mode": action(
            "Select full, delta, or skip-if-graph-ready interrogation policy.",
            "CONTRACT ONLY: adaptive interrogation policy",
        ),
        "continuation.confirm_scope": action(
            "Approve the version-matched MODIFY, ADD, and DEPRECATE delta scope.",
            "CONTRACT ONLY: continuation scope approval",
        ),
        "deliverable.detect_surfaces": action(
            "Detect stable runnable terminal, web, and native launch descriptors.",
            "CONTRACT ONLY over GET /api/v1/grid/deliverable",
        ),
        "deliverable.present": action(
            "Select the primary launch or evolution presentation for the detected surface.",
            "CONTRACT ONLY: launch presentation dispatcher",
        ),
        "deliverable.open_terminal": action(
            "Expose and run the verified terminal launch command.", "CONTRACT ONLY: host terminal launcher"
        ),
        "deliverable.open_browser": action(
            "Start a web server if needed, verify health, and open the URL.", "CONTRACT ONLY: browser launch lifecycle"
        ),
        "deliverable.open_native": action(
            "Validate and open a native artifact through a host capability.", "CONTRACT ONLY: native launch lifecycle"
        ),
        "project.register_for_continuation": action(
            "Persist project lineage for deterministic future Continuation sessions.",
            "CONTRACT ONLY: .gaijinn/project-lineage.json",
        ),
    }
}

bindings = {}


def bind(prefix, domain, desc):
    bindings[f"loom.{prefix}.{domain}"] = {"domain": domain, "description": desc}


bind(
    "vision",
    "design_intent",
    "Preserves the single Vision Canvas mission: express intent, answer one adaptive question at a time, and authorize handoff without exposing orchestration controls.",
)
bind(
    "vision",
    "behavioral",
    "Requires complete state reanalysis after every answer, exactly one next question or stop condition, and explicit confirm then accept handoff sequencing.",
)
bind(
    "vision",
    "operational",
    "Uses the real Intent Forge session, version, idempotency, readiness, and executable-projection contracts.",
)
bind(
    "vision",
    "governance",
    "Forbids orchestrate.prepare from the Vision Canvas and blocks handoff until readiness and projection requirements are satisfied.",
)
bind(
    "vision",
    "institutional",
    "Maintains browser, API, CLI, and autonomous-agent parity through canonical Intent Mapping actions.",
)

bind(
    "command",
    "design_intent",
    "Presents teleological deliberation, topology evidence, synthesized work units, and the human blueprint approval boundary before execution.",
)
bind(
    "command",
    "behavioral",
    "Orders deliberate, synthesize, and prepare without phase skips and projects only action-specific state changes.",
)
bind(
    "command",
    "operational",
    "Surfaces the seven teleology subphases, curvature floor, dark-bridge plan, projection mode, and work-unit counts.",
)
bind(
    "command",
    "governance",
    "Enforces handoff before teleology, teleology before synthesis, and blueprint approval before preparation.",
)
bind(
    "command",
    "institutional",
    "Retains Loom architectural teleology as a first-class reviewable authority record rather than a hidden implementation detail.",
)

bind(
    "terminal",
    "design_intent",
    "Represents the manufacturing sequence from swarm sizing through atomic sprint, worker monitoring, governed merge, and deliverable retrieval.",
)
bind(
    "terminal",
    "behavioral",
    "Prevents deploy before preparation, merge before worker completion, and deliverable retrieval before a clean merge.",
)
bind(
    "terminal",
    "operational",
    "Projects recommended swarm, worker states, logs, merge counts, structural score, and deliverable metadata from real pipeline contracts.",
)
bind(
    "terminal",
    "governance",
    "Treats sprint launch and merge as high-risk controls and preserves blocked and conflicted outcomes as distinct refusal states.",
)
bind(
    "terminal",
    "institutional",
    "Keeps the stage rail aligned with Loom manufacturing order and preserves auditability of every worker and merge disposition.",
)

bind(
    "continuation",
    "design_intent",
    "Lets an existing repository enter Loom through lineage and delta capture rather than a forced Genesis restart.",
)
bind(
    "continuation",
    "behavioral",
    "Uses rigid attach, lineage, graph, delta, scope, and handoff order while allowing adaptive questioning only inside delta interrogation.",
)
bind(
    "continuation",
    "operational",
    "Keys graph reuse to repository fingerprint and scan configuration, and sorts approved work units by operation then stable path.",
)
bind(
    "continuation",
    "governance",
    "Requires a valid graph before teleology and a version-matched MODIFY, ADD, DEPRECATE scope approval before handoff.",
)
bind(
    "continuation",
    "institutional",
    "Preserves parent-session and blueprint lineage as immutable provenance for each evolution session.",
)

bind(
    "deliverable",
    "design_intent",
    "Makes the completed product, not the build machinery, the primary post-merge experience while retaining diff and download access.",
)
bind(
    "deliverable",
    "behavioral",
    "Detects runnable surfaces deterministically, exposes exactly one primary launch action, and preserves failure recovery without invalidating the merged artifact.",
)
bind(
    "deliverable",
    "operational",
    "Projects surface descriptors, run command or URL, process status, changelog summary, archive metadata, and continuation registration state.",
)
bind(
    "deliverable",
    "governance",
    "Blocks surface detection before merge completion, launch before a complete descriptor, and lineage registration without a merge receipt.",
)
bind(
    "deliverable",
    "institutional",
    "Registers the successful project and last launch surface so future work re-enters through Continuation instead of Genesis.",
)

knowledge = {"bindings": bindings}

manifests = {
    "vision-canvas.manifest.yaml": {
        "screen": "loom.vision_canvas",
        "mission": "Express a software vision, resolve uncertainty, and authorize architectural handoff.",
        "mission_id": "loom-vision-canvas",
        "elements": [
            {
                "id": "vision-start-btn",
                "classification": "action_control",
                "action": "intake.start_session",
                "feedback_target": "vision-feedback",
                "label": "Start Intent Forge Session",
            },
            {
                "id": "vision-submit-answer-btn",
                "classification": "action_control",
                "action": "question.submit_answer",
                "feedback_target": "vision-feedback",
                "label": "Submit Current Answer",
            },
            {
                "id": "vision-revise-answer-btn",
                "classification": "action_control",
                "action": "question.revise_answer",
                "feedback_target": "vision-feedback",
                "label": "Revise Previous Answer",
            },
            {
                "id": "vision-confirm-handoff-btn",
                "classification": "action_control",
                "action": "handoff.confirm",
                "feedback_target": "vision-feedback",
                "label": "Confirm Handoff Readiness",
            },
            {
                "id": "vision-accept-handoff-btn",
                "classification": "action_control",
                "action": "handoff.accept",
                "feedback_target": "vision-feedback",
                "label": "Accept Architectural Handoff",
            },
            {
                "id": "vision-prompt-display",
                "classification": "display",
                "contract_path": "loom.vision.prompt",
                "label": "Vision prompt fixture awaiting session start",
            },
            {
                "id": "vision-question-display",
                "classification": "display",
                "contract_path": "loom.vision.current_question",
                "label": "No current question",
            },
            {
                "id": "vision-understanding-display",
                "classification": "display",
                "contract_path": "loom.vision.understanding",
                "label": "Understanding evidence not yet established",
            },
            {
                "id": "vision-readiness-display",
                "classification": "display",
                "contract_path": "loom.vision.readiness",
                "label": "Readiness 0 percent",
            },
            {
                "id": "vision-handoff-display",
                "classification": "display",
                "contract_path": "loom.vision.handoff_state",
                "label": "Handoff locked",
            },
            {
                "id": "vision-feedback",
                "classification": "display",
                "contract_path": "loom.vision.feedback",
                "label": "Vision Canvas initialized",
                "tag": "output",
            },
        ],
        "knowledge_bindings": {
            d: f"loom.vision.{d}" for d in ["design_intent", "behavioral", "operational", "governance", "institutional"]
        },
        "accessibility": {"profile": "wcag-aa-strict"},
        "smoke_scenarios": ["smoke/vision-canvas.smoke.yaml"],
    },
    "command-engine.manifest.yaml": {
        "screen": "loom.command_engine",
        "mission": "Deliberate architecture, synthesize the blueprint, and approve preparation.",
        "mission_id": "loom-command-engine",
        "elements": [
            {
                "id": "command-deliberate-btn",
                "classification": "action_control",
                "action": "teleology.deliberate",
                "feedback_target": "command-feedback",
                "label": "Run Architectural Teleology",
            },
            {
                "id": "command-synthesize-btn",
                "classification": "action_control",
                "action": "blueprint.synthesize",
                "feedback_target": "command-feedback",
                "label": "Synthesize Canonical Blueprint",
            },
            {
                "id": "command-prepare-btn",
                "classification": "action_control",
                "action": "orchestrate.prepare",
                "feedback_target": "command-feedback",
                "label": "Approve Blueprint and Prepare",
            },
            {
                "id": "command-phase-display",
                "classification": "display",
                "contract_path": "loom.command.teleology_phase",
                "label": "Teleology idle",
            },
            {
                "id": "command-topology-display",
                "classification": "display",
                "contract_path": "loom.command.topology",
                "label": "Topology evidence unavailable",
            },
            {
                "id": "command-bridge-display",
                "classification": "display",
                "contract_path": "loom.command.bridge_plan",
                "label": "Dark bridge plan unavailable",
            },
            {
                "id": "command-blueprint-display",
                "classification": "display",
                "contract_path": "loom.command.blueprint",
                "label": "Blueprint not synthesized",
            },
            {
                "id": "command-approval-display",
                "classification": "display",
                "contract_path": "loom.command.approval_gate",
                "label": "Blueprint approval locked",
            },
            {
                "id": "command-feedback",
                "classification": "display",
                "contract_path": "loom.command.feedback",
                "label": "Command Engine initialized",
                "tag": "output",
            },
        ],
        "knowledge_bindings": {
            d: f"loom.command.{d}"
            for d in ["design_intent", "behavioral", "operational", "governance", "institutional"]
        },
        "accessibility": {"profile": "wcag-aa-strict"},
        "smoke_scenarios": ["smoke/command-engine.smoke.yaml"],
    },
    "terminal.manifest.yaml": {
        "screen": "loom.terminal",
        "mission": "Size the swarm, execute the approved blueprint, validate the merge, and retrieve the deliverable.",
        "mission_id": "loom-terminal",
        "elements": [
            {
                "id": "terminal-assign-swarm-btn",
                "classification": "action_control",
                "action": "orchestrate.swarm",
                "feedback_target": "terminal-feedback",
                "label": "Assign Recommended Swarm",
            },
            {
                "id": "terminal-deploy-btn",
                "classification": "action_control",
                "action": "deploy.sprint",
                "feedback_target": "terminal-feedback",
                "label": "Launch Atomic Sprint",
            },
            {
                "id": "terminal-poll-grid-btn",
                "classification": "action_control",
                "action": "grid.poll_status",
                "feedback_target": "terminal-feedback",
                "label": "Poll Worker Status",
            },
            {
                "id": "terminal-merge-btn",
                "classification": "action_control",
                "action": "merge.run",
                "feedback_target": "terminal-feedback",
                "label": "Run Governed Merge",
            },
            {
                "id": "terminal-poll-merge-btn",
                "classification": "action_control",
                "action": "merge.poll_status",
                "feedback_target": "terminal-feedback",
                "label": "Poll Merge Status",
            },
            {
                "id": "terminal-download-btn",
                "classification": "action_control",
                "action": "deliverable.download",
                "feedback_target": "terminal-feedback",
                "label": "Download Deliverable",
            },
            {
                "id": "terminal-diff-btn",
                "classification": "action_control",
                "action": "deliverable.view_diff",
                "feedback_target": "terminal-feedback",
                "label": "View Merged Diff",
            },
            {
                "id": "terminal-phase-display",
                "classification": "display",
                "contract_path": "loom.terminal.phase",
                "label": "Awaiting prepared blueprint",
            },
            {
                "id": "terminal-swarm-display",
                "classification": "display",
                "contract_path": "loom.terminal.swarm",
                "label": "No swarm assigned",
            },
            {
                "id": "terminal-grid-display",
                "classification": "display",
                "contract_path": "loom.terminal.grid",
                "label": "No active workers",
            },
            {
                "id": "terminal-merge-display",
                "classification": "display",
                "contract_path": "loom.terminal.merge",
                "label": "Merge idle",
            },
            {
                "id": "terminal-deliverable-display",
                "classification": "display",
                "contract_path": "loom.terminal.deliverable",
                "label": "Deliverable unavailable",
            },
            {
                "id": "terminal-feedback",
                "classification": "display",
                "contract_path": "loom.terminal.feedback",
                "label": "Terminal initialized",
                "tag": "output",
            },
        ],
        "knowledge_bindings": {
            d: f"loom.terminal.{d}"
            for d in ["design_intent", "behavioral", "operational", "governance", "institutional"]
        },
        "accessibility": {"profile": "wcag-aa-strict"},
        "smoke_scenarios": ["smoke/terminal.smoke.yaml"],
    },
    "continuation.manifest.yaml": {
        "screen": "loom.continuation",
        "mission": "Attach an existing repository, preserve lineage, approve a bounded delta, and rejoin teleology.",
        "mission_id": "loom-continuation",
        "elements": [
            {
                "id": "continuation-attach-btn",
                "classification": "action_control",
                "action": "intake.attach_project",
                "feedback_target": "continuation-feedback",
                "label": "Attach Existing Project",
            },
            {
                "id": "continuation-resume-btn",
                "classification": "action_control",
                "action": "intake.resume_session",
                "feedback_target": "continuation-feedback",
                "label": "Load Loom Lineage",
            },
            {
                "id": "continuation-kind-btn",
                "classification": "action_control",
                "action": "intake.session_kind_select",
                "feedback_target": "continuation-feedback",
                "label": "Select Continuation Policy",
            },
            {
                "id": "continuation-bootstrap-btn",
                "classification": "action_control",
                "action": "graph.bootstrap",
                "feedback_target": "continuation-feedback",
                "label": "Bootstrap Repository Graph",
            },
            {
                "id": "continuation-mode-btn",
                "classification": "action_control",
                "action": "interrogation.set_mode",
                "feedback_target": "continuation-feedback",
                "label": "Select Delta Interrogation Mode",
            },
            {
                "id": "continuation-answer-btn",
                "classification": "action_control",
                "action": "question.submit_answer",
                "feedback_target": "continuation-feedback",
                "label": "Submit Delta Answer",
            },
            {
                "id": "continuation-scope-btn",
                "classification": "action_control",
                "action": "continuation.confirm_scope",
                "feedback_target": "continuation-feedback",
                "label": "Confirm Evolution Scope",
            },
            {
                "id": "continuation-confirm-handoff-btn",
                "classification": "action_control",
                "action": "handoff.confirm",
                "feedback_target": "continuation-feedback",
                "label": "Confirm Continuation Handoff",
            },
            {
                "id": "continuation-accept-handoff-btn",
                "classification": "action_control",
                "action": "handoff.accept",
                "feedback_target": "continuation-feedback",
                "label": "Accept Continuation Handoff",
            },
            {
                "id": "continuation-lineage-display",
                "classification": "display",
                "contract_path": "loom.continuation.lineage",
                "label": "No project attached",
            },
            {
                "id": "continuation-graph-display",
                "classification": "display",
                "contract_path": "loom.continuation.graph_status",
                "label": "Graph unavailable",
            },
            {
                "id": "continuation-mode-display",
                "classification": "display",
                "contract_path": "loom.continuation.interrogation_mode",
                "label": "Interrogation policy unset",
            },
            {
                "id": "continuation-scope-display",
                "classification": "display",
                "contract_path": "loom.continuation.delta_scope",
                "label": "Delta scope unavailable",
            },
            {
                "id": "continuation-handoff-display",
                "classification": "display",
                "contract_path": "loom.continuation.handoff_state",
                "label": "Continuation handoff locked",
            },
            {
                "id": "continuation-feedback",
                "classification": "display",
                "contract_path": "loom.continuation.feedback",
                "label": "Continuation initialized",
                "tag": "output",
            },
        ],
        "knowledge_bindings": {
            d: f"loom.continuation.{d}"
            for d in ["design_intent", "behavioral", "operational", "governance", "institutional"]
        },
        "accessibility": {"profile": "wcag-aa-strict"},
        "smoke_scenarios": ["smoke/continuation.smoke.yaml"],
    },
    "deliverable-launch.manifest.yaml": {
        "screen": "loom.deliverable_launch",
        "mission": "Present the merged product, launch a runnable surface, and preserve lineage for future evolution.",
        "mission_id": "loom-deliverable-launch",
        "elements": [
            {
                "id": "deliverable-detect-btn",
                "classification": "action_control",
                "action": "deliverable.detect_surfaces",
                "feedback_target": "deliverable-feedback",
                "label": "Detect Runnable Surfaces",
            },
            {
                "id": "deliverable-present-btn",
                "classification": "action_control",
                "action": "deliverable.present",
                "feedback_target": "deliverable-feedback",
                "label": "Present Primary Launch",
            },
            {
                "id": "deliverable-open-terminal-btn",
                "classification": "action_control",
                "action": "deliverable.open_terminal",
                "feedback_target": "deliverable-feedback",
                "label": "Run in Terminal",
            },
            {
                "id": "deliverable-open-browser-btn",
                "classification": "action_control",
                "action": "deliverable.open_browser",
                "feedback_target": "deliverable-feedback",
                "label": "Open in Browser",
            },
            {
                "id": "deliverable-open-native-btn",
                "classification": "action_control",
                "action": "deliverable.open_native",
                "feedback_target": "deliverable-feedback",
                "label": "Open Native Application",
            },
            {
                "id": "deliverable-download-btn",
                "classification": "action_control",
                "action": "deliverable.download",
                "feedback_target": "deliverable-feedback",
                "label": "Download Archive",
            },
            {
                "id": "deliverable-diff-btn",
                "classification": "action_control",
                "action": "deliverable.view_diff",
                "feedback_target": "deliverable-feedback",
                "label": "Review Diff",
            },
            {
                "id": "deliverable-register-btn",
                "classification": "action_control",
                "action": "project.register_for_continuation",
                "feedback_target": "deliverable-feedback",
                "label": "Register Continuation Lineage",
            },
            {
                "id": "deliverable-card-display",
                "classification": "display",
                "contract_path": "loom.deliverable.launch_card",
                "label": "Launch presentation unavailable",
            },
            {
                "id": "deliverable-surface-display",
                "classification": "display",
                "contract_path": "loom.deliverable.surfaces",
                "label": "No surfaces detected",
            },
            {
                "id": "deliverable-run-display",
                "classification": "display",
                "contract_path": "loom.deliverable.run_status",
                "label": "No launch active",
            },
            {
                "id": "deliverable-change-display",
                "classification": "display",
                "contract_path": "loom.deliverable.changelog",
                "label": "Changelog unavailable",
            },
            {
                "id": "deliverable-lineage-display",
                "classification": "display",
                "contract_path": "loom.deliverable.lineage",
                "label": "Lineage not registered",
            },
            {
                "id": "deliverable-feedback",
                "classification": "display",
                "contract_path": "loom.deliverable.feedback",
                "label": "Deliverable Launch initialized",
                "tag": "output",
            },
        ],
        "knowledge_bindings": {
            d: f"loom.deliverable.{d}"
            for d in ["design_intent", "behavioral", "operational", "governance", "institutional"]
        },
        "accessibility": {"profile": "wcag-aa-strict"},
        "smoke_scenarios": ["smoke/deliverable-launch.smoke.yaml"],
    },
}

(SRC / "actions.registry.yaml").write_text(yaml.safe_dump(actions, sort_keys=False), encoding="utf-8")
(SRC / "knowledge.registry.yaml").write_text(yaml.safe_dump(knowledge, sort_keys=False), encoding="utf-8")
for name, data in manifests.items():
    (SRC / name).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
print("wrote", len(manifests), "manifests and registries")
