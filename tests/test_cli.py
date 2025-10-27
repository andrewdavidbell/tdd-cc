"""
Test suite for CLI layer.

This module tests the command-line interface including argument parsing,
command handlers, output formatting, and error handling.

Following TD-AID methodology: All tests written BEFORE implementation.
"""

import sys
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
import pytest
from datetime import datetime

# Imports that will be tested (will fail until implementation exists)
from task_manager.cli import (
    create_parser,
    cmd_add,
    cmd_list,
    cmd_complete,
    cmd_incomplete,
    cmd_delete,
    cmd_clear,
    format_task,
    format_task_list,
    main,
)
from task_manager.models import Task, Priority, Status, ValidationError
from task_manager.storage import TaskNotFoundError, StorageError


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    task = Task(
        title="Sample Task",
        description="This is a test task",
        priority=Priority.HIGH,
        due_date=datetime(2025, 12, 31)
    )
    task.validate()
    return task


@pytest.fixture
def completed_task():
    """Create a completed task for testing."""
    task = Task(
        title="Completed Task",
        description="This task is done",
        priority=Priority.MEDIUM,
        due_date=datetime(2025, 11, 15)
    )
    task.validate()
    task.mark_complete()
    return task


@pytest.fixture
def task_list(sample_task, completed_task):
    """Create a list of tasks for testing."""
    task3 = Task(title="Another Task", priority=Priority.LOW)
    task3.validate()
    return [sample_task, completed_task, task3]


# ============================================================================
# Test Argument Parsing (Tests 1-12)
# ============================================================================

def test_parser_has_all_subcommands():
    """Test 1: Parser includes add, list, complete, incomplete, delete, clear subcommands."""
    parser = create_parser()
    # Get subparser actions using _SubParsersAction type
    import argparse
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    assert len(subparsers_actions) > 0

    # Get all subcommand names
    subparser_dict = subparsers_actions[0].choices
    assert 'add' in subparser_dict
    assert 'list' in subparser_dict
    assert 'complete' in subparser_dict
    assert 'incomplete' in subparser_dict
    assert 'delete' in subparser_dict
    assert 'clear' in subparser_dict


def test_add_command_required_title():
    """Test 2: Add command requires --title argument."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        # Should fail without --title
        parser.parse_args(['add'])


def test_add_command_optional_description():
    """Test 3: Add command accepts optional --description argument."""
    parser = create_parser()
    args = parser.parse_args(['add', '--title', 'Test Task', '--description', 'Test Description'])
    assert args.description == 'Test Description'


def test_add_command_optional_priority():
    """Test 4: Add command accepts optional --priority with default value."""
    parser = create_parser()
    # With priority
    args = parser.parse_args(['add', '--title', 'Test', '--priority', 'high'])
    assert args.priority == 'high'

    # Without priority (should have default)
    args_default = parser.parse_args(['add', '--title', 'Test'])
    assert args_default.priority == 'medium'


def test_add_command_optional_due_date():
    """Test 5: Add command accepts optional --due-date argument."""
    parser = create_parser()
    args = parser.parse_args(['add', '--title', 'Test', '--due-date', '2025-12-31'])
    assert args.due_date == '2025-12-31'


def test_list_command_optional_status():
    """Test 6: List command accepts optional --status filter."""
    parser = create_parser()
    args = parser.parse_args(['list', '--status', 'active'])
    assert args.status == 'active'


def test_list_command_optional_priority():
    """Test 7: List command accepts optional --priority filter."""
    parser = create_parser()
    args = parser.parse_args(['list', '--priority', 'high'])
    assert args.priority == 'high'


def test_list_command_optional_sort():
    """Test 8: List command accepts optional --sort-by argument."""
    parser = create_parser()
    args = parser.parse_args(['list', '--sort-by', 'due_date'])
    assert args.sort_by == 'due_date'


def test_complete_command_required_id():
    """Test 9: Complete command requires task_id argument."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        # Should fail without task_id
        parser.parse_args(['complete'])


def test_incomplete_command_required_id():
    """Test 10: Incomplete command requires task_id argument."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        # Should fail without task_id
        parser.parse_args(['incomplete'])


def test_delete_command_required_id():
    """Test 11: Delete command requires task_id argument."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        # Should fail without task_id
        parser.parse_args(['delete'])


