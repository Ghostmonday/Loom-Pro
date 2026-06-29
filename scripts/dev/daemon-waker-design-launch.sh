#!/usr/bin/env bash
# Launch multi-model Daemon Waker design pass (Grok headless; others manual).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PROMPT_SRC="${ROOT}/docs/architecture/daemon-waker-design-prompt.md"
PROMPT_OUT="${ROOT}/.gaijinn/afk/daemon-waker-prompt.txt"
DESIGN_DIR="${ROOT}/.gaijinn/design"
MODEL="${DAEMON_WAKER_MODEL:-grok-build}"

mkdir -p "${ROOT}/.gaijinn/afk" "$DESIGN_DIR"

# Extract prompt block from design doc
python3 - <<'PY' "$PROMPT_SRC" "$PROMPT_OUT"
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding="utf-8")
start = src.find("```markdown\n")
end = src.find("\n```", start + 12)
if start < 0 or end < 0:
    raise SystemExit("Could not find ```markdown prompt block in design doc")
block = src[start + len("```markdown\n") : end].strip()
Path(sys.argv[2]).write_text(block + "\n", encoding="utf-8")
print(f"Wrote {len(block)} chars → {sys.argv[2]}")
PY

echo "==> Prompt ready: $PROMPT_OUT"
echo ""
echo "Manual paste targets (copy $PROMPT_OUT):"
echo "  • ChatGPT — Gaijinn project chat"
echo "  • Gemini — new chat + attach docs/architecture/daemon-waker-design-prompt.md"
echo ""

if [[ "${1:-}" == "--manual-only" ]]; then
  exit 0
fi

if ! command -v grok >/dev/null 2>&1; then
  echo "grok not on PATH — use --manual-only and paste prompt into ChatGPT/Gemini"
  exit 1
fi

OUT="${DESIGN_DIR}/daemon-waker-grok.md"
echo "==> Grok design pass → $OUT"
grok \
  --prompt-file "$PROMPT_OUT" \
  --always-approve \
  --model "$MODEL" \
  --cwd "$ROOT" \
  --max-turns 40 \
  | tee "$OUT"

echo ""
echo "==> Next: paste same prompt into ChatGPT + Gemini; save to:"
echo "    $DESIGN_DIR/daemon-waker-chatgpt.md"
echo "    $DESIGN_DIR/daemon-waker-gemini.md"
echo "==> Then: gaijinn council say --global --as cursor 'DAEMON WAKER: designs ready for synthesis'"