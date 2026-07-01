"""Intent Mapping mirror driver — AI-isomorphic smoke tests without a browser.

Invention: ui/gaijinn-ui-intent-map.json is the source of truth for BOTH:
  - Human UI (contract only — rebuild after Loom backend; mirror driver below)
  - AI smoke tests (UiIntentDriver dispatches the same actions.*)

Interacting with the mirror triggers the same APIs, handlers, files, and errors
as clicking the browser. smoke_scenarios[] in the map are executable specs.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .intent_mirror import AssertionResult, IntentMirrorState, evaluate_assertions
from .repo_paths import INTENT_MAP_PATH, LOOM_PIPELINE_INTENT_MAP_PATH

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
        self.mirror = IntentMirrorState()
        self._spawn_http_status: int = 0
        self.forge_session_id: str | None = None
        self.forge_session_status: str = ""
        self.forge_blueprint_version: int = 1
        self.last_forge_action: str = ""

    @staticmethod
    def _mirror_readiness(data: Mapping[str, Any]) -> dict[str, Any]:
        readiness = dict(data.get("readiness") or {})
        readiness["can_handoff"] = bool(
            readiness.get("can_handoff")
            or readiness.get("ready_to_finalize")
            or data.get("session_status") == "FINALIZED"
            or (data.get("session_status") in {"QUESTIONING", "VALIDATING"} and not data.get("current_question"))
        )
        return readiness

    def prepare(
        self,
        intent: str,
        phases: list[str] | None = None,
        loaded_context: dict[str, Any] | None = None,
        intent_forge_session_id: str | None = None,
    ) -> PrepareObservation:
        body: dict[str, Any] = {"intent": intent}
        if phases is not None:
            body["phases"] = phases
        if loaded_context is not None:
            body["loaded_context"] = loaded_context
        if intent_forge_session_id:
            body["intent_forge_session_id"] = intent_forge_session_id
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
        self.mirror.prepare = dict(data)
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
        self.mirror.swarm = dict(data)
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
        spawn_headers = {
            **self.headers,
            "X-Idempotency-Key": str(uuid.uuid4()),
        }
        response = self.client.post("/api/v1/grid/spawn", json=body, headers=spawn_headers)
        self._spawn_http_status = response.status_code
        if response.status_code >= 400:
            raise RuntimeError(f"spawn failed {response.status_code}: {response.text}")
        payload = response.json()
        self.mirror.spawn = {
            **payload,
            "workers": payload.get("workers", []),
            "status": response.status_code,
            "sprint_status": payload.get("status"),
        }
        return payload

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

    def _dispatch_forge_intake_start_session(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        prompt = str(payload.get("prompt", payload.get("intent", "")))
        tier = str(payload.get("tier", "paid"))
        body = {"prompt": prompt, "tier": tier}
        response = self.client.post(
            "/api/v1/intent-forge/sessions",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge start_session failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_id = str(data.get("session_id", ""))
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", 1))
        self.last_forge_action = "intake.start_session"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.current_question = dict(data.get("current_question") or {})
        self.mirror.readiness = self._mirror_readiness(data)
        self.mirror.executable_projection = dict(data.get("executable_projection") or {})
        return data

    def _dispatch_forge_question_submit_answer(self, sid: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        answer = str(payload.get("answer", ""))
        question_id = str(payload.get("question_id", ""))
        body = {
            "answer": answer,
            "question_id": question_id,
            "idempotency_key": f"c02-{sid[-8:]}-{self.forge_blueprint_version}",
            "expected_blueprint_version": self.forge_blueprint_version,
        }
        response = self.client.post(
            f"/api/v1/intent-forge/sessions/{sid}/answers",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge submit_answer failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", self.forge_blueprint_version))
        self.last_forge_action = "question.submit_answer"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.current_question = dict(data.get("current_question") or {})
        self.mirror.readiness = self._mirror_readiness(data)
        return data

    def _dispatch_forge_handoff_confirm(self, sid: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        confirmation = str(payload.get("confirmation", "Proceed"))
        body = {
            "action": "confirm",
            "confirmation": confirmation,
            "idempotency_key": "c02-confirm-" + sid[-8:],
            "expected_blueprint_version": self.forge_blueprint_version,
        }
        response = self.client.post(
            f"/api/v1/intent-forge/sessions/{sid}/handoff",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge confirm_handoff failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", self.forge_blueprint_version))
        self.last_forge_action = "handoff.confirm"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.artifact = dict(data.get("artifact") or {})
        self.mirror.executable_projection = dict(data.get("executable_projection") or {})
        return data

    def _dispatch_forge_handoff_accept(self, sid: str) -> dict[str, Any]:
        body = {
            "action": "accept",
            "idempotency_key": "c02-accept-" + sid[-8:],
            "expected_blueprint_version": self.forge_blueprint_version,
        }
        response = self.client.post(
            f"/api/v1/intent-forge/sessions/{sid}/handoff",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge accept_handoff failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", self.forge_blueprint_version))
        self.last_forge_action = "handoff.accept"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.readiness = self._mirror_readiness(data)
        self.mirror.executable_projection = dict(data.get("executable_projection") or {})
        return data

    def _dispatch_forge_intake_start_session(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        prompt = str(payload.get("prompt", payload.get("intent", "")))
        tier = str(payload.get("tier", "paid"))
        body = {"prompt": prompt, "tier": tier}
        response = self.client.post(
            "/api/v1/intent-forge/sessions",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge start_session failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_id = str(data.get("session_id", ""))
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", 1))
        self.last_forge_action = "intake.start_session"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.current_question = dict(data.get("current_question") or {})
        self.mirror.readiness = self._mirror_readiness(data)
        self.mirror.executable_projection = dict(data.get("executable_projection") or {})
        return data

    def _dispatch_forge_question_submit_answer(self, sid: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        answer = str(payload.get("answer", ""))
        question_id = str(payload.get("question_id", ""))
        body = {
            "answer": answer,
            "question_id": question_id,
            "idempotency_key": f"c02-{sid[-8:]}-{self.forge_blueprint_version}",
            "expected_blueprint_version": self.forge_blueprint_version,
        }
        response = self.client.post(
            f"/api/v1/intent-forge/sessions/{sid}/answers",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge submit_answer failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", self.forge_blueprint_version))
        self.last_forge_action = "question.submit_answer"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.current_question = dict(data.get("current_question") or {})
        self.mirror.readiness = self._mirror_readiness(data)
        return data

    def _dispatch_forge_handoff_confirm(self, sid: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        confirmation = str(payload.get("confirmation", "Proceed"))
        body = {
            "action": "confirm",
            "confirmation": confirmation,
            "idempotency_key": "c02-confirm-" + sid[-8:],
            "expected_blueprint_version": self.forge_blueprint_version,
        }
        response = self.client.post(
            f"/api/v1/intent-forge/sessions/{sid}/handoff",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge confirm_handoff failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", self.forge_blueprint_version))
        self.last_forge_action = "handoff.confirm"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.artifact = dict(data.get("artifact") or {})
        self.mirror.executable_projection = dict(data.get("executable_projection") or {})
        return data

    def _dispatch_forge_handoff_accept(self, sid: str) -> dict[str, Any]:
        body = {
            "action": "accept",
            "idempotency_key": "c02-accept-" + sid[-8:],
            "expected_blueprint_version": self.forge_blueprint_version,
        }
        response = self.client.post(
            f"/api/v1/intent-forge/sessions/{sid}/handoff",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge accept_handoff failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", self.forge_blueprint_version))
        self.last_forge_action = "handoff.accept"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.readiness = self._mirror_readiness(data)
        self.mirror.executable_projection = dict(data.get("executable_projection") or {})
        return data

    def _dispatch_forge_intake_start_session(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        prompt = str(payload.get("prompt", payload.get("intent", "")))
        tier = str(payload.get("tier", "paid"))
        body = {"prompt": prompt, "tier": tier}
        response = self.client.post(
            "/api/v1/intent-forge/sessions",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge start_session failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_id = str(data.get("session_id", ""))
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", 1))
        self.last_forge_action = "intake.start_session"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.current_question = dict(data.get("current_question") or {})
        self.mirror.readiness = self._mirror_readiness(data)
        self.mirror.executable_projection = dict(data.get("executable_projection") or {})
        return data

    def _dispatch_forge_question_submit_answer(self, sid: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        answer = str(payload.get("answer", ""))
        question_id = str(payload.get("question_id", ""))
        body = {
            "answer": answer,
            "question_id": question_id,
            "idempotency_key": f"c02-{sid[-8:]}-{self.forge_blueprint_version}",
            "expected_blueprint_version": self.forge_blueprint_version,
        }
        response = self.client.post(
            f"/api/v1/intent-forge/sessions/{sid}/answers",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge submit_answer failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", self.forge_blueprint_version))
        self.last_forge_action = "question.submit_answer"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.current_question = dict(data.get("current_question") or {})
        self.mirror.readiness = self._mirror_readiness(data)
        return data

    def _dispatch_forge_handoff_confirm(self, sid: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        confirmation = str(payload.get("confirmation", "Proceed"))
        body = {
            "action": "confirm",
            "confirmation": confirmation,
            "idempotency_key": "c02-confirm-" + sid[-8:],
            "expected_blueprint_version": self.forge_blueprint_version,
        }
        response = self.client.post(
            f"/api/v1/intent-forge/sessions/{sid}/handoff",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge confirm_handoff failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", self.forge_blueprint_version))
        self.last_forge_action = "handoff.confirm"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.artifact = dict(data.get("artifact") or {})
        self.mirror.executable_projection = dict(data.get("executable_projection") or {})
        return data

    def _dispatch_forge_handoff_accept(self, sid: str) -> dict[str, Any]:
        body = {
            "action": "accept",
            "idempotency_key": "c02-accept-" + sid[-8:],
            "expected_blueprint_version": self.forge_blueprint_version,
        }
        response = self.client.post(
            f"/api/v1/intent-forge/sessions/{sid}/handoff",
            json=body,
            headers=self.headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"forge accept_handoff failed {response.status_code}: {response.text}")
        data = response.json()
        self.forge_session_status = str(data.get("session_status", ""))
        self.forge_blueprint_version = int(data.get("blueprint_version", self.forge_blueprint_version))
        self.last_forge_action = "handoff.accept"
        self.mirror.session_status = self.forge_session_status
        self.mirror.intent_forge = dict(data)
        self.mirror.readiness = self._mirror_readiness(data)
        self.mirror.executable_projection = dict(data.get("executable_projection") or {})
        return data

    def dispatch_loom_forge_action(
        self,
        action: str,
        args: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute one actions.* entry from the forge intent map.

        Mirrors: intake.start_session, question.submit_answer,
        handoff.confirm, handoff.accept.
        Syncs mirror fields session_status, artifact, intent_forge.
        """
        payload = dict(args or {})

        if action == "intake.start_session":
            return self._dispatch_forge_intake_start_session(payload)

        if not self.forge_session_id:
            raise RuntimeError("forge session required — call intake.start_session first")
        sid = self.forge_session_id

        if action == "question.submit_answer":
            return self._dispatch_forge_question_submit_answer(sid, payload)

        if action == "handoff.confirm":
            return self._dispatch_forge_handoff_confirm(sid, payload)

        if action == "handoff.accept":
            return self._dispatch_forge_handoff_accept(sid)

        raise KeyError(f"unknown forge action {action!r}")

    def dispatch_intent_action(
        self,
        action: str,
        args: Mapping[str, Any] | None = None,
        *,
        observation: SprintObservation | None = None,
        workers_default: int = 2,
    ) -> SprintObservation:
        """Execute one actions.* entry from the intent map (mirror of browser click)."""
        payload = dict(args or {})
        if action == "orchestrate.prepare":
            phase_args = payload.get("phases")
            # Inject forge session from driver state if not explicitly provided
            ifg = payload.get("intent_forge_session_id") or self.forge_session_id
            prep = self.prepare(
                str(payload.get("intent", "smoke")),
                phases=list(phase_args) if isinstance(phase_args, list) else None,
                intent_forge_session_id=ifg,
            )
            return SprintObservation(
                sprint_id="",
                status="prepared",
                session_id=prep.session_id,
                prepare=prep,
            )
        if action == "orchestrate.swarm":
            self.assign_swarm(int(payload.get("workers", workers_default)))
            return observation or SprintObservation(sprint_id="", status="swarmed", session_id=self.session_id)
        if action == "deploy.sprint":
            workers = int(payload.get("workers", workers_default))
            task = str(payload.get("task", self.intent or "smoke"))
            timeout = int(payload.get("timeout", 120))
            result = self.deploy_sprint(workers, task, timeout=timeout)
            if observation:
                result.prepare = observation.prepare
                if observation.session_id:
                    result.session_id = observation.session_id
            self.mirror.sprint = {"status": result.status, "sprint_id": result.sprint_id}
            self.mirror.sync_grid_visibility(sprint_status=result.status, worker_count=len(result.workers))
            return result
        if action == "chat.submit_intent":
            return self.full_flow(
                str(payload.get("text", payload.get("intent", "smoke"))),
                workers=int(payload.get("workers", 2)),
                timeout=int(payload.get("timeout", 120)),
            )
        if action == "grid.poll_status":
            if not observation or not observation.sprint_id:
                raise RuntimeError("grid.poll_status requires an active sprint")
            workers = int(payload.get("workers", workers_default))
            until = str(payload.get("until", "completed"))
            result = self.wait_for_sprint_terminal(
                observation.sprint_id,
                workers=workers,
                timeout_s=180.0 if until == "completed" else 60.0,
            )
            result.prepare = observation.prepare
            result.session_id = observation.session_id or self.session_id
            result.merge = observation.merge
            result.spawn_response = observation.spawn_response or self.mirror.spawn
            if result.sprint_id:
                self.mirror.grid_status = self.grid_status(result.sprint_id)
            self.mirror.sprint = {"status": result.status, "sprint_id": result.sprint_id}
            self.mirror.sync_grid_visibility(sprint_status=result.status, worker_count=len(result.workers))
            return result
        if action == "merge.run":
            sid = str(
                payload.get("session_id") or (observation.session_id if observation else "") or self.session_id or ""
            )
            merge_payload = self.run_merge(sid)
            self._apply_merge_mirror(merge_payload)
            base = observation or SprintObservation(sprint_id="", status="merged", session_id=sid)
            base.merge = merge_payload
            return base
        if action == "merge.poll_status":
            sid = str(
                payload.get("session_id") or (observation.session_id if observation else "") or self.session_id or ""
            )
            merge_payload = self.merge_status(sid)
            self._apply_merge_mirror(merge_payload)
            base = observation or SprintObservation(sprint_id="", status="merge_status", session_id=sid)
            base.merge = merge_payload
            return base
        if action == "deliverable.download":
            sid = str(
                payload.get("session_id") or (observation.session_id if observation else "") or self.session_id or ""
            )
            response = self.download_deliverable(sid)
            base = observation or SprintObservation(sprint_id="", status="deliverable", session_id=sid)
            base.deliverable_status = response.status_code
            base.deliverable_content_type = response.headers.get("content-type", "")
            return base
        raise KeyError(f"unknown intent action {action!r}")

    def dispatch_loom_action(
        self,
        action: str,
        args: Mapping[str, Any] | None = None,
        *,
        observation: SprintObservation | None = None,
        workers_default: int = 2,
    ) -> dict[str, Any] | SprintObservation:
        """Execute one action from the Loom pipeline intent map."""
        payload = dict(args or {})
        if action in {
            "intake.start_session",
            "question.submit_answer",
            "handoff.confirm",
            "handoff.accept",
        }:
            return self.dispatch_loom_forge_action(action, payload)

        if action == "teleology.deliberate":
            intent = str(payload.get("intent") or self.intent or "smoke")
            return self.collect_teleology_receipt(intent, self.forge_session_id)

        if action == "blueprint.synthesize":
            if not self.forge_session_id:
                raise RuntimeError("forge session required — call intake.start_session first")
            receipt = payload.get("teleology_receipt", self.mirror.teleology)
            body = {
                "intent_forge_session_id": self.forge_session_id,
                "teleology_receipt": receipt if isinstance(receipt, dict) else {},
            }
            response = self.client.post(
                "/api/v1/loom/blueprint/synthesize",
                json=body,
                headers=self.headers,
            )
            if response.status_code >= 400:
                raise RuntimeError(f"blueprint synthesis failed {response.status_code}: {response.text}")
            data = response.json()
            blueprint = data.get("blueprint")
            if isinstance(blueprint, dict):
                self.mirror.executable_projection = dict(blueprint)
                self.mirror.blueprint = dict(blueprint)
                self.mirror.baseline = {
                    "dark_bridge_count": int(
                        blueprint.get(
                            "graph_only_dark_bridge_count",
                            data.get("dark_bridge_count", 0),
                        )
                        or 0
                    )
                }
            return data

        if action == "orchestrate.prepare":
            phase_args = payload.get("phases")
            intent = str(
                payload.get("intent") or self.intent or self.mirror.intent_forge.get("original_prompt") or "smoke"
            )
            prep = self.prepare(
                intent,
                phases=list(phase_args) if isinstance(phase_args, list) else None,
                intent_forge_session_id=self.forge_session_id,
            )
            return SprintObservation(
                sprint_id="",
                status="prepared",
                session_id=prep.session_id,
                prepare=prep,
            )

        return self.dispatch_intent_action(
            action,
            payload,
            observation=observation,
            workers_default=workers_default,
        )

    def collect_teleology_receipt(
        self,
        intent: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Call GET /api/v1/blueprint/deliberate SSE and consume events until blueprint_freeze.

        Parses canonical SSE events, tracks subphases, computes curvature_floor
        from edge curvature kappa values, and stores the full teleology record
        on self.mirror.teleology.
        """
        # NOTE: custom TestClient doesn't forward params kwarg to URL.
        # Embed query params directly in the URL string.
        import urllib.parse

        url = f"/api/v1/blueprint/deliberate?intent={urllib.parse.quote(intent)}&stream_format=canonical"
        response = self.client.get(
            url,
            headers=self.headers,
        )
        response.raise_for_status()

        teleology: dict[str, Any] = {
            "intent": intent,
            "subphases": {},
            "events": [],
            "curvature_floor": 0.0,
            "edge_curvatures": [],
            "work_units": 0,
            "session_id": session_id or "",
            "blueprint_freeze": {},
        }

        body = response.text
        for block in body.split("\n\n"):
            block = block.strip()
            if not block:
                continue
            for line in block.split("\n"):
                line = line.strip()
                if not line.startswith("data: "):
                    continue
                try:
                    event = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue

                teleology["events"].append(event)

                event_type = event.get("event_type", "")
                subphase = event.get("subphase")
                canonical_data = event.get("data", {})

                # Track subphase start
                if event_type == "phase.begin" and subphase:
                    teleology["subphases"][subphase] = {"status": "started"}

                # Track subphase complete
                if event_type == "phase.complete":
                    sp = subphase or canonical_data.get("phase", "")
                    if sp:
                        entry = teleology["subphases"].setdefault(sp, {})
                        entry["status"] = "complete"
                        entry["elapsed_ms"] = canonical_data.get("elapsed_ms", 0)

                    # blueprint_freeze via deliberation_complete (phase=awaiting_swarm)
                    if event.get("phase") == "awaiting_swarm":
                        teleology["session_id"] = canonical_data.get("session_id", teleology["session_id"])
                        teleology["work_units"] = canonical_data.get("work_units", 0)
                        teleology["blueprint_freeze"] = {
                            "session_id": canonical_data.get("session_id"),
                            "work_units": canonical_data.get("work_units"),
                            "high_risk_units": canonical_data.get("high_risk_units"),
                            "recommended_swarm": canonical_data.get("recommended_swarm"),
                        }
                        if canonical_data.get("prepare"):
                            teleology["prepare"] = canonical_data["prepare"]

                # Track edge curvatures for curvature_floor computation
                if event_type == "topology.edge.curvature":
                    kappa = canonical_data.get("kappa", 0.0)
                    teleology["edge_curvatures"].append(kappa)

        if teleology["edge_curvatures"]:
            teleology["curvature_floor"] = min(teleology["edge_curvatures"])

        self.mirror.teleology = teleology
        return teleology

    def _apply_merge_mirror(self, payload: dict[str, Any]) -> None:
        inner = payload.get("merge_pipeline")
        if isinstance(inner, dict) and {"phase", "merged", "blocked"} <= set(inner):
            self.mirror.merge_pipeline = dict(inner)
        else:
            self.mirror.merge_pipeline = dict(payload)

    def _sync_mirror_from_observation(self, observation: SprintObservation) -> None:
        if observation.prepare:
            self.mirror.prepare = observation.prepare.raw or self.last_prepare_payload
        if observation.sprint_id:
            status_payload = self.grid_status(observation.sprint_id)
            self.mirror.grid_status = status_payload
            self.mirror.sprint = {
                "status": observation.status,
                "sprint_id": observation.sprint_id,
                **(status_payload.get("sprint") or {}),
            }
            self.mirror.sync_grid_visibility(
                sprint_status=observation.status,
                worker_count=len(observation.workers),
            )
        if observation.merge:
            self._apply_merge_mirror(observation.merge)

    def run_smoke_scenario(self, scenario_id: str, intent_map: Mapping[str, Any] | None = None) -> SprintObservation:
        catalog = intent_map or load_ui_intent_map()
        scenarios = {item["id"]: item for item in catalog.get("smoke_scenarios", [])}
        if scenario_id not in scenarios:
            raise KeyError(f"unknown smoke scenario {scenario_id!r}")
        scenario = scenarios[scenario_id]
        observation: SprintObservation | None = None
        workers_default = 2
        self.mirror = IntentMirrorState()
        for step in scenario.get("steps", []):
            api_step = step.get("api")
            if isinstance(api_step, str) and api_step.strip():
                method, _, path = api_step.strip().partition(" ")
                body = step.get("body", {})
                response = self.client.request(
                    method.upper(),
                    path,
                    json=body if body else None,
                    headers=self.headers,
                )
                if response.status_code >= 400:
                    raise RuntimeError(f"{api_step} failed {response.status_code}: {response.text}")
                data = response.json()
                self.mirror.session_status = str(data.get("session_status", "api_ok"))
                if "artifact" in data:
                    self.mirror.artifact = dict(data.get("artifact") or {})
                self.mirror.intent_forge = dict(data)
                observation = SprintObservation(
                    sprint_id="",
                    status=self.mirror.session_status,
                    session_id=str(data.get("session_id", "")),
                )
                continue
            action = step.get("action")
            if not action:
                continue
            args = step.get("args", {})
            workers_default = int(args.get("workers", workers_default))
            observation = self.dispatch_intent_action(
                str(action),
                args,
                observation=observation,
                workers_default=workers_default,
            )
            self._sync_mirror_from_observation(observation)
        if observation is None:
            raise RuntimeError(f"no executable steps in scenario {scenario_id!r}")
        return observation

    def run_loom_pipeline_scenario(
        self,
        scenario_id: str,
        intent_map: Mapping[str, Any] | None = None,
    ) -> SprintObservation:
        """Replay a scenario from the Loom pipeline map in declared order."""
        catalog = intent_map or load_ui_intent_map(LOOM_PIPELINE_INTENT_MAP_PATH)
        scenarios = {item["id"]: item for item in catalog.get("smoke_scenarios", [])}
        if scenario_id not in scenarios:
            raise KeyError(f"unknown Loom pipeline scenario {scenario_id!r}")

        self.mirror = IntentMirrorState()
        self.forge_session_id = None
        self.forge_session_status = ""
        self.forge_blueprint_version = 1
        self.last_forge_action = ""
        observation: SprintObservation | None = None
        workers_default = 2

        for step in scenarios[scenario_id].get("steps", []):
            api_step = step.get("api")
            if isinstance(api_step, str) and api_step.strip():
                method, _, path = api_step.strip().partition(" ")
                body = dict(step.get("body") or {})
                if method.upper() == "POST" and path == "/api/v1/intent-forge/sessions":
                    result = self.dispatch_loom_action(
                        "intake.start_session",
                        body,
                        observation=observation,
                        workers_default=workers_default,
                    )
                    if not isinstance(result, dict):
                        raise RuntimeError("Loom intake returned an invalid observation")
                    observation = SprintObservation(
                        sprint_id="",
                        status=str(result.get("session_status", "")),
                        session_id=str(result.get("session_id", "")),
                    )
                    continue

                response = self.client.request(
                    method.upper(),
                    path,
                    json=body if body else None,
                    headers=self.headers,
                )
                expected_status = step.get("expect_status")
                if expected_status is not None and response.status_code == int(expected_status):
                    continue
                if response.status_code >= 400:
                    raise RuntimeError(f"{api_step} failed {response.status_code}: {response.text}")
                continue

            action = step.get("action")
            if not action:
                continue
            args = dict(step.get("args") or {})
            for key in ("until", "repeat_until"):
                if key in step and key not in args:
                    args[key] = step[key]
            workers_default = int(args.get("workers", workers_default))
            repeat_until = str(args.pop("repeat_until", ""))
            attempts = 0
            while True:
                if (
                    action == "question.submit_answer"
                    and repeat_until == "readiness.can_handoff"
                    and not self.mirror.current_question
                ):
                    self.mirror.readiness["can_handoff"] = True
                    break
                if action == "question.submit_answer" and not args.get("question_id"):
                    args["question_id"] = self.mirror.current_question.get("question_id", "")
                result = self.dispatch_loom_action(
                    str(action),
                    args,
                    observation=observation,
                    workers_default=workers_default,
                )
                if isinstance(result, SprintObservation):
                    observation = result
                    self._sync_mirror_from_observation(observation)
                elif self.forge_session_id:
                    observation = observation or SprintObservation(
                        sprint_id="",
                        status=self.forge_session_status,
                        session_id=self.forge_session_id,
                    )
                if not repeat_until:
                    break
                attempts += 1
                if repeat_until == "readiness.can_handoff" and not self.mirror.current_question:
                    self.mirror.readiness["can_handoff"] = True
                    break
                condition = evaluate_assertions(
                    [repeat_until],
                    self.mirror.as_context(),
                )[0]
                if condition.passed:
                    break
                if attempts >= 20:
                    raise RuntimeError(f"{action} did not satisfy {repeat_until!r} after {attempts} attempts")
                args["question_id"] = self.mirror.current_question.get("question_id", "")

        if observation is None:
            raise RuntimeError(f"no executable steps in Loom scenario {scenario_id!r}")
        return observation

    def verify_scenario_assertions(
        self,
        scenario_id: str,
        *,
        intent_map: Mapping[str, Any] | None = None,
    ) -> list[AssertionResult]:
        catalog = intent_map or self._scenario_catalog(scenario_id)
        scenario = {item["id"]: item for item in catalog.get("smoke_scenarios", [])}[scenario_id]
        return evaluate_assertions(list(scenario.get("assertions", [])), self.mirror.as_context())

    def run_and_verify_scenario(
        self,
        scenario_id: str,
        *,
        workers: int = 2,
        intent_map: Mapping[str, Any] | None = None,
    ) -> tuple[SprintObservation, list[AssertionResult]]:
        catalog = intent_map or self._scenario_catalog(scenario_id)
        loom_scenarios = {
            item["id"] for item in load_ui_intent_map(LOOM_PIPELINE_INTENT_MAP_PATH).get("smoke_scenarios", [])
        }
        if scenario_id in loom_scenarios:
            observation = self.run_loom_pipeline_scenario(scenario_id, intent_map=catalog)
        else:
            observation = self.run_smoke_scenario(scenario_id, intent_map=catalog)
        assertion_results = self.verify_scenario_assertions(scenario_id, intent_map=catalog)
        failed = [item for item in assertion_results if not item.passed]
        if failed:
            details = "; ".join(f"{item.expression} ({item.detail})" for item in failed)
            raise AssertionError(f"scenario {scenario_id} mirror assertions failed: {details}")
        requested_workers = int(
            self.last_swarm_payload.get("workers_ready") or self.last_swarm_payload.get("workers") or workers
        )
        workflow = self.evaluate_scenario(
            scenario_id,
            observation,
            workers=requested_workers,
            intent_map=catalog,
        )
        if not workflow.passed:
            raise AssertionError(f"scenario {scenario_id} workflow confusion_count={workflow.confusion_count}")
        return observation, assertion_results

    def _scenario_catalog(self, scenario_id: str) -> Mapping[str, Any]:
        loom_catalog = load_ui_intent_map(LOOM_PIPELINE_INTENT_MAP_PATH)
        if any(item.get("id") == scenario_id for item in loom_catalog.get("smoke_scenarios", [])):
            return loom_catalog
        return load_ui_intent_map()

    def evaluate_scenario(
        self,
        scenario_id: str,
        observation: SprintObservation,
        *,
        workers: int,
        intent_map: Mapping[str, Any] | None = None,
    ) -> Any:
        from aoc_supervisor.workflow_evaluator import evaluate_workflow

        catalog = intent_map or self._scenario_catalog(scenario_id)
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
            greenfield=bool(scenario.get("greenfield"))
            and self.last_prepare_payload.get("blueprint_mode") != "loom_synthesis",
        )
