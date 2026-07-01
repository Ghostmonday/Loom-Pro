from __future__ import annotations

import json
from html.parser import HTMLParser

from aoc_supervisor.api import app
from aoc_supervisor.repo_paths import (
    FRONTEND_DIR,
    INTENT_FORGE_HTML_PATH,
    LOOM_INTENT_FORGE_INTENT_MAP_PATH,
    SANDBOX_SHARED_FILES,
    SANDBOX_WORKSPACE_FRAGMENTS,
)
from fastapi.testclient import TestClient


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "id" and value:
                self.ids.add(value)


def _ids(path):
    parser = IdCollector()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.ids


def test_runtime_routes_resolve_through_repo_paths() -> None:
    assert INTENT_FORGE_HTML_PATH == FRONTEND_DIR / "index.html"
    assert SANDBOX_WORKSPACE_FRAGMENTS["intent-forge.html"] == FRONTEND_DIR / "workspaces" / "intent-forge.html"
    assert SANDBOX_SHARED_FILES["intent-forge-driver.js"] == FRONTEND_DIR / "shared" / "intent-forge-driver.js"


def test_intent_forge_fragment_satisfies_canonical_dom_contract() -> None:
    contract = json.loads(LOOM_INTENT_FORGE_INTENT_MAP_PATH.read_text(encoding="utf-8"))
    expected = {element["dom_id"] for element in contract["elements"].values()}
    expected.add("vision-feedback")
    expected.add("vision-revision-editor")
    assert expected <= _ids(SANDBOX_WORKSPACE_FRAGMENTS["intent-forge.html"])


def test_shell_loads_fragment_and_real_driver_by_default() -> None:
    shell = INTENT_FORGE_HTML_PATH.read_text(encoding="utf-8")
    driver = SANDBOX_SHARED_FILES["intent-forge-driver.js"].read_text(encoding="utf-8")
    assert "shared/shell.js" in shell
    assert "shared/intent-forge-driver.js" in shell
    assert "currentWorkspace: null" in SANDBOX_SHARED_FILES["shell.js"].read_text(encoding="utf-8")
    assert 'return qs.get("loom_driver") === "mock"' in driver
    assert 'mode: explicitMockEnabled() ? "mock" : "api"' in driver
    assert 'var API_PREFIX = "/api/v1/intent-forge"' in driver


def test_static_routes_serve_shell_assets_fragments_and_contracts() -> None:
    client = TestClient(app)
    assert client.get("/").status_code == 200
    asset = client.get("/shared/intent-forge-driver.js")
    assert asset.status_code == 200
    assert "/api/v1/intent-forge" in asset.text
    fragment = client.get("/workspaces/intent-forge.html")
    assert fragment.status_code == 200
    assert "btn-start-session" in fragment.text
    contract = client.get("/ui/contracts/loom-intent-forge-intent-map.json")
    assert contract.status_code == 200
    assert contract.json()["route"] == "/"
