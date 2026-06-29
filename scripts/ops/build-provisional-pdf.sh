#!/usr/bin/env bash
# Build USPTO provisional filing PDFs: specification + drawings.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SPEC_SRC="${SPEC_SRC:-$ROOT/docs/campaign/legal/provisional-filing/USPTO-PATENT-APPLICATION-DRAFT.md}"
FIG_DIR="$ROOT/docs/campaign/legal/provisional-filing/figures"
OUT_DIR="$ROOT/dist/provisional-filing"

mkdir -p "$OUT_DIR"

if [[ ! -f "$SPEC_SRC" ]]; then
  SPEC_SRC="$HOME/Desktop/USPTO-PATENT-APPLICATION-DRAFT.md"
fi
if [[ ! -f "$SPEC_SRC" ]]; then
  echo "error: specification source not found" >&2
  exit 1
fi

echo "spec source: $SPEC_SRC"

# ── 01 Specification (HTML → Chrome PDF; pdflatex often missing packages) ──
SPEC_HTML="$OUT_DIR/01-SPECIFICATION.html"
pandoc "$SPEC_SRC" -o "$SPEC_HTML" --standalone --toc --toc-depth=2 \
  -V margin-left=1in -V margin-right=1in

CHROME=""
for c in google-chrome google-chrome-stable chromium chromium-browser "$HOME/.local/bin/google-chrome"; do
  if command -v "$c" >/dev/null 2>&1; then
    CHROME="$c"
    break
  fi
done

if [[ -n "$CHROME" ]]; then
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$OUT_DIR/01-SPECIFICATION.pdf" \
    "file://$SPEC_HTML" 2>/dev/null || true
fi

if [[ ! -f "$OUT_DIR/01-SPECIFICATION.pdf" ]]; then
  echo "error: could not build 01-SPECIFICATION.pdf — open $SPEC_HTML and Print → PDF" >&2
  exit 1
fi

# ── 02 Drawings (HTML wrapper → Chrome headless PDF) ──
DRAW_HTML="$OUT_DIR/02-DRAWINGS.html"
cat >"$DRAW_HTML" <<'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Patent Drawings — FIGS. 1 and 4</title>
  <style>
    @page { size: letter landscape; margin: 0.5in; }
    body { font-family: Arial, sans-serif; margin: 0; }
    .sheet { page-break-after: always; padding: 12px; }
    .sheet:last-child { page-break-after: auto; }
    h1 { font-size: 14px; margin: 0 0 8px; }
    img, object { max-width: 100%; height: auto; display: block; margin: 0 auto; }
    .note { font-size: 10px; color: #333; margin-top: 6px; }
  </style>
</head>
<body>
HTML

for fig in fig01-deployment-loop.svg fig04-giv-envelope.svg; do
  path="$FIG_DIR/$fig"
  if [[ -f "$path" ]]; then
    title="${fig%.svg}"
    cat >>"$DRAW_HTML" <<HTML
  <div class="sheet">
    <h1>${title}</h1>
    <object data="file://${path}" type="image/svg+xml" width="100%" height="480"></object>
    <p class="note">GIV = Agent Intent Vector. Reference numerals per USPTO-PATENT-APPLICATION-DRAFT.md</p>
  </div>
HTML
  fi
done

cat >>"$DRAW_HTML" <<'HTML'
</body>
</html>
HTML

if [[ -n "${CHROME:-}" ]]; then
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$OUT_DIR/02-DRAWINGS.pdf" \
    "file://$DRAW_HTML" 2>/dev/null || true
fi

if [[ ! -f "$OUT_DIR/02-DRAWINGS.pdf" ]]; then
  echo "drawings: Chrome headless unavailable — use $DRAW_HTML → Print → PDF"
fi

# ── Bundle manifest ──
cat >"$OUT_DIR/README.txt" <<EOF
Gaijinn Provisional Filing PDFs
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Inventor: Amir Khodabakhsh (California, US)

Upload to USPTO Patent Center:
  1. 01-SPECIFICATION.pdf  (required)
  2. 02-DRAWINGS.pdf       (recommended)

Source: $SPEC_SRC
EOF

echo ""
echo "=== Filing package ==="
ls -lh "$OUT_DIR"/*.pdf 2>/dev/null || ls -lh "$OUT_DIR"