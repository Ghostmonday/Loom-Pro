#!/usr/bin/env python3
"""Run gaijinn-ui-intent-map.json smoke scenarios as a user (live HTTP, no browser).

Usage:
  GAIJINN_API_BASE=http://127.0.0.1:8081 python scripts/dev/ui-intent-smoke-user.py flow.deepseek_hermes_user
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "aoc-cli"), str(ROOT / "aoc_supervisor")]

import httpx  # noqa: E402
from aoc_supervisor.ui_intent import UiIntentDriver, load_ui_intent_map  # noqa: E402


def main() -> int:
    scenario_id = sys.argv[1] if len(sys.argv) > 1 else "flow.deepseek_hermes_mock"
    base = os.environ.get("GAIJINN_API_BASE", "http://127.0.0.1:8080").rstrip("/")
    catalog = load_ui_intent_map()
    scenarios = {item["id"]: item for item in catalog.get("smoke_scenarios", [])}
    if scenario_id not in scenarios:
        print(f"unknown scenario: {scenario_id}", file=sys.stderr)
        return 2

    scenario = scenarios[scenario_id]
    requires = scenario.get("requires") or {}
    for key, expected in requires.items():
        actual = os.environ.get(key, "")
        if str(actual) != str(expected):
            print(
                f"requires {key}={expected!r} but environment has {actual!r}",
                file=sys.stderr,
            )
            return 2

    print(f"==> Gaijinn user smoke: {scenario_id}")
    print(f"    API base: {base}")
    print(f"    description: {scenario.get('description', '')}")

    timeout = httpx.Timeout(connect=30.0, read=360.0, write=30.0, pool=30.0)
    with httpx.Client(base_url=base, timeout=timeout) as client:
        driver = UiIntentDriver(client)
        observation = driver.run_smoke_scenario(scenario_id)
        workers = 1
        for step in scenario.get("steps", []):
            if step.get("action") == "deploy.sprint":
                workers = int(step.get("args", {}).get("workers", workers))
                break
        evaluation = driver.evaluate_scenario(scenario_id, observation, workers=workers)

    print(f"==> sprint status: {observation.status}")
    if observation.session_id:
        print(f"    session_id: {observation.session_id}")
    if observation.sprint_id:
        print(f"    sprint_id: {observation.sprint_id}")
    if observation.spawn_response:
        print(f"    spawn: {observation.spawn_response}")
    if observation.merge:
        print(f"    merge: phase={observation.merge.get('phase')} blocked={observation.merge.get('blocked')}")
    confusion = getattr(evaluation, "confusion_count", 0)
    print(f"==> evaluator confusion_count: {confusion}")
    for inv in getattr(evaluation, "invariants", []):
        if not inv.passed:
            print(f"    FAIL {inv.name}: {inv.detail}")

    ok = observation.status == "completed"
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
