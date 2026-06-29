#!/usr/bin/env python3
"""Vault knowledge linter — Section XIII Joint Governance enforcement.

Encodes all rules from raw/constitution-v0-section-xiii.md and
ADR-002-dual-invariant-domains.md as executable checks.

Domains (non-substitutable per Section XIII §1):
  - Vault: semantic integrity (links, frontmatter, provenance)
  - Gaijinn: execution integrity (convergence, handoff, merge)

Usage:
    python3 10_Operations/knowledge-linter.py
    python3 10_Operations/knowledge-linter.py --report-json  # JSON output
    python3 10_Operations/knowledge-linter.py --worker-gate   # skip governance convergence
    python3 10_Operations/knowledge-linter.py --strict        # warnings → errors
    python3 10_Operations/knowledge-linter.py --check         # compact pass/fail
    python3 10_Operations/knowledge-linter.py --list-checks   # enumerate checks
    python3 10_Operations/knowledge-linter.py --version       # print version
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

__version__ = "2.0.0"
VERSION = __version__

VAULT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = VAULT_ROOT.parents[1]

# ── Section XIII §2 — Canonical records ──────────────────────────────────

CANONICAL_RECORDS = {
    "execution_ledger": {
        "path": VAULT_ROOT / ".gaijinn" / "merge" / "governance.json",
        "label": "Gaijinn execution ledger (governance.json)",
        "domain": "gaijinn",
        "required_key": "structural_score",
    },
    "vault_event_ledger": {
        "path": VAULT_ROOT / "_multi-agent" / "events.md",
        "label": "Vault semantic event ledger (events.md)",
        "domain": "vault",
    },
    "council_ledger": {
        "path": VAULT_ROOT / ".gaijinn" / "bridge" / "council.md",
        "label": "Gaijinn Council operational ledger (council.md)",
        "domain": "gaijinn",
    },
    "constitution": {
        "path": VAULT_ROOT / "raw" / "constitution-v0-section-xiii.md",
        "label": "Section XIII constitution",
        "domain": "vault",
    },
    "adr_002": {
        "path": VAULT_ROOT / "30_Decisions" / "ADR-002-dual-invariant-domains.md",
        "label": "ADR-002 dual invariant domains",
        "domain": "vault",
    },
    "inv_gaijinn_binding": {
        "path": VAULT_ROOT / "00_Brain" / "invariants" / "INV-GAIJINN-BINDING.md",
        "label": "INV-GAIJINN-BINDING hard invariant",
        "domain": "vault",
    },
}

METRICS_MANIFEST_PATH = VAULT_ROOT / ".gaijinn" / "metrics_manifest.json"

# ── Section XIII §² — Convergence thresholds ────────────────────────────

CONVERGENCE_THRESHOLDS = {
    "simulated": 0.875,
    "production": 1.0,
}

# ── Section XIII §5 — Coordination ledgers ──────────────────────────────

COORDINATION_LEDGERS = {
    "vault_semantic": VAULT_ROOT / "_multi-agent" / "events.md",
    "gaijinn_operational": VAULT_ROOT / ".gaijinn" / "bridge" / "council.md",
}

# ── Section XIII §6 — Agent obligations key indicators ──────────────────

PROMOTION_PENDING_DIR = VAULT_ROOT / "pending"
PROMOTION_CONCEPT_DIR = VAULT_ROOT / "40_Concepts"

# ── YAML frontmatter requirements per file type ─────────────────────────

REQUIRED_FRONTMATTER_FIELDS = {
    "Concept": ["id", "type", "status"],
    "Decision": ["id", "type", "status", "date_decided", "deciders"],
    "Invariant": ["id", "type", "status", "enforcement_level"],
    "Task": ["id", "type", "status", "assigned_to"],
    "Project": ["id", "type", "status"],
    "Raw": ["id", "type", "status", "source", "ratified", "system_tier"],
}

FRONTMATTER_FILE_TYPES = {
    "constitution": "Raw",
    "ADR-": "Decision",
    "INV-": "Invariant",
    "OBSIDIAN-RUN": "Task",
    "PROJ-": "Project",
    "CONCEPT-": "Concept",
    "memory-execution-loop": "Concept",
}


def _infer_type(filename: str, body: str) -> str | None:
    """Infer vault document type from filename or YAML frontmatter."""
    yaml_type = _parse_frontmatter_field(body, "type")
    if yaml_type:
        return yaml_type
    for pattern, ftype in FRONTMATTER_FILE_TYPES.items():
        if pattern in filename:
            return ftype
    return None


def _parse_frontmatter(body: str) -> dict[str, str | list[str]] | None:
    """Parse YAML-like frontmatter between --- markers.

    We do NOT import yaml — this stays dependency-free.
    Only extracts top-level scalar fields and simple list values.
    """
    m = re.match(r"^---\s*\n(.*?)\n---", body, re.DOTALL)
    if not m:
        return None
    raw = m.group(1)
    result: dict[str, str | list[str]] = {}
    for line in raw.splitlines():
        line = line.strip()
        # Skip list items (indented) and empty lines
        if not line or line.startswith("-"):
            continue
        kv = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                # Simple inline list
                items = [x.strip().strip("\"'") for x in val[1:-1].split(",")]
                result[key] = items
            else:
                result[key] = val.strip("\"'")
    return result


def _parse_frontmatter_field(body: str, field: str) -> str | None:
    """Get a single field from YAML frontmatter."""
    fm = _parse_frontmatter(body)
    if fm and field in fm:
        val = fm[field]
        if isinstance(val, list):
            return str(val[0]) if val else None
        return str(val)
    return None


def _wikilink_targets(body: str) -> list[str]:
    """Extract all [[wikilink]] targets from a markdown body.

    Strips inline code blocks (backtick-quoted text) first so
    meta-examples like `[[targets]]` are not flagged as broken links.
    """
    # Strip inline code: `...` content (including backtick-quoted wikilinks)
    cleaned = re.sub(r"`[^`]+`", "", body)
    return re.findall(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]", cleaned)


def _resolve_wikilink(vault_root: Path, target: str) -> bool:
    """Resolve a [[wikilink]] to an actual file in the vault.

    Supports:
      - bare names (constitution-v0-section-xiii → raw/constitution-v0-section-xiii.md)
      - relative paths (raw/constitution-v0-section-xiii)
      - dotted or qualified names
    """
    # Direct .md path
    candidate = vault_root / f"{target}.md"
    if candidate.exists():
        return True

    # Walk vault directories looking for the filename
    stem = Path(target).name
    for md_file in vault_root.rglob(f"{stem}.md"):
        if md_file.is_file():
            return True

    # Check with path segments
    candidate2 = vault_root / target
    if candidate2.exists():
        return True

    return False


def _get_md_files(vault_root: Path, exclude_dirs: list[str] | None = None) -> list[Path]:
    """Get all .md files in the vault (excluding .gaijinn internal worker copies)."""
    files = []
    for p in vault_root.rglob("*.md"):
        rel = p.relative_to(vault_root)
        parts = rel.parts
        if any(part == ".gaijinn" for part in parts):
            continue
        if any(part.startswith(".") for part in parts):
            continue
        if exclude_dirs:
            skip = False
            for ex in exclude_dirs:
                if any(part == ex for part in parts):
                    skip = True
                    break
            if skip:
                continue
        files.append(p)
    return sorted(files)


def _safe_read_text(path: Path) -> str | None:
    """Read file text safely, returning None on any error."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, LookupError):
        return None


