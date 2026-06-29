"""Tests for platform-level vault knowledge linter — worker-015.

GAIJINN BLUEPRINT — test suite for knowledge_linter.py
--------------------------------------------------------
Layer: Test infrastructure
Status: LEARN SPRINT research artifact
Spec: .gaijinn/reviews/worker-015-knowledge-linter.md
"""

from __future__ import annotations

from pathlib import Path

from aoc_supervisor.knowledge_linter import (
    LintReport,
    LintViolation,
    lint_vault,
)


class TestLintViolation:
    """LintViolation is a frozen dataclass — basic construction."""

    def test_construction(self) -> None:
        v = LintViolation(rule_id="frontmatter-missing", file_path="Index.md", message="no frontmatter")
        assert v.rule_id == "frontmatter-missing"
        assert v.file_path == "Index.md"
        assert v.message == "no frontmatter"
        assert v.severity == "error"

    def test_custom_severity(self) -> None:
        v = LintViolation("file-name-spaces", "test.md", "spaces in name", severity="warning")
        assert v.severity == "warning"
        assert v.rule_id == "file-name-spaces"


class TestLintReport:
    """LintReport — construction, computed properties, serialisation."""

    def test_clean_report(self) -> None:
        report = LintReport(vault_name="clean", vault_path="/vault", total_files=3)
        assert report.passed
        assert report.error_count == 0
        assert report.warning_count == 0
        assert report.files_with_violations == []
        assert report.to_dict()["passed"] is True

    def test_report_with_errors(self) -> None:
        report = LintReport(
            vault_name="messy",
            vault_path="/vault",
            violations=(
                LintViolation("frontmatter-missing", "Index.md", "no fm", "error"),
                LintViolation("frontmatter-missing", "Gov.md", "no fm", "error"),
            ),
            total_files=5,
        )
        assert not report.passed
        assert report.error_count == 2
        assert report.warning_count == 0
        assert report.files_with_violations == ["Gov.md", "Index.md"]

    def test_report_with_warnings_only(self) -> None:
        report = LintReport(
            vault_name="warny",
            vault_path="/vault",
            violations=(LintViolation("file-name-spaces", "My Note.md", "spaces", "warning"),),
            total_files=1,
        )
        assert report.passed  # warnings don't fail
        assert report.error_count == 0
        assert report.warning_count == 1

    def test_to_dict_structure(self) -> None:
        report = LintReport(
            vault_name="test",
            vault_path="/vault",
            violations=(LintViolation("orphan-note", "Lonely.md", "no incoming links"),),
            total_files=10,
        )
        d = report.to_dict()
        assert d["vault_name"] == "test"
        assert d["passed"] is False
        assert len(d["violations"]) == 1
        assert d["violations"][0]["rule_id"] == "orphan-note"

    def test_print_report_clean(self, capsys) -> None:
        report = LintReport(vault_name="clean", vault_path="/v", total_files=2)
        report.print_report()
        captured = capsys.readouterr()
        assert "PASS" in captured.out
        assert "Errors: 0" in captured.out

    def test_print_report_fail(self, capsys) -> None:
        report = LintReport(
            vault_name="bad",
            vault_path="/v",
            violations=(LintViolation("empty-note", "Empty.md", "no content"),),
            total_files=1,
        )
        report.print_report()
        captured = capsys.readouterr()
        assert "FAIL" in captured.out
        assert "✗ [empty-note]" in captured.out


class TestLintVaultFrontmatter:
    """lint_vault — frontmatter checks."""

    def test_no_frontmatter_detected(self, tmp_path: Path) -> None:
        vault = tmp_path / "test-vault"
        vault.mkdir()
        (vault / "Index.md").write_text("# Just a heading\n\nSome content.\n", encoding="utf-8")

        report = lint_vault(vault, vault_name="test")
        assert not report.passed
        assert any(v.rule_id == "frontmatter-missing" for v in report.violations)

    def test_with_frontmatter_passes(self, tmp_path: Path) -> None:
        vault = tmp_path / "clean-vault"
        vault.mkdir()
        (vault / "Index.md").write_text("---\nid: idx\nstatus: active\n---\n# Index\n\nContent.\n", encoding="utf-8")

        report = lint_vault(vault, vault_name="clean")
        # Only expects clean, but may flag other checks — verify no frontmatter errors
        assert not any(v.rule_id == "frontmatter-missing" for v in report.violations)

    def test_required_metadata_keys(self, tmp_path: Path) -> None:
        vault = tmp_path / "req-vault"
        vault.mkdir()
        (vault / "Gov.md").write_text("---\nid: gov\ntype: governance\n---\n# Gov\n\nRules.\n", encoding="utf-8")

        required = frozenset({"id", "type", "scope"})
        report = lint_vault(vault, required_metadata_keys=required)
        assert not report.passed
        keys_found = {v.rule_id for v in report.violations}
        assert "frontmatter-missing-key" in keys_found

    def test_invalid_status(self, tmp_path: Path) -> None:
        vault = tmp_path / "status-check"
        vault.mkdir()
        (vault / "Note.md").write_text("---\nid: n1\nstatus: unknown_status\n---\n# Note\n\nBody.\n", encoding="utf-8")

        allowed = frozenset({"active", "draft", "immutable"})
        report = lint_vault(vault, allowed_statuses=allowed)
        assert not report.passed
        assert any(v.rule_id == "frontmatter-invalid-status" for v in report.violations)


