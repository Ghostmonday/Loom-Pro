from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    # tomllib was added in Python 3.11
    # For older versions, we might need a fallback if it's installed
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def test_supervisor_router_package_is_declared() -> None:
    if tomllib is None:
        import pytest
        pytest.skip("Neither tomllib nor tomli is available")

    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    packages = pyproject["tool"]["setuptools"]["packages"]
    assert "aoc_supervisor.routers" in packages
    assert Path("aoc_supervisor/aoc_supervisor/routers/__init__.py").is_file()
