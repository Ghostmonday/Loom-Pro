"""Tests for cross-vault wiki-link resolution — worker-006 cross-vault links.

GAIJINN BLUEPRINT — test suite for vault_links.py
---------------------------------------------------
Layer: Test infrastructure
Status: LEARN SPRINT research artifact
Spec: .gaijinn/reviews/worker-006-cross-vault-links.md

Tests cover parsing [[vault:Target]] style links, resolving them against
deploy manifests, and detecting broken links.
"""

from __future__ import annotations

from pathlib import Path

from aoc_supervisor.vault_deploy import VaultDeployment, VaultFile
from aoc_supervisor.vault_links import CrossVaultLink, VaultLinkResolver


class TestCrossVaultLink:
    """CrossVaultLink dataclass — construction, properties, repr."""

    def test_fresh_link_is_unresolved(self) -> None:
        link = CrossVaultLink(raw="[[affairs:Notice Ledger]]", vault="affairs", target="Notice Ledger")
        assert link.is_broken is True
        assert link.resolved_path is None

    def test_resolved_link(self) -> None:
        link = CrossVaultLink(
            raw="[[gaijinn:SKILL.md]]",
            vault="gaijinn",
            target="SKILL.md",
            resolved_path="/home/user/.gaijinn/vaults/gaijinn/SKILL.md",
        )
        assert link.is_broken is False
        assert link.resolved_path == "/home/user/.gaijinn/vaults/gaijinn/SKILL.md"

    def test_link_with_display_text(self) -> None:
        link = CrossVaultLink(
            raw="[[affairs:Contacts|View Contacts]]",
            vault="affairs",
            target="Contacts",
            display="View Contacts",
        )
        assert link.display == "View Contacts"
        assert link.is_broken is True

    def test_repr(self) -> None:
        broken = CrossVaultLink(raw="[[affairs:Missing]]", vault="affairs", target="Missing")
        assert "broken" in repr(broken)

        resolved = CrossVaultLink(raw="[[affairs:Index]]", vault="affairs", target="Index", resolved_path="/x/Index.md")
        assert "->" in repr(resolved)
        assert "/x/Index.md" in repr(resolved)


class TestVaultLinkResolverParse:
    """Parsing cross-vault wiki-links from text content."""

    def test_parses_single_cross_vault_link(self) -> None:
        resolver = VaultLinkResolver()
        links = resolver.parse_links("See [[affairs:Notice Ledger]] for details.")
        assert len(links) == 1
        assert links[0].vault == "affairs"
        assert links[0].target == "Notice Ledger"
        assert links[0].raw == "[[affairs:Notice Ledger]]"

    def test_parses_multiple_cross_vault_links(self) -> None:
        resolver = VaultLinkResolver()
        links = resolver.parse_links("Check [[gaijinn:SKILL.md]] and [[filesystem:Desktop Map]].")
        assert len(links) == 2
        assert links[0].vault == "gaijinn"
        assert links[0].target == "SKILL.md"
        assert links[1].vault == "filesystem"
        assert links[1].target == "Desktop Map"

    def test_parses_links_with_display_text(self) -> None:
        resolver = VaultLinkResolver()
        links = resolver.parse_links("See [[affairs:Contacts|View Contacts]]")
        assert len(links) == 1
        assert links[0].vault == "affairs"
        assert links[0].target == "Contacts"
        assert links[0].display == "View Contacts"

    def test_ignores_intra_vault_links(self) -> None:
        """[[Target]] (no colon) should not be parsed as cross-vault."""
        resolver = VaultLinkResolver()
        links = resolver.parse_links("See [[Notice Ledger]] and [[Contacts]].")
        assert links == []

    def test_ignores_plain_brackets_and_other_markup(self) -> None:
        resolver = VaultLinkResolver()
        links = resolver.parse_links("Some [text] in brackets, not a wiki-link.")
        assert links == []

    def test_handles_empty_content(self) -> None:
        resolver = VaultLinkResolver()
        assert resolver.parse_links("") == []

    def test_parses_links_adjacent_to_punctuation(self) -> None:
        resolver = VaultLinkResolver()
        links = resolver.parse_links("Read [[affairs:Index]]! It's great.")
        assert len(links) == 1
        assert links[0].raw == "[[affairs:Index]]"

    def test_parses_link_with_dot_in_target(self) -> None:
        resolver = VaultLinkResolver()
        links = resolver.parse_links("See [[gaijinn:README.md]] for setup.")
        assert len(links) == 1
        assert links[0].target == "README.md"
        assert links[0].vault == "gaijinn"

    def test_strips_whitespace_from_vault_and_target(self) -> None:
        resolver = VaultLinkResolver()
        links = resolver.parse_links("See [[ affairs : Notice Ledger ]] for details.")
        assert len(links) == 1
        assert links[0].vault == "affairs"
        assert links[0].target == "Notice Ledger"


