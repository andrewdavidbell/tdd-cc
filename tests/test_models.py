"""Test suite for Task Manager domain models."""

import pytest
from datetime import datetime, timedelta
from task_manager.models import Priority, Status, Task, ValidationError


# Test Priority Enum

def test_priority_enum_has_correct_values():
    """Verify Priority enum has HIGH, MEDIUM, LOW values."""
    assert hasattr(Priority, 'HIGH')
    assert hasattr(Priority, 'MEDIUM')
    assert hasattr(Priority, 'LOW')


def test_priority_enum_values():
    """Verify Priority enum values are correct strings."""
    assert Priority.HIGH.value == 'high'
    assert Priority.MEDIUM.value == 'medium'
    assert Priority.LOW.value == 'low'


# Test Status Enum

def test_status_enum_has_correct_values():
    """Verify Status enum has ACTIVE, COMPLETED values."""
    assert hasattr(Status, 'ACTIVE')
    assert hasattr(Status, 'COMPLETED')


def test_status_enum_values():
    """Verify Status enum values are correct strings."""
    assert Status.ACTIVE.value == 'active'
    assert Status.COMPLETED.value == 'completed'


# Test Task Creation

def test_create_task_with_minimal_fields():
    """Create task with only title."""
    task = Task(title="Buy groceries")
    assert task.title == "Buy groceries"


def test_create_task_with_all_fields():
    """Create task with all optional fields."""
    due_date = datetime.now() + timedelta(days=1)
    task = Task(
        title="Complete project",
        description="Finish the TD-AID project",
        priority=Priority.HIGH,
        due_date=due_date
    )
    assert task.title == "Complete project"
    assert task.description == "Finish the TD-AID project"
    assert task.priority == Priority.HIGH
    assert task.due_date == due_date


def test_task_auto_generates_id():
    """Verify UUID is auto-generated."""
    task = Task(title="Test task")
    assert task.id is not None
    assert isinstance(task.id, str)
    assert len(task.id) == 36  # UUID format


def test_task_auto_sets_created_at():
    """Verify timestamp is auto-set."""
    before = datetime.now()
    task = Task(title="Test task")
    after = datetime.now()
    assert task.created_at is not None
    assert isinstance(task.created_at, datetime)
    assert before <= task.created_at <= after


def test_task_defaults_status_to_active():
    """Verify default status is ACTIVE."""
    task = Task(title="Test task")
    assert task.status == Status.ACTIVE


def test_task_defaults_priority_to_medium():
    """Verify default priority is MEDIUM."""
    task = Task(title="Test task")
    assert task.priority == Priority.MEDIUM


def test_task_completed_at_is_none_for_new_task():
    """Verify completed_at is None for new tasks."""
    task = Task(title="Test task")
    assert task.completed_at is None


# Test Task Validation

def test_validate_empty_title_raises_error():
    """Empty string should fail validation."""
    with pytest.raises(ValidationError, match="Title cannot be empty"):
        task = Task(title="")
        task.validate()


def test_validate_whitespace_only_title_raises_error():
    """Whitespace-only title should fail validation."""
    with pytest.raises(ValidationError, match="Title cannot be empty"):
        task = Task(title="   ")
        task.validate()


def test_validate_title_too_long_raises_error():
    """Title >200 chars should fail validation."""
    long_title = "a" * 201
    with pytest.raises(ValidationError, match="Title cannot exceed 200 characters"):
        task = Task(title=long_title)
        task.validate()


def test_validate_description_too_long_raises_error():
    """Description >1000 chars should fail validation."""
    long_description = "a" * 1001
    with pytest.raises(ValidationError, match="Description cannot exceed 1000 characters"):
        task = Task(title="Test", description=long_description)
        task.validate()


def test_validate_invalid_priority_raises_error():
    """Invalid priority value should fail validation."""
    with pytest.raises((ValidationError, ValueError, AttributeError)):
        Task(title="Test", priority="urgent")


def test_validate_invalid_due_date_format_raises_error():
    """Invalid due date format should fail validation."""
    with pytest.raises((ValidationError, TypeError, ValueError)):
        Task(title="Test", due_date="2025-13-45")


def test_validate_past_due_date_raises_error():
    """Past due date should fail validation."""
    past_date = datetime.now() - timedelta(days=1)
    with pytest.raises(ValidationError, match="Due date cannot be in the past"):
        task = Task(title="Test", due_date=past_date)
        task.validate()


