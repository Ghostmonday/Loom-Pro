"""UI intent map driver — machine smoke tests isomorphic to gaijinn-terminal.html.

GAIJINN BLUEPRINT — mirror driver (API replay without browser)
--------------------------------------------------------------
Layer: Test infrastructure / isomorphic state machine driver
Status: shipped for prepare → swarm → deploy.sprint → grid.poll_status → merge → deliverable.download
Spec: ui/gaijinn-ui-intent-map.json (actions, flow, smoke_scenarios)

UiIntentDriver method order MUST match gaijinn-terminal.html submit flow.
When adding a terminal action, add: intent map action → driver method → test.

AI agents — DO
  - Read load_ui_intent_map() before changing terminal JS
  - Assert on prepare/swarm payloads evaluators already check

Gaps (planned, not coded)
  - simulate DOM visibility (grid.empty hidden) — API-only today
  - Replay council_say side effects
  - Full FAILED path simulation

Robustness path
  - Scenario runner that reads smoke_scenarios[] generically from JSON
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .repo_paths import INTENT_MAP_PATH

DEFAULT_QUOTE_PAYLOAD: dict[str, Any] = {
    "workers": 2,
    "agent_slots": 2,
    "assignment_count": 2,
    "nodes": [{"id": f"node-{i}"} for i in range(4)],
}


@dataclass
class PrepareObservation:
    session_id: str
    work_units: int
    high_risk_units: int
    suggested_swarm: list[int]
    recommended_swarm: int = 2
    swarm_rationale: str = ""
    blueprint_mode: str = "graph"
    work_stream_titles: list[str] = field(default_factory=list)
    phases: list[str] = field(default_factory=list)
    current_phase: str = ""
    phase_count: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class SprintObservation:
    sprint_id: str
    status: str
    session_id: str | None = None
    workers: list[dict[str, Any]] = field(default_factory=list)
    spawn_response: dict[str, Any] = field(default_factory=dict)
    prepare: PrepareObservation | None = None
    merge: dict[str, Any] | None = None
    deliverable_status: int | None = None
    deliverable_content_type: str = ""


def load_ui_intent_map(path: Path | None = None) -> dict[str, Any]:
    target = path or INTENT_MAP_PATH
    with target.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class UiIntentDriver:
    """Replay terminal UI actions against the API (same sequence as browser JS)."""

    def __init__(self, client: Any, *, user_id: str = "terminal-user") -> None:
        self.client = client
        self.user_id = user_id
        self.headers = {"X-User-Id": user_id}
        self.session_id: str | None = None
        self.intent: str = ""
        self.work_units: int = 0
        self.last_prepare_payload: dict[str, Any] = {}
        self.last_swarm_payload: dict[str, Any] = {}

    def prepare(
        self,
        intent: str,
        phases: list[str] | None = None,
        loaded_context: dict[str, Any] | None = None,
    ) -> PrepareObservation:
        body: dict[str, Any] = {"intent": intent}
        if phases is not None:
            body["phases"] = phases
        if loaded_context is not None:
            body["loaded_context"] = loaded_context
        response = self.client.post(
            "/api/v1/orchestrate/prepare",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"prepare failed {response.status_code}: {response.text}")
        data = response.json()
        self.session_id = str(data["session_id"])
        self.intent = intent
        self.work_units = int(data.get("work_units", 0))
        self.last_prepare_payload = dict(data)
        return PrepareObservation(
            session_id=self.session_id,
            work_units=self.work_units,
            high_risk_units=int(data.get("high_risk_units", 0)),
            suggested_swarm=list(data.get("suggested_swarm", [1, 2, 4])),
            recommended_swarm=int(data.get("recommended_swarm", 2)),
            swarm_rationale=str(data.get("swarm_rationale", "")),
            blueprint_mode=str(data.get("blueprint_mode", "graph")),
            work_stream_titles=list(data.get("work_stream_titles", [])),
            phases=list(data.get("phases", [])),
            current_phase=str(data.get("current_phase", "")),
            phase_count=int(data.get("phase_count", 0)),
            raw=dict(data),
        )

    def assign_swarm(self, workers: int, *, session_id: str | None = None) -> dict[str, Any]:
        sid = session_id or self.session_id
        if not sid:
            raise RuntimeError("session_id required — call prepare() first")
        response = self.client.post(
            "/api/v1/orchestrate/swarm",
            json={"session_id": sid, "workers": workers},
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"swarm failed {response.status_code}: {response.text}")
        data = response.json()
        self.last_swarm_payload = dict(data)
        return data

    def quote(self, workers: int, *, assignment_count: int | None = None) -> dict[str, Any]:
        count = assignment_count if assignment_count is not None else max(workers, self.work_units, 1)
        payload = {
            **DEFAULT_QUOTE_PAYLOAD,
            "workers": workers,
            "agent_slots": workers,
            "assignment_count": count,
        }
        response = self.client.post("/api/v1/quote", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def purchase(self, workers: int, *, assignment_count: int | None = None) -> dict[str, Any]:
        count = assignment_count if assignment_count is not None else max(workers, self.work_units, 1)
        payload = {
            **DEFAULT_QUOTE_PAYLOAD,
            "workers": workers,
            "agent_slots": workers,
            "assignment_count": count,
        }
        response = self.client.post("/api/v1/blueprint/purchase", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def spawn(
        self,
        *,
        workers: int,
        sprint_token: str,
        task: str,
        session_id: str | None = None,
        model: str = "grok-composer-2.5-fast",
        sandbox: str = "default",
        reasoning: str = "high",
        always_approve: bool = True,
        timeout: int = 120,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "workers": workers,
            "model": model,
            "sandbox": sandbox,
            "reasoning": reasoning,
            "always_approve": always_approve,
            "sprint_token": sprint_token,
            "task": task or "Execute assigned tasks within the locked scope.",
            "timeout": timeout,
        }
        sid = session_id if session_id is not None else self.session_id
        if sid:
            body["session_id"] = sid
        response = self.client.post("/api/v1/grid/spawn", json=body, headers=self.headers)
        if response.status_code >= 400:
            raise RuntimeError(f"spawn failed {response.status_code}: {response.text}")
        return response.json()

    def grid_status(self, sprint_id: str) -> dict[str, Any]:
        response = self.client.get(f"/api/v1/grid/status?sprint_id={sprint_id}")
        response.raise_for_status()
        return response.json()

    def run_merge(self, session_id: str | None = None) -> dict[str, Any]:
        sid = session_id or self.session_id
        if not sid:
            raise RuntimeError("session_id required — call prepare() first")
        response = self.client.post(
            "/api/v1/grid/merge",
            json={"session_id": sid},
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"merge failed {response.status_code}: {response.text}")
        return response.json()

    def merge_status(self, session_id: str | None = None) -> dict[str, Any]:
        sid = session_id or self.session_id
        if not sid:
            raise RuntimeError("session_id required — call prepare() first")
        response = self.client.get(f"/api/v1/grid/merge/status?session_id={sid}")
        response.raise_for_status()
        return response.json()

    def advance_phase(self, session_id: str | None = None) -> dict[str, Any]:
        sid = session_id or self.session_id
        if not sid:
            raise RuntimeError("session_id required — call prepare() first")
        response = self.client.post(
            "/api/v1/orchestrate/advance-phase",
            json={"session_id": sid},
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"advance failed {response.status_code}: {response.text}")
        return response.json()

    def merge_report(self, session_id: str | None = None) -> dict[str, Any]:
        sid = session_id or self.session_id
        if not sid:
            raise RuntimeError("session_id required — call prepare() first")
        response = self.client.get(f"/api/v1/grid/merge/report?session_id={sid}")
        response.raise_for_status()
        return response.json()

    def project_diff(self, session_id: str | None = None) -> dict[str, Any]:
        sid = session_id or self.session_id
        if not sid:
            raise RuntimeError("session_id required — call prepare() first")
        response = self.client.get(f"/api/v1/grid/diff?session_id={sid}")
        response.raise_for_status()
        return response.json()

    def download_deliverable(self, session_id: str | None = None) -> Any:
        sid = session_id or self.session_id
        if not sid:
            raise RuntimeError("session_id required — call prepare() first")
        response = self.client.get(f"/api/v1/grid/deliverable?session_id={sid}")
        response.raise_for_status()
        return response

    def deploy_sprint(self, workers: int, task: str, *, timeout: int = 120) -> SprintObservation:
        purchase = self.purchase(workers)
        spawn_data = self.spawn(
            workers=workers,
            sprint_token=purchase["sprint_token"],
            task=task,
            timeout=timeout,
        )
        sprint_id = str(spawn_data["sprint_id"])
        observation = self.wait_for_sprint_terminal(sprint_id, workers=workers, timeout_s=timeout + 30)
        observation.spawn_response = spawn_data
        observation.session_id = self.session_id
        return observation

    def full_flow(self, intent: str, *, workers: int = 2, timeout: int = 120) -> SprintObservation:
        """Mirror browser: prepare → swarm → deploy → poll."""
        prep = self.prepare(intent)
        self.assign_swarm(workers)
        obs = self.deploy_sprint(workers, intent, timeout=timeout)
        obs.prepare = prep
        return obs

    def wait_for_sprint_terminal(
        self,
        sprint_id: str,
        *,
        workers: int,
        timeout_s: float = 60.0,
        poll_interval_s: float = 0.15,
    ) -> SprintObservation:
        deadline = time.monotonic() + timeout_s
        last_status = "running"
        last_workers: list[dict[str, Any]] = []
        while time.monotonic() < deadline:
            payload = self.grid_status(sprint_id)
            sprint = payload.get("sprint") or {}
            last_status = str(sprint.get("status", "running"))
            last_workers = list(payload.get("workers") or [])
            if last_status in {"completed", "failed", "timed_out"}:
                break
            terminal = sum(
                1
                for worker in last_workers[:workers]
                if str(worker.get("status", "")) in {"completed", "failed", "timed_out"}
            )
            if terminal >= workers:
                last_status = (
                    "failed"
                    if any(
                        str(worker.get("status", "")) in {"failed", "timed_out"} for worker in last_workers[:workers]
                    )
                    else "completed"
                )
                break
            time.sleep(poll_interval_s)
        return SprintObservation(sprint_id=sprint_id, status=last_status, workers=last_workers)

    def run_smoke_scenario(self, scenario_id: str, intent_map: Mapping[str, Any] | None = None) -> SprintObservation:
        catalog = intent_map or load_ui_intent_map()
        scenarios = {item["id"]: item for item in catalog.get("smoke_scenarios", [])}
        if scenario_id not in scenarios:
            raise KeyError(f"unknown smoke scenario {scenario_id!r}")
        scenario = scenarios[scenario_id]
        observation: SprintObservation | None = None
        workers_default = 2
        for step in scenario.get("steps", []):
            action = step.get("action")
            args = step.get("args", {})
            if action == "orchestrate.prepare":
                phase_args = args.get("phases")
                prep = self.prepare(
                    str(args.get("intent", "smoke")),
                    phases=list(phase_args) if isinstance(phase_args, list) else None,
                )
                observation = SprintObservation(
                    sprint_id="",
                    status="prepared",
                    session_id=prep.session_id,
                    prepare=prep,
                )
            elif action == "orchestrate.swarm":
                workers_default = int(args.get("workers", workers_default))
                self.assign_swarm(workers_default)
            elif action == "deploy.sprint":
                workers = int(args.get("workers", workers_default))
                task = str(args.get("task", self.intent or "smoke"))
                timeout = int(args.get("timeout", 120))
                saved_prep = observation.prepare if observation else None
                saved_session = observation.session_id if observation else self.session_id
                observation = self.deploy_sprint(workers, task, timeout=timeout)
                observation.prepare = saved_prep
                if saved_session:
                    observation.session_id = saved_session
            elif action == "chat.submit_intent":
                return self.full_flow(
                    str(args.get("text", args.get("intent", "smoke"))),
                    workers=int(args.get("workers", 2)),
                    timeout=int(args.get("timeout", 120)),
                )
            elif action == "grid.poll_status":
                if observation and observation.sprint_id:
                    saved_prep = observation.prepare
                    saved_session = observation.session_id
                    saved_merge = observation.merge
                    workers = int(args.get("workers", workers_default))
                    observation = self.wait_for_sprint_terminal(
                        observation.sprint_id,
                        workers=workers,
                    )
                    observation.prepare = saved_prep
                    observation.session_id = saved_session
                    observation.merge = saved_merge
                    observation.spawn_response = observation.spawn_response or {}
            elif action == "merge.run":
                sid = str(
                    args.get("session_id") or (observation.session_id if observation else "") or self.session_id or ""
                )
                merge_payload = self.run_merge(sid)
                if observation is None:
                    observation = SprintObservation(sprint_id="", status="merged", session_id=sid)
                observation.merge = merge_payload
            elif action == "merge.poll_status":
                sid = str(
                    args.get("session_id") or (observation.session_id if observation else "") or self.session_id or ""
                )
                merge_payload = self.merge_status(sid)
                if observation is None:
                    observation = SprintObservation(sprint_id="", status="merge_status", session_id=sid)
                observation.merge = merge_payload
            elif action == "deliverable.download":
                sid = str(
                    args.get("session_id") or (observation.session_id if observation else "") or self.session_id or ""
                )
                response = self.download_deliverable(sid)
                if observation is None:
                    observation = SprintObservation(sprint_id="", status="deliverable", session_id=sid)
                observation.deliverable_status = response.status_code
                observation.deliverable_content_type = response.headers.get("content-type", "")
        if observation is None:
            raise RuntimeError(f"no executable steps in scenario {scenario_id!r}")
        return observation

    def evaluate_scenario(
        self,
        scenario_id: str,
        observation: SprintObservation,
        *,
        workers: int,
        intent_map: Mapping[str, Any] | None = None,
    ) -> Any:
        from aoc_supervisor.workflow_evaluator import evaluate_workflow

        catalog = intent_map or load_ui_intent_map()
        scenario = {item["id"]: item for item in catalog.get("smoke_scenarios", [])}[scenario_id]
        grid_status: dict[str, Any] = {}
        if observation.sprint_id:
            grid_status = self.grid_status(observation.sprint_id)
        return evaluate_workflow(
            scenario_id=scenario_id,
            prepare=self.last_prepare_payload or None,
            swarm=self.last_swarm_payload or None,
            grid_status=grid_status or None,
            workers=observation.workers,
            merge=observation.merge,
            intent=self.intent,
            workers_requested=workers,
            greenfield=bool(scenario.get("greenfield")),
        )
