// GENERATED FILE - DO NOT EDIT. Regenerate from canonical sources.
"use strict";

function renderFallback(target, state, payload) {
  const detail = payload == null ? "" : ` ${JSON.stringify(payload)}`;
  target.textContent = `[${state}]${detail}`;
}

async function dispatchControl(control) {
  if (control.getAttribute("aria-busy") === "true") return;

  const actionId = control.dataset.action;
  const targetId = control.dataset.feedbackTarget;
  const target = document.getElementById(targetId);
  if (!actionId || !target) throw new Error("Invalid generated action binding.");
  if (!globalThis.LoomMirrorDriver?.dispatch) {
    throw new Error("LoomMirrorDriver.dispatch is not installed.");
  }

  control.setAttribute("aria-busy", "true");
  if ("disabled" in control) control.disabled = true;
  renderFallback(target, "pending", { action: actionId });

  try {
    const result = await globalThis.LoomMirrorDriver.dispatch(actionId);
    if (globalThis.LoomProjectionDriver?.project) {
      globalThis.LoomProjectionDriver.project(target.dataset.contractPath, result, target);
    } else {
      renderFallback(target, "succeeded", result);
    }
  } catch (error) {
    if (globalThis.LoomConsole?.surfaceError) {
      globalThis.LoomConsole.surfaceError(actionId, error, target);
    } else {
      renderFallback(target, "failed", { message: String(error?.message || error) });
    }
  } finally {
    control.setAttribute("aria-busy", "false");
    if ("disabled" in control) control.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('[data-classification="action_control"][data-action]').forEach((control) => {
    control.addEventListener("click", () => dispatchControl(control));
    if (control.tagName !== "BUTTON") {
      control.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          dispatchControl(control);
        }
      });
    }
  });
});
