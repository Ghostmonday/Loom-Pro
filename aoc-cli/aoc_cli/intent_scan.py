"""Layer 1 Reactive extraction — Intent Nodes from source code.

Statically extracts HTTP routes, CLI commands, guard conditions, and side-effects
into the interaction_graph format consumed by inferring.infer_reflective_layer().
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .dataflow import analyze_handler_dataflow

_ROUTE_DECORATOR = re.compile(
    r"^(?:app|router|api|bp)\.(get|post|put|delete|patch|head|options|trace)$",
    re.IGNORECASE,
)
_PATH_PARAM = re.compile(r"\{([^}]+)\}")
_CONTEXT_PARAM_HINTS = frozenset(
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
_OPERATION_VERBS = (
    ("create", "created"),
    ("activate", "active"),
    ("trigger", "running"),
    ("start", "running"),
    ("run", "running"),
    ("cancel", "cancelled"),
    ("delete", "deleted"),
    ("remove", "deleted"),
    ("fail", "failed"),
    ("update", "updated"),
    ("resolve", "resolved"),
    ("purchase", "purchased"),
    ("merge", "merged"),
    ("spawn", "spawned"),
    ("prepare", "prepared"),
)


def extract_interaction_graph(root: Path, python_files: Iterable[Path]) -> list[dict[str, Any]]:
    """Scan Python files and return Layer 1 Intent Nodes."""
    nodes: list[dict[str, Any]] = []
    for relative in sorted(python_files, key=lambda item: item.as_posix()):
        path = root / relative
        text = _read_text(path)
        if not text:
            continue
        try:
            tree = ast.parse(text, filename=relative.as_posix())
        except SyntaxError:
            continue
        nodes.extend(_extract_from_module(tree, relative))
    return _dedupe_intent_nodes(nodes)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _extract_from_module(tree: ast.Module, relative: Path) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes.extend(_extract_function_intents(node, relative))
    return nodes


def _extract_function_intents(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    relative: Path,
) -> list[dict[str, Any]]:
    route = _route_from_decorators(func)
    typer_cmd: str | None = None
    if route is None:
        typer_cmd = _typer_command_name(func)
        if typer_cmd is None:
            return []
        route = ("CLI", typer_cmd)

    method, path = route
    intent = _intent_name(method, path, func.name)
    cluster = _resource_cluster(path, intent)
    context_params, query_params = _path_parameters(path, func)
    prior_state, resulting_state = _infer_states(intent, method, path)
    guards = _guard_conditions(func)
    side_effects = _side_effects(func)
    capability = _capability_from_route(method, path, side_effects)
    side_effect_score = min(3.0, 0.25 * len(side_effects) + (1.0 if "delete" in intent else 0.0))
    dataflow = analyze_handler_dataflow(func)

    return [
        {
            "agent_intent": intent,
            "valid_prior_state": prior_state,
            "resulting_state": resulting_state,
            "http_method": None if method == "CLI" else method.upper(),
            "http_path": None if method == "CLI" else path,
            "cli_command": typer_cmd if method == "CLI" else None,
            "side_effects": side_effects,
            "guard_conditions": guards,
            "context_params": context_params,
            "query_params": query_params,
            "resource_cluster": cluster,
            "capability_level": capability,
            "side_effect_score": side_effect_score,
            "source_file": relative.as_posix(),
            "source_line": func.lineno,
            "dataflow": dataflow,
        }
    ]


def _route_from_decorators(func: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, str] | None:
    for decorator in func.decorator_list:
        call = _decorator_call(decorator)
        if call is None:
            continue
        func_name, args, _kwargs = call
        if not _ROUTE_DECORATOR.match(func_name):
            continue
        if not args:
            continue
        path = args[0] if isinstance(args[0], str) else _literal_str(args[0])
        if path is None:
            continue
        return func_name.split(".")[-1], path
    return None


def _decorator_call(node: ast.expr) -> tuple[str, list[Any], dict[str, Any]] | None:
    if isinstance(node, ast.Call):
        func = node.func
    else:
        func = node
        node = ast.Call(func=func, args=[], keywords=[])

    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        current: ast.expr = func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        func_name = ".".join(reversed(parts))
    elif isinstance(func, ast.Name):
        func_name = func.id
    else:
        return None

    args = [_literal_value(arg) for arg in node.args]
    kwargs = {keyword.arg: _literal_value(keyword.value) for keyword in node.keywords if keyword.arg}
    return func_name, args, kwargs


def _literal_str(node: Any) -> str | None:
    value = _literal_value(node)
    return str(value) if isinstance(value, str) else None


def _literal_value(node: ast.expr) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _typer_command_name(func: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    for decorator in func.decorator_list:
        call = _decorator_call(decorator)
        if call is None:
            continue
        func_name, args, kwargs = call
        if func_name.endswith(".command") or func_name == "command":
            if args and isinstance(args[0], str):
                return args[0]
            return func.name.replace("_", "-")
    return None


def _intent_name(method: str, path: str, func_name: str) -> str:
    if method == "CLI":
        return f"cli_{func_name}"
    segments = [segment for segment in path.strip("/").split("/") if segment and not segment.startswith("{")]
    if segments:
        resource = segments[-1].replace("-", "_")
        return f"{resource}_{method.lower()}"
    return f"{func_name}_{method.lower()}"


def _resource_cluster(path: str, intent: str) -> str:
    if path == "CLI":
        for suffix in ("_create", "_delete", "_update", "_list", "_get"):
            if intent.endswith(suffix):
                return intent[: -len(suffix)].removeprefix("cli_")
        return intent.removeprefix("cli_")
    segments = [segment for segment in path.strip("/").split("/") if segment and not segment.startswith("{")]
    if len(segments) >= 2 and segments[-1] in {"spawn", "merge", "prepare", "swarm", "status", "diff", "deliverable"}:
        return segments[-2].replace("-", "_")
    if segments:
        return segments[-1].replace("-", "_")
    return intent


def _path_parameters(path: str, func: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[list[str], list[str]]:
    path_params = [match.group(1) for match in _PATH_PARAM.finditer(path)]
    arg_names = {arg.arg for arg in func.args.args}
    context: list[str] = []
    query: list[str] = []
    for param in path_params:
        normalized = param.lower().replace("-", "_")
        if (
            normalized in _CONTEXT_PARAM_HINTS
            or normalized.endswith("_id")
            and normalized.split("_")[0] in {"org", "user", "tenant"}
        ):
            context.append(param)
        else:
            query.append(param)
    for name in sorted(arg_names):
        lowered = name.lower()
        if lowered in _CONTEXT_PARAM_HINTS and name not in context:
            context.append(name)
    return sorted(set(context)), sorted(set(query))


def _infer_states(intent: str, method: str, path: str) -> tuple[str | None, str | None]:
    lowered = f"{intent} {path} {method}".lower()
    for verb, state_suffix in _OPERATION_VERBS:
        if verb in lowered:
            resource = intent
            for suffix in ("_create", "_activate", "_trigger", "_cancel", "_delete", "_update", "_get", "_post"):
                if resource.endswith(suffix):
                    resource = resource[: -len(suffix)]
                    break
            if verb == "create":
                return None, f"{resource}_created"
            if verb in {"activate", "trigger", "start", "run"}:
                return f"{resource}_created", f"{resource}_{state_suffix}"
            if verb == "cancel":
                return f"{resource}_running", f"{resource}_cancelled"
            if verb in {"delete", "remove"}:
                return None, f"{resource}_deleted"
            if verb == "fail":
                return f"{resource}_running", f"{resource}_failed"
            return f"{resource}_pending", f"{resource}_{state_suffix}"
    if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        return None, f"{intent}_completed"
    return None, None


def _guard_conditions(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    guards: list[str] = []
    for node in ast.walk(func):
        if not isinstance(node, ast.If):
            continue
        test = _expr_preview(node.test)
        if _looks_like_guard(test, node):
            guards.append(test.strip())
    return guards[:5]


def _expr_preview(node: ast.expr) -> str:
    if isinstance(node, ast.Compare):
        left = _expr_preview(node.left)
        ops = []
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            if isinstance(op, ast.NotEq):
                ops.append("!=")
            elif isinstance(op, ast.Eq):
                ops.append("==")
            else:
                ops.append("?")
            ops.append(_expr_preview(comparator))
        return f"{left} {' '.join(ops)}".strip()
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Attribute):
        return f"{_expr_preview(node.value)}.{node.attr}"
    return "guard"


def _looks_like_guard(test: str, node: ast.If) -> bool:
    lowered = test.lower()
    if any(token in lowered for token in ("error", "status", "active", "permission", "auth", "forbidden", "invalid")):
        return True
    return any(isinstance(child, (ast.Raise, ast.Return)) for child in node.body)


def _side_effects(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    effects: list[str] = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if not name:
            continue
        lowered = name.lower()
        if any(
            token in lowered
            for token in ("create", "insert", "update", "delete", "write", "save", "commit", "deduct", "spawn", "merge")
        ):
            effects.append(name)
    return sorted(set(effects))[:8]


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _capability_from_route(method: str, path: str, side_effects: list[str]) -> float:
    score = 1.0
    if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        score += 1.5
    if "admin" in path.lower() or "billing" in path.lower():
        score += 1.0
    score += min(2.0, 0.25 * len(side_effects))
    return float(min(6.0, score))


def _dedupe_intent_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for node in nodes:
        key = str(node["agent_intent"])
        existing = seen.get(key)
        if existing is None or len(node.get("side_effects", [])) > len(existing.get("side_effects", [])):
            seen[key] = node
    return [seen[key] for key in sorted(seen)]