class TestLintVaultWikiLinks:
    """lint_vault — wiki-link resolution checks."""

    def test_valid_wiki_links(self, tmp_path: Path) -> None:
        vault = tmp_path / "linked-vault"
        vault.mkdir()
        (vault / "Index.md").write_text("See [[Note A]] and [[Note B]].\n", encoding="utf-8")
        (vault / "Note A.md").write_text("# Note A\nContent.\n", encoding="utf-8")
        (vault / "Note B.md").write_text("# Note B\nContent.\n", encoding="utf-8")

        report = lint_vault(vault, vault_name="links")
        assert not any(v.rule_id == "wiki-link-broken" for v in report.violations)

    def test_broken_wiki_link(self, tmp_path: Path) -> None:
        vault = tmp_path / "broken-links"
        vault.mkdir()
        (vault / "Index.md").write_text("See [[Missing Note]].\n", encoding="utf-8")

        report = lint_vault(vault, vault_name="broken")
        assert any(v.rule_id == "wiki-link-broken" for v in report.violations)

    def test_wiki_link_with_extension(self, tmp_path: Path) -> None:
        vault = tmp_path / "ext-links"
        vault.mkdir()
        (vault / "Index.md").write_text("See [[Target.md]]\n", encoding="utf-8")
        (vault / "Target.md").write_text("# Target\n\nPresent.\n", encoding="utf-8")

        report = lint_vault(vault)
        assert not any(v.rule_id == "wiki-link-broken" for v in report.violations)


class TestLintVaultOrphans:
    """lint_vault — orphan detection."""

    def test_orphan_note_detected(self, tmp_path: Path) -> None:
        vault = tmp_path / "orphan-vault"
        vault.mkdir()
        (vault / "Index.md").write_text("---\nid: idx\n---\n# Index\nLinked.\n", encoding="utf-8")
        (vault / "Linked Note.md").write_text("---\nid: ln\n---\n# Linked\n[[Index]]\n", encoding="utf-8")
        (vault / "Orphan.md").write_text("---\nid: orp\n---\n# Orphan\nNo one links to me.\n", encoding="utf-8")

        report = lint_vault(vault)
        assert any(v.rule_id == "orphan-note" for v in report.violations)
        orphan_violations = [v for v in report.violations if v.rule_id == "orphan-note"]
        assert any("Orphan.md" in v.file_path for v in orphan_violations)

    def test_no_orphans_when_all_linked(self, tmp_path: Path) -> None:
        vault = tmp_path / "well-linked"
        vault.mkdir()
        (vault / "Index.md").write_text("See [[Note A]] and [[Note B]].\n", encoding="utf-8")
        (vault / "Note A.md").write_text("Links to [[Note B]].\n", encoding="utf-8")
        (vault / "Note B.md").write_text("Links to [[Note A]].\n", encoding="utf-8")

        report = lint_vault(vault)
        assert not any(v.rule_id == "orphan-note" for v in report.violations)


class TestLintVaultFileNaming:
    """lint_vault — file naming checks."""

    def test_spaces_in_filename_warns(self, tmp_path: Path) -> None:
        vault = tmp_path / "naming-vault"
        vault.mkdir()
        (vault / "My Note.md").write_text("content\n", encoding="utf-8")

        report = lint_vault(vault)
        assert any(v.rule_id == "file-name-spaces" for v in report.violations)
        space_v = [v for v in report.violations if v.rule_id == "file-name-spaces"]
        assert space_v[0].severity == "warning"

    def test_clean_filenames(self, tmp_path: Path) -> None:
        vault = tmp_path / "clean-names"
        vault.mkdir()
        (vault / "Index.md").write_text("content\n", encoding="utf-8")
        (vault / "Note-A.md").write_text("content\n", encoding="utf-8")
        (vault / "2024-06-17-Log.md").write_text("content\n", encoding="utf-8")

        report = lint_vault(vault)
        assert not any(v.rule_id.startswith("file-name-") for v in report.violations)


