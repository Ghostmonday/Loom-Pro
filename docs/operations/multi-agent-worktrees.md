# Multi-Agent Worktree Protocol

This project may have Copilot, Codex, DeepSeek, and other assistants active at
the same time. Git branches alone are not enough isolation when multiple tools
are attached to one IDE folder. Use separate worktrees.

## Current Layout

| Path | Branch | Role |
|------|--------|------|
| `/home/ghostmonday/Desktop/Loom` | `main` | Canonical integration worktree |
| `/home/ghostmonday/Desktop/Loom-codex` | `codex/a3-d2-proposal-boundary` | Codex implementation worktree |
| `/home/ghostmonday/Desktop/Loom-deepseek` | `audit/code-hygiene-pass` | DeepSeek audit worktree |

`origin/main` is the only canonical remote branch unless the user explicitly
asks for a review branch to be pushed.

## Why This Exists

One git worktree can have only one checked-out branch. If two agents share the
same folder, a branch switch by one agent changes the filesystem under the
other agent. That breaks trust in diffs, tests, and IDE state.

Separate worktrees give each agent its own checked-out branch while sharing the
same repository history.

## Agent Rules

1. Work only in your assigned worktree.
2. Do not switch branches in `/home/ghostmonday/Desktop/Loom`.
3. Do not edit another agent's worktree.
4. Do not merge or rebase unless explicitly assigned.
5. Do not push local agent branches unless explicitly assigned.
6. Preserve untracked files unless the owner says they are disposable.
7. Keep changes scoped to the branch mission.

## Start Checklist

Run this before touching files:

```bash
pwd
git status --short --branch
git worktree list
git log --oneline -n 3
```

Then confirm:

- path matches assignment;
- branch matches assignment;
- dirty files are expected;
- task scope matches the branch name.

If any item is unclear, stop and report.

## Creating A New Agent Worktree

From the canonical repo:

```bash
cd /home/ghostmonday/Desktop/Loom
git fetch --prune origin
git worktree add -b <owner>/<short-task-name> /home/ghostmonday/Desktop/Loom-<owner> main
```

Examples:

```bash
git worktree add -b codex/a3-d2-proposal-boundary /home/ghostmonday/Desktop/Loom-codex main
git worktree add -b audit/code-hygiene-pass /home/ghostmonday/Desktop/Loom-deepseek main
```

## Integration Rules

Only integrate one branch into `main` at a time.

Before merging, collect:

- `git status --short --branch`;
- `git diff --stat main...HEAD`;
- changed file list;
- test commands and exact pass/skip/warning counts;
- `git diff --check`;
- Ruff check and format check for touched Python files;
- unresolved risks or skipped verification.

Merge from `/home/ghostmonday/Desktop/Loom` only:

```bash
cd /home/ghostmonday/Desktop/Loom
git switch main
git pull --ff-only origin main
git merge --no-ff <branch-name>
```

After merge, rerun the verification appropriate to the touched scope. Push
`main` only after the merged result is clean.

## Keeping Worktrees Current

If `main` receives an operations-only update that every agent should inherit,
fast-forward each clean agent worktree:

```bash
cd /home/ghostmonday/Desktop/Loom-codex
git merge --ff-only main

cd /home/ghostmonday/Desktop/Loom-deepseek
git merge --ff-only main
```

If a worktree has local commits, use an intentional merge from `main` and report
the merge commit. If it has unrelated dirty files, stop before updating it.

## Cleaning Up Finished Worktrees

After a branch is merged and pushed:

```bash
cd /home/ghostmonday/Desktop/Loom
git worktree remove /home/ghostmonday/Desktop/Loom-<owner>
git branch -d <branch-name>
```

Delete remote branches only after confirming the merged commit exists on
`origin/main`.

## Current Ownership Notes

- Codex owns A3/D2 LLM Proposal Boundary planning and implementation work in
  `Loom-codex`.
- DeepSeek owns code-hygiene audit reporting in `Loom-deepseek`.
- The canonical `Loom` folder is for integration and should stay clean.
