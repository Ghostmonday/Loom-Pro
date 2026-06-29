"""promote command — Ingress/Promotion Pipeline.

Wraps the vault promoter agent (promote.sh + validate_promotion.py + vault linter)
into a unified CLI command.

Pipeline: vault linter (pre) → validate_promotion.py → promote.sh → vault linter (post)

Usage:
    gaijinn promote                          # auto-detect vault from CWD
    gaijinn promote --vault /path/to/vault   # explicit vault path
    gaijinn promote --check                  # dry-run: validate only
    gaijinn promote --file foo.md            # promote specific file
    gaijinn promote --list                   # list pending with validation status
    gaijinn promote --skip-linter            # skip vault linter (e.g. during dev loop)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer


def _find_vault_root(cwd: Path) -> Path | None:
    """Find the vault root by looking for .gaijinn/ directory.

    Walks up from CWD, checking for .gaijinn/merge/governance.json as the anchor.
    Falls back to checking known vault paths.
    """
    # Walk up from CWD
    current = cwd.resolve()
    for parent in [current] + list(current.parents):
        gaijinn_dir = parent / ".gaijinn"
        if gaijinn_dir.is_dir() and (gaijinn_dir / "bridge" / "council.md").exists():
            return parent

    # Check known vault paths
    known_vaults = [
        Path.home() / "workspace" / "github.com" / "ghost-monday" / "Gaijinn" / "vaults" / "gaijinn-memory-fs",
    ]
    for v in known_vaults:
        if v.exists() and (v / ".gaijinn").is_dir():
            return v

    return None


def _run_vault_linter(vault_root: Path) -> bool:
    """Run the vault knowledge linter. Returns True if it passes."""
    linter = vault_root / "10_Operations" / "knowledge-linter.py"
    if not linter.exists():
        typer.echo(f"  ⚠ vault linter not found at {linter}", err=True)
        return False

    result = subprocess.run(
        [sys.executable, str(linter), "--exclude-dirs", "pending,.gaijinn"],
        capture_output=True,
        text=True,
        cwd=str(vault_root),
    )

    # Print output
    for line in result.stdout.splitlines():
        typer.echo(f"  {line}")

    if result.returncode != 0:
        for line in result.stderr.splitlines():
            if line.strip():
                typer.echo(f"  ! {line}", err=True)

    return result.returncode == 0


def _find_promote_sh(vault_root: Path) -> Path:
    """Find promote.sh in the vault."""
    candidates = [
        vault_root / "10_Operations" / "agents" / "promoter" / "promote.sh",
        vault_root / "10_Operations" / "promote.sh",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def promote_cmd(
    vault_root: str | None = None,
    check: bool = False,
    file: str | None = None,
    list_files: bool = False,
    skip_linter: bool = False,
) -> None:
    """Promote content from /pending/ to /40_Concepts/ through the validation pipeline.

    Pipeline: vault linter (pre) → [validate_promotion.py] → promote.sh → vault linter (post)
    """
    # ── Resolve vault root ──────────────────────────────────────────────
    if vault_root:
        root = Path(vault_root).resolve()
    else:
        detected = _find_vault_root(Path.cwd())
        if detected is None:
            typer.echo(
                "ERROR: Could not detect vault root. Run from inside a Gaijinn vault or pass --vault /path/to/vault",
                err=True,
            )
            raise typer.Exit(code=1)
        root = detected

    if not root.is_dir():
        typer.echo(f"ERROR: Vault root '{root}' does not exist or is not a directory", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Vault root: {root}")
    typer.echo("")

    # ── List mode ───────────────────────────────────────────────────────
    if list_files:
        promote_sh = _find_promote_sh(root)
        if not promote_sh.exists():
            typer.echo("ERROR: promote.sh not found in vault", err=True)
            raise typer.Exit(code=1)
        result = subprocess.run(
            [str(promote_sh), "--list"],
            capture_output=False,
            cwd=str(root),
        )
        raise typer.Exit(code=result.returncode)

    # ── Pre-promotion vault linter ─────────────────────────────────────
    if not skip_linter:
        typer.echo("═══ Pre-promotion vault linter ═══")
        linter_pass = _run_vault_linter(root)
        if not linter_pass:
            typer.echo("")
            typer.echo(
                "✗ PRE-PROMOTION LINTER FAILED — fix violations before promoting.\n"
                "  Use --skip-linter to force promotion (not recommended).",
                err=True,
            )
            raise typer.Exit(code=1)
        typer.echo("")
    else:
        typer.echo("  ⚠ Vault linter skipped (--skip-linter)")
        typer.echo("")

    # ── Run promote.sh ─────────────────────────────────────────────────
    promote_sh = _find_promote_sh(root)
    if not promote_sh.exists():
        typer.echo(f"ERROR: promote.sh not found at {promote_sh}", err=True)
        raise typer.Exit(code=1)

    promote_args = [str(promote_sh)]
    if check:
        promote_args.append("--check")
    if file:
        promote_args.extend(["--file", file])

    typer.echo("═══ Promotion pipeline ═══")
    result = subprocess.run(
        promote_args,
        capture_output=False,
        cwd=str(root),
    )

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

    # ── Post-promotion vault linter ────────────────────────────────────
    if not skip_linter and not check and file is None:
        typer.echo("")
        typer.echo("═══ Post-promotion vault linter ═══")
        linter_pass = _run_vault_linter(root)
        if not linter_pass:
            typer.echo("")
            typer.echo(
                "⚠ Post-promotion linter has violations (non-blocking — promotion succeeded).\n"
                "  Review violations above.",
            )
        typer.echo("")

    typer.echo("Promotion complete.")
