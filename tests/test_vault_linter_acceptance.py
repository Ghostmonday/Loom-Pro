"""Regression: vault_linter acceptance must not double worker-relative paths."""

from __future__ import annotations

import os
from pathlib import Path

from aoc_cli.helpers.merge import run_acceptance_check


def test_vault_linter_uses_toolchain_root_not_worker_sandbox(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    worker = vault / ".gaijinn" / "workers" / "worker-001"
    ops = vault / "10_Operations"
    ops.mkdir(parents=True)
    worker.mkdir(parents=True)
    linter = ops / "knowledge-linter.py"
    linter.write_text(
        "#!/usr/bin/env python3\nimport sys\nprint('VAULT LINTER: PASS')\nsys.exit(0)\n",
        encoding="utf-8",
    )
    # Worker copy would fail if invoked — must not be used.
    (worker / "10_Operations").mkdir(parents=True)
    (worker / "10_Operations" / "knowledge-linter.py").write_text(
        "import sys\nprint('WRONG LINTER')\nsys.exit(1)\n",
        encoding="utf-8",
    )
    code, output = run_acceptance_check(
        worker,
        "vault_linter",
        toolchain_root=vault,
        env={**os.environ, "GAIJINN_PROJECT_ROOT": str(worker.resolve())},
    )
    assert code == 0, output
    assert "PASS" in output
    assert "WRONG" not in output
