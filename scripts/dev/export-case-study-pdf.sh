#!/usr/bin/env bash
# Export GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md → PDF for design-partner distribution.
# Requires: pandoc (+ optional xelatex or wkhtmltopdf for PDF engine).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$ROOT/docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.md"
OUT="${CASE_STUDY_PDF:-$ROOT/docs/campaign/GAIJINN-PARALLEL-EXECUTION-CASE-STUDY.pdf}"

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: case study not found at $SRC" >&2
  exit 1
fi

if ! command -v pandoc >/dev/null 2>&1; then
  echo "ERROR: pandoc not installed." >&2
  echo "  Ubuntu/Debian: sudo apt install pandoc texlive-xetex" >&2
  echo "  macOS: brew install pandoc basictex" >&2
  exit 1
fi

echo "==> Verifying case study structural anchors"
grep -E "##|convergence|0\.50|0\.8889|1\.0|30\.8|34\.6|163|171|241|44|92|TX-HT|Section 5" "$SRC" | head -24
echo "    ($(wc -l < "$SRC") lines total)"

PDF_ENGINE=""
if command -v xelatex >/dev/null 2>&1; then
  PDF_ENGINE="xelatex"
elif command -v pdflatex >/dev/null 2>&1; then
  PDF_ENGINE="pdflatex"
elif command -v wkhtmltopdf >/dev/null 2>&1; then
  PDF_ENGINE="wkhtmltopdf"
fi

if [[ -z "$PDF_ENGINE" ]]; then
  echo "ERROR: no PDF engine found (xelatex, pdflatex, or wkhtmltopdf)." >&2
  echo "  Ubuntu/Debian: sudo apt install texlive-xetex" >&2
  exit 1
fi

HTML_OUT="${CASE_STUDY_HTML:-${OUT%.pdf}.html}"

echo "==> Building PDF → $OUT (engine: $PDF_ENGINE)"
if pandoc "$SRC" \
  -o "$OUT" \
  --from=gfm \
  --pdf-engine="$PDF_ENGINE" \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V documentclass=article \
  --toc \
  --toc-depth=2 2>/dev/null; then
  echo "==> Done: $OUT ($(du -h "$OUT" | cut -f1))"
else
  echo "WARN: PDF build failed (missing LaTeX packages?). Falling back to standalone HTML." >&2
  pandoc "$SRC" \
    -o "$HTML_OUT" \
    --from=gfm \
    --standalone \
    --toc \
    --toc-depth=2 \
    -V title="Gaijinn Parallel Execution Case Study"
  echo "==> HTML fallback: $HTML_OUT ($(du -h "$HTML_OUT" | cut -f1))"
  echo "    Install full TeX for PDF: sudo apt install texlive-xetex texlive-latex-extra" >&2
fi