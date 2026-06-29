"""Shared merge-pipeline utilities for collect, validate, and merge-grid.

GAIJINN BLUEPRINT — post-sprint integration pipeline
----------------------------------------------------
Layer: CLI deploy aftermath (collect → validate → merge-grid)
Status: shipped — collect/validate/merge-grid + copy-mode fallback + governance scoring
Commands: gaijinn collect, validate-worker, merge-grid
Artifacts: .gaijinn/merge/{collected,validated,report,governance}.json

Product gap: intent map has no MergeValidation subphase yet; UI jumps to Complete.
AI agents — extend classify_worker_status / detect_trespasses before UI work.

Invariants (must never regress):
  - PROTECTED_INVARIANT_PATHS never merged from workers
  - Blocked workers (trespass, failed output.log) excluded from merge order
  - worker_merge_order respects blueprint depends_on DAG

Robustness: surface merge_pipeline_status() to orchestrate API for terminal chip.
"""

from __future__ import annotations

import filecmp
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from ..blueprint import Blueprint
from ..errors import CollectError, ConflictError, MergeError
from ..giv import GIV
from .constants import (
    BLUEPRINT_JSON_PATH,
    GAIJINN_DIR,
    OUTPUT_LOG_FILENAME,
    WORKER_HANDOFF_BASENAMES,
    WORKERS_DIR,
)
from .io import _load_blueprint_optional, _load_giv
from .workers import _paths_overlap

