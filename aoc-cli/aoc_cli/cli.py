"""Unified Loom CLI entrypoint — command registration only; logic lives in commands/."""

from __future__ import annotations

from pathlib import Path

import typer

from .commands.activate import activate_cmd
from .commands.analyze_ import analyze_cmd
from .commands.audit import audit_cmd
from .commands.collect import collect_cmd
from .commands.compile_prompt import compile_prompt_cmd
from .commands.council import (
    council_init_cmd,
    council_rebuild_cmd,
    council_say_cmd,
    council_show_cmd,
    council_watch_cmd,
)
from .commands.doctor import doctor_cmd
from .commands.grid_spawn import grid_spawn_cmd
from .commands.hermes_ import hermes_cmd
from .commands.init_ import init_cmd
from .commands.merge_grid import merge_grid_cmd
from .commands.monitor import monitor_cmd
from .commands.plan import plan_cmd
from .commands.run_grid import run_grid_cmd
from .commands.scan import scan_cmd
from .commands.status import status_cmd
from .commands.validate_worker import validate_worker_cmd
from .commands.version import version_cmd
from .helpers import DEFAULT_GRAPH_PATH, DEFAULT_METRICS_PATH, DEFAULT_POLL_INTERVAL

app = typer.Typer(
    name="loom",
    help="Loom CLI — blueprint-driven parallelization engine and multi-agent governance gateway.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def main() -> None:
    """Run the Typer application."""
    app()


@app.command()
def activate(
    license_key: str = typer.Argument(
        ...,
        help="License key to activate for this local checkout.",
    ),
) -> None:
    """Store local activation metadata in .gaijinn/license.json."""
    activate_cmd(license_key)


@app.command()
def init(
    project_prompt: str = typer.Argument(
        ...,
        help="Project prompt used to seed build manifest generation.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing Loom init state.",
    ),
    blueprint_template: bool = typer.Option(
        False,
        "--blueprint-template",
        help="Write an editable build manifest template at .gaijinn/blueprint.md.",
    ),
    agent_files: bool = typer.Option(
        True,
        "--agent-files/--no-agent-files",
        help="Append Loom guidance blocks to CLAUDE.md and .cursorrules.",
    ),
) -> None:
    """Initialize .gaijinn project state and build manifest seed files."""
    init_cmd(project_prompt, force, blueprint_template, agent_files)


@app.command()
def audit(
    target_dir: Path = typer.Argument(
        Path("."),
        help="Repository root to audit for multi-agent structural readiness.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    json_only: bool = typer.Option(
        False,
        "--json-only",
        "--json",
        help="Emit raw audit JSON to stdout.",
    ),
    report_path: Path | None = typer.Option(
        None,
        "--report-path",
        help="Override audit report destination (default: <target>/.gaijinn/audit-report.json).",
        file_okay=True,
        dir_okay=False,
    ),
    stdout_only: bool = typer.Option(
        False,
        "--stdout-only",
        help="Do not write .gaijinn/audit-report.json; print report only.",
    ),
) -> None:
    """Evaluate repository structural readiness for parallel agent swarms (read-only)."""
    audit_cmd(
        target_dir,
        json_only=json_only,
        report_path=report_path,
        write_report=not stdout_only,
    )


@app.command()
def scan(
    path: Path = typer.Argument(
        ...,
        help="Directory to scan into .gaijinn/graph.json.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
) -> None:
    """Scan a directory, honoring .gitignore, and write .gaijinn/graph.json."""
    scan_cmd(path)


@app.command()
def compile_prompt(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print a stable machine-readable compile summary.",
    ),
) -> None:
    """Compile project.json into .gaijinn/intent.txt."""
    compile_prompt_cmd(json_output)


@app.command()
def run_grid(
    workers: int = typer.Option(
        ...,
        "--workers",
        "-w",
        min=1,
        help="Number of isolated worker directories to create.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing worker directories and manifest.",
    ),
    bootstrap_single_worker: bool = typer.Option(
        False,
        "--bootstrap-single-worker",
        help="Allow one project-scoped bootstrap worker before blueprint generation.",
    ),
) -> None:
    """Create isolated worker directories under .gaijinn/workers/."""
    run_grid_cmd(workers, force, bootstrap_single_worker)


@app.command()
def hermes(
    message: str | None = typer.Argument(
        None,
        help="Optional message for a one-shot Hermes session.",
    ),
    interactive: bool = typer.Option(
        False,
        "-i",
        "--interactive",
        help="Open interactive Hermes chat (type hermes in terminal).",
    ),
    global_council: bool = typer.Option(
        True,
        "--global/--project",
        help="Use machine-wide council at ~/.gaijinn/bridge/council.md (default).",
    ),
) -> None:
    """Hermes chat session from the terminal — council-backed, no relay."""
    hermes_cmd(message, interactive, global_council)


@app.command()
def grid_spawn(
    workers: int = typer.Option(
        ...,
        "--workers",
        "-w",
        min=1,
        help="Number of workers to spawn (must match run-grid count).",
    ),
    model: str = typer.Option(
        "grok-composer-2.5-fast",
        "--model",
        "-m",
        help="Grok Build model for all agents (must be same for consistency).",
    ),
    timeout: int = typer.Option(
        3600,
        "--timeout",
        min=1,
        help="Seconds to wait for each worker before killing it.",
    ),
    executor: str = typer.Option(
        "auto",
        "--executor",
        "-e",
        help="Execution coder: auto (prefer codex), codex, or grok.",
    ),
) -> None:
    """Spawn Codex or Grok agents per worker cell. Atomic sprint — no cancel."""
    grid_spawn_cmd(workers, model, timeout, executor)


@app.command()
def plan(
    workers: int = typer.Option(
        2,
        "--workers",
        "-w",
        min=1,
        help="Intended worker count for planning summary.",
    ),
    max_risk: str = typer.Option(
        "high",
        "--max-risk",
        help="Maximum allowed assignment risk: low, medium, or high.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print the generated build manifest JSON after writing artifacts.",
    ),
) -> None:
    """Generate the build manifest at .gaijinn/blueprint.json and .gaijinn/blueprint.md."""
    plan_cmd(workers, max_risk, json_output)


@app.command()
def collect() -> None:
    """Collect worker execution state for the merge pipeline."""
    collect_cmd()


@app.command("validate-worker")
def validate_worker(
    worker_id: str | None = typer.Argument(
        None,
        help="Worker ID to validate (e.g. worker-001). Validates all collected workers when omitted.",
    ),
    workers_dir: Path | None = typer.Option(
        None,
        "--workers-dir",
        help="Override path to worker directories.",
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Run merge-pipeline validation gates for one or all collected workers."""
    validate_worker_cmd(worker_id, workers_dir)


@app.command("merge-grid")
def merge_grid(
    strategy: str = typer.Option(
        "sequential",
        "--strategy",
        help="Merge strategy (only sequential is supported today).",
    ),
    base_branch: str | None = typer.Option(
        None,
        "--base-branch",
        help="Base branch for the integration branch (default: current git branch).",
    ),
    skip_tests: bool = typer.Option(
        False,
        "--no-test",
        help="Skip pytest/ruff gate after each merge.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Simulate merge without touching git.",
    ),
) -> None:
    """Merge validated worker branches into loom/integration."""
    merge_grid_cmd(strategy, base_branch, skip_tests, dry_run)


@app.command()
def status(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print a stable machine-readable status payload.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit non-zero when status is degraded or tripped.",
    ),
) -> None:
    """Summarize current .gaijinn project state."""
    status_cmd(json_output, strict)


@app.command()
def analyze(
    graph: Path = typer.Option(
        DEFAULT_GRAPH_PATH,
        "--graph",
        "-g",
        help="Input graph JSON path.",
        file_okay=True,
        dir_okay=False,
    ),
    output: Path = typer.Option(
        DEFAULT_METRICS_PATH,
        "--output",
        "-o",
        help="Metrics artifact JSON path.",
        file_okay=True,
        dir_okay=False,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print a stable machine-readable analysis summary.",
    ),
    fail_on_rejection: bool = typer.Option(
        False,
        "--fail-on-rejection",
        help="Exit non-zero when any node fails the preflight hard floor.",
    ),
    fail_on_shadow_bridge: bool = typer.Option(
        False,
        "--fail-on-shadow-bridge",
        help="Exit non-zero when preflight detects isolation signals.",
    ),
) -> None:
    """Run integrity preflight and write the metrics manifest."""
    analyze_cmd(graph, output, json_output, fail_on_rejection, fail_on_shadow_bridge)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind address for the product API."),
    port: int = typer.Option(8080, "--port", "-p", help="HTTP port for the product API."),
) -> None:
    """Run the hosted Loom API (billing, preflight, grid) — keeps the engine server-side."""
    import uvicorn
    from aoc_supervisor.api import app as api_app

    typer.echo(f"Loom product API on http://{host}:{port}")
    typer.echo("Open / for the command bridge terminal.")
    uvicorn.run(api_app, host=host, port=port)


@app.command()
def monitor(
    manifest: Path = typer.Option(
        DEFAULT_METRICS_PATH,
        "--manifest",
        "-m",
        help="Metrics manifest path to monitor.",
        file_okay=True,
        dir_okay=False,
    ),
    poll_interval: float = typer.Option(
        DEFAULT_POLL_INTERVAL,
        "--poll-interval",
        min=0.1,
        help="Polling interval in seconds.",
    ),
) -> None:
    """Watch metrics manifest writes and validate supervisor state."""
    monitor_cmd(manifest, poll_interval)


@app.command()
def doctor(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print stable machine-readable diagnostics.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit non-zero when any hard diagnostic fails.",
    ),
) -> None:
    """Check the local Loom installation and project artifacts."""
    doctor_cmd(json_output, strict)


council_app = typer.Typer(
    name="council",
    help="Shared council thread — one file for you and every agent (no relay).",
    no_args_is_help=True,
)


@council_app.command("say")
def council_say(
    message: str = typer.Argument(..., help="Message to append to the council thread."),
    author: str = typer.Option(
        "user",
        "--as",
        "-a",
        help="Speaker: user, cursor, grok, loom, deepseek, other.",
    ),
    author_id: str | None = typer.Option(
        None,
        "--id",
        help="Display id (e.g. worker-001, Amir, composer).",
    ),
    role: str = typer.Option(
        "participant",
        "--role",
        "-r",
        help="Role label: participant, advisor, executor, system.",
    ),
    global_council: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Use machine-wide council at ~/.gaijinn/bridge/council.md (all terminals).",
    ),
) -> None:
    """Append to .gaijinn/bridge/council.md (all agents read this file)."""
    council_say_cmd(message, author, author_id, role, global_council)


@council_app.command("show")
def council_show(
    json_output: bool = typer.Option(False, "--json", help="Print messages as JSON."),
    tail: int = typer.Option(0, "--tail", "-n", help="Show only the last N messages."),
    global_council: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Machine-wide council at ~/.gaijinn/bridge/council.md",
    ),
) -> None:
    """Print the shared council thread."""
    council_show_cmd(json_output, tail, global_council)


@council_app.command("watch")
def council_watch(
    poll_interval: float = typer.Option(1.0, "--poll-interval", min=0.2, help="Poll interval in seconds."),
) -> None:
    """Watch for new council messages."""
    council_watch_cmd(poll_interval)


@council_app.command("init")
def council_init() -> None:
    """Create .gaijinn/bridge/ council files."""
    council_init_cmd()


@council_app.command("rebuild")
def council_rebuild(
    global_council: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Rebuild machine-wide council at ~/.gaijinn/bridge/council.md",
    ),
) -> None:
    """Regenerate council.md from council.jsonl with current timestamp formatting."""
    council_rebuild_cmd(global_council)


app.add_typer(council_app, name="council")


@app.command("version")
def version_command(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print version information as JSON.",
    ),
) -> None:
    """Print the installed Loom version."""
    version_cmd(json_output)


if __name__ == "__main__":
    main()
