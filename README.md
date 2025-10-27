# Task Manager CLI

A command-line task manager application built in Python following Test-Driven AI Development (TD-AID) methodology. Manage your daily tasks efficiently from the terminal with features including priority levels, due dates, and status tracking.

## Features

- ✅ **Create tasks** with title, description, priority, and due dates
- 📋 **List tasks** with flexible filtering and sorting
- ✔️ **Mark tasks complete** or incomplete
- 🗑️ **Delete tasks** individually or clear all completed tasks
- 💾 **Persistent storage** with atomic writes and automatic backups
- 🎯 **Priority levels**: High, Medium, Low
- 📅 **Due date tracking** with ISO date format
- 🔒 **Data integrity** through JSON schema validation

## Installation

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tdd-cc
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. Install the package in development mode:
   ```bash
   uv pip install -e .
   ```

4. Verify installation:
   ```bash
   task_cli --help
   ```

## Usage

### Adding Tasks

Create a new task with a title (required):
```bash
task_cli add --title "Buy groceries"
```

Create a task with all optional fields:
```bash
task_cli add --title "Complete project report" \
             --description "Finalise Q4 report with charts" \
             --priority high \
             --due-date 2025-12-31
```

**Priority levels**: `high`, `medium` (default), `low`
**Date format**: `YYYY-MM-DD`

### Listing Tasks

List all tasks:
```bash
task_cli list
```

Filter by status:
```bash
task_cli list --status active
task_cli list --status completed
```

Filter by priority:
```bash
task_cli list --priority high
task_cli list --priority medium
task_cli list --priority low
```

Sort tasks:
```bash
task_cli list --sort-by created_at  # Newest first (default)
task_cli list --sort-by due_date    # Earliest due date first
task_cli list --sort-by priority    # High to low priority
```

Combine filters and sorting:
```bash
task_cli list --status active --priority high --sort-by due_date
```

### Completing Tasks

Mark a task as complete:
```bash
task_cli complete <task-id>
```

Mark a task as active (incomplete):
```bash
task_cli incomplete <task-id>
```

### Deleting Tasks

Delete a specific task:
```bash
task_cli delete <task-id>
```

Clear all completed tasks:
```bash
task_cli clear
```

## Data Storage

Tasks are stored in a JSON file with the following default locations:

- **Unix/macOS**: `~/.task_manager/tasks.json`
- **Windows**: `%USERPROFILE%\.task_manager\tasks.json`

### Storage Features

- **Atomic writes**: Prevents data corruption if the process is interrupted
- **Automatic backups**: Creates `.bak` file before overwriting
- **JSON schema validation**: Ensures data integrity on load
- **UTF-8 encoding**: Full Unicode support for international characters

### Custom Storage Location

Override the default storage path using the `TASK_STORAGE_PATH` environment variable:

```bash
export TASK_STORAGE_PATH="/path/to/custom/tasks.json"
task_cli list
```

## Development

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src/task_manager --cov-report=term-missing
```

Run specific test file:
```bash
pytest tests/test_operations.py
```

Run tests in verbose mode:
```bash
pytest -v
```

### Test Coverage

The project maintains high test coverage:

- **Models**: 98.39% coverage (33 tests)
- **Storage**: 97.89% coverage (35 tests)
- **Operations**: 98.41% coverage (40 tests)
- **CLI**: 76.52% coverage (46 tests)
- **Integration**: Full end-to-end testing (22 tests)
- **Overall**: 90.08% coverage (176 total tests)

### Code Structure

```
task_manager/
├── src/
│   └── task_manager/
│       ├── __init__.py
│       ├── models.py       # Task model and data structures
│       ├── storage.py      # JSON file handling with atomic writes
│       ├── operations.py   # Core task operations (CRUD + filtering)
│       └── cli.py          # Command-line interface
├── tests/
│   ├── test_models.py      # Unit tests for Task model
│   ├── test_storage.py     # Unit tests for storage layer
│   ├── test_operations.py  # Unit tests for business logic
│   ├── test_cli.py         # Unit tests for CLI layer
│   └── test_integration.py # End-to-end integration tests
├── pyproject.toml          # Project configuration
└── README.md
```

## Architecture

### Layered Architecture

The application follows a clean layered architecture:

1. **Domain Models** (`models.py`): Task data class with validation
2. **Storage Layer** (`storage.py`): JSON persistence with atomic writes
3. **Business Logic** (`operations.py`): CRUD operations, filtering, sorting
4. **CLI Layer** (`cli.py`): Argument parsing and user interface

### Data Flow

```
CLI Command → operations.py → storage.py → tasks.json
     ↓              ↓              ↓
  Validation    Business      Atomic
  & Parsing      Logic         Write
```

## Troubleshooting

### Common Issues

**Issue**: `task_cli: command not found`

**Solution**: Ensure the virtual environment is activated and the package is installed:
```bash
source .venv/bin/activate
uv pip install -e .
```

---

**Issue**: `Permission denied` when writing tasks

**Solution**: Check file permissions on the storage directory:
```bash
ls -la ~/.task_manager/
chmod 755 ~/.task_manager
chmod 644 ~/.task_manager/tasks.json
```

---

**Issue**: `StorageError: Invalid JSON format`

**Solution**: The tasks.json file may be corrupted. Restore from backup:
```bash
cd ~/.task_manager
cp tasks.json.bak tasks.json
```

---

**Issue**: Tasks not persisting after restart

**Solution**: Verify the storage path is correct:
```bash
echo $TASK_STORAGE_PATH  # Should be empty or valid path
ls -la ~/.task_manager/tasks.json
```

## Project Methodology

This project was built using **Test-Driven AI Development (TD-AID)**, a methodology that emphasises:

- Writing tests **before** implementation code
- Never modifying tests to make them pass
- Writing only the minimum code necessary
- Continuous refactoring while maintaining passing tests

### Development Phases

1. **Phase 0**: Project Setup
2. **Phase 1**: Domain Models (33 tests)
3. **Phase 2**: Storage Layer (35 tests)
4. **Phase 3**: Business Logic (40 tests)
5. **Phase 4**: CLI Layer (46 tests)
6. **Phase 5**: Integration & Polish (22 tests)

**Total**: 176 tests, 90.08% coverage

## Examples

### Daily Workflow

```bash
# Morning: Add today's tasks
task_cli add --title "Review pull requests" --priority high
task_cli add --title "Team standup" --priority medium --due-date 2025-10-28
task_cli add --title "Update documentation" --priority low

# Check what needs doing
task_cli list --status active --sort-by priority

# Complete tasks as you go
task_cli complete <task-id>

# Evening: Clear completed tasks
task_cli clear
```

### Weekly Review

```bash
# See all active tasks sorted by due date
task_cli list --status active --sort-by due_date

# See what was completed this week
task_cli list --status completed

# Clean up completed tasks
task_cli clear
```

## Acknowledgment

Thank you to Andrew Cranston for sharing his AI assisted Test-Driven Development methodology, [TD-AID](https://andrewjcode.substack.com/p/ai-is-writing-terrible-code).

## Contributing

This project follows TD-AID principles. When contributing:

1. Always write tests before implementation
2. Never modify tests to make them pass - fix the implementation instead
3. Ensure all tests pass before submitting
4. Maintain code coverage above 90%
5. Use British English spelling in code and documentation

## Licence

This project is part of a Test-Driven AI Development demonstration.

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review the test files for usage examples
- Consult `PLAN.md` and `STAGES.md` for development details
