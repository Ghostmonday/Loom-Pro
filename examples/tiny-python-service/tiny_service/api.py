"""Small API facade for task operations."""

from __future__ import annotations

from .service import TaskService
from .storage import InMemoryTaskStore

_service = TaskService(InMemoryTaskStore())


def create_task(title: str) -> dict[str, str]:
    """Create a task and return a serializable response."""
    task = _service.create(title)
    return {"id": task.id, "title": task.title, "status": task.status}


def get_task(task_id: str) -> dict[str, str] | None:
    """Return a task response when it exists."""
    task = _service.get(task_id)
    if task is None:
        return None
    return {"id": task.id, "title": task.title, "status": task.status}
