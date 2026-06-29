from __future__ import annotations

import ast
import json
from pathlib import Path

from aoc_supervisor.repo_paths import FRONTEND_DIR, INTENT_FORGE_HTML_PATH, REPO_ROOT, SANDBOX_PAGES

REGISTRY_PATH = Path("docs/reference/canonical-authority.registry.json")
GENERATED_MARKER = "GENERATED FILE - DO NOT EDIT. Regenerate from canonical sources."
INACTIVE_ROOTS = {"frontend-formation-complete", "vaults/gaijinn-memory-fs"}
OBSOLETE_UI_ROUTES = {"/ui/index.html", "/ui/intent-forge.html", "/ui/project-hub.html"}


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_declares_single_authorities_for_major_surfaces() -> None:
    registry = _registry()
    authorities = registry["authorities"]
    assert registry["product_name"] == "Loom"
    assert authorities["naming_and_package_identity"]["source"] == "pyproject.toml"
    assert authorities["canonical_paths"]["source"] == "aoc_supervisor/aoc_supervisor/repo_paths.py"
    assert authorities["frontend_runtime"]["source"] == "sandbox_frontend"
    assert authorities["frontend_formation_compiler"]["source"] == "loom-frontend-base/frontend-formation"
    assert authorities["overlay_policy_and_registry"]["sources"] == [
        ".loom/overlays/policy.json",
        ".loom/overlays/registry.json",
    ]
    assert authorities["perfect_spec_interrogation"]["classification"].startswith("runtime-canonical")


def test_runtime_frontend_paths_do_not_drift_to_legacy_ui() -> None:
    assert FRONTEND_DIR == REPO_ROOT / "sandbox_frontend"
    assert INTENT_FORGE_HTML_PATH == FRONTEND_DIR / "index.html"
    assert SANDBOX_PAGES["hub"] == FRONTEND_DIR / "index.html"
    assert all("/ui/" not in path.as_posix() for path in SANDBOX_PAGES.values())


def test_generated_frontend_artifacts_are_marker_guarded() -> None:
    registry = _registry()
    marker = registry["generated_artifact_policy"]["marker"]
    generated_root = Path(registry["generated_artifact_policy"]["generated_roots"][0])
    assert generated_root.is_dir()
    for path in generated_root.rglob("*"):
        if path.is_file() and path.suffix in {".yaml", ".yml", ".html", ".css", ".js"}:
            assert marker in path.read_text(encoding="utf-8", errors="ignore")[:300], path


def test_python_runtime_imports_do_not_target_inactive_duplicate_trees() -> None:
    for path in Path(".").rglob("*.py"):
        if any(part in INACTIVE_ROOTS for part in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", "") or ""
                names = [alias.name for alias in getattr(node, "names", [])]
                import_text = " ".join([module, *names])
                assert "frontend-formation-complete" not in import_text
                assert "vaults.gaijinn-memory-fs" not in import_text


def test_obsolete_ui_html_routes_are_not_resurrected() -> None:
    router_text = Path("aoc_supervisor/aoc_supervisor/routers/static_ui.py").read_text(encoding="utf-8")
    api_text = Path("aoc_supervisor/aoc_supervisor/api.py").read_text(encoding="utf-8")
    for route in OBSOLETE_UI_ROUTES:
        assert route not in router_text
        assert route not in api_text
