"""Directory scanning helpers for Gaijinn CLI commands."""

from __future__ import annotations

import ast
import json
import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from .constants import DEFAULT_METRICS_PATH, WORKERS_DIR

_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

# ── Scan helpers ───────────────────────────────────────────────────────


def _extract_layer1_intent_nodes(root: Path, python_files: set[Path]) -> list[dict[str, Any]]:
    from ..intent_scan import extract_interaction_graph
    from ..semantic_moat import enrich_intent_semantics

    nodes = extract_interaction_graph(root, python_files)
    return enrich_intent_semantics(nodes)


def _scan_directory(root: Path) -> dict[str, Any]:
    ignore_patterns = _load_gitignore_patterns(root)
    files: list[Path] = []

    for candidate in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = candidate.relative_to(root)
        if _is_ignored(relative, candidate.is_dir(), ignore_patterns):
            if candidate.is_dir():
                continue
            continue
        if candidate.is_file():
            files.append(relative)

    python_files = {relative for relative in files if relative.suffix == ".py"}
    module_index = _python_module_index(python_files)
    nodes = [_scan_node(root, relative) for relative in files]
    edges = _python_import_edges(root, python_files, module_index)
    edges.extend(_markdown_wikilink_edges(root, {relative for relative in files if relative.suffix == ".md"}))
    interaction_graph = _extract_layer1_intent_nodes(root, python_files)
    return {
        "schema_version": 1,
        "root": str(root),
        "layer1_reactive": {
            "file_nodes": len(nodes),
            "intent_nodes": len(interaction_graph),
        },
        "nodes": nodes,
        "edges": edges,
        "interaction_graph": interaction_graph,
    }


def _scan_node(root: Path, relative: Path) -> dict[str, Any]:
    path = root / relative
    text = _read_scan_text(path)
    return {
        "id": relative.as_posix(),
        "path": relative.as_posix(),
        "extension": relative.suffix,
        "language": _language_for_path(relative),
        "line_count": _line_count(text),
        "size_bytes": path.stat().st_size,
        "capability_level": _capability_level(relative, text),
        "side_effect_score": _scan_side_effect_score(relative, text),
    }


def _read_scan_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def _line_count(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines())


def _language_for_path(relative: Path) -> str:
    languages = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".json": "json",
        ".md": "markdown",
        ".toml": "toml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".html": "html",
        ".css": "css",
        ".sh": "shell",
    }
    if relative.name in {"Dockerfile", "Containerfile"}:
        return "dockerfile"
    return languages.get(relative.suffix.lower(), "unknown")


def _capability_level(relative: Path, text: str) -> float:
    path_text = relative.as_posix().lower()
    lowered = text.lower()
    score = 1.0
    if relative.suffix == ".py":
        score += 1.0
    if any(part.startswith("test") for part in relative.parts) or relative.name.startswith("test_"):
        score -= 0.5

    capability_keywords = {
        "api": 1.0,
        "auth": 1.0,
        "billing": 1.0,
        "database": 1.0,
        "db": 0.75,
        "deploy": 1.0,
        "enforcer": 1.0,
        "gravity": 1.0,
        "grid_spawn": 0.75,
        "grok": 0.75,
        "orchestrator": 1.0,
        "security": 1.0,
        "sse": 0.5,
        "terminal": 0.75,
        "worker": 0.75,
    }
    combined = f"{path_text}\n{lowered}"
    for keyword, weight in capability_keywords.items():
        if keyword in combined:
            score += weight
    if "def main" in lowered or "@app.command" in lowered or "typer." in lowered:
        score += 0.5
    return float(max(0.0, min(6.0, score)))


