"""Work-unit assignment invariants."""

from __future__ import annotations

from aoc_cli.blueprint import WorkUnit
from aoc_cli.helpers.workers import _assign_work_units


def _unit(unit_id: str) -> WorkUnit:
    return WorkUnit(
        id=unit_id,
        title=unit_id,
        description=unit_id,
        allowed_paths=(f"{unit_id}/",),
        acceptance_checks=("ok",),
    )


def test_more_workers_than_units_leaves_standby() -> None:
    assignments = _assign_work_units((_unit("WU-1"),), 3)
    assert [unit.id for unit in assignments[1]] == ["WU-1"]
    assert assignments[2] == ()
    assert assignments[3] == ()


def test_each_unit_assigned_once() -> None:
    units = (_unit("WU-1"), _unit("WU-2"), _unit("WU-3"))
    assignments = _assign_work_units(units, 4)
    seen: list[str] = []
    for worker_units in assignments.values():
        for unit in worker_units:
            seen.append(unit.id)
    assert seen == ["WU-1", "WU-2", "WU-3"]


def test_more_units_than_workers_assigns_every_unit_once() -> None:
    units = tuple(_unit(f"WU-{index}") for index in range(1, 6))
    assignments = _assign_work_units(units, 2)

    assigned = [unit.id for worker_units in assignments.values() for unit in worker_units]

    assert sorted(assigned) == sorted(unit.id for unit in units)
    assert len(assigned) == len(set(assigned))
    assert len(assignments[1]) == 3
    assert len(assignments[2]) == 2
