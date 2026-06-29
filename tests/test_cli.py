from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from aoc_cli.cli import app
from aoc_cli.commands import grid_spawn as grid_spawn_module
from aoc_cli.errors import GridSpawnError
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_help_shows_available_commands() -> None:
    result = runner.invoke(app, ["--help"], color=False)

    assert result.exit_code == 0
    assert "Loom CLI" in result.output
    for command in (
        "activate",
        "audit",
        "init",
        "scan",
        "compile-prompt",
        "run-grid",
        "collect",
        "validate-worker",
        "merge-grid",
        "plan",
        "status",
        "analyze",
        "monitor",
        "doctor",
        "version",
        "council",
    ):
        assert command in result.output


def test_public_workflow_writes_gaijinn_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["activate", "GAIJINN-TEAM-XXXXXXXX"], color=False)
    assert result.exit_code == 0, result.output
    license_payload = json.loads(Path(".gaijinn/license.json").read_text(encoding="utf-8"))
    assert license_payload["status"] == "active"
    assert license_payload["license_key_hash"] == hashlib.sha256(b"GAIJINN-TEAM-XXXXXXXX").hexdigest()
    assert license_payload["license_key_preview"] == "GAIJ...XXXX"
    assert "license_key" not in license_payload

    result = runner.invoke(
        app,
        ["init", "Build a REST API with Postgres and JWT auth"],
        color=False,
    )
    assert result.exit_code == 0, result.output

    project = json.loads(Path(".gaijinn/project.json").read_text(encoding="utf-8"))
    assert project["capabilities"] == ["api", "auth", "database"]
    assert Path(".gaijinn/GENERATE_BLUEPRINT.md").read_text(encoding="utf-8").startswith("# Generate Loom Blueprint")
    assert "Next suggested commands:" in result.output
    assert "1. loom compile-prompt" in result.output
    assert "2. loom scan ." in result.output
    assert "3. loom analyze" in result.output
    assert "4. loom plan --workers 2" in result.output
    assert "5. loom run-grid --workers 2" in result.output

    result = runner.invoke(app, ["compile-prompt"], color=False)
    assert result.exit_code == 0, result.output
    intent = Path(".gaijinn/intent.txt").read_text(encoding="utf-8")
    giv = json.loads(Path(".gaijinn/giv.json").read_text(encoding="utf-8"))
    assert "Build a REST API with Postgres and JWT auth" in intent
    assert "- backend" in intent
    assert giv["worker_id"] == "project"
    assert giv["capabilities"] == ["auth_security", "backend"]
    assert giv["allowed_paths"] == [
        "aoc-cli/aoc_cli/",
        "aoc_supervisor/aoc_supervisor/",
        "docs/",
        "tests/",
    ]
    assert "work domains: auth_security, backend" in result.output
    assert "risk flags: security-sensitive changes" in result.output

    Path("aoc-cli/aoc_cli").mkdir(parents=True)
    Path("aoc-cli/aoc_cli/api.py").write_text("def app():\n    return 'ok'\n", encoding="utf-8")
    result = runner.invoke(app, ["scan", "."], color=False)
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["analyze"], color=False)
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["plan", "--workers", "1"], color=False)
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["run-grid", "--workers", "1"], color=False)
    assert result.exit_code == 0, result.output
    assert Path(".gaijinn/workers/worker-001/intent.txt").read_text(encoding="utf-8")
    manifest = json.loads(Path(".gaijinn/workers/manifest.json").read_text(encoding="utf-8"))
    assert manifest["workers"] == ["worker-001"]

    result = runner.invoke(app, ["status"], color=False)
    assert result.exit_code == 0, result.output
    assert "workers: 1" in result.output


