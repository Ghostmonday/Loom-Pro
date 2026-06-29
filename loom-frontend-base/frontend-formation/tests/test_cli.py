import json
from pathlib import Path

from validator.cli.main import main

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specification"


def test_json_output_is_machine_readable(capsys):
    code = main([
        "--project",
        str(ROOT / "examples/passing/frontend-formation.yaml"),
        "--spec-dir",
        str(SPEC),
        "--format",
        "json",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["passed"] is True
    assert payload["error_count"] == 0
    assert payload["checked_screens"] == 1


def test_failing_cli_returns_nonzero(capsys):
    code = main([
        "--project",
        str(ROOT / "examples/failing/frontend-formation.yaml"),
        "--spec-dir",
        str(SPEC),
        "--format",
        "json",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["passed"] is False
    assert payload["error_count"] > 0