class TestLintVaultEmptyNotes:
    """lint_vault — empty note detection."""

    def test_empty_note_detected(self, tmp_path: Path) -> None:
        vault = tmp_path / "empty-vault"
        vault.mkdir()
        (vault / "Empty.md").write_text("---\nid: empty\n---\n", encoding="utf-8")

        report = lint_vault(vault)
        assert any(v.rule_id == "empty-note" for v in report.violations)

    def test_note_with_content_not_empty(self, tmp_path: Path) -> None:
        vault = tmp_path / "content-vault"
        vault.mkdir()
        (vault / "Full.md").write_text("---\nid: full\n---\n# Real content\n\nLots of text.\n", encoding="utf-8")

        report = lint_vault(vault)
        assert not any(v.rule_id == "empty-note" for v in report.violations)


class TestLintVaultCrossVaultLinks:
    """lint_vault — cross-vault link detection."""

    def test_cross_vault_link_warns(self, tmp_path: Path) -> None:
        vault = tmp_path / "cross-vault"
        vault.mkdir()
        (vault / "Index.md").write_text("See [[affairs:Calendar]].\n", encoding="utf-8")

        report = lint_vault(vault)
        assert any(v.rule_id == "cross-vault-link" for v in report.violations)
        cross_v = [v for v in report.violations if v.rule_id == "cross-vault-link"]
        assert cross_v[0].severity == "warning"


class TestLintVaultExcludedPaths:
    """lint_vault — hidden directories are skipped."""

    def test_skips_hidden_dirs(self, tmp_path: Path) -> None:
        vault = tmp_path / "hidden-check"
        vault.mkdir()
        (vault / "Index.md").write_text("content\n", encoding="utf-8")
        hidden = vault / ".hidden"
        hidden.mkdir()
        (hidden / "Secret.md").write_text("hidden\n", encoding="utf-8")

        report = lint_vault(vault)
        assert report.total_files == 1


class TestLintVaultBareDir:
    """lint_vault — edge cases."""

    def test_empty_vault_no_errors(self, tmp_path: Path) -> None:
        vault = tmp_path / "empty"
        vault.mkdir()
        report = lint_vault(vault)
        assert report.passed
        assert report.total_files == 0

    def test_nonexistent_vault(self, tmp_path: Path) -> None:
        vault = tmp_path / "does-not-exist"
        report = lint_vault(vault)
        assert not report.passed
        assert any(v.rule_id == "vault-not-found" for v in report.violations)

    def test_vault_name_defaults_to_basename(self, tmp_path: Path) -> None:
        vault = tmp_path / "my-vault"
        vault.mkdir()
        report = lint_vault(vault)
        assert report.vault_name == "my-vault"

    def test_custom_vault_name(self, tmp_path: Path) -> None:
        vault = tmp_path / "dir-name"
        vault.mkdir()
        report = lint_vault(vault, vault_name="affairs")
        assert report.vault_name == "affairs"


class TestLintVaultComprehensive:
    """End-to-end test with multiple rule types to simulate a real vault."""

    def test_comprehensive_vault(self, tmp_path: Path) -> None:
        vault = tmp_path / "comprehensive"
        vault.mkdir()

        # Well-formed note with frontmatter
        (vault / "Index.md").write_text(
            "---\nid: idx\ntype: index\nstatus: active\n---\n# Index\n\nSee [[Architecture]] and [[Rules]].\n",
            encoding="utf-8",
        )
        # Valid target note
        (vault / "Architecture.md").write_text(
            "---\nid: arch\ntype: concept\nstatus: active\n---\n# Architecture\n\n[[Index]]\n",
            encoding="utf-8",
        )
        # Target note
        (vault / "Rules.md").write_text(
            "---\nid: rules\ntype: governance\nstatus: draft\n---\n# Rules\n\n[[Index]]\n",
            encoding="utf-8",
        )
        # Broken link
        (vault / "Updated.md").write_text(
            "---\nid: upd\ntype: note\n---\nSee [[Old Note That Was Deleted]].\n",
            encoding="utf-8",
        )
        # Orphan note (no incoming links)
        (vault / "Forgotten.md").write_text(
            "---\nid: forg\ntype: note\n---\n# Forgotten\n\nNobody links here.\n",
            encoding="utf-8",
        )
        # Empty note
        (vault / "Stub.md").write_text("---\nid: stub\ntype: stub\n---\n", encoding="utf-8")
        # Cross-vault link
        (vault / "Cross.md").write_text(
            "---\nid: cross\ntype: note\n---\nSee [[filesystem:Desktop Map]].\n",
            encoding="utf-8",
        )

        report = lint_vault(vault, vault_name="comprehensive")

        # Verify it found violations across multiple rule types
        found_rules = {v.rule_id for v in report.violations}
        assert "wiki-link-broken" in found_rules  # [[Old Note That Was Deleted]]
        assert "orphan-note" in found_rules  # Forgotten.md
        assert "cross-vault-link" in found_rules  # [[filesystem:Desktop Map]]
        assert "empty-note" in found_rules  # Stub.md

        # Verify total files counted correctly
        assert report.total_files == 7
