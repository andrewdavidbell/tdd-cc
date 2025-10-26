"""Storage layer for task persistence using JSON.

This module provides atomic file operations, automatic backups, and JSON schema
validation for storing tasks persistently. The TaskStorage class implements a
safe write mechanism using temporary files and atomic renames to prevent data
corruption in case of failures.

Key Features:
    - Atomic writes: Uses temp file + rename to prevent partial updates
    - Automatic backups: Creates .bak file before overwriting existing data
    - JSON schema validation: Ensures loaded data matches expected structure
    - Error handling: Comprehensive error handling with descriptive messages

JSON File Format:
    {
        "tasks": [
            {
                "id": "uuid-string",
                "title": "Task title",
                "description": "Optional description",
                "priority": "high|medium|low",
                "due_date": "ISO 8601 date or null",
                "status": "active|completed",
                "created_at": "ISO 8601 timestamp",
                "completed_at": "ISO 8601 timestamp or null"
            }
        ]
    }
"""

import json
import shutil
from pathlib import Path
from typing import List, Union
from src.task_manager.models import Task


class StorageError(Exception):
    """Raised when storage operations fail.

    This exception is raised for file I/O errors, permission issues,
    JSON parsing errors, or schema validation failures.

    Examples:
        - Failed to create storage directory
        - Permission denied when writing file
        - Corrupted JSON file
        - Invalid JSON schema
        - Disk full error
    """
    pass


class TaskNotFoundError(Exception):
    """Raised when a task with given ID is not found.

    This exception is raised when attempting to retrieve, update, or delete
    a task that doesn't exist in storage.

    Attributes:
        message: Description of which task ID was not found
    """
    pass