def _scan_side_effect_score(relative: Path, text: str) -> float:
    lowered = f"{relative.as_posix().lower()}\n{text.lower()}"
    score = 0.0
    side_effect_keywords = {
        "eventstream": 0.75,
        "grid_spawn": 0.5,
        "popen": 1.0,
        "sse": 0.75,
        "write_text": 0.75,
        "open(": 0.5,
        "subprocess": 1.0,
        "socket": 1.0,
        "requests.": 1.0,
        "httpx.": 1.0,
        "delete": 0.75,
        "unlink": 0.75,
        "rmtree": 1.0,
        "mkdir": 0.5,
        "chmod": 0.75,
        "os.environ": 0.5,
        "database": 0.75,
        "postgres": 0.75,
        "sqlite": 0.75,
        "stripe": 1.0,
        "billing": 1.0,
    }
    for keyword, weight in side_effect_keywords.items():
        if keyword in lowered:
            score += weight
    return float(max(0.0, min(3.0, score)))


def _python_module_index(files: set[Path]) -> dict[str, Path]:
    modules: dict[str, Path] = {}
    for relative in sorted(files, key=lambda item: item.as_posix()):
        if relative.name == "__init__.py":
            module_parts = relative.parent.parts
        else:
            module_parts = (*relative.parent.parts, relative.stem)
        if module_parts:
            modules[".".join(module_parts)] = relative
    return modules


def _build_md_link_index(md_files: set[Path]) -> dict[str, str]:
    """Map wikilink aliases (with/without .md, stems, paths) to canonical file paths."""
    index: dict[str, str] = {}
    for relative in md_files:
        posix = relative.as_posix()
        index[posix] = posix
        stem = relative.stem
        parent = relative.parent.as_posix()
        if posix.endswith(".md"):
            index[posix[:-3]] = posix
        if parent and parent != ".":
            index[f"{parent}/{stem}"] = posix
        index[stem] = posix
    return index


def _resolve_wikilink_target(raw_target: str, link_index: dict[str, str]) -> str | None:
    """Resolve Obsidian-style wikilink targets to scanned markdown file paths."""
    target = raw_target.strip()
    if not target:
        return None
    if "|" in target:
        target = target.split("|", 1)[0].strip()
    if target in link_index:
        return link_index[target]
    if not target.endswith(".md"):
        with_md = f"{target}.md"
        if with_md in link_index:
            return link_index[with_md]
    return target if target.endswith(".md") else None


def _markdown_wikilink_edges(root: Path, md_files: set[Path]) -> list[dict[str, str]]:
    link_index = _build_md_link_index(md_files)
    edges: list[dict[str, str]] = []
    for relative in sorted(md_files, key=lambda item: item.as_posix()):
        source = relative.as_posix()
        text = _read_scan_text(root / relative)
        for match in _WIKILINK_RE.finditer(text):
            resolved = _resolve_wikilink_target(match.group(1), link_index)
            if resolved and resolved != source:
                edges.append(
                    {
                        "source": source,
                        "target": resolved,
                        "kind": "wikilink",
                    }
                )
    return edges


def _python_import_edges(root: Path, files: set[Path], module_index: dict[str, Path]) -> list[list[str]]:
    edges: set[tuple[str, str]] = set()
    for relative in sorted(files, key=lambda item: item.as_posix()):
        imports = _python_imports(root / relative, relative)
        for import_name in imports:
            target = _resolve_python_import(import_name, module_index)
            if target is not None and target != relative:
                edges.add((relative.as_posix(), target.as_posix()))
    return [[source, target] for source, target in sorted(edges)]


def _python_imports(path: Path, relative: Path) -> list[str]:
    text = _read_scan_text(path)
    if not text:
        return []
    try:
        tree = ast.parse(text, filename=relative.as_posix())
    except SyntaxError:
        return []

    imports: set[str] = set()
    package = _python_package(relative)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = _absolute_import_name(package, node.module, node.level)
            if base:
                imports.add(base)
            for alias in node.names:
                if alias.name != "*":
                    imports.add(f"{base}.{alias.name}" if base else alias.name)
    return sorted(imports)


def _python_package(relative: Path) -> str:
    parts = relative.parent.parts
    return ".".join(parts)


def _absolute_import_name(package: str, module: str | None, level: int) -> str:
    if level <= 0:
        return module or ""
    package_parts = package.split(".") if package else []
    keep = max(0, len(package_parts) - level + 1)
    prefix = package_parts[:keep]
    if module:
        prefix.extend(module.split("."))
    return ".".join(part for part in prefix if part)


