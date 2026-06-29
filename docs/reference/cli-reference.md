# Gaijinn CLI Reference

Run commands from the project root you want Gaijinn to manage. Most project artifacts are written under `.gaijinn/`.

## `gaijinn activate`

Purpose: store local activation metadata. This command does not contact a remote license service.

Syntax:

```bash
gaijinn activate LICENSE_KEY
```

Options: none.

Artifacts:

- Writes `.gaijinn/license.json`.
- Creates `.gaijinn/` if needed.

Examples:

```bash
gaijinn activate local-dev
gaijinn activate GAIJINN-TEAM-XXXXXXXX
```

## `gaijinn init`

Purpose: initialize Gaijinn state for the current checkout.

Syntax:

```bash
gaijinn init [OPTIONS] "PROJECT PROMPT"
```

Options:

- `--force`: overwrite existing `.gaijinn/project.json` and seed state.
- `--blueprint-template`: write editable `.gaijinn/blueprint.md`.
- `--agent-files / --no-agent-files`: add or skip Gaijinn guidance blocks in `CLAUDE.md` and `.cursorrules`.

Artifacts:

- Writes `.gaijinn/project.json`.
- Writes `.gaijinn/GENERATE_BLUEPRINT.md`.
- Optionally writes `.gaijinn/blueprint.md`.
- Optionally updates `CLAUDE.md` and `.cursorrules`.

Examples:

```bash
gaijinn init "Build a REST API with Postgres and JWT auth"
gaijinn init --no-agent-files "Ship a CLI task tracker with tests"
gaijinn init --force --blueprint-template "Refactor billing safely"
```

## `gaijinn scan`

Purpose: scan a directory into a deterministic graph for analysis.

Syntax:

```bash
gaijinn scan PATH
```

Options: none.

Artifacts:

- Writes `.gaijinn/graph.json` or the graph path stored in project state.
- Honors common generated directories and basic `.gitignore` patterns.

Examples:

```bash
gaijinn scan .
gaijinn scan examples/tiny-python-service
```

## `gaijinn analyze`

Purpose: compute gravity, curvature, rejected nodes, and Shadow Bridges from a graph.

Syntax:

```bash
gaijinn analyze [OPTIONS]
```

Options:

- `--graph PATH`, `-g PATH`: input graph JSON path. Defaults to `.gaijinn/graph.json`.
- `--output PATH`, `-o PATH`: metrics output path. Defaults to `.gaijinn/metrics_manifest.json`.
- `--json`: print a stable machine-readable summary.
- `--fail-on-rejection`: exit `2` when any node is below the gravity hard floor.
- `--fail-on-shadow-bridge`: exit `3` when any edge is flagged as a Shadow Bridge.

Artifacts:

- Writes `.gaijinn/metrics_manifest.json` by default.
- Updates project metrics path when a custom `.gaijinn/...` output path is used.

Examples:

```bash
gaijinn analyze
gaijinn analyze --json
gaijinn analyze --graph graph.json --output metrics.json
gaijinn analyze --fail-on-rejection --fail-on-shadow-bridge
```

## `gaijinn compile-prompt`

Purpose: compile the project prompt into a worker-scoped Agent Intent Vector.

Syntax:

```bash
gaijinn compile-prompt [OPTIONS]
```

Options:

- `--json`: print a stable machine-readable compile summary.

Artifacts:

- Writes `.gaijinn/giv.json`.
- Writes `.gaijinn/intent.txt`.

Examples:

```bash
gaijinn compile-prompt
gaijinn compile-prompt --json
```

## `gaijinn plan`

Purpose: generate a deterministic implementation blueprint from graph, metrics, and GIV state.

Syntax:

```bash
gaijinn plan [OPTIONS]
```

Options:

- `--workers N`, `-w N`: intended worker count for the plan summary. Default: `2`.
- `--max-risk low|medium|high`: reject generated plans above this risk. Default: `high`.
- `--json`: print the generated blueprint JSON after writing artifacts.

Artifacts:

