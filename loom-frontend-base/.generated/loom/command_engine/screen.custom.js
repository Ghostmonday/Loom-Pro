// GENERATED FILE - DO NOT EDIT. Regenerate from canonical sources.
"use strict";

(function installScreenProjectionController() {
  const bindings = {
  "loom.command.teleology_phase": "command-phase-display",
  "loom.command.topology": "command-topology-display",
  "loom.command.bridge_plan": "command-bridge-display",
  "loom.command.blueprint": "command-blueprint-display",
  "loom.command.approval_gate": "command-approval-display"
};

  function project(paths) {
    if (!globalThis.LoomProjectionDriver?.project) return;
    const unique = [...new Set(paths)];
    for (const path of unique) {
      const id = bindings[path];
      if (!id) continue;
      const target = document.getElementById(id);
      if (target) globalThis.LoomProjectionDriver.project(path, { state: "succeeded", action: "projection.refresh" }, target);
    }
  }

  document.addEventListener("DOMContentLoaded", () => project(Object.keys(bindings)));
  document.addEventListener("loom:action-complete", (event) => {
    const changed = Array.isArray(event.detail?.changed) ? event.detail.changed : [];
    project(changed.filter((path) => Object.prototype.hasOwnProperty.call(bindings, path)));
  });
})();
