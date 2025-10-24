"""Domain models for Task Manager.

This module contains the core domain models for the task management system,
including task priority levels, status values, and the Task entity itself.
"""

from enum import Enum
from datetime import datetime
from uuid import uuid4
from typing import Optional


class Priority(Enum):
    """Task priority levels.

    Attributes:
        HIGH: High priority task
        MEDIUM: Medium priority task (default)
        LOW: Low priority task
    """
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class Status(Enum):
    """Task status values.

    Attributes:
        ACTIVE: Task is active and not yet completed
        COMPLETED: Task has been marked as complete
    """
    ACTIVE = 'active'
    COMPLETED = 'completed'


class ValidationError(Exception):
    """Raised when task validation fails.

    This exception is raised when task data does not meet validation requirements,
    such as empty titles, excessive length, or invalid date ranges.
    """
    pass


class Task:
    """Represents a task with title, description, priority, and due date.

    A Task is the core entity in the task management system. Each task has a unique
    identifier, title, optional description, priority level, optional due date, and
    tracks its creation time and completion status.

    Attributes:
        id (str): Unique identifier (UUID)
        title (str): Task title (required, max 200 characters)
        description (Optional[str]): Task description (max 1000 characters)
        priority (Priority): Task priority level (HIGH, MEDIUM, or LOW)
        due_date (Optional[datetime]): When the task is due
        status (Status): Current status (ACTIVE or COMPLETED)
        created_at (datetime): When the task was created
        completed_at (Optional[datetime]): When the task was completed (None if active)
    """

    def __init__(
        self,
        title: str,
        description: Optional[str] = None,
        priority: Priority = Priority.MEDIUM,
        due_date: Optional[datetime] = None,
        id: Optional[str] = None,
        status: Status = Status.ACTIVE,
        created_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ):
        """Initialise a new Task.

        Args:
            title: The task title (required, will be stripped of whitespace)
            description: Optional task description
            priority: Task priority level (default: MEDIUM)
            due_date: Optional due date (must be a datetime object or None)
            id: Optional task ID (auto-generated UUID if not provided)
            status: Task status (default: ACTIVE)
            created_at: Optional creation timestamp (auto-set to now if not provided)
            completed_at: Optional completion timestamp (None for new tasks)

        Raises:
            ValueError: If priority is not a Priority enum
            TypeError: If due_date is not a datetime object or None
        """
        # Validate priority is a Priority enum
        if not isinstance(priority, Priority):
            raise ValueError(f"Invalid priority: {priority}")

        # Validate due_date is a datetime or None
        if due_date is not None and not isinstance(due_date, datetime):
            raise TypeError(f"Invalid due_date type: {type(due_date)}")

        self.id = id if id else str(uuid4())
        self.title = title.strip() if title else title
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.status = status
        self.created_at = created_at if created_at else datetime.now()
        self.completed_at = completed_at

    def validate(self) -> None:
        """Validate task data against business rules.

        Checks that the task meets all validation requirements:
        - Title is not empty and not exceeds 200 characters
        - Description does not exceed 1000 characters
        - Due date is not in the past

        Raises:
            ValidationError: If any validation rule is violated
        """
        # Validate title
        if not self.title or not self.title.strip():
            raise ValidationError("Title cannot be empty")

        if len(self.title) > 200:
            raise ValidationError("Title cannot exceed 200 characters")

        # Validate description
        if self.description and len(self.description) > 1000:
            raise ValidationError("Description cannot exceed 1000 characters")

        # Validate due date
        if self.due_date and self.due_date < datetime.now():
            raise ValidationError("Due date cannot be in the past")

    def mark_complete(self) -> None:
        """Mark task as completed.

        Sets the task status to COMPLETED and records the completion timestamp.
        This method is idempotent - calling it multiple times has the same effect.
        """
        self.status = Status.COMPLETED
        self.completed_at = datetime.now()

    def mark_incomplete(self) -> None:
        """Mark task as active (incomplete).

        Sets the task status to ACTIVE and clears the completion timestamp.
        This effectively "uncompletes" a task.
        """
        self.status = Status.ACTIVE
        self.completed_at = None

    def to_dict(self) -> dict:
        """Serialise task to dictionary.

        Converts the task to a dictionary representation suitable for JSON
        serialisation or storage. Enum values are converted to strings, and
        datetime objects are converted to ISO format strings.

        Returns:
            dict: Dictionary containing all task fields
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value if isinstance(self.priority, Priority) else self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status.value if isinstance(self.status, Status) else self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Create Task from dictionary.

        Deserialises a task from a dictionary representation, typically loaded
        from JSON storage. Handles parsing of ISO format datetime strings and
        enum string values.

        Args:
            data: Dictionary containing task data with at minimum 'id' and 'title' keys

        Returns:
            Task: A new Task instance created from the dictionary data

        Raises:
            KeyError: If required fields ('id' or 'title') are missing
            ValueError: If enum values are invalid
        """
        # Parse datetime fields
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])

        completed_at = None
        if data.get('completed_at'):
            completed_at = datetime.fromisoformat(data['completed_at'])

        due_date = None
        if data.get('due_date'):
            due_date = datetime.fromisoformat(data['due_date'])

        # Parse enum fields
        priority = Priority(data.get('priority', 'medium'))
        status = Status(data.get('status', 'active'))

        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description'),
            priority=priority,
            due_date=due_date,
            status=status,
            created_at=created_at,
            completed_at=completed_at
        )

    def __eq__(self, other) -> bool:
        """Check equality based on task ID.

        Two tasks are considered equal if they have the same ID, regardless
        of other field values.

        Args:
            other: Object to compare with

        Returns:
            bool: True if other is a Task with the same ID, False otherwise
        """
        if not isinstance(other, Task):
            return False
        return self.id == other.id