def test_scan_respects_gitignore_and_writes_graph(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text("ignored.txt\nbuild/\n", encoding="utf-8")
    (root / "kept.py").write_text(
        "import package.service\nfrom package import model\nprint('ok')\n",
        encoding="utf-8",
    )
    (root / "package").mkdir()
    (root / "package" / "__init__.py").write_text("", encoding="utf-8")
    (root / "package" / "service.py").write_text(
        "from . import model\n\ndef save():\n    model.write()\n",
        encoding="utf-8",
    )
    (root / "package" / "model.py").write_text(
        "from pathlib import Path\n\ndef write():\n    Path('x').write_text('x')\n",
        encoding="utf-8",
    )
    (root / "ignored.txt").write_text("secret\n", encoding="utf-8")
    (root / "build").mkdir()
    (root / "build" / "artifact.txt").write_text("generated\n", encoding="utf-8")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "vendor.py").write_text("print('ignored')\n", encoding="utf-8")
    (root / ".venv").mkdir()
    (root / ".venv" / "library.py").write_text("print('ignored')\n", encoding="utf-8")

    result = runner.invoke(app, ["scan", str(root)], color=False)
    assert result.exit_code == 0, result.output
    first_graph_text = Path(".gaijinn/graph.json").read_text(encoding="utf-8")

    graph = json.loads(first_graph_text)
    paths = {node["path"] for node in graph["nodes"]}
    assert "kept.py" in paths
    assert "package/service.py" in paths
    assert "package/model.py" in paths
    assert "ignored.txt" not in paths
    assert "build/artifact.txt" not in paths
    assert "node_modules/vendor.py" not in paths
    assert ".venv/library.py" not in paths

    node_by_path = {node["path"]: node for node in graph["nodes"]}
    assert node_by_path["kept.py"]["language"] == "python"
    assert node_by_path["kept.py"]["line_count"] == 3
    assert node_by_path["package/model.py"]["capability_level"] >= 2.0
    assert node_by_path["package/model.py"]["side_effect_score"] > 0.0
    assert graph["edges"] == [
        ["kept.py", "package/__init__.py"],
        ["kept.py", "package/model.py"],
        ["kept.py", "package/service.py"],
        ["package/service.py", "package/__init__.py"],
        ["package/service.py", "package/model.py"],
    ]

    result = runner.invoke(app, ["scan", str(root)], color=False)
    assert result.exit_code == 0, result.output
    assert Path(".gaijinn/graph.json").read_text(encoding="utf-8") == first_graph_text

    result = runner.invoke(app, ["analyze"], color=False)
    assert result.exit_code == 0, result.output
    assert Path(".gaijinn/metrics_manifest.json").exists()


def test_plan_writes_blueprint_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("pkg").mkdir()
    Path("pkg/router.py").write_text("from . import service\n", encoding="utf-8")
    Path("pkg/service.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "Build a backend API with tests"], color=False)
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["compile-prompt"], color=False)
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["scan", "."], color=False)
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["analyze"], color=False)
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["plan", "--workers", "2", "--max-risk", "high", "--json"], color=False)

    assert result.exit_code == 0, result.output
    blueprint = json.loads(result.output)
    assert blueprint["schema_version"] == 1
    assert blueprint["work_units"]
    assert Path(".gaijinn/blueprint.json").exists()
    assert Path(".gaijinn/blueprint.md").read_text(encoding="utf-8").startswith("# Gaijinn Blueprint")
    all_allowed_paths = [path for unit in blueprint["work_units"] for path in unit["allowed_paths"]]
    assert len(all_allowed_paths) == len(set(all_allowed_paths))