def test_clear_command_no_args():
    """Test 12: Clear command requires no arguments."""
    parser = create_parser()
    args = parser.parse_args(['clear'])
    assert args.command == 'clear'


# ============================================================================
# Test Command Handlers (Tests 13-32)
# ============================================================================

@patch('task_manager.cli.operations.create_task')
def test_cmd_add_creates_task(mock_create_task, sample_task):
    """Test 13: cmd_add calls operations.create_task()."""
    mock_create_task.return_value = sample_task

    args = Mock(
        title='Test Task',
        description='Test Description',
        priority='high',
        due_date='2025-12-31'
    )

    cmd_add(args)
    mock_create_task.assert_called_once_with(
        title='Test Task',
        description='Test Description',
        priority='high',
        due_date='2025-12-31'
    )


@patch('task_manager.cli.operations.create_task')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_add_displays_success_message(mock_stdout, mock_create_task, sample_task):
    """Test 14: cmd_add displays success message."""
    mock_create_task.return_value = sample_task

    args = Mock(title='Test', description=None, priority='medium', due_date=None)
    cmd_add(args)

    output = mock_stdout.getvalue()
    assert 'success' in output.lower() or 'created' in output.lower() or 'added' in output.lower()


@patch('task_manager.cli.operations.create_task')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_add_displays_task_details(mock_stdout, mock_create_task, sample_task):
    """Test 15: cmd_add displays task details."""
    mock_create_task.return_value = sample_task

    args = Mock(title='Test', description=None, priority='medium', due_date=None)
    cmd_add(args)

    output = mock_stdout.getvalue()
    assert sample_task.title in output


@patch('task_manager.cli.operations.create_task')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_add_handles_validation_error(mock_stdout, mock_create_task):
    """Test 16: cmd_add handles ValidationError gracefully."""
    mock_create_task.side_effect = ValidationError("Invalid task data")

    args = Mock(title='', description=None, priority='medium', due_date=None)

    # Should not raise exception
    cmd_add(args)

    output = mock_stdout.getvalue()
    assert 'error' in output.lower() or 'invalid' in output.lower()


@patch('task_manager.cli.operations.list_tasks')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_list_displays_all_tasks(mock_stdout, mock_list_tasks, task_list):
    """Test 17: cmd_list displays all tasks."""
    mock_list_tasks.return_value = task_list

    args = Mock(status=None, priority=None, sort_by='created_at')
    cmd_list(args)

    output = mock_stdout.getvalue()
    for task in task_list:
        assert task.title in output


@patch('task_manager.cli.operations.list_tasks')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_list_displays_empty_message(mock_stdout, mock_list_tasks):
    """Test 18: cmd_list displays message when no tasks exist."""
    mock_list_tasks.return_value = []

    args = Mock(status=None, priority=None, sort_by='created_at')
    cmd_list(args)

    output = mock_stdout.getvalue()
    assert 'no tasks' in output.lower() or 'empty' in output.lower()


@patch('task_manager.cli.operations.list_tasks')
def test_cmd_list_filters_by_status(mock_list_tasks):
    """Test 19: cmd_list applies status filter."""
    mock_list_tasks.return_value = []

    args = Mock(status='active', priority=None, sort_by='created_at')
    cmd_list(args)

    mock_list_tasks.assert_called_once_with(
        status_filter='active',
        priority_filter=None,
        sort_by='created_at'
    )


@patch('task_manager.cli.operations.list_tasks')
def test_cmd_list_filters_by_priority(mock_list_tasks):
    """Test 20: cmd_list applies priority filter."""
    mock_list_tasks.return_value = []

    args = Mock(status=None, priority='high', sort_by='created_at')
    cmd_list(args)

    mock_list_tasks.assert_called_once_with(
        status_filter=None,
        priority_filter='high',
        sort_by='created_at'
    )


@patch('task_manager.cli.operations.list_tasks')
def test_cmd_list_sorts_correctly(mock_list_tasks):
    """Test 21: cmd_list applies sort order."""
    mock_list_tasks.return_value = []

    args = Mock(status=None, priority=None, sort_by='priority')
    cmd_list(args)

    mock_list_tasks.assert_called_once_with(
        status_filter=None,
        priority_filter=None,
        sort_by='priority'
    )


@patch('task_manager.cli.operations.update_task_status')
def test_cmd_complete_marks_task_complete(mock_update_status):
    """Test 22: cmd_complete calls update_task_status() with completed status."""
    args = Mock(task_id='test-uuid-123')
    cmd_complete(args)

    mock_update_status.assert_called_once_with('test-uuid-123', "completed")


