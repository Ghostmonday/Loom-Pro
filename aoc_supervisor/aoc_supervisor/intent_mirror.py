"""Intent Mirror — AI-isomorphic UI state and assertion evaluation.

Every browser element and action is declared in ui/gaijinn-ui-intent-map.json.
UiIntentDriver is the thin executor of that map: same triggers,
same API calls, same errors — no browser required for smoke tests.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AssertionResult:
    expression: str
    passed: bool
    detail: str = ""


@dataclass
class IntentMirrorState:
    """Virtual UI + API snapshot for evaluating map assertions without a browser."""

    prepare: dict[str, Any] = field(default_factory=dict)
    swarm: dict[str, Any] = field(default_factory=dict)
    spawn: dict[str, Any] = field(default_factory=dict)
    sprint: dict[str, Any] = field(default_factory=dict)
    merge_pipeline: dict[str, Any] = field(default_factory=dict)
    grid_status: dict[str, Any] = field(default_factory=dict)
    grid: dict[str, Any] = field(default_factory=dict)
    session_status: str = ""
    artifact: dict[str, Any] = field(default_factory=dict)
    intent_forge: dict[str, Any] = field(default_factory=dict)
    readiness: dict[str, Any] = field(default_factory=dict)
    current_question: dict[str, Any] = field(default_factory=dict)
    executable_projection: dict[str, Any] = field(default_factory=dict)
    teleology: dict[str, Any] = field(default_factory=dict)
    blueprint: dict[str, Any] = field(default_factory=dict)
    baseline: dict[str, Any] = field(default_factory=dict)

    def as_context(self) -> dict[str, Any]:
        return {
            "prepare": self.prepare,
            "swarm": self.swarm,
            "spawn": self.spawn,
            "sprint": self.sprint,
            "merge_pipeline": self.merge_pipeline,
            "grid_status": self.grid_status,
            "grid": self.grid,
            "session_status": self.session_status,
            "artifact": self.artifact,
            "intent_forge": self.intent_forge,
            "readiness": self.readiness,
            "current_question": self.current_question,
            "executable_projection": self.executable_projection,
            "teleology": self.teleology,
            "blueprint": self.blueprint,
            "baseline": self.baseline,
        }

    def sync_grid_visibility(self, *, sprint_status: str, worker_count: int) -> None:
        active = sprint_status in {"running", "completed"} and worker_count > 0
        self.grid = {
            "view": "live" if active else "idle",
            "empty": {"hidden": active},
            "container": {"hidden": not active, "visible": active},
        }


def _resolve_path(context: Mapping[str, Any], path: str) -> Any:
    current: Any = context
    for part in path.split("."):
        if part.endswith("]"):
            name, index_text = part[:-1].split("[", 1)
            if name:
                if not isinstance(current, Mapping) or name not in current:
                    return None
                current = current[name]
            try:
                index = int(index_text)
            except ValueError:
                return None
            if not isinstance(current, list) or index >= len(current):
                return None
            current = current[index]
            continue
        if part == "length":
            return len(current) if isinstance(current, list) else None
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _eval_special(expression: str, context: Mapping[str, Any]) -> AssertionResult | None:
    if expression == "swarm.no_idle_warning":
        swarm = context.get("swarm")
        warning = swarm.get("swarm_warning") if isinstance(swarm, Mapping) else None
        passed = not warning
        return AssertionResult(expression, passed, f"swarm_warning={warning!r}")

    match = re.match(r"^(.+?) contains (.+)$", expression)
    if match:
        left_path, needle = match.group(1), match.group(2).strip()
        value = _resolve_path(context, left_path)
        if value is None:
            return AssertionResult(expression, False, f"missing {left_path}")
        passed = needle.lower() in str(value).lower()
        return AssertionResult(expression, passed, f"{left_path}={value!r}")

    match = re.match(r"^(.+?) is (.+)$", expression)
    if match:
        left_path, type_name = match.group(1), match.group(2).strip()
        value = _resolve_path(context, left_path)
        passed = isinstance(value, list) if type_name == "list" else False
        return AssertionResult(expression, passed, f"{left_path} type={type(value).__name__}")

    match = re.match(r"^(.+?) in (.+)$", expression)
    if match and "==" not in expression and ">=" not in expression:
        left_path, options = match.group(1), match.group(2)
        value = _resolve_path(context, left_path)
        allowed = [item.strip() for item in options.split(",")]
        passed = str(value) in allowed
        return AssertionResult(expression, passed, f"{left_path}={value!r} allowed={allowed}")

    return None


def evaluate_assertion(expression: str, context: Mapping[str, Any]) -> AssertionResult:
    expr = expression.strip()
    special = _eval_special(expr, context)
    if special is not None:
        return special

    for op in ("==", ">=", "<=", "!=", ">", "<"):
        if op not in expr:
            continue
        left, right = [part.strip() for part in expr.split(op, 1)]
        left_value = _resolve_path(context, left) if "." in left or "[" in left else context.get(left)
        if right.replace(".", "", 1).isdigit():
            right_value: Any = float(right) if "." in right else int(right)
        elif right.lower() in {"true", "false"}:
            right_value = right.lower() == "true"
        elif (right.startswith('"') and right.endswith('"')) or (right.startswith("'") and right.endswith("'")):
            right_value = right[1:-1]
        elif "." in right or "[" in right:
            right_value = _resolve_path(context, right)
        else:
            right_value = right

        if op == "==":
            passed = left_value == right_value
        elif op == ">=":
            passed = left_value is not None and left_value >= right_value
        elif op == "<=":
            passed = left_value is not None and left_value <= right_value
        elif op == "!=":
            passed = left_value != right_value
        elif op == ">":
            passed = left_value is not None and left_value > right_value
        else:
            passed = left_value is not None and left_value < right_value
        return AssertionResult(expr, passed, f"{left}={left_value!r} {op} {right_value!r}")

    value = _resolve_path(context, expr)
    passed = bool(value)
    return AssertionResult(expr, passed, f"{expr}={value!r}")


def evaluate_assertions(expressions: list[str], context: Mapping[str, Any]) -> list[AssertionResult]:
    return [evaluate_assertion(item, context) for item in expressions]
