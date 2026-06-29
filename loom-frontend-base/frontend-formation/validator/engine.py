"""Validation orchestration for one screen or an entire frontend-formation project."""

from __future__ import annotations

from pathlib import Path

from validator.core import ValidationResult, Violation
from validator.parser.html_loader import load_html
from validator.parser.manifest_loader import (
    SchemaValidationError,
    elements_by_id,
    load_action_registry,
    load_knowledge_registry,
    load_manifest,
    load_project,
    load_smoke_scenario,
)
from validator.rules import (
    r001_contract_anchoring,
    r002_mission_singularity,
    r003_element_mapping,
    r004_feedback_loop,
    r005_knowledge_binding,
    r006_accessibility,
    r007_smoke_verification,
)


def schema_violations(error: SchemaValidationError) -> list[Violation]:
    return [
        Violation(
            code="FFM-SCHEMA",
            severity="ERROR",
            element_ref="(schema)",
            message=message,
            rule_name="Canonical Specification",
            source=error.source_path,
        )
        for message in error.errors
    ]


def io_violation(path: str | Path, exc: Exception) -> Violation:
    return Violation(
        code="FFM-IO",
        severity="ERROR",
        element_ref="(file)",
        message=str(exc),
        rule_name="Input Boundary",
        source=str(path),
    )


def _load_scenarios(manifest_path: Path, manifest: dict, schema_dir: Path):
    scenarios = []
    violations = []
    for relative in manifest.get("smoke_scenarios", []):
        scenario_path = (manifest_path.parent / relative).resolve()
        try:
            scenarios.append((str(scenario_path), load_smoke_scenario(scenario_path, schema_dir)))
        except SchemaValidationError as error:
            violations.extend(schema_violations(error))
        except OSError as error:
            violations.append(io_violation(scenario_path, error))
    return scenarios, violations


def validate_screen(
    manifest_path: str | Path,
    html_path: str | Path,
    action_registry: dict,
    knowledge_registry: dict,
    schema_dir: str | Path,
) -> ValidationResult:
    result = ValidationResult(checked_screens=1)
    manifest_path = Path(manifest_path).resolve()
    html_path = Path(html_path).resolve()
    schema_dir = Path(schema_dir).resolve()

    try:
        manifest = load_manifest(manifest_path, schema_dir)
    except SchemaValidationError as error:
        result.extend(schema_violations(error))
        return result
    except OSError as error:
        result.violations.append(io_violation(manifest_path, error))
        return result

    try:
        document = load_html(html_path)
    except OSError as error:
        result.violations.append(io_violation(html_path, error))
        return result

    manifest_elements = elements_by_id(manifest)
    scenarios, scenario_load_violations = _load_scenarios(manifest_path, manifest, schema_dir)
    result.extend(scenario_load_violations)

    result.extend(r001_contract_anchoring.check(document, action_registry))
    result.extend(r002_mission_singularity.check(manifest, document))
    result.extend(r003_element_mapping.check(document, manifest, manifest_elements))
    result.extend(r004_feedback_loop.check(document, manifest_elements, action_registry))
    result.extend(r005_knowledge_binding.check(manifest, knowledge_registry))
    result.extend(r006_accessibility.check(document, manifest_elements))
    result.extend(r007_smoke_verification.check(manifest, scenarios, manifest_elements))
    return result


def validate_project(project_path: str | Path, schema_dir: str | Path) -> ValidationResult:
    result = ValidationResult()
    project_path = Path(project_path).resolve()
    schema_dir = Path(schema_dir).resolve()

    try:
        project = load_project(project_path, schema_dir)
    except SchemaValidationError as error:
        result.extend(schema_violations(error))
        return result
    except OSError as error:
        result.violations.append(io_violation(project_path, error))
        return result

    base = project_path.parent
    action_path = (base / project["action_registry"]).resolve()
    knowledge_path = (base / project["knowledge_registry"]).resolve()

    try:
        actions = load_action_registry(action_path, schema_dir)
    except SchemaValidationError as error:
        result.extend(schema_violations(error))
        return result
    except OSError as error:
        result.violations.append(io_violation(action_path, error))
        return result

    try:
        knowledge = load_knowledge_registry(knowledge_path, schema_dir)
    except SchemaValidationError as error:
        result.extend(schema_violations(error))
        return result
    except OSError as error:
        result.violations.append(io_violation(knowledge_path, error))
        return result

    for screen in project.get("screens", []):
        screen_result = validate_screen(
            base / screen["manifest"],
            base / screen["html"],
            actions,
            knowledge,
            schema_dir,
        )
        result.checked_screens += screen_result.checked_screens
        result.extend(screen_result.violations)

    return result
