"""Type-flow analysis — static taint tracking for Layer 1 Intent Nodes.

Marks identity variables (org_id, user_id) as Sources and DB/file mutation
calls as Sinks, then traces the AST to detect data-flow punctures: paths
that reach a Sink without carrying required Source taint.
"""

from __future__ import annotations

import ast
from typing import Any

SOURCE_PARAM_HINTS = frozenset(
    {
        "org",
        "org_id",
        "organization",
        "organization_id",
        "tenant",
        "tenant_id",
        "user",
        "user_id",
        "userid",
        "orgid",
    }
)
_SINK_CALL_HINTS = frozenset(
    {
        "execute",
        "executemany",
        "commit",
        "delete",
        "remove",
        "drop",
        "truncate",
        "write_text",
        "write_bytes",
        "unlink",
        "rmtree",
        "insert",
        "update",
        "save",
        "create",
        "exec",
    }
)


def analyze_handler_dataflow(func: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    """Return taint/dataflow metadata for a route or CLI handler."""
    sources = _identity_sources(func)
    sinks = _mutation_sinks(func)
    punctures = _dataflow_punctures(func, sources, sinks)
    return {
        "taint_sources": sorted(sources),
        "mutation_sinks": sinks,
        "dataflow_punctures": punctures,
        "has_dataflow_puncture": bool(punctures),
    }


def _identity_sources(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    sources: set[str] = set()
    for arg in func.args.args:
        normalized = arg.arg.lower().replace("-", "_")
        if normalized in SOURCE_PARAM_HINTS:
            sources.add(arg.arg)
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id.lower()
            if name in SOURCE_PARAM_HINTS:
                sources.add(node.targets[0].id)
    return sources


def _mutation_sinks(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict[str, Any]]:
    sinks: list[dict[str, Any]] = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        call_name = _call_qualified_name(node)
        if call_name is None:
            continue
        leaf = call_name.split(".")[-1].lower()
        if leaf not in _SINK_CALL_HINTS and not any(hint in call_name.lower() for hint in _SINK_CALL_HINTS):
            continue
        args_used = sorted(_names_in_expr(node))
        sinks.append(
            {
                "call": call_name,
                "line": getattr(node, "lineno", 0),
                "args_referenced": args_used,
            }
        )
    return sinks


def _dataflow_punctures(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    sources: set[str],
    sinks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not sinks or not sources:
        return []

    punctures: list[dict[str, Any]] = []
    for sink in sinks:
        referenced = set(sink.get("args_referenced", []))
        if not referenced:
            punctures.append(
                {
                    "sink": sink["call"],
                    "line": sink["line"],
                    "missing_sources": sorted(sources),
                    "description": (
                        f"Mutation sink {sink['call']} at line {sink['line']} "
                        f"does not reference identity sources {sorted(sources)}."
                    ),
                }
            )
            continue
        missing = sorted(
            source
            for source in sources
            if source not in referenced and not _source_reaches_names(func, source, referenced)
        )
        if missing:
            punctures.append(
                {
                    "sink": sink["call"],
                    "line": sink["line"],
                    "missing_sources": missing,
                    "description": (
                        f"Data-flow puncture: {sink['call']} at line {sink['line']} missing taint from {missing}."
                    ),
                }
            )
    return punctures


def _source_reaches_names(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    source: str,
    target_names: set[str],
) -> bool:
    """Conservative intraprocedural check: source flows into any target name."""
    aliases: dict[str, set[str]] = {source: {source}}
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            refs = _names_in_expr(node.value)
            for target in targets:
                inherited = set()
                for ref in refs:
                    inherited.update(aliases.get(ref, {ref} if ref == source else set()))
                if inherited:
                    aliases[target] = inherited
        if isinstance(node, ast.Call):
            call_names = _names_in_expr(node)
            tainted = source in call_names or any(source in aliases.get(n, set()) for n in call_names)
            if tainted:
                for name in _names_in_expr(node):
                    if name in target_names:
                        return True
    return any(source in aliases.get(name, set()) or name == source for name in target_names)


def _names_in_expr(node: ast.expr | ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.add(child.id)
    return names


def _call_qualified_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = []
        current: ast.expr = func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return None
