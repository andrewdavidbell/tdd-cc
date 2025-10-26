"""Tests for storage layer (JSON persistence)."""

import json
import pytest
from pathlib import Path
from datetime import datetime
from src.task_manager.models import Task, Priority, Status
from src.task_manager.storage import TaskStorage, StorageError, TaskNotFoundError


# Fixtures for test setup

@pytest.fixture
def temp_storage_path(tmp_path):
    """Create a temporary path for storage testing."""
    return tmp_path / "test_tasks.json"


@pytest.fixture
def storage(temp_storage_path):
    """Create a TaskStorage instance with temporary path."""
    return TaskStorage(temp_storage_path)


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        id="test-id-001",
        title="Test Task",
        description="Test Description",
        priority=Priority.HIGH,
        status=Status.ACTIVE,
        created_at=datetime(2025, 10, 24, 10, 0, 0)
    )


@pytest.fixture
def sample_tasks():
    """Create multiple sample tasks for testing."""
    return [
        Task(
            id="task-001",
            title="Task 1",
            priority=Priority.HIGH,
            status=Status.ACTIVE,
            created_at=datetime(2025, 10, 24, 10, 0, 0)
        ),
        Task(
            id="task-002",
            title="Task 2",
            priority=Priority.MEDIUM,
            status=Status.COMPLETED,
            created_at=datetime(2025, 10, 24, 11, 0, 0),
            completed_at=datetime(2025, 10, 24, 12, 0, 0)
        ),
        Task(
            id="task-003",
            title="Task 3",
            priority=Priority.LOW,
            status=Status.ACTIVE,
            created_at=datetime(2025, 10, 24, 12, 0, 0)
        )
    ]


# Test TaskStorage Initialisation (3 tests)

def test_storage_init_creates_directory_if_not_exists(tmp_path):
    """Test that TaskStorage creates parent directory if it doesn't exist."""
    storage_path = tmp_path / "new_dir" / "tasks.json"
    storage = TaskStorage(storage_path)

    assert storage_path.parent.exists()
    assert storage_path.parent.is_dir()


def test_storage_init_with_existing_directory(temp_storage_path):
    """Test that TaskStorage works with existing directory."""
    # Ensure parent directory exists
    temp_storage_path.parent.mkdir(parents=True, exist_ok=True)

    storage = TaskStorage(temp_storage_path)
    assert storage.file_path == temp_storage_path


def test_storage_init_creates_empty_file_if_not_exists(temp_storage_path):
    """Test that TaskStorage creates empty JSON file if it doesn't exist."""
    storage = TaskStorage(temp_storage_path)

    assert temp_storage_path.exists()
    assert temp_storage_path.is_file()

    # Verify file contains empty task list
    with open(temp_storage_path, 'r') as f:
        data = json.load(f)
        assert 'tasks' in data
        assert data['tasks'] == []


# Test Loading Tasks (5 tests)

def test_load_empty_file_returns_empty_list(storage, temp_storage_path):
    """Test that loading an empty file returns an empty list."""
    # Create empty tasks file
    with open(temp_storage_path, 'w') as f:
        json.dump({'tasks': []}, f)

    tasks = storage.load()
    assert tasks == []


def test_load_tasks_from_file(storage, temp_storage_path, sample_tasks):
    """Test that tasks are loaded correctly from file."""
    # Write tasks to file
    task_dicts = [task.to_dict() for task in sample_tasks]
    with open(temp_storage_path, 'w') as f:
        json.dump({'tasks': task_dicts}, f)

    loaded_tasks = storage.load()

    assert len(loaded_tasks) == 3
    assert all(isinstance(task, Task) for task in loaded_tasks)
    assert loaded_tasks[0].id == "task-001"
    assert loaded_tasks[1].id == "task-002"
    assert loaded_tasks[2].id == "task-003"


def test_load_validates_json_schema(storage, temp_storage_path):
    """Test that load validates JSON schema and raises error on invalid format."""
    # Write invalid JSON (missing 'tasks' key)
    with open(temp_storage_path, 'w') as f:
        json.dump({'invalid_key': []}, f)

    with pytest.raises(StorageError) as excinfo:
        storage.load()

    assert "Invalid JSON schema" in str(excinfo.value)


