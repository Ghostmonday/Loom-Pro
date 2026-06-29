"""Layer 2 grid executor — Codex codes work units."""

from __future__ import annotations

from pathlib import Path

from aoc_cli.helpers.grid_executor import (
    build_spawn_command,
    execution_cwd_for_worker,
    project_root_from_worker_dir,
    resolve_grid_executor,
    session_root_from_worker_dir,
)


def test_resolve_grid_executor_prefers_codex(monkeypatch) -> None:
    monkeypatch.setattr("aoc_cli.helpers.grid_executor.shutil.which", lambda name: name == "codex")
    assert resolve_grid_executor("auto") == "codex"
    assert resolve_grid_executor("codex") == "codex"


def test_build_spawn_command_uses_codex_workspace_write(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("aoc_cli.helpers.grid_executor.shutil.which", lambda name: name == "codex")
    project = tmp_path / "session"
    workers = project / ".gaijinn" / "workers" / "worker-001"
    workers.mkdir(parents=True)
    cmd = build_spawn_command(
        worker_name="worker-001",
        worker_dir=workers,
        full_prompt="Implement src/core/",
        model="ignored-for-codex",
        executor="codex",
    )
    assert cmd[0] == "codex"
    assert "workspace-write" in cmd
    assert str(workers.resolve()) in cmd
    assert str(project.resolve()) not in cmd
    assert "Implement src/core/" in cmd[-1]


def test_build_spawn_command_falls_back_to_grok(monkeypatch) -> None:
    monkeypatch.setattr(
        "aoc_cli.helpers.grid_executor.shutil.which",
        lambda name: name == "grok",
    )
    cmd = build_spawn_command(
        worker_name="worker-001",
        worker_dir=Path("/data/session/.gaijinn/workers/worker-001"),
        full_prompt="task",
        model="grok-composer-2.5-fast",
        executor="auto",
    )
    assert cmd[0] == "grok"


def test_session_root_from_worker_dir() -> None:
    worker = Path("/data/session/.gaijinn/workers/worker-002")
    assert session_root_from_worker_dir(worker) == Path("/data/session")
    assert project_root_from_worker_dir(worker) == Path("/data/session")


def test_execution_cwd_for_worker_uses_checkout() -> None:
    worker = Path("/data/session/.gaijinn/workers/worker-002")
    assert execution_cwd_for_worker(worker) == worker.resolve()


def test_build_spawn_command_uses_deepseek_via_codex(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("aoc_cli.helpers.grid_executor.shutil.which", lambda name: name == "codex")
    project = tmp_path / "vault"
    workers = project / ".gaijinn" / "workers" / "worker-001"
    workers.mkdir(parents=True)
    cmd = build_spawn_command(
        worker_name="worker-001",
        worker_dir=workers,
        full_prompt="Promote pending concept",
        model="deepseek-v4-flash",
        executor="deepseek",
    )
    assert cmd[0] == "codex"
    assert "-m" in cmd
    assert "deepseek-v4-flash" in cmd
    assert "workspace-write" in cmd
