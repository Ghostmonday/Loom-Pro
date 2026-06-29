"""Vault deployment data model and deploy path resolution.

GAIJINN BLUEPRINT — GUI deploy path (worker-004)
--------------------------------------------------
Layer: Cross-cutting / vault surface resolution
Status: LEARN SPRINT research artifact
Spec: .gaijinn/reviews/worker-004-gui-deploy-path.md

Defines the VaultDeployment data model for mapping Obsidian vault content
to a deployable GUI surface under the .gaijinn/ convention.

Integration points:
  - aoc_supervisor/api.py — new GET /vault/<name> endpoints
  - aoc_supervisor/repo_paths.py — VAULTS_DIR path resolution
  - scripts/dev/  — vault deploy/promotion scripts
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Regex to match Obsidian wiki-links: [[Link]] or [[Link|Display]]
_WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


@dataclass(frozen=True)
class VaultFile:
    """Metadata for a single file within a deployed vault."""

    rel_path: str
    """Relative path within the vault (e.g. 'Index.md', 'Notice Ledger.md')."""

    size_bytes: int
    """File size in bytes at deploy time."""

    md5_hash: str
    """MD5 hex digest of file content at deploy time."""

    wiki_links: list[str] = field(default_factory=list)
    """Resolved wiki-link targets found in this file ([[Target]])."""


@dataclass(frozen=True)
class VaultDeployment:
    """A deployable snapshot of an Obsidian vault under .gaijinn/vaults/.

    Captures the source Obsidian vault structure, the deploy destination,
    and per-file metadata for serving and monitoring.
    """

    name: str
    """Vault identifier — must match directory name in .gaijinn/vaults/<name>/."""

    source_dir: Path
    """Path to the original Obsidian vault directory."""

    deploy_dir: Path
    """Path where vault content is/will be deployed under .gaijinn/vaults/<name>/."""

    files: tuple[VaultFile, ...] = field(default_factory=tuple)
    """Deployed files with metadata. Ordered by rel_path."""

    deployed_at: datetime | None = None
    """UTC timestamp of the last deployment. None if never deployed."""

    # Derived metadata — computed at construction
    total_size_bytes: int = 0
    """Sum of size_bytes across all files. Computed automatically."""

    total_link_count: int = 0
    """Sum of wiki-link count across all files. Computed automatically."""

    def __post_init__(self) -> None:
        """Compute derived metadata from files."""
        # Use object.__setattr__ because dataclass is frozen
        total_size = sum(f.size_bytes for f in self.files)
        total_links = sum(len(f.wiki_links) for f in self.files)
        object.__setattr__(self, "total_size_bytes", total_size)
        object.__setattr__(self, "total_link_count", total_links)

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "name": self.name,
            "source_dir": str(self.source_dir),
            "deploy_dir": str(self.deploy_dir),
            "files": [
                {
                    "rel_path": f.rel_path,
                    "size_bytes": f.size_bytes,
                    "md5_hash": f.md5_hash,
                    "wiki_links": f.wiki_links,
                }
                for f in self.files
            ],
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "total_size_bytes": self.total_size_bytes,
            "total_link_count": self.total_link_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VaultDeployment:
        """Deserialize from a dict produced by to_dict()."""
        raw_deployed = data.get("deployed_at")
        deployed_at: datetime | None = None
        if raw_deployed:
            try:
                deployed_at = datetime.fromisoformat(str(raw_deployed))
            except (ValueError, TypeError):
                deployed_at = None

        files = tuple(
            VaultFile(
                rel_path=str(f["rel_path"]),
                size_bytes=int(f["size_bytes"]),
                md5_hash=str(f["md5_hash"]),
                wiki_links=list(f.get("wiki_links", [])),
            )
            for f in data.get("files", [])
        )

        return cls(
            name=str(data["name"]),
            source_dir=Path(str(data["source_dir"])),
            deploy_dir=Path(str(data["deploy_dir"])),
            files=files,
            deployed_at=deployed_at,
        )

    # ── Manifest I/O ───────────────────────────────────────────────────────

    def write_manifest(self, manifest_dir: Path | None = None) -> Path:
        """Write deployment manifest to JSON file.

        The manifest is written to:
            <deploy_dir>/deploy-manifest.json

        Or to <manifest_dir>/<name>-deploy-manifest.json if manifest_dir is given.
        """
        target: Path
        if manifest_dir is not None:
            target = manifest_dir.resolve() / f"{self.name}-deploy-manifest.json"
        else:
            target = self.deploy_dir / "deploy-manifest.json"

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target

    @classmethod
    def read_manifest(cls, manifest_path: Path) -> VaultDeployment:
        """Load a VaultDeployment from a manifest file."""
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    # ── Convenience ────────────────────────────────────────────────────────

    @property
    def file_count(self) -> int:
        """Number of files in this deployment."""
        return len(self.files)

    @property
    def age_seconds(self) -> float | None:
        """Seconds since deployment, or None if never deployed."""
        if self.deployed_at is None:
            return None
        return (datetime.now(timezone.utc) - self.deployed_at).total_seconds()

    def get_file(self, rel_path: str) -> VaultFile | None:
        """Look up a file by its relative path."""
        for f in self.files:
            if f.rel_path == rel_path:
                return f
        return None

    def __repr__(self) -> str:
        age = f"{self.age_seconds:.0f}s ago" if self.age_seconds is not None else "never deployed"
        return (
            f"VaultDeployment(name={self.name!r}, "
            f"files={self.file_count}, "
            f"links={self.total_link_count}, "
            f"size={self.total_size_bytes}B, "
            f"age={age})"
        )


# ── Discovery helpers ─────────────────────────────────────────────────────


def discover_vault_deployment(
    vault_name: str,
    source_dir: Path,
    deploy_root: Path,
) -> VaultDeployment:
    """Create a VaultDeployment by scanning a source Obsidian vault directory.

    Args:
        vault_name: Vault identifier (e.g. 'affairs', 'filesystem', 'gaijinn').
        source_dir: Path to the Obsidian vault source directory.
        deploy_root: Root directory under which vaults are deployed
                     (e.g. Path.home() / '.gaijinn' / 'vaults').

    Returns:
        A populated VaultDeployment with file metadata from the source.
    """
    import hashlib

    deploy_dir = deploy_root / vault_name

    files: list[VaultFile] = []
    for entry in sorted(source_dir.iterdir()):
        if not entry.is_file():
            continue

        content = entry.read_bytes()
        md5 = hashlib.md5(content, usedforsecurity=False).hexdigest()  # noqa: S324  # non-crypto checksum only

        # Extract wiki-links from text content
        wiki_links: list[str] = []
        try:
            text = content.decode("utf-8")
            wiki_links = sorted({match[0] for match in _WIKI_LINK_RE.findall(text)})
        except (UnicodeDecodeError, LookupError):
            pass  # Binary files or decode errors

        files.append(
            VaultFile(
                rel_path=entry.name,
                size_bytes=len(content),
                md5_hash=md5,
                wiki_links=wiki_links,
            )
        )

    return VaultDeployment(
        name=vault_name,
        source_dir=source_dir.resolve(),
        deploy_dir=deploy_dir.resolve(),
        files=tuple(files),
        deployed_at=datetime.now(timezone.utc),
    )


def available_vault_deployments(deploy_root: Path) -> list[VaultDeployment]:
    """Discover all deployed vaults under a deploy root.

    Scans <deploy_root>/*/deploy-manifest.json and loads each one.
    Returns an empty list if no manifests are found.
    """
    if not deploy_root.is_dir():
        return []

    results: list[VaultDeployment] = []
    for d in sorted(deploy_root.iterdir()):
        if not d.is_dir():
            continue
        manifest = d / "deploy-manifest.json"
        if manifest.exists():
            try:
                results.append(VaultDeployment.read_manifest(manifest))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    return results
