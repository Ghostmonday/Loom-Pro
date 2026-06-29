"""Tests for markdown wikilink edges in scan."""

from __future__ import annotations

from pathlib import Path

from aoc_cli.helpers.scan import _scan_directory


def test_scan_extracts_wikilink_edges(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("See [[b.md]] for details.\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("Back to [[a.md]].\n", encoding="utf-8")
    graph = _scan_directory(tmp_path)
    edges = graph.get("edges", [])
    kinds = {(e["source"], e["target"], e.get("kind")) for e in edges}
    assert ("a.md", "b.md", "wikilink") in kinds
    assert ("b.md", "a.md", "wikilink") in kinds


def test_scan_resolves_extensionless_and_frontmatter_wikilinks(tmp_path: Path) -> None:
    (tmp_path / "40_Concepts").mkdir(parents=True)
    (tmp_path / "40_Concepts" / "target.md").write_text("# Target\n", encoding="utf-8")
    (tmp_path / "40_Concepts" / "source.md").write_text(
        '---\nrelated_concepts:\n  - "[[40_Concepts/target]]"\n---\n'
        "See [[40_Concepts/target]] in body.\n"
        "No self [[40_Concepts/source]].\n",
        encoding="utf-8",
    )
    graph = _scan_directory(tmp_path)
    wikilinks = [
        (e["source"], e["target"])
        for e in graph.get("edges", [])
        if isinstance(e, dict) and e.get("kind") == "wikilink"
    ]
    assert ("40_Concepts/source.md", "40_Concepts/target.md") in wikilinks
    assert sum(1 for s, t in wikilinks if s == t) == 0
