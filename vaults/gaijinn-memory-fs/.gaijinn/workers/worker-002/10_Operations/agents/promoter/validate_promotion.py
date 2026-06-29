#!/usr/bin/env python3
"""
validate_promotion.py — Validates pending notes for promotion to /40_Concepts/

Checks:
  1.  YAML frontmatter: valid YAML, required base fields (id, type, status, tags)
  2.  Type-specific fields: Concept requires promoted_from, promoted_by, promotion_date, related_concepts
  3.  Wikilinks: all [[path]] references resolve to existing vault files
  4.  OCC compliance: provenance chain verifiable (linked refs exist)
  5.  GIV allowlist enforcement: worker-owned files respect assigned allowed paths
  6.  Convergence gate: structural_score meets threshold before concept promotion
  7.  Promotion path safety: pending file exists, target 40_Concepts/ path is clear
  8.  Promotion date freshness: promotion_date within 24h window (warning if older, error if future)
  9.  Pending cross-references: detect circular links between pending/ files
  10. Three-gates artifacts: when vault_promote phase is active, verify mirror-smoke, perf-bench, and
      human-signoff artifacts exist or are deferred
  11. Strict mode: when --strict is set, all warnings are promoted to errors

Exit codes:
  0 = PASS (all checks pass, no strict errors)
  1 = FAIL (one or more checks fail, or warnings promoted to errors in strict mode)

Usage:
  python3 validate_promotion.py --file <path> --vault-root <path>
  python3 validate_promotion.py --batch <pending-dir> --vault-root <path>
  python3 validate_promotion.py --batch <pending-dir> --vault-root <path> --report-json
  python3 validate_promotion.py --file <path> --vault-root <path> --report-json
  python3 validate_promotion.py --batch <pending-dir> --vault-root <path> --strict
  python3 validate_promotion.py --batch <pending-dir> --vault-root <path> --metrics-output <path>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# ── Frontmatter schema (from vault.yaml) ──────────────────────────

REQUIRED_BASE_FIELDS = {
    "id": {"type": "string", "description": "Unique note identifier, kebab-case"},
    "type": {
        "type": "enum",
        "values": ["Raw", "Decision", "Invariant", "Project", "Concept", "Task", "Event", "Agent"],
    },
    "status": {
        "type": "enum",
        "values": ["draft", "review", "accepted", "immutable", "completed", "active"],
    },
    "tags": {"type": "list<string>", "min_items": 1},
}

TYPE_SCHEMAS: dict[str, dict] = {
    "Raw": {"required_fields": ["source", "ratified"]},
    "Decision": {
        "required_fields": [
            "date_decided",
            "deciders",
            "supersedes",
            "superseded_by",
            "linked_constitution",
            "system_tier",
        ]
    },
    "Invariant": {
        "required_fields": ["enforcement_level", "scope"],
    },
    "Project": {
        "required_fields": [],
    },
    "Concept": {
        "required_fields": [
            "promoted_from",
            "promoted_by",
            "promotion_date",
            "related_concepts",
        ]
    },
    "Task": {"required_fields": ["assigned_to", "work_unit"]},
    "Event": {"required_fields": ["event_type", "timestamp", "actor"]},
    "Agent": {"required_fields": ["worker_id", "work_unit_ids", "profile"]},
}


# ── Check classes (enriched error metadata) ─────────────────────


class ValidationError:
    """A structured validation error with check-type classification."""

    __slots__ = ("check", "message", "file", "severity")

    def __init__(self, check: str, message: str, file: str = "", severity: str = "error"):
        self.check = check
        self.message = message
        self.file = file
        self.severity = severity

    def to_dict(self) -> dict:
        return {"check": self.check, "message": self.message, "file": self.file, "severity": self.severity}

    def __str__(self) -> str:
        prefix = f"[{self.severity.upper()}]" if self.severity != "error" else ""
        file_info = f" ({self.file})" if self.file else ""
        return f"{prefix}{self.check}: {self.message}{file_info}"


# ── Parsing ─────────────────────────────────────────────────────


def parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """Extract YAML frontmatter from markdown text.

    Returns (frontmatter_dict, error_message_or_None).
    """
    if not text.startswith("---"):
        return None, "missing YAML frontmatter (must start with '---')"

    if yaml is None:
        return None, "PyYAML not installed — cannot validate frontmatter"

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "unclosed YAML frontmatter (missing closing '---')"

    frontmatter_text = parts[1]
    if not frontmatter_text.strip():
        return None, "empty YAML frontmatter"

    try:
        fm = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        return None, f"invalid YAML frontmatter: {e}"

    if not isinstance(fm, dict):
        return None, f"frontmatter must be a dict, got {type(fm).__name__}"

    return fm, None


# ── Validation functions ────────────────────────────────────────


def validate_base_fields(fm: dict) -> list[ValidationError]:
    """Validate required base fields (id, type, status, tags)."""
    errors: list[ValidationError] = []

    for field_name, spec in REQUIRED_BASE_FIELDS.items():
        if field_name not in fm:
            errors.append(
                ValidationError("frontmatter.base", f"missing required field '{field_name}' ({spec['description']})")
            )
            continue

        value = fm[field_name]
        spec_type = spec["type"]

        if spec_type == "string":
            if not isinstance(value, str) or not value.strip():
                errors.append(ValidationError("frontmatter.base", f"'{field_name}' must be a non-empty string"))

        elif spec_type == "enum":
            if value not in spec["values"]:
                allowed = ", ".join(spec["values"])
                errors.append(
                    ValidationError("frontmatter.base", f"'{field_name}' must be one of: {allowed} (got '{value}')")
                )

        elif spec_type == "list<string>":
            if not isinstance(value, list):
                errors.append(ValidationError("frontmatter.base", f"'{field_name}' must be a list"))
            else:
                min_items = spec.get("min_items", 0)
                if len(value) < min_items:
                    errors.append(
                        ValidationError("frontmatter.base", f"'{field_name}' must have at least {min_items} item(s)")
                    )
                for item in value:
                    if not isinstance(item, str):
                        errors.append(ValidationError("frontmatter.base", f"'{field_name}' items must be strings"))

    return errors


def validate_type_specific_fields(fm: dict) -> list[ValidationError]:
    """Validate type-specific required fields."""
    errors: list[ValidationError] = []
    note_type = fm.get("type")

    if note_type and note_type in TYPE_SCHEMAS:
        schema = TYPE_SCHEMAS[note_type]
        for field_name in schema.get("required_fields", []):
            if field_name not in fm or fm[field_name] is None:
                errors.append(
                    ValidationError(
                        "frontmatter.type_specific",
                        f"missing type-specific field '{field_name}' (required for type '{note_type}')",
                    )
                )

    return errors


def validate_wikilinks(text: str, vault_root: Path) -> list[ValidationError]:
    """Validate that all [[wikilinks]] resolve to existing vault files.

    Supports:
      [[path/to/file]]           → path/to/file.md
      [[path/to/file|display]]   → path/to/file.md
      [[#heading]]               → (self-ref heading — pass)
    """
    errors: list[ValidationError] = []

    # Match [[something]] but not [[#heading]] (self-ref headings)
    # Match [[path]] and [[path|display]]
    pattern = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
    matches = pattern.findall(text)

    # Build index of all .md files in the vault (excluding pending/, .gaijinn/)
    vault_files: dict[str, Path] = {}
    for md_file in vault_root.rglob("*.md"):
        rel = md_file.relative_to(vault_root)
        # Skip hidden dirs and pending (targets don't exist yet for self-refs)
        parts = rel.parts
        if any(p.startswith(".") for p in parts):
            continue
        if parts[0] == "pending":
            continue
        # Index by stem (without .md) and by full path
        stem = rel.with_suffix("").as_posix()
        vault_files[stem] = md_file
        vault_files[md_file.stem] = md_file

    for target, display in matches:
        target = target.strip()
        if not target:
            continue

        # Self-ref headings — skip
        if target.startswith("#"):
            continue

        # External URLs — skip
        if target.startswith("http://") or target.startswith("https://"):
            continue

        # .gaijinn/ or ./gaijinn paths — skip (platform refs)
        if target.startswith(".gaijinn") or target.startswith("./gaijinn"):
            continue

        # Try to resolve
        resolved = False

        # Exact match: target → target.md
        if target in vault_files or target.endswith(".md") and target in vault_files:
            resolved = True
        # Try with / prefix stripped
        elif target.startswith("/"):
            key = target.lstrip("/")
            if key in vault_files or key.rstrip(".md") in vault_files:
                resolved = True

        if not resolved:
            errors.append(ValidationError("wikilink", f"broken wikilink: [[{target}]] ({target})"))

    return errors


def validate_occ_compliance(fm: dict, vault_root: Path) -> list[ValidationError]:
    """Validate OCC compliance: provenance chain and linked reference resolution."""
    errors: list[ValidationError] = []

    note_type = fm.get("type", "")

    # 1. Provenance chain: Concepts must have promoted_from
    if note_type == "Concept":
        promoted_from = fm.get("promoted_from")
        if not promoted_from:
            errors.append(
                ValidationError("OCC.provenance", "Concept type requires 'promoted_from' field (provenance chain)")
            )
        elif isinstance(promoted_from, str) and promoted_from:
            source_path = vault_root / promoted_from
            # Check the pending file still exists (for the original source)
            pending_candidate = vault_root / "pending" / Path(promoted_from).name
            if not source_path.exists() and not pending_candidate.exists():
                warn_only = ["source"] if vault_root.name in str(source_path) else []
                if not warn_only:
                    errors.append(
                        ValidationError(
                            "OCC.provenance",
                            f"promoted_from path '{promoted_from}' not found on disk",
                            severity="warning",
                        )
                    )

    # 2. Linked references must resolve
    linked_fields = [
        "linked_decisions",
        "linked_invariants",
        "linked_operations",
        "links",
        "related_concepts",
        "linked_constitution",
    ]
    vault_files: dict[str, Path] = {}
    for md_file in vault_root.rglob("*.md"):
        rel = md_file.relative_to(vault_root)
        parts = rel.parts
        if any(p.startswith(".") for p in parts):
            continue
        stem = rel.with_suffix("").as_posix()
        vault_files[stem] = md_file

    for field in linked_fields:
        value = fm.get(field)
        if not value:
            continue

        items: list[str] = []
        if isinstance(value, str):
            items = [value]
        elif isinstance(value, list):
            items = value

        for item in items:
            if not item or not isinstance(item, str):
                continue
            # Extract wikilink target from markdown-style link
            wl_match = re.match(r"\[\[([^\]]+)\]\]", item)
            if wl_match:
                target = wl_match.group(1)
                # Strip any display text
                if "|" in target:
                    target = target.split("|")[0]

                if target.startswith(".gaijinn"):
                    continue
                if target.startswith("#"):
                    continue

                # Resolve
                resolved = False
                key = target.rstrip(".md")
                if key in vault_files or target in vault_files:
                    resolved = True

                if not resolved:
                    errors.append(
                        ValidationError(
                            "OCC.linked_reference",
                            f"linked reference '{field}' → [[{target}]] does not resolve",
                        )
                    )

    return errors


def validate_promotion_date_freshness(fm: dict) -> list[ValidationError]:
    """Validate promotion_date is reasonable: not more than 24h in the past, not in the future."""
    errors: list[ValidationError] = []
    note_type = fm.get("type", "")
    if note_type != "Concept":
        return errors

    promotion_date = fm.get("promotion_date")
    if not promotion_date:
        return errors  # Will be caught by type-specific validation

    now = datetime.now(timezone.utc)
    try:
        if isinstance(promotion_date, str):
            dt = datetime.fromisoformat(promotion_date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        elif isinstance(promotion_date, datetime):
            dt = promotion_date
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            errors.append(ValidationError("freshness.date", "promotion_date must be an ISO-8601 string or datetime"))
            return errors

        age_hours = (now - dt).total_seconds() / 3600
        if age_hours < 0:
            errors.append(
                ValidationError(
                    "freshness.date", f"promotion_date ({promotion_date}) is in the future", severity="error"
                )
            )
        elif age_hours > 24:
            errors.append(
                ValidationError(
                    "freshness.date",
                    f"promotion_date ({promotion_date}) is {age_hours:.1f}h old — exceeds 24h freshness window",
                    severity="warning",
                )
            )
    except (ValueError, TypeError) as e:
        errors.append(ValidationError("freshness.date", f"invalid promotion_date format: {e}", severity="warning"))

    return errors


def validate_pending_cross_references(text: str, vault_root: Path, source_file: Path) -> list[ValidationError]:
    """Detect cross-references between files both in pending/ directory (circular reference risk).

    A pending file that links to another pending file creates a circular validation
    dependency — both may fail the wikilink check if the other doesn't exist yet.
    """
    errors: list[ValidationError] = []
    pending_dir = vault_root / "pending"

    # Only run for files in pending/
    if not str(source_file.resolve()).startswith(str(pending_dir.resolve())):
        return errors

    # Build list of pending files
    pending_stems: set[str] = set()
    if pending_dir.is_dir():
        for pf in pending_dir.glob("*.md"):
            pending_stems.add(pf.stem)

    if not pending_stems:
        return errors

    # Find wikilinks in this file
    pattern = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    matches = pattern.findall(text)

    for target in matches:
        target = target.strip()
        if not target or target.startswith("#") or target.startswith("http"):
            continue
        # Extract stem from target (handle path/to/file or file)
        target_stem = Path(target).stem
        if target_stem in pending_stems:
            errors.append(
                ValidationError(
                    "pending.cross_reference",
                    f"pending file links to another pending file '{target}' — circular reference risk",
                    severity="warning",
                )
            )

    return errors


def validate_three_gates_artifacts(vault_root: Path, fm: dict) -> list[ValidationError]:
    """Validate three-gates artifacts when vault_promote phase is active.

    Checks that mirror-smoke results, perf-bench results, and human-signoff
    artifacts exist or are explicitly deferred. Non-blocking — reports as
    warnings since these gates are advisory during validation.
    """
    errors: list[ValidationError] = []

    phase = fm.get("phase", "")
    subphase = fm.get("subphase", "")
    check_gates = phase == "vault_promote" or subphase in (
        "mirror_smoke",
        "perf_bench",
        "human_signoff",
        "promoting_concepts",
    )

    if not check_gates:
        return errors

    # Check mirror-smoke artifact
    smoke_path = vault_root / ".gaijinn" / "ui-intent-smoke-results.json"
    if not smoke_path.exists():
        errors.append(
            ValidationError(
                "three_gates.mirror_smoke",
                "mirror-smoke result artifact (.gaijinn/ui-intent-smoke-results.json) not found — "
                "gate must pass before promotion completes",
                severity="warning",
            )
        )

    # Check perf-bench artifact
    perf_path = vault_root / ".gaijinn" / "perf-bench-results.json"
    if not perf_path.exists():
        errors.append(
            ValidationError(
                "three_gates.perf_bench",
                "perf-bench result artifact (.gaijinn/perf-bench-results.json) not found — "
                "performance gate must pass before promotion completes",
                severity="warning",
            )
        )

    # Check human-signoff artifact
    signoff_path = vault_root / ".gaijinn" / "human-signoff.md"
    if not signoff_path.exists():
        errors.append(
            ValidationError(
                "three_gates.human_signoff",
                "human-signoff artifact (.gaijinn/human-signoff.md) not found — "
                "human approval gate must pass before promotion completes",
                severity="warning",
            )
        )

    return errors


def _read_json_file(path: Path) -> tuple[dict | None, str | None]:
    """Read a JSON object from disk, returning an error string on failure."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"
    except OSError as e:
        return None, f"cannot read file: {e}"

    if not isinstance(data, dict):
        return None, f"expected JSON object, got {type(data).__name__}"
    return data, None


def _metrics_manifest_paths(vault_root: Path) -> list[Path]:
    """Return candidate metrics manifest locations for vault and worker contexts."""
    return [
        vault_root / ".gaijinn" / "metrics_manifest.json",
        vault_root / ".." / ".gaijinn" / "metrics_manifest.json",
    ]


def _load_metrics_manifest(vault_root: Path) -> tuple[dict | None, Path | None, str | None]:
    """Load the first available metrics manifest."""
    read_errors: list[str] = []
    for manifest_path in _metrics_manifest_paths(vault_root):
        candidate = manifest_path.resolve()
        if not candidate.exists():
            continue
        manifest, error = _read_json_file(candidate)
        if manifest is None:
            read_errors.append(f"{candidate}: {error}")
            continue
        return manifest, candidate, None

    if read_errors:
        return None, None, "; ".join(read_errors)
    return None, None, "metrics_manifest.json not found"


def _latest_governance_from_metrics(manifest: dict) -> dict | None:
    """Extract the current merge governance block from metrics_manifest.json."""
    merge_governance = manifest.get("merge_governance", {})
    if not isinstance(merge_governance, dict):
        return None

    latest = merge_governance.get("latest")
    if isinstance(latest, dict):
        return latest

    runs = merge_governance.get("runs", [])
    if isinstance(runs, list) and runs:
        for run in reversed(runs):
            if isinstance(run, dict):
                return run
    return None


def validate_metrics_manifest(vault_root: Path) -> list[ValidationError]:
    """Review metrics manifest for rejected nodes and Shadow Bridges.

    Shadow Bridges are execution-boundary violations and block promotion.
    Rejected nodes are reported as warnings unless the manifest bookkeeping is
    internally inconsistent, which means the gravity floor cannot be trusted.
    """
    errors: list[ValidationError] = []
    manifest, manifest_path, manifest_error = _load_metrics_manifest(vault_root)
    if manifest is None:
        errors.append(
            ValidationError(
                "metrics.manifest",
                f"{manifest_error} — cannot review rejected nodes or Shadow Bridges",
                severity="warning",
            )
        )
        return errors

    manifest_file = str(manifest_path) if manifest_path else ""

    curvature_meta = manifest.get("curvature_meta", {})
    if isinstance(curvature_meta, dict):
        shadow_bridge_count = curvature_meta.get("shadow_bridge_count", 0)
        try:
            shadow_bridge_count = int(shadow_bridge_count)
        except (TypeError, ValueError):
            errors.append(
                ValidationError(
                    "metrics.shadow_bridge",
                    f"shadow_bridge_count is not numeric: {shadow_bridge_count!r}",
                    file=manifest_file,
                )
            )
            shadow_bridge_count = 0

        if shadow_bridge_count > 0:
            errors.append(
                ValidationError(
                    "metrics.shadow_bridge",
                    f"{shadow_bridge_count} Shadow Bridge(s) detected — promotion blocked by ADR-002 Protocol A",
                    file=manifest_file,
                )
            )
    else:
        errors.append(ValidationError("metrics.shadow_bridge", "curvature_meta must be an object", file=manifest_file))

    gravity_meta = manifest.get("gravity_meta", {})
    if not isinstance(gravity_meta, dict):
        errors.append(ValidationError("metrics.rejected_nodes", "gravity_meta must be an object", file=manifest_file))
        return errors

    hard_floor = gravity_meta.get("hard_floor", 0.2)
    try:
        hard_floor = float(hard_floor)
    except (TypeError, ValueError):
        errors.append(
            ValidationError(
                "metrics.rejected_nodes",
                f"gravity hard_floor is not numeric: {hard_floor!r}",
                file=manifest_file,
            )
        )
        hard_floor = 0.2

    nodes = gravity_meta.get("nodes", {})
    rejected_nodes = gravity_meta.get("rejected_nodes", [])
    if not isinstance(nodes, dict):
        errors.append(
            ValidationError("metrics.rejected_nodes", "gravity_meta.nodes must be an object", file=manifest_file)
        )
        nodes = {}
    if not isinstance(rejected_nodes, list):
        errors.append(
            ValidationError("metrics.rejected_nodes", "gravity_meta.rejected_nodes must be a list", file=manifest_file)
        )
        rejected_nodes = []

    rejected_set = {node for node in rejected_nodes if isinstance(node, str)}
    computed_rejected: set[str] = set()
    for node, node_meta in nodes.items():
        if not isinstance(node, str) or not isinstance(node_meta, dict):
            continue
        gravity = node_meta.get("gravity")
        try:
            gravity_value = float(gravity)
        except (TypeError, ValueError):
            errors.append(
                ValidationError(
                    "metrics.rejected_nodes",
                    f"node '{node}' has non-numeric gravity: {gravity!r}",
                    file=manifest_file,
                )
            )
            continue
        if gravity_value < hard_floor and node_meta.get("automatic_rejection") is True:
            computed_rejected.add(node)

    missing = sorted(computed_rejected - rejected_set)
    stale = sorted(rejected_set - computed_rejected)
    if missing:
        errors.append(
            ValidationError(
                "metrics.rejected_nodes",
                f"{len(missing)} rejected node(s) missing from gravity_meta.rejected_nodes: {', '.join(missing)}",
                file=manifest_file,
            )
        )
    if stale:
        errors.append(
            ValidationError(
                "metrics.rejected_nodes",
                f"{len(stale)} stale rejected node(s) listed above gravity floor: {', '.join(stale)}",
                file=manifest_file,
            )
        )

    if rejected_set and not missing and not stale:
        errors.append(
            ValidationError(
                "metrics.rejected_nodes",
                f"{len(rejected_set)} rejected node(s) reviewed; gravity bookkeeping is consistent",
                file=manifest_file,
                severity="warning",
            )
        )

    return errors


def validate_giv_allowlist(fm: dict) -> list[ValidationError]:
    """Validate GIV allowlist enforcement: worker-owned files respect scoped paths.

    Checks that if the file declares a work unit or worker_id, it does not
    reference prohibited sibling-owned paths.
    """
    errors: list[ValidationError] = []

    worker_id = fm.get("worker_id", "")
    links = fm.get("links", [])
    if not isinstance(links, list):
        links = [links] if links else []

    for link in links:
        if isinstance(link, str) and link.startswith("[["):
            target = link.strip("[]")
            if "|" in target:
                target = target.split("|")[0]
            # Flag cross-domain direct writes to prohibited paths
            prohibited_prefixes = (
                ".agents/",
                "00_Brain/invariants/",
                "30_Decisions/",
                "40_Concepts/",
            )
            for prefix in prohibited_prefixes:
                if target.startswith(prefix):
                    errors.append(
                        ValidationError(
                            "GIV.allowlist",
                            f"link to '{target}' may cross GIV boundary (prohibited for worker {worker_id})",
                            severity="warning",
                        )
                    )

    return errors


def validate_convergence_gate(vault_root: Path, threshold_override: float | None = None) -> list[ValidationError]:
    """Validate convergence gate: structural_score meets threshold before promotion.

    Args:
        vault_root: Root of the vault to check governance.json under.
        threshold_override: If set, overrides the default threshold (0.875 dry-run / 1.0 production).
            Used when --convergence-threshold flag is passed via CLI.
    """
    errors: list[ValidationError] = []

    governance_paths = [
        vault_root / ".gaijinn" / "merge" / "governance.json",
        vault_root / ".." / ".gaijinn" / "merge" / "governance.json",
    ]

    governance = None
    governance_source = None
    for gp in governance_paths:
        gp = gp.resolve()
        if gp.exists():
            governance, error = _read_json_file(gp)
            if governance is None:
                continue
            governance_source = gp

    if governance is None:
        manifest, manifest_path, _manifest_error = _load_metrics_manifest(vault_root)
        if manifest is not None:
            governance = _latest_governance_from_metrics(manifest)
            governance_source = manifest_path

    if governance is None:
        errors.append(
            ValidationError(
                "convergence.gate",
                "governance.json not found and metrics_manifest.json has no latest merge_governance — "
                "cannot verify convergence threshold",
            )
        )
        return errors

    structural_score = governance.get("structural_score", {})
    if not isinstance(structural_score, dict):
        errors.append(
            ValidationError(
                "convergence.gate",
                f"structural_score must be an object in {governance_source}",
            )
        )
        return errors

    convergence = structural_score.get("convergence", 0.0)
    try:
        convergence = float(convergence)
    except (TypeError, ValueError):
        errors.append(
            ValidationError(
                "convergence.gate",
                f"convergence value is not numeric in {governance_source}: {convergence!r}",
            )
        )
        return errors

    # Override threshold if explicitly provided, otherwise use dry_run-aware default
    if threshold_override is not None:
        threshold = threshold_override
        dry_run = structural_score.get("dry_run", False)  # still capture for the error message
    else:
        dry_run = structural_score.get("dry_run", False)
        threshold = 0.875 if dry_run else 1.0

    if convergence < threshold:
        errors.append(
            ValidationError(
                "convergence.gate",
                f"convergence {convergence} < threshold {threshold} (dry_run={dry_run}) — promotion blocked until convergence met",
                severity="error",
            )
        )

    return errors


def validate_promotion_path_safety(fm: dict, vault_root: Path, source_file: Path) -> list[ValidationError]:
    """Validate promotion path safety: source file exists, target path is clear."""
    errors: list[ValidationError] = []

    note_type = fm.get("type", "")
    if note_type != "Concept":
        return errors

    # Source verification
    if note_type == "Concept":
        promoted_from = fm.get("promoted_from", "")
        if promoted_from:
            source = vault_root / promoted_from
            if not source.exists():
                # Check if the source is a pending file
                pending_source = vault_root / "pending" / promoted_from
                if not pending_source.exists():
                    pending_source2 = vault_root / "pending" / Path(promoted_from).name
                    if not pending_source2.exists():
                        errors.append(
                            ValidationError(
                                "promotion.path",
                                f"promoted_from source '{promoted_from}' not found in pending/ or vault",
                            )
                        )

    # Target path: derived from file id or name
    note_id = fm.get("id", "")
    if note_id:
        target_path = vault_root / "40_Concepts" / f"{note_id}.md"
        if target_path.exists():
            errors.append(
                ValidationError(
                    "promotion.path",
                    f"target path 40_Concepts/{note_id}.md already exists — promotion would overwrite existing note",
                )
            )

    return errors


# ── File validation orchestrator ─────────────────────────────────


def validate_file(
    filepath: Path, vault_root: Path, convergence_threshold: float | None = None
) -> list[ValidationError]:
    """Run all validations on a single file. Returns list of errors (empty = pass)."""
    errors: list[ValidationError] = []

    if not filepath.exists():
        return [ValidationError("file", f"file not found: {filepath}")]

    text = filepath.read_text(encoding="utf-8")

    # ── 1. Frontmatter validation ──
    fm, fm_err = parse_frontmatter(text)
    if fm_err:
        errors.append(ValidationError("frontmatter.parse", fm_err, file=str(filepath)))
        return errors  # Can't proceed without valid frontmatter
    assert fm is not None  # type safety — early return above handles None

    base_errors = validate_base_fields(fm)
    errors.extend(base_errors)

    type_errors = validate_type_specific_fields(fm)
    errors.extend(type_errors)

    # ── 2. Wikilink validation ──
    wl_errors = validate_wikilinks(text, vault_root)
    errors.extend(wl_errors)

    # ── 3. OCC compliance ──
    occ_errors = validate_occ_compliance(fm, vault_root)
    errors.extend(occ_errors)

    # ── 4. GIV allowlist enforcement ──
    giv_errors = validate_giv_allowlist(fm)
    errors.extend(giv_errors)

    # ── 5. Convergence gate ──
    cvg_errors = validate_convergence_gate(vault_root, threshold_override=convergence_threshold)
    errors.extend(cvg_errors)

    # ── 6. Metrics manifest review (rejected nodes / Shadow Bridges) ──
    metrics_errors = validate_metrics_manifest(vault_root)
    errors.extend(metrics_errors)

    # ── 7. Promotion path safety ──
    prom_errors = validate_promotion_path_safety(fm, vault_root, filepath)
    errors.extend(prom_errors)

    # ── 8. Promotion date freshness ──
    fresh_errors = validate_promotion_date_freshness(fm)
    errors.extend(fresh_errors)

    # ── 9. Pending cross-reference detection ──
    xref_errors = validate_pending_cross_references(text, vault_root, filepath)
    errors.extend(xref_errors)

    # ── 10. Three-gates artifacts (vault_promote phase) ──
    gates_errors = validate_three_gates_artifacts(vault_root, fm)
    errors.extend(gates_errors)

    return errors


def validate_batch(
    pending_dir: Path, vault_root: Path, convergence_threshold: float | None = None
) -> dict[str, list[ValidationError]]:
    """Validate all .md files in a directory. Returns {filename: [errors]}."""
    results: dict[str, list[ValidationError]] = {}

    if not pending_dir.is_dir():
        print(f"ERROR: '{pending_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(pending_dir.glob("*.md"))
    if not md_files:
        print(f"WARNING: no .md files found in '{pending_dir}'", file=sys.stderr)

    for md_file in md_files:
        errors = validate_file(md_file, vault_root, convergence_threshold=convergence_threshold)
        results[md_file.name] = errors

    return results


# ── Main ─────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pending notes for promotion")
    parser.add_argument("--file", help="Path to a single pending file")
    parser.add_argument("--batch", help="Directory path containing pending .md files to validate")
    parser.add_argument("--vault-root", required=True, help="Vault root directory")
    parser.add_argument(
        "--report-json",
        action="store_true",
        help="Output structured JSON report instead of plain text",
    )
    parser.add_argument(
        "--convergence-threshold",
        type=float,
        default=None,
        help="Override convergence threshold (default: 0.875 for dry-run, 1.0 for production)",
    )
    parser.add_argument(
        "--metrics-output",
        type=str,
        default=None,
        help="Path to write metrics_manifest-compatible validation results JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Upgrade all warnings to errors — exit code 1 if any warning is present",
    )
    args = parser.parse_args()

    if not args.file and not args.batch:
        print("ERROR: either --file or --batch is required", file=sys.stderr)
        return 1

    vault_root = Path(args.vault_root).resolve()
    if not vault_root.is_dir():
        print(f"ERROR: vault root '{vault_root}' is not a directory", file=sys.stderr)
        return 1

    if args.batch:
        pending_dir = Path(args.batch).resolve()
        results = validate_batch(pending_dir, vault_root, convergence_threshold=args.convergence_threshold)
    else:
        filepath = Path(args.file).resolve()
        errors = validate_file(filepath, vault_root, convergence_threshold=args.convergence_threshold)
        results = {filepath.name: errors}

    # ── Compute summary ──
    total_files = len(results)
    strict = args.strict
    total_errors = sum(
        1
        for errs in results.values()
        for err in errs
        if err.severity == "error" or (strict and err.severity == "warning")
    )
    total_warnings = sum(1 for errs in results.values() for err in errs if err.severity == "warning" and not strict)
    if strict:
        passed_files = sum(1 for errs in results.values() if not errs)
    else:
        passed_files = sum(1 for errs in results.values() if not errs)
    has_blocking = total_errors > 0

    meta = {
        "validator": "validate_promotion.py",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vault_root": str(vault_root),
        "total_files": total_files,
        "passed": passed_files,
        "errors": total_errors,
        "warnings": total_warnings,
        "result": "FAIL" if has_blocking else "PASS",
    }

    # ── Metrics output ──
    if args.metrics_output:
        metrics_path = Path(args.metrics_output).resolve()
        metrics_data = {
            "validator_results": {
                "meta": {k: v for k, v in meta.items() if k != "files"},
                "files": {},
                "node_updates": [],
            }
        }
        for fname, errs in results.items():
            file_data = {
                "errors": [e.to_dict() for e in errs if e.severity == "error"],
                "warnings": [e.to_dict() for e in errs if e.severity == "warning"],
                "passed": not errs,
            }
            metrics_data["validator_results"]["files"][fname] = file_data
            # Generate node update entries for gravity metrics
            check_types_seen: set[str] = set()
            for e in errs:
                check_types_seen.add(e.check)
            metrics_data["validator_results"]["node_updates"].append(
                {
                    "node": f"pending/{fname}",
                    "validated_at": meta["timestamp"],
                    "validation_result": "pass" if not errs else "fail",
                    "blocking_errors": len([e for e in errs if e.severity == "error"]),
                    "warnings": len([e for e in errs if e.severity == "warning"]),
                    "check_types": sorted(check_types_seen),
                }
            )

        try:
            metrics_path.write_text(json.dumps(metrics_data, indent=2), encoding="utf-8")
            if not args.report_json and not args.batch and not args.file:
                print(f"Metrics output written to {metrics_path}", file=sys.stderr)
        except OSError as e:
            print(f"ERROR: cannot write metrics output to {metrics_path}: {e}", file=sys.stderr)
            return 1

    if args.report_json:
        # Structured JSON output
        report: dict = {**meta}
        report["files"] = {}
        for fname, errs in results.items():
            report["files"][fname] = {
                "errors": [e.to_dict() for e in errs if e.severity == "error"],
                "warnings": [e.to_dict() for e in errs if e.severity == "warning"],
                "passed": not errs,
            }
        print(json.dumps(report, indent=2))
        return 1 if has_blocking else 0

    # Plain text output
    if has_blocking:
        print("=== FAIL ===")
    else:
        print("=== PASS ===")

    print(f"Files: {total_files}  Passed: {passed_files}  Errors: {total_errors}  Warnings: {total_warnings}")
    print()

    for fname in sorted(results.keys()):
        errs = results[fname]
        if not errs:
            print(f"  ✓ {fname} — pass")
            continue
        print(f"  ✗ {fname} — {len(errs)} issue(s)")
        for e in errs:
            print(f"      {e}")

    return 1 if has_blocking else 0


if __name__ == "__main__":
    sys.exit(main())
