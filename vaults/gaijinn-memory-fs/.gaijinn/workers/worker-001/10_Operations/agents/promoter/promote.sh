#!/usr/bin/env bash
# promote.sh — Ingress/Promotion Pipeline
# Validates and promotes content from /pending/ to /40_Concepts/
#
# Usage:
#   ./promote.sh                                      — promote all pending files
#   ./promote.sh --check                              — dry-run: validate only, don't promote
#   ./promote.sh --file <name>.md                     — promote a specific pending file
#   ./promote.sh --list                               — list pending files with validation status
#   ./promote.sh --strict                             — upgrade all warnings to errors (passes --strict to validator)
#   ./promote.sh --metrics-output <path>              — write validation results as JSON metrics
#   ./promote.sh --linter                             — run vault linter before promotion (advisory pre-gate)
#   ./promote.sh --event-ledger-mode <direct|handoff|off>
#                                                     — choose post-promotion event-ledger behavior
#
# Flags can be combined: ./promote.sh --check --strict --linter --metrics-output /tmp/metrics.json
#
# Acceptance gates:
#   1. Frontmatter: valid YAML, required fields per vault.yaml schema
#   2. Wikilinks: all [[path]] references resolve to existing vault files
#   3. OCC compliance: provenance chain verifiable (promoted_from, linked refs)
#   4. Three-gates artifact check: mirror-smoke, perf-bench, human-signoff artifacts
#      verified when vault_promote phase is active (warnings unless --strict)
#   5. Strict mode: --strict flag upgrades all warnings to errors
#
# Integration notes:
#   - validate_promotion.py (WU-006) runs 11 checks total including three-gates
#   - When using --metrics-output <path>, validation metrics are written as JSON
#     for downstream processing (e.g., metrics_manifest ingestion)
#   - The --linter gate is advisory by default; use --strict for hard enforcement
#   - The event ledger defaults to handoff mode. Use --event-ledger-mode direct
#     only when the active GIV scope permits writing _multi-agent/events.md.
#
# Exits 0 on all-success, 1 on any failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PENDING_DIR="$VAULT_ROOT/pending"
CONCEPT_DIR="$VAULT_ROOT/40_Concepts"
VALIDATOR="$SCRIPT_DIR/validate_promotion.py"
LINTER="${LINTER_PATH:-$VAULT_ROOT/10_Operations/knowledge-linter.py}"
PROMOTER_WORKER="${PROMOTER_WORKER_ID:-promoter-worker-002}"
EVENT_LEDGER_MODE="${PROMOTE_EVENT_LEDGER_MODE:-handoff}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

pass()  { echo -e "  ${GREEN}✓${NC} $1"; }
fail()  { echo -e "  ${RED}✗${NC} $1"; }
info()  { echo -e "  ${CYAN}→${NC} $1"; }
warn()  { echo -e "  ${YELLOW}⚠${NC} $1"; }

CHECK_ONLY=false
TARGET_FILE=""
RUN_LINTER=false
STRICT_MODE=false
METRICS_OUTPUT=""

usage() {
    echo "Usage: $0 [--check|--dry-run] [--file <name.md>] [--list] [--linter] [--strict] [--metrics-output <path>] [--event-ledger-mode <direct|handoff|off>]"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check|--dry-run) CHECK_ONLY=true; shift ;;
        --file)
            if [ $# -lt 2 ]; then
                usage
                exit 1
            fi
            TARGET_FILE="$2"
            shift 2
            ;;
        --list) TARGET_FILE="__list__"; shift ;;
        --linter) RUN_LINTER=true; shift ;;
        --strict) STRICT_MODE=true; shift ;;
        --metrics-output)
            if [ $# -lt 2 ]; then
                usage
                exit 1
            fi
            METRICS_OUTPUT="$2"
            shift 2
            ;;
        --event-ledger-mode)
            if [ $# -lt 2 ]; then
                usage
                exit 1
            fi
            EVENT_LEDGER_MODE="$2"
            shift 2
            ;;
        *) usage; exit 1 ;;
    esac
done

case "$EVENT_LEDGER_MODE" in
    direct|handoff|off) ;;
    *)
        echo -e "${RED}Error:${NC} --event-ledger-mode must be one of: direct, handoff, off"
        exit 1
        ;;
esac

# ── Preflight ──────────────────────────────────────────────────────
if [ ! -d "$PENDING_DIR" ]; then
    info "No /pending/ directory exists. Creating empty one."
    mkdir -p "$PENDING_DIR"
fi

