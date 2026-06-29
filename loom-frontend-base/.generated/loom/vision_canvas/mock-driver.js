// GENERATED FILE - DO NOT EDIT. Regenerate from canonical sources.
/**
 * Deterministic Loom contract driver.
 *
 * This is a browser verification fixture, not a substitute for the real API.
 * It preserves canonical phase order, gates, action-specific projections, and
 * cross-surface state through localStorage on one origin.
 */
"use strict";

(function installLoomContractDriver() {
  const STORAGE_KEY = "loom.frontend.contract-fixture.v1";
  const FIXED_DELAY_MS = 120;

  const DEFAULT_STATE = Object.freeze({
    vision: {
      prompt: "Build a local-first software system with explicit authority gates.",
      session_status: "CREATED",
      current_question: "No active question.",
      understanding: "No evidence recorded.",
      readiness: 0,
      answer_count: 0,
      handoff_confirmed: false,
      handed_off: false,
      executable_projection: false
    },
    command: {
      teleology_phase: "idle",
      teleology_complete: false,
      topology: "No teleology receipt.",
      bridge_plan: "No dark-bridge analysis.",
      synthesis_complete: false,
      blueprint: "No synthesized blueprint.",
      blueprint_approved: false,
      prepared: false
    },
    terminal: {
      phase: "awaiting_preparation",
      recommended_swarm: 3,
      workers: 0,
      swarm_assigned: false,
      sprint_status: "idle",
      worker_statuses: [],
      merge_phase: "idle",
      merged: 0,
      blocked: 0,
      conflicted: 0,
      deliverable_ready: false
    },
    continuation: {
      attached: false,
      repo_path: "/workspace/existing-project",
      parent_session_id: null,
      blueprint_version: 0,
      session_kind: "continuation",
      graph_ready: false,
      repository_fingerprint: null,
      interrogation_mode: "unset",
      delta_answered: false,
      scope_confirmed: false,
      handoff_confirmed: false,
      handed_off: false
    },
    deliverable: {
      detected_surfaces: [],
      primary_surface: null,
      presented: false,
      run_state: "idle",
      run_target: null,
      lineage_registered: false
    }
  });

  function cloneDefault() {
    return JSON.parse(JSON.stringify(DEFAULT_STATE));
  }

  function loadState() {
    try {
      const raw = globalThis.localStorage?.getItem(STORAGE_KEY);
      return raw ? { ...cloneDefault(), ...JSON.parse(raw) } : cloneDefault();
    } catch (_error) {
      return cloneDefault();
    }
  }

  function saveState(state) {
    globalThis.localStorage?.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function screenId() {
    return document.getElementById("screen-root")?.dataset.screen || "unknown";
  }

  function pause() {
    return new Promise((resolve) => setTimeout(resolve, FIXED_DELAY_MS));
  }

  function success(action, changed, payload = {}, mode = "contract_fixture") {
    return {
      state: "succeeded",
      status: "success",
      action,
      screen: screenId(),
      changed,
      mode,
      payload
    };
  }

  function reject(action, message, changed = []) {
    const error = new Error(message);
    error.loomState = "rejected";
    error.action = action;
    error.screen = screenId();
    error.changed = changed;
    throw error;
  }

  function requireGate(condition, action, message, changed = []) {
    if (!condition) reject(action, message, changed);
  }

  function currentState() {
    return loadState();
  }

  globalThis.LoomMirrorDriver = {
    async dispatch(actionId) {
      await pause();
      const state = loadState();
      const screen = screenId();

      switch (actionId) {
        case "intake.start_session": {
          state.vision.session_status = "QUESTIONING";
          state.vision.current_question = "Which authority boundaries must the system enforce without exception?";
          state.vision.understanding = "Prompt accepted; evidence-state analysis initialized.";
          state.vision.readiness = 0.25;
          saveState(state);
          return success(actionId, [
            "loom.vision.prompt",
            "loom.vision.current_question",
            "loom.vision.understanding",
            "loom.vision.readiness",
            "loom.vision.handoff_state"
          ], { session_status: state.vision.session_status }, "real_api_fixture");
        }

        case "question.submit_answer": {
          if (screen === "loom.continuation") {
            requireGate(state.continuation.attached, actionId, "GATE_REFUSAL: attach a repository before delta interrogation.", ["loom.continuation.handoff_state"]);
            state.continuation.delta_answered = true;
            state.continuation.interrogation_mode = state.continuation.graph_ready ? "delta" : "full";
            saveState(state);
            return success(actionId, ["loom.continuation.interrogation_mode", "loom.continuation.delta_scope"], { answer_recorded: true }, "real_api_with_continuation_fixture");
          }

          requireGate(state.vision.session_status === "QUESTIONING", actionId, "GATE_REFUSAL: no active Intent Forge question.", ["loom.vision.current_question"]);
          state.vision.answer_count += 1;
          if (state.vision.answer_count === 1) {
            state.vision.readiness = 0.58;
            state.vision.current_question = "What failure or refusal states must remain distinct in the final system?";
            state.vision.understanding = "Authority boundaries confirmed; failure semantics remain unresolved.";
          } else {
            state.vision.readiness = 0.91;
            state.vision.current_question = "Interrogation complete; review readiness and confirm handoff.";
            state.vision.understanding = "Authority, failure semantics, and operational intent confirmed.";
            state.vision.session_status = "FINALIZED";
          }
          saveState(state);
          return success(actionId, [
            "loom.vision.current_question",
            "loom.vision.understanding",
            "loom.vision.readiness",
            "loom.vision.handoff_state"
          ], { answer_count: state.vision.answer_count, session_status: state.vision.session_status }, "real_api_fixture");
        }

        case "question.revise_answer": {
          requireGate(screen === "loom.vision_canvas", actionId, "GATE_REFUSAL: answer revision belongs to the Vision Canvas.");
          requireGate(state.vision.answer_count > 0, actionId, "GATE_REFUSAL: no recorded answer exists to revise.", ["loom.vision.understanding"]);
          state.vision.understanding = "Previous answer revised; full evidence-state reanalysis completed.";
          state.vision.readiness = Math.max(0.5, state.vision.readiness - 0.05);
          saveState(state);
          return success(actionId, ["loom.vision.understanding", "loom.vision.readiness"], { revised: true }, "real_api_fixture");
        }

        case "question.finalize": {
          requireGate(screen === "loom.vision_canvas", actionId, "GATE_REFUSAL: finalization belongs to the Vision Canvas.");
          requireGate(["QUESTIONING", "VALIDATING"].includes(state.vision.session_status) && state.vision.readiness >= 0.8, actionId, "GATE_REFUSAL: sufficient readiness is required before finalization.", ["loom.vision.handoff_state"]);
          state.vision.session_status = "FINAL_CONFIRMATION";
          state.vision.current_question = "Final confirmation requested; confirm handoff readiness.";
          saveState(state);
          return success(actionId, [
            "loom.vision.current_question",
            "loom.vision.handoff_state"
          ], { session_status: state.vision.session_status }, "real_api_fixture");
        }

        case "handoff.confirm": {
          if (screen === "loom.continuation") {
            requireGate(state.continuation.scope_confirmed, actionId, "GATE_REFUSAL: approve a version-matched delta scope before handoff.", ["loom.continuation.handoff_state"]);
            state.continuation.handoff_confirmed = true;
            saveState(state);
            return success(actionId, ["loom.continuation.handoff_state"], { confirmed: true }, "contract_fixture");
          }
          requireGate(["FINAL_CONFIRMATION", "FINALIZED"].includes(state.vision.session_status) && state.vision.readiness >= 0.8, actionId, "GATE_REFUSAL: readiness and FINALIZED status are required before confirmation.", ["loom.vision.handoff_state"]);
          state.vision.handoff_confirmed = true;
          state.vision.executable_projection = true;
          saveState(state);
          return success(actionId, ["loom.vision.handoff_state"], { executable_projection: true }, "real_api_fixture");
        }

        case "handoff.accept": {
          if (screen === "loom.continuation") {
            requireGate(state.continuation.handoff_confirmed, actionId, "GATE_REFUSAL: continuation handoff must be confirmed first.", ["loom.continuation.handoff_state"]);
            state.continuation.handed_off = true;
            saveState(state);
            return success(actionId, ["loom.continuation.handoff_state"], { session_status: "HANDED_OFF" }, "contract_fixture");
          }
          requireGate(state.vision.handoff_confirmed && state.vision.executable_projection, actionId, "GATE_REFUSAL: confirmed executable projection required.", ["loom.vision.handoff_state"]);
          state.vision.handed_off = true;
          state.vision.session_status = "HANDED_OFF";
          saveState(state);
          return success(actionId, ["loom.vision.handoff_state"], { session_status: "HANDED_OFF" }, "real_api_fixture");
        }

        case "teleology.deliberate": {
          requireGate(state.vision.handed_off || state.continuation.handed_off, actionId, "GATE_REFUSAL: teleology requires a canonical handoff.", ["loom.command.approval_gate"]);
          state.command.teleology_phase = "blueprint_freeze";
          state.command.teleology_complete = true;
          state.command.topology = "curvature_floor=-0.30; nodes=18; partitions=4";
          state.command.bridge_plan = "dark_bridges=1; welds=3; handoff_gateways=1";
          saveState(state);
          return success(actionId, ["loom.command.teleology_phase", "loom.command.topology", "loom.command.bridge_plan", "loom.command.approval_gate"], { subphase: "blueprint_freeze" }, "real_sse_fixture");
        }

        case "blueprint.synthesize": {
          requireGate(state.command.teleology_complete, actionId, "GATE_REFUSAL: teleology must reach blueprint_freeze before synthesis.", ["loom.command.approval_gate"]);
          state.command.synthesis_complete = true;
          state.command.blueprint = "projection_mode=loom_synthesis; work_units=4; dark_bridge_count=1";
          saveState(state);
          return success(actionId, ["loom.command.blueprint", "loom.command.approval_gate"], { work_units: 4, projection_mode: "loom_synthesis" }, "real_api_fixture");
        }

        case "orchestrate.prepare": {
          requireGate(state.command.synthesis_complete && (state.vision.handed_off || state.continuation.handed_off), actionId, "GATE_REFUSAL: handed-off synthesized blueprint required before prepare.", ["loom.command.approval_gate"]);
          state.command.blueprint_approved = true;
          state.command.prepared = true;
          state.terminal.phase = "awaiting_swarm";
          saveState(state);
          return success(actionId, ["loom.command.approval_gate", "loom.command.blueprint"], { recommended_swarm: state.terminal.recommended_swarm }, "real_api_fixture");
        }

        case "orchestrate.swarm": {
          requireGate(state.command.prepared, actionId, "GATE_REFUSAL: prepare and blueprint approval are required before swarm assignment.", ["loom.terminal.phase"]);
          state.terminal.workers = state.terminal.recommended_swarm;
          state.terminal.swarm_assigned = true;
          state.terminal.phase = "ready_to_deploy";
          saveState(state);
          return success(actionId, ["loom.terminal.phase", "loom.terminal.swarm"], { workers: state.terminal.workers }, "real_api_fixture");
        }

        case "deploy.sprint": {
          requireGate(state.terminal.swarm_assigned && state.command.blueprint_approved, actionId, "GATE_REFUSAL: approved blueprint and assigned swarm required for atomic sprint.", ["loom.terminal.phase"]);
          state.terminal.phase = "complete";
          state.terminal.sprint_status = "completed";
          state.terminal.worker_statuses = ["worker-001:completed", "worker-002:completed", "worker-003:completed"];
          saveState(state);
          return success(actionId, ["loom.terminal.phase", "loom.terminal.grid"], { sprint_status: "completed" }, "real_api_sequence_fixture");
        }

        case "grid.poll_status": {
          requireGate(state.terminal.sprint_status !== "idle", actionId, "GATE_REFUSAL: no sprint exists to poll.", ["loom.terminal.grid"]);
          return success(actionId, ["loom.terminal.grid", "loom.terminal.phase"], { sprint_status: state.terminal.sprint_status }, "real_api_fixture");
        }

        case "merge.run": {
          requireGate(state.terminal.sprint_status === "completed", actionId, "GATE_REFUSAL: every worker must be terminal before merge.", ["loom.terminal.merge"]);
          state.terminal.merge_phase = "completed";
          state.terminal.merged = 3;
          state.terminal.blocked = 0;
          state.terminal.conflicted = 0;
          state.terminal.deliverable_ready = true;
          saveState(state);
          return success(actionId, ["loom.terminal.merge", "loom.terminal.deliverable", "loom.terminal.phase"], { merged: 3, blocked: 0, conflicted: 0 }, "real_api_fixture");
        }

        case "merge.poll_status": {
          requireGate(state.terminal.merge_phase !== "idle", actionId, "GATE_REFUSAL: merge has not started.", ["loom.terminal.merge"]);
          return success(actionId, ["loom.terminal.merge", "loom.terminal.deliverable"], { phase: state.terminal.merge_phase }, "real_api_fixture");
        }

        case "deliverable.download": {
          requireGate(state.terminal.deliverable_ready, actionId, "GATE_REFUSAL: clean completed merge required before download.", ["loom.terminal.deliverable", "loom.deliverable.launch_card"]);
          return success(actionId, screen === "loom.terminal" ? ["loom.terminal.deliverable"] : ["loom.deliverable.launch_card"], { filename: "loom-deliverable.zip", checksum: "sha256:fixture" }, "real_api_fixture");
        }

        case "deliverable.view_diff": {
          requireGate(state.terminal.deliverable_ready, actionId, "GATE_REFUSAL: completed merge required before diff review.", ["loom.terminal.deliverable", "loom.deliverable.changelog"]);
          return success(actionId, screen === "loom.terminal" ? ["loom.terminal.deliverable"] : ["loom.deliverable.changelog"], { files_changed: 12 }, "real_api_fixture");
        }

        case "intake.attach_project": {
          state.continuation.attached = true;
          state.continuation.parent_session_id = "loom-parent-001";
          state.continuation.blueprint_version = 4;
          saveState(state);
          return success(actionId, ["loom.continuation.lineage", "loom.continuation.graph_status", "loom.continuation.handoff_state"], { repository_fingerprint: "fixture:9d31" }, "contract_fixture");
        }

        case "intake.resume_session": {
          requireGate(state.continuation.attached, actionId, "GATE_REFUSAL: attach the repository before loading lineage.", ["loom.continuation.lineage"]);
          return success(actionId, ["loom.continuation.lineage"], { parent_session_id: state.continuation.parent_session_id }, "contract_fixture");
        }

        case "intake.session_kind_select": {
          requireGate(state.continuation.attached, actionId, "GATE_REFUSAL: attach the repository before selecting evolution policy.", ["loom.continuation.interrogation_mode"]);
          const order = ["continuation", "hotfix", "v2", "refactor"];
          const index = order.indexOf(state.continuation.session_kind);
          state.continuation.session_kind = order[(index + 1) % order.length];
          saveState(state);
          return success(actionId, ["loom.continuation.lineage", "loom.continuation.interrogation_mode"], { session_kind: state.continuation.session_kind }, "contract_fixture");
        }

        case "graph.bootstrap": {
          requireGate(state.continuation.attached, actionId, "GATE_REFUSAL: attached repository required before graph bootstrap.", ["loom.continuation.graph_status"]);
          state.continuation.graph_ready = true;
          state.continuation.repository_fingerprint = "fixture:9d31";
          saveState(state);
          return success(actionId, ["loom.continuation.graph_status", "loom.continuation.interrogation_mode"], { graph_status: "GRAPH_READY" }, "real_cli_fixture");
        }

        case "interrogation.set_mode": {
          requireGate(state.continuation.graph_ready, actionId, "GATE_REFUSAL: graph readiness is required before interrogation policy selection.", ["loom.continuation.interrogation_mode"]);
          state.continuation.interrogation_mode = state.continuation.blueprint_version > 0 ? "skip_if_graph_ready" : "delta";
          saveState(state);
          return success(actionId, ["loom.continuation.interrogation_mode", "loom.continuation.delta_scope"], { mode: state.continuation.interrogation_mode }, "contract_fixture");
        }

        case "continuation.confirm_scope": {
          requireGate(state.continuation.graph_ready && (state.continuation.delta_answered || state.continuation.interrogation_mode === "skip_if_graph_ready"), actionId, "GATE_REFUSAL: graph-ready bounded delta required before scope approval.", ["loom.continuation.delta_scope", "loom.continuation.handoff_state"]);
          state.continuation.scope_confirmed = true;
          saveState(state);
          return success(actionId, ["loom.continuation.delta_scope", "loom.continuation.handoff_state"], { approved_operations: ["MODIFY", "ADD", "DEPRECATE"] }, "contract_fixture");
        }

        case "deliverable.detect_surfaces": {
          requireGate(state.terminal.merge_phase === "completed" && state.terminal.blocked === 0 && state.terminal.conflicted === 0, actionId, "GATE_REFUSAL: a clean completed merge is required before surface detection.", ["loom.deliverable.launch_card"]);
          state.deliverable.detected_surfaces = ["web", "terminal"];
          state.deliverable.primary_surface = "web";
          saveState(state);
          return success(actionId, ["loom.deliverable.launch_card", "loom.deliverable.surfaces", "loom.deliverable.changelog"], { primary_surface: "web" }, "contract_fixture");
        }

        case "deliverable.present": {
          requireGate(state.deliverable.detected_surfaces.length > 0, actionId, "GATE_REFUSAL: detect runnable surfaces before presentation.", ["loom.deliverable.launch_card"]);
          state.deliverable.presented = true;
          saveState(state);
          return success(actionId, ["loom.deliverable.launch_card", "loom.deliverable.surfaces", "loom.deliverable.run_status"], { primary_surface: state.deliverable.primary_surface }, "contract_fixture");
        }

        case "deliverable.open_terminal":
        case "deliverable.open_browser":
        case "deliverable.open_native": {
          requireGate(state.deliverable.presented, actionId, "GATE_REFUSAL: launch presentation must be established first.", ["loom.deliverable.run_status"]);
          const surface = {
            "deliverable.open_terminal": "terminal",
            "deliverable.open_browser": "web",
            "deliverable.open_native": "native"
          }[actionId];
          requireGate(state.deliverable.detected_surfaces.includes(surface), actionId, `GATE_REFUSAL: ${surface} is not a detected runnable surface.`, ["loom.deliverable.surfaces", "loom.deliverable.run_status"]);
          state.deliverable.run_state = "succeeded";
          state.deliverable.run_target = surface;
          saveState(state);
          return success(actionId, ["loom.deliverable.run_status", "loom.deliverable.launch_card"], { surface }, "contract_fixture");
        }

        case "project.register_for_continuation": {
          requireGate(state.deliverable.run_state === "succeeded" && state.terminal.deliverable_ready, actionId, "GATE_REFUSAL: successful launch and merge receipt required before lineage registration.", ["loom.deliverable.lineage"]);
          state.deliverable.lineage_registered = true;
          saveState(state);
          return success(actionId, ["loom.deliverable.lineage"], { continuation_route: "/continuation" }, "contract_fixture");
        }

        default: {
          const error = new Error(`Undeclared action implementation: ${actionId}`);
          error.loomState = "failed";
          error.action = actionId;
          error.screen = screen;
          error.changed = [];
          throw error;
        }
      }
    },

    snapshot: currentState,

    reset() {
      const state = cloneDefault();
      saveState(state);
      return state;
    }
  };

  function percent(value) {
    return `${Math.round(Number(value || 0) * 100)}%`;
  }

  globalThis.LoomProjectionDriver = {
    project(contractPath, result, targetElement) {
      if (!targetElement) return;
      const state = loadState();

      if (contractPath.endsWith(".feedback")) {
        const terminalState = result?.state || "succeeded";
        const mode = result?.mode ? ` mode=${result.mode}` : "";
        targetElement.textContent = `[${terminalState}] ${result?.action || "action"}${mode}`;
        targetElement.dataset.currentState = terminalState;
        document.dispatchEvent(new CustomEvent("loom:action-complete", { detail: result }));
        return;
      }

      const renders = {
        "loom.vision.prompt": () => `[VISION] ${state.vision.prompt}`,
        "loom.vision.current_question": () => `[QUESTION] ${state.vision.current_question}`,
        "loom.vision.understanding": () => `[UNDERSTANDING] ${state.vision.understanding}`,
        "loom.vision.readiness": () => `[READINESS] ${percent(state.vision.readiness)} | status=${state.vision.session_status}`,
        "loom.vision.handoff_state": () => `[HANDOFF] confirmed=${state.vision.handoff_confirmed} accepted=${state.vision.handed_off} projection=${state.vision.executable_projection}`,

        "loom.command.teleology_phase": () => `[TELEOLOGY] phase=${state.command.teleology_phase} complete=${state.command.teleology_complete}`,
        "loom.command.topology": () => `[TOPOLOGY] ${state.command.topology}`,
        "loom.command.bridge_plan": () => `[BRIDGE PLAN] ${state.command.bridge_plan}`,
        "loom.command.blueprint": () => `[BLUEPRINT] ${state.command.blueprint}`,
        "loom.command.approval_gate": () => `[APPROVAL] synthesized=${state.command.synthesis_complete} approved=${state.command.blueprint_approved} prepared=${state.command.prepared}`,

        "loom.terminal.phase": () => `[PHASE] ${state.terminal.phase} | sprint=${state.terminal.sprint_status}`,
        "loom.terminal.swarm": () => `[SWARM] recommended=${state.terminal.recommended_swarm} assigned=${state.terminal.workers}`,
        "loom.terminal.grid": () => `[GRID]\n${state.terminal.worker_statuses.length ? state.terminal.worker_statuses.join("\n") : "No workers active."}`,
        "loom.terminal.merge": () => `[MERGE] phase=${state.terminal.merge_phase} merged=${state.terminal.merged} blocked=${state.terminal.blocked} conflicted=${state.terminal.conflicted}`,
        "loom.terminal.deliverable": () => `[DELIVERABLE] ready=${state.terminal.deliverable_ready} archive=loom-deliverable.zip diff=available_after_merge`,

        "loom.continuation.lineage": () => `[LINEAGE] attached=${state.continuation.attached} repo=${state.continuation.repo_path} parent=${state.continuation.parent_session_id || "none"} version=${state.continuation.blueprint_version} kind=${state.continuation.session_kind}`,
        "loom.continuation.graph_status": () => `[GRAPH] ready=${state.continuation.graph_ready} fingerprint=${state.continuation.repository_fingerprint || "none"}`,
        "loom.continuation.interrogation_mode": () => `[INTERROGATION] mode=${state.continuation.interrogation_mode} delta_answered=${state.continuation.delta_answered}`,
        "loom.continuation.delta_scope": () => `[DELTA SCOPE] ${state.continuation.scope_confirmed ? "APPROVED MODIFY→ADD→DEPRECATE" : "awaiting graph-ready bounded scope"}`,
        "loom.continuation.handoff_state": () => `[HANDOFF] scope=${state.continuation.scope_confirmed} confirmed=${state.continuation.handoff_confirmed} accepted=${state.continuation.handed_off}`,

        "loom.deliverable.launch_card": () => `[LAUNCH] ready=${state.terminal.deliverable_ready} presented=${state.deliverable.presented} primary=${state.deliverable.primary_surface || "none"}`,
        "loom.deliverable.surfaces": () => `[SURFACES] ${state.deliverable.detected_surfaces.length ? state.deliverable.detected_surfaces.join(", ") : "none"}`,
        "loom.deliverable.run_status": () => `[RUN] state=${state.deliverable.run_state} target=${state.deliverable.run_target || "none"}`,
        "loom.deliverable.changelog": () => `[CHANGELOG] added=4 modified=7 deprecated=1 tests=passed merge_receipt=${state.terminal.merge_phase}`,
        "loom.deliverable.lineage": () => `[LINEAGE] registered=${state.deliverable.lineage_registered} continuation_route=/continuation`
      };

      targetElement.textContent = renders[contractPath] ? renders[contractPath]() : `[UNBOUND] ${contractPath}`;
    }
  };

  globalThis.LoomConsole = {
    surfaceError(actionId, error, targetElement) {
      if (!targetElement) return;
      const terminalState = error?.loomState || "failed";
      const detail = {
        state: terminalState,
        status: terminalState,
        action: actionId,
        screen: error?.screen || screenId(),
        changed: Array.isArray(error?.changed) ? error.changed : [],
        mode: "gate_enforced",
        payload: { message: String(error?.message || error) }
      };
      targetElement.textContent = `[${terminalState}] ${actionId}: ${detail.payload.message}`;
      targetElement.dataset.currentState = terminalState;
      document.dispatchEvent(new CustomEvent("loom:action-complete", { detail }));
    }
  };
})();