def test_run_grid_rejects_empty_blueprint(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    gaijinn = tmp_path / ".gaijinn"
    gaijinn.mkdir()
    (gaijinn / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "activation_status": "active",
                "project_root": str(tmp_path),
                "initialized_at": "2026-06-18T00:00:00Z",
                "prompt_hash": "testhash",
                "intent_path": ".gaijinn/intent.txt",
                "graph_path": ".gaijinn/graph.json",
                "metrics_path": ".gaijinn/metrics_manifest.json",
                "blueprint_path": ".gaijinn/blueprint.md",
                "workers_path": ".gaijinn/workers",
            }
        ),
        encoding="utf-8",
    )
    (gaijinn / "intent.txt").write_text("vault sprint\n", encoding="utf-8")
    (gaijinn / "giv.json").write_text(
        json.dumps({"worker_id": "project", "allowed_paths": ["40_Concepts/"]}),
        encoding="utf-8",
    )
    (gaijinn / "blueprint.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_goal": "vault sprint",
                "assumptions": [],
                "work_units": [],
                "dependencies": {},
                "risks": [],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["run-grid", "--workers", "2", "--force"], color=False)
    assert result.exit_code != 0
    assert "zero work units" in result.output.lower()


def test_run_grid_requires_project_state(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run-grid", "--workers", "1"], color=False)

    assert result.exit_code != 0
    assert "run `gaijinn init" in result.output


def test_grid_spawn_hard_fails_when_manifest_worker_dir_missing(tmp_path) -> None:
    workers_path = tmp_path / "workers"
    workers_path.mkdir()
    (workers_path / "worker-001").mkdir()
    (workers_path / "manifest.json").write_text(
        json.dumps(
            {
                "workers": ["worker-001", "worker-002"],
                "worker_details": [{"worker_id": "worker-001"}, {"worker_id": "worker-002"}],
            }
        ),
        encoding="utf-8",
    )
    state = SimpleNamespace(metrics_path=tmp_path / "metrics.json", workers_path=workers_path)

    with (
        patch.object(grid_spawn_module, "validate_grid_readiness", return_value={"ready": True}),
        pytest.raises(GridSpawnError, match="missing worker"),
    ):
        grid_spawn_module._ensure_grid_spawn_prerequisites(state, 2)


def test_grid_spawn_timeout_kills_worker_and_updates_manifest(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    state = SimpleNamespace(
        metrics_path=Path(".gaijinn/metrics_manifest.json"),
        workers_path=Path(".gaijinn/workers"),
    )
    worker_dir = state.workers_path / "worker-001"
    worker_dir.mkdir(parents=True)
    (worker_dir / "WORK_UNIT.md").write_text("Do work", encoding="utf-8")
    (state.workers_path / "manifest.json").write_text(
        json.dumps({"worker_details": [{"worker_id": "worker-001", "status": "created"}]}),
        encoding="utf-8",
    )

    proc = Mock()
    proc.returncode = -9
    proc.wait.side_effect = [grid_spawn_module.subprocess.TimeoutExpired(["grok"], 1), None]

    with (
        patch.object(grid_spawn_module, "_require_project_state", return_value=state),
        patch.object(grid_spawn_module, "_ensure_grid_spawn_prerequisites", return_value={}),
        patch.object(grid_spawn_module, "shutil"),
        patch.object(grid_spawn_module, "_spawn_worker", return_value=proc),
        pytest.raises(Exception, match="worker\\(s\\) failed"),
    ):
        grid_spawn_module.grid_spawn_cmd(workers=1, model="grok-composer-2.5-fast", timeout=1)

    proc.kill.assert_called_once()
    manifest = json.loads((state.workers_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["worker_details"][0]["status"] == "timed_out"
    assert manifest["sprint"]["timeout_seconds"] == 1


def test_grid_spawn_warns_on_manifest_update_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    state = SimpleNamespace(
        metrics_path=Path(".gaijinn/metrics_manifest.json"),
        workers_path=Path(".gaijinn/workers"),
    )
    worker_dir = state.workers_path / "worker-001"
    worker_dir.mkdir(parents=True)
    (worker_dir / "WORK_UNIT.md").write_text("Do work", encoding="utf-8")
    (state.workers_path / "manifest.json").write_text(
        json.dumps({"worker_details": [{"worker_id": "worker-001", "status": "created"}]}),
        encoding="utf-8",
    )

    proc = Mock(returncode=0)
    proc.wait.return_value = None
    echoes: list[str] = []

    with (
        patch.object(grid_spawn_module, "_require_project_state", return_value=state),
        patch.object(grid_spawn_module, "_ensure_grid_spawn_prerequisites", return_value={}),
        patch.object(grid_spawn_module, "_spawn_worker", return_value=proc),
        patch.object(grid_spawn_module, "_write_manifest_atomic", side_effect=OSError("disk full")),
        patch.object(grid_spawn_module.typer, "echo", side_effect=lambda message="": echoes.append(str(message))),
    ):
        grid_spawn_module.grid_spawn_cmd(workers=1, model="grok-composer-2.5-fast")

    assert any("Warning: failed to update worker manifest" in message for message in echoes)


def test_init_twice_without_force_fails_without_overwriting(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "Build an API"], color=False)
    assert result.exit_code == 0, result.output
    first_project = Path(".gaijinn/project.json").read_text(encoding="utf-8")
    first_seed = Path(".gaijinn/GENERATE_BLUEPRINT.md").read_text(encoding="utf-8")

    result = runner.invoke(app, ["init", "Build a CLI"], color=False)

    assert result.exit_code != 0
    assert ".gaijinn/project.json already exists" in result.output
    assert "use --force" in result.output
    assert "overwrite project state" in result.output
    assert Path(".gaijinn/project.json").read_text(encoding="utf-8") == first_project
    assert Path(".gaijinn/GENERATE_BLUEPRINT.md").read_text(encoding="utf-8") == first_seed


def test_init_force_overwrites_state_and_agent_blocks_idempotently(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("CLAUDE.md").write_text("# Existing Claude Notes\n", encoding="utf-8")
    Path(".cursorrules").write_text("Existing cursor rules\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "Build an API"], color=False)
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["init", "--force", "Build a CLI"], color=False)
    assert result.exit_code == 0, result.output

    project = json.loads(Path(".gaijinn/project.json").read_text(encoding="utf-8"))
    assert project["project_prompt"] == "Build a CLI"
    for agent_path in (Path("CLAUDE.md"), Path(".cursorrules")):
        content = agent_path.read_text(encoding="utf-8")
        assert content.count("<!-- BEGIN GAIJINN INIT -->") == 1
        assert content.count("<!-- END GAIJINN INIT -->") == 1
        assert "Build an API" not in content
        assert "Build a CLI" in content


def test_init_blueprint_template_and_no_agent_files(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["init", "--blueprint-template", "--no-agent-files", "Ship a worker scheduler"],
        color=False,
    )

    assert result.exit_code == 0, result.output
    blueprint = Path(".gaijinn/blueprint.md").read_text(encoding="utf-8")
    assert blueprint.startswith("# Gaijinn Blueprint")
    assert "Ship a worker scheduler" in blueprint
    assert "Before running the commands, edit .gaijinn/blueprint.md." in result.output
    assert not Path("CLAUDE.md").exists()
    assert not Path(".cursorrules").exists()


def test_corrupt_project_state_reports_actionable_error(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path(".gaijinn").mkdir()
    Path(".gaijinn/project.json").write_text("{not-json", encoding="utf-8")

    result = runner.invoke(app, ["compile-prompt"], color=False)

    assert result.exit_code != 0
    assert "invalid JSON in .gaijinn/project.json" in result.output
    assert "line 1" in result.output


def test_incomplete_project_state_reports_missing_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path(".gaijinn").mkdir()
    Path(".gaijinn/project.json").write_text('{"schema_version": 1}\n', encoding="utf-8")

    result = runner.invoke(app, ["compile-prompt"], color=False)

    assert result.exit_code != 0
    assert "missing required field" in result.output
    assert "project_root" in result.output


def test_legacy_project_state_still_compiles_prompt(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path(".gaijinn").mkdir()
    Path(".gaijinn/project.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project_prompt": "Build an API",
                "capabilities": ["api"],
                "artifacts": {
                    "blueprint_seed": ".gaijinn/GENERATE_BLUEPRINT.md",
                    "graph": ".gaijinn/graph.json",
                    "intent": ".gaijinn/intent.txt",
                },
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["compile-prompt"], color=False)

    assert result.exit_code == 0, result.output
    assert "Build an API" in Path(".gaijinn/intent.txt").read_text(encoding="utf-8")
    assert Path(".gaijinn/giv.json").exists()


def test_compile_prompt_json_output_is_stable(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["init", "Build React UI, docs, and pytest coverage"],
        color=False,
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["compile-prompt", "--json"], color=False)

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "schema_version": 1,
        "giv": ".gaijinn/giv.json",
        "intent": ".gaijinn/intent.txt",
        "work_domains": ["docs", "frontend", "tests"],
        "allowed_paths": ["README.md", "aoc-cli/aoc_cli/", "docs/", "tests/"],
        "prohibitions": [
            "no destructive cleanup outside workspace",
            "no edits outside assigned paths",
            "no git push",
            "no network calls",
            "no secret exfiltration",
        ],
        "risk_flags": [],
    }


def test_analyze_writes_metrics_manifest_for_graph_json(tmp_path) -> None:
    graph_path = tmp_path / "graph.json"
    output_path = tmp_path / "metrics_manifest.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "ingest", "capability_level": 2, "side_effect_score": 0.5},
                    {"id": "plan", "capability_level": 3, "side_effect_score": 1},
                    {"id": "apply", "capability_level": 4, "side_effect_score": 1},
                ],
                "edges": [["ingest", "plan"], ["plan", "apply"]],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["analyze", "--graph", str(graph_path), "--output", str(output_path)],
        color=False,
    )

    assert result.exit_code == 0, result.output
    assert output_path.exists()

    metrics = json.loads(output_path.read_text(encoding="utf-8"))
    assert metrics["gravity_meta"]["automatic_rejection"] is False
    assert set(metrics["gravity_meta"]["nodes"]) == {"ingest", "plan", "apply"}
    assert set(metrics["curvature_meta"]["edges"]) == {"ingest->plan", "plan->apply"}
    assert metrics["curvature_meta"]["shadow_bridge_count"] == 0
    assert metrics["reflective_meta"]["intent_node_count"] == 0


def test_analyze_json_output_is_stable(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GAIJINN_OPERATOR", "1")
    graph_path = tmp_path / "graph.json"
    output_path = tmp_path / "metrics_manifest.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "router", "capability_level": 1, "side_effect_score": 0},
                    {"id": "deploy", "capability_level": 5, "side_effect_score": 3},
                    {"id": "isolated", "capability_level": 5, "side_effect_score": 0},
                ],
                "edges": [["router", "deploy"]],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["analyze", "--graph", str(graph_path), "--output", str(output_path), "--json"],
        color=False,
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "schema_version": 1,
        "graph": graph_path.as_posix(),
        "metrics": output_path.as_posix(),
        "node_count": 3,
        "edge_count": 1,
        "automatic_rejection": True,
        "rejection_count": 1,
        "rejected_nodes": ["isolated"],
        "shadow_bridge_count": 1,
        "shadow_bridges": ["router->deploy"],
        "layer2_intent_nodes": 0,
        "lifecycle_chain_count": 0,
        "disconnected_gap_count": 0,
        "capability_ceiling_count": 0,
        "type_flow_puncture_count": 0,
        "symmetry_shadowbridge_count": 0,
        "inferred_path": None,
    }


def test_analyze_failure_flags_exit_nonzero(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GAIJINN_OPERATOR", "1")
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "router", "capability_level": 1, "side_effect_score": 0},
                    {"id": "deploy", "capability_level": 5, "side_effect_score": 3},
                    {"id": "isolated", "capability_level": 5, "side_effect_score": 0},
                ],
                "edges": [["router", "deploy"]],
            }
        ),
        encoding="utf-8",
    )

    rejection = runner.invoke(
        app,
        [
            "analyze",
            "--graph",
            str(graph_path),
            "--output",
            str(tmp_path / "rejection_metrics.json"),
            "--json",
            "--fail-on-rejection",
        ],
        color=False,
    )
    shadow_bridge = runner.invoke(
        app,
        [
            "analyze",
            "--graph",
            str(graph_path),
            "--output",
            str(tmp_path / "shadow_bridge_metrics.json"),
            "--json",
            "--fail-on-shadow-bridge",
        ],
        color=False,
    )

    assert rejection.exit_code == 2, rejection.output
    assert shadow_bridge.exit_code == 3, shadow_bridge.output
    assert json.loads(rejection.output)["rejected_nodes"] == ["isolated"]
    assert json.loads(shadow_bridge.output)["shadow_bridges"] == ["router->deploy"]