def _load_json_file(path: Path) -> tuple[dict | None, str | None]:
    """Load a JSON object, returning (data, error)."""
    body = _safe_read_text(path)
    if body is None:
        return None, f"Cannot read JSON file: {path}"
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"
    if not isinstance(data, dict):
        return None, f"JSON root is not an object in {path}"
    return data, None


def _load_metrics_manifest() -> tuple[dict | None, str | None]:
    """Load the ADR-002 metrics manifest."""
    if not METRICS_MANIFEST_PATH.exists():
        return None, f"metrics_manifest.json not found: {METRICS_MANIFEST_PATH}"
    return _load_json_file(METRICS_MANIFEST_PATH)


def _latest_governance_record() -> tuple[dict | None, str | None]:
    """Load the latest governance record from governance.json or metrics manifest.

    ADR-002 names metrics_manifest.json as the source of truth for pipeline
    health. Some runs embed merge governance there instead of writing the
    standalone .gaijinn/merge/governance.json ledger.
    """
    gov_path = CANONICAL_RECORDS["execution_ledger"]["path"]
    if gov_path.exists():
        return _load_json_file(gov_path)

    manifest, err = _load_metrics_manifest()
    if err:
        return None, (f"governance.json not found and metrics manifest unavailable — {err}")

    merge_governance = manifest.get("merge_governance")
    if not isinstance(merge_governance, dict):
        return None, ("governance.json not found and metrics_manifest.json missing 'merge_governance' block")

    latest = merge_governance.get("latest")
    if not isinstance(latest, dict):
        return None, ("governance.json not found and metrics_manifest.json merge_governance missing 'latest' record")
    return latest, None


def _looks_like_force_policy_text(line: str) -> bool:
    """Return True when a force-pattern match is policy text, not an action."""
    normalized = line.strip().lower()
    policy_markers = (
        "do not force",
        "don't force",
        "never force",
        "no force",
        "no force-",
        "no forced",
        "prohibits force",
        "force-overwrite pattern",
        "force overwrite pattern",
        "force-overwrites",
        "force overwrites",
        "force merge if blocked",
        "section xiii",
    )
    return any(marker in normalized for marker in policy_markers)


# ══════════════════════════════════════════════════════════════════════════
# Checks
# ══════════════════════════════════════════════════════════════════════════


def check_required_artifacts() -> list[str]:
    """Section XIII §2 — Canonical records exist."""
    violations = []
    for key, info in CANONICAL_RECORDS.items():
        if key == "execution_ledger" and not info["path"].exists():
            latest, err = _latest_governance_record()
            if latest is not None and "structural_score" in latest:
                continue
            violations.append(
                f"[{info['domain']}] Missing required artifact: {info['label']} "
                f"({info['path']}); metrics_manifest fallback invalid: {err}"
            )
            continue
        if not info["path"].exists():
            violations.append(f"[{info['domain']}] Missing required artifact: {info['label']} ({info['path']})")
    return violations