class TestVaultLinkResolverResolve:
    """Resolving cross-vault links against deploy manifests."""

    def _setup_resolver(self, tmp_path: Path) -> VaultLinkResolver:
        """Create a resolver pre-loaded with test vault manifests."""
        deploy_root = tmp_path / ".gaijinn" / "vaults"

        # Deploy "affairs" vault
        affairs_dir = deploy_root / "affairs"
        affairs_dir.mkdir(parents=True)
        VaultDeployment(
            name="affairs",
            source_dir=tmp_path / "Affairs",
            deploy_dir=affairs_dir,
            files=(
                VaultFile("Index.md", 200, "abc", ["Notice Ledger", "Contacts"]),
                VaultFile("Notice Ledger.md", 300, "def", []),
                VaultFile("Contacts.md", 150, "ghi", []),
            ),
        ).write_manifest()

        # Deploy "gaijinn" vault
        gaijinn_dir = deploy_root / "gaijinn"
        gaijinn_dir.mkdir()
        VaultDeployment(
            name="gaijinn",
            source_dir=tmp_path / "Gaijinn",
            deploy_dir=gaijinn_dir,
            files=(
                VaultFile("Index.md", 500, "jkl", []),
                VaultFile("SKILL.md", 300, "mno", ["Architecture"]),
            ),
        ).write_manifest()

        return VaultLinkResolver(deploy_root=deploy_root)

    def test_resolves_existing_cross_vault_link(self, tmp_path: Path) -> None:
        resolver = self._setup_resolver(tmp_path)
        link = CrossVaultLink(raw="[[affairs:Notice Ledger]]", vault="affairs", target="Notice Ledger")
        resolved = resolver.resolve_link(link)
        assert resolved.is_broken is False
        assert resolved.resolved_path is not None
        assert "Notice Ledger" in resolved.resolved_path

    def test_returns_broken_for_missing_target(self, tmp_path: Path) -> None:
        resolver = self._setup_resolver(tmp_path)
        link = CrossVaultLink(raw="[[affairs:MissingFile]]", vault="affairs", target="MissingFile")
        resolved = resolver.resolve_link(link)
        assert resolved.is_broken is True

    def test_returns_broken_for_unknown_vault(self, tmp_path: Path) -> None:
        resolver = self._setup_resolver(tmp_path)
        link = CrossVaultLink(raw="[[unknown:Index]]", vault="unknown", target="Index")
        resolved = resolver.resolve_link(link)
        assert resolved.is_broken is True

    def test_does_not_re_resolve_already_resolved(self, tmp_path: Path) -> None:
        resolver = self._setup_resolver(tmp_path)
        link = CrossVaultLink(
            raw="[[affairs:Index]]",
            vault="affairs",
            target="Index",
            resolved_path="/already/resolved/Index.md",
        )
        resolved = resolver.resolve_link(link)
        assert resolved.resolved_path == "/already/resolved/Index.md"

    def test_resolves_with_case_insensitive_match(self, tmp_path: Path) -> None:
        resolver = self._setup_resolver(tmp_path)
        # File exists as "Index.md" — querying "index.md" should match case-insensitively
        link = CrossVaultLink(raw="[[affairs:index.md]]", vault="affairs", target="index.md")
        resolved = resolver.resolve_link(link)
        assert resolved.is_broken is False

    def test_resolve_all(self, tmp_path: Path) -> None:
        resolver = self._setup_resolver(tmp_path)
        links = [
            CrossVaultLink(raw="[[affairs:Index]]", vault="affairs", target="Index"),
            CrossVaultLink(raw="[[affairs:Missing]]", vault="affairs", target="Missing"),
            CrossVaultLink(raw="[[gaijinn:SKILL.md]]", vault="gaijinn", target="SKILL.md"),
        ]
        resolved = resolver.resolve_all(links)
        assert resolved[0].is_broken is False
        assert resolved[1].is_broken is True
        assert resolved[2].is_broken is False

    def test_check_text_parse_and_resolve(self, tmp_path: Path) -> None:
        resolver = self._setup_resolver(tmp_path)
        results = resolver.check_text("See [[affairs:Notice Ledger]] and [[gaijinn:SKILL.md]]")
        assert len(results) == 2
        assert all(r.is_broken is False for r in results)