def test_analyze_reports_friendly_graph_validation_errors(tmp_path) -> None:
    missing = runner.invoke(app, ["analyze", "--graph", str(tmp_path / "missing.json")], color=False)
    assert missing.exit_code != 0
    assert "missing graph JSON" in missing.output
    assert "scan" in missing.output

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{not-json", encoding="utf-8")
    invalid = runner.invoke(app, ["analyze", "--graph", str(invalid_path)], color=False)
    assert invalid.exit_code != 0
    assert "invalid JSON" in invalid.output
    assert "line 1" in invalid.output

    empty_path = tmp_path / "empty.json"
    empty_path.write_text('{"nodes": []}', encoding="utf-8")
    empty = runner.invoke(app, ["analyze", "--graph", str(empty_path)], color=False)
    assert empty.exit_code != 0
    assert "contains no nodes" in empty.output

    bad_score_path = tmp_path / "bad-score.json"
    bad_score_path.write_text(
        json.dumps({"nodes": [{"id": "deploy", "capability_level": "high"}], "edges": []}),
        encoding="utf-8",
    )
    bad_score = runner.invoke(app, ["analyze", "--graph", str(bad_score_path)], color=False)
    assert bad_score.exit_code != 0
    assert "cannot analyze" in bad_score.output
    assert "got 'high'" in bad_score.output


def test_analyze_updates_project_metrics_path(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "Build an API"], color=False)
    assert result.exit_code == 0, result.output

    Path(".gaijinn/graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "ingest", "capability_level": 2, "side_effect_score": 0.5},
                    {"id": "plan", "capability_level": 3, "side_effect_score": 1},
                    {"id": "apply", "capability_level": 4, "side_effect_score": 1},
                ],
                "edges": [["ingest", "plan"], ["plan", "apply"]],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["analyze", "--output", ".gaijinn/custom_metrics.json", "--json"],
        color=False,
    )

    assert result.exit_code == 0, result.output
    project = json.loads(Path(".gaijinn/project.json").read_text(encoding="utf-8"))
    assert project["metrics_path"] == ".gaijinn/custom_metrics.json"


