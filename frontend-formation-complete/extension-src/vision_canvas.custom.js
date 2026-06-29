"use strict";

(function installScreenProjectionController() {
  const bindings = {
  "loom.vision.prompt": "vision-prompt-display",
  "loom.vision.current_question": "vision-question-display",
  "loom.vision.understanding": "vision-understanding-display",
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

  document.addEventListener("DOMContentLoaded", () => {
    project(Object.keys(bindings));
    const submitBtn = document.getElementById("vision-submit-answer-btn");
    if (submitBtn) {
      const textarea = document.createElement("textarea");
      textarea.id = "vision-answer-input";
      textarea.placeholder = "Type your answer here...";
      textarea.style.cssText = "grid-column: 1 / -1; min-height: 5rem; padding: 0.5rem; background: var(--loom-panel); color: var(--loom-text); border: 1px solid var(--loom-border); margin-bottom: 0.5rem; border-radius: 4px; font-family: inherit;";
      submitBtn.parentNode.insertBefore(textarea, submitBtn);
    }
  });
  document.addEventListener("loom:action-complete", (event) => {
    const changed = Array.isArray(event.detail?.changed) ? event.detail.changed : [];
    project(changed.filter((path) => Object.prototype.hasOwnProperty.call(bindings, path)));
  });
})();