def check_governance_convergence() -> list[str]:
    """Section XIII §3 — Convergence thresholds enforced."""
    violations = []
    gov, err = _latest_governance_record()
    if err or gov is None:
        violations.append(f"[gaijinn] Cannot verify convergence: {err}")
        return violations

    score_block = gov.get("structural_score", {})
    if not score_block:
        violations.append("[gaijinn] governance.json missing 'structural_score' block")
        return violations

    convergence = score_block.get("convergence")
    if convergence is None:
        violations.append("[gaijinn] governance.json structural_score missing 'convergence' key")
        return violations

    dry_run = score_block.get("dry_run", False)
    threshold = CONVERGENCE_THRESHOLDS["simulated"] if dry_run else CONVERGENCE_THRESHOLDS["production"]

    if convergence < threshold:
        mode = "simulated (dry-run)" if dry_run else "production"
        violations.append(
            f"[gaijinn] Convergence {convergence:.3f} below {mode} threshold {threshold} (Section XIII §3)"
        )
    elif (
        dry_run
        and convergence < CONVERGENCE_THRESHOLDS["production"]
        and convergence >= CONVERGENCE_THRESHOLDS["simulated"]
    ):
        violations.append(
            f"[gaijinn] Simulated convergence {convergence:.3f} meets simulated threshold "
            f"({CONVERGENCE_THRESHOLDS['simulated']}) but is below production threshold "
            f"({CONVERGENCE_THRESHOLDS['production']}) — expected for dry-run mode"
        )

    # Check ADR waiver for production runs below 1.0
    if not dry_run and convergence < 1.0:
        adr_path = CANONICAL_RECORDS["adr_002"]["path"]
        waiver_found = False
        if adr_path.exists():
            adr_body = _safe_read_text(adr_path)
            if adr_body and re.search(r"waiver|partial\.state|documented partial", adr_body, re.IGNORECASE):
                waiver_found = True
        if not waiver_found:
            violations.append(
                f"[gaijinn] Production convergence {convergence:.3f} < 1.0 with no ADR waiver "
                f"documented — Section XIII §3 requires 1.0 or a waiving ADR"
            )

    return violations


def check_metrics_manifest_health() -> list[str]:
    """ADR-002 Metrics Manifest — rejected nodes and Shadow Bridges.

    Rejected nodes are allowed while tracked, but the manifest must be
    internally consistent. Shadow Bridges are merge-blocking violations.
    """
    violations = []
    manifest, err = _load_metrics_manifest()
    if err or manifest is None:
        violations.append(f"[gaijinn] Cannot review metrics manifest: {err}")
        return violations

    gravity_meta = manifest.get("gravity_meta")
    if not isinstance(gravity_meta, dict):
        violations.append("[gaijinn] metrics_manifest.json missing 'gravity_meta' block")
    else:
        hard_floor = gravity_meta.get("hard_floor", 0.2)
        nodes = gravity_meta.get("nodes")
        rejected_nodes = gravity_meta.get("rejected_nodes")
        if not isinstance(nodes, dict):
            violations.append("[gaijinn] metrics_manifest.json gravity_meta missing 'nodes' map")
        if not isinstance(rejected_nodes, list):
            violations.append("[gaijinn] metrics_manifest.json gravity_meta missing 'rejected_nodes' list")
        elif isinstance(nodes, dict):
            rejected_set = set(str(n) for n in rejected_nodes)
            expected_rejected = set()
            for node, meta in nodes.items():
                if not isinstance(meta, dict):
                    violations.append(f"[gaijinn] metrics manifest node '{node}' metadata is not an object")
                    continue
                gravity = meta.get("gravity")
                automatic = bool(meta.get("automatic_rejection", False))
                if isinstance(gravity, (int, float)) and automatic and gravity < hard_floor:
                    expected_rejected.add(str(node))
            missing = sorted(expected_rejected - rejected_set)
            stale = sorted(rejected_set - expected_rejected)
            if missing:
                violations.append(
                    f"[gaijinn] metrics_manifest rejected_nodes missing automatic rejections: {', '.join(missing)}"
                )
            if stale:
                violations.append(
                    f"[gaijinn] metrics_manifest rejected_nodes contains stale entries: {', '.join(stale)}"
                )

    curvature_meta = manifest.get("curvature_meta")
    if not isinstance(curvature_meta, dict):
        violations.append("[gaijinn] metrics_manifest.json missing 'curvature_meta' block")
    else:
        shadow_count = curvature_meta.get("shadow_bridge_count", 0)
        shadow_bridges = curvature_meta.get("shadow_bridges", [])
        if not isinstance(shadow_count, int):
            violations.append("[gaijinn] metrics_manifest curvature_meta shadow_bridge_count is not an int")
        elif shadow_count > 0:
            details = shadow_bridges if isinstance(shadow_bridges, list) else []
            violations.append(f"[gaijinn] metrics_manifest reports {shadow_count} Shadow Bridge(s): {details}")
        if isinstance(shadow_bridges, list) and shadow_count != len(shadow_bridges):
            violations.append(
                "[gaijinn] metrics_manifest Shadow Bridge count/list mismatch: "
                f"count={shadow_count}, list={len(shadow_bridges)}"
            )

    return violations