def test_version_command_prints_package_version() -> None:
    result = runner.invoke(app, ["version"], color=False)

    assert result.exit_code == 0, result.output
    assert result.output.strip() == "0.1.0"


def test_doctor_reports_meaningful_json_diagnostics(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor", "--json"], color=False)

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["status"] in {"pass", "warn"}
    checks = {item["name"]: item for item in payload["diagnostics"]}
    assert checks["python"]["status"] == "pass"
    assert checks["import:aoc_cli"]["status"] == "pass"
    assert checks["dependency:typer"]["status"] == "pass"
    assert checks[".gaijinn writable"]["status"] == "pass"
    assert checks["artifact:project"]["status"] == "warn"


def test_doctor_strict_exits_nonzero_on_invalid_existing_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path(".gaijinn").mkdir()
    Path(".gaijinn/project.json").write_text("{not-json", encoding="utf-8")

    result = runner.invoke(app, ["doctor", "--strict"], color=False)

    assert result.exit_code == 2, result.output
    assert "FAIL" in result.output
    assert "artifact:project" in result.output
    assert "invalid JSON" in result.output


def _init_minimal_project(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["init", "--force", "--no-agent-files", "Merge pipeline test project"],
        color=False,
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["compile-prompt"], color=False)
    assert result.exit_code == 0, result.output


def test_collect_no_workers(tmp_path, monkeypatch) -> None:
    _init_minimal_project(monkeypatch, tmp_path)
    result = runner.invoke(app, ["collect"], color=False)
    assert result.exit_code != 0
    assert "gaijinn run-grid" in result.output


def test_validate_worker_missing(tmp_path, monkeypatch) -> None:
    _init_minimal_project(monkeypatch, tmp_path)
    merge_dir = tmp_path / ".gaijinn" / "merge"
    merge_dir.mkdir(parents=True)
    collected = {
        "schema_version": 1,
        "collected_at": "2026-06-15T00:00:00Z",
        "base_ref": "HEAD",
        "workers": {"worker-001": {"status": "completed"}},
    }
    (merge_dir / "collected.json").write_text(json.dumps(collected), encoding="utf-8")
    workers_dir = tmp_path / ".gaijinn" / "workers"
    workers_dir.mkdir(parents=True)
    (workers_dir / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "workers": ["worker-001"], "worker_details": []}),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate-worker", "worker-001"], color=False)
    assert result.exit_code != 0
    assert "worker directory missing" in result.output.lower()


