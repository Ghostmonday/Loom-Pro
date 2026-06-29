from __future__ import annotations

import pytest
from tiny_service.api import create_task, get_task
from tiny_service.service import TaskService
from tiny_service.storage import InMemoryTaskStore


def test_create_and_get_task() -> None:
    created = create_task("Write smoke test")

    found = get_task(created["id"])

    assert found == {
        "id": created["id"],
        "title": "Write smoke test",
        "status": "open",
    }


def test_service_rejects_empty_title() -> None:
    service = TaskService(InMemoryTaskStore())

    with pytest.raises(ValueError, match="title must not be empty"):
        service.create("  ")


def test_task_payload_is_terminal_safe() -> None:
    created = create_task("Terminal bridge smoke task")

    assert set(created) == {"id", "title", "status"}
    assert isinstance(created["id"], str)
    assert created["title"] == "Terminal bridge smoke task"
    assert created["status"] == "open"