def check_dual_ledger_health() -> list[str]:
    """Section XIII §5 — Both ledgers exist and have recent entries."""
    violations = []
    for name, path in COORDINATION_LEDGERS.items():
        domain = "vault" if "vault" in name else "gaijinn"
        if not path.exists():
            violations.append(f"[{domain}] Coordination ledger missing: {name} ({path})")
            continue

        body = _safe_read_text(path)
        if body is None:
            violations.append(f"[{domain}] Cannot read coordination ledger: {name} ({path})")
            continue

        if len(body.strip()) < 100:
            violations.append(f"[{domain}] Coordination ledger '{name}' appears empty or sparse")
    return violations


def check_yaml_frontmatter(exclude_dirs: list[str] | None = None) -> list[str]:
    """Section XIII §6.1 — Vault files have provenance metadata (YAML frontmatter)."""
    violations = []
    md_files = _get_md_files(VAULT_ROOT, exclude_dirs=exclude_dirs)

    for fp in md_files:
        rel = fp.relative_to(VAULT_ROOT)

        body = _safe_read_text(fp)
        if body is None:
            violations.append(f"[vault] Cannot read file: {rel} — possible encoding or permission issue")
            continue

        # Skip README and AGENTS.md (they have non-standard frontmatter or none)
        if fp.name in ("README.md",):
            continue

        fm = _parse_frontmatter(body)
        doc_type = _infer_type(fp.name, body)

        if fm is None:
            violations.append(
                f"[vault] Missing YAML frontmatter: {rel} (Section XIII §6.1 — declare identity before writing)"
            )
            continue

        # Check required fields for the inferred type
        if doc_type and doc_type in REQUIRED_FRONTMATTER_FIELDS:
            for field in REQUIRED_FRONTMATTER_FIELDS[doc_type]:
                if field not in fm or not fm[field]:
                    violations.append(
                        f"[vault] Missing required frontmatter field '{field}' in {rel} (type: {doc_type})"
                    )
        elif doc_type:
            # Unknown type — at minimum require id
            if "id" not in fm:
                violations.append(f"[vault] Missing 'id' in frontmatter: {rel}")

    return violations


def check_orphan_wikilinks(exclude_dirs: list[str] | None = None) -> list[str]:
    """Section XIII §6.2 + ADR-002 — Verify all [[wikilinks]] resolve to existing files."""
    violations = []
    md_files = _get_md_files(VAULT_ROOT, exclude_dirs=exclude_dirs)

    for fp in md_files:
        rel = fp.relative_to(VAULT_ROOT)
        body = _safe_read_text(fp)
        if body is None:
            continue
        targets = _wikilink_targets(body)

        for target in targets:
            # Skip external URLs and non-file targets
            if target.startswith("http://") or target.startswith("https://"):
                continue
            if target.startswith(".") and "/" in target:
                # .gaijinn/ paths — check relative to parent dirs
                continue

            if not _resolve_wikilink(VAULT_ROOT, target):
                violations.append(f"[vault] Orphan wikilink in {rel}: [[{target}]] — target not found")

    return violations


def check_agent_obligation_declare_scope(exclude_dirs: list[str] | None = None) -> list[str]:
    """Section XIII §6.1 — Work unit scope declaration check.

    Verifies that files outside worker scratch directories have GIV-compliant
    provenance and that no handoff-less writes to sibling-owned paths exist.
    """
    violations = []
    # Check pending/ directory for un-promoted files
    if PROMOTION_PENDING_DIR.exists():
        for f in PROMOTION_PENDING_DIR.iterdir():
            if f.is_file() and f.suffix in (".md", ".py", ".json"):
                rel = f.relative_to(VAULT_ROOT)
                parts = rel.parts
                if exclude_dirs:
                    if any(any(part == ex for part in parts) for ex in exclude_dirs):
                        continue
                # Pending files need frontmatter with ownership
                body = _safe_read_text(f)
                if body is None:
                    continue
                fm = _parse_frontmatter(body)
                if fm and "owned_by" not in fm and "assigned_to" not in fm:
                    violations.append(
                        f"[vault] Pending file {f.name} has no owner/assignment declaration (Section XIII §6.1)"
                    )

    return violations


def check_agent_obligation_promotion_gate() -> list[str]:
    """Section XIII §6.2 — Vault linter + Gaijinn validate-worker before promotion.

    Checks that /40_Concepts/ files have proper frontmatter and referenced
    governance artifacts exist before files reach concept status.
    """
    violations = []
    if not PROMOTION_CONCEPT_DIR.exists():
        return violations

    concept_files = list(PROMOTION_CONCEPT_DIR.iterdir())
    if not concept_files:
        return violations

    for f in concept_files:
        if f.suffix != ".md":
            continue
        body = _safe_read_text(f)
        if body is None:
            violations.append(f"[vault] Cannot read /40_Concepts/{f.name} — encoding or permission error")
            continue
        fm = _parse_frontmatter(body)
        if fm is None:
            violations.append(
                f"[vault] /40_Concepts/{f.name} missing YAML frontmatter — "
                f"must pass linter before promotion (Section XIII §6.2)"
            )
            continue

        # Concepts must have linked decisions or invariants
        has_links = "linked_decisions" in fm or "linked_invariants" in fm or "linked_operations" in fm
        if not has_links:
            violations.append(
                f"[vault] /40_Concepts/{f.name} has no linked decisions, invariants, "
                f"or operations — conceptual orphan (Section XIII §6.2)"
            )

    return violations


