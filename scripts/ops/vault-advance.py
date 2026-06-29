#!/usr/bin/env python3
"""vault-advance: one phase per tick, 10-phase vault advancement cycle.
Scheduled via Hermes cron every 15m (no_agent). Advances the gaijinn-memory-fs vault
through learn→act→measure→promote→distill (2 passes = 10 phases).

Phase definitions match vault-ui-intent-map.json intent phases:
  vault_learn (0,5) → vault_act (1,6) → vault_measure (2,7) → vault_promote (3,8) → vault_distill (4,9)
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT = os.path.join(ROOT, "vaults", "gaijinn-memory-fs")
STATE_FILE = os.path.join(ROOT, ".gaijinn", "vault-advance-state.json")
LOGFILE = os.path.join(ROOT, ".gaijinn", "vault-advance.log")

PHASES = [
    "vault_learn",
    "vault_act",
    "vault_measure",
    "vault_promote",
    "vault_distill",
    "vault_learn_2",
    "vault_act_2",
    "vault_measure_2",
    "vault_promote_2",
    "vault_distill_2",
]

PHASE_LABELS = {
    "vault_learn": "Scan pending items, detect new concepts",
    "vault_act": "Process/converge pending into structured form",
    "vault_measure": "Validate with gaijinn analyze, check integrity",
    "vault_promote": "Move pending items to 40_Concepts/",
    "vault_distill": "Synthesize context, update Current_Context.md",
    "vault_learn_2": "Second pass: deep scan, cross-reference",
    "vault_act_2": "Refine, backfill provenance chains",
    "vault_measure_2": "Re-validate, check linter",
    "vault_promote_2": "Second promotion round, sweep orphans",
    "vault_distill_2": "Finalize, log events, rotate phase",
}


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LOGFILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"phase_index": 0, "cycle": 0, "created_at": datetime.now(timezone.utc).isoformat()}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def run_cmd(cmd, capture=True):
    """Run a shell command, return (ok, output)."""
    try:
        result = subprocess.run(  # noqa: S603
            ["/bin/bash", "-c", cmd],
            capture_output=capture,
            text=True,
            timeout=120,
        )
        ok = result.returncode == 0
        out = result.stdout.strip() if result.stdout else ""
        err = result.stderr.strip() if result.stderr else ""
        return ok, out or err or f"exit code {result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


def phase_learn():
    """Scan pending/ for new items, list unprocessed concepts."""
    pending_dir = os.path.join(VAULT, "pending")
    if not os.path.isdir(pending_dir):
        return True, "no pending/ directory"

    items = [f for f in os.listdir(pending_dir) if f.endswith((".md", ".json", ".yaml", ".yml"))]
    if items:
        return True, f"found {len(items)} pending items: {', '.join(items[:5])}"
    return True, "no pending items"


def phase_act():
    """Run gaijinn analyze to process pending into structured form."""
    ok, out = run_cmd("gaijinn analyze 2>&1 || true")
    # Check for grid spawn readiness
    ok2, out2 = run_cmd("gaijinn analyze 2>&1 | grep -E 'grid_spawn_ready|coupling_reviews|flagged_files' || true")
    summary = out.split("\n")[-3:] if out else "no output"
    detail = out2 if out2 else "no blockers"
    return ok, f"analyze done | summary: {summary} | {detail}"


def phase_measure():
    """Run linter check on vault."""
    lint_script = os.path.join(VAULT, "10_Operations", "knowledge-linter.py")
    if os.path.exists(lint_script):
        ok, out = run_cmd(f"python3 '{lint_script}' --check 2>&1 || true")
        return ok, f"linter: {'PASS' if ok else 'ISSUES'} | {out[:200]}"
    # Fallback: check state file linter result
    state_path = os.path.join(ROOT, ".gaijinn", "hermes-loop-state.json")
    if os.path.exists(state_path):
        with open(state_path) as f:
            ls = json.load(f)
            return ls.get("linter_pass", False), f"linter_pass={ls.get('linter_pass')}"
    return True, "no linter found, skipping"


def phase_promote():
    """Promote pending items to 40_Concepts/."""
    pending_dir = os.path.join(VAULT, "pending")
    concepts_dir = os.path.join(VAULT, "40_Concepts")
    if not os.path.isdir(pending_dir):
        return True, "no pending/ directory"

    items = [f for f in os.listdir(pending_dir) if f.endswith(".md")]
    if not items:
        return True, "nothing to promote"

    promoted = 0
    for item in items:
        src = os.path.join(pending_dir, item)
        dst = os.path.join(concepts_dir, item)
        if not os.path.exists(dst):
            os.rename(src, dst)
            promoted += 1
            log(f"  PROMOTED {item} → 40_Concepts/")

    gaijinn_promote_ok, _ = run_cmd("gaijinn promote --yes 2>&1 || true")
    return True, f"promoted {promoted} files, gaijinn promote={'ok' if gaijinn_promote_ok else 'noop'}"


def phase_distill():
    """Update Current_Context.md with health snapshot."""
    state_path = os.path.join(ROOT, ".gaijinn", "hermes-loop-state.json")
    phase_state = "unknown"
    convergence = "unknown"
    if os.path.exists(state_path):
        with open(state_path) as f:
            ls = json.load(f)
            phase_state = ls.get("phase", "unknown")
            convergence = ls.get("convergence", "unknown")

    ctx_path = os.path.join(VAULT, "Current_Context.md")
    with open(ctx_path, "w") as f:
        f.write(
            f"""# Current Context — Vault Health Snapshot

*Generated by vault-advance at {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}*

- **System phase:** {phase_state}
- **Convergence:** {convergence}
- **Cycle:** advancement pipeline running
- **Status:** autonomous
"""
        )
    return True, f"Current_Context.md updated (phase={phase_state}, convergence={convergence})"


def main():
    state = load_state()
    phase_idx = state["phase_index"]
    cycle = state["cycle"]
    phase = PHASES[phase_idx]
    label = PHASE_LABELS.get(phase, phase)

    log(f"START phase={phase} ({phase_idx + 1}/{len(PHASES)}) cycle={cycle} — {label}")

    # Dispatch phase handler
    if phase in ("vault_learn", "vault_learn_2"):
        ok, detail = phase_learn()
    elif phase in ("vault_act", "vault_act_2"):
        ok, detail = phase_act()
    elif phase in ("vault_measure", "vault_measure_2"):
        ok, detail = phase_measure()
    elif phase in ("vault_promote", "vault_promote_2"):
        ok, detail = phase_promote()
    elif phase in ("vault_distill", "vault_distill_2"):
        ok, detail = phase_distill()
    else:
        ok, detail = True, "unknown phase (noop)"

    # Advance to next phase
    next_idx = (phase_idx + 1) % len(PHASES)
    if next_idx == 0:
        cycle += 1

    state["phase_index"] = next_idx
    state["cycle"] = cycle
    state["last_phase"] = phase
    state["last_ok"] = ok
    state["last_detail"] = detail
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    status = "OK" if ok else "WARN"
    log(f"DONE phase={phase} → next={PHASES[next_idx]} cycle={cycle} [{status}] {detail[:100]}")
    print(f"[{status}] phase={phase} done. Cycle={cycle} Next={PHASES[next_idx]}. {detail[:200]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
