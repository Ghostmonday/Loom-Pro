"""Deterministic scaffold generator for contract-bound frontend screens."""

from __future__ import annotations

import html
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from validator.engine import validate_project
from validator.parser.manifest_loader import (
    load_action_registry,
    load_knowledge_registry,
    load_manifest,
)


@dataclass
class GenerationError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def _humanize(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("_", "-").split("-") if part)


def _default_tag(element: dict[str, Any], feedback_targets: set[str]) -> str:
    if element.get("tag"):
        return element["tag"]
    classification = element["classification"]
    if classification == "action_control":
        return "button"
    if classification == "display" and element["id"] in feedback_targets:
        return "output"
    if classification == "display":
        return "div"
    if classification == "input_control":
        return "textarea"
    return "section"


def render_html(manifest: dict[str, Any]) -> str:
    feedback_targets = {
        element["feedback_target"]
        for element in manifest["elements"]
        if element["classification"] == "action_control"
    }
    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{html.escape(manifest['mission'])}</title>",
        '  <link rel="stylesheet" href="screen.css">',
        '  <link rel="stylesheet" href="screen.custom.css">',
        "</head>",
        "<body>",
        "  <main",
        '    id="screen-root"',
        f'    data-screen="{html.escape(manifest["screen"], quote=True)}"',
        f'    data-mission="{html.escape(manifest["mission_id"], quote=True)}"',
        '    class="workspace-shell"',
        "  >",
        f"    <h1>{html.escape(manifest['mission'])}</h1>",
    ]

    for element in manifest["elements"]:
        element_id = element["id"]
        classification = element["classification"]
        tag = _default_tag(element, feedback_targets)
        label = element.get("label") or _humanize(element_id)
        attrs = [
            f'id="{html.escape(element_id, quote=True)}"',
            f'data-classification="{classification}"',
        ]
        if classification == "action_control":
            attrs.extend([
                f'data-action="{html.escape(element["action"], quote=True)}"',
                f'data-feedback-target="{html.escape(element["feedback_target"], quote=True)}"',
                f'aria-label="{html.escape(label, quote=True)}"',
                'aria-busy="false"',
                'type="button"' if tag == "button" else 'role="button"',
            ])
            if tag != "button":
                attrs.append('tabindex="0"')
        elif classification == "display":
            attrs.append(f'data-contract-path="{html.escape(element["contract_path"], quote=True)}"')
            if element_id in feedback_targets:
                attrs.extend(['aria-live="polite"', 'aria-atomic="true"'])
        elif classification == "input_control":
            attrs.append(f'data-contract-path="{html.escape(element["contract_path"], quote=True)}"')
            if element.get("placeholder") is not None:
                attrs.append(f'placeholder="{html.escape(str(element["placeholder"]), quote=True)}"')
            if element.get("disabled") is True:
                attrs.append("disabled")
            if element.get("readonly") is True:
                attrs.append("readonly")
            if element.get("name"):
                attrs.append(f'name="{html.escape(element["name"], quote=True)}"')
            if tag == "input":
                attrs.append(f'type="{html.escape(element.get("type", "text"), quote=True)}"')

        if classification == "input_control":
            lines.append(f'    <label for="{html.escape(element_id, quote=True)}">{html.escape(label)}</label>')
            lines.append(f"    <{tag} {' '.join(attrs)}></{tag}>")
        else:
            lines.append(f"    <{tag} {' '.join(attrs)}>{html.escape(label)}</{tag}>")

    lines.extend([
        "  </main>",
        '  <script src="shell.js"></script>',
        '  <script src="screen.custom.js"></script>',
        "</body>",
        "</html>",
        "",
    ])
    return "\n".join(lines)


def render_js() -> str:
    return '''"use strict";

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
'''


def render_css() -> str:
    return ''':root {
  font-family: system-ui, sans-serif;
  line-height: 1.5;
}

body {
  margin: 0;
  padding: 2rem;
}

.workspace-shell {
  max-width: 64rem;
  margin: 0 auto;
  display: grid;
  gap: 1rem;
}

[data-classification="action_control"] {
  min-height: 2.75rem;
  padding: 0.65rem 1rem;
  cursor: pointer;
}

[data-classification="action_control"]:focus-visible {
  outline: 0.2rem solid currentColor;
  outline-offset: 0.2rem;
}

[data-classification="display"] {
  min-height: 1.5rem;
}

[data-classification="input_control"] {
  min-height: 2.75rem;
  padding: 0.65rem 1rem;
}

textarea[data-classification="input_control"] {
  min-height: 7rem;
}
'''


