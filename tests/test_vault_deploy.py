"""Tests for vault deployment data model — worker-004 GUI deploy path.

GAIJINN BLUEPRINT — test suite for vault_deploy.py
----------------------------------------------------
Layer: Test infrastructure
Status: LEARN SPRINT research artifact
Spec: .gaijinn/reviews/worker-004-gui-deploy-path.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from aoc_supervisor.vault_deploy import (
    VaultDeployment,
    VaultFile,
    available_vault_deployments,
    discover_vault_deployment,
)


class TestVaultFile:
    """VaultFile is a frozen dataclass — basic construction and access."""

    def test_construction(self) -> None:
        vf = VaultFile(rel_path="Index.md", size_bytes=200, md5_hash="abc123")
        assert vf.rel_path == "Index.md"
        assert vf.size_bytes == 200
        assert vf.md5_hash == "abc123"
        assert vf.wiki_links == []

    def test_with_wiki_links(self) -> None:
        vf = VaultFile(
            rel_path="Gov.md",
            size_bytes=300,
            md5_hash="def456",
            wiki_links=["Architecture", "Codex Fullpass"],
        )
        assert vf.wiki_links == ["Architecture", "Codex Fullpass"]


class TestVaultDeployment:
    """VaultDeployment — creation, serialisation, and derived metadata."""

    def test_empty_deployment(self) -> None:
        d = VaultDeployment(
            name="test",
            source_dir=Path("/src"),
            deploy_dir=Path("/dst"),
        )
        assert d.name == "test"
        assert d.file_count == 0
        assert d.total_size_bytes == 0
        assert d.total_link_count == 0
        assert d.deployed_at is None
        assert d.age_seconds is None

    def test_with_files_computes_derived_metadata(self) -> None:
        d = VaultDeployment(
            name="affairs",
            source_dir=Path("/src/affairs"),
            deploy_dir=Path("/dst/affairs"),
            files=(
                VaultFile("Index.md", 100, "aaa", ["Notice Ledger", "Contacts"]),
                VaultFile("Notice Ledger.md", 300, "bbb", []),
            ),
            deployed_at=datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc),
        )
        assert d.file_count == 2
        assert d.total_size_bytes == 400
        assert d.total_link_count == 2
        assert d.age_seconds is not None

    def test_get_file(self) -> None:
        d = VaultDeployment(
            name="gaijinn",
            source_dir=Path("/src"),
            deploy_dir=Path("/dst"),
            files=(VaultFile("Index.md", 249, "ccc", ["Architecture"]),),
        )
        found = d.get_file("Index.md")
        assert found is not None
        assert found.size_bytes == 249

        assert d.get_file("Missing.md") is None

    def test_to_dict_round_trip(self) -> None:
        original = VaultDeployment(
            name="filesystem",
            source_dir=Path("/home/user/Obsidian/FileSystem"),
            deploy_dir=Path("/home/user/.gaijinn/vaults/filesystem"),
            files=(VaultFile("Index.md", 202, "d1e2f3", ["Gaijinn Repo", "Projects", "Desktop Map"]),),
            deployed_at=datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc),
        )

        raw = original.to_dict()
        assert raw["name"] == "filesystem"
        assert raw["total_size_bytes"] == 202
        assert raw["total_link_count"] == 3

        restored = VaultDeployment.from_dict(raw)
        assert restored == original
        assert restored.deployed_at == original.deployed_at

    def test_from_dict_no_deployed_at(self) -> None:
        d = VaultDeployment.from_dict(
            {
                "name": "bare",
                "source_dir": "/x",
                "deploy_dir": "/y",
                "files": [],
                "deployed_at": None,
                "total_size_bytes": 0,
                "total_link_count": 0,
            }
        )
        assert d.deployed_at is None
        assert d.age_seconds is None

    def test_manifest_write_and_read(self, tmp_path: Path) -> None:
        original = VaultDeployment(
            name="gaijinn",
            source_dir=Path("/src"),
            deploy_dir=tmp_path / "gaijinn",
            files=(VaultFile("Index.md", 249, "abc", ["Architecture"]),),
            deployed_at=datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc),
        )

        # Write manifest to custom manifest_dir
        manifest_path = original.write_manifest(manifest_dir=tmp_path)
        assert manifest_path.exists()

        # Read it back
        restored = VaultDeployment.read_manifest(manifest_path)
        assert restored == original

    def test_manifest_write_default_location(self, tmp_path: Path) -> None:
        d = VaultDeployment(
            name="filesystem",
            source_dir=Path("/src"),
            deploy_dir=tmp_path / "vaults" / "filesystem",
        )
        manifest = d.write_manifest()
        assert manifest == tmp_path / "vaults" / "filesystem" / "deploy-manifest.json"
        assert manifest.exists()


class TestDiscoverVaultDeployment:
    """discover_vault_deployment — scanning real files from an Obsidian vault."""

    def test_discover_files_and_wiki_links(self, tmp_path: Path) -> None:
        source = tmp_path / "Affairs"
        source.mkdir()

        # Write a note with wiki-links
        (source / "Index.md").write_text(
            "# Affairs\n\nSee [[Notice Ledger]] and [[Contacts]].",
            encoding="utf-8",
        )
        # Write a note with no links
        (source / "Notice Ledger.md").write_text(
            "# Notice Ledger\n\n| # | Date |\n|---|---|",
            encoding="utf-8",
        )

        deploy_root = tmp_path / ".gaijinn" / "vaults"
        deployment = discover_vault_deployment("affairs", source, deploy_root)

        assert deployment.name == "affairs"
        assert deployment.file_count == 2
        assert deployment.total_link_count == 2  # [[Notice Ledger]] and [[Contacts]]
        assert deployment.deployed_at is not None

        # Verify files are sorted
        assert deployment.files[0].rel_path == "Index.md"
        assert deployment.files[1].rel_path == "Notice Ledger.md"

        # Verify wiki-links extracted correctly
        idx_file = deployment.get_file("Index.md")
        assert idx_file is not None
        assert "Notice Ledger" in idx_file.wiki_links
        assert "Contacts" in idx_file.wiki_links

    def test_discover_with_empty_source(self, tmp_path: Path) -> None:
        source = tmp_path / "EmptyVault"
        source.mkdir()

        deployment = discover_vault_deployment("empty", source, tmp_path / ".gaijinn" / "vaults")
        assert deployment.file_count == 0
        assert deployment.total_size_bytes == 0

    def test_discover_skips_directories(self, tmp_path: Path) -> None:
        source = tmp_path / "VaultWithDirs"
        source.mkdir()
        (source / "Note.md").write_text("hello", encoding="utf-8")
        (source / "subdir").mkdir()

        deployment = discover_vault_deployment("vault", source, tmp_path / ".gaijinn" / "vaults")
        assert deployment.file_count == 1  # Only Note.md, not subdir


class TestAvailableVaultDeployments:
    """available_vault_deployments — discovering multiple deployed vaults."""

    def test_no_manifests_returns_empty(self, tmp_path: Path) -> None:
        root = tmp_path / "no-vaults"
        root.mkdir()
        assert available_vault_deployments(root) == []

    def test_missing_root_returns_empty(self, tmp_path: Path) -> None:
        root = tmp_path / "does-not-exist"
        assert available_vault_deployments(root) == []

    def test_discovers_multiple_vaults(self, tmp_path: Path) -> None:
        root = tmp_path / ".gaijinn" / "vaults"

        # Deploy two vaults
        for name in ("affairs", "gaijinn"):
            deploy_dir = root / name
            deploy_dir.mkdir(parents=True)

            deployment = VaultDeployment(
                name=name,
                source_dir=Path(f"/src/{name}"),
                deploy_dir=deploy_dir,
            )
            deployment.write_manifest()  # writes to deploy_dir/deploy-manifest.json

        vaults = available_vault_deployments(root)
        names = [v.name for v in vaults]
        assert "affairs" in names
        assert "gaijinn" in names
        assert len(vaults) == 2

    def test_skips_corrupted_manifests(self, tmp_path: Path) -> None:
        root = tmp_path / "vaults"
        bad = root / "bad-vault"
        bad.mkdir(parents=True)

        # Write invalid JSON
        (bad / "deploy-manifest.json").write_text("not json", encoding="utf-8")

        # Also put a valid one next to it
        good = root / "good-vault"
        good.mkdir()
        VaultDeployment(
            name="good",
            source_dir=Path("/src"),
            deploy_dir=good,
        ).write_manifest()

        vaults = available_vault_deployments(root)
        assert len(vaults) == 1
        assert vaults[0].name == "good"


class TestVaultDeploymentRepr:
    """Human-readable __repr__ for debugging."""

    def test_never_deployed(self) -> None:
        d = VaultDeployment(
            name="affairs",
            source_dir=Path("/x"),
            deploy_dir=Path("/y"),
        )
        assert "never deployed" in repr(d)
        assert "name='affairs'" in repr(d)

    def test_deployed(self) -> None:
        d = VaultDeployment(
            name="gaijinn",
            source_dir=Path("/x"),
            deploy_dir=Path("/y"),
            files=(VaultFile("Index.md", 249, "abc"),),
            deployed_at=datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc),
        )
        assert "files=1" in repr(d)
        assert "links=0" in repr(d)
        assert "249B" in repr(d)
        assert "age=" in repr(d)
