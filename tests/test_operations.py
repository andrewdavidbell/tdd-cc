"""Tests for business logic operations (CRUD + filtering/sorting)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.task_manager.models import Task, Priority, Status, ValidationError
from src.task_manager.storage import TaskNotFoundError, StorageError
from src.task_manager import operations


# Fixtures for test setup

@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        id="test-id-001",
        title="Test Task",
        description="Test Description",
        priority=Priority.HIGH,
        status=Status.ACTIVE,
        created_at=datetime(2025, 10, 27, 10, 0, 0)
    )


@pytest.fixture
def sample_tasks():
    """Create multiple sample tasks with various properties for testing."""
    return [
        Task(
            id="task-001",
            title="High Priority Active Task",
            priority=Priority.HIGH,
            status=Status.ACTIVE,
            created_at=datetime(2025, 10, 27, 10, 0, 0),
            due_date=datetime(2025, 10, 30)
        ),
        Task(
            id="task-002",
            title="Medium Priority Completed Task",
            priority=Priority.MEDIUM,
            status=Status.COMPLETED,
            created_at=datetime(2025, 10, 26, 10, 0, 0),
            completed_at=datetime(2025, 10, 26, 15, 0, 0)
        ),
        Task(
            id="task-003",
            title="Low Priority Active Task",
            priority=Priority.LOW,
            status=Status.ACTIVE,
            created_at=datetime(2025, 10, 25, 10, 0, 0),
            due_date=datetime(2025, 11, 5)
        ),
        Task(
            id="task-004",
            title="High Priority Completed Task",
            priority=Priority.HIGH,
            status=Status.COMPLETED,
            created_at=datetime(2025, 10, 24, 10, 0, 0),
            completed_at=datetime(2025, 10, 25, 10, 0, 0),
            due_date=datetime(2025, 10, 28)
        ),
        Task(
            id="task-005",
            title="Medium Priority Active Task No Due Date",
            priority=Priority.MEDIUM,
            status=Status.ACTIVE,
            created_at=datetime(2025, 10, 23, 10, 0, 0)
        ),
    ]


@pytest.fixture(autouse=True)
def reset_storage():
    """Reset storage before each test to ensure clean state."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = []
        yield mock_storage


# Test Create Task

def test_create_task_with_minimal_fields():
    """Create task with only title."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        task = operations.create_task(title="Buy groceries")
        assert task.title == "Buy groceries"
        assert task.priority == Priority.MEDIUM  # default
        assert task.status == Status.ACTIVE  # default
        mock_storage.add.assert_called_once()


def test_create_task_with_all_fields():
    """Create task with all optional fields provided."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        due_date = datetime.now() + timedelta(days=1)
        task = operations.create_task(
            title="Complete project",
            description="Finish the implementation",
            priority="high",
            due_date=due_date
        )
        assert task.title == "Complete project"
        assert task.description == "Finish the implementation"
        assert task.priority == Priority.HIGH
        assert task.due_date == due_date
        mock_storage.add.assert_called_once()


def test_create_task_validates_input():
    """Creating task with invalid input raises ValidationError."""
    with pytest.raises(ValidationError):
        operations.create_task(title="")  # empty title


def test_create_task_persists_to_storage():
    """Created task is saved via storage."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        task = operations.create_task(title="Test Task")
        mock_storage.add.assert_called_once_with(task)


def test_create_task_returns_task_object():
    """create_task returns a Task object."""
    with patch('src.task_manager.operations.storage'):
        task = operations.create_task(title="Test Task")
        assert isinstance(task, Task)
        assert task.title == "Test Task"


# Test Get Task

def test_get_existing_task(sample_task):
    """Retrieve existing task by ID."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_by_id.return_value = sample_task
        task = operations.get_task("test-id-001")
        assert task.id == "test-id-001"
        assert task.title == "Test Task"


def test_get_nonexistent_task_raises_error():
    """Getting non-existent task raises TaskNotFoundError."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_by_id.side_effect = TaskNotFoundError("Task not found")
        with pytest.raises(TaskNotFoundError):
            operations.get_task("nonexistent-id")


def test_get_task_returns_correct_task(sample_tasks):
    """get_task returns the correct task when multiple tasks exist."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_by_id.return_value = sample_tasks[2]
        task = operations.get_task("task-003")
        assert task.id == "task-003"
        assert task.title == "Low Priority Active Task"


# Test List Tasks

def test_list_all_tasks_empty():
    """List tasks returns empty list when no tasks exist."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = []
        tasks = operations.list_tasks()
        assert tasks == []


def test_list_all_tasks(sample_tasks):
    """List all tasks without filters returns all tasks."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks()
        assert len(tasks) == 5