class TestVaultLinkResolverBrokenLinks:
    """Isolating broken links."""

    def test_broken_links_from_text(self, tmp_path: Path) -> None:
        resolver = VaultLinkResolver(deploy_root=tmp_path / "empty")
        broken = resolver.broken_links("[[affairs:Missing]] and [[gaijinn:AlsoMissing]]")
        assert len(broken) == 2


class TestVaultLinkResolverReport:
    """Human-readable report generation."""

    def test_report_with_no_links(self) -> None:
        resolver = VaultLinkResolver()
        report = resolver.report("")
        assert "0 link(s)" in report

    def test_report_with_mixed_results(self, tmp_path: Path) -> None:
        resolver = VaultLinkResolver(deploy_root=tmp_path / "empty")
        report = resolver.report("[[affairs:Missing]]")
        assert "BROKEN" in report
        assert "Summary:" in report
        assert "0 resolved, 1 broken" in report


class TestVaultLinkResolverKnownVaults:
    """Discovering known vaults from manifests."""

    def test_no_vaults_when_no_deploy_root(self) -> None:
        resolver = VaultLinkResolver()
        assert resolver.known_vaults == []

    def test_known_vaults_from_manifests(self, tmp_path: Path) -> None:
        resolver = VaultLinkResolver(deploy_root=tmp_path / "nonexistent")
        assert resolver.known_vaults == []

    def test_known_vaults_after_setup(self, tmp_path: Path) -> None:
        deploy_root = tmp_path / ".gaijinn" / "vaults"

        # Deploy two vaults
        for name in ("affairs", "gaijinn"):
            d = deploy_root / name
            d.mkdir(parents=True)
            VaultDeployment(name=name, source_dir=tmp_path / name, deploy_dir=d).write_manifest()

        resolver = VaultLinkResolver(deploy_root=deploy_root)
        assert "affairs" in resolver.known_vaults
        assert "gaijinn" in resolver.known_vaults


class TestVaultLinkResolverEdgeCases:
    """Edge cases for the resolver."""

    def test_no_deploy_root_returns_broken(self) -> None:
        resolver = VaultLinkResolver()
        link = CrossVaultLink(raw="[[affairs:Index]]", vault="affairs", target="Index")
        assert resolver.resolve_link(link).is_broken is True

    def test_output_logged_via_report_method(self, tmp_path: Path) -> None:
        """Verify report output is terminal-safe and structured."""
        resolver = VaultLinkResolver(deploy_root=tmp_path / "empty")
        report = resolver.report("[[affairs:Index.md]]")
        assert report.strip()
        # Report must have consistent line structure
        lines = report.splitlines()
        assert any("BROKEN" in line for line in lines)
        assert any("Summary:" in line for line in lines)

    def test_resolves_after_index_is_built(self, tmp_path: Path) -> None:
        """Resolving should work after known_vaults triggers index build."""
        deploy_root = tmp_path / ".gaijinn" / "vaults"
        affairs_dir = deploy_root / "affairs"
        affairs_dir.mkdir(parents=True)
        VaultDeployment(
            name="affairs",
            source_dir=tmp_path / "Affairs",
            deploy_dir=affairs_dir,
            files=(VaultFile("Index.md", 200, "abc"),),
        ).write_manifest()

        resolver = VaultLinkResolver(deploy_root=deploy_root)
        # Trigger index build via known_vaults
        _ = resolver.known_vaults

        link = CrossVaultLink(raw="[[affairs:Index.md]]", vault="affairs", target="Index.md")
        resolved = resolver.resolve_link(link)
        assert resolved.is_broken is False
