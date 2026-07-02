"""Load YAML/JSON contracts and validate them against canonical schemas."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml


@dataclass
class SchemaValidationError(Exception):
    source_path: str
    errors: list[str]

    def __str__(self) -> str:
        return f"{self.source_path} failed schema validation ({len(self.errors)} error(s))"


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    return value if isinstance(value, dict) else {}


def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def load_schema(path: str | Path) -> dict[str, Any]:
    return load_json(path)


def validate_instance(instance: dict[str, Any], schema_path: str | Path, source_path: str | Path) -> None:
    schema = load_schema(schema_path)
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: [str(x) for x in e.path])
    if errors:
        formatted = [f"{'/'.join(str(p) for p in error.path) or '(root)'}: {error.message}" for error in errors]
        raise SchemaValidationError(str(source_path), formatted)


def _load_validated(path: str | Path, schema_dir: str | Path, schema_name: str) -> dict[str, Any]:
    instance = load_yaml(path)
    validate_instance(instance, Path(schema_dir) / schema_name, path)
    return instance


def load_manifest(path: str | Path, schema_dir: str | Path) -> dict[str, Any]:
    return _load_validated(path, schema_dir, "screen-manifest.schema.json")


def load_action_registry(path: str | Path, schema_dir: str | Path) -> dict[str, Any]:
    return _load_validated(path, schema_dir, "action-registry.schema.json")


def load_knowledge_registry(path: str | Path, schema_dir: str | Path) -> dict[str, Any]:
    return _load_validated(path, schema_dir, "knowledge-registry.schema.json")


def load_smoke_scenario(path: str | Path, schema_dir: str | Path) -> dict[str, Any]:
    return _load_validated(path, schema_dir, "smoke-scenario.schema.json")


def load_project(path: str | Path, schema_dir: str | Path) -> dict[str, Any]:
    return _load_validated(path, schema_dir, "frontend-formation.schema.json")


def element_id_counts(manifest: dict[str, Any]) -> Counter[str]:
    return Counter(str(item.get("id")) for item in manifest.get("elements", []) if item.get("id"))


def elements_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for element in manifest.get("elements", []):
        element_id = element.get("id")
        if element_id and element_id not in result:
            result[element_id] = element
    return result
