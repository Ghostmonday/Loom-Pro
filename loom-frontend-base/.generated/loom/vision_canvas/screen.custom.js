// GENERATED FILE - DO NOT EDIT. Regenerate from canonical sources.
"use strict";

(function installScreenProjectionController() {
  const bindings = {
  "loom.vision.prompt": "vision-prompt-display",
  "loom.vision.current_question": "vision-question-display",
  "loom.vision.current_answer": "vision-answer-input",
  "loom.vision.understanding": "vision-history-display",
  "loom.vision.answer_revision": "vision-revision-editor",
  "loom.vision.readiness": "vision-readiness-display",
  "loom.vision.handoff_state": "vision-handoff-display"
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
