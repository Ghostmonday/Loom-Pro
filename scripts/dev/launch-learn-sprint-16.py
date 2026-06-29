#!/usr/bin/env python3
"""Launch 16-worker LEARN sprint via Command Bridge API (port 8082 vault)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "aoc-cli"), str(ROOT / "aoc_supervisor")]

import httpx  # noqa: E402
from aoc_supervisor.ui_intent import UiIntentDriver  # noqa: E402

INTENT = (
    "LEARN SPRINT: Discover the perfect joint workflow for Gaijinn dogfooding and "
    "well-formed Obsidian vault systems. Map Affairs/FileSystem/Gaijinn Obsidian vaults "
    "to gaijinn-memory-fs and platform .gaijinn/. Each worker owns one slice: "
    "constitution alignment, knowledge linter, ingress/promotion, GUI deploy path, "
    "cross-vault links, metrics targets. Deliver research + concrete artifacts in "
    "assigned paths. Post blockers to council."
)


def main() -> int:
    base = os.environ.get("GAIJINN_API_BASE", "http://127.0.0.1:8082").rstrip("/")
    workers = int(os.environ.get("GAIJINN_LEARN_WORKERS", "16"))
    timeout = int(os.environ.get("GAIJINN_LEARN_TIMEOUT", "900"))
    executor = os.environ.get("GAIJINN_LEARN_EXECUTOR", "deepseek")
    model = os.environ.get("GAIJINN_LEARN_MODEL", "deepseek-v4-flash")

    print(f"==> LEARN sprint: {workers} workers @ {base}")
    print(f"    executor={executor} model={model} timeout={timeout}s")

    http_timeout = httpx.Timeout(connect=60.0, read=float(timeout + 120), write=60.0, pool=60.0)
    with httpx.Client(base_url=base, timeout=http_timeout) as client:
        driver = UiIntentDriver(client)
        prep = driver.prepare(INTENT)
        print(
            f"==> prepare: session={prep.session_id} work_units={prep.work_units} recommended={prep.recommended_swarm}"
        )
        swarm = driver.assign_swarm(workers)
        print(f"==> swarm: {swarm}")
        obs = driver.deploy_sprint(
            workers,
            INTENT,
            timeout=timeout,
            executor=executor,
            model=model,
        )
        obs.prepare = prep

    print(f"==> sprint terminal: {obs.status}")
    print(f"    session_id: {obs.session_id}")
    print(f"    sprint_id: {obs.sprint_id}")
    if obs.spawn_response:
        print(f"    spawn: {obs.spawn_response}")
    terminal = sum(
        1 for w in (obs.workers or [])[:workers] if str(w.get("status", "")) in {"completed", "failed", "timed_out"}
    )
    print(f"    workers_terminal: {terminal}/{workers}")
    return 0 if obs.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
