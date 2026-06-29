# Scripts

| Directory | Scripts | Purpose |
|-----------|---------|---------|
| `ci/` | `acceptance.sh` | Full E2E golden-path validation (used in CI) |
| `dev/` | `phase0-demo.sh` | Serve terminal with mock grid at `:8080` |
| `dev/` | `demo-local.sh` | Isolated temp-dir demo workflow |
| `dev/` | `ui-intent-smoke.sh` | Mirror smoke tests (no browser) |
| `dev/` | `collect-corpus.sh` | Corpus collection helper |
| `codex/` | `codex-ui-mirror-setup.sh` | Venv + baseline confusion test |
| `codex/` | `codex-ui-mirror-exec.sh` | Run or cloud-submit UI mirror task |
| `codex/` | `codex-parallel-launch.sh` | Launch 5 subsystem Codex Cloud tasks |

All scripts resolve the repo root from their subdirectory (`../..`).