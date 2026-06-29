"""Business logic for the tiny task service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    status: str = "open"


class TaskStore(Protocol):
    def save(self, task: Task) -> None:
        """Persist a task."""

    def get(self, task_id: str) -> Task | None:
        """Fetch a task by id."""


class TaskService:
    def __init__(self, store: TaskStore) -> None:
        self._store = store

    def create(self, title: str) -> Task:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("title must not be empty")
        task = Task(id=uuid4().hex, title=clean_title)
        self._store.save(task)
        return task

    def get(self, task_id: str) -> Task | None:
        return self._store.get(task_id)