MERGE_DIR = GAIJINN_DIR / "merge"
COLLECTED_PATH = MERGE_DIR / "collected.json"
VALIDATED_PATH = MERGE_DIR / "validated.json"
REPORT_PATH = MERGE_DIR / "report.json"
GOVERNANCE_PATH = MERGE_DIR / "governance.json"
COMPLETION_LEDGER_PATH = MERGE_DIR / "completion-ledger.json"
MERGE_ARCHIVE_DIR = MERGE_DIR / "archive"
HANDOFF_QUEUE_PATH = MERGE_DIR / "handoff-queue.json"
MERGE_ARTIFACT_BASENAMES = (
    "collected.json",
    "validated.json",
    "report.json",
    "governance.json",
    "completion-ledger.json",
    "handoff-queue.json",
)
INTEGRATION_BRANCH = "loom/integration"
GOVERNANCE_SCHEMA_VERSION = 1
PROTECTED_INVARIANT_PATHS = (
    ".gaijinn/",
    "CLAUDE.md",
    ".cursorrules",
)
ERROR_TAIL_PATTERNS = (
    re.compile(r"\berror\b", re.IGNORECASE),
    re.compile(r"\bfailed\b", re.IGNORECASE),
    re.compile(r"\bfatal\b", re.IGNORECASE),
    re.compile(r"exit\s+code\s*:\s*(?!0\b)\d+", re.IGNORECASE),
    re.compile(r"FAILED \(exit [1-9]\d*\)", re.IGNORECASE),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_merge_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically write deterministic JSON for merge pipeline artifacts."""
    if path.name == COMPLETION_LEDGER_PATH.name:
        entries = payload.get("entries", [])
        if isinstance(entries, list) and not entries and path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing = {}
            if isinstance(existing, dict) and existing.get("entries"):
                project_root = path.parent.parent.parent
                if completion_ledger_is_protected(project_root):
                    raise MergeError(
                        "completion ledger is protected while convergence>=1.0",
                        cause="refusing to write empty completion-ledger.json",
                        fix_command="archive merge artifacts first; clear converged_at before intentional reset",
                    )
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def archive_merge_artifacts(project_root: Path, label: str | None = None) -> Path:
    """Copy merge pipeline artifacts into ``.gaijinn/merge/archive/<label>/``."""
    stamp = label or utc_now().replace(":", "-")
    archive_dir = project_root / MERGE_ARCHIVE_DIR / stamp
    archive_dir.mkdir(parents=True, exist_ok=True)
    merge_root = project_root / MERGE_DIR
    for basename in MERGE_ARTIFACT_BASENAMES:
        source = merge_root / basename
        if source.exists():
            shutil.copy2(source, archive_dir / basename)
    return archive_dir


def _governance_convergence(project_root: Path) -> float:
    path = project_root / GOVERNANCE_PATH
    if not path.exists():
        return 0.0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0.0
    if not isinstance(payload, dict):
        return 0.0
    score = payload.get("structural_score", {})
    if not isinstance(score, dict):
        return 0.0
    try:
        return float(score.get("convergence", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def completion_ledger_is_protected(
    project_root: Path,
    *,
    hermes_state: Mapping[str, Any] | None = None,
) -> bool:
    """Refuse destructive ledger wipes when vault is fully converged."""
    ledger = load_completion_ledger(project_root)
    if not ledger.get("entries"):
        return False
    convergence = _governance_convergence(project_root)
    if convergence < 1.0:
        return False
    if (
        hermes_state is not None
        and hermes_state.get("converged_at")
        and float(hermes_state.get("convergence", 0) or 0) >= 1.0
    ):
        return True
    return convergence >= 1.0


def load_completion_ledger(project_root: Path) -> dict[str, Any]:
    path = project_root / COMPLETION_LEDGER_PATH
    if not path.exists():
        return {"schema_version": 1, "entries": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"schema_version": 1, "entries": []}
    if not isinstance(payload, dict):
        return {"schema_version": 1, "entries": []}
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    return {"schema_version": 1, "entries": [entry for entry in entries if isinstance(entry, Mapping)]}


def completion_ledger_entries_by_wu(project_root: Path) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for entry in load_completion_ledger(project_root).get("entries", []):
        if not isinstance(entry, Mapping):
            continue
        wu_id = str(entry.get("wu_id", "")).strip()
        if wu_id:
            entries[wu_id] = dict(entry)
    return entries


def content_hash_for_allowed_paths(project_root: Path, allowed_paths: Sequence[str]) -> str:
    """Hash current post-weld file contents under a work unit's allowed paths."""
    digest = hashlib.sha256()
    for relative in _iter_scope_relative_files(project_root, allowed_paths):
        path = project_root / relative
        if not path.is_file():
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def ledger_entry_matches_current_root(
    project_root: Path, entry: Mapping[str, Any], allowed_paths: Sequence[str]
) -> bool:
    expected = str(entry.get("content_hash", "")).strip()
    return bool(expected) and content_hash_for_allowed_paths(project_root, allowed_paths) == expected


def upsert_completion_ledger_entries(
    project_root: Path,
    entries: Sequence[Mapping[str, Any]],
    *,
    hermes_state: Mapping[str, Any] | None = None,
    allow_wipe: bool = False,
) -> int:
    """Append/update completion ledger entries by WU id; return changed entry count."""
    ledger = load_completion_ledger(project_root)
    by_wu = completion_ledger_entries_by_wu(project_root)
    changed = 0
    for entry in entries:
        wu_id = str(entry.get("wu_id", "")).strip()
        if not wu_id:
            continue
        normalized = dict(entry)
        if by_wu.get(wu_id) != normalized:
            changed += 1
        by_wu[wu_id] = normalized
    if not by_wu and completion_ledger_is_protected(project_root, hermes_state=hermes_state) and not allow_wipe:
        raise MergeError(
            "completion ledger is protected while convergence>=1.0",
            cause="refusing to wipe converged ledger entries",
            fix_command="archive merge artifacts first; clear converged_at before intentional reset",
        )
    ledger["entries"] = [by_wu[wu_id] for wu_id in sorted(by_wu)]
    write_merge_json(project_root / COMPLETION_LEDGER_PATH, ledger)
    return changed


def load_worker_manifest(workers_path: Path) -> dict[str, Any]:
    manifest_path = workers_path / "manifest.json"
    if not manifest_path.exists():
        raise CollectError(
            "worker manifest missing",
            cause=f"expected manifest at {manifest_path}",
            fix_command="gaijinn run-grid --workers 2",
        )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CollectError(
            "worker manifest is invalid JSON",
            cause=str(exc),
            fix_command="gaijinn run-grid --workers 2 --force",
        ) from exc
    if not isinstance(payload, dict):
        raise CollectError("worker manifest must contain a JSON object", fix_command="gaijinn run-grid --workers 2")
    return payload


def worker_details_map(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    details = manifest.get("worker_details", [])
    if isinstance(details, list):
        return {
            str(item.get("worker_id")): dict(item)
            for item in details
            if isinstance(item, Mapping) and item.get("worker_id")
        }
    workers = manifest.get("workers", [])
    if isinstance(workers, list):
        return {str(worker_id): {"worker_id": str(worker_id)} for worker_id in workers}
    return {}


def git_run(cwd: Path, args: Sequence[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "commit.gpgsign=false", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=check,
    )


def resolve_base_branch(project_root: Path, override: str | None = None) -> str:
    if override:
        return override.strip()
    result = git_run(project_root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return "main"


def resolve_base_ref(project_root: Path, base_branch: str) -> str:
    for ref in (base_branch, "main", "master", "HEAD"):
        result = git_run(project_root, ["rev-parse", "--verify", ref])
        if result.returncode == 0:
            return result.stdout.strip()
    raise MergeError(
        f"cannot resolve base ref from branch {base_branch!r}",
        cause="git could not resolve the integration base branch",
        fix_command="git checkout main",
    )


def worker_has_git(worker_dir: Path) -> bool:
    git_path = worker_dir / ".git"
    return git_path.exists()


WORKER_TREE_IGNORE_DIRS = frozenset({".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"})


def _iter_worker_tree_files(worker_dir: Path) -> list[str]:
    """Enumerate project files under a worker checkout (full tree, minus metadata)."""
    discovered: set[str] = set()
    if not worker_dir.is_dir():
        return []
    for path in worker_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(worker_dir)
        if any(part in WORKER_TREE_IGNORE_DIRS for part in rel.parts):
            continue
        if rel.name in WORKER_HANDOFF_BASENAMES:
            continue
        if rel.name in {OUTPUT_LOG_FILENAME, "codex-last-message.txt", "giv.json", "metadata.json"}:
            continue
        if rel.name in {"WORKER_INTENT.txt", "intent.txt", "WORK_UNIT.md"}:
            continue
        discovered.add(rel.as_posix())
    return sorted(discovered)


def _iter_scope_relative_files(root: Path, scope_paths: Sequence[str]) -> list[str]:
    """Expand GIV allowed paths into posix-relative file paths under root."""
    discovered: set[str] = set()
    for scope in scope_paths:
        normalized = str(scope).replace("\\", "/").strip()
        if not normalized:
            continue
        target = root / normalized
        if target.is_file():
            discovered.add(PurePosixPath(normalized).as_posix())
            continue
        if target.is_dir():
            for path in target.rglob("*"):
                if path.is_file():
                    discovered.add(path.relative_to(root).as_posix())
            continue
        if target.exists():
            discovered.add(PurePosixPath(normalized).as_posix())
    return sorted(discovered)


def apply_copy_mode_worker_changes(
    worker_dir: Path,
    project_root: Path,
    relative_paths: Sequence[str],
) -> list[str]:
    """Apply scoped filesystem mutations from a copy-mode worker into project_root."""
    applied: list[str] = []
    for relative in relative_paths:
        source = worker_dir / relative
        if not source.is_file():
            continue
        destination = project_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        applied.append(relative)
    return sorted(applied)


def changed_files_filesystem(
    worker_dir: Path,
    baseline_dir: Path,
    scope_paths: Sequence[str] | None = None,
) -> list[str]:
    """Compare the full worker tree to session baseline (scope_paths ignored for discovery)."""
    del scope_paths  # retained for call-site compatibility; trespass uses full-tree diff
    changed: list[str] = []
    for relative in _iter_worker_tree_files(worker_dir):
        worker_file = worker_dir / relative
        baseline_file = baseline_dir / relative
        if not baseline_file.is_file() or not filecmp.cmp(worker_file, baseline_file, shallow=False):
            changed.append(relative)
    return sorted(set(changed))


def _line_delta_for_files(
    worker_dir: Path,
    baseline_dir: Path,
    relative_paths: Sequence[str],
) -> tuple[int, int]:
    insertions = 0
    deletions = 0
    for relative in relative_paths:
        worker_file = worker_dir / relative
        baseline_file = baseline_dir / relative
        worker_lines = (
            worker_file.read_text(encoding="utf-8", errors="replace").splitlines() if worker_file.is_file() else []
        )
        baseline_lines = (
            baseline_file.read_text(encoding="utf-8", errors="replace").splitlines() if baseline_file.is_file() else []
        )
        insertions += max(0, len(worker_lines) - len(baseline_lines))
        deletions += max(0, len(baseline_lines) - len(worker_lines))
    return insertions, deletions


def _git_changed_files(worker_dir: Path, base_ref: str) -> list[str]:
    discovered: set[str] = set()
    for args in (
        ["diff", "--name-only", base_ref],
        ["diff", "--name-only", "--cached", base_ref],
        ["diff", "--name-only", "HEAD"],
    ):
        result = git_run(worker_dir, args)
        if result.returncode == 0:
            discovered.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    untracked = git_run(worker_dir, ["ls-files", "--others", "--exclude-standard"])
    if untracked.returncode == 0:
        discovered.update(line.strip() for line in untracked.stdout.splitlines() if line.strip())
    return sorted(discovered)


def changed_files(
    worker_dir: Path,
    base_ref: str,
    *,
    baseline_dir: Path | None = None,
    scope_paths: Sequence[str] | None = None,
) -> list[str]:
    if worker_has_git(worker_dir):
        return _git_changed_files(worker_dir, base_ref)
    if baseline_dir is not None:
        return changed_files_filesystem(worker_dir, baseline_dir, scope_paths)
    return []


def diff_summary(
    worker_dir: Path,
    base_ref: str,
    *,
    baseline_dir: Path | None = None,
    scope_paths: Sequence[str] | None = None,
) -> dict[str, int]:
    if not worker_has_git(worker_dir):
        if baseline_dir is not None and scope_paths:
            changed = changed_files_filesystem(worker_dir, baseline_dir, scope_paths)
            insertions, deletions = _line_delta_for_files(worker_dir, baseline_dir, changed)
            return {
                "files_changed": len(changed),
                "insertions": insertions,
                "deletions": deletions,
            }
        return {"files_changed": 0, "insertions": 0, "deletions": 0}
    result = git_run(worker_dir, ["diff", "--numstat", base_ref])
    if result.returncode != 0:
        return {"files_changed": 0, "insertions": 0, "deletions": 0}
    files_changed = 0
    insertions = 0
    deletions = 0
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        files_changed += 1
        if parts[0] != "-":
            insertions += int(parts[0])
        if parts[1] != "-":
            deletions += int(parts[1])
    return {
        "files_changed": files_changed,
        "insertions": insertions,
        "deletions": deletions,
    }


def path_is_allowed(file_path: str, allowed_paths: Sequence[str], denied_paths: Sequence[str]) -> bool:
    normalized = PurePosixPath(file_path.replace("\\", "/"))
    if any(_path_matches(normalized, allowed) for allowed in allowed_paths):
        return True
    for denied in denied_paths:
        if _path_matches(normalized, denied):
            return False
    return False


def _path_matches(file_path: PurePosixPath, rule: str) -> bool:
    rule_path = PurePosixPath(rule.replace("\\", "/"))
    if rule.endswith("/"):
        return file_path.as_posix().startswith(rule_path.as_posix()) or _paths_overlap(Path(rule_path), Path(file_path))
    return (
        file_path == rule_path
        or file_path.as_posix().startswith(f"{rule_path.as_posix()}/")
        or _paths_overlap(Path(rule_path), Path(file_path))
    )


def scope_changed_for_giv(changed: Sequence[str]) -> list[str]:
    """Exclude run-grid handoff artifacts from GIV scope checks."""
    scoped: list[str] = []
    for path in changed:
        if PurePosixPath(path.replace("\\", "/")).name in WORKER_HANDOFF_BASENAMES:
            continue
        scoped.append(path)
    return scoped


def detect_trespasses(changed: Sequence[str], giv: GIV) -> list[str]:
    return sorted(
        path
        for path in scope_changed_for_giv(changed)
        if not path_is_allowed(path, giv.allowed_paths, giv.denied_paths)
    )


def intent_hash(worker_dir: Path) -> str:
    for candidate in (worker_dir / "intent.txt", worker_dir / "WORKER_INTENT.txt"):
        if candidate.exists():
            return hashlib.sha256(candidate.read_bytes()).hexdigest()
    return ""


def output_log_path(worker_dir: Path) -> Path:
    return worker_dir / OUTPUT_LOG_FILENAME


def output_log_blocked(worker_dir: Path, manifest_detail: Mapping[str, Any] | None = None) -> bool:
    status = str((manifest_detail or {}).get("status", "")).lower()
    if status in {"failed", "timed_out", "blocked"}:
        return True
    log_path = output_log_path(worker_dir)
    if not log_path.exists():
        return False
    content = log_path.read_text(encoding="utf-8", errors="replace").strip()
    if not content:
        return False
    tail = "\n".join(content.splitlines()[-20:])
    return any(pattern.search(tail) for pattern in ERROR_TAIL_PATTERNS)


def has_diff(
    worker_dir: Path,
    base_ref: str,
    *,
    baseline_dir: Path | None = None,
    scope_paths: Sequence[str] | None = None,
) -> bool:
    return bool(
        changed_files(
            worker_dir,
            base_ref,
            baseline_dir=baseline_dir,
            scope_paths=scope_paths,
        )
    )


def classify_worker_status(
    worker_dir: Path,
    giv: GIV,
    base_ref: str,
    manifest_detail: Mapping[str, Any] | None = None,
    *,
    baseline_dir: Path | None = None,
) -> str:
    log_path = output_log_path(worker_dir)
    work_unit_path = worker_dir / "WORK_UNIT.md"
    scope_paths = giv.allowed_paths if baseline_dir is not None else None
    diff_exists = has_diff(
        worker_dir,
        base_ref,
        baseline_dir=baseline_dir,
        scope_paths=scope_paths,
    )
    log_exists = log_path.exists()
    log_content = log_path.read_text(encoding="utf-8", errors="replace").strip() if log_exists else ""

    if not log_exists and not diff_exists:
        return "pending"

    if output_log_blocked(worker_dir, manifest_detail):
        return "blocked"

    if diff_exists:
        trespasses = detect_trespasses(
            changed_files(
                worker_dir,
                base_ref,
                baseline_dir=baseline_dir,
                scope_paths=scope_paths,
            ),
            giv,
        )
        if trespasses:
            return "dirty"

    if work_unit_path.exists() and diff_exists and log_content:
        return "completed"

    if diff_exists:
        return "dirty"
    return "pending"


def _agent_output_section(output_log: str) -> str:
    """Return grok agent output only (grid-spawn prepends the scope prompt to output.log)."""
    marker = "=" * 60
    if marker in output_log:
        return output_log.split(marker, 1)[-1]
    return output_log


def scan_denied_command_violations(output_log: str, denied_commands: Sequence[str]) -> list[str]:
    searchable = _agent_output_section(output_log).lower()
    violations: list[str] = []
    for command in denied_commands:
        needle = command.strip().lower()
        if needle and re.search(rf"(?<![a-z0-9_]){re.escape(needle)}(?![a-z0-9_])", searchable):
            violations.append(command)
    return sorted(set(violations))


def unit_owner_map(manifest_details: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    """Map work-unit id → owning worker_id from manifest worker_details."""
    owners: dict[str, str] = {}
    for worker_id, detail in manifest_details.items():
        assigned = detail.get("assigned_work_units", [])
        if not isinstance(assigned, list):
            continue
        for unit_id in assigned:
            owners[str(unit_id)] = worker_id
    return owners


def sibling_dependency_deferral(
    worker_id: str,
    manifest_detail: Mapping[str, Any] | None,
    manifest_details: Mapping[str, Mapping[str, Any]],
    blueprint: Blueprint | None,
) -> tuple[bool, list[str], list[str]]:
    """Return whether pre-merge tests should defer for sibling-owned dependencies."""
    if blueprint is None or manifest_detail is None:
        return False, [], []

    assigned = manifest_detail.get("assigned_work_units", [])
    if not isinstance(assigned, list) or not assigned:
        return False, [], []

    owners = unit_owner_map(manifest_details)
    unit_map = {unit.id: unit for unit in blueprint.work_units}
    sibling_units: list[str] = []
    sibling_workers: list[str] = []

    for unit_id in assigned:
        unit = unit_map.get(str(unit_id))
        if unit is None:
            continue
        for dep_id in unit.depends_on:
            owner = owners.get(str(dep_id))
            if owner and owner != worker_id:
                sibling_units.append(str(dep_id))
                sibling_workers.append(owner)

    if not sibling_units:
        return False, [], []

    return True, sorted(set(sibling_units)), sorted(set(sibling_workers))


def acceptance_checks_for_worker(
    worker_dir: Path,
    manifest_detail: Mapping[str, Any] | None,
    blueprint: Blueprint | None,
    *,
    project_root: Path | None = None,
) -> tuple[str, ...]:
    checks: list[str] = []
    domains: set[str] = set()
    if manifest_detail and blueprint is not None:
        assigned = manifest_detail.get("assigned_work_units", [])
        if isinstance(assigned, list):
            unit_map = {unit.id: unit for unit in blueprint.work_units}
            for unit_id in assigned:
                unit = unit_map.get(str(unit_id))
                if unit is not None:
                    domains.add(str(getattr(unit, "domain", "")).lower())
                    checks.extend(unit.acceptance_checks)
    work_unit = (
        (worker_dir / "WORK_UNIT.md").read_text(encoding="utf-8", errors="replace")
        if (worker_dir / "WORK_UNIT.md").exists()
        else ""
    )
    if "pytest" in work_unit.lower():
        checks.append("pytest")
    if "ruff" in work_unit.lower():
        checks.append("ruff")
    if "vault_linter" in work_unit.lower():
        checks.append("vault_linter")
    normalized = {check.lower() for check in checks if check}
    if "vault" in domains:
        if "pytest" in normalized:
            normalized.discard("pytest")
            normalized.add("vault_linter")
        elif not normalized:
            normalized.add("vault_linter")
    if domains and not domains <= {"code", "vault"}:
        normalized.add("unresolved_domain")
    return tuple(sorted(normalized))


def pytest_targets_for_worker(
    worker_dir: Path,
    allowed_paths: Sequence[str],
    changed: Sequence[str],
) -> list[str]:
    targets: list[str] = []
    for path in changed:
        normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
        if normalized.startswith("tests/") and normalized.endswith(".py"):
            targets.append(normalized)

    for allowed in allowed_paths:
        norm = PurePosixPath(allowed.replace("\\", "/")).as_posix().rstrip("/")
        if norm == "tests":
            continue
        if "billing" in norm or norm.endswith("/api.py") or norm.endswith("preflight.py"):
            targets.append("tests/test_preflight.py")
        elif norm.endswith("handoff.py") or norm.endswith("merge.py"):
            targets.extend(["tests/test_handoff.py", "tests/test_merge.py"])

    existing: list[str] = []
    seen: set[str] = set()
    for target in targets:
        if target in seen:
            continue
        seen.add(target)
        if (worker_dir / target).is_file():
            existing.append(target)
    return existing


def run_acceptance_check(
    project_root: Path,
    command: str,
    *,
    env: Mapping[str, str] | None = None,
    toolchain_root: Path | None = None,
    pytest_targets: Sequence[str] | None = None,
) -> tuple[int, str]:
    run_env = dict(env) if env is not None else os.environ.copy()
    run_env.setdefault("GAIJINN_PROJECT_ROOT", str(project_root.resolve()))
    if toolchain_root is not None:
        prefixes = [
            str(project_root.resolve()),
            str((toolchain_root / "aoc-cli").resolve()),
            str((toolchain_root / "aoc_supervisor").resolve()),
        ]
        existing = run_env.get("PYTHONPATH", "").strip()
        run_env["PYTHONPATH"] = os.pathsep.join([*prefixes, existing] if existing else prefixes)
    if command == "pytest":
        pytest_args = (
            [sys.executable, "-m", "pytest", "-q", *pytest_targets]
            if pytest_targets
            else [sys.executable, "-m", "pytest", "-q"]
        )
        proc = subprocess.run(
            pytest_args,
            cwd=str(project_root),
            env=run_env,
            text=True,
            capture_output=True,
            check=False,
        )
    elif command == "ruff":
        proc = subprocess.run(
            ["ruff", "check", "."],
            cwd=str(project_root),
            env=run_env,
            text=True,
            capture_output=True,
            check=False,
        )
    elif command == "vault_linter":
        vault_root = (toolchain_root or project_root).resolve()
        linter = vault_root / "10_Operations" / "knowledge-linter.py"
        if not linter.is_file():
            return 1, f"vault linter missing at {linter}"
        proc = subprocess.run(
            [
                os.path.abspath(sys.executable),
                str(linter),
                "--check",
                "--worker-gate",
                "--exclude-dirs",
                "pending",
            ],
            cwd=str(vault_root),
            env=run_env,
            text=True,
            capture_output=True,
            check=False,
        )
    else:
        return 0, ""
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output


def invariant_violations(
    changed: Sequence[str],
    giv: GIV,
    *,
    deleted_files: Sequence[str] | None = None,
) -> list[str]:
    violations: list[str] = []
    for path in changed:
        for protected in PROTECTED_INVARIANT_PATHS:
            if (path == protected.rstrip("/") or path.startswith(protected)) and not path_is_allowed(
                path, giv.allowed_paths, giv.denied_paths
            ):
                violations.append(f"modified protected path: {path}")
    for path in deleted_files or ():
        for protected in PROTECTED_INVARIANT_PATHS:
            if (path == protected.rstrip("/") or path.startswith(protected)) and not path_is_allowed(
                path, giv.allowed_paths, giv.denied_paths
            ):
                violations.append(f"deleted protected path: {path}")
    return sorted(set(violations))


def deleted_files(worker_dir: Path, base_ref: str) -> list[str]:
    if not worker_has_git(worker_dir):
        return []
    result = git_run(worker_dir, ["diff", "--name-only", "--diff-filter=D", base_ref])
    if result.returncode != 0:
        return []
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def worker_merge_order(
    worker_ids: Sequence[str],
    manifest_details: Mapping[str, Mapping[str, Any]],
    blueprint: Blueprint | None,
) -> list[str]:
    if blueprint is None or not blueprint.work_units:
        return sorted(worker_ids)

    unit_order = _topo_sort_units(blueprint.work_units)
    unit_rank = {unit_id: index for index, unit_id in enumerate(unit_order)}

    def rank(worker_id: str) -> tuple[int, str]:
        detail = manifest_details.get(worker_id, {})
        assigned = detail.get("assigned_work_units", [])
        if not isinstance(assigned, list) or not assigned:
            return (len(unit_rank) + 1, worker_id)
        scores = [unit_rank.get(str(unit_id), len(unit_rank) + 1) for unit_id in assigned]
        return (min(scores), worker_id)

    return sorted(worker_ids, key=rank)


def _topo_sort_units(work_units: Sequence[Any]) -> list[str]:
    units = {unit.id: unit for unit in work_units}
    incoming = {unit.id: set(unit.depends_on) for unit in work_units}
    order: list[str] = []
    ready = sorted(unit_id for unit_id, deps in incoming.items() if not deps)
    while ready:
        current = ready.pop(0)
        order.append(current)
        for unit_id, deps in incoming.items():
            if current in deps:
                deps.remove(current)
                if not deps and unit_id not in order and unit_id not in ready:
                    ready.append(unit_id)
        ready.sort()
    for unit_id in sorted(units):
        if unit_id not in order:
            order.append(unit_id)
    return order


def load_blueprint_optional(project_root: Path) -> Blueprint | None:
    return _load_blueprint_optional(project_root / BLUEPRINT_JSON_PATH)


def load_worker_giv(worker_dir: Path) -> GIV:
    return _load_giv(worker_dir / "giv.json")


def parse_conflict_files(merge_output: str, project_root: Path) -> list[str]:
    files = re.findall(r"^CONFLICT.*?:\s*(.+)$", merge_output, flags=re.MULTILINE)
    if files:
        return sorted(set(files))
    status = git_run(project_root, ["diff", "--name-only", "--diff-filter=U"])
    if status.returncode == 0 and status.stdout.strip():
        return sorted(line.strip() for line in status.stdout.splitlines() if line.strip())
    return []


def ensure_worker_branch_committed(worker_dir: Path, branch: str | None) -> None:
    if not worker_has_git(worker_dir) or not branch:
        return
    status = git_run(worker_dir, ["status", "--porcelain"])
    if status.returncode != 0 or not status.stdout.strip():
        return
    giv = load_worker_giv(worker_dir)
    staged_any = False
    for line in status.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path in scope_changed_for_giv([path]) and path_is_allowed(path, giv.allowed_paths, giv.denied_paths):
            git_run(worker_dir, ["add", "--", path], check=False)
            staged_any = True
    if not staged_any:
        return
    git_run(
        worker_dir,
        ["commit", "-m", f"gaijinn: worker changes for {branch}"],
        check=False,
    )


def checkout_integration_branch(project_root: Path, base_ref: str, *, dry_run: bool) -> None:
    if dry_run:
        return
    exists = git_run(project_root, ["show-ref", "--verify", f"refs/heads/{INTEGRATION_BRANCH}"])
    if exists.returncode == 0:
        checkout = git_run(project_root, ["checkout", INTEGRATION_BRANCH])
        if checkout.returncode != 0:
            raise MergeError(
                f"failed to checkout {INTEGRATION_BRANCH}",
                cause=(checkout.stderr or checkout.stdout).strip(),
                fix_command=f"git checkout {INTEGRATION_BRANCH}",
            )
        return
    create = git_run(project_root, ["checkout", "-b", INTEGRATION_BRANCH, base_ref])
    if create.returncode != 0:
        raise MergeError(
            f"failed to create integration branch {INTEGRATION_BRANCH}",
            cause=(create.stderr or create.stdout).strip(),
            fix_command=f"git checkout -b {INTEGRATION_BRANCH} {base_ref}",
        )


def merge_worker_branch(
    project_root: Path,
    branch: str,
    *,
    dry_run: bool,
) -> tuple[bool, str | None, list[str]]:
    if dry_run:
        return True, None, []
    merge = git_run(project_root, ["merge", "--no-edit", branch])
    if merge.returncode == 0:
        rev = git_run(project_root, ["rev-parse", "HEAD"])
        commit = rev.stdout.strip() if rev.returncode == 0 else None
        return True, commit, []
    output = (merge.stderr or "") + (merge.stdout or "")
    conflicts = parse_conflict_files(output, project_root)
    git_run(project_root, ["merge", "--abort"], check=False)
    if conflicts:
        raise ConflictError(
            f"merge conflict merging {branch}",
            cause=f"conflicted files: {', '.join(conflicts)}",
            fix_command="resolve conflicts manually then gaijinn merge-grid --strategy sequential",
        )
    raise MergeError(
        f"failed to merge {branch}",
        cause=output.strip() or "git merge returned non-zero",
        fix_command="gaijinn validate-worker && gaijinn merge-grid --strategy sequential",
    )


def revert_last_merge(project_root: Path) -> None:
    git_run(project_root, ["reset", "--hard", "HEAD~1"], check=False)


def run_post_merge_checks(project_root: Path) -> tuple[bool, str]:
    outputs: list[str] = []
    ok = True
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "").strip()
    root_path = str(project_root.resolve())
    env["PYTHONPATH"] = os.pathsep.join([root_path, existing] if existing else [root_path])
    for label, args in (
        ("pytest", [sys.executable, "-m", "pytest", "-q"]),
        ("ruff", ["ruff", "check", "."]),
    ):
        if label == "ruff" and shutil.which(args[0]) is None:
            continue
        proc = subprocess.run(args, cwd=str(project_root), env=env, text=True, capture_output=True, check=False)
        if proc.returncode != 0:
            ok = False
        chunk = (proc.stdout or "") + (proc.stderr or "")
        if chunk.strip():
            outputs.append(f"=== {label} ===\n{chunk.strip()}")
    combined = "\n\n".join(outputs)
    return ok, combined[:4000]


def parse_conflict_files_from_error(error: ConflictError) -> list[str]:
    cause = error.cause or ""
    if "conflicted files:" in cause:
        files = cause.split("conflicted files:", 1)[1].strip()
        return sorted(item.strip() for item in files.split(",") if item.strip())
    return []


def load_merge_report(project_root: Path) -> dict[str, Any] | None:
    report_path = project_root / REPORT_PATH
    if not report_path.exists():
        return None
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def merge_worker_breakdown(project_root: Path) -> list[dict[str, Any]]:
    """Summarize per-worker validation and merge outcomes for terminal display."""
    validated: dict[str, Any] = {}
    validated_path = project_root / VALIDATED_PATH
    if validated_path.exists():
        try:
            loaded = json.loads(validated_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                validated = loaded
        except json.JSONDecodeError:
            pass

    report_workers: dict[str, Any] = {}
    report = load_merge_report(project_root)
    if report:
        workers = report.get("workers", {})
        if isinstance(workers, dict):
            report_workers = workers

    worker_ids = sorted(set(validated) | set(report_workers))
    breakdown: list[dict[str, Any]] = []
    for worker_id in worker_ids:
        validation = validated.get(worker_id, {})
        merge_result = report_workers.get(worker_id, {})
        gates = validation.get("gates", {}) if isinstance(validation, Mapping) else {}
        failed_gates = [
            name for name, gate in gates.items() if isinstance(gate, Mapping) and gate.get("passed") is False
        ]
        entry: dict[str, Any] = {
            "worker_id": worker_id,
            "validated": bool(validation),
            "passed": bool(validation.get("passed")) if isinstance(validation, Mapping) else None,
            "failed_gates": failed_gates,
            "merge_status": str(merge_result.get("status", "")) if isinstance(merge_result, Mapping) else "",
        }
        if isinstance(merge_result, Mapping) and merge_result.get("conflict_files"):
            entry["conflict_files"] = list(merge_result.get("conflict_files", []))
        breakdown.append(entry)
    return breakdown


def merge_pipeline_status(project_root: Path) -> dict[str, Any]:
    collected_path = project_root / COLLECTED_PATH
    validated_path = project_root / VALIDATED_PATH
    report_path = project_root / REPORT_PATH

    collected_count = 0
    validated_count = 0
    validated_passed = 0
    merged = 0
    already_merged = 0
    blocked = 0
    conflicted = 0
    phase = "idle"
    report_exists = report_path.exists()

    if collected_path.exists():
        try:
            collected = json.loads(collected_path.read_text(encoding="utf-8"))
            workers = collected.get("workers", {})
            if isinstance(workers, dict):
                collected_count = len(workers)
        except json.JSONDecodeError:
            pass
        phase = "validating"

    if validated_path.exists():
        try:
            validated = json.loads(validated_path.read_text(encoding="utf-8"))
            if isinstance(validated, dict):
                validated_count = len(validated)
                validated_passed = sum(
                    1 for item in validated.values() if isinstance(item, Mapping) and item.get("passed") is True
                )
        except json.JSONDecodeError:
            pass
        phase = "merging"

    if report_exists:
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            summary = report.get("summary", {})
            if isinstance(summary, Mapping):
                merged = int(summary.get("merged", 0) or 0)
                already_merged = int(summary.get("already_merged", 0) or 0)
                blocked = int(summary.get("blocked", 0) or 0)
                conflicted = int(summary.get("conflicted", 0) or 0)
            phase = "completed"
        except json.JSONDecodeError:
            phase = "merging"

    payload: dict[str, Any] = {
        "phase": phase,
        "collected": collected_count,
        "validated": validated_count,
        "validated_passed": validated_passed,
        "merged": merged,
        "already_merged": already_merged,
        "blocked": blocked,
        "conflicted": conflicted,
    }
    if report_exists:
        payload["report_path"] = REPORT_PATH.as_posix()
    workers = merge_worker_breakdown(project_root)
    if workers:
        payload["workers"] = workers
    governance = load_merge_governance(project_root)
    if governance is not None:
        payload["structural_score"] = governance.get("structural_score")
        payload["governance_path"] = GOVERNANCE_PATH.as_posix()
    return payload


@dataclass(frozen=True)
class StructuralScore:
    """Unified post-sprint merge governance score (maps test_merge_integrity invariants)."""

    convergence: float
    conflict_free: bool
    handoff_isolation: bool
    merge_order_valid: bool
    validation_pass_rate: float
    merged_workers: int
    already_merged_workers: int
    blocked_workers: int
    conflicted_workers: int
    atomic_weld_units: int
    transaction_bus_synchronized: bool
    dry_run: bool
    merge_order: tuple[str, ...] = field(default_factory=tuple)
    ledger_entries_written: int = 0
    merge_latency_ms: int | None = None
    invariants: dict[str, bool] = field(default_factory=dict)
    scored_at: str = ""
    schema_version: int = GOVERNANCE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scored_at": self.scored_at or utc_now(),
            "structural_score": {
                "convergence": round(self.convergence, 4),
                "conflict_free": self.conflict_free,
                "handoff_isolation": self.handoff_isolation,
                "merge_order_valid": self.merge_order_valid,
                "validation_pass_rate": round(self.validation_pass_rate, 4),
                "merged_workers": self.merged_workers,
                "already_merged_workers": self.already_merged_workers,
                "blocked_workers": self.blocked_workers,
                "conflicted_workers": self.conflicted_workers,
                "ledger_entries_written": self.ledger_entries_written,
                "atomic_weld_units": self.atomic_weld_units,
                "transaction_bus_synchronized": self.transaction_bus_synchronized,
                "dry_run": self.dry_run,
                "merge_order": list(self.merge_order),
                "merge_latency_ms": self.merge_latency_ms,
                "invariants": dict(sorted(self.invariants.items())),
            },
        }


def _load_merge_artifact(project_root: Path, rel_path: Path) -> dict[str, Any] | None:
    path = project_root / rel_path
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _parse_utc_timestamp(value: str) -> datetime | None:
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _count_atomic_weld_units(blueprint: Blueprint | None) -> int:
    if blueprint is None:
        return 0
    count = 0
    for unit in blueprint.work_units:
        title = unit.title.lower()
        if "atomic block" in title or "coupling review" in title:
            count += 1
    return count


def _merge_order_is_valid(merged_order: Sequence[str], expected_order: Sequence[str]) -> bool:
    if not merged_order:
        return False
    rank = {worker_id: index for index, worker_id in enumerate(expected_order)}
    if any(worker_id not in rank for worker_id in merged_order):
        return False
    indices = [rank[worker_id] for worker_id in merged_order]
    return indices == sorted(indices)


def _transaction_bus_synchronized(project_root: Path, validated: Mapping[str, Any]) -> bool:
    queue = _load_merge_artifact(project_root, HANDOFF_QUEUE_PATH) or {}
    if "transaction_bus_synchronized" in queue:
        return bool(queue["transaction_bus_synchronized"])
    for entry in validated.values():
        if not isinstance(entry, Mapping):
            continue
        integrity = entry.get("handoff_integrity", {})
        if isinstance(integrity, Mapping) and "transaction_bus_synchronized" in integrity:
            return bool(integrity["transaction_bus_synchronized"])
    return True


def _handoff_isolation_from_validated(validated: Mapping[str, Any], *, dry_run: bool = False) -> bool:
    if dry_run:
        return True
    for entry in validated.values():
        if not isinstance(entry, Mapping):
            return False
        gates = entry.get("gates", {})
        if not isinstance(gates, Mapping):
            return False
        path_gate = gates.get("path_allowlist", {})
        if isinstance(path_gate, Mapping) and path_gate.get("passed") is False:
            return False
    return True


def _convergence_scoring_invariants(invariants: Mapping[str, bool], *, dry_run: bool) -> dict[str, bool]:
    """Invariants that count toward convergence (mock dry-run excludes not_dry_run)."""
    excluded = {"merge.not_dry_run"} if dry_run else set()
    return {key: value for key, value in invariants.items() if key not in excluded}


def compute_merge_structural_score(project_root: Path) -> StructuralScore:
    """Synthesize post-sprint artifacts into a unified governance score (idempotent)."""
    collected = _load_merge_artifact(project_root, COLLECTED_PATH) or {}
    validated = _load_merge_artifact(project_root, VALIDATED_PATH) or {}
    report = _load_merge_artifact(project_root, REPORT_PATH) or {}

    summary = report.get("summary", {}) if isinstance(report.get("summary"), Mapping) else {}
    merged_workers = int(summary.get("merged", 0) or 0)
    already_merged_workers = int(summary.get("already_merged", 0) or 0)
    blocked_workers = int(summary.get("blocked", 0) or 0)
    conflicted_workers = int(summary.get("conflicted", 0) or 0)
    ledger_entries_written = int(summary.get("ledger_entries_written", 0) or 0)
    dry_run = bool(report.get("dry_run"))

    workers_path = project_root / WORKERS_DIR
    manifest = load_worker_manifest(workers_path) if (workers_path / "manifest.json").exists() else {}
    details = worker_details_map(manifest)
    blueprint = load_blueprint_optional(project_root)

    passing = sorted(worker_id for worker_id, entry in validated.items() if entry.get("passed") is True or dry_run)
    expected_order = tuple(worker_merge_order(passing, details, blueprint))

    report_workers = report.get("workers", {})
    merged_order: list[str] = []
    recorded_order = report.get("merge_order")
    if isinstance(recorded_order, list):
        merged_order = [str(worker_id) for worker_id in recorded_order]
    elif isinstance(report_workers, Mapping):
        merged_order = [
            worker_id
            for worker_id, entry in report_workers.items()
            if isinstance(entry, Mapping) and entry.get("status") == "merged"
        ]

    validated_total = len(validated)
    validated_passed = len(passing)
    validation_pass_rate = (validated_passed / validated_total) if validated_total else 0.0

    handoff_isolation = _handoff_isolation_from_validated(validated, dry_run=dry_run)
    transaction_bus_synchronized = _transaction_bus_synchronized(project_root, validated)
    merge_order_valid = _merge_order_is_valid(merged_order, expected_order)
    conflict_free = conflicted_workers == 0
    not_blocked = blocked_workers == 0
    phase_completed = bool(report)
    real_merge = not dry_run

    invariants = {
        "merge.phase_completed": phase_completed,
        "merge.no_conflicted": conflict_free,
        "merge.no_blocked": not_blocked,
        "merge.handoff_isolation": handoff_isolation,
        "merge.transaction_bus_synchronized": transaction_bus_synchronized,
        "merge.order_valid": merge_order_valid,
        "merge.not_dry_run": real_merge,
        "merge.validation_pass_rate_full": validation_pass_rate == 1.0 if validated_total else False,
        "merge.merged_work": (merged_workers + already_merged_workers) >= 1
        or int(summary.get("backlog_pre_sprint", 1) or 0) == 0,
    }
    scoring = _convergence_scoring_invariants(invariants, dry_run=dry_run)
    passed = sum(1 for ok in scoring.values() if ok)
    convergence = passed / len(scoring) if scoring else 0.0

    collected_at = _parse_utc_timestamp(str(collected.get("collected_at", "")))
    completed_at = _parse_utc_timestamp(str(report.get("completed_at", "")))
    merge_latency_ms: int | None = None
    if collected_at is not None and completed_at is not None:
        merge_latency_ms = max(0, int((completed_at - collected_at).total_seconds() * 1000))

    return StructuralScore(
        convergence=convergence,
        conflict_free=conflict_free,
        handoff_isolation=handoff_isolation,
        merge_order_valid=merge_order_valid,
        validation_pass_rate=validation_pass_rate,
        merged_workers=merged_workers,
        already_merged_workers=already_merged_workers,
        blocked_workers=blocked_workers,
        conflicted_workers=conflicted_workers,
        atomic_weld_units=_count_atomic_weld_units(blueprint),
        transaction_bus_synchronized=transaction_bus_synchronized,
        dry_run=dry_run,
        merge_order=tuple(merged_order),
        ledger_entries_written=ledger_entries_written,
        merge_latency_ms=merge_latency_ms,
        invariants=invariants,
        scored_at=utc_now(),
    )


def write_merge_governance(project_root: Path, score: StructuralScore | None = None) -> Path:
    """Write governance.json from a fresh or supplied structural score."""
    payload = (score or compute_merge_structural_score(project_root)).to_dict()
    path = project_root / GOVERNANCE_PATH
    write_merge_json(path, payload)
    return path


def load_merge_governance(project_root: Path) -> dict[str, Any] | None:
    return _load_merge_artifact(project_root, GOVERNANCE_PATH)


def record_merge_governance_history(project_root: Path, score: StructuralScore) -> None:
    """Attach latest structural score to metrics_manifest for rolling agent context."""
    metrics_path = project_root / GAIJINN_DIR / "metrics_manifest.json"
    if not metrics_path.exists():
        return
    try:
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if not isinstance(payload, dict):
        return

    history = payload.setdefault("merge_governance", {"schema_version": GOVERNANCE_SCHEMA_VERSION, "runs": []})
    if not isinstance(history, dict):
        return
    runs = history.setdefault("runs", [])
    if not isinstance(runs, list):
        return
    entry = score.to_dict()
    runs.append(entry)
    history["latest"] = entry
    write_merge_json(metrics_path, payload)


def format_structural_score_council_message(
    score: StructuralScore,
    *,
    session_id: str = "",
) -> str:
    pct = int(round(score.convergence * 100))
    prefix = f"Session {session_id} — " if session_id else ""
    parts = [
        f"{prefix}Structural score {score.convergence:.2f} ({pct}%)",
        f"{score.merged_workers} merged",
    ]
    if score.conflicted_workers:
        parts.append(f"{score.conflicted_workers} conflicted")
    if score.blocked_workers:
        parts.append(f"{score.blocked_workers} blocked")
    if score.merge_order:
        parts.append(f"order {'→'.join(score.merge_order)}")
    if score.merge_latency_ms is not None:
        parts.append(f"latency {score.merge_latency_ms}ms")
    if score.atomic_weld_units:
        parts.append(f"{score.atomic_weld_units} atomic weld unit(s)")
    return " — ".join(parts)
