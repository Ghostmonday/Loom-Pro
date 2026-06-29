from __future__ import annotations

import json

import pytest
from aoc_cli.giv import DEFAULT_PROHIBITIONS, GIV, GIVValidationError


def test_giv_render_for_worker_includes_constraints() -> None:
    intent = GIV(
        worker_id="worker-001",
        allowed_paths=("aoc-cli/aoc_cli/giv.py", "tests/test_giv.py"),
        denied_paths=(".env",),
        allowed_commands=("pytest tests/test_giv.py",),
        capabilities=("implement giv schema",),
        invariants=("deterministic output",),
    )

    rendered = intent.render_intent()

    assert rendered.startswith("# Agent Intent Vector\n\nWorker: worker-001")
    assert "- aoc-cli/aoc_cli/giv.py" in rendered
    assert "- pytest tests/test_giv.py" in rendered
    assert "- git push" in rendered
    assert "- no secret exfiltration" in rendered
    assert "- deterministic output" in rendered


def test_giv_denies_git_push_by_default() -> None:
    intent = GIV(worker_id="worker-001", allowed_paths=("aoc-cli/aoc_cli/giv.py",))

    assert "git push" in intent.denied_commands
    assert "no git push" in intent.prohibitions


def test_giv_merges_default_prohibitions() -> None:
    intent = GIV(
        worker_id="worker-001",
        allowed_paths=("aoc-cli/aoc_cli/giv.py",),
        prohibitions=("no network writes",),
    )

    for prohibition in DEFAULT_PROHIBITIONS:
        assert prohibition in intent.prohibitions
    assert "no network writes" in intent.prohibitions


def test_giv_rejects_missing_worker_id() -> None:
    with pytest.raises(GIVValidationError, match="worker_id is required"):
        GIV(worker_id=" ", allowed_paths=("aoc-cli/aoc_cli/giv.py",))


def test_giv_rejects_empty_allowed_paths() -> None:
    with pytest.raises(GIVValidationError, match="allowed_paths cannot be empty"):
        GIV(worker_id="worker-001", allowed_paths=())


def test_giv_json_serialization_is_deterministic() -> None:
    intent = GIV(
        worker_id="worker-001",
        allowed_paths=("tests/test_giv.py", "aoc-cli/aoc_cli/giv.py"),
        denied_commands=("rm -rf /",),
    )

    payload = json.loads(intent.to_json())

    assert payload["worker_id"] == "worker-001"
    assert payload["allowed_paths"] == ["aoc-cli/aoc_cli/giv.py", "tests/test_giv.py"]
    assert payload["denied_commands"] == ["git push", "rm -rf /"]


def test_giv_from_dict_applies_defaults() -> None:
    intent = GIV.from_dict(
        {
            "worker_id": "worker-001",
            "allowed_paths": ["aoc-cli/aoc_cli/giv.py"],
        }
    )

    assert intent.denied_commands == ("git push",)
    assert "no edits outside assigned paths" in intent.prohibitions