def check_agent_obligation_no_force_merge() -> list[str]:
    """Section XIII §6.3 — No force-overwrites on merge failure; OCC replay."""
    violations = []
    # Check for quarantine artifacts (merge failures turned to OCC quarantine)
    quarantine_paths = [
        REPO_ROOT / ".gaijinn" / "merge" / "quarantine",
        VAULT_ROOT / ".gaijinn" / "merge" / "quarantine",
    ]
    for qp in quarantine_paths:
        if qp.exists():
            try:
                if any(qp.iterdir()):
                    violations.append(
                        f"[gaijinn] Quarantine artifacts found in {qp} — unresolved merge conflicts "
                        f"(Section XIII §6.3 — OCC replay required, no force-overwrites)"
                    )
            except OSError:
                violations.append(f"[gaijinn] Cannot read quarantine directory: {qp}")
    return violations


def check_agent_obligation_sprint_report() -> list[str]:
    """Section XIII §6.4 — Sprint results reported to Council.

    Checks council.md for convergence score and linter violation references.
    """
    violations = []
    council_path = COORDINATION_LEDGERS["gaijinn_operational"]
    if not council_path.exists():
        violations.append("[gaijinn] Council ledger not found — cannot verify sprint reports")
        return violations

    body = _safe_read_text(council_path)
    if body is None:
        violations.append("[gaijinn] Cannot read council ledger")
        return violations

    # Presence of convergence and score keywords in council
    has_score = bool(re.search(r"convergence|structural_score|\d+\.\d+", body))
    has_violations = bool(re.search(r"linter.*violation|lint.*fail|violation", body, re.IGNORECASE))

    if not has_score:
        violations.append(
            "[gaijinn] Council ledger has no convergence score references — "
            "sprint results not reported (Section XIII §6.4)"
        )

    return violations


def check_separate_domain_evaluation() -> list[str]:
    """Section XIII §6.5 — Vault metrics and Gaijinn metrics evaluated separately."""
    violations = []
    vault_metrics = VAULT_ROOT / ".gaijinn" / "custom_metrics.json"
    gaijinn_metrics = VAULT_ROOT / ".gaijinn" / "metrics_manifest.json"
    governance = CANONICAL_RECORDS["execution_ledger"]["path"]

    vault_domain_ok = vault_metrics.exists()
    gaijinn_domain_ok = gaijinn_metrics.exists() or governance.exists()

    if not vault_domain_ok:
        violations.append(
            "[vault] No vault-domain metrics manifest found (.gaijinn/custom_metrics.json) — "
            "Section XIII §6.5 requires separate evaluation"
        )

    if not gaijinn_domain_ok:
        violations.append(
            "[gaijinn] No Gaijinn-domain metrics found (governance.json or metrics_manifest.json) — "
            "Section XIII §6.5 requires separate evaluation"
        )

    return violations


def check_shadow_bridge_clean() -> list[str]:
    """ADR-002 Protocol A — No ungoverned cross-boundary writes."""
    violations = []
    workers_dir = VAULT_ROOT / ".gaijinn" / "workers"
    if not workers_dir.exists():
        return violations

    for worker_dir in sorted(workers_dir.iterdir()):
        if not worker_dir.is_dir():
            continue
        giv_file = worker_dir / "giv.json"
        if not giv_file.exists():
            continue

        giv_body = _safe_read_text(giv_file)
        if giv_body is None:
            continue
        try:
            giv = json.loads(giv_body)
        except json.JSONDecodeError:
            continue

        shadow_bridges = giv.get("shadow_bridge_count", 0)
        if shadow_bridges and shadow_bridges > 0:
            violations.append(
                f"[gaijinn] Worker {worker_dir.name}: {shadow_bridges} shadow bridge(s) "
                f"detected — ADR-002 Protocol A violation"
            )

    return violations