class TaskStorage:
    """Manages task persistence to JSON file with atomic writes and backups.

    This class provides a safe and reliable storage mechanism for tasks using JSON
    file format. It implements atomic write operations (write to temp file, then
    rename) to prevent data corruption, and automatically creates backups before
    overwriting existing files.

    The storage automatically creates the necessary directory structure and
    initialises an empty task file if it doesn't exist.

    Attributes:
        file_path (Path): Path to the JSON storage file

    Example:
        >>> storage = TaskStorage(Path("~/.task_manager/tasks.json"))
        >>> task = Task(title="Buy milk")
        >>> storage.add(task)
        >>> all_tasks = storage.get_all()
    """

    def __init__(self, file_path: Union[Path, str]) -> None:
        """Initialise TaskStorage with file path.

        Creates parent directory and empty file if they don't exist. This
        ensures the storage is ready for use immediately after instantiation.

        Args:
            file_path: Path to JSON file for storing tasks (accepts Path object or string)

        Note:
            If the file doesn't exist, it will be created with an empty task list.
            If the parent directory doesn't exist, it will be created as well.
        """
        self.file_path = Path(file_path)

        # Create parent directory if it doesn't exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create empty file if it doesn't exist
        if not self.file_path.exists():
            self._write_json({'tasks': []})

    def _validate_schema(self, data: dict) -> None:
        """Validate that JSON data has correct schema.

        Args:
            data: Dictionary loaded from JSON

        Raises:
            StorageError: If schema is invalid
        """
        if 'tasks' not in data:
            raise StorageError("Invalid JSON schema: missing 'tasks' key")

    def load(self) -> List[Task]:
        """Load tasks from JSON file.

        Reads the JSON file, validates its schema, and deserialises all tasks
        into Task objects. If the file contains invalid JSON or doesn't match
        the expected schema, a StorageError is raised.

        Returns:
            List of Task objects loaded from storage (empty list if no tasks)

        Raises:
            StorageError: If file cannot be loaded, JSON is invalid, or schema is incorrect
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._validate_schema(data)

            # Deserialise all task dictionaries into Task objects
            tasks = []
            for task_dict in data['tasks']:
                tasks.append(Task.from_dict(task_dict))

            return tasks

        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to load tasks: Invalid JSON format - {e}")
        except (OSError, IOError) as e:
            raise StorageError(f"Failed to load tasks: {e}")

    def save(self, tasks: List[Task]) -> None:
        """Save tasks to JSON file using atomic write.

        This method serialises all tasks to JSON format and writes them to the
        storage file using an atomic write operation (write to temp file, then
        rename). Before writing, it creates a backup of the existing file if
        one exists with content.

        The atomic write ensures that the file is never left in a partially
        written state, protecting against corruption if the process is interrupted.

        Args:
            tasks: List of Task objects to save to storage

        Raises:
            StorageError: If file cannot be written due to permissions, disk space, etc.
        """
        try:
            # Create backup if file exists and has content
            if self.file_path.exists() and self.file_path.stat().st_size > 0:
                self._create_backup()

            # Serialise tasks to dictionaries
            task_dicts = [task.to_dict() for task in tasks]
            data = {'tasks': task_dicts}

            # Atomic write to prevent partial updates
            self._atomic_write(data)

        except (OSError, IOError) as e:
            raise StorageError(f"Failed to save tasks: {e}")

    def get_all(self) -> List[Task]:
        """Get all tasks from storage.

        Loads and returns all tasks from the JSON file. Each invocation reads
        from the file, ensuring fresh data is retrieved.

        Returns:
            List of all Task objects (empty list if no tasks exist)

        Raises:
            StorageError: If file cannot be read or contains invalid data
        """
        return self.load()

    def get_by_id(self, task_id: str) -> Task:
        """Get task by ID.

        Searches through all tasks to find one matching the given ID. This
        operation loads all tasks from storage and performs a linear search.

        Args:
            task_id: Unique identifier of the task to retrieve

        Returns:
            Task object with matching ID

        Raises:
            TaskNotFoundError: If no task with the given ID exists in storage
            StorageError: If file cannot be read or contains invalid data
        """
        tasks = self.load()
        for task in tasks:
            if task.id == task_id:
                return task

        raise TaskNotFoundError(f"Task with ID '{task_id}' not found")

    def add(self, task: Task) -> None:
        """Add task to storage.

        Adds a new task to storage and persists it immediately. Validates that
        no task with the same ID already exists before adding.

        Args:
            task: Task object to add to storage

        Raises:
            StorageError: If task with same ID already exists or file cannot be written
        """
        tasks = self.load()

        # Check for duplicate ID
        if any(t.id == task.id for t in tasks):
            raise StorageError(f"Task with ID '{task.id}' already exists")

        tasks.append(task)
        self.save(tasks)

    def remove(self, task_id: str) -> None:
        """Remove task from storage.

        Deletes the task with the specified ID and persists the change
        immediately. If no task with the given ID exists, raises an error.

        Args:
            task_id: Unique identifier of the task to remove

        Raises:
            TaskNotFoundError: If no task with the given ID exists in storage
            StorageError: If file cannot be written after removal
        """
        tasks = self.load()

        # Find and remove task
        task_found = False
        filtered_tasks = []
        for task in tasks:
            if task.id == task_id:
                task_found = True
            else:
                filtered_tasks.append(task)

        if not task_found:
            raise TaskNotFoundError(f"Task with ID '{task_id}' not found")

        self.save(filtered_tasks)

    def update(self, task: Task) -> None:
        """Update existing task in storage.

        Replaces an existing task with the provided task object (matching by ID)
        and persists the change immediately. The task ID must exist in storage.

        Args:
            task: Task object with updated data (ID must match existing task)

        Raises:
            TaskNotFoundError: If no task with matching ID exists in storage
            StorageError: If file cannot be written after update
        """
        tasks = self.load()

        # Find and update task
        task_found = False
        updated_tasks = []
        for existing_task in tasks:
            if existing_task.id == task.id:
                task_found = True
                updated_tasks.append(task)
            else:
                updated_tasks.append(existing_task)

        if not task_found:
            raise TaskNotFoundError(f"Task with ID '{task.id}' not found")

        self.save(updated_tasks)

    def _atomic_write(self, data: dict) -> None:
        """Write data to file atomically using temp file and rename.

        This method implements atomic write semantics by writing to a temporary
        file first, then atomically renaming it to the target file. This ensures
        that the file is never left in a partially written state, even if the
        process is killed during the write operation.

        The rename operation is atomic on POSIX systems (Linux, macOS), providing
        strong guarantees against corruption.

        Args:
            data: Dictionary to write as JSON (will be formatted with 2-space indent)

        Raises:
            OSError: If write fails due to permissions, disk space, etc.
        """
        # Write to temp file first
        temp_path = self.file_path.with_suffix('.json.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            # Atomic rename (POSIX atomic operation)
            shutil.move(str(temp_path), str(self.file_path))

        finally:
            # Clean up temp file if it still exists (e.g., if rename failed)
            if temp_path.exists():
                temp_path.unlink()

    def _create_backup(self) -> None:
        """Create backup copy of current file.

        Creates a backup file with .bak extension before performing destructive
        operations. The backup preserves metadata (timestamps, permissions) using
        copy2. If a previous backup exists, it will be overwritten.

        The backup file is named by appending .bak to the original filename
        (e.g., tasks.json -> tasks.json.bak).

        Raises:
            OSError: If backup creation fails due to permissions or disk space
        """
        backup_path = self.file_path.with_suffix('.json.bak')
        shutil.copy2(str(self.file_path), str(backup_path))

    def _write_json(self, data: dict) -> None:
        """Write JSON data to file (simple write, not atomic).

        This is a simple write operation used only during initialisation when
        creating an empty storage file. For all other writes, use save() which
        provides atomic write semantics.

        Args:
            data: Dictionary to write as JSON (will be formatted with 2-space indent)

        Raises:
            OSError: If write fails
        """
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