def test_list_tasks_filter_by_active_status(sample_tasks):
    """Filter tasks by active status returns only active tasks."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(status_filter="active")
        assert len(tasks) == 3
        assert all(task.status == Status.ACTIVE for task in tasks)


def test_list_tasks_filter_by_completed_status(sample_tasks):
    """Filter tasks by completed status returns only completed tasks."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(status_filter="completed")
        assert len(tasks) == 2
        assert all(task.status == Status.COMPLETED for task in tasks)


def test_list_tasks_filter_by_high_priority(sample_tasks):
    """Filter tasks by high priority returns only high priority tasks."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(priority_filter="high")
        assert len(tasks) == 2
        assert all(task.priority == Priority.HIGH for task in tasks)


def test_list_tasks_filter_by_medium_priority(sample_tasks):
    """Filter tasks by medium priority returns only medium priority tasks."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(priority_filter="medium")
        assert len(tasks) == 2
        assert all(task.priority == Priority.MEDIUM for task in tasks)


def test_list_tasks_filter_by_low_priority(sample_tasks):
    """Filter tasks by low priority returns only low priority tasks."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(priority_filter="low")
        assert len(tasks) == 1
        assert all(task.priority == Priority.LOW for task in tasks)


def test_list_tasks_combined_filters(sample_tasks):
    """Combined status and priority filters work correctly."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(status_filter="active", priority_filter="high")
        assert len(tasks) == 1
        assert tasks[0].id == "task-001"
        assert tasks[0].status == Status.ACTIVE
        assert tasks[0].priority == Priority.HIGH


def test_list_tasks_sort_by_created_at_desc(sample_tasks):
    """Default sort by created_at returns newest first."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(sort_by="created_at")
        assert tasks[0].id == "task-001"  # newest
        assert tasks[-1].id == "task-005"  # oldest


def test_list_tasks_sort_by_due_date_asc(sample_tasks):
    """Sort by due_date returns earliest due date first."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(sort_by="due_date")
        # Tasks with due dates should come first, sorted by date
        assert tasks[0].due_date is not None
        # Verify tasks with due dates are sorted correctly
        tasks_with_dates = [t for t in tasks if t.due_date is not None]
        assert tasks_with_dates[0].id == "task-004"  # 2025-10-28
        assert tasks_with_dates[1].id == "task-001"  # 2025-10-30
        assert tasks_with_dates[2].id == "task-003"  # 2025-11-05


def test_list_tasks_sort_by_due_date_none_last(sample_tasks):
    """Tasks without due dates appear last when sorting by due_date."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(sort_by="due_date")
        # Last tasks should have no due date
        tasks_without_dates = [t for t in tasks if t.due_date is None]
        assert len(tasks_without_dates) == 2  # task-002 and task-005


def test_list_tasks_sort_by_priority(sample_tasks):
    """Sort by priority returns high→medium→low."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(sort_by="priority")
        # Group by priority and verify order
        priorities = [task.priority for task in tasks]
        high_count = priorities.count(Priority.HIGH)
        medium_count = priorities.count(Priority.MEDIUM)
        low_count = priorities.count(Priority.LOW)

        # Verify high priority tasks come first
        assert all(p == Priority.HIGH for p in priorities[:high_count])
        # Then medium priority
        assert all(p == Priority.MEDIUM for p in priorities[high_count:high_count + medium_count])
        # Then low priority
        assert all(p == Priority.LOW for p in priorities[high_count + medium_count:])


def test_list_tasks_filter_and_sort(sample_tasks):
    """Combined filtering and sorting work correctly."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        tasks = operations.list_tasks(status_filter="active", sort_by="priority")
        assert len(tasks) == 3
        # Verify all are active
        assert all(task.status == Status.ACTIVE for task in tasks)
        # Verify sorted by priority (high first)
        assert tasks[0].priority == Priority.HIGH
        assert tasks[-1].priority == Priority.LOW


# Test Update Task Status

def test_mark_task_complete(sample_task):
    """Mark active task as completed."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_by_id.return_value = sample_task
        task = operations.update_task_status("test-id-001", "completed")
        assert task.status == Status.COMPLETED


def test_mark_task_incomplete(sample_tasks):
    """Mark completed task as active."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        completed_task = sample_tasks[1]  # completed task
        mock_storage.get_by_id.return_value = completed_task
        task = operations.update_task_status("task-002", "active")
        assert task.status == Status.ACTIVE


def test_mark_complete_sets_timestamp(sample_task):
    """Marking task complete sets completed_at timestamp."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_by_id.return_value = sample_task
        task = operations.update_task_status("test-id-001", "completed")
        assert task.completed_at is not None
        assert isinstance(task.completed_at, datetime)