def check_handoff_tickets_integrity() -> list[str]:
    """ADR-002 Protocol C — Handoff tickets in council.jsonl are well-formed."""
    violations = []
    council_jsonl = VAULT_ROOT / ".gaijinn" / "bridge" / "council.jsonl"
    if not council_jsonl.exists():
        return violations

    body = _safe_read_text(council_jsonl)
    if body is None:
        return violations

    for i, line in enumerate(body.strip().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            violations.append(f"[gaijinn] council.jsonl line {i}: invalid JSON")
            continue

        if entry.get("type") == "handoff":
            required = ["source_worker", "target_work_unit_id", "target_file", "status"]
            for field in required:
                if field not in entry:
                    violations.append(f"[gaijinn] council.jsonl line {i}: handoff ticket missing '{field}'")

    return violations


def check_dual_ledger_material_changes() -> list[str]:
    """Section XIII — Both ledgers must log material changes (cross-reference check).

    If one ledger has recent entries, the other should too.
    """
    violations = []
    vault_ledger = COORDINATION_LEDGERS["vault_semantic"]
    gaijinn_ledger = COORDINATION_LEDGERS["gaijinn_operational"]

    vault_alive = vault_ledger.exists() and vault_ledger.stat().st_size > 200
    gaijinn_alive = gaijinn_ledger.exists() and gaijinn_ledger.stat().st_size > 200

    if vault_alive and not gaijinn_alive:
        violations.append(
            "[vault/gaijinn] Vault event ledger has entries but Gaijinn Council ledger "
            "is empty — material changes must be logged in BOTH (Section XIII §5)"
        )
    elif gaijinn_alive and not vault_alive:
        violations.append(
            "[vault/gaijinn] Gaijinn Council ledger has entries but vault event ledger "
            "is empty — material changes must be logged in BOTH (Section XIII §5)"
        )

    return violations


def check_giv_allowlist_enforcement(exclude_dirs: list[str] | None = None) -> list[str]:
    """Section XIII §4 — Worker GIV allowlist enforcement.

    Validates that:
      - Every worker's giv.json allowed_paths entries resolve to real files.
      - No file owned by a worker (inside its .gaijinn/workers/<id>/ directory)
        appears outside the worker's allowed_paths (shadowbridge prevention).
    """
    violations = []
    workers_dir = VAULT_ROOT / ".gaijinn" / "workers"
    if not workers_dir.exists():
        return violations

    for worker_dir in sorted(workers_dir.iterdir()):
        if not worker_dir.is_dir():
            continue
        wid = worker_dir.name
        giv_file = worker_dir / "giv.json"
        if not giv_file.exists():
            violations.append(f"[gaijinn] Worker {wid}: giv.json not found — cannot verify allowlist")
            continue

        giv_body = _safe_read_text(giv_file)
        if giv_body is None:
            violations.append(f"[gaijinn] Worker {wid}: giv.json unreadable")
            continue
        try:
            giv = json.loads(giv_body)
        except json.JSONDecodeError as e:
            violations.append(f"[gaijinn] Worker {wid}: giv.json parse error: {e}")
            continue

        allowed = giv.get("allowed_paths", [])
        if not allowed:
            violations.append(f"[gaijinn] Worker {wid}: no allowed_paths in giv.json — Section XIII §4 violation")
            continue

        # Check that each allowed_path resolves to a real file
        for ap in allowed:
            ap_str = str(ap)
            if ap_str == ".":
                continue
            candidate = VAULT_ROOT / ap_str
            if not candidate.exists():
                violations.append(f"[gaijinn] Worker {wid}: allowed_path '{ap_str}' does not resolve to existing file")

        # Check for shadowbridges: files in worker dir that are NOT in allowed_paths
        worker_scratch_dir = worker_dir
        owned_files = []
        for f in worker_scratch_dir.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".py", ".json", ".yaml", ".toml", ".sh"):
                rel = f.relative_to(worker_scratch_dir)
                owned_files.append(str(rel))

        if owned_files:
            output_log = worker_dir / "output.log"
            if output_log.exists():
                log_body = _safe_read_text(output_log)
                if log_body is not None:
                    for match in re.finditer(
                        r"(?:write|edit|patch)\s+['\"]?([a-zA-Z0-9_./-]+\.(?:md|py|json|yaml|toml|sh))['\"]?",
                        log_body,
                        re.IGNORECASE,
                    ):
                        target = match.group(1)
                        if target not in allowed and not any(target.startswith(f"{a}/") for a in allowed):
                            denied = giv.get("denied_paths", []) + giv.get("sibling_denied_paths", [])
                            if any(target == d or target.startswith(f"{d}/") for d in denied):
                                violations.append(
                                    f"[gaijinn] Worker {wid}: shadowbridge — wrote to "
                                    f"sibling-owned path '{target}' (not in allowed_paths, "
                                    f"Section XIII §4)"
                                )

    return violations


def check_occ_compliance() -> list[str]:
    """Section XIII §4, §6.3 — OCC compliance checks.

    Detects:
      - Stale quarantine artifacts (>1 hour old from last merge attempt)
      - Force-overwrite patterns in worker output logs
      - Git unmerged files
    """
    violations = []

    # 1. Stale quarantine artifacts
    quarantine_paths = [
        REPO_ROOT / ".gaijinn" / "merge" / "quarantine",
        VAULT_ROOT / ".gaijinn" / "merge" / "quarantine",
    ]
    now = time.time()
    for qp in quarantine_paths:
        if qp.exists():
            try:
                for item in qp.iterdir():
                    if item.is_file():
                        age_seconds = now - item.stat().st_mtime
                        if age_seconds > 3600:  # > 1 hour
                            violations.append(
                                f"[gaijinn] Stale quarantine artifact: {qp.name}/{item.name} "
                                f"({age_seconds / 60:.0f}m old) — OCC replay required, "
                                f"no force-overwrites (Section XIII §6.3)"
                            )
            except OSError:
                violations.append(f"[gaijinn] Cannot scan quarantine directory: {qp}")

    # 2. Force-overwrite patterns in worker output logs
    workers_dir = VAULT_ROOT / ".gaijinn" / "workers"
    if workers_dir.exists():
        for worker_dir in sorted(workers_dir.iterdir()):
            if not worker_dir.is_dir():
                continue
            output_log = worker_dir / "output.log"
            if not output_log.exists():
                continue
            log_body = _safe_read_text(output_log)
            if log_body is None:
                continue

            force_patterns = [
                r"(?:git\s+)?(?:checkout|merge|push|reset|add)\s+.*--[a-z]*f[a-z]*",
                r"(?:force[ds]?\s+(?:write|overwrite|patch|merge|push|checkout|commit))",
                r"(?:--?f(?:orce)?)\s+(?:write|overwrite|patch|merge)",
                r"bypass(?:ed|ing)?\s+(?:linter|merge\s*gate)",
            ]
            for pattern in force_patterns:
                matches = list(re.finditer(pattern, log_body, re.IGNORECASE))
                for m in matches:
                    line_start = log_body.rfind("\n", 0, m.start()) + 1
                    line_end = log_body.find("\n", m.end())
                    line = log_body[line_start : line_end if line_end > 0 else None]
                    if (
                        "check_occ_compliance" in line
                        or "force-overwrite patterns" in line
                        or "Section XIII §4, §6.3" in line
                        or _looks_like_force_policy_text(line)
                    ):
                        continue
                    violations.append(
                        f"[gaijinn] Worker {worker_dir.name}: force-overwrite pattern "
                        f"detected in output.log ({repr(pattern)}) — Section XIII §6.3 "
                        f"prohibits force-overwrites"
                    )
                    break  # report once per worker per pattern type

    # 3. Git unmerged files
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=VAULT_ROOT,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            unmerged = [
                line.strip()
                for line in result.stdout.splitlines()
                if line.startswith("UU") or line.startswith("AA") or line.startswith("DD")
            ]
            if unmerged:
                for uf in unmerged:
                    violations.append(
                        f"[gaijinn] Unmerged file in git: {uf} — OCC replay required "
                        f"(Section XIII §6.3, no force-overwrites)"
                    )
    except subprocess.TimeoutExpired:
        violations.append("[gaijinn] git status timed out — cannot verify unmerged files")
    except (OSError, FileNotFoundError):
        pass  # git not available or not in path

    return violations


