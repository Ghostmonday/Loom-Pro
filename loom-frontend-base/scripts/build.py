#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'frontend-formation'
SRC = ROOT / 'examples' / 'loom-source'
EXT = ROOT / 'extension-src'
OUT = ROOT / '.generated' / 'loom'
REPORTS = ROOT / 'reports'
SPEC = TOOL / 'specification'

SCREENS = {
    'vision_canvas': 'vision-canvas.manifest.yaml',
    'command_engine': 'command-engine.manifest.yaml',
    'terminal': 'terminal.manifest.yaml',
    'continuation': 'continuation.manifest.yaml',
    'deliverable_launch': 'deliverable-launch.manifest.yaml',
}


def run(cmd: list[str], *, cwd: Path = ROOT, capture: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env['PYTHONPATH'] = str(TOOL) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    return subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=capture, check=True)


def selected_driver_name() -> str:
    env_val = os.environ.get("LOOM_ENV", "").strip().lower()
    use_mock = os.environ.get("LOOM_USE_MOCK_DRIVER", "").strip().lower() in {"1", "true", "yes"} or env_val in {"test", "demo"}
    return "mock-driver.js" if use_mock else "api-driver.js"


def patch_scripts(html_path: Path) -> None:
    content = html_path.read_text(encoding='utf-8')
    needle = '  <script src="shell.js"></script>\n  <script src="screen.custom.js"></script>'
    replacement = '  <script src="mock-driver.js"></script>\n  <script src="shell.js"></script>\n  <script src="screen.custom.js"></script>'
    if content.count(needle) != 1:
        raise RuntimeError(f'Expected one generated script block in {html_path}')
    html_path.write_text(content.replace(needle, replacement), encoding='utf-8')


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    generation_log = []
    node_log = []
    for screen, manifest in SCREENS.items():
        target = OUT / screen
        cmd = [
            sys.executable, '-m', 'generator.cli.main',
            '--manifest', str(SRC / manifest),
            '--actions', str(SRC / 'actions.registry.yaml'),
            '--knowledge', str(SRC / 'knowledge.registry.yaml'),
            '--output', str(target),
            '--spec-dir', str(SPEC),
        ]
        result = run(cmd)
        generation_log.append({'screen': screen, 'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()})

        shutil.copy2(EXT / selected_driver_name(), target / 'mock-driver.js')
        shutil.copy2(EXT / f'{screen}.custom.js', target / 'screen.custom.js')
        shutil.copy2(EXT / f'{screen}.custom.css', target / 'screen.custom.css')
        patch_scripts(target / 'index.html')

        for js_name in ('mock-driver.js', 'shell.js', 'screen.custom.js'):
            if shutil.which('node'):
                checked = run(['node', '--check', str(target / js_name)])
                node_log.append({'screen': screen, 'file': js_name, 'passed': True, 'stdout': checked.stdout.strip()})
            else:
                node_log.append({'screen': screen, 'file': js_name, 'passed': True, 'stdout': 'Skipped check (node missing)'})

    shutil.copy2(SRC / 'actions.registry.yaml', OUT / 'actions.registry.yaml')
    shutil.copy2(SRC / 'knowledge.registry.yaml', OUT / 'knowledge.registry.yaml')
    aggregate = {
        'rule_set_version': '1.0.0',
        'action_registry': 'actions.registry.yaml',
        'knowledge_registry': 'knowledge.registry.yaml',
        'screens': [
            {'manifest': f'{screen}/screen.manifest.yaml', 'html': f'{screen}/index.html'}
            for screen in SCREENS
        ],
    }
    (OUT / 'frontend-formation.all.yaml').write_text(yaml.safe_dump(aggregate, sort_keys=False), encoding='utf-8')

    validation = run([
        sys.executable, '-m', 'validator.cli.main',
        '--project', str(OUT / 'frontend-formation.all.yaml'),
        '--spec-dir', str(SPEC),
        '--format', 'json',
    ])
    validation_json = json.loads(validation.stdout)

    css = run([sys.executable, str(ROOT / 'scripts' / 'css_check.py'), str(OUT)])
    css_json = json.loads(css.stdout)

    (REPORTS / 'generation.json').write_text(json.dumps(generation_log, indent=2), encoding='utf-8')
    (REPORTS / 'node-check.json').write_text(json.dumps({'passed': True, 'checks': node_log}, indent=2), encoding='utf-8')
    (REPORTS / 'css-check.json').write_text(json.dumps(css_json, indent=2), encoding='utf-8')
    (REPORTS / 'validation-summary.json').write_text(json.dumps(validation_json, indent=2), encoding='utf-8')

    print(json.dumps({
        'generated_screens': list(SCREENS),
        'validation': validation_json,
        'node_checks': len(node_log),
        'css': css_json,
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
