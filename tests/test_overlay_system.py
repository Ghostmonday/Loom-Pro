from __future__ import annotations

import json
import shutil
from pathlib import Path

from aoc_supervisor.overlay_system import validate_overlay_authority
from aoc_supervisor.workflow_evaluator import evaluate_workflow

ROOT = Path(__file__).resolve().parents[1]


def _copy_authority(tmp_path: Path) -> Path:
    target = tmp_path / "repo"
    shutil.copytree(ROOT / ".loom", target / ".loom")
    return target


def _write_overlay(root: Path, registration_id: str = "overlay.test", **updates) -> dict:
    payload = {
        "overlay_id": registration_id,
        "version": "1.0.0",
        "provenance": {
            "source": "tests",
            "created_by": "pytest",
            "created_at": "2026-06-29T00:00:00Z",
            "reason": "coverage",
        },
        "authority": {
            "authority_id": "loom.overlay.authority",
            "signature_required": True,
            "signature": "test-signature",
        },
        "applicability": {"runtime": "workflow_evaluator", "scenario_id": "*"},
        "lifecycle": {"status": "validated", "reason": "validated for test"},
        "promotion": {"promoted_by": "pytest", "reason": "promotion tested"},
        "rejection": {"rejected_by": "", "reason": "not rejected"},
        "supersession": {"superseded_by": "", "reason": "not superseded"},
    }
    payload.update(updates)
    path = root / ".loom" / "overlays" / f"{registration_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    registry_path = root / ".loom" / "overlays" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["overlays"][registration_id] = {
        "path": f".loom/overlays/{registration_id}.json",
        "version": payload.get("version", "1.0.0"),
        "source": payload.get("provenance", {}).get("source", "tests")
        if isinstance(payload.get("provenance"), dict)
        else "tests",
        "applicability": payload.get("applicability", {}),
        "lifecycle_status": payload.get("lifecycle", {}).get("status", "validated")
        if isinstance(payload.get("lifecycle"), dict)
        else "validated",
    }
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return payload


def _codes(report):
    return {issue.code for issue in report.issues}


def test_valid_registration(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    _write_overlay(root)
    monkeypatch.chdir(root)
    assert validate_overlay_authority().passed


def test_malformed_overlays_fail_closed(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    _write_overlay(root, provenance={})
    monkeypatch.chdir(root)
    report = validate_overlay_authority()
    assert not report.passed
    assert "provenance" in _codes(report)


def test_unknown_overlays_fail_closed(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    (root / ".loom" / "overlays" / "unknown.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(root)
    report = validate_overlay_authority()
    assert not report.passed
    assert "unknown" in _codes(report)


def test_provenance_failures(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    _write_overlay(root, authority={"authority_id": "rogue", "signature_required": True, "signature": "x"})
    monkeypatch.chdir(root)
    report = validate_overlay_authority()
    assert not report.passed
    assert {"unauthorized"}.issubset(_codes(report))


def test_conflicting_overlays(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    _write_overlay(root, "overlay.one", overlay_id="overlay.conflict")
    _write_overlay(root, "overlay.two", overlay_id="overlay.conflict")
    monkeypatch.chdir(root)
    report = validate_overlay_authority()
    assert not report.passed
    assert "conflict" in _codes(report)


def test_stale_versions(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    _write_overlay(root)
    registry_path = root / ".loom" / "overlays" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["overlays"]["overlay.test"]["version"] = "9.9.9"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.chdir(root)
    report = validate_overlay_authority()
    assert not report.passed
    assert "stale" in _codes(report)


def test_promotion_and_rejection(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    _write_overlay(
        root,
        lifecycle={"status": "rejected", "reason": "failed validation"},
        rejection={"rejected_by": "pytest", "reason": "bad provenance"},
    )
    monkeypatch.chdir(root)
    assert validate_overlay_authority().passed


def test_supersession(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    _write_overlay(
        root,
        lifecycle={"status": "superseded", "reason": "replaced"},
        supersession={"superseded_by": "overlay.next", "reason": "newer authority"},
    )
    monkeypatch.chdir(root)
    assert validate_overlay_authority().passed


def test_registry_file_drift(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    _write_overlay(root, applicability={"runtime": "other", "scenario_id": "*"})
    registry_path = root / ".loom" / "overlays" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["overlays"]["overlay.test"]["applicability"] = {"runtime": "workflow_evaluator", "scenario_id": "*"}
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.chdir(root)
    report = validate_overlay_authority()
    assert not report.passed
    assert "drift" in _codes(report)


def test_explicit_legacy_migration(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    path = root / ".loom" / "overlays" / "overlay.legacy.json"
    path.write_text(
        json.dumps(
            {
                "legacy_overlay": {
                    "id": "overlay.legacy",
                    "version": "1.0.0",
                    "provenance": {
                        "source": "tests",
                        "created_by": "pytest",
                        "created_at": "2026-06-29T00:00:00Z",
                        "reason": "legacy migration",
                    },
                    "authority": {
                        "authority_id": "loom.overlay.authority",
                        "signature_required": True,
                        "signature": "legacy-signature",
                    },
                    "applies_to": {"runtime": "workflow_evaluator", "scenario_id": "*"},
                    "status": "validated",
                    "reason": "migrated explicitly",
                    "promotion": {"promoted_by": "pytest", "reason": "legacy promotion"},
                    "rejection": {"rejected_by": "", "reason": "not rejected"},
                    "supersession": {"superseded_by": "", "reason": "not superseded"},
                }
            }
        ),
        encoding="utf-8",
    )
    registry_path = root / ".loom" / "overlays" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["overlays"]["overlay.legacy"] = {
        "path": ".loom/overlays/overlay.legacy.json",
        "version": "1.0.0",
        "source": "tests",
        "applicability": {"runtime": "workflow_evaluator", "scenario_id": "*"},
        "lifecycle_status": "validated",
    }
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.chdir(root)
    assert validate_overlay_authority().passed


def test_invalid_legacy_data_not_silently_accepted(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    path = root / ".loom" / "overlays" / "overlay.legacy.json"
    path.write_text(json.dumps({"legacy_id": "overlay.legacy"}), encoding="utf-8")
    registry_path = root / ".loom" / "overlays" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["overlays"]["overlay.legacy"] = {
        "path": ".loom/overlays/overlay.legacy.json",
        "version": "1.0.0",
        "source": "tests",
        "applicability": {"runtime": "workflow_evaluator", "scenario_id": "*"},
        "lifecycle_status": "validated",
    }
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.chdir(root)
    report = validate_overlay_authority()
    assert not report.passed
    assert "legacy" in _codes(report)


def test_fail_closed_evaluator_behavior(tmp_path, monkeypatch):
    root = _copy_authority(tmp_path)
    (root / ".loom" / "overlays" / "policy.json").unlink()
    monkeypatch.chdir(root)
    evaluation = evaluate_workflow(scenario_id="overlay-fail-closed")
    assert not evaluation.passed
    assert any(item.name == "overlay.authority" and not item.passed for item in evaluation.invariants)