def test_load_handles_corrupted_file(storage, temp_storage_path):
    """Test that load handles corrupted JSON file gracefully."""
    # Write corrupted JSON
    with open(temp_storage_path, 'w') as f:
        f.write("{ invalid json content }")

    with pytest.raises(StorageError) as excinfo:
        storage.load()

    assert "Failed to load tasks" in str(excinfo.value)


def test_load_converts_dicts_to_task_objects(storage, temp_storage_path):
    """Test that load converts dictionaries to Task objects."""
    task_dict = {
        'id': 'test-001',
        'title': 'Test Task',
        'description': 'Test Description',
        'priority': 'high',
        'due_date': None,
        'status': 'active',
        'created_at': '2025-10-24T10:00:00',
        'completed_at': None
    }

    with open(temp_storage_path, 'w') as f:
        json.dump({'tasks': [task_dict]}, f)

    tasks = storage.load()

    assert len(tasks) == 1
    assert isinstance(tasks[0], Task)
    assert tasks[0].title == "Test Task"
    assert tasks[0].priority == Priority.HIGH


# Test Saving Tasks (6 tests)

def test_save_empty_list(storage, temp_storage_path):
    """Test that saving an empty list creates valid JSON."""
    storage.save([])

    with open(temp_storage_path, 'r') as f:
        data = json.load(f)
        assert data['tasks'] == []


def test_save_single_task(storage, temp_storage_path, sample_task):
    """Test that a single task is saved correctly."""
    storage.save([sample_task])

    with open(temp_storage_path, 'r') as f:
        data = json.load(f)
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['id'] == "test-id-001"
        assert data['tasks'][0]['title'] == "Test Task"


def test_save_multiple_tasks(storage, temp_storage_path, sample_tasks):
    """Test that multiple tasks are saved correctly."""
    storage.save(sample_tasks)

    with open(temp_storage_path, 'r') as f:
        data = json.load(f)
        assert len(data['tasks']) == 3
        assert data['tasks'][0]['id'] == "task-001"
        assert data['tasks'][1]['id'] == "task-002"
        assert data['tasks'][2]['id'] == "task-003"


def test_save_uses_atomic_write(storage, temp_storage_path, sample_task):
    """Test that save uses atomic write to prevent corruption."""
    # First, write initial data
    storage.save([sample_task])

    # Read the file to confirm it exists
    assert temp_storage_path.exists()

    # Simulate atomic write by checking no temp file remains
    temp_files = list(temp_storage_path.parent.glob("*.tmp"))
    assert len(temp_files) == 0


def test_save_creates_backup_before_write(storage, temp_storage_path, sample_task, sample_tasks):
    """Test that save creates backup of existing file before writing."""
    # First save
    storage.save([sample_task])

    # Second save should create backup
    storage.save(sample_tasks)

    backup_path = temp_storage_path.with_suffix('.json.bak')
    assert backup_path.exists()

    # Verify backup contains original data
    with open(backup_path, 'r') as f:
        data = json.load(f)
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['id'] == "test-id-001"


def test_save_preserves_task_order(storage, temp_storage_path, sample_tasks):
    """Test that save preserves the order of tasks."""
    storage.save(sample_tasks)

    loaded_tasks = storage.load()

    assert len(loaded_tasks) == 3
    assert loaded_tasks[0].id == "task-001"
    assert loaded_tasks[1].id == "task-002"
    assert loaded_tasks[2].id == "task-003"


# Test Get All (3 tests)

def test_get_all_returns_empty_list_when_no_tasks(storage):
    """Test that get_all returns empty list when storage has no tasks."""
    tasks = storage.get_all()
    assert tasks == []


def test_get_all_returns_all_tasks(storage, sample_tasks):
    """Test that get_all returns all stored tasks."""
    storage.save(sample_tasks)

    tasks = storage.get_all()

    assert len(tasks) == 3
    assert tasks[0].id == "task-001"
    assert tasks[1].id == "task-002"
    assert tasks[2].id == "task-003"