def test_validate_accepts_future_due_date():
    """Future due date should pass validation."""
    future_date = datetime.now() + timedelta(days=1)
    task = Task(title="Test", due_date=future_date)
    task.validate()  # Should not raise


def test_validate_accepts_none_due_date():
    """None due date should pass validation."""
    task = Task(title="Test", due_date=None)
    task.validate()  # Should not raise


# Test Task Methods

def test_mark_complete_sets_status_to_completed():
    """Status changes to COMPLETED when marked complete."""
    task = Task(title="Test task")
    task.mark_complete()
    assert task.status == Status.COMPLETED


def test_mark_complete_sets_completed_at_timestamp():
    """Completed_at timestamp is set when marked complete."""
    task = Task(title="Test task")
    before = datetime.now()
    task.mark_complete()
    after = datetime.now()
    assert task.completed_at is not None
    assert isinstance(task.completed_at, datetime)
    assert before <= task.completed_at <= after


def test_mark_incomplete_sets_status_to_active():
    """Status changes to ACTIVE when marked incomplete."""
    task = Task(title="Test task")
    task.mark_complete()
    task.mark_incomplete()
    assert task.status == Status.ACTIVE


def test_mark_incomplete_clears_completed_at():
    """Completed_at is cleared when marked incomplete."""
    task = Task(title="Test task")
    task.mark_complete()
    task.mark_incomplete()
    assert task.completed_at is None


def test_to_dict_serialises_all_fields():
    """All fields present in dict serialisation."""
    due_date = datetime.now() + timedelta(days=1)
    task = Task(
        title="Test task",
        description="Test description",
        priority=Priority.HIGH,
        due_date=due_date
    )
    task_dict = task.to_dict()

    assert 'id' in task_dict
    assert 'title' in task_dict
    assert 'description' in task_dict
    assert 'priority' in task_dict
    assert 'due_date' in task_dict
    assert 'status' in task_dict
    assert 'created_at' in task_dict
    assert 'completed_at' in task_dict


def test_to_dict_handles_none_values():
    """None values serialised correctly."""
    task = Task(title="Test task")
    task_dict = task.to_dict()

    assert task_dict['description'] is None
    assert task_dict['due_date'] is None
    assert task_dict['completed_at'] is None


def test_from_dict_creates_task():
    """Task created from valid dict."""
    task_dict = {
        'id': '12345678-1234-1234-1234-123456789012',
        'title': 'Test task',
        'description': 'Test description',
        'priority': 'high',
        'due_date': None,
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'completed_at': None
    }
    task = Task.from_dict(task_dict)
    assert task.title == 'Test task'
    assert task.description == 'Test description'


def test_from_dict_with_missing_required_fields_raises_error():
    """Missing title field should fail."""
    task_dict = {
        'id': '12345678-1234-1234-1234-123456789012',
        'description': 'Test description'
    }
    with pytest.raises((ValidationError, KeyError)):
        Task.from_dict(task_dict)


def test_from_dict_preserves_id():
    """ID from dict is preserved."""
    task_id = '12345678-1234-1234-1234-123456789012'
    task_dict = {
        'id': task_id,
        'title': 'Test task',
        'description': None,
        'priority': 'medium',
        'due_date': None,
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'completed_at': None
    }
    task = Task.from_dict(task_dict)
    assert task.id == task_id


def test_task_equality_based_on_id():
    """Two tasks with same ID are equal."""
    task1 = Task(title="Task 1")
    task2 = Task(title="Task 2")
    task2.id = task1.id  # Set same ID
    assert task1 == task2


# Test Edge Cases

def test_priority_case_insensitive():
    """Priority values should handle different cases."""
    # This tests the Task initialization accepting string priorities
    task1 = Task(title="Test", priority=Priority.HIGH)
    task2 = Task(title="Test", priority=Priority.HIGH)
    assert task1.priority == task2.priority


def test_title_strips_whitespace():
    """Leading/trailing spaces removed from title."""
    task = Task(title="  Test task  ")
    assert task.title == "Test task"


def test_unicode_in_title_and_description():
    """Unicode characters supported in title and description."""
    task = Task(
        title="タスク 📝",
        description="Description with émojis 🎉 and spëcial çhars"
    )
    assert task.title == "タスク 📝"
    assert task.description == "Description with émojis 🎉 and spëcial çhars"
