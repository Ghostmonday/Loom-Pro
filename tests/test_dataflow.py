from __future__ import annotations

import ast
import textwrap

from aoc_cli.dataflow import analyze_handler_dataflow


def test_dataflow_flags_missing_org_taint_at_delete_sink() -> None:
    source = textwrap.dedent(
        """
        def delete_secret(resource_id: str):
            delete_record(resource_id)
        """
    ).strip()
    func = ast.parse(source).body[0]
    assert isinstance(func, ast.FunctionDef)
    result = analyze_handler_dataflow(func)
    assert result["taint_sources"] == []
    assert result["has_dataflow_puncture"] is False


def test_dataflow_puncture_when_sink_lacks_source_reference() -> None:
    source = textwrap.dedent(
        """
        def delete_secret(org_id: str, resource_id: str):
            delete_record(resource_id)
        """
    ).strip()
    func = ast.parse(source).body[0]
    assert isinstance(func, ast.FunctionDef)
    result = analyze_handler_dataflow(func)
    assert "org_id" in result["taint_sources"]
    assert result["has_dataflow_puncture"] is True
    assert result["dataflow_punctures"][0]["missing_sources"] == ["org_id"]
