# DeepSeek / Claw X — SOURCE DUMP RULES (read before any dump)

## You broke it last time. Do not do that again.

The Desktop file `gaijinn-source-dump.txt` was **corrupted** because you stuffed **binary data into a text file**:

- **79,638 null bytes**
- **705 binary sections** (git objects, SQLite, `.coverage`)
- Editors show garbage; the whole file is unusable

That happened because you dumped `.gaijinn/sessions/*/.git/objects/*` and other binaries **as if they were UTF-8 text**. They are not. Never improvise a dump script.

---

## The rule

| DO | DON'T |
|----|-------|
| Run the official script | Write your own `find \| cat` one-liner |
| Text source only | Embed `.git/objects`, `.db`, `.coverage`, images |
| Skip `.gaijinn/sessions/` entirely | Dump worker session trees |
| Verify **0 null bytes** after | Ship a file grep calls "binary" |
| `[SKIPPED: binary]` if unsure | Read bytes and hope |

---

## The only approved command

```bash
cd ~/Desktop/gaijinn
bash scripts/dev/source-dump.sh ~/Desktop/gaijinn-source-dump.txt
```

Script must print: `0 null bytes`. If it does not, **stop and report** — do not give the user the file.

---

## What belongs in a source dump

**Include:** `.py`, `.json`, `.md`, `.sh`, `.toml`, intent maps, `docs/`, `tests/`, `aoc-cli/`, `aoc_supervisor/`

**Never include:**

- `.git/` (anywhere, including nested under `.gaijinn/sessions/`)
- `.venv/`, `__pycache__/`, `node_modules/`
- `vaults/` (duplicate worker copies)
- `dist/`, `.gaijinn/sessions/`, `.gaijinn/codex/` logs
- `.coverage`, `*.db`, `*.sqlite`, `*.pyc`, `*.png`, `*.pdf`, `*.zip`

---

## Format (script already does this)

```text
================================================================================
FILE: path/to/file.py
================================================================================
<utf-8 contents>
```

One header per file. No JSON wrapping. No base64 unless user explicitly asks for a **separate** archive.

---

## Verification you must run and report

```bash
python3 -c "
from pathlib import Path
p = Path('$HOME/Desktop/gaijinn-source-dump.txt')
b = p.read_bytes()
assert b.count(b'\\x00') == 0, 'NULL BYTES — DUMP INVALID'
print(f'OK: {p.stat().st_size/1024/1024:.2f} MB, null bytes: 0')
"
```

---

## If user asks for "full repo dump"

1. Run `scripts/dev/source-dump.sh`
2. Offer `gaijinn-source-dump.txt.gz` (compressed)
3. Report file count + MB + **null byte check passed**
4. Do **not** commit the dump to git

---

## Escalate to user when

- Script fails
- Null bytes > 0
- User wants binaries → suggest `tar.gz` of repo with excludes, not text mash

**Improvising dumps is how you waste the user's time and tokens. Use the script.**