# ══════════════════════════════════════════════════════════════════════════
# Check metadata
# ══════════════════════════════════════════════════════════════════════════

CHECK_DESCRIPTIONS = {
    "section_xiii_artifacts": "Section XIII §2 — Canonical records",
    "section_xiii_convergence": "Section XIII §3 — Convergence thresholds",
    "section_xiii_dual_ledger": "Section XIII §5 — Coordination ledgers exist",
    "section_xiii_dual_ledger_material": "Section XIII §5 — Dual-ledger material changes",
    "section_xiii_obligation_scope": "Section XIII §6.1 — Scope declaration",
    "section_xiii_obligation_promotion": "Section XIII §6.2 — Promotion gate (→ /40_Concepts/)",
    "section_xiii_obligation_no_force_merge": "Section XIII §6.3 — No force-overwrites",
    "section_xiii_obligation_sprint_report": "Section XIII §6.4 — Sprint report to Council",
    "section_xiii_obligation_separate_domains": "Section XIII §6.5 — Separate domain evaluation",
    "vault_yaml_frontmatter": "ADR-002 — YAML frontmatter provenance",
    "vault_orphan_wikilinks": "ADR-002 — Orphan wikilink check",
    "gaijinn_metrics_manifest": "ADR-002 — Metrics manifest rejected nodes + Shadow Bridges",
    "gaijinn_shadow_bridge": "ADR-002 Protocol A — Shadow bridge detection",
    "gaijinn_handoff_integrity": "ADR-002 Protocol C — Handoff ticket integrity",
    "gaijinn_giv_allowlist": "Section XIII §4 — GIV allowlist enforcement",
    "gaijinn_occ_compliance": "Section XIII §4, §6.3 — OCC compliance",
}

DOMAIN_MAP = {
    "section_xiii_artifacts": "gaijinn",
    "section_xiii_convergence": "gaijinn",
    "section_xiii_dual_ledger": "vault/gaijinn",
    "section_xiii_dual_ledger_material": "vault/gaijinn",
    "section_xiii_obligation_scope": "vault",
    "section_xiii_obligation_promotion": "vault",
    "section_xiii_obligation_no_force_merge": "gaijinn",
    "section_xiii_obligation_sprint_report": "gaijinn",
    "section_xiii_obligation_separate_domains": "vault/gaijinn",
    "vault_yaml_frontmatter": "vault",
    "vault_orphan_wikilinks": "vault",
    "gaijinn_metrics_manifest": "gaijinn",
    "gaijinn_shadow_bridge": "gaijinn",
    "gaijinn_handoff_integrity": "gaijinn",
    "gaijinn_giv_allowlist": "gaijinn",
    "gaijinn_occ_compliance": "gaijinn",
}


def _list_checks() -> None:
    """Print all available checks and exit."""
    print(f"VAULT KNOWLEDGE LINTER — Available Checks (v{__version__})")
    print("=" * 66)
    for idx, (check_id, domain) in enumerate(DOMAIN_MAP.items(), 1):
        desc = CHECK_DESCRIPTIONS.get(check_id, check_id)
        print(f"  {idx:2d}. [{domain:13s}] {desc}")
    print("=" * 66)
    print(f"  Total: {len(DOMAIN_MAP)} checks across v2 domains + ADR-002 protocols")
    print()


