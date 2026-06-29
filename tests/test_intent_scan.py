from __future__ import annotations

import textwrap
from pathlib import Path

from aoc_cli.intent_scan import extract_interaction_graph


def test_extract_fastapi_route_intent_node(tmp_path: Path) -> None:
    source = tmp_path / "api.py"
    source.write_text(
        textwrap.dedent(
            """
            from fastapi import FastAPI, HTTPException

            app = FastAPI()

            @app.post("/pipelines/{org_id}/runs")
            def create_run(org_id: str, resource_id: str):
                if org_id != "active":
                    raise HTTPException(status_code=400, detail="inactive")
                create_run_record(resource_id)
                return {"status": "ok"}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    nodes = extract_interaction_graph(tmp_path, {Path("api.py")})
    assert len(nodes) == 1
    node = nodes[0]
    assert node["http_method"] == "POST"
    assert node["http_path"] == "/pipelines/{org_id}/runs"
    assert "org_id" in node["context_params"]
    assert node["guard_conditions"]
    assert "create_run_record" in node["side_effects"]
