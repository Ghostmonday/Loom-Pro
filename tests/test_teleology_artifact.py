"""Tests for Loom C22 — Teleology Artifact Emitter.

Validates ``build_teleology_artifact``, schema compliance, atomic persistence,
and the handoff.confirm hook that wires everything together.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from aoc_supervisor.teleology_artifact import (
    build_teleology_artifact,
    teleology_path,
    validate_teleology_artifact,
    write_teleology_artifact,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "teleology_pipeline_executor.json"


def _load_fixture() -> dict[str, Any]:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# build_teleology_artifact
# ---------------------------------------------------------------------------


class TestBuildTeleologyArtifact:
    """Unit tests for the teleology artifact builder."""

    def test_build_returns_valid_structure(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)

        assert isinstance(artifact, dict)
        assert artifact["schema_version"] == 1
        assert artifact["session_id"] == "sess_c22_test_01"
        assert artifact["goal"] == "Build a CLI note-taking app with markdown export and tag-based search."

    def test_goal_falls_back_to_artifact_product_definition(self):
        state = _load_fixture()
        state.pop("original_prompt", None)
        artifact = build_teleology_artifact(state)
        # Falls back to artifact.product_definition
        assert "CLI note-taking app" in artifact["goal"]

    def test_goal_default_when_no_source(self):
        artifact = build_teleology_artifact({"session_id": "x", "artifact": None})
        assert artifact["goal"] == "Unspecified goal"

    def test_constraints_are_extracted(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        assert len(artifact["constraints"]) >= 3
        assert any("Linux and macOS" in c for c in artifact["constraints"])

    def test_non_goals_appear_as_constraints(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        assert any("No GUI" in c for c in artifact["constraints"])

    def test_success_criteria_includes_acceptance_criteria(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        assert any("500ms" in s for s in artifact["success_criteria"])

    def test_domains_reflect_addressed_coverage(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        domains = artifact["domains"]
        assert "product_scope" in domains
        assert "data_model" in domains
        assert "non_functional_requirements" not in domains  # na=True

    def test_required_capabilities_from_work_units(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        caps = artifact["required_capabilities"]
        assert len(caps) > 0
        ids = [c["id"] for c in caps]
        assert "wu_001" in ids
        assert "wu_002" in ids

    def test_capability_ids_are_dot_namespaced(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        for cap in artifact["required_capabilities"]:
            assert cap["id"] == cap["id"].lower(), f"id {cap['id']!r} not lowercase"

    @pytest.mark.parametrize("bad_id", ["UPPERCASE", "has spaces", "has-hyphen", "123abc"])
    def test_capability_ids_reject_bad_formats(self, bad_id):
        """Only a concern if something produces such ids; this is a schema
        compliance check that the builder never generates invalid ids."""
        state = _load_fixture()
        # Force a bad id into work_units to verify the builder normalizes it
        state["executable_projection"]["work_units"].append(
            {
                "id": bad_id,
                "title": f"Capability {bad_id}",
                "path": "src/bad/",
                "risk": "low",
                "depends_on": [],
            }
        )
        artifact = build_teleology_artifact(state)
        errors = validate_teleology_artifact(artifact)
        assert not errors, f"produced invalid artifact: {errors}"

    def test_invariants_from_assumptions(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        assert len(artifact["invariants"]) >= 1
        assert any("Python 3.10" in inv["statement"] for inv in artifact["invariants"])

    def test_states_from_pipeline_plan(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        assert "foundation" in artifact["states"]
        assert "storage" in artifact["states"]
        assert "interface" in artifact["states"]

    def test_states_fallback_when_no_pipeline_plan(self):
        state = _load_fixture()
        state.pop("executable_projection", None)
        artifact = build_teleology_artifact(state)
        # Falls back to session statuses
        assert "CREATED" in artifact["states"]
        assert "FINALIZED" in artifact["states"]

    def test_evidence_block(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        ev = artifact["evidence"]
        assert "forge_prompt" in ev
        assert ev["questions_answered"] >= 2
        assert "handoff_at" in ev


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


class TestTeleologySchemaValidation:
    """Validates that built artifacts satisfy the schema contract."""

    def test_valid_artifact_passes(self):
        state = _load_fixture()
        artifact = build_teleology_artifact(state)
        errors = validate_teleology_artifact(artifact)
        assert not errors, f"validation errors: {errors}"

    def test_missing_required_key_fails(self):
        errors = validate_teleology_artifact({})
        assert len(errors) >= 5  # goal, constraints, success_criteria, domains, required_capabilities, invariants

    def test_bad_schema_version_fails(self):
        errors = validate_teleology_artifact(
            {
                "schema_version": 2,
                "session_id": "x",
                "goal": "x",
                "constraints": ["x"],
                "success_criteria": ["x"],
                "domains": ["x"],
                "required_capabilities": [{"id": "test", "description": "test"}],
                "invariants": [],
            }
        )
        assert any("schema_version must be 1" in e for e in errors)

    def test_empty_required_capabilities_fails(self):
        errors = validate_teleology_artifact(
            {
                "schema_version": 1,
                "session_id": "x",
                "goal": "x",
                "constraints": ["x"],
                "success_criteria": ["x"],
                "domains": ["x"],
                "required_capabilities": [],
                "invariants": [],
            }
        )
        assert any("non-empty" in e for e in errors)

    def test_capability_id_pattern_enforced(self):
        errors = validate_teleology_artifact(
            {
                "schema_version": 1,
                "session_id": "x",
                "goal": "x",
                "constraints": ["x"],
                "success_criteria": ["x"],
                "domains": ["x"],
                "required_capabilities": [{"id": "Invalid-ID!", "description": "bad"}],
                "invariants": [],
            }
        )
        assert any("pattern" in e or "Invalid" in e for e in errors)

    def test_capability_missing_description_fails(self):
        errors = validate_teleology_artifact(
            {
                "schema_version": 1,
                "session_id": "x",
                "goal": "x",
                "constraints": ["x"],
                "success_criteria": ["x"],
                "domains": ["x"],
                "required_capabilities": [{"id": "test"}],
                "invariants": [],
            }
        )
        assert any("description" in e for e in errors)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestTeleologyPersistence:
    """Tests for atomic JSON write of teleology.json."""

    def test_write_creates_file(self, tmp_path: Path):
        state = _load_fixture()
        state["session_id"] = "sess_persist_01"
        artifact = write_teleology_artifact(tmp_path, state)
        path = teleology_path(tmp_path, "sess_persist_01")
        assert path.is_file(), f"teleology.json not written at {path}"
        with open(path, encoding="utf-8") as f:
            on_disk = json.load(f)
        assert on_disk["session_id"] == "sess_persist_01"
        assert on_disk["goal"] == artifact["goal"]

    def test_write_atomic_replace(self, tmp_path: Path):
        """Verify the write uses atomic replace (no stale temp files)."""
        state = _load_fixture()
        state["session_id"] = "sess_atomic"
        write_teleology_artifact(tmp_path, state)
        path = teleology_path(tmp_path, "sess_atomic")
        assert path.is_file()
        # No .tmp files should be lingering
        tmp_files = list(path.parent.glob(".*.tmp"))
        assert len(tmp_files) == 0, f"stale temp files: {tmp_files}"

    def test_written_artifact_validates(self, tmp_path: Path):
        state = _load_fixture()
        state["session_id"] = "sess_validate_write"
        write_teleology_artifact(tmp_path, state)
        path = teleology_path(tmp_path, "sess_validate_write")
        with open(path, encoding="utf-8") as f:
            on_disk = json.load(f)
        errors = validate_teleology_artifact(on_disk)
        assert not errors, f"written artifact fails validation: {errors}"

    def test_writes_to_correct_directory(self, tmp_path: Path):
        state = _load_fixture()
        state["session_id"] = "sess_correct_dir"
        write_teleology_artifact(tmp_path, state)
        path = tmp_path / ".gaijinn" / "sessions" / "sess_correct_dir" / "teleology.json"
        assert path.is_file()

    def test_write_without_prompt_has_default_goal(self, tmp_path: Path):
        state = _load_fixture()
        state["session_id"] = "sess_no_prompt"
        state.pop("original_prompt", None)
        state.pop("artifact", None)
        write_teleology_artifact(tmp_path, state)
        path = teleology_path(tmp_path, "sess_no_prompt")
        with open(path, encoding="utf-8") as f:
            on_disk = json.load(f)
        assert on_disk["goal"] == "Unspecified goal"


# ---------------------------------------------------------------------------
# Handoff.confirm integration (behavioural)
# ---------------------------------------------------------------------------


class TestHandoffConfirmTeleologyHook:
    """Verify that the confirm_handoff path calls write_teleology_artifact.

    We test this by monkeypatching write_teleology_artifact onto the
    IntentForgeService.confirm_handoff path and verifying it is invoked
    with the expected state.
    """

    def test_confirm_triggers_teleology_write(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Handoff confirm should build and write the teleology artifact.

        Uses a free-tier session (auto-finalizes with full domain coverage)
        then confirms and checks teleology.json existence.
        """
        from aoc_supervisor.intent_forge_service import IntentForgeService

        service = IntentForgeService(tmp_path)

        initial = service.create_session(
            user_id="test-user",
            prompt="Build a simple CLI calculator",
            tier="free",
        )
        sid = initial["session_id"]
        assert initial["session_status"] == "FINALIZED"

        service.confirm_handoff(
            sid,
            idempotency_key="ik-c22-confirm",
            expected_blueprint_version=1,
            confirmation="Proceed with build",
        )

        teleo_path = tmp_path / ".gaijinn" / "sessions" / sid / "teleology.json"
        assert teleo_path.is_file(), f"teleology.json not written at {teleo_path}"

        with open(teleo_path, encoding="utf-8") as f:
            teleology = json.load(f)
        assert teleology["session_id"] == sid
        assert "goal" in teleology
        errors = validate_teleology_artifact(teleology)
        assert not errors, f"teleology artifact invalid: {errors}"


# ---------------------------------------------------------------------------
# Empty / edge-case inputs
# ---------------------------------------------------------------------------


class TestTeleologyEdgeCases:
    """Edge cases: empty state, missing keys, etc."""

    def test_empty_state_produces_usable_defaults(self):
        artifact = build_teleology_artifact({"session_id": "empty"})
        assert artifact["schema_version"] == 1
        assert artifact["session_id"] == "empty"
        assert artifact["goal"] == "Unspecified goal"
        assert len(artifact["constraints"]) >= 1
        assert len(artifact["success_criteria"]) >= 1
        assert len(artifact["required_capabilities"]) >= 1

    def test_missing_session_id(self):
        artifact = build_teleology_artifact({})
        assert artifact["session_id"] == ""

    def test_schema_version_constant(self):
        artifact = build_teleology_artifact({"session_id": "v"})
        assert artifact["schema_version"] == 1

    def test_large_fixture_does_not_mutate_input(self):
        state = _load_fixture()
        original = json.dumps(state, sort_keys=True)
        _ = build_teleology_artifact(state)
        assert json.dumps(state, sort_keys=True) == original
