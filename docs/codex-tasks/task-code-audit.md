# Codex Task — Post-Merge Demo Code Audit (read-only)

## Objective
Audit `main` after merge-loop wiring (`d52264a` + `4073264`). Produce a structured report for Amir — **do not edit application source**.

## Working directory
`/home/ghostmonday/Desktop/Loom`

## Setup
```bash
cd /home/ghostmonday/Desktop/Loom
export GAIJINN_MOCK_GRID=1
export PYTHONPATH="aoc-cli:aoc_supervisor:${PYTHONPATH}"
git status -sb
git log -5 --oneline
```

## Files you MAY create/edit (only these)
- `.gaijinn/codex/code-audit-report.md`

## Files you MUST NOT edit
- Any file under `aoc-cli/`, `aoc_supervisor/`, `ui/`, `tests/`, `scripts/`, `docs/` (except reading)
- `.gaijinn/project.json`, council bridge files

## Audit scope (read code + run checks)
1. **Demo loop completeness**: intent → prepare → swarm → spawn → complete → merge → deliverable
2. **Merge pipeline**: API endpoints, orchestrate `run_merge`, terminal `runPostSprintMerge`, evaluator `evaluate_merge`
3. **Intent map alignment**: `ui/loom-ui-intent-map.json` vs terminal + driver
4. **Test coverage gaps**: what smoke/e2e paths are untested
5. **Loose ends**: uncommitted artifacts, stale processes, TODO/GAPS comments, dead code
6. **Demo blockers for buyers**: top 5 risks ranked by severity
7. **Security/ops**: secrets in repo, billing edge cases, subprocess/git safety

## Verification (run, do not fix failures)
```bash
.venv/bin/python -m pytest -q
bash scripts/dev/ui-intent-smoke.sh 2>/dev/null || true
```

## Report format (write to `.gaijinn/codex/code-audit-report.md`)
```markdown
# Gaijinn Code Audit — <date>
## Executive summary (3 bullets)
## Demo loop status (table: layer | shipped | gap)
## Findings (severity: critical/high/medium/low)
## Test results
## Recommended next tasks (ordered, max 8)
## Files reviewed (list)
```

## Acceptance
1. Report file exists with all sections
2. Full pytest run captured in report (pass/fail count)
3. Zero source file diffs outside `.gaijinn/codex/code-audit-report.md`
4. One-paragraph summary in your final message

## Constraints
- **Audit only** — no fixes, no commits
- Do not push to remote
- Do not spawn subagents