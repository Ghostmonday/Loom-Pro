"""Overlay System v2 deterministic authority.

Canonical files:
  - .loom/overlays/policy.json
  - .loom/overlays/registry.json

The validator is fail-closed: missing, malformed, stale, conflicting,
unregistered, unauthorized, or drifted overlay data produces failed checks.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CANONICAL_POLICY_PATH = Path(".loom/overlays/policy.json")
CANONICAL_REGISTRY_PATH = Path(".loom/overlays/registry.json")
TERMINAL_STATUSES = {"promoted", "rejected", "superseded"}
ACTIVE_STATUSES = {"registered", "validated", "promoting", "promoted"}


@dataclass(frozen=True)
class OverlayIssue:
    code: str
    detail: str


@dataclass(frozen=True)
class OverlayValidationReport:
    passed: bool
    issues: list[OverlayIssue] = field(default_factory=list)
    policy_version: str = ""
    registry_version: str = ""

    def as_checks(self) -> list[tuple[str, bool, str]]:
        if self.passed:
            return [("overlay.authority", True, f"policy={self.policy_version} registry={self.registry_version}")]
        return [(f"overlay.{issue.code}", False, issue.detail) for issue in self.issues]


def load_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"missing {path}"
    except json.JSONDecodeError as exc:
        return None, f"malformed json {path}: {exc.msg}"
    except OSError as exc:
        return None, f"unreadable {path}: {exc}"
    if not isinstance(payload, dict):
        return None, f"{path} must contain a JSON object"
    return payload, None


def _required_string(payload: Mapping[str, Any], key: str, issues: list[OverlayIssue], code: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        issues.append(OverlayIssue(code, f"missing or invalid string field '{key}'"))
        return ""
    return value.strip()


def _as_object(payload: Mapping[str, Any], key: str, issues: list[OverlayIssue], code: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        issues.append(OverlayIssue(code, f"missing or invalid object field '{key}'"))
        return {}
    return value


def _as_list(payload: Mapping[str, Any], key: str, issues: list[OverlayIssue], code: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        issues.append(OverlayIssue(code, f"missing or invalid list field '{key}'"))
        return []
    return value


def _validate_policy(policy: Mapping[str, Any], issues: list[OverlayIssue]) -> None:
    _required_string(policy, "policy_id", issues, "policy")
    _required_string(policy, "version", issues, "policy")
    if policy.get("fail_closed") is not True:
        issues.append(OverlayIssue("policy", "policy.fail_closed must be true"))
    required_fields = set(_as_list(policy, "required_overlay_fields", issues, "policy"))
    expected = {
        "overlay_id",
        "version",
        "provenance",
        "authority",
        "applicability",
        "lifecycle",
        "promotion",
        "rejection",
        "supersession",
    }
    missing = sorted(expected - required_fields)
    if missing:
        issues.append(OverlayIssue("policy", f"policy missing required field declarations: {missing}"))
    lifecycle = _as_object(policy, "lifecycle", issues, "policy")
    allowed_statuses = set(_as_list(lifecycle, "allowed_statuses", issues, "policy")) if lifecycle else set()
    if not TERMINAL_STATUSES.issubset(allowed_statuses):
        issues.append(OverlayIssue("policy", "lifecycle.allowed_statuses must include promoted, rejected, superseded"))
    transitions = _as_object(policy, "promotion_transitions", issues, "policy")
    for transition in ("register", "validate", "promote", "reject", "supersede"):
        rule = transitions.get(transition) if isinstance(transitions, Mapping) else None
        if not isinstance(rule, Mapping) or rule.get("reason_required") is not True:
            issues.append(OverlayIssue("policy", f"promotion transition '{transition}' must require a reason"))


def _overlay_payload_from_legacy(raw: Mapping[str, Any]) -> dict[str, Any] | None:
    """Deterministically migrate explicitly marked legacy overlay records only."""
    legacy = raw.get("legacy_overlay")
    if not isinstance(legacy, Mapping):
        return None
    return {
        "overlay_id": legacy.get("id"),
        "version": legacy.get("version"),
        "provenance": legacy.get("provenance"),
        "authority": legacy.get("authority"),
        "applicability": legacy.get("applies_to"),
        "lifecycle": {"status": legacy.get("status"), "reason": legacy.get("reason")},
        "promotion": legacy.get("promotion", {}),
        "rejection": legacy.get("rejection", {}),
        "supersession": legacy.get("supersession", {}),
    }


def _load_overlay_file(path: Path, issues: list[OverlayIssue]) -> Mapping[str, Any]:
    payload, error = load_json_file(path)
    if error or payload is None:
        issues.append(OverlayIssue("file", error or f"invalid {path}"))
        return {}
    if "overlay_id" in payload:
        return payload
    migrated = _overlay_payload_from_legacy(payload)
    if migrated is None:
        issues.append(
            OverlayIssue("legacy", f"{path} is neither Overlay v2 nor an explicitly migratable legacy overlay")
        )
        return {}
    return migrated


def _validate_overlay(
    entry_id: str,
    entry: Mapping[str, Any],
    overlay: Mapping[str, Any],
    policy: Mapping[str, Any],
    issues: list[OverlayIssue],
) -> None:
    overlay_id = _required_string(overlay, "overlay_id", issues, "malformed")
    version = _required_string(overlay, "version", issues, "malformed")
    if overlay_id != entry_id:
        issues.append(OverlayIssue("drift", f"registry id '{entry_id}' does not match overlay_id '{overlay_id}'"))
    if version != entry.get("version"):
        registry_version = entry.get("version")
        issues.append(
            OverlayIssue("stale", f"{overlay_id} file version '{version}' != registry version '{registry_version}'")
        )

    authority = _as_object(overlay, "authority", issues, "malformed")
    allowed_authorities = set(_as_list(policy, "allowed_authorities", issues, "policy"))
    authority_id = authority.get("authority_id") if authority else None
    if authority_id not in allowed_authorities:
        issues.append(OverlayIssue("unauthorized", f"{overlay_id} authority '{authority_id}' is not allowed"))
    if authority.get("signature_required") is not True or not authority.get("signature"):
        issues.append(OverlayIssue("provenance", f"{overlay_id} requires an auditable authority signature"))

    provenance = _as_object(overlay, "provenance", issues, "malformed")
    if provenance.get("source") != entry.get("source"):
        issues.append(OverlayIssue("provenance", f"{overlay_id} provenance source does not match registry"))
    for key in ("created_by", "created_at", "reason"):
        if not provenance.get(key):
            issues.append(OverlayIssue("provenance", f"{overlay_id} provenance.{key} is required"))

    applicability = _as_object(overlay, "applicability", issues, "malformed")
    declared_scope = entry.get("applicability")
    if declared_scope and applicability != declared_scope:
        issues.append(OverlayIssue("drift", f"{overlay_id} applicability differs from registry"))

    lifecycle = _as_object(overlay, "lifecycle", issues, "malformed")
    status = lifecycle.get("status")
    allowed_statuses = set((_as_object(policy, "lifecycle", issues, "policy")).get("allowed_statuses", []))
    if status not in allowed_statuses:
        issues.append(OverlayIssue("malformed", f"{overlay_id} lifecycle status '{status}' is not allowed"))
    if not lifecycle.get("reason"):
        issues.append(OverlayIssue("promotion", f"{overlay_id} lifecycle.reason is required"))
    if status != entry.get("lifecycle_status"):
        issues.append(OverlayIssue("drift", f"{overlay_id} lifecycle status differs from registry"))

    for section_name in ("promotion", "rejection", "supersession"):
        section = _as_object(overlay, section_name, issues, "malformed")
        if not section.get("reason"):
            issues.append(OverlayIssue(section_name, f"{overlay_id} {section_name}.reason is required"))
    if status == "superseded" and not overlay.get("supersession", {}).get("superseded_by"):
        issues.append(OverlayIssue("supersession", f"{overlay_id} superseded overlays require superseded_by"))
    if status == "rejected" and not overlay.get("rejection", {}).get("rejected_by"):
        issues.append(OverlayIssue("rejection", f"{overlay_id} rejected overlays require rejected_by"))


def validate_overlay_authority(
    *,
    root: Path | None = None,
    policy_path: Path | None = None,
    registry_path: Path | None = None,
) -> OverlayValidationReport:
    base = root or Path.cwd()
    policy_file = policy_path or base / CANONICAL_POLICY_PATH
    registry_file = registry_path or base / CANONICAL_REGISTRY_PATH
    issues: list[OverlayIssue] = []

    policy, policy_error = load_json_file(policy_file)
    registry, registry_error = load_json_file(registry_file)
    if policy_error or policy is None:
        issues.append(OverlayIssue("authority", policy_error or "invalid policy"))
    if registry_error or registry is None:
        issues.append(OverlayIssue("authority", registry_error or "invalid registry"))
    if issues:
        return OverlayValidationReport(False, issues)

    _validate_policy(policy, issues)
    if registry.get("policy_id") != policy.get("policy_id") or registry.get("policy_version") != policy.get("version"):
        issues.append(OverlayIssue("drift", "registry policy reference does not match canonical policy"))
    _required_string(registry, "registry_id", issues, "registry")
    _required_string(registry, "version", issues, "registry")
    entries = registry.get("overlays")
    if not isinstance(entries, Mapping):
        issues.append(OverlayIssue("registry", "registry.overlays must be an object"))
        entries = {}

    seen_identity: set[tuple[str, str, str]] = set()
    for overlay_id, entry in entries.items():
        if not isinstance(entry, Mapping):
            issues.append(OverlayIssue("registry", f"registry entry '{overlay_id}' must be an object"))
            continue
        path_value = entry.get("path")
        if not isinstance(path_value, str) or not path_value:
            issues.append(OverlayIssue("registry", f"{overlay_id} registry path is required"))
            continue
        if Path(path_value).as_posix() in {CANONICAL_POLICY_PATH.as_posix(), CANONICAL_REGISTRY_PATH.as_posix()}:
            issues.append(OverlayIssue("conflict", f"{overlay_id} cannot use canonical authority file as overlay file"))
            continue
        overlay = _load_overlay_file(base / path_value, issues)
        if not overlay:
            continue
        identity = (
            str(overlay.get("overlay_id")),
            str(overlay.get("version")),
            json.dumps(overlay.get("applicability", {}), sort_keys=True),
        )
        if identity in seen_identity and overlay.get("lifecycle", {}).get("status") in ACTIVE_STATUSES:
            issues.append(OverlayIssue("conflict", f"duplicate active overlay identity {identity}"))
        seen_identity.add(identity)
        _validate_overlay(str(overlay_id), entry, overlay, policy, issues)

    registry_dir = registry_file.parent
    for path in sorted(registry_dir.glob("*.json")):
        rel = path.relative_to(base).as_posix() if path.is_relative_to(base) else path.as_posix()
        if rel in {CANONICAL_POLICY_PATH.as_posix(), CANONICAL_REGISTRY_PATH.as_posix()}:
            continue
        registered = any(isinstance(entry, Mapping) and entry.get("path") == rel for entry in entries.values())
        if not registered:
            issues.append(OverlayIssue("unknown", f"unregistered overlay file {rel}"))

    return OverlayValidationReport(
        passed=not issues,
        issues=issues,
        policy_version=str(policy.get("version", "")),
        registry_version=str(registry.get("version", "")),
    )