@patch('task_manager.cli.operations.update_task_status')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_complete_displays_success_message(mock_stdout, mock_update_status):
    """Test 23: cmd_complete displays success message."""
    args = Mock(task_id='test-uuid-123')
    cmd_complete(args)

    output = mock_stdout.getvalue()
    assert 'complete' in output.lower() or 'success' in output.lower()


@patch('task_manager.cli.operations.update_task_status')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_complete_handles_not_found_error(mock_stdout, mock_update_status):
    """Test 24: cmd_complete handles TaskNotFoundError."""
    mock_update_status.side_effect = TaskNotFoundError("Task not found")

    args = Mock(task_id='nonexistent-id')
    cmd_complete(args)

    output = mock_stdout.getvalue()
    assert 'not found' in output.lower() or 'error' in output.lower()


@patch('task_manager.cli.operations.update_task_status')
def test_cmd_incomplete_marks_task_active(mock_update_status):
    """Test 25: cmd_incomplete calls update_task_status() with active status."""
    args = Mock(task_id='test-uuid-123')
    cmd_incomplete(args)

    mock_update_status.assert_called_once_with('test-uuid-123', "active")


@patch('task_manager.cli.operations.update_task_status')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_incomplete_displays_success_message(mock_stdout, mock_update_status):
    """Test 26: cmd_incomplete displays success message."""
    args = Mock(task_id='test-uuid-123')
    cmd_incomplete(args)

    output = mock_stdout.getvalue()
    assert 'active' in output.lower() or 'incomplete' in output.lower() or 'success' in output.lower()


@patch('task_manager.cli.operations.delete_task')
def test_cmd_delete_removes_task(mock_delete_task):
    """Test 27: cmd_delete calls delete_task()."""
    args = Mock(task_id='test-uuid-123')
    cmd_delete(args)

    mock_delete_task.assert_called_once_with('test-uuid-123')


@patch('task_manager.cli.operations.delete_task')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_delete_displays_success_message(mock_stdout, mock_delete_task):
    """Test 28: cmd_delete displays success message."""
    args = Mock(task_id='test-uuid-123')
    cmd_delete(args)

    output = mock_stdout.getvalue()
    assert 'delete' in output.lower() or 'removed' in output.lower() or 'success' in output.lower()


@patch('task_manager.cli.operations.delete_task')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_delete_handles_not_found_error(mock_stdout, mock_delete_task):
    """Test 29: cmd_delete handles TaskNotFoundError."""
    mock_delete_task.side_effect = TaskNotFoundError("Task not found")

    args = Mock(task_id='nonexistent-id')
    cmd_delete(args)

    output = mock_stdout.getvalue()
    assert 'not found' in output.lower() or 'error' in output.lower()


@patch('task_manager.cli.operations.clear_completed_tasks')
def test_cmd_clear_removes_completed_tasks(mock_clear_completed):
    """Test 30: cmd_clear calls clear_completed_tasks()."""
    mock_clear_completed.return_value = 5

    args = Mock()
    cmd_clear(args)

    mock_clear_completed.assert_called_once()


@patch('task_manager.cli.operations.clear_completed_tasks')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_clear_displays_count_message(mock_stdout, mock_clear_completed):
    """Test 31: cmd_clear displays count of removed tasks."""
    mock_clear_completed.return_value = 5

    args = Mock()
    cmd_clear(args)

    output = mock_stdout.getvalue()
    assert '5' in output


@patch('task_manager.cli.operations.clear_completed_tasks')
@patch('sys.stdout', new_callable=StringIO)
def test_cmd_clear_displays_none_message(mock_stdout, mock_clear_completed):
    """Test 32: cmd_clear displays message when no completed tasks."""
    mock_clear_completed.return_value = 0

    args = Mock()
    cmd_clear(args)

    output = mock_stdout.getvalue()
    assert '0' in output or 'no' in output.lower()


# ============================================================================
# Test Output Formatting (Tests 33-38)
# ============================================================================

def test_format_task_includes_all_fields(sample_task):
    """Test 33: format_task includes ID, title, priority, status, etc."""
    output = format_task(sample_task)

    assert str(sample_task.id) in output
    assert sample_task.title in output
    assert sample_task.priority.value in output
    assert sample_task.status.value in output


