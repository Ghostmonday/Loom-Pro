# Daemon Waker — Multi-Model Design Prompt

**Purpose:** Copy this entire document (or the **Prompt block** below) into Grok, ChatGPT, Gemini, or any headless agent. Each model proposes or critiques a **Daemon Waker** that keeps **Composer 2.5 (inside Grok Build beta)** executing toward V1 without Amir at the keyboard.

**Repo:** `Ghostmonday/Gaijinn` · **Council:** `~/.gaijinn/bridge/council.md`  
**Program lead:** Composer 2.5 @ Grok Build beta (this agent) · **Advisory:** ChatGPT Codex, Gemini, Hermes

---

## Prompt block (copy from here)

```markdown
# DESIGN BRIEF — Gaijinn Daemon Waker for Composer (Cursor)

You are an infrastructure architect. Design a **Daemon Waker** system that keeps **Composer 2.5 (Grok Build beta)** **running and productive** while the human (Amir) is away. This is not a generic cron job — it is a **wake → delegate → verify → sleep** loop across multiple AI runtimes.

## Identity (binding)

**Composer = Composer 2.5 running inside Grok Build beta** (`grok` CLI / headless sessions).  
This is **not** a separate Cursor Desktop window Amir must open. External models (ChatGPT, Gemini) advise; **Grok Build hosts the program lead.**

## Problem statement

Composer 2.5 is the **program lead** for shipping Gaijinn v1. Grok Build sessions:
- Do not persist indefinitely (context limits, turn limits, reboot)
- Need **daemon pings** (`grok --resume <sessionId>` or fresh `--prompt-file`) to continue from council/inbox
- Already have partial automation (`grok-afk-daemon.sh`) that pings but does not reliably resume sessions

We need a **Daemon Waker** that:
1. Detects when Composer is **idle/stale** (no council ack, inbox stale, tests red, sprint stuck)
2. **Wakes** Composer via a reliable channel (not human relay)
3. Passes a **minimal, actionable** prompt (one P0 task, evidence, done criteria)
4. **Verifies** progress before next wake (pytest delta, council post, git diff, merge metrics)
5. **Backoff** when blocked (credentials, ambiguous product choice) without spamming

## What already exists (do not reinvent blindly)

| Component | Role | Gap |
|-----------|------|-----|
| `scripts/dev/composer-autonomy-loop.sh` | 90–120s tick: council watcher + Hermes loop | Does **not** start Cursor/Composer |
| `scripts/dev/council_composer_watcher.py` | Reads `@composer` / `ACTION:*` from global + project council | Runs bash actions only; inbox is passive |
| `scripts/dev/grok-afk-daemon.sh` | Grok headless ping loop (`AFK_MODE=composer-lead`) | Grok relays to council; **not** Composer |
| `~/.gaijinn/bridge/council.md` | Single blackboard for all agents | Composer must read; no push to IDE |
| `.gaijinn/composer-watcher-inbox.md` | Pending pings for human to open Cursor | Requires Amir to open IDE |
| `.gaijinn/afk/mission.md` | V1 acceptance criteria | `done` file stops Grok daemon only |
| `gaijinn hermes` | DeepSeek orchestrator CLI | Vault/grid execution, not Composer |

**Control chain today:**
```
Amir (optional) → Grok AFK → council @composer → watcher inbox → Amir opens Cursor
Hermes cron → vault pipeline (parallel track)
Composer autonomy loop → bash scripts only
```

**Target chain:**
```
Daemon Waker → [wake Composer] → Composer executes → council ack → waker sleeps
                     ↑                                    ↓
              Grok/GPT/Gemini ping              verify: tests, merge, inbox cleared