def _scenario_for(manifest: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    actions = [e for e in manifest["elements"] if e["classification"] == "action_control"]
    if not actions:
        raise GenerationError("Scaffold generation requires at least one action_control for a smoke flow.")
    action = actions[0]
    feedback_id = action["feedback_target"]
    feedback = next((e for e in manifest["elements"] if e["id"] == feedback_id), None)
    if not feedback or feedback.get("classification") != "display":
        raise GenerationError(f"Feedback target '{feedback_id}' must be a manifest display element.")

    return {
        "scenario": scenario_id,
        "screen": manifest["screen"],
        "steps": [
            {"kind": "assert_initial_state", "target": feedback_id, "expected": {"present": True}},
            {"kind": "perform_interaction", "target": action["id"]},
            {"kind": "assert_intermediate_feedback", "target": feedback_id, "expected": {"state": "pending"}},
            {"kind": "assert_terminal_state", "target": feedback_id, "expected": {"any_of": ["succeeded", "failed"]}},
            {"kind": "assert_contract_projection", "target": feedback["contract_path"], "expected": {"observable": True}},
            {"kind": "assert_accessibility_state", "target": action["id"], "expected": {"accessible_name": True}},
            {"kind": "assert_no_prohibited_side_effect", "target": action["id"], "expected": {"inline_handlers": False}},
        ],
    }


def generate_scaffold(
    manifest_path: str | Path,
    actions_path: str | Path,
    knowledge_path: str | Path,
    output_dir: str | Path,
    schema_dir: str | Path,
    force: bool = False,
):
    manifest_path = Path(manifest_path).resolve()
    actions_path = Path(actions_path).resolve()
    knowledge_path = Path(knowledge_path).resolve()
    output_dir = Path(output_dir).resolve()
    schema_dir = Path(schema_dir).resolve()

    manifest = load_manifest(manifest_path, schema_dir)
    actions = load_action_registry(actions_path, schema_dir)
    knowledge = load_knowledge_registry(knowledge_path, schema_dir)

    preserved = {}
    if output_dir.exists() and any(output_dir.iterdir()):
        if not force:
            raise GenerationError(f"Output directory is not empty: {output_dir}. Use --force to replace generated files.")
        for name in ("screen.custom.css", "screen.custom.js"):
            path = output_dir / name
            if path.exists():
                preserved[name] = path.read_text(encoding="utf-8")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "index.html").write_text(render_html(manifest), encoding="utf-8")
    (output_dir / "shell.js").write_text(render_js(), encoding="utf-8")
    (output_dir / "screen.css").write_text(render_css(), encoding="utf-8")
    (output_dir / "screen.custom.css").write_text(preserved.get("screen.custom.css", ""), encoding="utf-8")
    (output_dir / "screen.custom.js").write_text(preserved.get("screen.custom.js", ""), encoding="utf-8")
    (output_dir / "screen.manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (output_dir / "actions.registry.yaml").write_text(yaml.safe_dump(actions, sort_keys=False), encoding="utf-8")
    (output_dir / "knowledge.registry.yaml").write_text(yaml.safe_dump(knowledge, sort_keys=False), encoding="utf-8")

    for index, relative_path in enumerate(manifest["smoke_scenarios"], start=1):
        target = output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        scenario_id = f"{manifest['screen']}.smoke-{index}"
        target.write_text(yaml.safe_dump(_scenario_for(manifest, scenario_id), sort_keys=False), encoding="utf-8")

    project = {
        "rule_set_version": "1.0.0",
        "action_registry": "actions.registry.yaml",
        "knowledge_registry": "knowledge.registry.yaml",
        "screens": [{"manifest": "screen.manifest.yaml", "html": "index.html"}],
    }
    (output_dir / "frontend-formation.yaml").write_text(yaml.safe_dump(project, sort_keys=False), encoding="utf-8")

    result = validate_project(output_dir / "frontend-formation.yaml", schema_dir)
    if not result.passed:
        diagnostics = "\n".join(v.format() for v in result.violations)
        raise GenerationError(f"Generator closure failure: generated output did not validate.\n{diagnostics}")
    return result
