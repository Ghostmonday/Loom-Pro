# ping!

You are in **AFK autonomy mode**. The user left the PC. A daemon will keep sending this ping until you finish the mission or they touch `.gaijinn/afk/stop`.

## Your job this turn

1. Read `.gaijinn/afk/mission.md` — that is the end goal and acceptance criteria.
2. Do **one meaningful chunk** of work toward it (implement, fix, test, merge, lint — whatever the mission needs).
3. Read `.gaijinn/composer-watcher-inbox.md` and vault council if the mission involves the vault.
4. Post a one-line progress note: `gaijinn council say --as cursor "AFK: …"` when you change something material.

## How YOU stop the daemon (required when done)

When **every** acceptance criterion in the mission is satisfied:

```bash
echo "DONE: <one-line summary>" > .gaijinn/afk/done
```

Write that file in the **same turn** you finish — do not wait for another ping. The daemon exits on the next check.

If you are blocked on the human (credentials, ambiguous product choice):

```bash
echo "BLOCKED: <what you need>" > .gaijinn/afk/blocked
```

Keep working on everything else; only write `done` when the full mission is complete.

## Rules

- `--yolo` is on: execute tools, don't ask permission.
- Prefer finishing the mission over meta-work.
- Do not start unrelated refactors.
- If tests exist for your change, run them.