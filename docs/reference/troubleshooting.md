# Troubleshooting

## `gaijinn: command not found`

Symptom: the shell cannot find `gaijinn`.

Cause: the package is not installed, or the Python scripts directory is not on `PATH`.

Fix: run `pip install -e .` from the repository root, then reopen the shell if needed.

Prevention: use a project virtual environment and activate it before running Gaijinn.

## `missing .gaijinn/project.json`

Symptom: commands such as `compile-prompt`, `plan`, or `run-grid` fail before doing work.

Cause: the project has not been initialized.

Fix: run `gaijinn init "PROJECT PROMPT"`.

Prevention: start every new project workflow with `gaijinn init`.

## `.gaijinn/project.json already exists`

Symptom: `gaijinn init` refuses to overwrite state.

Cause: Gaijinn protects existing project metadata by default.

Fix: run `gaijinn init --force "PROJECT PROMPT"` only when replacing the existing state is intended.

Prevention: inspect `.gaijinn/project.json` before using `--force`.

## `invalid JSON in .gaijinn/project.json`

Symptom: commands report a JSON line and column error.

Cause: project state was manually edited into invalid JSON.

Fix: repair the JSON or rerun `gaijinn init --force "PROJECT PROMPT"`.

Prevention: edit JSON with tooling that validates before saving.

## `missing .gaijinn/intent.txt`

Symptom: `gaijinn run-grid` fails with a missing compiled intent.

Cause: `compile-prompt` has not been run since initialization.

Fix: run `gaijinn compile-prompt`.

Prevention: follow the standard order: `init`, `scan`, `analyze`, `compile-prompt`, `plan`, `run-grid`.

## `missing graph JSON`

Symptom: `gaijinn analyze` cannot find `.gaijinn/graph.json`.

Cause: no scan has been run, or a custom graph path was not passed.

Fix: run `gaijinn scan .`, or pass `gaijinn analyze --graph PATH`.

Prevention: scan after source files change and before analysis.

## `graph JSON contains no nodes`

Symptom: analysis fails because the graph is empty.

Cause: the scanned path had no usable files, or ignore rules excluded everything.

Fix: scan the intended project root and check `.gitignore` patterns.

Prevention: run `gaijinn scan .` from the repository root unless intentionally scanning a subdirectory.

## Automatic Rejection

Symptom: `gaijinn analyze --fail-on-rejection` exits `2`, or `status --strict` reports degraded state.

Cause: one or more nodes scored below the gravity hard floor.

Fix: inspect `gravity_meta.rejected_nodes` in `.gaijinn/metrics_manifest.json`, then add context, split the task, or avoid assigning that node to parallel work.

Prevention: keep high-capability, low-context changes out of broad worker scopes.

## Shadow Bridge Detected

Symptom: `gaijinn analyze --fail-on-shadow-bridge` exits `3`, or status shows a nonzero Shadow Bridge count.

Cause: an edge has negative curvature or a risky transition.

Fix: inspect `curvature_meta.shadow_bridges`, isolate the bridge file, and regenerate the plan.

Prevention: keep high-risk transitions explicit in the graph and isolate sensitive paths.

## `run-grid` Says Worker State Already Exists

Symptom: `gaijinn run-grid --workers N` refuses to continue.

Cause: `.gaijinn/workers/` already contains worker directories or a manifest.

Fix: run `gaijinn run-grid --workers N --force` when overwriting old handoffs is intended.

Prevention: archive or remove old worker outputs before creating a new grid.

## Git Worktree Creation Fails

Symptom: `run-grid` fails while adding a Git worktree.

Cause: branch conflicts, existing worktree metadata, or Git restrictions.

Fix: remove stale worktrees with `git worktree prune`, choose `--force` for stale Gaijinn directories, or run from a dirty tree to use copy mode.

Prevention: keep worker branches and worktrees cleaned up after merging or discarding work.

## Doctor Reports Missing Artifacts

Symptom: `gaijinn doctor` prints `WARN` for project, graph, metrics, GIV, blueprint, or worker manifest.

Cause: the workflow has not produced those artifacts yet.

Fix: run the next missing workflow command shown in the diagnostic detail.

Prevention: use `scripts/ci/acceptance.sh` or the README quickstart to verify a full local run.

## Doctor Strict Exits Nonzero

Symptom: `gaijinn doctor --strict` exits `2`.

Cause: a hard diagnostic failed, such as an unsupported Python version, missing dependency import, unwritable `.gaijinn/`, or invalid existing artifact.

Fix: read the `FAIL` row, repair the reported environment or artifact, then rerun `gaijinn doctor --strict`.

Prevention: run `gaijinn doctor` after dependency upgrades and before creating worker handoffs.

