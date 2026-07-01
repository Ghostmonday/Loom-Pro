from __future__ import annotations

import sys
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@pytest.mark.skipif(tomllib is None, reason="tomllib (Python 3.11+) or tomli required to run this test")
def test_supervisor_router_package_is_declared() -> None:
    if tomllib is None:
        import pytest

        pytest.skip("Neither tomllib nor tomli is available")

    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    packages = pyproject["tool"]["setuptools"]["packages"]
    assert "aoc_supervisor.routers" in packages
    assert Path("aoc_supervisor/aoc_supervisor/routers/__init__.py").is_file()
