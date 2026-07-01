from __future__ import annotations

import json
from html.parser import HTMLParser

from aoc_supervisor.repo_paths import (
    FRONTEND_DIR,
    LOOM_INTENT_FORGE_INTENT_MAP_PATH,
)


class _IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "id" and value:
                self.ids.add(value)


def test_intent_forge_dom_ids_sandbox() -> None:
    """Check the intent-forge workspace fragment has the DOM IDs declared in contract."""
    contract = json.loads(LOOM_INTENT_FORGE_INTENT_MAP_PATH.read_text(encoding="utf-8"))
    expected_ids = {element["dom_id"] for element in contract["elements"].values()}

    forge_fragment = FRONTEND_DIR / "workspaces" / "intent-forge.html"
    assert forge_fragment.exists(), f"Workspace fragment not found: {forge_fragment}"
    parser = _IdCollector()
    parser.feed(forge_fragment.read_text(encoding="utf-8"))

    found = expected_ids & parser.ids
    assert len(found) > 0, f"No contract DOM IDs found in workspace fragment. Contract expects: {expected_ids}"
