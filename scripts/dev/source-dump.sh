#!/usr/bin/env bash
# Gaijinn source dump — TEXT ONLY. Never embed binaries in .txt.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$HOME/Desktop/gaijinn-source-dump.txt}"
COMMIT="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
BRANCH="$(git -C "$ROOT" branch --show-current 2>/dev/null || echo unknown)"

python3 - "$ROOT" "$OUT" "$BRANCH" "$COMMIT" <<'PY'
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
BRANCH = sys.argv[3]
COMMIT = sys.argv[4]

EXT = {".py", ".json", ".md", ".sh", ".toml", ".html", ".js", ".css", ".yaml", ".yml", ".txt", ".ini", ".cfg"}
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
SKIP_PREFIXES = ("vaults/", "dist/", ".gaijinn/sessions/", ".gaijinn/codex/", ".gaijinn/workers/")
SKIP_NAMES = {".coverage", ".DS_Store"}


def skip(p: Path) -> bool:
    rel = p.relative_to(ROOT).as_posix()
    if p.name in SKIP_NAMES or rel.startswith(SKIP_PREFIXES):
        return True
    if any(part in SKIP_DIRS for part in p.parts):
        return True
    return p.suffix not in EXT and p.name not in ("Makefile", "Dockerfile", "LICENSE")


def is_text(path: Path) -> bool:
    try:
        data = path.read_bytes()[:8192]
    except OSError:
        return False
    if b"\x00" in data or data.startswith(b"SQLite format 3"):
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


files = sorted(p for p in ROOT.rglob("*") if p.is_file() and not skip(p) and is_text(p))

header = (
    "=" * 80 + "\n"
    "GAIJINN SOURCE CODE DUMP (TEXT ONLY)\n"
    f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
    f"Repo: {ROOT}\n"
    f"Branch: {BRANCH}\n"
    f"Commit: {COMMIT}\n"
    f"Files included: {len(files)}\n"
    "SKIPPED: .git, .venv, vaults/, .gaijinn/sessions/, dist/, all binaries\n"
    + "=" * 80 + "\n\n"
)

with OUT.open("w", encoding="utf-8", newline="\n") as out:
    out.write(header)
    for fp in files:
        rel = fp.relative_to(ROOT).as_posix()
        sep = "=" * 80
        out.write(f"\n{sep}\nFILE: {rel}\n{sep}\n")
        text = fp.read_text(encoding="utf-8")
        out.write(text)
        if not text.endswith("\n"):
            out.write("\n")

blob = OUT.read_bytes()
if b"\x00" in blob:
    raise SystemExit("FATAL: dump contains null bytes — aborting")

print(f"OK: {OUT} ({len(blob) / 1024 / 1024:.2f} MB, {len(files)} files, 0 null bytes)")
PY

gzip -kf "$OUT"
echo "Compressed: ${OUT}.gz"