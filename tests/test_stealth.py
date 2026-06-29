from __future__ import annotations

import json

import pytest
from aoc_cli.cli import app
from aoc_cli.helpers.stealth import (
    customer_preflight_from_metrics,
    dark_bridge_internal_log,
    dark_bridge_user_log,
    sanitize_analyze_api_response,
    sanitize_blocked_reason,
    stealth_mode,
)
from typer.testing import CliRunner

runner = CliRunner()


SAMPLE_METRICS = {
    "gravity_meta": {
        "automatic_rejection": True,
        "rejected_nodes": ["pkg/risky.py"],
        "nodes": {"a.py": {}, "b.py": {}},
    },
    "curvature_meta": {
        "shadow_bridge_count": 2,
        "edges": {},
    },
}


def test_stealth_mode_default_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAIJINN_OPERATOR", raising=False)
    monkeypatch.delenv("GAIJINN_STEALTH", raising=False)
    assert stealth_mode() is True


def test_operator_mode_disables_stealth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAIJINN_OPERATOR", "1")
    assert stealth_mode() is False


def test_sanitize_blocked_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAIJINN_OPERATOR", raising=False)
    monkeypatch.setenv("GAIJINN_STEALTH", "1")
    assert "coupling review" in sanitize_blocked_reason("3 shadow bridge(s)")
    assert "coupling review" in sanitize_blocked_reason("3 SHADOW BRIDGE(S)")


def test_dark_bridge_logging_messages() -> None:
    assert "DARK BRIDGE SEVERITY CRITICAL" in dark_bridge_internal_log("a.py", "b.py")
    assert "coupling reviews" in dark_bridge_user_log()


def test_customer_preflight_hides_internal_terms() -> None:
    payload = customer_preflight_from_metrics(SAMPLE_METRICS)
    blob = json.dumps(payload)
    assert "shadow" not in blob
    assert "curvature" not in blob
    assert payload["coupling_review_count"] == 2
    assert payload["preflight_status"] == "review"


def test_analyze_api_response_is_customer_safe() -> None:
    payload = sanitize_analyze_api_response(
        status="DEGRADED",
        automatic_rejection=False,
        shadow_bridge_count=3,
        rejected_nodes=["x.py"],
        integrity_score=42,
    )
    blob = json.dumps(payload)
    assert "shadow_bridge" not in blob
    assert payload["coupling_review_count"] == 3
    assert payload["integrity_score"] == 42


def test_analyze_json_stealth_by_default(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAIJINN_OPERATOR", raising=False)
    graph_path = tmp_path / "graph.json"
    output_path = tmp_path / "metrics_manifest.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "router", "capability_level": 1, "side_effect_score": 0},
                    {"id": "deploy", "capability_level": 5, "side_effect_score": 3},
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
    payload = json.loads(result.output)
    assert "integrity_score" in payload
    assert "coupling_review_count" in payload
    assert "shadow_bridge_count" not in payload


def test_status_json_stealth_by_default(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAIJINN_OPERATOR", raising=False)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--no-agent-files", "demo"], color=False)
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["status", "--json"], color=False)
    assert result.exit_code == 0, result.output
    blob = result.output
    assert "shadow_bridge" not in blob
    assert "integrity_score" in blob