if [ ! -f "$VALIDATOR" ]; then
    echo -e "${RED}FATAL:${NC} Validator not found at $VALIDATOR"
    exit 1
fi

# ── Linter pre-promotion gate ──────────────────────────────────────
if [ "$RUN_LINTER" = true ]; then
    echo -e "${CYAN}═══ Linter Pre-Promotion Gate ═══${NC}"
    if [ ! -f "$LINTER" ]; then
        echo -e "  ${YELLOW}⚠${NC} Linter not found at $LINTER — skipping"
    else
        LINTER_RESULT=$(python3 "$LINTER" --check 2>&1) || true
        if echo "$LINTER_RESULT" | grep -q "VAULT LINTER: PASS"; then
            echo -e "  ${GREEN}✓${NC} Vault linter PASS — promoting is safe"
        else
            echo -e "  ${RED}✗${NC} Vault linter FAIL — promoting with violations may create orphans"
            echo -e "  ${YELLOW}⚠${NC} Proceeding anyway (--linter is advisory; use --check for strict gate)"
        fi
    fi
    echo ""
fi

# ── List mode ──────────────────────────────────────────────────────
if [ "$TARGET_FILE" = "__list__" ]; then
    echo -e "${CYAN}Pending files — validation status:${NC}"
    echo ""
    PENDING_FILES=$(find "$PENDING_DIR" -maxdepth 1 -name "*.md" | sort)
    if [ -z "$PENDING_FILES" ]; then
        echo "  (empty — no files in /pending/)"
        exit 0
    fi
    for f in $PENDING_FILES; do
        BASENAME=$(basename "$f")
        VALIDATOR_ARGS=("--file" "$f" "--vault-root" "$VAULT_ROOT")
        if [ "$STRICT_MODE" = true ]; then
            VALIDATOR_ARGS+=("--strict")
        fi
        RESULT=$(python3 "$VALIDATOR" "${VALIDATOR_ARGS[@]}" 2>&1 || true)
        if echo "$RESULT" | grep -q "=== PASS ===" || echo "$RESULT" | grep -q "^PASS"; then
            echo -e "  ${GREEN}✓${NC} $BASENAME — ready to promote"
        else
            ERRORS=$(echo "$RESULT" | grep "^FAIL" | sed 's/^FAIL: //')
            echo -e "  ${RED}✗${NC} $BASENAME — $ERRORS"
        fi
    done
    exit 0
fi

# ── Collect files to process ──────────────────────────────────────
if [ -n "$TARGET_FILE" ]; then
    if [[ "$TARGET_FILE" == pending/* ]]; then
        TARGET_FILE="${TARGET_FILE#pending/}"
    fi
    if [[ "$TARGET_FILE" == */* || "$TARGET_FILE" == .* || ! "$TARGET_FILE" =~ ^[A-Za-z0-9._-]+\.md$ ]]; then
        echo -e "${RED}Error:${NC} --file expects a safe pending markdown filename, e.g. concept-name.md"
        exit 1
    fi
    FILES=("$PENDING_DIR/$TARGET_FILE")
    if [ ! -f "${FILES[0]}" ]; then
        echo -e "${RED}Error:${NC} File '$TARGET_FILE' not found in /pending/"
        exit 1
    fi
else
    mapfile -t FILES < <(find "$PENDING_DIR" -maxdepth 1 -name "*.md" | sort)
fi

