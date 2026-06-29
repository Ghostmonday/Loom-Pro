# Codex Fullpass — Hermes Agent Briefing

You are one of 6 Hermes agents running the Codex Fullpass on Gaijinn. Your job: implement ONE slice of the fullpass, then report back.

## Shared Context

- **Repo:** `~/Desktop/Gaijinn` — cd there first
- **Baseline:** tag `pre-codex-fullpass-6361ad5`, branch `main`
- **Orchestrator:** Hermes (#35 in council)
- **Implementer:** Codex CLI (`codex exec -C . -s workspace-write`)
- **Cursor is FROZEN** on backend code — no edits to `aoc-cli/`, `aoc_supervisor/`, or backend `tests/` except by Codex
- **No user-facing quality gates** — `prompt_coverage` is internal dev tooling

## Your Protocol (every slice)

1. **Read your task doc** — the slice-specific file passed to you
2. **Run codex exec** — feed the task doc as the prompt:
   ```
   codex exec -C . -s workspace-write "$(cat docs/codex-tasks/<your-task-file>)"
   ```
3. **Run acceptance** — the slice-specific test command
4. **Full suite check** — `python3 -m pytest tests/ -q` (no regressions below current baseline)
5. **Write report** — save to `.gaijinn/codex/slice-NN-report.md`
6. **Council post** — `gaijinn council say --as hermes --id hermes-slice-N "Slice N complete: summary, test count, commit hash"`
7. **Commit & push** — `git add -A && git commit -m 'codex-slice-NN: description' && git push origin main`
8. **Report back** to the user that your slice is done

## Rules

- Small focused diffs only — no drive-by refactors
- Do NOT re-implement what's already shipped (inference pipelines, post-24 audit fixes)
- If conflicts arise with another slice's work, note them in the report — do not force merge
- If Codex fails, retry once, then report the error
- Dogfood editor (Rust/Go test editor) is NOT ready — do not start it

## Council

All agents read and post to `.gaijinn/bridge/council.md` before acting and after completing. One shared thread — no relay between AIs.
