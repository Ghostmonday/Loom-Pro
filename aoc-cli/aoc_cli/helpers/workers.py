"""Worker grid utilities for Gaijinn CLI commands."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..blueprint import WorkUnit
from ..errors import SafetyError
from ..giv import GIV
from .constants import WORKERS_DIR
from .io import _summary_list, _write_json

# ── Blueprint / work-unit helpers ──────────────────────────────────────


def _project_work_unit(giv: GIV) -> WorkUnit:
    return WorkUnit(
        id="WU-001",
        title="Project-scoped implementation",
        description="Use the compiled Gaijinn intent because no blueprint.json has been generated yet.",
        allowed_paths=giv.allowed_paths,
        denied_paths=giv.denied_paths,
        acceptance_checks=("pytest",),
        estimated_risk="medium",
    )


def _validate_work_unit_paths(work_units: tuple[WorkUnit, ...]) -> None:
    owners: dict[str, str] = {}
    for unit in work_units:
        for path in unit.allowed_paths:
            for owned_path, owner in owners.items():
                if _paths_overlap(Path(owned_path), Path(path)):
                    raise SafetyError(
                        "overlapping worker write paths",
                        cause=f"{unit.id} {path!r} overlaps {owner} {owned_path!r}",
                        fix_command="gaijinn plan --workers 2",
                    )
            owners[path] = unit.id


def _assign_work_units(work_units: tuple[WorkUnit, ...], workers: int) -> dict[int, tuple[WorkUnit, ...]]:
    """Round-robin assign every work unit once; excess workers stay standby (no units)."""
    assignments: dict[int, list[WorkUnit]] = {index: [] for index in range(1, workers + 1)}
    for offset, unit in enumerate(sorted(work_units, key=lambda item: item.id)):
        worker_index = (offset % workers) + 1
        assignments[worker_index].append(unit)
    return {index: tuple(units) for index, units in assignments.items()}


def _standby_allowed_path(worker_name: str) -> str:
    """Narrow write scope for idle workers — no project file overlap."""
    return f".gaijinn/standby/{worker_name}/"


def _paths_overlap(left: Path, right: Path) -> bool:
    left_parts = left.parts
    right_parts = right.parts
    return (
        left_parts == right_parts
        or left_parts == right_parts[: len(left_parts)]
        or right_parts == left_parts[: len(right_parts)]
    )


# ── Worker helpers ─────────────────────────────────────────────────────


def _prepare_workers_root(workers_path: Path, workers: int, force: bool) -> None:
    existing = [workers_path / f"worker-{index:03d}" for index in range(1, workers + 1)]
    conflicts = [path for path in existing if path.exists()]
    manifest = workers_path / "manifest.json"
    if (conflicts or manifest.exists()) and not force:
        raise SafetyError(
            f"{workers_path} already contains worker state",
            cause="use --force to overwrite existing worker handoffs",
            fix_command=f"gaijinn run-grid --workers {workers} --force",
        )
    if not force:
        workers_path.mkdir(parents=True, exist_ok=True)
        return
    if manifest.exists():
        manifest.unlink()
    for path in conflicts:
        _remove_worker_dir(path)
    workers_path.mkdir(parents=True, exist_ok=True)


def _remove_worker_dir(path: Path) -> None:
    if (path / ".git").exists() or path.is_dir():
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(path)],
            cwd=Path.cwd(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    if path.exists():
        shutil.rmtree(path)


def _create_worktree(worker_dir: Path, branch: str) -> None:
    result = subprocess.run(
        ["git", "worktree", "add", "-B", branch, str(worker_dir), "HEAD"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SafetyError(
            f"failed to create git worktree {worker_dir}",
            cause=(result.stderr or result.stdout).strip(),
            fix_command="gaijinn run-grid --workers 2 --force",
        )


def _copy_worker_tree(source: Path, worker_dir: Path) -> None:
    ignore = shutil.ignore_patterns(
        ".git",
        ".gaijinn/workers",
        "workers",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "node_modules",
    )
    shutil.copytree(source, worker_dir, ignore=ignore)


def _sibling_denied_paths(worker_index: int, assignments: dict[int, tuple[WorkUnit, ...]]) -> tuple[str, ...]:
    """Union of allowed_paths from all other workers' assigned work units."""
    own_paths = {path for unit in assignments.get(worker_index, ()) for path in unit.allowed_paths}
    return tuple(
        sorted(
            {
                path
                for index, units in assignments.items()
                if index != worker_index
                for unit in units
                for path in unit.allowed_paths
                if path not in own_paths
            }
        )
    )


