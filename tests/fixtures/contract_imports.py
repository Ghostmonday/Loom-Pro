"""Guarded imports for Perfect SPEC Interrogation contract tests.

Collection must succeed before production modules land. Runtime tests fail with
canonical DoD references instead of skipping or weakening assertions.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, TypeVar

import pytest

_WORKTREE_AOC = Path(__file__).resolve().parents[2] / "aoc_supervisor"
if _WORKTREE_AOC.is_dir():
    worktree_path = str(_WORKTREE_AOC)
    if sys.path[0] != worktree_path:
        if worktree_path in sys.path:
            sys.path.remove(worktree_path)
        sys.path.insert(0, worktree_path)
    for module_name in list(sys.modules):
        if module_name == "aoc_supervisor" or module_name.startswith("aoc_supervisor."):
            del sys.modules[module_name]

T = TypeVar("T")


def module_available(module_path: str) -> bool:
    return importlib.util.find_spec(module_path) is not None


def _purge_stale_module(module_path: str) -> None:
    if not _WORKTREE_AOC.is_dir():
        return
    worktree_root = str(_WORKTREE_AOC.resolve())
    cached = sys.modules.get(module_path)
    if cached is None:
        return
    module_file = str(getattr(cached, "__file__", "") or "")
    if module_file and worktree_root not in module_file:
        del sys.modules[module_path]


def require_module(module_path: str, attr: str, *, dod: str) -> Any:
    """Import a production symbol or fail with a canonical DoD reference."""
    if not module_available(module_path):
        pytest.fail(f"{dod}: production module `{module_path}` is required by PERFECT-SPEC-INTERROGATION")
    _purge_stale_module(module_path)
    module = importlib.import_module(module_path)
    if not hasattr(module, attr):
        _purge_stale_module(module_path)
        module = importlib.import_module(module_path)
    if not hasattr(module, attr):
        pytest.fail(f"{dod}: `{module_path}.{attr}` must exist per canonical contract")
    return getattr(module, attr)


def require_callable(module_path: str, attr: str, *, dod: str) -> Any:
    obj = require_module(module_path, attr, dod=dod)
    if not callable(obj):
        pytest.fail(f"{dod}: `{module_path}.{attr}` must be callable")
    return obj
