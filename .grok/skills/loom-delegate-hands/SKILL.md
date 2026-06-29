---
name: loom-delegate-hands
description: Delegate grep/patch/pytest/commit work to DeepSeek Flash subagents via spawn_subagent. Composer stays on Grok for gates only. Use for parallel investigation, mechanical fixes, test runs, and queue updates.
---

# Loom delegate hands (DeepSeek Flash)

## When to delegate (default for grunt work)

Spawn `hands` or `general-purpose` subagents (routed to `deepseek-flash` in `~/.grok/config.toml`) for:

- repo-wide grep / file discovery
- mechanical patches (imports, renames, compat shims)
- pytest / CI verify commands
- git status, commit, push on a named branch
- queue doc row updates after verify

## When NOT to delegate (Composer / Grok stays)

- critique approval and intent-map design
- architecture forks, merge conflict strategy
- user green-light gates
- second-failed-slice escalation

## Spawn pattern

Launch **parallel** subagents when tasks are independent:

```
spawn_subagent — [hands] grep UTC imports
spawn_subagent — [hands] patch timezone.utc
spawn_subagent — [hands] run pytest verify
```

Synthesize results, single commit, one SESSION BRIEF.

## Env

Requires `DEEPSEEK_API_KEY` in `~/.grok/secrets.env` (sourced from `~/.bashrc`).