"""Build sessions — intent → blueprint → swarm (stealth math, user-facing stats only).

GAIJINN BLUEPRINT — session orchestration
-----------------------------------------
Layer: Orchestration (prepare → assign_swarm → ready_to_deploy)
Status: partial — happy path + merge + multi-phase advance re-blueprint wired; failed phase pending
Spec: ui/gaijinn-ui-intent-map.json state_machine.transitions
API: POST /orchestrate/prepare, POST /orchestrate/swarm

Product narrative: Intent → Blueprint → Swarm → Deploy → Complete
Phases stored in .gaijinn/sessions/<id>/session.json (not exposed as raw blueprint)

AI agents — DO
  - Keep prepare() idempotent per session_id; assign_swarm only run-grid
  - Return swarm_warning when workers > work_units (honest idle_agents)
  - Use intent_mode=True sizing when blueprint_mode=intent
  - Default greenfield: gaijinn plan (gravity/curvature); keyword only when GAIJINN_KEYWORD_GREENFIELD=1

AI agents — DON'T
  - Re-run gaijinn plan inside assign_swarm (blueprint frozen at prepare)
  - Expose graph.json / curvature / shadow-bridge stats to terminal (stealth)

Gaps (planned, not coded)
  - Phase ``failed`` + deploy.failure transition in terminal
  - Session persistence across server restarts (in-memory _active index only)
  - Brownfield intent that blends graph plan + intent streams

Robustness path
  - Session recovery from disk without _active cache
  - Structured errors surfaced to Phase.FAILED without council noise
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aoc_cli.helpers.council import append_message
from aoc_cli.helpers.merge import (
    compute_merge_structural_score,
    format_structural_score_council_message,
    merge_pipeline_status,
    record_merge_governance_history,
    write_merge_governance,
)

from aoc_supervisor.intent_blueprint import (
    detect_intent_streams,
    is_greenfield_intent,
    swarm_rationale,
    swarm_warning,
    write_intent_blueprint,
)
from aoc_supervisor.session_security import resolve_confined_session_path, validate_session_id

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PROJECT = REPO_ROOT / "examples" / "tiny-python-service"
# Design phase: each gaijinn stage may run as long as the project needs.
DESIGN_COMMAND_TIMEOUT_DEFAULT = 3600
DESIGN_COMMAND_TIMEOUT_MAX = 14_400
CANONICAL_PHASES: tuple[str, ...] = ("backend", "frontend", "testing")
PHASE_LABELS: dict[str, str] = {"backend": "Backend", "frontend": "Frontend", "testing": "Testing"}


def normalize_phases(phases: Any = None) -> tuple[str, ...]:
    """Validate pipeline run phases and return canonical execution order."""
    if phases is None:
        return ("backend",)
    if not isinstance(phases, list) or not phases:
        raise ValueError("phases must be a non-empty list")
    selected: set[str] = set()
    for phase in phases:
        if not isinstance(phase, str):
            raise ValueError("phases must contain phase names")
        phase_id = phase.strip().lower()
        if phase_id not in CANONICAL_PHASES:
            raise ValueError(f"unknown phase: {phase}")
        if phase_id in selected:
            raise ValueError(f"duplicate phase: {phase_id}")
        selected.add(phase_id)
    return tuple(phase for phase in CANONICAL_PHASES if phase in selected)


def _normalize_loaded_context(loaded_context: Any = None) -> dict[str, Any]:
    if loaded_context is None:
        return {}
    if not isinstance(loaded_context, dict):
        raise ValueError("loaded_context must be an object")

    normalized: dict[str, Any] = {}
    for end in ("backend", "frontend"):
        value = loaded_context.get(end)
        if value is None:
            continue
        if not isinstance(value, dict):
            raise ValueError(f"loaded_context.{end} must be an object")
        source = {str(k): v for k, v in value.items() if k in {"prior_session_id", "zip_path", "project_path"} and v}
        if not source:
            raise ValueError(f"loaded_context.{end} must include prior_session_id, zip_path, or project_path")
        if "project_path" in source and not Path(str(source["project_path"])).expanduser().exists():
            raise ValueError(f"loaded_context.{end}.project_path does not exist")
        if "zip_path" in source and not Path(str(source["zip_path"])).expanduser().exists():
            raise ValueError(f"loaded_context.{end}.zip_path does not exist")
        normalized[end] = source
    return normalized


def _required_loaded_ends(phases: tuple[str, ...]) -> tuple[str, ...]:
    selected = set(phases)
    if selected == {"testing"}:
        return ("backend", "frontend")
    if selected == {"frontend", "testing"}:
        return ("backend",)
    if selected == {"backend", "testing"}:
        return ("frontend",)
    return ()


def _phase_warning(phases: tuple[str, ...], loaded_context: dict[str, Any]) -> str | None:
    if phases == ("frontend",) and "backend" not in loaded_context:
        return "backend context is recommended before preparing a frontend-only phase"
    return None


def _loaded_context_ref(end_context: dict[str, Any]) -> str:
    return str(end_context.get("prior_session_id") or end_context.get("project_path") or "loaded")


def _record_completed_phase_in_loaded_context(
    loaded_context: dict[str, Any],
    completed_phase: str,
    session_id: str,
    session_root: Path,
) -> dict[str, Any]:
    """Attach merged deliverable for a completed pipeline end."""
    updated = dict(loaded_context)
    updated[completed_phase] = {
        "prior_session_id": session_id,
        "project_path": str(session_root.resolve()),
    }
    return updated


def _phase_advance_intent(next_phase: str, base_intent: str, loaded_context: dict[str, Any]) -> str:
    """Compose phase-specific intent for re-blueprint after merge."""
    base = base_intent.strip()
    if next_phase == "frontend":
        backend_ref = _loaded_context_ref(loaded_context.get("backend", {}))
        return f"Build frontend UI integrating with backend context ({backend_ref}) for: {base}"
    if next_phase == "backend":
        frontend_ref = _loaded_context_ref(loaded_context.get("frontend", {}))
        return f"Build backend services integrating with frontend context ({frontend_ref}) for: {base}"
    if next_phase == "testing":
        refs = [
            f"{end}={_loaded_context_ref(loaded_context[end])}"
            for end in ("backend", "frontend")
            if end in loaded_context
        ]
        ctx = ", ".join(refs) if refs else "merged deliverable"
        return f"Run acceptance tests and integration tests against {ctx} for: {base}"
    return base


def _reset_swarm_artifacts(session_root: Path) -> None:
    workers_dir = session_root / ".gaijinn" / "workers"
    if workers_dir.exists():
        shutil.rmtree(workers_dir)


def _annotate_blueprint_loaded_context(session_root: Path, loaded_context: dict[str, Any]) -> None:
    blueprint_path = session_root / ".gaijinn" / "blueprint.json"
    if not blueprint_path.exists():
        return
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    blueprint["loaded_context"] = loaded_context
    blueprint_path.write_text(json.dumps(blueprint, indent=2) + "\n", encoding="utf-8")


def _run_blueprint_pipeline(
    session_root: Path,
    intent: str,
    *,
    command_timeout: int | None = None,
    use_intent_blueprint: bool = False,
    loaded_context: dict[str, Any] | None = None,
) -> tuple[int, int, tuple[str, ...], str, tuple[str, ...]]:
    """Scan → analyze → compile-prompt → plan or intent blueprint."""
    timeout = design_command_timeout(command_timeout)
    _run_gaijinn(session_root, "scan", ".", timeout=timeout)
    _run_gaijinn(session_root, "analyze", timeout=timeout)
    _run_gaijinn(session_root, "compile-prompt", timeout=timeout)

    blueprint_mode = "graph"
    work_stream_titles: tuple[str, ...] = ()
    if use_intent_blueprint:
        blueprint = write_intent_blueprint(session_root, intent)
        _assert_greenfield_blueprint(blueprint)
        blueprint_mode = "intent"
        work_stream_titles = tuple(blueprint.get("work_stream_titles", ()))
    else:
        _run_gaijinn(session_root, "plan", "--workers", "4", timeout=timeout)

    if loaded_context:
        _annotate_blueprint_loaded_context(session_root, loaded_context)

    work_units, high_risk, titles, mode = _read_blueprint_stats(session_root)
    if not work_stream_titles:
        work_stream_titles = titles
    return work_units, high_risk, titles, blueprint_mode or mode, work_stream_titles


def validate_loaded_context(phases: tuple[str, ...], loaded_context: Any = None) -> dict[str, Any]:
    normalized = _normalize_loaded_context(loaded_context)
    missing = [end for end in _required_loaded_ends(phases) if end not in normalized]
    if missing:
        needed = ", ".join(missing)
        phase_text = " + ".join(PHASE_LABELS.get(phase, phase) for phase in phases)
        raise ValueError(f"{phase_text} requires loaded context first: {needed}")
    return normalized


def _pipeline_plan(
    phases: tuple[str, ...], current_index: int = 0, completed: list[str] | None = None
) -> dict[str, Any]:
    current_index = max(0, min(current_index, len(phases) - 1))
    return {
        "phases": list(phases),
        "current_index": current_index,
        "current_phase": phases[current_index],
        "completed_phases": list(completed or []),
    }


@dataclass(frozen=True)
class SessionSnapshot:
    session_id: str
    intent: str
    project_root: Path
    work_units: int
    high_risk_units: int
    workers_ready: int
    phase: str
    work_stream_titles: tuple[str, ...] = ()
    swarm_rationale: str = ""
    blueprint_mode: str = "graph"
    selected_swarm: int | None = None
    swarm_warning: str | None = None
    idle_agents: int = 0
    phases: tuple[str, ...] = ("backend",)
    current_phase: str = "backend"
    pipeline_plan: dict[str, Any] | None = None
    loaded_context: dict[str, Any] | None = None
    phase_warning: str | None = None
    phase_message: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        intent_mode = self.blueprint_mode == "intent"
        recommended = _recommend_swarm(self.work_units, intent_mode=intent_mode)
        payload: dict[str, Any] = {
            "session_id": self.session_id,
            "intent": self.intent,
            "work_units": self.work_units,
            "high_risk_units": self.high_risk_units,
            "workers_ready": self.workers_ready,
            "phase": self.phase,
            "phases": list(self.phases),
            "current_phase": self.current_phase,
            "phase_count": len(self.phases),
            "pipeline_plan": self.pipeline_plan or _pipeline_plan(self.phases),
            "loaded_context": self.loaded_context or {},
            "suggested_swarm": _suggest_swarm(self.work_units, intent_mode=intent_mode),
            "recommended_swarm": recommended,
            "work_stream_titles": list(self.work_stream_titles),
            "swarm_rationale": self.swarm_rationale
            or swarm_rationale(
                list(detect_intent_streams(self.intent)),
                recommended,
            ),
            "blueprint_mode": self.blueprint_mode,
            "max_productive_swarm": self.work_units,
        }
        if self.selected_swarm is not None:
            payload["selected_swarm"] = self.selected_swarm
        if self.swarm_warning:
            payload["swarm_warning"] = self.swarm_warning
            payload["idle_agents"] = self.idle_agents
        if self.phase_warning:
            payload["phase_warning"] = self.phase_warning
        if self.phase_message:
            payload["message"] = self.phase_message
        return payload


def _recommend_swarm(work_units: int, *, intent_mode: bool = False) -> int:
    """Single recommended swarm size from blueprint complexity."""
    if intent_mode:
        if work_units <= 1:
            return 1
        return min(16, max(2, work_units))
    if work_units <= 1:
        return 1
    if work_units <= 4:
        return min(4, max(2, work_units))
    if work_units <= 12:
        return min(8, max(4, (work_units + 2) // 3))
    return min(16, max(8, (work_units + 3) // 4))


def _suggest_swarm(work_units: int, *, intent_mode: bool = False) -> list[int]:
    recommended = _recommend_swarm(work_units, intent_mode=intent_mode)
    if intent_mode:
        options = {recommended}
        if work_units > 2:
            half = max(2, work_units // 2)
            if half != recommended:
                options.add(half)
        if work_units >= 6 and recommended < 16:
            options.add(min(16, recommended + 2))
        return sorted(options)
    if work_units <= 1:
        return [1, 2]
    if work_units <= 4:
        return sorted({max(2, work_units - 1), recommended} if work_units > 2 else {1, 2, recommended})
    if work_units <= 12:
        return sorted({max(2, work_units // 2), recommended, min(16, work_units + 2)})
    return sorted({max(4, work_units // 2), recommended, min(16, work_units + 2)})


def design_command_timeout(requested: int | None = None) -> int:
    """Resolve per-command timeout for init/scan/analyze/plan (seconds)."""
    if requested is not None:
        return max(60, min(int(requested), DESIGN_COMMAND_TIMEOUT_MAX))
    env_raw = os.environ.get("GAIJINN_DESIGN_TIMEOUT", "").strip()
    if env_raw.isdigit():
        return max(60, min(int(env_raw), DESIGN_COMMAND_TIMEOUT_MAX))
    return DESIGN_COMMAND_TIMEOUT_DEFAULT


def _repo_venv_python() -> Path | None:
    """Prefer the repo-local venv interpreter (has networkx, numpy, etc.)."""
    override = os.environ.get("GAIJINN_PYTHON", "").strip()
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file():
            return candidate
    venv_bin = REPO_ROOT / ".venv" / "bin"
    for name in ("python3.11", "python3", "python"):
        candidate = venv_bin / name
        # Keep the .venv/bin wrapper path — resolving uv symlinks drops site-packages.
        if candidate.is_file():
            return candidate
    return None


def _gaijinn_python() -> str:
    """Absolute interpreter path — safe when cwd is a temp session root."""
    venv_python = _repo_venv_python()
    if venv_python is not None:
        return str(venv_python.expanduser())
    exe = Path(sys.executable)
    if exe.is_file():
        return str(exe.resolve())
    fallback = shutil.which("python3")
    if fallback:
        return fallback
    raise RuntimeError(f"Python interpreter not found: {sys.executable!r}")


def _pythonpath_env() -> dict[str, str]:
    env = os.environ.copy()
    venv_python = _repo_venv_python()
    if venv_python is not None:
        venv_root = venv_python.parent.parent
        env["VIRTUAL_ENV"] = str(venv_root)
        env["PATH"] = os.pathsep.join([str(venv_python.parent), env.get("PATH", "")])
    else:
        env.pop("VIRTUAL_ENV", None)
    env.pop("PYTHON", None)
    roots = [str((REPO_ROOT / "aoc-cli").resolve()), str((REPO_ROOT / "aoc_supervisor").resolve())]
    existing = env.get("PYTHONPATH", "")
    existing_roots = [str(Path(item).expanduser().resolve()) for item in existing.split(os.pathsep) if item]
    env["PYTHONPATH"] = os.pathsep.join([*roots, *existing_roots])
    return env


def _run_gaijinn(project_root: Path, *args: str, timeout: int | None = None) -> None:
    effective_timeout = design_command_timeout(timeout)
    result = subprocess.run(
        [_gaijinn_python(), "-m", "aoc_cli", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=effective_timeout,
        env=_pythonpath_env(),
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "gaijinn command failed").strip()
        raise RuntimeError(f"gaijinn {' '.join(args)} failed: {detail[-2000:]}")


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    for key, value in (
        ("GIT_AUTHOR_NAME", "gaijinn"),
        ("GIT_AUTHOR_EMAIL", "gaijinn@local"),
        ("GIT_COMMITTER_NAME", "gaijinn"),
        ("GIT_COMMITTER_EMAIL", "gaijinn@local"),
    ):
        env.setdefault(key, value)
    return env


def _git_executable() -> str:
    git = shutil.which("git")
    if not git:
        raise RuntimeError("git executable not found on PATH")
    return git


def _ensure_session_git_repo(session_root: Path) -> None:
    """Merge collect requires a resolvable base ref; seeded sessions are not git worktrees."""
    if (session_root / ".git").exists():
        return
    git = _git_executable()
    init = subprocess.run(
        [git, "init", "-b", "main"],
        cwd=session_root,
        capture_output=True,
        text=True,
        check=False,
        env=_git_env(),
    )
    if init.returncode != 0:
        detail = (init.stderr or init.stdout or "git init failed").strip()
        raise RuntimeError(f"session git init failed: {detail[-500:]}")
    subprocess.run([git, "add", "-A"], cwd=session_root, capture_output=True, check=False, env=_git_env())
    commit = subprocess.run(
        [git, "-c", "commit.gpgsign=false", "commit", "-m", "gaijinn session seed", "--allow-empty"],
        cwd=session_root,
        capture_output=True,
        text=True,
        check=False,
        env=_git_env(),
    )
    if commit.returncode != 0:
        detail = (commit.stderr or commit.stdout or "git commit failed").strip()
        raise RuntimeError(f"session git commit failed: {detail[-500:]}")


def _seed_session_project(session_root: Path, intent: str) -> None:
    if not TEMPLATE_PROJECT.exists():
        raise RuntimeError(f"template project missing: {TEMPLATE_PROJECT}")
    shutil.copytree(
        TEMPLATE_PROJECT,
        session_root,
        dirs_exist_ok=False,
        ignore=shutil.ignore_patterns(".gaijinn", "__pycache__", "*.pyc", ".pytest_cache"),
    )
    gaijinn_dir = session_root / ".gaijinn"
    gaijinn_dir.mkdir(parents=True, exist_ok=True)
    (gaijinn_dir / "intent.txt").write_text(intent.strip() + "\n", encoding="utf-8")
    _ensure_session_git_repo(session_root)


def _keyword_greenfield_enabled() -> bool:
    """Legacy keyword STREAM_SPECS path; off by default (ENG-103 gravity greenfield)."""
    return os.environ.get("GAIJINN_KEYWORD_GREENFIELD", "").strip() == "1"


def _read_blueprint_stats(project_root: Path) -> tuple[int, int, tuple[str, ...], str]:
    blueprint_path = project_root / ".gaijinn" / "blueprint.json"
    if not blueprint_path.exists():
        return 0, 0, (), "graph"
    payload = json.loads(blueprint_path.read_text(encoding="utf-8"))
    units = payload.get("work_units", [])
    if not isinstance(units, list):
        return 0, 0, (), str(payload.get("blueprint_mode", "graph"))
    high_risk = sum(
        1 for unit in units if isinstance(unit, dict) and str(unit.get("estimated_risk", "low")).lower() == "high"
    )
    titles = tuple(str(unit.get("title", "")) for unit in units if isinstance(unit, dict) and unit.get("title"))
    mode = str(payload.get("blueprint_mode", "graph"))
    return len(units), high_risk, titles, mode


def _assert_greenfield_blueprint(payload: dict[str, Any], *, keyword_mode: bool = False) -> None:
    """Validate frozen blueprint for greenfield orchestrate sessions."""
    mode = str(payload.get("blueprint_mode", "graph"))
    if keyword_mode:
        if mode != "intent":
            raise RuntimeError("keyword greenfield sessions must freeze an intent blueprint")
    elif mode == "intent" and payload.get("projection_mode") not in ("intent_forge", "keyword"):
        raise RuntimeError("graph greenfield sessions must use gravity blueprint metadata")
    paths = [
        str(path)
        for unit in payload.get("work_units", [])
        if isinstance(unit, dict)
        for path in unit.get("allowed_paths", [])
    ]
    if len(paths) != len(set(paths)):
        raise RuntimeError("greenfield blueprint emitted duplicate allowed paths")
    if keyword_mode and any("tiny_service" in path for path in paths):
        raise RuntimeError("keyword greenfield blueprint leaked tiny_service template paths")


def _workers_in_manifest(project_root: Path) -> int:
    manifest_path = project_root / ".gaijinn" / "workers" / "manifest.json"
    if not manifest_path.exists():
        return 0
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    details = payload.get("worker_details", [])
    if isinstance(details, list) and details:
        return len(details)
    return int(payload.get("worker_count", 0) or 0)


def _snapshot_from_meta(session_root: Path, meta: dict[str, Any]) -> SessionSnapshot:
    work_units, high_risk, titles, mode = _read_blueprint_stats(session_root)
    streams = tuple(meta.get("work_stream_titles", titles)) or titles
    blueprint_mode = str(meta.get("blueprint_mode", mode))
    phases = normalize_phases(meta.get("phases"))
    current_phase = str(meta.get("current_phase", phases[0]))
    pipeline_plan = meta.get("pipeline_plan")
    if not isinstance(pipeline_plan, dict):
        pipeline_plan = _pipeline_plan(phases)
    intent_mode = blueprint_mode == "intent"
    recommended = _recommend_swarm(work_units, intent_mode=intent_mode)
    return SessionSnapshot(
        session_id=str(meta["session_id"]),
        intent=str(meta.get("intent", "")),
        project_root=session_root,
        work_units=work_units,
        high_risk_units=high_risk,
        workers_ready=int(meta.get("workers_ready", _workers_in_manifest(session_root))),
        phase=str(meta.get("phase", "unknown")),
        work_stream_titles=streams,
        swarm_rationale=str(
            meta.get(
                "swarm_rationale",
                swarm_rationale(list(detect_intent_streams(str(meta.get("intent", "")))), recommended),
            )
        ),
        blueprint_mode=blueprint_mode,
        selected_swarm=meta.get("selected_swarm"),
        swarm_warning=meta.get("swarm_warning"),
        idle_agents=int(meta.get("idle_agents", 0)),
        phases=phases,
        current_phase=current_phase,
        pipeline_plan=pipeline_plan,
        loaded_context=dict(meta.get("loaded_context", {})) if isinstance(meta.get("loaded_context"), dict) else {},
        phase_warning=meta.get("phase_warning"),
        phase_message=meta.get("phase_message"),
    )


class OrchestrateSessionStore:
    """In-memory session index; artifacts live on disk under .gaijinn/sessions/."""

    def __init__(self, host_root: Path) -> None:
        self.host_root = host_root.resolve()
        self.sessions_dir = self.host_root / ".gaijinn" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._active: dict[str, Path] = {}

    def prepare(
        self,
        intent: str,
        phases: Any = None,
        loaded_context: Any = None,
        *,
        owner_user_id: str = "anonymous",
        on_step: Any = None,
        layer1_timeout: int | None = None,
        executable_blueprint: dict[str, Any] | None = None,
        orchestrate_session_id: str | None = None,
    ) -> SessionSnapshot:
        # GAIJINN: default greenfield + brownfield → gaijinn plan (gravity). Keyword only via env.
        intent = intent.strip()
        if not intent:
            raise ValueError("intent is required")
        normalized_phases = normalize_phases(phases)
        normalized_loaded_context = validate_loaded_context(normalized_phases, loaded_context)
        phase_warning = _phase_warning(normalized_phases, normalized_loaded_context)
        pipeline_plan = _pipeline_plan(normalized_phases)

        session_id = (orchestrate_session_id or uuid.uuid4().hex[:12]).strip()
        session_root = self.sessions_dir / session_id
        if session_root.exists() and orchestrate_session_id is None:
            raise RuntimeError(f"session collision: {session_id}")

        command_timeout = design_command_timeout(layer1_timeout)

        def _emit(step: str, payload: dict[str, Any] | None = None) -> None:
            if on_step is not None:
                on_step(step, payload or {})

        _emit(
            "session_seed",
            {
                "session_id": session_id,
                "session_root": str(session_root),
                "layer1_timeout_s": command_timeout,
            },
        )
        _seed_session_project(session_root, intent)

        blueprint_mode = "graph"
        work_stream_titles: tuple[str, ...] = ()
        if executable_blueprint is not None:
            _emit("intent_forge_projection_start", {})
            gaijinn_dir = session_root / ".gaijinn"
            gaijinn_dir.mkdir(parents=True, exist_ok=True)
            blueprint_path = gaijinn_dir / "blueprint.json"
            blueprint_path.write_text(json.dumps(executable_blueprint, indent=2) + "\n", encoding="utf-8")
            blueprint = executable_blueprint
            _assert_greenfield_blueprint(blueprint, keyword_mode=True)
            projection_mode = str(blueprint.get("projection_mode", ""))
            blueprint_mode = (
                "loom_synthesis"
                if projection_mode == "loom_synthesis"
                else str(blueprint.get("blueprint_mode", "intent"))
            )
            work_stream_titles = tuple(blueprint.get("work_stream_titles", ()))
            _emit("intent_forge_projection_complete", {"work_streams": len(work_stream_titles)})
        else:
            _emit("init_start", {"layer1_timeout_s": command_timeout})
            _run_gaijinn(session_root, "init", "--force", "--no-agent-files", intent, timeout=command_timeout)
            _emit("init_complete", {})
            _emit("scan_start", {})
            _run_gaijinn(session_root, "scan", ".", timeout=command_timeout)
            _emit("scan_complete", {})
            _emit("analyze_start", {})
            _run_gaijinn(session_root, "analyze", timeout=command_timeout)
            _emit("analyze_complete", {})
            _emit("compile_prompt_start", {})
            _run_gaijinn(session_root, "compile-prompt", timeout=command_timeout)
            _emit("compile_prompt_complete", {})

            if is_greenfield_intent(intent) and _keyword_greenfield_enabled():
                _emit("intent_blueprint_start", {})
                blueprint = write_intent_blueprint(session_root, intent)
                _assert_greenfield_blueprint(blueprint, keyword_mode=True)
                blueprint_mode = "intent"
                work_stream_titles = tuple(blueprint.get("work_stream_titles", ()))
                _emit("intent_blueprint_complete", {"work_streams": len(work_stream_titles)})
            else:
                _emit("plan_start", {"workers": 4})
                _run_gaijinn(session_root, "plan", "--workers", "4", timeout=command_timeout)
                _emit("plan_complete", {})
                if is_greenfield_intent(intent):
                    blueprint_path = session_root / ".gaijinn" / "blueprint.json"
                    if blueprint_path.exists():
                        blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
                        _assert_greenfield_blueprint(blueprint, keyword_mode=False)

        work_units, high_risk, titles, mode = _read_blueprint_stats(session_root)
        if not work_stream_titles:
            work_stream_titles = titles
        recommended = _recommend_swarm(work_units, intent_mode=(blueprint_mode == "intent"))
        rationale = swarm_rationale(list(detect_intent_streams(intent)), recommended)

        self._active[session_id] = session_root
        meta = {
            "session_id": session_id,
            "owner_user_id": owner_user_id.strip() or "anonymous",
            "intent": intent,
            "work_units": work_units,
            "high_risk_units": high_risk,
            "phase": "awaiting_swarm",
            "phases": list(normalized_phases),
            "current_phase": normalized_phases[0],
            "pipeline_plan": pipeline_plan,
            "loaded_context": normalized_loaded_context,
            "phase_warning": phase_warning,
            "blueprint_mode": blueprint_mode or mode,
            "work_stream_titles": list(work_stream_titles),
            "swarm_rationale": rationale,
        }
        (session_root / ".gaijinn" / "session.json").write_text(
            json.dumps(meta, indent=2) + "\n",
            encoding="utf-8",
        )
        return SessionSnapshot(
            session_id=session_id,
            intent=intent,
            project_root=session_root,
            work_units=work_units,
            high_risk_units=high_risk,
            workers_ready=0,
            phase="awaiting_swarm",
            work_stream_titles=work_stream_titles,
            swarm_rationale=rationale,
            blueprint_mode=blueprint_mode or mode,
            phases=normalized_phases,
            current_phase=normalized_phases[0],
            pipeline_plan=pipeline_plan,
            loaded_context=normalized_loaded_context,
            phase_warning=phase_warning,
        )

    def assign_swarm(self, session_id: str, workers: int) -> SessionSnapshot:
        if workers < 1 or workers > 16:
            raise ValueError("workers must be between 1 and 16")
        session_root = self._resolve(session_id)
        meta_path = session_root / ".gaijinn" / "session.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        intent = str(meta.get("intent", ""))

        # GAIJINN: blueprint frozen at prepare — only run-grid here (no re-plan).
        _run_gaijinn(session_root, "run-grid", "--workers", str(workers), "--force")

        work_units, high_risk, titles, mode = _read_blueprint_stats(session_root)
        ready = _workers_in_manifest(session_root)
        warning = swarm_warning(workers, work_units)
        idle_agents = max(0, workers - work_units) if warning else 0
        phases = normalize_phases(meta.get("phases"))
        pipeline_plan = meta.get("pipeline_plan")
        if not isinstance(pipeline_plan, dict):
            pipeline_plan = _pipeline_plan(phases)
        meta.update(
            {
                "workers_ready": ready,
                "phase": "ready_to_deploy",
                "selected_swarm": workers,
                "swarm_warning": warning,
                "idle_agents": idle_agents,
                "work_units": work_units,
                "high_risk_units": high_risk,
                "blueprint_mode": meta.get("blueprint_mode", mode),
            }
        )
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        self._active[session_id] = session_root
        return SessionSnapshot(
            session_id=session_id,
            intent=intent,
            project_root=session_root,
            work_units=work_units,
            high_risk_units=high_risk,
            workers_ready=ready,
            phase="ready_to_deploy",
            work_stream_titles=tuple(meta.get("work_stream_titles", titles)),
            swarm_rationale=str(meta.get("swarm_rationale", "")),
            blueprint_mode=str(meta.get("blueprint_mode", mode)),
            selected_swarm=workers,
            swarm_warning=warning,
            idle_agents=idle_agents,
            phases=phases,
            current_phase=str(meta.get("current_phase", phases[0])),
            pipeline_plan=pipeline_plan,
            loaded_context=dict(meta.get("loaded_context", {})) if isinstance(meta.get("loaded_context"), dict) else {},
            phase_warning=meta.get("phase_warning"),
        )

    def workers_dir(self, session_id: str) -> Path:
        return self._resolve(session_id) / ".gaijinn" / "workers"

    def get(self, session_id: str) -> SessionSnapshot:
        session_root = self._resolve(session_id)
        meta = json.loads((session_root / ".gaijinn" / "session.json").read_text(encoding="utf-8"))
        return _snapshot_from_meta(session_root, meta)

    def project_root(self, session_id: str) -> Path:
        return self._resolve(session_id)

    def merge_status(self, session_id: str) -> dict[str, Any]:
        return merge_pipeline_status(self._resolve(session_id))

    def run_merge(self, session_id: str) -> dict[str, Any]:
        session_root = self._resolve(session_id)
        _ensure_session_git_repo(session_root)
        meta_path = session_root / ".gaijinn" / "session.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["phase"] = "merging"
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

        try:
            _run_gaijinn(session_root, "collect")
            _run_gaijinn(session_root, "validate-worker")
            merge_args = ["merge-grid"]
            if os.environ.get("GAIJINN_SKIP_MERGE_TESTS", "").strip().lower() in {"1", "true", "yes", "on"}:
                merge_args.append("--no-test")
            if os.environ.get("GAIJINN_MOCK_GRID", "").strip().lower() in {"1", "true", "yes", "on"}:
                merge_args.append("--dry-run")
            _run_gaijinn(session_root, *merge_args)
        except Exception:
            meta["phase"] = "merge_failed"
            meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
            raise

        phases = normalize_phases(meta.get("phases"))
        plan = meta.get("pipeline_plan")
        if not isinstance(plan, dict):
            plan = _pipeline_plan(phases)
        current_index = int(plan.get("current_index", 0) or 0)
        completed = list(plan.get("completed_phases", [])) if isinstance(plan.get("completed_phases"), list) else []
        current_phase = str(meta.get("current_phase", phases[current_index]))
        if current_phase not in completed:
            completed.append(current_phase)
        plan.update(
            {
                "phases": list(phases),
                "current_index": current_index,
                "current_phase": current_phase,
                "completed_phases": completed,
            }
        )
        meta["pipeline_plan"] = plan
        meta["phase"] = "awaiting_next_phase" if current_index + 1 < len(phases) else "merge_complete"
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

        score = compute_merge_structural_score(session_root)
        write_merge_governance(session_root, score)
        record_merge_governance_history(session_root, score)
        with contextlib.suppress(OSError, ValueError):
            append_message(
                format_structural_score_council_message(score, session_id=session_id),
                author="gaijinn",
                author_id="merge-governance",
                global_council=True,
            )

        merge_payload = merge_pipeline_status(session_root)
        return {
            "session_id": session_id,
            "phase": meta["phase"],
            "current_phase": current_phase,
            "pipeline_plan": plan,
            "merge_pipeline": merge_payload,
            "structural_score": merge_payload.get("structural_score"),
            "governance_path": merge_payload.get("governance_path"),
        }

    def advance_phase(self, session_id: str, *, layer1_timeout: int | None = None) -> SessionSnapshot:
        session_root = self._resolve(session_id)
        meta_path = session_root / ".gaijinn" / "session.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        phases = normalize_phases(meta.get("phases"))
        plan = meta.get("pipeline_plan")
        if not isinstance(plan, dict):
            plan = _pipeline_plan(phases)
        current_index = int(plan.get("current_index", 0) or 0)
        if current_index + 1 >= len(phases):
            raise ValueError("no remaining phases to advance")
        if str(meta.get("phase", "")) != "awaiting_next_phase":
            raise ValueError("current phase must be merged before advancing")

        next_index = current_index + 1
        next_phase = phases[next_index]
        current_phase = str(meta.get("current_phase", phases[current_index]))
        base_intent = str(meta.get("intent", ""))
        session_id_str = str(meta["session_id"])

        raw_loaded = meta.get("loaded_context", {})
        loaded_context = dict(raw_loaded) if isinstance(raw_loaded, dict) else {}
        loaded_context = _record_completed_phase_in_loaded_context(
            loaded_context,
            current_phase,
            session_id_str,
            session_root,
        )
        loaded_context = validate_loaded_context(phases, loaded_context)

        phase_intent = _phase_advance_intent(next_phase, base_intent, loaded_context)
        use_intent_blueprint = str(meta.get("blueprint_mode", "graph")) == "intent"
        (session_root / ".gaijinn" / "intent.txt").write_text(phase_intent.strip() + "\n", encoding="utf-8")
        _reset_swarm_artifacts(session_root)

        work_units, high_risk, _titles, mode, work_stream_titles = _run_blueprint_pipeline(
            session_root,
            phase_intent,
            command_timeout=layer1_timeout,
            use_intent_blueprint=use_intent_blueprint,
            loaded_context=loaded_context,
        )
        recommended = _recommend_swarm(work_units, intent_mode=(mode == "intent"))
        rationale = swarm_rationale(list(detect_intent_streams(phase_intent)), recommended)
        context_ends = ", ".join(sorted(loaded_context)) or "none"
        message = (
            f"{PHASE_LABELS[next_phase]} phase blueprint ready — {work_units} work units "
            f"(loaded context: {context_ends})"
        )

        plan.update({"phases": list(phases), "current_index": next_index, "current_phase": next_phase})
        meta.update(
            {
                "phase": "awaiting_swarm",
                "current_phase": next_phase,
                "pipeline_plan": plan,
                "loaded_context": loaded_context,
                "phase_message": message,
                "phase_intent_context": phase_intent,
                "workers_ready": 0,
                "selected_swarm": None,
                "swarm_warning": None,
                "idle_agents": 0,
                "work_units": work_units,
                "high_risk_units": high_risk,
                "blueprint_mode": mode,
                "work_stream_titles": list(work_stream_titles),
                "swarm_rationale": rationale,
            }
        )
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        return _snapshot_from_meta(session_root, meta)

    def _resolve(self, session_id: str) -> Path:
        normalized = validate_session_id(session_id)
        if normalized in self._active:
            active = self._active[normalized].resolve()
            resolve_confined_session_path(self.sessions_dir, normalized)
            return active
        candidate = resolve_confined_session_path(self.sessions_dir, normalized)
        self._active[normalized] = candidate
        return candidate
