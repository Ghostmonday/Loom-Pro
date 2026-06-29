#!/usr/bin/env python3
"""Backfill vault completion-ledger.json after destructive cleanup.

Seeds ledger entries from:
  1. Authoritative dogfood merge (events [63], 6 workers @ 2026-06-18T07:20:02Z)
  2. Current blueprint work units (converged vault — plan backlog should be 0)

Usage:
  python scripts/ops/backfill-completion-ledger.py
  python scripts/ops/backfill-completion-ledger.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VAULT = ROOT / "vaults" / "gaijinn-memory-fs"
sys.path[:0] = [str(ROOT / "aoc-cli"), str(ROOT / "aoc_supervisor")]

from aoc_cli.blueprint import stable_work_unit_id  # noqa: E402
from aoc_cli.helpers.merge import (  # noqa: E402
    archive_merge_artifacts,
    content_hash_for_allowed_paths,
    load_completion_ledger,
    upsert_completion_ledger_entries,
    utc_now,
)

DOGFOOD_MERGE_AT = "2026-06-18T07:20:02Z"
BACKFILL_SOURCE = "backfill-2026-06-19"

# Stable ids verified via stable_work_unit_id(allowed_paths, acceptance_checks).
DOGFOOD_SPECS: list[dict[str, Any]] = [
    {
        "worker_id": "worker-001",
        "merged_at": DOGFOOD_MERGE_AT,
        "allowed_paths": [
            ".agents/codex-deepseek.toml.example",
            ".agents/hermes-deepseek.env.example",
        ],
        "acceptance_checks": [
            "review metrics manifest for rejected nodes or Shadow Bridges",
            "vault_linter",
        ],
    },
    {
        "worker_id": "worker-002",
        "merged_at": DOGFOOD_MERGE_AT,
        "allowed_paths": [
            "10_Operations/HERMES-DEVELOPMENT-ORDERS.md",
            "40_Concepts/event-sourcing-vault.md",
        ],
        "acceptance_checks": [
            "review metrics manifest for rejected nodes or Shadow Bridges",
            "vault_linter",
        ],
    },
    {
        "worker_id": "worker-003",
        "merged_at": DOGFOOD_MERGE_AT,
        "allowed_paths": ["aoc_supervisor/aoc_supervisor/preflight.py"],
        "acceptance_checks": ["vault_linter"],
    },
    {
        "worker_id": "worker-004",
        "merged_at": DOGFOOD_MERGE_AT,
        "allowed_paths": [
            "aoc_supervisor/aoc_supervisor/api.py",
            "aoc_supervisor/aoc_supervisor/billing.py",
            "aoc_supervisor/aoc_supervisor/__init__.py",
        ],
        "acceptance_checks": [
            "review metrics manifest for rejected nodes or Shadow Bridges",
            "vault_linter",
        ],
    },
    {
        "worker_id": "worker-005",
        "merged_at": DOGFOOD_MERGE_AT,
        "allowed_paths": [".cursorrules"],
        "acceptance_checks": ["vault_linter"],
    },
    {
        "worker_id": "worker-006",
        "merged_at": DOGFOOD_MERGE_AT,
        "allowed_paths": ["20_Projects/deepseek-codex-setup.md"],
        "acceptance_checks": ["vault_linter"],
    },
]


def _ledger_entry(
    project_root: Path,
    *,
    worker_id: str,
    merged_at: str,
    allowed_paths: list[str],
    acceptance_checks: list[str],
) -> dict[str, Any]:
    wu_id = stable_work_unit_id(allowed_paths, acceptance_checks)
    return {
        "wu_id": wu_id,
        "content_hash": content_hash_for_allowed_paths(project_root, allowed_paths),
        "merged_at": merged_at,
        "worker_id": worker_id,
        "allowed_paths": allowed_paths,
        "acceptance_checks": acceptance_checks,
        "source": BACKFILL_SOURCE,
    }


def _entries_from_blueprint(project_root: Path, blueprint_payload: dict[str, Any]) -> list[dict[str, Any]]:
    merged_at = utc_now()
    entries: list[dict[str, Any]] = []
    work_units = blueprint_payload.get("work_units", [])
    if not isinstance(work_units, list):
        return entries
    for index, unit in enumerate(work_units, start=1):
        if not isinstance(unit, dict):
            continue
        allowed_paths = unit.get("allowed_paths", [])
        acceptance_checks = unit.get("acceptance_checks", [])
        if not isinstance(allowed_paths, list) or not isinstance(acceptance_checks, list):
            continue
        entries.append(
            _ledger_entry(
                project_root,
                worker_id=f"blueprint-{index:03d}",
                merged_at=merged_at,
                allowed_paths=[str(path) for path in allowed_paths],
                acceptance_checks=[str(check) for check in acceptance_checks],
            )
        )
    return entries


def _entries_from_dogfood(project_root: Path) -> list[dict[str, Any]]:
    return [
        _ledger_entry(
            project_root,
            worker_id=spec["worker_id"],
            merged_at=spec["merged_at"],
            allowed_paths=list(spec["allowed_paths"]),
            acceptance_checks=list(spec["acceptance_checks"]),
        )
        for spec in DOGFOOD_SPECS
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill vault completion ledger")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--vault", type=Path, default=VAULT)
    args = parser.parse_args()

    vault = args.vault.resolve()
    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1

    blueprint_path = vault / ".gaijinn" / "blueprint.json"
    if not blueprint_path.exists():
        print(f"blueprint missing: {blueprint_path}", file=sys.stderr)
        return 1

    blueprint_payload = json.loads(blueprint_path.read_text(encoding="utf-8"))
    before = load_completion_ledger(vault)
    before_count = len(before.get("entries", []))

    entries_by_wu: dict[str, dict[str, Any]] = {}
    for entry in _entries_from_dogfood(vault) + _entries_from_blueprint(vault, blueprint_payload):
        entries_by_wu[entry["wu_id"]] = entry

    entries = [entries_by_wu[wu_id] for wu_id in sorted(entries_by_wu)]
    print(f"backfill: {before_count} -> {len(entries)} ledger entries ({len(DOGFOOD_SPECS)} dogfood + blueprint)")

    if args.dry_run:
        for entry in entries[:8]:
            print(f"  {entry['wu_id']} worker={entry['worker_id']} hash={entry['content_hash'][:12]}...")
        if len(entries) > 8:
            print(f"  ... +{len(entries) - 8} more")
        return 0

    archive_dir = archive_merge_artifacts(vault, label=BACKFILL_SOURCE)
    print(f"archived prior merge artifacts -> {archive_dir}")

    changed = upsert_completion_ledger_entries(vault, entries, allow_wipe=True)
    print(f"upserted {changed} changed entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
