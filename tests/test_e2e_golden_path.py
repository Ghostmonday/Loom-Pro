from __future__ import annotations

import json
import shutil
from pathlib import Path

from aoc_cli.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_tiny_python_service_golden_path(tmp_path, monkeypatch) -> None:
    source = Path(__file__).resolve().parents[1] / "examples" / "tiny-python-service"
    project = tmp_path / "tiny-python-service"
    shutil.copytree(source, project)
    monkeypatch.chdir(project)

    if (project / ".gaijinn").exists():
        shutil.rmtree(project / ".gaijinn")

    commands = [
        ["init", "--force", "--no-agent-files", "Build a backend API service with tests"],
        ["scan", "."],
        ["analyze"],
        ["compile-prompt"],
        ["plan", "--workers", "2"],
        ["run-grid", "--workers", "2"],
        ["status", "--strict"],
    ]

    for command in commands:
        result = runner.invoke(app, command, color=False)
        assert result.exit_code == 0, f"gaijinn {' '.join(command)} failed:\n{result.output}"

    assert Path(".gaijinn/graph.json").exists()
    assert Path(".gaijinn/metrics_manifest.json").exists()
    assert Path(".gaijinn/blueprint.json").exists()
    assert Path(".gaijinn/intent.txt").exists()
    assert Path(".gaijinn/workers/manifest.json").exists()

    status = runner.invoke(app, ["status", "--json", "--strict"], color=False)
    assert status.exit_code == 0, status.output
    payload = json.loads(status.output)
    assert payload["state"] == "ready"
    assert payload["worker_grid"]["count"] == 2
    assert payload.get("rejected_node_count", 0) == 0
    assert payload.get("shadow_bridge_count", 0) == 0

    graph = json.loads(Path(".gaijinn/graph.json").read_text(encoding="utf-8"))
    paths = {node["path"] for node in graph["nodes"]}
    assert {
        "tiny_service/api.py",
        "tiny_service/service.py",
        "tiny_service/storage.py",
        "tests/test_api.py",
    }.issubset(paths)


def test_grid_api_endpoints(tmp_path: Path, monkeypatch) -> None:
    """Validate terminal bridge API surface without spawning live agents."""
    from unittest.mock import patch

    import aoc_supervisor.api as api
    from aoc_supervisor.billing import LocalFileLedgerStorageProvider
    from fastapi.testclient import TestClient

    ledger_path = tmp_path / ".aoc" / "billing" / "accounts.json"
    lock_path = tmp_path / ".aoc" / "billing" / "accounts.lock"
    provider = LocalFileLedgerStorageProvider(ledger_path, lock_path)
    provider.write_ledger({"terminal-user": {"balance": "100.00", "status": "active"}})

    workers_dir = tmp_path / ".gaijinn" / "workers"
    workers_dir.mkdir(parents=True)
    (workers_dir / "manifest.json").write_text(
        json.dumps({"worker_details": [{"worker_id": "worker-001", "status": "created"}]}),
        encoding="utf-8",
    )
    (workers_dir / "worker-001").mkdir()
    (workers_dir / "worker-001" / "output.log").write_text("ready\n", encoding="utf-8")
    with (
        patch.object(api, "DEFAULT_LEDGER_STORAGE", provider),
        patch.object(api, "ROOT_DIR", tmp_path),
        patch.object(api, "WORKERS_DIR", workers_dir),
        patch.object(api, "SCRATCH_DIR", tmp_path / ".gaijinn" / "scratch"),
        TestClient(api.app) as client,
    ):
        root_ui = client.get("/")
        assert root_ui.status_code == 200
        assert "Blueprint" in root_ui.text

        terminal = client.get("/terminal")
        assert terminal.status_code == 200
        assert "Blueprint" in terminal.text

        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert "active_sprints" in health.json()

        status = client.get("/api/v1/grid/status")
        assert status.status_code == 200
        assert status.json()["total"] == 1

        logs = client.get("/api/v1/grid/logs")
        assert logs.status_code == 200
        assert logs.json()["logs"]["worker-001"] == "ready\n"

        spawn_no_token = client.post(
            "/api/v1/grid/spawn",
            json={"workers": 2},
            headers={"X-Idempotency-Key": "e2e-spawn-missing-token"},
        )
        assert spawn_no_token.status_code == 401

        quote = client.post(
            "/api/v1/quote",
            json={"workers": 1, "nodes": [{"id": "a"}, {"id": "b"}], "assignment_count": 1},
        )
        assert quote.status_code == 200
        assert "deploy_fee" in quote.json()
        assert "integrity_score" in quote.json()


def test_acceptance_script_fails_on_bad_command() -> None:
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "scripts" / "ci" / "acceptance.sh"
    env = {**subprocess.os.environ, "GAIJINN_TEST_INJECT_FAILURE": "1", "PYTHON": sys.executable}
    result = subprocess.run(
        [Path("/usr/bin/env"), "bash", str(script)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        env=env,
    )
    assert result.returncode != 0, f"should have failed but exited {result.returncode}"
    assert "[FAIL] injected-failure" in result.stdout
