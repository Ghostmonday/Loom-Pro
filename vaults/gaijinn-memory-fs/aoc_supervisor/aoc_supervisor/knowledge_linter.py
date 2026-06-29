"""Platform-level vault knowledge linter — reusable lint engine for any Obsidian vault.

GAIJINN BLUEPRINT — Knowledge linter (worker-015)
---------------------------------------------------
Layer: Cross-cutting / vault semantic integrity
Status: LEARN SPRINT research artifact
Spec: .gaijinn/reviews/worker-015-knowledge-linter.md

Defines the LintReport data model and linting rules for validating Obsidian
vault well-formedness. Designed to be called from:
  - The promotion pipeline (Gate 1 variant: vault linter pass)
  - Gaijinn validate-worker as a pre-merge check
  - CLI: python -m aoc_supervisor.knowledge_linter --vault <path>

Integration points:
  - aoc_supervisor/vault_deploy.py — VaultDeployment can pass vault_path into lint()
  - aoc_supervisor/workflow_evaluator.py — evaluate_vault_lint() gate
  - scripts/dev/ — vault-lint-smoke.sh wrapper for CI
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

# ── Regexes ──────────────────────────────────────────────────────────────────

_WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]|]+))?\]\]")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.+?)\n---", re.DOTALL)
_OBSIDIAN_VAULT_LINK_RE = re.compile(r"\[\[([a-zA-Z_/.-]+):(.+?)\]\]")


# ── Violation model ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class LintViolation:
    """A single lint violation with file path, rule id, and human-readable message."""

    rule_id: str
    """Short identifier for the rule (e.g. 'frontmatter-missing', 'wiki-link-broken')."""

    file_path: str
    """Relative path of the violating file within the vault."""

    message: str
    """Human-readable description of the violation."""

    severity: str = "error"
    """Severity level: 'error' or 'warning'."""


@dataclass(frozen=True)
class LintReport:
    """Complete lint report for a single vault scan.

    Contains all violations found, plus summary statistics for pipeline use.
    """

    vault_name: str
    """Vault identifier (e.g. 'affairs', 'filesystem', 'gaijinn')."""

    vault_path: str
    """Resolved absolute path to the vault directory scanned."""

    violations: tuple[LintViolation, ...] = field(default_factory=tuple)
    """All violations found during the scan, ordered by file then rule."""

    total_files: int = 0
    """Number of markdown files scanned."""

    # ── Computed properties ─────────────────────────────────────────────────

    @property
    def passed(self) -> bool:
        """True if no errors (warnings are non-blocking)."""
        return all(v.severity != "error" for v in self.violations)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")

    @property
    def files_with_violations(self) -> list[str]:
        """Sorted list of unique filenames that have at least one violation."""
        return sorted({v.file_path for v in self.violations})

    # ── Serialisation ───────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "vault_name": self.vault_name,
            "vault_path": self.vault_path,
            "total_files": self.total_files,
            "passed": self.passed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "files_with_violations": self.files_with_violations,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "file_path": v.file_path,
                    "message": v.message,
                    "severity": v.severity,
                }
                for v in self.violations
            ],
        }

    def print_report(self, file: IO[str] | None = None) -> None:
        """Print a human-readable lint report to stdout (or a given file handle)."""
        out = file or __import__("sys").stdout
        status = "PASS" if self.passed else "FAIL"
        out.write(f"=== VAULT LINT: {self.vault_name} [{status}] ===\n")
        out.write(f"  Files scanned: {self.total_files}\n")
        out.write(f"  Errors: {self.error_count}  Warnings: {self.warning_count}\n")
        if self.violations:
            out.write("\n  Violations:\n")
            for v in self.violations:
                marker = "✗" if v.severity == "error" else "⚠"
                out.write(f"    {marker} [{v.rule_id}] {v.file_path}: {v.message}\n")


# ── Lint function ────────────────────────────────────────────────────────────


def lint_vault(
    vault_path: str | Path,
    vault_name: str | None = None,
    *,
    require_frontmatter: bool = True,
    check_wiki_links: bool = True,
    detect_orphans: bool = True,
    check_file_naming: bool = True,
    check_empty_notes: bool = True,
    allowed_statuses: frozenset[str] | None = None,
    required_metadata_keys: frozenset[str] | None = None,
) -> LintReport:
    """Lint an Obsidian vault directory for well-formedness.

    Args:
        vault_path: Path to the Obsidian vault directory.
        vault_name: Vault identifier. Defaults to directory basename.
        require_frontmatter: Check each .md file has YAML frontmatter.
        check_wiki_links: Validate [[wiki-links]] resolve within the vault.
        detect_orphans: Flag notes not linked from any other note.
        check_file_naming: Flag files with names that break Obsidian conventions.
        check_empty_notes: Flag notes with no content beyond frontmatter.
        allowed_statuses: If given, validate 'status' frontmatter values.
        required_metadata_keys: If given, validate frontmatter contains these keys.

    Returns:
        A LintReport with all violations found.
    """
    vault = Path(vault_path).resolve()
    name = vault_name or vault.name

    if not vault.is_dir():
        return LintReport(
            vault_name=name,
            vault_path=str(vault),
            violations=(LintViolation("vault-not-found", "", f"vault directory not found: {vault}"),),
        )

    markdown_files: list[Path] = sorted(vault.glob("**/*.md"))
    # Exclude hidden directories
    markdown_files = [p for p in markdown_files if not any(part.startswith(".") for part in p.relative_to(vault).parts)]

    violations: list[LintViolation] = []
    file_data: dict[str, str] = {}  # rel_path -> full text
    link_graph: dict[str, set[str]] = {}  # rel_path -> set of wiki-link targets

    for md_file in markdown_files:
        rel_path = str(md_file.relative_to(vault))
        text = md_file.read_text(encoding="utf-8")
        file_data[rel_path] = text

        # File naming check
        if check_file_naming:
            violations.extend(_check_file_naming(rel_path, md_file))

        # Frontmatter check
        fm = _parse_frontmatter(text)

        if require_frontmatter:
            if fm is None:
                violations.append(LintViolation("frontmatter-missing", rel_path, "no YAML frontmatter found"))
            else:
                violations.extend(_check_frontmatter_keys(rel_path, fm, required_metadata_keys, allowed_statuses))

        # Empty note check
        if check_empty_notes and _is_empty_note(text):
            violations.append(LintViolation("empty-note", rel_path, "note has no content beyond frontmatter"))

        # Extract wiki-links
        if check_wiki_links:
            targets = {match[0] for match in _WIKI_LINK_RE.findall(text)}
            link_graph[rel_path] = targets

    # Wiki-link resolution check after building the full index
    if check_wiki_links and file_data:
        all_files = set(file_data.keys())
        all_stems = {Path(k).stem: k for k in all_files}

        for source_file, targets in link_graph.items():
            for target in targets:
                # Skip cross-vault links (vault:Target pattern)
                if _OBSIDIAN_VAULT_LINK_RE.match(f"[[{target}]]"):
                    violations.append(
                        LintViolation(
                            "cross-vault-link",
                            source_file,
                            f"cross-vault link to [[{target}]] — resolution requires vault registry",
                            severity="warning",
                        )
                    )
                    continue

                # Try exact path match first, then stem match
                if target in all_files:
                    continue
                # Remove .md extension and try again
                target_no_ext = target.removesuffix(".md")
                if target_no_ext in all_stems:
                    continue
                # Check with .md appended
                target_with_ext = target + ".md"
                if target_with_ext in all_files:
                    continue
                # Check without extension as a stem
                if target in all_stems or target in (Path(k).stem for k in all_files):
                    continue

                violations.append(
                    LintViolation(
                        "wiki-link-broken",
                        source_file,
                        f"broken [[{target}]] — no matching file in vault",
                    )
                )

    # Orphan detection
    if detect_orphans and file_data:
        linked_from: dict[str, int] = {}
        for targets in link_graph.values():
            for t in targets:
                # Map target to a file path
                if t in linked_from:
                    linked_from[t] += 1
                else:
                    linked_from[t] = 1

        orphans: list[str] = []
        for rel_path in file_data:
            # Index.md and AGENTS.md are commonly unlinked entry points — exclude
            basename = Path(rel_path).name
            if basename in ("Index.md", "AGENTS.md"):
                continue
            # Check if any wiki-link points to this file
            stem = Path(rel_path).stem
            if stem not in linked_from and rel_path not in linked_from:
                is_index = rel_path.endswith("/Index.md")
                if not is_index:
                    orphans.append(rel_path)

        for orphan in sorted(orphans):
            violations.append(LintViolation("orphan-note", orphan, "no incoming wiki-links from other notes"))

    return LintReport(
        vault_name=name,
        vault_path=str(vault),
        violations=tuple(sorted(violations, key=lambda v: (v.file_path, v.rule_id))),
        total_files=len(markdown_files),
    )


# ── Internal helpers ─────────────────────────────────────────────────────────


def _parse_frontmatter(text: str) -> dict[str, str] | None:
    """Extract YAML frontmatter as a dict of key-value strings.

    Returns None if no frontmatter block is found. Only handles simple
    scalar YAML values — does NOT parse nested objects or lists.
    """
    match = _FRONTMATTER_RE.search(text)
    if not match:
        return None

    block = match.group(1)
    result: dict[str, str] = {}
    for line in block.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _check_file_naming(rel_path: str, path: Path) -> list[LintViolation]:
    """Check file naming conventions."""
    result: list[LintViolation] = []
    name = path.name
    if " " in name:
        result.append(LintViolation("file-name-spaces", rel_path, f"filename contains spaces: {name}", "warning"))
    if not name.endswith(".md"):
        result.append(LintViolation("file-name-not-markdown", rel_path, f"file is not .md: {name}"))
    if any(c in name for c in "#?%*|\\<>"):
        result.append(LintViolation("file-name-illegal-chars", rel_path, f"filename has illegal characters: {name}"))
    return result


def _check_frontmatter_keys(
    rel_path: str,
    fm: dict[str, str],
    required_keys: frozenset[str] | None,
    allowed_statuses: frozenset[str] | None,
) -> list[LintViolation]:
    """Check frontmatter for required keys and valid status values."""
    result: list[LintViolation] = []

    if required_keys:
        for key in required_keys:
            if key not in fm or not fm[key]:
                result.append(
                    LintViolation(
                        "frontmatter-missing-key",
                        rel_path,
                        f"missing or empty required frontmatter key: {key}",
                    )
                )

    if allowed_statuses and "status" in fm:
        if fm["status"] not in allowed_statuses:
            result.append(
                LintViolation(
                    "frontmatter-invalid-status",
                    rel_path,
                    f"invalid status '{fm['status']}' — allowed: {', '.join(sorted(allowed_statuses))}",
                )
            )

    return result


def _is_empty_note(text: str) -> bool:
    """Check if a note has no meaningful content beyond its frontmatter."""
    body = _FRONTMATTER_RE.sub("", text).strip()
    return not body or body == ""


# ── CLI entry point ──────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: lint a vault directory and print the report."""
    import argparse

    parser = argparse.ArgumentParser(description="Lint an Obsidian vault for well-formedness")
    parser.add_argument("--vault", type=str, required=True, help="Path to the Obsidian vault directory")
    parser.add_argument("--name", type=str, default=None, help="Vault identifier (default: directory basename)")
    parser.add_argument("--require-frontmatter", action="store_true", default=True)
    parser.add_argument("--no-frontmatter", dest="require_frontmatter", action="store_false")
    parser.add_argument("--no-wiki-links", dest="check_wiki_links", action="store_false")
    parser.add_argument("--no-orphans", dest="detect_orphans", action="store_false")
    parser.add_argument("--json", action="store_true", help="Output JSON report instead of human-readable")

    args = parser.parse_args(argv)

    report = lint_vault(
        args.vault,
        vault_name=args.name,
        require_frontmatter=args.require_frontmatter,
        check_wiki_links=args.check_wiki_links,
        detect_orphans=args.detect_orphans,
    )

    if args.json:
        import json

        json.dump(report.to_dict(), __import__("sys").stdout, indent=2)
        print()
    else:
        report.print_report()

    return 0 if report.passed else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
