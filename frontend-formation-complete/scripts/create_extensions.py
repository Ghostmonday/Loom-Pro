from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / 'extension-src'

screen_maps = {
    'vision_canvas': {
        'loom.vision.prompt':'vision-prompt-display',
        'loom.vision.current_question':'vision-question-display',
        'loom.vision.understanding':'vision-understanding-display',
        'loom.vision.readiness':'vision-readiness-display',
        'loom.vision.handoff_state':'vision-handoff-display',
    },
    'command_engine': {
        'loom.command.teleology_phase':'command-phase-display',
        'loom.command.topology':'command-topology-display',
        'loom.command.bridge_plan':'command-bridge-display',
        'loom.command.blueprint':'command-blueprint-display',
        'loom.command.approval_gate':'command-approval-display',
    },
    'terminal': {
        'loom.terminal.phase':'terminal-phase-display',
        'loom.terminal.swarm':'terminal-swarm-display',
        'loom.terminal.grid':'terminal-grid-display',
        'loom.terminal.merge':'terminal-merge-display',
        'loom.terminal.deliverable':'terminal-deliverable-display',
    },
    'continuation': {
        'loom.continuation.lineage':'continuation-lineage-display',
        'loom.continuation.graph_status':'continuation-graph-display',
        'loom.continuation.interrogation_mode':'continuation-mode-display',
        'loom.continuation.delta_scope':'continuation-scope-display',
        'loom.continuation.handoff_state':'continuation-handoff-display',
    },
    'deliverable_launch': {
        'loom.deliverable.launch_card':'deliverable-card-display',
        'loom.deliverable.surfaces':'deliverable-surface-display',
        'loom.deliverable.run_status':'deliverable-run-display',
        'loom.deliverable.changelog':'deliverable-change-display',
        'loom.deliverable.lineage':'deliverable-lineage-display',
    },
}

js_template = '''"use strict";

(function installScreenProjectionController() {{
  const bindings = {bindings};

  function project(paths) {{
    if (!globalThis.LoomProjectionDriver?.project) return;
    const unique = [...new Set(paths)];
    for (const path of unique) {{
      const id = bindings[path];
      if (!id) continue;
      const target = document.getElementById(id);
      if (target) globalThis.LoomProjectionDriver.project(path, {{ state: "succeeded", action: "projection.refresh" }}, target);
    }}
  }}

  document.addEventListener("DOMContentLoaded", () => project(Object.keys(bindings)));
  document.addEventListener("loom:action-complete", (event) => {{
    const changed = Array.isArray(event.detail?.changed) ? event.detail.changed : [];
    project(changed.filter((path) => Object.prototype.hasOwnProperty.call(bindings, path)));
  }});
}})();
'''

for name, bindings in screen_maps.items():
    (EXT / f'{name}.custom.js').write_text(js_template.format(bindings=json.dumps(bindings, indent=2)), encoding='utf-8')

base = '''
:root {
  --loom-bg: #08090c;
  --loom-panel: #11141a;
  --loom-panel-strong: #171c24;
  --loom-border: #354154;
  --loom-text: #f1f5f9;
  --loom-muted: #a8b3c3;
  --loom-accent: ACCENT;
  --loom-danger: #ff5c7a;
  --loom-focus: #f8e16c;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 1.25rem;
  background: var(--loom-bg);
  color: var(--loom-text);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 0.875rem;
  line-height: 1.45;
}
.workspace-shell {
  display: grid;
  grid-template-columns: minmax(15rem, 21rem) minmax(0, 1fr);
  gap: 0.8rem;
  max-width: 92rem;
  margin: 0 auto;
}
h1 {
  grid-column: 1 / -1;
  margin: 0 0 0.4rem;
  padding: 0.85rem 1rem;
  border: 2px solid var(--loom-accent);
  background: var(--loom-panel-strong);
  color: var(--loom-accent);
  font-size: 1rem;
  line-height: 1.5;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
[data-classification="action_control"] {
  grid-column: 1;
  min-height: 3rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--loom-border);
  border-left: 4px solid var(--loom-accent);
  background: var(--loom-panel);
  color: var(--loom-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
[data-classification="action_control"]:hover { background: var(--loom-panel-strong); }
[data-classification="action_control"]:focus-visible {
  outline: 3px solid var(--loom-focus);
  outline-offset: 2px;
}
[data-classification="action_control"][aria-busy="true"] { opacity: 0.72; cursor: progress; }
[data-classification="display"] {
  grid-column: 2;
  min-width: 0;
  min-height: 3rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--loom-border);
  background: var(--loom-panel);
  color: var(--loom-muted);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
[data-contract-path$="feedback"] {
  grid-column: 1 / -1;
  border-left: 5px solid var(--loom-accent);
  color: var(--loom-text);
}
[data-current-state="rejected"], [data-current-state="failed"] {
  border-left-color: var(--loom-danger);
  color: #ffd5dd;
}
@media (max-width: 58rem) {
  body { padding: 0.7rem; }
  .workspace-shell { grid-template-columns: 1fr; }
  h1, [data-classification="action_control"], [data-classification="display"] { grid-column: 1; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; animation: none !important; }
}
'''
accents = {
    'vision_canvas':'#50e3a4',
    'command_engine':'#65d9ff',
    'terminal':'#f6c85f',
    'continuation':'#bd93f9',
    'deliverable_launch':'#ff8f70',
}

for name, accent in accents.items():
    extra = ''
    if name == 'terminal':
        extra = '\n#terminal-grid-display, #terminal-merge-display { background: #05070a; color: #a7f3d0; }\n'
    if name == 'command_engine':
        extra = '\n#command-topology-display, #command-bridge-display { background: #071016; color: #a5f3fc; }\n'
    if name == 'continuation':
        extra = '\n#continuation-scope-display { border-style: dashed; }\n'
    if name == 'deliverable_launch':
        extra = '\n#deliverable-card-display { border-width: 2px; color: var(--loom-text); }\n'
    (EXT / f'{name}.custom.css').write_text(base.replace('ACCENT', accent) + extra, encoding='utf-8')

print('created', len(screen_maps), 'custom JS and CSS pairs')