```

## Environment constraints

- **OS:** Linux (Ubuntu-class), bash, Python 3.10+, systemd or cron acceptable
- **Composer:** Cursor Desktop — may support CLI/headless (`cursor`, `grok`, API TBD — propose options)
- **Council:** `gaijinn council say --global --as <author> "..."` — mandatory handoff bus
- **No Amir relay:** Agents coordinate via council only
- **Full automation:** Amir delegated gate-3; waker must not ask permission for routine wakes
- **Bone before flesh:** `gaijinn scan` / `analyze` / `plan` before grid-spawn
- **Secrets:** GitHub token in keyring; Codex Cloud env currently ERROR — design local fallback

## V1 north star (waker optimizes for this)

Composer writes `.gaijinn/afk/done` when ALL true:
1. Full `pytest` green (no collection errors)
2. `test_ui_intent_smoke.py` + PKM confusion_count == 0
3. `scripts/dev/phase0-demo.sh` serves terminal `:8080` mock grid
4. Orchestrate API prepare → swarm → grid status works
5. Merge phase wired in terminal or gap closed
6. Council V1 ship note with commit + demo URL

## Your deliverable

Produce a **design document** with these sections:

### 1. Architecture diagram
ASCII or Mermaid: Waker, Composer, Council, Grok relay, Hermes, watchdog timers.

### 2. Wake channels (ranked)
Evaluate at least 3 options with pros/cons:
- A) Cursor CLI / Composer headless (if exists or plausible)
- B) Council + inbox + `notify-send` + file trigger (`.gaijinn/composer-wake.json`)
- C) External model ping (Grok/ChatGPT/Gemini) that posts `@composer ACTION:wake` and runs bounded local script
- D) systemd user service + `gaijinn` subprocess chain
- E) Your proposal

### 3. Stale detection
Concrete signals + thresholds:
- Council seq ack lag (Composer last post vs Grok ping)
- Inbox age (`composer-watcher-inbox.md` mtime)
- Hermes phase stuck (same phase > N ticks)
- pytest failure count unchanged > N wakes
- git dirty with no commits > N hours

### 4. Wake payload schema
JSON or markdown template for each wake (max 2KB):
```json
{
  "wake_id": "uuid",
  "priority": "P0",
  "task": "one sentence",
  "evidence": {},
  "files": [],
  "verify_commands": [],
  "stop_when": "council post contains DONE or pytest exit 0"
}
```

### 5. Multi-model division of labor
Table: which model does what (Grok ping, GPT design review, Gemini watchdog critique, Composer implement).

### 6. Failure modes + backoff
Session expired, IDE closed, grok exit 1, merge convergence drop, duplicate wake storms.

### 7. Implementation plan (PR-sized slices)
Ordered list of 5–8 PRs with files to touch under `scripts/dev/` and `.gaijinn/`.

### 8. Acceptance tests
How we know the waker works (daemon integration test, fake stale inbox → wake → ack within 5 min).

## Rules for your response

- Be **specific to Gaijinn paths** listed above.
- Prefer **cron-safe, idempotent** steps (lock files, pid files).
- Do not propose Amir as relay.
- Call out **Cursor/Composer headless gaps** honestly — if unknown, propose discovery spike PR #1.
- Keep scope to **waker orchestration**; do not redesign the whole vault civilization.
- End with **3 open questions** for the other models to debate in council.

## Context files to reference (if you have repo access)

- `scripts/dev/composer-autonomy-loop.sh`
- `scripts/dev/council_composer_watcher.py`
- `scripts/dev/grok-afk-daemon.sh`
- `scripts/dev/afk-ping-composer-lead.md`
- `.gaijinn/afk/mission.md`
- `docs/architecture/terminal-bridge.md`
- `ui/gaijinn-ui-intent-map.json` (`_ai_blueprint`)

Begin your design.
```

---

## How to run this across models

### Round 1 — Independent designs (parallel)

| Model | How to run | Save output to |
|-------|------------|----------------|
| **Grok** | `grok --prompt-file docs/architecture/daemon-waker-design-prompt.md --always-approve --cwd .` | `.gaijinn/design/daemon-waker-grok.md` |
| **ChatGPT** | Paste Prompt block into project chat (Gaijinn env) | `.gaijinn/design/daemon-waker-chatgpt.md` |
| **Gemini** | Paste Prompt block + attach this file | `.gaijinn/design/daemon-waker-gemini.md` |
| **Composer** | Implement winning synthesis | `scripts/dev/composer-waker-daemon.sh` (future) |

### Round 2 — Cross-review (sequential)

Give each model the other two outputs:

```markdown
You previously designed a Daemon Waker. Review these competing designs:
- [paste grok output]
- [paste chatgpt output]

Synthesize: what to keep, what to reject, final architecture. Post conflicts as council-ready ADR bullets.
```

### Round 3 — Council merge

```bash
gaijinn council say --global --as cursor "DAEMON WAKER ADR: <one paragraph synthesis>. PR plan: <ordered list>. Blockers: <cursor headless unknowns>."
```

---

## Launcher script (optional)

```bash
# Extract prompt only (no markdown wrapper)
sed -n '/^```markdown$/,/^```$/p' docs/architecture/daemon-waker-design-prompt.md | sed '1d;$d' > .gaijinn/afk/daemon-waker-prompt.txt

# Grok design pass
mkdir -p .gaijinn/design
grok --prompt-file .gaijinn/afk/daemon-waker-prompt.txt \
  --always-approve --cwd /home/ghost-monday/Desktop/Gaijinn \
  --model grok-build --max-turns 30 \
  > .gaijinn/design/daemon-waker-grok.md
```

---

## Success criteria for the design phase

- [ ] Three model outputs saved under `.gaijinn/design/`
- [ ] Consensus wake channel chosen (with fallback)
- [ ] `ACTION:wake` added to `council_composer_watcher.py` (implementation PR)
- [ ] Integration test or dry-run script `scripts/dev/composer-waker-dry-run.sh`
- [ ] Council ADR posted; Amir not required to relay between models

---

_Amir: paste the Prompt block into any model, or run the launcher. Composer implements the winning design autonomously._