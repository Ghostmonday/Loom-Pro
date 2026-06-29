---
id: "PROJ-DEEPSEEK-SETUP"
type: "Project"
status: "active"
priority: "P1"
tags:
  - Project
  - Domain/Infrastructure
---

# DeepSeek + Codex setup (gaijinn-memory-fs)

Gaijinn grid workers use **Codex** with model `deepseek-v4-flash`. Codex speaks the OpenAI **Responses** protocol; DeepSeek's native API is **Chat Completions** — so you need a **bridge profile** in `~/.codex/config.toml`, not a bare `base_url = https://api.deepseek.com`.

## 1. API key (shell)

```bash
export DEEPSEEK_API_KEY="sk-..."   # from https://platform.deepseek.com/api_keys
```

Persist in `~/.bashrc` or use a secret manager. Never commit the key to the vault.

## 2. Codex profile (`~/.codex/config.toml`)

Append (or merge) this block. Pick **one** bridge:

### Option A — Local CCX gateway (recommended for control)

```toml
[profiles.deepseek]
model = "deepseek-v4-flash"
model_provider = "ccx-bridge"

[model_providers.ccx-bridge]
name = "Local CCX Gateway"
base_url = "http://localhost:3000/v1"
env_key = "DEEPSEEK_API_KEY"
```

Start your CCX gateway first, then:

```bash
export DEEPSEEK_API_KEY="sk-..."
codex exec --profile deepseek -m deepseek-v4-flash -C . -s workspace-write "smoke test"
```

### Option B — OpenRouter BYOK

```toml
[profiles.deepseek]
model = "deepseek/deepseek-v4-flash"
model_provider = "openrouter"

[model_providers.openrouter]
name = "OpenRouter"
base_url = "https://openrouter.ai/api/v1"
env_key = "OPENROUTER_API_KEY"
```

Bind your DeepSeek key in the OpenRouter dashboard (BYOK). Shell uses `OPENROUTER_API_KEY`, not `DEEPSEEK_API_KEY`.

## 3. Gaijinn binding

This vault's `.gaijinn/project.json` sets:

```json
"executor_profile": {
  "grid_executor": "deepseek",
  "grid_model": "deepseek-v4-flash",
  "hermes_model": "deepseek-v4-flash",
  "codex_profile": "deepseek"
}
```

Grid spawn runs: `codex exec --profile deepseek -m deepseek-v4-flash ...`

Override profile for one session: `export GAIJINN_CODEX_PROFILE=deepseek-openrouter`

## 4. Hermes orchestrator

```bash
cd vaults/gaijinn-memory-fs
hermes model    # select provider + deepseek-v4-flash interactively once
gaijinn hermes -i
```

Or one-shot: `hermes -m deepseek-v4-flash -z "status check"`

Hermes reads `hermes_model` from project.json when launched via `gaijinn hermes`.

## 5. Verify

```bash
cd vaults/gaijinn-memory-fs
export DEEPSEEK_API_KEY="sk-..."
codex exec --profile deepseek -m deepseek-v4-flash -C . -s workspace-write "Reply OK only"
python -m pytest ../../tests/test_grid_executor.py -q -k deepseek
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `401` | Wrong key or wrong `env_key` in profile |
| `404` / model not found | Use `deepseek-v4-flash`; check gateway model list |
| Codex still uses OpenAI | `codex logout`, then `--profile deepseek` |
| Tool/patch parse errors | Bridge incomplete — try CCX or OpenRouter, not direct DeepSeek URL |

## Sprint validation (WU-ec692d62, 2026-06-18)

- Documented merge-compounding: Codex workers may return zero-delta when `completion-ledger.json` already holds the WU `content_hash` — disposition `already_merged`, not `blocked`.
- Canonical monorepo path: `/home/ghost-monday/Desktop/Gaijinn` (not workspace duplicate).
- Cross-ref: [[20_Projects/deepseek-hermes-setup.md]] for Hermes orchestrator config.

## Related

- [[raw/constitution-v0-section-xiii]]
- [[30_Decisions/ADR-002-dual-invariant-domains]]
- Example profile snippet: `.agents/codex-deepseek.toml.example`