def test_mark_incomplete_clears_timestamp(sample_tasks):
    """Marking task incomplete clears completed_at timestamp."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        completed_task = sample_tasks[1]
        mock_storage.get_by_id.return_value = completed_task
        task = operations.update_task_status("task-002", "active")
        assert task.completed_at is None


def test_update_status_persists_to_storage(sample_task):
    """Status change is persisted to storage."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_by_id.return_value = sample_task
        operations.update_task_status("test-id-001", "completed")
        mock_storage.update.assert_called_once()


def test_update_nonexistent_task_raises_error():
    """Updating non-existent task raises TaskNotFoundError."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_by_id.side_effect = TaskNotFoundError("Task not found")
        with pytest.raises(TaskNotFoundError):
            operations.update_task_status("nonexistent-id", "completed")


def test_mark_already_completed_task_complete(sample_tasks):
    """Marking already completed task as complete is idempotent."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        completed_task = sample_tasks[1]
        original_completed_at = completed_task.completed_at
        mock_storage.get_by_id.return_value = completed_task
        task = operations.update_task_status("task-002", "completed")
        assert task.status == Status.COMPLETED
        # Should maintain the task's current state


# Test Delete Task

def test_delete_existing_task():
    """Delete existing task successfully."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        operations.delete_task("test-id-001")
        mock_storage.remove.assert_called_once_with("test-id-001")


def test_delete_nonexistent_task_raises_error():
    """Deleting non-existent task raises TaskNotFoundError."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.remove.side_effect = TaskNotFoundError("Task not found")
        with pytest.raises(TaskNotFoundError):
            operations.delete_task("nonexistent-id")


def test_delete_persists_to_storage():
    """Task deletion is persisted to storage."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        operations.delete_task("test-id-001")
        # Verify storage.remove was called
        assert mock_storage.remove.called


def test_delete_removes_correct_task(sample_tasks):
    """Deletion removes only the specified task."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        operations.delete_task("task-003")
        mock_storage.remove.assert_called_with("task-003")


# Test Clear Completed Tasks

def test_clear_completed_tasks_removes_all_completed(sample_tasks):
    """Clear completed tasks removes all completed tasks."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        count = operations.clear_completed_tasks()
        # Should remove 2 completed tasks
        assert count == 2
        # Verify remove was called twice
        assert mock_storage.remove.call_count == 2


def test_clear_completed_tasks_preserves_active(sample_tasks):
    """Clear completed tasks preserves active tasks."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        operations.clear_completed_tasks()
        # Verify remove was only called for completed tasks
        removed_ids = [call[0][0] for call in mock_storage.remove.call_args_list]
        assert "task-002" in removed_ids  # completed
        assert "task-004" in removed_ids  # completed
        assert "task-001" not in removed_ids  # active
        assert "task-003" not in removed_ids  # active
        assert "task-005" not in removed_ids  # active


def test_clear_completed_tasks_empty_list():
    """Clear completed tasks with no completed tasks returns 0."""
    active_only = [
        Task(
            id="task-001",
            title="Active Task",
            status=Status.ACTIVE,
            created_at=datetime.now()
        )
    ]
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = active_only
        count = operations.clear_completed_tasks()
        assert count == 0
        mock_storage.remove.assert_not_called()


def test_clear_completed_tasks_persists_to_storage(sample_tasks):
    """Clear completed tasks persists changes to storage."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        operations.clear_completed_tasks()
        # Verify storage.remove was called
        assert mock_storage.remove.called


def test_clear_completed_returns_count(sample_tasks):
    """clear_completed_tasks returns number of tasks removed."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        count = operations.clear_completed_tasks()
        assert isinstance(count, int)
        assert count == 2


# Test Edge Cases

def test_operations_with_storage_error():
    """Operations handle storage errors gracefully."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.add.side_effect = StorageError("Disk full")
        with pytest.raises(StorageError):
            operations.create_task(title="Test Task")


def test_concurrent_operations_safe(sample_tasks):
    """Multiple operations don't corrupt data (basic safety check)."""
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = sample_tasks
        # Perform multiple operations
        tasks1 = operations.list_tasks(status_filter="active")
        tasks2 = operations.list_tasks(priority_filter="high")
        # Both should work independently
        assert len(tasks1) == 3
        assert len(tasks2) == 2


def test_list_tasks_large_dataset():
    """Performance test with 1000+ tasks completes successfully."""
    large_dataset = [
        Task(
            id=f"task-{i:04d}",
            title=f"Task {i}",
            priority=Priority.MEDIUM,
            status=Status.ACTIVE,
            created_at=datetime.now() - timedelta(hours=i)
        )
        for i in range(1000)
    ]
    with patch('src.task_manager.operations.storage') as mock_storage:
        mock_storage.get_all.return_value = large_dataset
        tasks = operations.list_tasks()
        assert len(tasks) == 1000
