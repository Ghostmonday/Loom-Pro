# Agent Execution Rules - Loom Workspace

This repository supports concurrent AI work through separate git worktrees.
Do not simulate isolation by switching branches inside another agent's folder.

## Canonical Worktree

- `/home/ghostmonday/Desktop/Loom` is the canonical `main` worktree.
- Keep it clean and synced with `origin/main`.
- Do not perform feature work here unless the user explicitly assigns this folder.
- Use this folder for final integration, verification, and merge checkpoints.

## Active Agent Worktrees

- Codex worktree: `/home/ghostmonday/Desktop/Loom-codex`
- DeepSeek worktree: `/home/ghostmonday/Desktop/Loom-deepseek`

Each agent should work only inside its assigned worktree. If you need a new
branch, create a new sibling worktree instead of switching branches in place.

## Required Start Check

Before making changes, run:

```bash
pwd
git status --short --branch
git worktree list
```

Stop and report if:

- you are in the wrong worktree;
- the branch does not match your assignment;
- there are dirty files you did not create;
- the task would require editing another agent's worktree.

## Branch And Merge Discipline

- One branch has one owner and one scope.
- Do not merge, rebase, push, or delete branches unless the user or merge
  captain explicitly asks.
- Do not switch the canonical `main` worktree away from `main`.
- Never use destructive cleanup commands to "fix" another agent's state.
- Preserve unrelated dirty or untracked files.

## Merge Gates

Before any agent branch is merged into `main`, report:

- changed files;
- intended scope;
- tests run and exact result counts;
- `git diff --check`;
- Ruff check/format check when Python files changed;
- any remaining dirty or untracked files.

Full details live in
[`docs/operations/multi-agent-worktrees.md`](docs/operations/multi-agent-worktrees.md).
