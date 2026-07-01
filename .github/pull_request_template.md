## Summary

Briefly describe what this branch changes and why.

## Agent / Worktree

- Owner:
- Worktree path:
- Branch:
- Base commit:
- Scope:

## Changed Files

List the intentional files or directories touched by this branch.

## Verification

- [ ] `git status --short --branch` reviewed
- [ ] `git diff --check` passed
- [ ] Ruff check passed, or not applicable
- [ ] Ruff format check passed, or not applicable
- [ ] Targeted tests passed, or not applicable
- [ ] Full suite passed, or explicitly deferred with reason

Exact commands and counts:

```text
paste verification commands and exact pass/skip/warning counts here
```

## Isolation Check

- [ ] I worked only in my assigned worktree
- [ ] I did not switch the canonical `main` worktree away from `main`
- [ ] I did not modify another agent's worktree
- [ ] I did not merge, rebase, push, or delete branches outside this PR's scope
- [ ] Unrelated dirty or untracked files are listed below

Unrelated dirty/untracked files:

```text
none, or list exact paths and owner
```

## Risk Notes

- Behavior changes:
- Tests not run:
- Follow-up work:

## Merge Captain Checklist

- [ ] Branch scope matches the PR
- [ ] Diff reviewed for unrelated changes
- [ ] Required checks passed
- [ ] CODEOWNER review complete
- [ ] Merge order is compatible with other active worktrees