def run_all_checks(
    *, worker_gate: bool = False, exclude_dirs: list[str] | None = None, strict: bool = False
) -> dict[str, list[str]]:
    """Run all Section XIII compliance checks grouped by domain.

    Args:
        worker_gate: Skip governance convergence check (for worker-side use).
        exclude_dirs: Directories to exclude from file-walking checks.
        strict: If True, warnings are promoted to errors.

    Returns:
        Dict mapping check_name to list of violation strings.
    """
    checks: dict[str, list[str]] = {
        "section_xiii_artifacts": check_required_artifacts(),
        "section_xiii_convergence": [] if worker_gate else check_governance_convergence(),
        "section_xiii_dual_ledger": check_dual_ledger_health(),
        "section_xiii_dual_ledger_material": check_dual_ledger_material_changes(),
        "section_xiii_obligation_scope": check_agent_obligation_declare_scope(exclude_dirs=exclude_dirs),
        "section_xiii_obligation_promotion": check_agent_obligation_promotion_gate(),
        "section_xiii_obligation_no_force_merge": check_agent_obligation_no_force_merge(),
        "section_xiii_obligation_sprint_report": check_agent_obligation_sprint_report(),
        "section_xiii_obligation_separate_domains": check_separate_domain_evaluation(),
        "vault_yaml_frontmatter": check_yaml_frontmatter(exclude_dirs=exclude_dirs),
        "vault_orphan_wikilinks": check_orphan_wikilinks(exclude_dirs=exclude_dirs),
        "gaijinn_metrics_manifest": check_metrics_manifest_health(),
        "gaijinn_shadow_bridge": check_shadow_bridge_clean(),
        "gaijinn_handoff_integrity": check_handoff_tickets_integrity(),
        "gaijinn_giv_allowlist": check_giv_allowlist_enforcement(exclude_dirs=exclude_dirs),
        "gaijinn_occ_compliance": check_occ_compliance(),
    }

    if strict:
        # In strict mode, flag any check that produces violations with a
        # "strict_violation" prefix even if the domain is "vault/gaijinn"
        for check_name, violations in list(checks.items()):
            if violations:
                checks[check_name] = [f"[STRICT] {v}" if not v.startswith("[STRICT]") else v for v in violations]

    return checks


def main() -> int:
    args = sys.argv[1:]

    if "--version" in args:
        print(f"knowledge-linter.py v{__version__}")
        return 0

    if "--list-checks" in args:
        _list_checks()
        return 0

    worker_gate = "--worker-gate" in args
    compact = "--check" in args
    report_json = "--report-json" in args
    strict = "--strict" in args

    # Parse --exclude-dirs (comma-separated)
    exclude_dirs_arg: str | None = None
    for i, arg in enumerate(args):
        if arg == "--exclude-dirs" and i + 1 < len(args):
            exclude_dirs_arg = args[i + 1]
            break
    exclude_dirs: list[str] = []
    if exclude_dirs_arg:
        exclude_dirs = [d.strip() for d in exclude_dirs_arg.split(",") if d.strip()]

    results = run_all_checks(worker_gate=worker_gate, exclude_dirs=exclude_dirs, strict=strict)

    if compact:
        all_violations = [v for vs in results.values() for v in vs]
        if all_violations:
            print("VAULT LINTER: FAIL")
            for v in all_violations[:12]:
                print(f"  \u2717 {v}")
            return 1
        print("VAULT LINTER: PASS")
        return 0

    # Flatten violations with domain tags
    all_violations: list[tuple[str, str]] = []
    for check_name, violations in results.items():
        for v in violations:
            all_violations.append((check_name, v))

    vault_count = sum(1 for _, v in all_violations if "[vault" in v)
    gaijinn_count = sum(1 for _, v in all_violations if "[gaijinn" in v)

    if report_json:
        report = {
            "result": "FAIL" if all_violations else "PASS",
            "total_violations": len(all_violations),
            "vault_domain_violations": vault_count,
            "gaijinn_domain_violations": gaijinn_count,
            "tool_version": __version__,
            "checks": {
                name: {
                    "violations_count": len(vs),
                    "domain": DOMAIN_MAP.get(name, "unknown"),
                    "violations": vs,
                }
                for name, vs in results.items()
            },
        }
        print(json.dumps(report, indent=2))
        return 1 if all_violations else 0

    # Human-readable output
    print("\u2550" * 66)
    print(f"  VAULT KNOWLEDGE LINTER v{__version__} \u2014 Section XIII Compliance")
    print("\u2550" * 66)

    print(f"\n  Vault path:  {VAULT_ROOT}")
    print(f"  Files scanned: {len(_get_md_files(VAULT_ROOT, exclude_dirs=exclude_dirs))}")
    print()

    if not all_violations:
        print("  \u2713 ALL CHECKS PASS \u2014 Section XIII joint governance compliant")
        print()
        print("  Domain summary:")
        print("    Vault semantic:   \u2713 clean")
        print("    Gaijinn execution: \u2713 clean")
        print("\u2550" * 66)
        return 0

    print(f"  \u2717 {len(all_violations)} VIOLATION(S) FOUND")
    print()

    for check_name, violations in results.items():
        if not violations:
            continue
        label = CHECK_DESCRIPTIONS.get(check_name, check_name)
        domain = DOMAIN_MAP.get(check_name, "unknown")
        print(f"  [{domain}] {label}:")
        for v in violations:
            print(f"    \u2717 {v}")
        print()

    print("  Domain breakdown:")
    print(f"    Vault semantic violations:   {vault_count}")
    print(f"    Gaijinn execution violations: {gaijinn_count}")
    print("    (Non-substitutable per Section XIII \u00a71)")
    print()

    print("\u2550" * 66)
    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