- Writes `.gaijinn/blueprint.json`.
- Writes `.gaijinn/blueprint.md`.

Examples:

```bash
gaijinn plan --workers 2
gaijinn plan --workers 4 --max-risk medium
gaijinn plan --json
```

## `gaijinn run-grid`

Purpose: create isolated worker handoff directories.

Syntax:

```bash
gaijinn run-grid --workers N [OPTIONS]
```

Options:

- `--workers N`, `-w N`: number of worker directories to create. Required; must be at least `1`.
- `--force`: overwrite existing worker directories and manifest.

Artifacts:

- Writes `.gaijinn/workers/manifest.json`.
- Writes `.gaijinn/workers/worker-*/intent.txt`, `giv.json`, `README.md`, and `metadata.json`.
- Uses Git worktrees when running inside a clean Git worktree; otherwise copies the checkout into worker directories.

Examples:

```bash
gaijinn run-grid --workers 2
gaijinn run-grid --workers 3 --force
```

## `gaijinn grid-spawn`

Purpose: spawn Grok Build agents for each worker cell and run an atomic sprint to completion.

Syntax:

```bash
gaijinn grid-spawn --workers N [OPTIONS]
```

Options:

- `--workers N`, `-w N`: number of workers to spawn. Required; must match the `run-grid` count.
- `--model MODEL`, `-m MODEL`: Grok Build model for all agents. Default: `grok-composer-2.5-fast`. All agents use the same model.

Prerequisites:

- `gaijinn run-grid` must have created worker handoffs.
- Metrics must pass grid readiness checks (`gaijinn analyze` with no rejections or shadow bridges).
- `grok` executable must be on `PATH`.

Artifacts:

- Writes `.gaijinn/workers/worker-*/output.log` with raw Grok Build stdout.
- Updates `.gaijinn/workers/manifest.json` sprint status on completion.

Notes:

- Atomic sprint — no cancel once spawned.
- Blocked when grid readiness fails; run `gaijinn doctor` to check `grok` availability.

Examples:

```bash
gaijinn grid-spawn --workers 2
gaijinn grid-spawn --workers 2 --model grok-composer-2.5-fast
```

## `gaijinn status`

Purpose: summarize current Gaijinn project state.

Syntax:

```bash
gaijinn status [OPTIONS]
```

Options:

- `--json`: print a stable machine-readable status payload.
- `--strict`: exit `2` when state is degraded or tripped.

Artifacts: reads `.gaijinn/` state; writes nothing.

Examples:

```bash
gaijinn status
gaijinn status --json --strict
```

## `gaijinn doctor`

Purpose: diagnose installation health, dependency imports, Git availability, `.gaijinn/` writability, and artifact validity.

Syntax:

```bash
gaijinn doctor [OPTIONS]
```

Options:

- `--json`: print stable machine-readable diagnostics.
- `--strict`: exit `2` when any hard diagnostic fails.

Artifacts:

- Creates `.gaijinn/` if missing to verify writability.
- Reads existing artifacts and reports missing artifacts as warnings.

Examples:

```bash
gaijinn doctor
gaijinn doctor --json
gaijinn doctor --strict
```

## `gaijinn monitor`

Purpose: watch a metrics manifest and run supervisor validation when it changes.

Syntax:

```bash
gaijinn monitor [OPTIONS]
```

Options:

- `--manifest PATH`, `-m PATH`: metrics manifest to watch. Default: `.gaijinn/metrics_manifest.json`.
- `--poll-interval SECONDS`: polling interval. Default: `1.0`; minimum: `0.1`.

Artifacts: reads the metrics manifest; writes nothing.

Examples:

```bash
gaijinn monitor
gaijinn monitor --manifest .gaijinn/metrics_manifest.json --poll-interval 0.5
```

## `gaijinn version`

Purpose: print the installed Gaijinn version.

Syntax:

```bash
gaijinn version [OPTIONS]
```

Options:

- `--json`: print version information as JSON.

Artifacts: none.

Examples:

```bash
gaijinn version
gaijinn version --json
```

