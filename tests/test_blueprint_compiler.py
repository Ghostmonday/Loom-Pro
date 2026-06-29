from __future__ import annotations

from pathlib import Path

from aoc_cli.blueprint_compiler import compile_inferred_json
from aoc_cli.inferring import infer_reflective_layer


def test_compile_inferred_json_writes_workflows(tmp_path: Path) -> None:
    interaction_graph = [
        {
            "agent_intent": "pipeline_create",
            "valid_prior_state": None,
            "resulting_state": "pipeline_created",
            "resource_cluster": "pipeline",
            "source_file": "api/pipelines.py",
        },
        {
            "agent_intent": "pipeline_activate",
            "valid_prior_state": "pipeline_created",
            "resulting_state": "pipeline_active",
            "resource_cluster": "pipeline",
            "source_file": "api/pipelines.py",
        },
    ]
    reflective_meta = infer_reflective_layer(interaction_graph)
    output = tmp_path / "inferred.json"
    payload = compile_inferred_json(
        project_prompt="Build locker rental system",
        interaction_graph=interaction_graph,
        reflective_meta=reflective_meta,
        output_path=output,
    )
    assert output.exists()
    assert payload["workflow_count"] >= 1
    assert payload["layer0"]["functional_domains"]
    assert payload["workflows"][0]["steps"]


def test_compile_inferred_json_end_to_end_with_reflective_meta(tmp_path: Path) -> None:
    interaction_graph = [
        {
            "agent_intent": "pipeline_create",
            "valid_prior_state": None,
            "resulting_state": "pipeline_created",
            "resource_cluster": "pipeline",
            "context_params": ["orgID", "userID"],
            "query_params": ["pipelineID"],
            "source_file": "api/pipelines.py",
        },
        {
            "agent_intent": "pipeline_activate",
            "valid_prior_state": "pipeline_created",
            "resulting_state": "pipeline_active",
            "resource_cluster": "pipeline",
            "context_params": ["orgID", "userID"],
            "query_params": ["pipelineID"],
            "source_file": "api/pipelines.py",
        },
        {
            "agent_intent": "pipeline_trigger",
            "valid_prior_state": "pipeline_active",
            "resulting_state": "pipeline_running",
            "resource_cluster": "pipeline",
            "context_params": ["orgID"],
            "query_params": ["pipelineID"],
            "source_file": "workers/pipeline_runner.py",
            "dataflow": {
                "taint_sources": ["orgID"],
                "mutation_sinks": ["start_worker"],
                "dataflow_punctures": [
                    {
                        "sink": "start_worker",
                        "missing_sources": ["orgID"],
                        "description": "Worker start omits orgID.",
                    }
                ],
            },
        },
        {
            "agent_intent": "pipeline_restart",
            "valid_prior_state": "pipeline_paused",
            "resulting_state": "pipeline_running",
            "resource_cluster": "pipeline",
            "context_params": ["orgID", "userID"],
            "query_params": ["pipelineID"],
            "source_file": "workers/pipeline_runner.py",
        },
    ]
    reflective_meta = infer_reflective_layer(interaction_graph)
    output_path = tmp_path / "inferred.json"

    written_payload = compile_inferred_json(
        project_prompt="Build a security payment orchestration pipeline with offline audit logs",
        interaction_graph=interaction_graph,
        reflective_meta=reflective_meta,
        output_path=output_path,
    )
    memory_payload = compile_inferred_json(
        project_prompt="Build a security payment orchestration pipeline with offline audit logs",
        interaction_graph=interaction_graph,
        reflective_meta=reflective_meta,
    )

    assert output_path.exists()
    assert written_payload == memory_payload
    assert written_payload["schema_version"] == 1
    assert written_payload["layer"] == 2
    assert written_payload["workflows"]
    assert written_payload["workflows"][0]["steps"][:3] == [
        "pipeline_create",
        "pipeline_activate",
        "pipeline_trigger",
    ]
    assert written_payload["disconnected_gaps"]
    assert written_payload["shadowbridges"]
    assert {"auth_security", "billing_payment"} <= set(written_payload["layer0"]["functional_domains"])
