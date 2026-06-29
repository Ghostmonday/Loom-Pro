"""scan command implementation."""

from __future__ import annotations

from pathlib import Path

import typer

from ..helpers import (
    DEFAULT_GRAPH_PATH,
    _ensure_gaijinn_dir,
    _optional_project_state,
    _scan_directory,
    _write_json,
)


def scan_cmd(path: Path) -> None:
    """Scan a directory, honoring .gitignore, and write .gaijinn/graph.json."""
    root = path.resolve()
    if not root.is_dir():
        raise typer.BadParameter(f"{path} is not a directory")

    state = _optional_project_state()
    graph_path = state.graph_path if state is not None else DEFAULT_GRAPH_PATH
    _ensure_gaijinn_dir()
    graph = _scan_directory(root)
    _write_json(graph_path, graph)
    intent_count = len(graph.get("interaction_graph", []))
    typer.echo(f"Scanned {len(graph['nodes'])} files and {intent_count} intent nodes into {graph_path}")