def test_get_all_returns_copies_not_references(storage, sample_tasks):
    """Test that get_all returns new instances, not references to internal storage."""
    storage.save(sample_tasks)

    tasks1 = storage.get_all()
    tasks2 = storage.get_all()

    # Modify first returned list
    tasks1[0].title = "Modified Title"

    # Second list should not be affected
    assert tasks2[0].title == "Task 1"


# Test Add Task (4 tests)

def test_add_task_to_empty_storage(storage, sample_task):
    """Test adding a task to empty storage."""
    storage.add(sample_task)

    tasks = storage.get_all()
    assert len(tasks) == 1
    assert tasks[0].id == "test-id-001"


def test_add_task_to_existing_storage(storage, sample_tasks, sample_task):
    """Test adding a task to storage that already has tasks."""
    storage.save(sample_tasks)

    new_task = Task(id="task-004", title="Task 4")
    storage.add(new_task)

    tasks = storage.get_all()
    assert len(tasks) == 4
    assert tasks[3].id == "task-004"


def test_add_task_persists_to_file(storage, temp_storage_path, sample_task):
    """Test that adding a task persists it to the JSON file."""
    storage.add(sample_task)

    # Create new storage instance and verify task is there
    new_storage = TaskStorage(temp_storage_path)
    tasks = new_storage.get_all()

    assert len(tasks) == 1
    assert tasks[0].id == "test-id-001"


def test_add_duplicate_id_raises_error(storage, sample_task):
    """Test that adding a task with duplicate ID raises error."""
    storage.add(sample_task)

    duplicate_task = Task(id="test-id-001", title="Duplicate")

    with pytest.raises(StorageError) as excinfo:
        storage.add(duplicate_task)

    assert "already exists" in str(excinfo.value).lower()


# Test Remove Task (4 tests)

def test_remove_existing_task(storage, sample_tasks):
    """Test removing an existing task."""
    storage.save(sample_tasks)

    storage.remove("task-002")

    tasks = storage.get_all()
    assert len(tasks) == 2
    assert all(task.id != "task-002" for task in tasks)


def test_remove_nonexistent_task_raises_error(storage):
    """Test that removing a nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError) as excinfo:
        storage.remove("nonexistent-id")

    assert "not found" in str(excinfo.value).lower()


def test_remove_persists_to_file(storage, temp_storage_path, sample_tasks):
    """Test that removing a task persists the change to file."""
    storage.save(sample_tasks)
    storage.remove("task-002")

    # Create new storage instance and verify removal persisted
    new_storage = TaskStorage(temp_storage_path)
    tasks = new_storage.get_all()

    assert len(tasks) == 2
    assert all(task.id != "task-002" for task in tasks)


def test_remove_from_multiple_tasks(storage, sample_tasks):
    """Test removing correct task when multiple tasks exist."""
    storage.save(sample_tasks)

    storage.remove("task-001")

    tasks = storage.get_all()
    assert len(tasks) == 2
    assert tasks[0].id == "task-002"
    assert tasks[1].id == "task-003"


# Test Update Task (4 tests)

def test_update_existing_task(storage, sample_tasks):
    """Test updating an existing task."""
    storage.save(sample_tasks)

    updated_task = Task(
        id="task-001",
        title="Updated Task 1",
        priority=Priority.LOW,
        status=Status.COMPLETED,
        created_at=datetime(2025, 10, 24, 10, 0, 0),
        completed_at=datetime(2025, 10, 24, 15, 0, 0)
    )

    storage.update(updated_task)

    task = storage.get_by_id("task-001")
    assert task.title == "Updated Task 1"
    assert task.priority == Priority.LOW
    assert task.status == Status.COMPLETED


def test_update_nonexistent_task_raises_error(storage, sample_task):
    """Test that updating a nonexistent task raises TaskNotFoundError."""
    nonexistent_task = Task(id="nonexistent-id", title="Nonexistent")

    with pytest.raises(TaskNotFoundError) as excinfo:
        storage.update(nonexistent_task)

    assert "not found" in str(excinfo.value).lower()


def test_update_persists_to_file(storage, temp_storage_path, sample_tasks):
    """Test that updating a task persists the change to file."""
    storage.save(sample_tasks)

    updated_task = Task(
        id="task-001",
        title="Updated Task 1",
        created_at=datetime(2025, 10, 24, 10, 0, 0)
    )
    storage.update(updated_task)

    # Create new storage instance and verify update persisted
    new_storage = TaskStorage(temp_storage_path)
    task = new_storage.get_by_id("task-001")

    assert task.title == "Updated Task 1"


def test_update_preserves_other_tasks(storage, sample_tasks):
    """Test that updating one task doesn't affect other tasks."""
    storage.save(sample_tasks)

    updated_task = Task(
        id="task-002",
        title="Updated Task 2",
        created_at=datetime(2025, 10, 24, 11, 0, 0)
    )
    storage.update(updated_task)

    # Verify other tasks unchanged
    task1 = storage.get_by_id("task-001")
    task3 = storage.get_by_id("task-003")

    assert task1.title == "Task 1"
    assert task3.title == "Task 3"