def _resolve_python_import(import_name: str, module_index: dict[str, Path]) -> Path | None:
    parts = import_name.split(".")
    for length in range(len(parts), 0, -1):
        candidate = ".".join(parts[:length])
        if candidate in module_index:
            return module_index[candidate]
    return None


def _load_gitignore_patterns(root: Path) -> list[str]:
    patterns = [
        ".git/",
        ".gaijinn/",
        "node_modules/",
        "__pycache__/",
        ".venv/",
        ".ruff_cache/",
        "*.egg-info/",
        ".aoc/",
    ]
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return patterns

    for line in gitignore.read_text(encoding="utf-8").splitlines():
        pattern = line.strip()
        if not pattern or pattern.startswith("#") or pattern.startswith("!"):
            continue
        patterns.append(pattern)
    return patterns


def shadow_bridge_summary(manifest_path: str | Path = DEFAULT_METRICS_PATH) -> dict[str, Any]:
    """Return shadow-bridge and rejection counts from a metrics manifest."""
    path = Path(manifest_path)
    if not path.exists():
        return {
            "exists": False,
            "shadow_bridge_count": 0,
            "rejected_node_count": 0,
            "rejected_nodes": [],
            "automatic_rejection": False,
        }

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("metrics manifest must be a JSON object")

    gravity_meta = payload.get("gravity_meta", {})
    curvature_meta = payload.get("curvature_meta", {})
    rejected = sorted(str(item) for item in gravity_meta.get("rejected_nodes", []))
    return {
        "exists": True,
        "shadow_bridge_count": int(curvature_meta.get("shadow_bridge_count", 0) or 0),
        "rejected_node_count": len(rejected),
        "rejected_nodes": rejected,
        "automatic_rejection": bool(gravity_meta.get("automatic_rejection", False)),
    }


def validate_grid_readiness(
    manifest_path: str | Path = DEFAULT_METRICS_PATH,
    workers_path: str | Path = WORKERS_DIR,
) -> dict[str, Any]:
    """Check whether the project is ready for an atomic Grok Build grid sprint."""
    metrics = shadow_bridge_summary(manifest_path)
    workers_dir = Path(workers_path)
    manifest_file = workers_dir / "manifest.json"
    worker_dirs = sorted(path for path in workers_dir.glob("worker-*") if path.is_dir())
    blocked_reasons: list[str] = []
    if not metrics["exists"]:
        blocked_reasons.append("metrics manifest missing")
    if metrics["automatic_rejection"]:
        blocked_reasons.append("automatic rejection tripped")
    if metrics["rejected_node_count"] > 0:
        blocked_reasons.append(f"{metrics['rejected_node_count']} rejected node(s)")
    if metrics["shadow_bridge_count"] > 0:
        blocked_reasons.append(f"{metrics['shadow_bridge_count']} shadow bridge(s)")
    if not manifest_file.exists():
        blocked_reasons.append("worker manifest missing")
    if not worker_dirs:
        blocked_reasons.append("no worker directories")

    output_logs = [path / "output.log" for path in worker_dirs]
    from .stealth import sanitize_blocked_reasons

    return {
        "ready": not blocked_reasons,
        "blocked_reasons": sanitize_blocked_reasons(blocked_reasons),
        "worker_count": len(worker_dirs),
        "manifest_exists": manifest_file.exists(),
        "output_logs_present": sum(log.exists() for log in output_logs),
        "atomic_sprint": True,
        "cancel_supported": False,
        **metrics,
    }


def _is_ignored(relative: Path, is_dir: bool, patterns: list[str]) -> bool:
    rel = relative.as_posix()
    rel_dir = f"{rel}/" if is_dir else rel
    for pattern in patterns:
        normalized = pattern.strip("/")
        if not normalized:
            continue
        if pattern.endswith("/") and (rel_dir == f"{normalized}/" or rel_dir.startswith(f"{normalized}/")):
            return True
        if "/" not in normalized and any(part == normalized for part in relative.parts):
            return True
        if fnmatch(rel, normalized) or fnmatch(rel, pattern) or fnmatch(relative.name, normalized):
            return True
    return False