def test_merge_grid_no_validated(tmp_path, monkeypatch) -> None:
    _init_minimal_project(monkeypatch, tmp_path)
    result = runner.invoke(app, ["merge-grid"], color=False)
    assert result.exit_code != 0
    assert "gaijinn validate-worker" in result.output


def test_status_with_merge_pipeline(tmp_path, monkeypatch) -> None:
    _init_minimal_project(monkeypatch, tmp_path)
    merge_dir = tmp_path / ".gaijinn" / "merge"
    merge_dir.mkdir(parents=True)
    (merge_dir / "collected.json").write_text(
        json.dumps({"workers": {"worker-001": {}, "worker-002": {}}}),
        encoding="utf-8",
    )
    (merge_dir / "validated.json").write_text(
        json.dumps({"worker-001": {"passed": True}, "worker-002": {"passed": False}}),
        encoding="utf-8",
    )
    (merge_dir / "report.json").write_text(
        json.dumps({"summary": {"merged": 1, "blocked": 1, "conflicted": 0, "total": 2}}),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["status", "--json"], color=False)
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    merge = payload["merge_pipeline"]
    assert merge["phase"] == "completed"
    assert merge["collected"] == 2
    assert merge["validated_passed"] == 1
    assert merge["merged"] == 1
    assert merge["blocked"] == 1

    strict = runner.invoke(app, ["status", "--json", "--strict"], color=False)
    assert strict.exit_code == 2


COMMANDS_WITH_HELP = [
    ("activate", "Store local activation metadata"),
    ("init", "Initialize .gaijinn project state"),
    ("scan", "Scan a directory"),
    ("analyze", "integrity preflight"),
    ("compile-prompt", "Compile project.json"),
    ("run-grid", "Create isolated worker directories"),
    ("collect", "Collect worker execution state"),
    ("validate-worker", "Run merge-pipeline validation"),
    ("merge-grid", "Merge validated worker branches"),
    ("status", "Summarize current"),
    ("monitor", "Watch metrics manifest"),
    ("doctor", "Check the local Loom installation"),
    ("version", "Print the installed Loom version"),
]


@pytest.mark.parametrize("command,help_text", COMMANDS_WITH_HELP)
def test_command_help_shows_purpose(command, help_text):
    result = runner.invoke(app, [command, "--help"], color=False)
    assert result.exit_code == 0, f"{command} --help failed: {result.output}"
    assert help_text.lower() in result.output.lower()
    assert "Traceback" not in result.output
