---
name: afk-daemon
description: >
  Start or stop the non-stop Grok AFK daemon so the agent keeps working while the
  user is away and stops itself by writing .gaijinn/afk/done when the mission is
  complete. Use when the user says AFK, leave PC, keep working, ping daemon,
  autonomy daemon, or wants the agent to continue until a milestone.
metadata:
  short-description: "AFK ping daemon — agent stops itself when done"
---

# AFK daemon

## What it is

A shell loop that runs `grok -p "ping!"` on an interval. Each ping is one agent turn toward `.gaijinn/afk/mission.md`. **The agent stops the daemon** by writing `.gaijinn/afk/done`. The user can abort anytime with `.gaijinn/afk/stop`.

## Before starting (do this with the user once)

1. Ensure `.gaijinn/afk/mission.md` exists with clear acceptance criteria.
2. Copy from `.gaijinn/afk/mission.example.md` if missing.
3. Confirm `grok` is on PATH and `XAI_API_KEY` or login is valid for headless.

## Start

```bash
bash scripts/dev/grok-afk-daemon.sh
```

Background (user leaving PC):

```bash
nohup bash scripts/dev/grok-afk-daemon.sh >> .gaijinn/afk/daemon.log 2>&1 &
```

## Stop

| Who | How |
|-----|-----|
| User | `touch .gaijinn/afk/stop` |
| User | `kill $(cat .gaijinn/afk/daemon.pid)` |
| Agent | `echo "DONE: …" > .gaijinn/afk/done` when mission complete |

## Env

| Variable | Default | Meaning |
|----------|---------|---------|
| `AFK_INTERVAL_SEC` | 90 | Seconds between pings |
| `AFK_MAX_TURNS` | 60 | Max tool turns per ping |
| `AFK_MODEL` | grok-build | Headless model |

## Agent obligations every ping

1. Read mission.md
2. Ship one chunk of progress
3. Write `done` when **all** acceptance criteria met — same turn, no waiting

## Logs

`tail -f .gaijinn/afk/daemon.log`

Session resume state: `.gaijinn/afk/session.json`