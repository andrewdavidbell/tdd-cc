"""
Command-line interface for the Task Manager application.

This module provides the CLI layer for interacting with the task manager,
including argument parsing, command handlers, and output formatting.
"""

import argparse
import sys
from typing import List

from task_manager import operations
from task_manager.models import Task, Status, ValidationError
from task_manager.storage import TaskNotFoundError, StorageError


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the CLI.

    Returns:
        ArgumentParser: Configured argument parser with all subcommands.
    """
    parser = argparse.ArgumentParser(
        prog='task_cli',
        description='Command-line task manager for organising daily tasks'
    )

    # Create subparsers for each command
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('--title', required=True, help='Task title (required)')
    add_parser.add_argument('--description', help='Task description (optional)')
    add_parser.add_argument(
        '--priority',
        default='medium',
        choices=['high', 'medium', 'low'],
        help='Task priority (default: medium)'
    )
    add_parser.add_argument('--due-date', help='Due date in YYYY-MM-DD format (optional)')

    # List command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument(
        '--status',
        choices=['active', 'completed'],
        help='Filter by status (optional)'
    )
    list_parser.add_argument(
        '--priority',
        choices=['high', 'medium', 'low'],
        help='Filter by priority (optional)'
    )
    list_parser.add_argument(
        '--sort-by',
        default='created_at',
        choices=['created_at', 'due_date', 'priority'],
        help='Sort tasks by field (default: created_at)'
    )

    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Mark a task as complete')
    complete_parser.add_argument('task_id', help='Task ID')

    # Incomplete command
    incomplete_parser = subparsers.add_parser('incomplete', help='Mark a task as active')
    incomplete_parser.add_argument('task_id', help='Task ID')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a task')
    delete_parser.add_argument('task_id', help='Task ID')

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all completed tasks')

    return parser


def cmd_add(args: argparse.Namespace) -> None:
    """
    Handle the 'add' command to create a new task.

    Args:
        args: Parsed command-line arguments containing title, description, priority, due_date.
    """
    try:
        task = operations.create_task(
            title=args.title,
            description=args.description,
            priority=args.priority,
            due_date=args.due_date
        )
        print(f"✓ Task created successfully!")
        print(format_task(task))
    except ValidationError as e:
        print(f"Error: {e}")
    except StorageError as e:
        print(f"Storage error: {e}")


def cmd_list(args: argparse.Namespace) -> None:
    """
    Handle the 'list' command to display tasks.

    Args:
        args: Parsed command-line arguments containing status, priority, sort_by filters.
    """
    try:
        tasks = operations.list_tasks(
            status_filter=args.status,
            priority_filter=args.priority,
            sort_by=args.sort_by
        )

        if not tasks:
            print("No tasks found.")
        else:
            print(format_task_list(tasks))
    except StorageError as e:
        print(f"Storage error: {e}")


def cmd_complete(args: argparse.Namespace) -> None:
    """
    Handle the 'complete' command to mark a task as completed.

    Args:
        args: Parsed command-line arguments containing task_id.
    """
    try:
        operations.update_task_status(args.task_id, "completed")
        print(f"✓ Task marked as complete: {args.task_id}")
    except TaskNotFoundError as e:
        print(f"Error: Task not found: {args.task_id}")
    except StorageError as e:
        print(f"Storage error: {e}")


def cmd_incomplete(args: argparse.Namespace) -> None:
    """
    Handle the 'incomplete' command to mark a task as active.

    Args:
        args: Parsed command-line arguments containing task_id.
    """
    try:
        operations.update_task_status(args.task_id, "active")
        print(f"✓ Task marked as active: {args.task_id}")
    except TaskNotFoundError as e:
        print(f"Error: Task not found: {args.task_id}")
    except StorageError as e:
        print(f"Storage error: {e}")


def cmd_delete(args: argparse.Namespace) -> None:
    """
    Handle the 'delete' command to remove a task.

    Args:
        args: Parsed command-line arguments containing task_id.
    """
    try:
        operations.delete_task(args.task_id)
        print(f"✓ Task deleted successfully: {args.task_id}")
    except TaskNotFoundError as e:
        print(f"Error: Task not found: {args.task_id}")
    except StorageError as e:
        print(f"Storage error: {e}")


def cmd_clear(args: argparse.Namespace) -> None:
    """
    Handle the 'clear' command to remove all completed tasks.

    Args:
        args: Parsed command-line arguments (none required).
    """
    try:
        count = operations.clear_completed_tasks()
        if count == 0:
            print("No completed tasks to clear.")
        else:
            print(f"✓ Cleared {count} completed task(s).")
    except StorageError as e:
        print(f"Storage error: {e}")


def format_task(task: Task) -> str:
    """
    Format a single task for display.

    Args:
        task: The task to format.

    Returns:
        str: Formatted task string.
    """
    lines = []
    lines.append(f"  ID: {task.id}")
    lines.append(f"  Title: {task.title}")

    if task.description:
        lines.append(f"  Description: {task.description}")

    lines.append(f"  Priority: {task.priority.value}")
    lines.append(f"  Status: {task.status.value}")

    if task.due_date:
        # Format datetime as YYYY-MM-DD
        due_date_str = task.due_date.strftime('%Y-%m-%d')
        lines.append(f"  Due Date: {due_date_str}")

    # Format created_at
    created_str = task.created_at.strftime('%Y-%m-%d %H:%M:%S')
    lines.append(f"  Created: {created_str}")

    if task.completed_at:
        # Format completed_at
        completed_str = task.completed_at.strftime('%Y-%m-%d %H:%M:%S')
        lines.append(f"  Completed: {completed_str}")

    return '\n'.join(lines)


def format_task_list(tasks: List[Task]) -> str:
    """
    Format a list of tasks as a table.

    Args:
        tasks: List of tasks to format.

    Returns:
        str: Formatted task list as a table.
    """
    if not tasks:
        return "No tasks to display."

    # Define column widths
    id_width = 36  # UUID is 36 characters
    title_width = 30
    priority_width = 8
    status_width = 10
    due_date_width = 12

    # Header
    lines = []
    header = (
        f"{'ID':<{id_width}} | "
        f"{'Title':<{title_width}} | "
        f"{'Priority':<{priority_width}} | "
        f"{'Status':<{status_width}} | "
        f"{'Due Date':<{due_date_width}}"
    )
    lines.append(header)
    lines.append('-' * len(header))

    # Task rows
    for task in tasks:
        # Truncate title if too long
        title_display = task.title[:title_width] if len(task.title) > title_width else task.title

        # Format due date - handle datetime objects
        if task.due_date:
            due_date_display = task.due_date.strftime('%Y-%m-%d')
        else:
            due_date_display = 'N/A'

        row = (
            f"{str(task.id):<{id_width}} | "
            f"{title_display:<{title_width}} | "
            f"{task.priority.value:<{priority_width}} | "
            f"{task.status.value:<{status_width}} | "
            f"{due_date_display:<{due_date_width}}"
        )
        lines.append(row)

    return '\n'.join(lines)


def main() -> int:
    """
    Main entry point for the CLI application.

    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    parser = create_parser()
    args = parser.parse_args()

    # Command dispatch
    if args.command == 'add':
        cmd_add(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'complete':
        cmd_complete(args)
    elif args.command == 'incomplete':
        cmd_incomplete(args)
    elif args.command == 'delete':
        cmd_delete(args)
    elif args.command == 'clear':
        cmd_clear(args)
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
