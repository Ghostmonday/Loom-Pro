"""Cross-vault wiki-link resolution for deployed Obsidian vaults.

GAIJINN BLUEPRINT — cross-vault links (worker-006)
--------------------------------------------------
Layer: Cross-cutting / vault link resolution
Status: LEARN SPRINT research artifact
Spec: .gaijinn/reviews/worker-006-cross-vault-links.md

Resolves [[vault_name:File Name]] style cross-vault wiki-links between
deployed Obsidian vaults under .gaijinn/vaults/. Builds on the existing
VaultDeployment model from vault_deploy.py for manifest-based lookups.

Integration points:
  - aoc_supervisor/vault_deploy.py — VaultDeployment model, _WIKI_LINK_RE
  - aoc_supervisor/repo_paths.py — potential VAULTS_DIR path convention
  - gaijinn-memory-fs — optional in-memory link resolution hook

Link syntax:
  [[Target]]               — intra-vault link (same vault, pass-through)
  [[vault_name:Target]]    — cross-vault link (resolved via deploy manifest)
  [[vault_name:Target|Display]] — cross-vault link with display text

Design decisions:
  - Cross-vault links are resolved lazily at query/read time, not eagerly at
    deploy time. This keeps the deploy manifest append-only and avoids
    redeployment when a linked vault changes.
  - Broken cross-vault links are warnings, not errors. A broken link is
    reported as a BrokenCrossVaultLink namedtuple with the original link text,
    allowing callers to decide how to surface it (e.g., warn in council, render
    with a broken-link indicator in the GUI).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# Regex for cross-vault wiki-links: [[vault_name:Target]] or [[vault_name:Target|Display]]
_CROSS_VAULT_LINK_RE = re.compile(r"\[\[([^\[\]\|:]+):([^\[\]\|]+?)(?:\|([^\[\]]+))?\]\]")


@dataclass(frozen=True)
class CrossVaultLink:
    """A parsed cross-vault wiki-link with vault and target information.

    Attributes:
        raw: The original link text (e.g. '[[affairs:Notice Ledger]]').
        vault: The vault name segment (e.g. 'affairs').
        target: The target file name within the vault (e.g. 'Notice Ledger').
        display: Optional display text override (e.g. 'Notice Ledger').
        resolved_path: Absolute path to the target file, if found.
    """

    raw: str
    vault: str
    target: str
    display: str | None = None
    resolved_path: str | None = None

    @property
    def is_broken(self) -> bool:
        """True if the link could not be resolved to an existing file."""
        return self.resolved_path is None

    def __repr__(self) -> str:
        status = "broken" if self.is_broken else f"-> {self.resolved_path}"
        return f"CrossVaultLink({self.raw!r}, vault={self.vault!r}, target={self.target!r}, {status})"


class VaultLinkResolver:
    """Resolve cross-vault wiki-links against a set of deployed vault manifests.

    Typical usage::

        from aoc_supervisor.vault_deploy import available_vault_deployments
        from aoc_supervisor.vault_links import VaultLinkResolver

        resolver = VaultLinkResolver(deploy_root=Path.home() / ".gaijinn" / "vaults")
        links = resolver.parse_links("See [[affairs:Notice Ledger]] for details.")
        for link in links:
            resolved = resolver.resolve_link(link)

    Args:
        deploy_root: Root directory under which vaults are deployed
            (e.g. Path.home() / '.gaijinn' / 'vaults'). Each subdirectory with a
            deploy-manifest.json is a candidate vault.
        memory_fs_lookup: Optional callable for gaijinn-memory-fs integration.
            Signature: (vault_name: str, file_name: str) -> str | None.
            Should return the file content or None if not found.
    """

    def __init__(
        self,
        deploy_root: Path | None = None,
        memory_fs_lookup: Callable[[str, str], str | None] | None = None,
    ) -> None:
        self._deploy_root = deploy_root
        self._memory_fs_lookup = memory_fs_lookup
        # Lazy-loaded vault index: {vault_name: {file_rel_path: ...}}
        self._vault_index: dict[str, dict[str, str]] | None = None

    # ── Public API ──────────────────────────────────────────────────────────

    def parse_links(self, content: str) -> list[CrossVaultLink]:
        """Parse all cross-vault wiki-links from content.

        Returns a list of CrossVaultLink objects. Intra-vault links
        (``[[Target]]`` without a colon) are ignored — only ``vault:Target``
        style links are captured.
        """
        results: list[CrossVaultLink] = []
        for match in _CROSS_VAULT_LINK_RE.finditer(content):
            vault = match.group(1).strip()
            target = match.group(2).strip()
            display = match.group(3).strip() if match.group(3) else None
            raw = match.group(0)
            results.append(CrossVaultLink(raw=raw, vault=vault, target=target, display=display))
        return results

    def resolve_link(self, link: CrossVaultLink) -> CrossVaultLink:
        """Resolve a single cross-vault link against deployed manifests.

        If the link is already resolved (resolved_path is set), returns it
        unchanged. Otherwise looks up the target in the vault's deploy manifest.

        Returns a new CrossVaultLink with resolved_path set, or the original
        link if it could not be resolved (is_broken will be True).
        """
        if link.resolved_path is not None:
            return link

        vault_index = self._ensure_index()
        manifest_dir = vault_index.get(link.vault)
        if manifest_dir is None:
            return link  # Unknown vault

        # Look for the target file — exact match, then case-insensitive match
        target_lower = link.target.lower()
        if self._deploy_root is None:
            return link  # No deploy root configured — can't resolve paths
        for file_rel_path in manifest_dir:
            if file_rel_path == link.target or file_rel_path.lower() == target_lower:
                # Found it!
                resolved_path = str((self._deploy_root / link.vault / file_rel_path).resolve())
                return CrossVaultLink(
                    raw=link.raw,
                    vault=link.vault,
                    target=link.target,
                    display=link.display,
                    resolved_path=resolved_path,
                )

        # Obsidian convention: [[Target]] resolves to Target.md or Target.md
        # Try .md extension before declaring broken
        target_with_md = link.target + ".md"
        target_md_lower = target_with_md.lower()
        for file_rel_path in manifest_dir:
            if file_rel_path == target_with_md or file_rel_path.lower() == target_md_lower:
                resolved_path = str((self._deploy_root / link.vault / file_rel_path).resolve())
                return CrossVaultLink(
                    raw=link.raw,
                    vault=link.vault,
                    target=link.target,
                    display=link.display,
                    resolved_path=resolved_path,
                )

        return link  # No match found — broken link

    def resolve_all(self, links: list[CrossVaultLink]) -> list[CrossVaultLink]:
        """Resolve all links and return the resolved list.

        Links that could not be resolved are returned with is_broken=True.
        """
        return [self.resolve_link(link) for link in links]

    def check_text(self, content: str) -> list[CrossVaultLink]:
        """Parse and resolve all cross-vault links in content in one call."""
        return self.resolve_all(self.parse_links(content))

    def broken_links(self, links_or_content: str | list[CrossVaultLink]) -> list[CrossVaultLink]:
        """Return only the unresolved (broken) links from parsed or raw content."""
        if isinstance(links_or_content, str):
            links = self.parse_links(links_or_content)
        else:
            links = links_or_content
        return [self.resolve_link(link) for link in links if self.resolve_link(link).is_broken]

    def report(self, links_or_content: str | list[CrossVaultLink]) -> str:
        """Generate a human-readable report of cross-vault link resolution.

        Includes counts of resolved, broken, and total links.
        """
        if isinstance(links_or_content, str):
            links = self.parse_links(links_or_content)
        else:
            links = links_or_content

        resolved = self.resolve_all(links)
        total = len(resolved)
        broken = [l for l in resolved if l.is_broken]
        ok = [l for l in resolved if not l.is_broken]

        lines = [f"Cross-vault link report: {total} link(s)"]
        for link in ok:
            lines.append(f"  OK    {link.raw} -> {link.resolved_path}")
        for link in broken:
            lines.append(f"  BROKEN {link.raw} (vault={link.vault!r}, target={link.target!r})")
        lines.append(f"Summary: {len(ok)} resolved, {len(broken)} broken")
        return "\n".join(lines)

    # ── Internal ────────────────────────────────────────────────────────────

    def _ensure_index(self) -> dict[str, dict[str, str]]:
        """Build vault index if needed and return it."""
        if self._vault_index is None:
            self._build_vault_index()
        return self._vault_index  # type: ignore[return-value]

    def _build_vault_index(self) -> None:
        """Build an index of all deployed vault files from deploy manifests.

        Index structure: {vault_name: {file_rel_path: ...}}
        """
        self._vault_index = {}
        if self._deploy_root is None or not self._deploy_root.is_dir():
            return

        for vault_dir in sorted(self._deploy_root.iterdir()):
            if not vault_dir.is_dir():
                continue
            manifest = vault_dir / "deploy-manifest.json"
            if not manifest.exists():
                continue
            try:
                from aoc_supervisor.vault_deploy import VaultDeployment

                deployment = VaultDeployment.read_manifest(manifest)
            except Exception:  # noqa: BLE001
                # Skip malformed manifests
                continue

            name = deployment.name
            file_map: dict[str, str] = {}
            for vf in deployment.files:
                file_map[vf.rel_path] = vf.rel_path
            self._vault_index[name] = file_map

    @property
    def known_vaults(self) -> list[str]:
        """List of vault names known to this resolver."""
        return sorted(self._ensure_index().keys())