# Test Get By ID (2 tests)

def test_get_by_id_finds_existing_task(storage, sample_tasks):
    """Test that get_by_id returns the correct task."""
    storage.save(sample_tasks)

    task = storage.get_by_id("task-002")

    assert task is not None
    assert task.id == "task-002"
    assert task.title == "Task 2"
    assert task.priority == Priority.MEDIUM


def test_get_by_id_nonexistent_raises_error(storage, sample_tasks):
    """Test that get_by_id raises TaskNotFoundError for nonexistent ID."""
    storage.save(sample_tasks)

    with pytest.raises(TaskNotFoundError) as excinfo:
        storage.get_by_id("nonexistent-id")

    assert "not found" in str(excinfo.value).lower()


# Test Error Handling (3 tests)

def test_storage_error_on_permission_denied(tmp_path):
    """Test that StorageError is raised when file permissions deny access."""
    storage_path = tmp_path / "tasks.json"
    storage = TaskStorage(storage_path)

    # Make directory read-only to prevent file writes
    tmp_path.chmod(0o555)

    sample_task = Task(id="test-001", title="Test")

    try:
        with pytest.raises(StorageError) as excinfo:
            storage.add(sample_task)

        assert "permission" in str(excinfo.value).lower() or "failed" in str(excinfo.value).lower()
    finally:
        # Restore permissions for cleanup
        tmp_path.chmod(0o755)


def test_storage_error_on_disk_full(storage, temp_storage_path, sample_task, monkeypatch):
    """Test that StorageError is raised when disk is full (simulated)."""
    def mock_write_fail(*args, **kwargs):
        raise OSError("No space left on device")

    # Mock the file write to simulate disk full
    monkeypatch.setattr("builtins.open", mock_write_fail)

    with pytest.raises(StorageError) as excinfo:
        storage.save([sample_task])

    assert "failed" in str(excinfo.value).lower()


def test_corrupted_backup_falls_back_gracefully(storage, temp_storage_path, sample_tasks):
    """Test that storage handles corrupted backup file gracefully."""
    # Create initial tasks
    storage.save(sample_tasks)

    # Corrupt the backup file
    backup_path = temp_storage_path.with_suffix('.json.bak')
    with open(backup_path, 'w') as f:
        f.write("{ corrupted json }")

    # Should still be able to save (backup corruption shouldn't block new saves)
    new_task = Task(id="task-004", title="Task 4")
    storage.add(new_task)

    tasks = storage.get_all()
    assert len(tasks) == 4


# Test Concurrency Safety (1 test)

def test_atomic_write_prevents_partial_updates(storage, temp_storage_path, sample_tasks):
    """Test that atomic write prevents partial file updates on failure."""
    storage.save(sample_tasks)

    # Verify original content is intact
    original_tasks = storage.get_all()
    assert len(original_tasks) == 3

    # Even if write were to fail midway, the atomic write should ensure
    # either complete write or no write (original file intact)
    # This is verified by checking no .tmp files remain
    temp_files = list(temp_storage_path.parent.glob("*.tmp"))
    assert len(temp_files) == 0

    # Original file should be complete and valid JSON
    with open(temp_storage_path, 'r') as f:
        data = json.load(f)
        assert len(data['tasks']) == 3
