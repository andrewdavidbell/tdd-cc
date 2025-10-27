"""Business logic operations for task management (CRUD + filtering/sorting).

This module provides the core business logic for task management operations,
including creating, retrieving, updating, and deleting tasks, as well as
filtering and sorting task lists.

All operations interact with the storage layer to persist changes. The module
uses a singleton storage instance for consistent data access across all operations.

Key Operations:
    - create_task: Create and persist a new task
    - get_task: Retrieve a task by ID
    - list_tasks: List tasks with filtering and sorting
    - update_task_status: Mark tasks as complete or active
    - delete_task: Remove a task from storage
    - clear_completed_tasks: Bulk removal of completed tasks

Example:
    >>> task = create_task(title="Buy groceries", priority="high")
    >>> tasks = list_tasks(status_filter="active", sort_by="priority")
    >>> update_task_status(task.id, "completed")
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
from src.task_manager.models import Task, Priority, Status, ValidationError
from src.task_manager.storage import TaskStorage, TaskNotFoundError, StorageError


# Module-level storage instance (singleton pattern)
DEFAULT_STORAGE_PATH = Path.home() / ".task_manager" / "tasks.json"
storage = TaskStorage(DEFAULT_STORAGE_PATH)

# Mapping dictionaries for string to enum conversion
PRIORITY_MAP = {
    "high": Priority.HIGH,
    "medium": Priority.MEDIUM,
    "low": Priority.LOW
}

STATUS_MAP = {
    "active": Status.ACTIVE,
    "completed": Status.COMPLETED
}

PRIORITY_SORT_ORDER = {
    Priority.HIGH: 0,
    Priority.MEDIUM: 1,
    Priority.LOW: 2
}


def create_task(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    due_date: Optional[datetime] = None
) -> Task:
    """Create a new task and persist to storage.

    Args:
        title: Task title (required, non-empty)
        description: Optional task description
        priority: Priority level (high/medium/low), defaults to medium
        due_date: Optional due date

    Returns:
        The created Task object

    Raises:
        ValidationError: If task data is invalid
        StorageError: If storage operation fails
    """
    # Convert priority string to Priority enum
    priority_enum = PRIORITY_MAP.get(priority.lower(), Priority.MEDIUM)

    # Create task
    task = Task(
        title=title,
        description=description,
        priority=priority_enum,
        due_date=due_date
    )

    # Validate task before persisting
    task.validate()

    # Persist to storage
    storage.add(task)

    return task


def get_task(task_id: str) -> Task:
    """Retrieve a task by ID.

    Args:
        task_id: UUID string of the task

    Returns:
        The requested Task object

    Raises:
        TaskNotFoundError: If task with given ID doesn't exist
    """
    return storage.get_by_id(task_id)


def list_tasks(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    sort_by: str = "created_at"
) -> List[Task]:
    """List tasks with optional filtering and sorting.

    Args:
        status_filter: Filter by status (active/completed), None for all
        priority_filter: Filter by priority (high/medium/low), None for all
        sort_by: Sort field (created_at/due_date/priority), default created_at

    Returns:
        List of Task objects matching filters, sorted as specified
    """
    tasks = storage.get_all()

    # Apply status filter
    if status_filter:
        status_enum = STATUS_MAP.get(status_filter.lower())
        if status_enum:
            tasks = [t for t in tasks if t.status == status_enum]

    # Apply priority filter
    if priority_filter:
        priority_enum = PRIORITY_MAP.get(priority_filter.lower())
        if priority_enum:
            tasks = [t for t in tasks if t.priority == priority_enum]

    # Apply sorting
    if sort_by == "created_at":
        # Sort by created_at descending (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
    elif sort_by == "due_date":
        # Sort by due_date ascending, None values last
        tasks.sort(key=lambda t: (t.due_date is None, t.due_date if t.due_date else datetime.max))
    elif sort_by == "priority":
        # Sort by priority: HIGH=0, MEDIUM=1, LOW=2
        tasks.sort(key=lambda t: PRIORITY_SORT_ORDER.get(t.priority, 999))

    return tasks


def update_task_status(task_id: str, status: str) -> Task:
    """Update a task's status (mark complete or incomplete).

    Args:
        task_id: UUID string of the task
        status: New status (active/completed)

    Returns:
        The updated Task object

    Raises:
        TaskNotFoundError: If task with given ID doesn't exist
    """
    task = storage.get_by_id(task_id)

    # Update status using Task methods
    if status.lower() == "completed":
        task.mark_complete()
    elif status.lower() == "active":
        task.mark_incomplete()

    # Persist changes
    storage.update(task)

    return task


def delete_task(task_id: str) -> None:
    """Delete a task by ID.

    Args:
        task_id: UUID string of the task

    Raises:
        TaskNotFoundError: If task with given ID doesn't exist
    """
    storage.remove(task_id)


def clear_completed_tasks() -> int:
    """Remove all completed tasks from storage.

    Returns:
        Number of tasks removed

    Raises:
        StorageError: If storage operation fails
    """
    tasks = storage.get_all()
    completed_tasks = [t for t in tasks if t.status == Status.COMPLETED]

    for task in completed_tasks:
        storage.remove(task.id)

    return len(completed_tasks)