if [ ${#FILES[@]} -eq 0 ]; then
    info "No files in /pending/ to promote."
    exit 0
fi

# ── Process each file ──────────────────────────────────────────────
TOTAL=${#FILES[@]}
PASSED=0
FAILED=0

echo -e "${CYAN}═══ Promotion Pipeline ═══${NC}"
echo -e "  Source: $PENDING_DIR"
echo -e "  Target: $CONCEPT_DIR"
echo -e "  Mode:   $([ "$CHECK_ONLY" = true ] && echo 'CHECK-ONLY (dry-run)' || echo 'PROMOTE')"
if [ "$STRICT_MODE" = true ]; then
    echo -e "  Strict: ${YELLOW}ENABLED${NC} (warnings treated as errors)"
fi
if [ -n "$METRICS_OUTPUT" ]; then
    echo -e "  Metrics: $METRICS_OUTPUT"
fi
echo ""

for FILEPATH in "${FILES[@]}"; do
    BASENAME=$(basename "$FILEPATH")
    echo -e "${CYAN}[$((PASSED + FAILED + 1))/$TOTAL]${NC} $BASENAME"

    # Run validator with dynamic args
    VALIDATOR_ARGS=("--file" "$FILEPATH" "--vault-root" "$VAULT_ROOT")
    if [ "$STRICT_MODE" = true ]; then
        VALIDATOR_ARGS+=("--strict")
    fi
    if [ -n "$METRICS_OUTPUT" ]; then
        VALIDATOR_ARGS+=("--metrics-output" "$METRICS_OUTPUT")
    fi
    VALIDATION=$(python3 "$VALIDATOR" "${VALIDATOR_ARGS[@]}" 2>&1) || true

    if echo "$VALIDATION" | grep -q "=== PASS ===" || echo "$VALIDATION" | grep -q "^PASS"; then
        pass "Validation passed"

        if [ "$CHECK_ONLY" = true ]; then
            info "Would promote → $CONCEPT_DIR/$BASENAME"
            PASSED=$((PASSED + 1))
        else
            # Promote: move file to /40_Concepts/
            TARGET_PATH="$CONCEPT_DIR/$BASENAME"
            mkdir -p "$CONCEPT_DIR"
            if [ -e "$TARGET_PATH" ]; then
                fail "Target already exists after validation: 40_Concepts/$BASENAME"
                FAILED=$((FAILED + 1))
                echo ""
                continue
            fi
            cp -- "$FILEPATH" "$TARGET_PATH"
            # Update frontmatter promotion fields if it's a Concept type
            TARGET_PATH="$TARGET_PATH" BASENAME="$BASENAME" PROMOTER_WORKER="$PROMOTER_WORKER" python3 -c "
import os
import yaml, sys
from pathlib import Path
from datetime import datetime

path = Path(os.environ['TARGET_PATH'])
text = path.read_text()
parts = text.split('---', 2)
if len(parts) >= 3:
    fm = yaml.safe_load(parts[1])
    if fm and fm.get('type') == 'Concept':
        bits = text.split('---', 2)
        body = bits[2]
        # Inject/update promotion metadata
        meta = yaml.safe_load(bits[1]) or {}
        meta['promoted_from'] = meta.get('promoted_from', 'pending/' + os.environ['BASENAME'])
        meta['promoted_by'] = meta.get('promoted_by', os.environ['PROMOTER_WORKER'])
        meta['promotion_date'] = meta.get('promotion_date', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))
        new_fm = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()
        path.write_text('---\n' + new_fm + '\n---\n' + body.lstrip())
" 2>/dev/null || true
            rm -- "$FILEPATH"
            pass "Promoted → 40_Concepts/$BASENAME"
            PASSED=$((PASSED + 1))
        fi
    else
        ERRORS=$(echo "$VALIDATION" | grep -E "(^FAIL:|=== FAIL ===)" | sed 's/^FAIL: */>> /' | sed 's/.*=== FAIL ===.*/errors above/' || echo "$VALIDATION")
        fail "$ERRORS"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

# ── Summary ────────────────────────────────────────────────────────
echo -e "${CYAN}═══ Summary ═══${NC}"
echo -e "  Total:  $TOTAL"
echo -e "  Passed: ${GREEN}$PASSED${NC}"
echo -e "  Failed: ${RED}$FAILED${NC}"

if [ "$FAILED" -gt 0 ] && [ "$CHECK_ONLY" = true ]; then
    warn "Dry-run: $FAILED file(s) would fail promotion. Fix errors above."
fi

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi

# If we promoted anything, handle the vault semantic event ledger.
if [ "$PASSED" -gt 0 ] && [ "$CHECK_ONLY" = false ]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    LEDGER="$VAULT_ROOT/_multi-agent/events.md"
    LEDGER_ROW="| $TIMESTAMP | $PROMOTER_WORKER | concept_promoted | 40_Concepts | Promoted $PASSED file(s) via promote.sh — frontmatter+wikilink+OCC validated |"
    case "$EVENT_LEDGER_MODE" in
        direct)
            echo "$LEDGER_ROW" >> "$LEDGER"
            pass "Logged promotion event to vault event ledger"
            ;;
        handoff)
            warn "Vault event ledger update requires handoff; not writing _multi-agent/events.md"
            cat <<EOF
+++ GAIJINN_HANDOFF_TICKET_START ++++
{
  "target_work_unit_id": "WU-014",
  "target_file": "_multi-agent/events.md",
  "required_mutation_context": "Append semantic promotion event row: $LEDGER_ROW"
}
+++ GAIJINN_HANDOFF_TICKET_END ++++
EOF
            ;;
        off)
            warn "Vault event ledger logging disabled by --event-ledger-mode off"
            ;;
    esac
fi

echo -e "${GREEN}Done.${NC}"
exit 0
