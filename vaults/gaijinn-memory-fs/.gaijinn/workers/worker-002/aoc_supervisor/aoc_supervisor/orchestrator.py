"""Workspace orchestration and telemetry validation for Gaijinn clusters."""

from __future__ import annotations

import ast
import json
import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from uuid import uuid4

from aoc_cli.gravity import compute_gravity_and_curvature

from .billing import deduct_compute_costs, enforce_billing_gate
from .enforcer import StructuralGravityViolation, validate_system_state

JobState = Literal["queued", "running", "completed", "blocked", "failed"]


@dataclass(slots=True)
class ClusterJob:
    """In-memory dispatch record for a simulated sub-agent task."""

    job_id: str
    agent_id: str
    prompt_payload: str
    workspace: Path
    output_file: Path | None = None
    status: JobState = "queued"
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def mark(self, status: JobState, error: str | None = None) -> None:
        self.status = status
        self.error = error
        self.updated_at = time.time()


class ClusterOrchestrator:
    """Coordinate isolated agent workspaces and supervisor validation."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        user_id: str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.gaijinn_dir = self.project_root / ".gaijinn"
        self.sandbox_root = self.gaijinn_dir / "sandboxes"
        self.metrics_manifest = self.gaijinn_dir / "metrics_manifest.json"
        self.user_id = user_id
        self.logger = logger or logging.getLogger(__name__)
        self.jobs: dict[str, ClusterJob] = {}
        self.agent_jobs: dict[str, str] = {}
        self.blocked = False

    def provision_sandbox(self, agent_id: str) -> Path:
        """Create a clean isolated sandbox for an agent."""
        self._ensure_not_blocked()
        safe_agent_id = self._validate_agent_id(agent_id)
        workspace = self.sandbox_root / safe_agent_id

        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    @enforce_billing_gate
    def dispatch_parallel_task(self, agent_id: str, prompt_payload: str, *, graph_size: int = 1) -> str:
        """Simulate dispatch to a sub-agent and write deterministic mock output."""
        self._ensure_not_blocked()
        workspace = self.provision_sandbox(agent_id)
        job_id = f"{agent_id}-{uuid4().hex[:12]}"
        job = ClusterJob(
            job_id=job_id,
            agent_id=agent_id,
            prompt_payload=prompt_payload,
            workspace=workspace,
        )
        self.jobs[job_id] = job
        self.agent_jobs[agent_id] = job_id

        try:
            job.mark("running")
            output_file = workspace / "generated_agent_output.py"
            output_file.write_text(self._render_mock_agent_code(agent_id, prompt_payload), encoding="utf-8")
            job.output_file = output_file
            deduct_compute_costs(self.user_id, graph_size)
            job.mark("completed")
            return job_id
        except Exception as exc:
            job.mark("failed", str(exc))
            raise

    def evaluate_cluster_safety(self) -> bool:
        """Compute gravity telemetry in-process and enforce the safety gate.

        Reads the workspace sandbox payloads, builds an interaction graph,
        computes structural gravity and curvature in-memory, writes the
        metrics manifest to disk, then validates system state natively.
        """
        self._ensure_not_blocked()
        self.gaijinn_dir.mkdir(parents=True, exist_ok=True)

        try:
            graph_data = self._build_graph_data_from_sandboxes()
            telemetry = compute_gravity_and_curvature(graph_data)
            self.metrics_manifest.write_text(
                json.dumps(telemetry, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            if validate_system_state(self.metrics_manifest):
                return True
            self._crash_cluster("system state validation returned TRIPPED")
        except StructuralGravityViolation as exc:
            self._crash_cluster(f"structural gravity violation: {exc}")

        return False

    def _build_graph_data_from_sandboxes(self) -> dict:
        """Build a graph_data dict from all completed agent sandboxes.

        Each completed job becomes a node with capability and side-effect
        scores derived from static analysis of the generated agent code.
        Directed edges connect jobs in completion order.
        """
        nodes: list[dict] = []
        completed_agents: list[str] = []
        heavy_call_names = {"open", "exec", "eval", "socket", "connect"}

        if not self.sandbox_root.exists():
            return {"nodes": [], "edges": []}

        for agent_dir in sorted(self.sandbox_root.iterdir()):
            if not agent_dir.is_dir():
                continue
            output_file = agent_dir / "agent_output.py"
            if not output_file.exists():
                output_file = agent_dir / "generated_agent_output.py"
            if not output_file.exists():
                continue
            agent_id = agent_dir.name
            completed_agents.append(agent_id)

            try:
                source = output_file.read_text(encoding="utf-8")
                syntax_tree = ast.parse(source)
            except SyntaxError:
                capability_level = 1.0
                side_effect_score = 3.0
            else:
                ast_nodes = list(ast.walk(syntax_tree))
                imports_count = sum(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast_nodes)
                side_effect_calls = sum(
                    isinstance(node, ast.Call)
                    and (
                        (isinstance(node.func, ast.Name) and node.func.id in heavy_call_names)
                        or (isinstance(node.func, ast.Attribute) and node.func.attr in heavy_call_names)
                    )
                    for node in ast_nodes
                )
                total_nodes = len(ast_nodes)

                capability_level = min(6.0, 1.0 + (total_nodes / 50.0) + (imports_count * 0.5))
                side_effect_score = min(3.0, (side_effect_calls * 0.75) + (imports_count * 0.25))

            nodes.append(
                {
                    "id": agent_id,
                    "capability_level": capability_level,
                    "side_effect_score": side_effect_score,
                }
            )

        edges: list[dict] = []
        for i in range(len(completed_agents) - 1):
            edges.append(
                {
                    "source": completed_agents[i],
                    "target": completed_agents[i + 1],
                }
            )

        if completed_agents:
            edges.append(
                {
                    "source": completed_agents[-1],
                    "target": completed_agents[0],
                }
            )

        return {"nodes": nodes, "edges": edges}

    def _crash_cluster(self, reason: str) -> None:
        self.blocked = True
        for job in self.jobs.values():
            if job.status in {"queued", "running"}:
                job.mark("blocked", reason)
        self.logger.critical("CATASTROPHIC CLUSTER CRASH: %s", reason)
        raise SystemExit(1)

    def _ensure_not_blocked(self) -> None:
        if self.blocked:
            raise RuntimeError("cluster is blocked after catastrophic safety failure")

    @staticmethod
    def _validate_agent_id(agent_id: str) -> str:
        if not agent_id or Path(agent_id).name != agent_id or agent_id in {".", ".."}:
            raise ValueError(f"unsafe agent_id: {agent_id!r}")
        return agent_id

    @staticmethod
    def _render_mock_agent_code(agent_id: str, prompt_payload: str) -> str:
        escaped_prompt = repr(prompt_payload)
        escaped_agent = repr(agent_id)
        return (
            '"""Generated mock implementation emitted by ClusterOrchestrator."""\n\n'
            f"AGENT_ID = {escaped_agent}\n"
            f"PROMPT_PAYLOAD = {escaped_prompt}\n\n"
            "def run() -> dict[str, str]:\n"
            "    return {\n"
            '        "agent_id": AGENT_ID,\n'
            '        "status": "completed",\n'
            '        "prompt_payload": PROMPT_PAYLOAD,\n'
            "    }\n"
        )