def _worker_giv(
    base_giv: GIV,
    worker_name: str,
    units: tuple[WorkUnit, ...],
    assignments: dict[int, tuple[WorkUnit, ...]] | None = None,
) -> GIV:
    if units:
        allowed_paths = tuple(path for unit in units for path in unit.allowed_paths)
    else:
        allowed_paths = (_standby_allowed_path(worker_name),)
    denied_paths = tuple(path for unit in units for path in unit.denied_paths)
    worker_index = _worker_index(worker_name)
    sibling_denied_paths = (
        _sibling_denied_paths(worker_index, assignments) if worker_index is not None and assignments is not None else ()
    )
    return GIV(
        worker_id=worker_name,
        allowed_paths=allowed_paths,
        denied_paths=(*base_giv.denied_paths, *denied_paths, *sibling_denied_paths),
        allowed_commands=base_giv.allowed_commands,
        denied_commands=base_giv.denied_commands,
        capabilities=base_giv.capabilities,
        prohibitions=base_giv.prohibitions,
        invariants=base_giv.invariants,
        structural_tokens=base_giv.structural_tokens,
        sibling_denied_paths=sibling_denied_paths,
    )


def _worker_index(worker_name: str) -> int | None:
    try:
        return int(worker_name.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return None


def _worker_metadata(
    worker_name: str,
    index: int,
    mode: str,
    branch: str | None,
    clean_git: bool | None,
    units: tuple[WorkUnit, ...],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "worker_id": worker_name,
        "index": index,
        "mode": mode,
        "branch": branch,
        "status": "spawning",
        "git_clean": clean_git,
        "assigned_work_units": [unit.id for unit in units],
        "allowed_paths": sorted({path for unit in units for path in unit.allowed_paths}),
    }


def _write_worker_artifacts(
    worker_dir: Path,
    worker_name: str,
    giv: GIV,
    units: tuple[WorkUnit, ...],
    metadata: Mapping[str, Any],
) -> None:
    (worker_dir / "WORKER_INTENT.txt").write_text(giv.render_intent(), encoding="utf-8")
    (worker_dir / "intent.txt").write_text(giv.render_intent(), encoding="utf-8")
    (worker_dir / "WORK_UNIT.md").write_text(_work_unit_markdown(worker_name, units), encoding="utf-8")
    (worker_dir / "giv.json").write_text(giv.to_json(), encoding="utf-8")
    _write_json(worker_dir / "metadata.json", metadata)


def _work_unit_markdown(worker_name: str, units: tuple[WorkUnit, ...]) -> str:
    lines = [
        f"# {worker_name} Work Units",
        "",
    ]
    if not units:
        lines.extend(["No work units assigned.", ""])
        return "\n".join(lines)
    for unit in units:
        lines.extend(
            [
                f"## {unit.id}: {unit.title}",
                "",
                unit.description,
                "",
                f"- Estimated risk: {unit.estimated_risk}",
                f"- Allowed paths: {_summary_list(unit.allowed_paths)}",
                f"- Denied paths: {_summary_list(unit.denied_paths)}",
                f"- Depends on: {_summary_list(unit.depends_on)}",
                "- Acceptance checks:",
                *[f"  - {check}" for check in unit.acceptance_checks],
                "",
            ]
        )
    return "\n".join(lines)


def _worker_count(workers_dir: Path = WORKERS_DIR) -> int:
    if not workers_dir.exists():
        return 0
    return sum(1 for path in workers_dir.iterdir() if path.is_dir() and path.name.startswith("worker-"))