def test_format_task_handles_none_values():
    """Test 34: format_task handles None values correctly."""
    task = Task(title="Minimal Task")
    task.validate()

    output = format_task(task)

    # Should not crash, and should handle None description and due_date
    assert task.title in output


def test_format_task_displays_due_date(sample_task):
    """Test 35: format_task displays due date correctly."""
    output = format_task(sample_task)

    # Check for formatted due date string
    due_date_str = sample_task.due_date.strftime('%Y-%m-%d')
    assert due_date_str in output


def test_format_task_list_as_table(task_list):
    """Test 36: format_task_list displays tasks in table format."""
    output = format_task_list(task_list)

    # Should contain all task titles
    for task in task_list:
        assert task.title in output

    # Should have some table structure (lines or separators)
    assert '\n' in output


def test_format_task_list_headers(task_list):
    """Test 37: format_task_list includes table headers."""
    output = format_task_list(task_list)

    # Check for common header names
    output_lower = output.lower()
    assert 'id' in output_lower or 'title' in output_lower


def test_format_task_list_alignment(task_list):
    """Test 38: format_task_list has proper column alignment."""
    output = format_task_list(task_list)

    # Should have multiple lines (one per task + headers)
    lines = output.strip().split('\n')
    assert len(lines) >= len(task_list)


# ============================================================================
# Test Help Text (Tests 39-41)
# ============================================================================

def test_main_help_lists_commands():
    """Test 39: --help shows all available commands."""
    parser = create_parser()
    help_text = parser.format_help()

    assert 'add' in help_text
    assert 'list' in help_text
    assert 'complete' in help_text
    assert 'delete' in help_text


def test_add_help_shows_options():
    """Test 40: add --help shows all available options."""
    import argparse
    parser = create_parser()

    # Get the add subparser
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    add_parser = subparsers_actions[0].choices['add']
    help_text = add_parser.format_help()

    assert '--title' in help_text
    assert '--description' in help_text
    assert '--priority' in help_text
    assert '--due-date' in help_text


def test_list_help_shows_filters():
    """Test 41: list --help shows filter options."""
    import argparse
    parser = create_parser()

    # Get the list subparser
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    list_parser = subparsers_actions[0].choices['list']
    help_text = list_parser.format_help()

    assert '--status' in help_text
    assert '--priority' in help_text
    assert '--sort-by' in help_text


# ============================================================================
# Test Error Handling (Tests 42-44)
# ============================================================================

@patch('task_manager.cli.operations.list_tasks')
@patch('sys.stdout', new_callable=StringIO)
def test_handles_storage_error_gracefully(mock_stdout, mock_list_tasks):
    """Test 42: Storage errors are displayed to user gracefully."""
    mock_list_tasks.side_effect = StorageError("Storage file corrupted")

    args = Mock(status=None, priority=None, sort_by='created_at')
    cmd_list(args)

    output = mock_stdout.getvalue()
    assert 'error' in output.lower() or 'storage' in output.lower()


@patch('sys.argv', ['task_cli', 'invalid_command'])
@patch('sys.stderr', new_callable=StringIO)
def test_invalid_command_shows_error(mock_stderr):
    """Test 43: Unknown command shows error message."""
    with pytest.raises(SystemExit):
        main()

    error_output = mock_stderr.getvalue()
    assert 'invalid' in error_output.lower() or 'error' in error_output.lower()


@patch('sys.argv', ['task_cli', 'add'])
@patch('sys.stderr', new_callable=StringIO)
def test_missing_required_arg_shows_error(mock_stderr):
    """Test 44: Missing required argument shows usage error."""
    with pytest.raises(SystemExit):
        main()

    error_output = mock_stderr.getvalue()
    assert 'required' in error_output.lower() or 'error' in error_output.lower()


# ============================================================================
# Test Entry Point (Tests 45-46)
# ============================================================================

def test_main_entry_point_exists():
    """Test 45: main() function exists and is callable."""
    assert callable(main)


@patch('sys.argv', ['task_cli', '--help'])
@patch('sys.stdout', new_callable=StringIO)
def test_main_entry_point_callable(mock_stdout):
    """Test 46: main() can be called from command line."""
    with pytest.raises(SystemExit) as exc_info:
        main()

    # --help should exit with code 0
    assert exc_info.value.code == 0

    output = mock_stdout.getvalue()
    assert len(output) > 0  # Should produce help text
