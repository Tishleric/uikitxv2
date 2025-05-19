# tests/lumberjack/test_logging_config.py

import logging

# Import ListHandler - KEEPING for other tests if needed, but not this one
from logging.handlers import BufferingHandler
from pathlib import Path
from unittest.mock import patch

import pytest

# Assuming 'src' is accessible in the path for imports
from lumberjack.logging_config import setup_logging, shutdown_logging

# --- Fixtures ---

@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    """Provides a temporary directory for log files."""
    d = tmp_path / "logs"
    # setup_logging should create it, but ensure it exists for cleanup checks
    d.mkdir(exist_ok=True)
    return d

@pytest.fixture
def db_path(log_dir: Path) -> str:
    """Provides a path within the temporary log directory."""
    return str(log_dir / "test_config_logs.db")

# --- Custom Handler for testing specific logger ---
# Keep ListHandler definition if used by other tests, otherwise remove
class ListHandler(BufferingHandler):
    def __init__(self, capacity):
        super().__init__(capacity)
        self.buffer = [] # Ensure buffer is initialized as list

    def shouldFlush(self, record):
        return False # Never flush automatically

    def emit(self, record):
        # Store the raw record object instead of formatted string
        self.buffer.append(record)

@pytest.fixture(autouse=True)
def cleanup_logging():
    """Ensures logging state is clean before and after each test."""
    # Before test: Shutdown any existing logging and clear handlers
    shutdown_logging() # Close any handlers from previous tests
    root_logger = logging.getLogger()
    config_logger = logging.getLogger('lumberjack.logging_config')
    # Store original handlers and level
    original_root_handlers = root_logger.handlers[:]
    original_root_level = root_logger.level
    original_config_handlers = config_logger.handlers[:]
    original_config_level = config_logger.level
    original_config_propagate = config_logger.propagate

    # Clear handlers *before* test, pytest might add its own during setup
    root_logger.handlers.clear()
    config_logger.handlers.clear()
    # print("\n[Cleanup Pre] Logging handlers cleared.")

    yield # Run the test

    # After test: Shutdown logging again and restore original state
    # print("[Cleanup Post] Shutting down logging...")
    shutdown_logging()
    root_logger.handlers.clear()
    config_logger.handlers.clear()
    # Restore original state
    for handler in original_root_handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(original_root_level)
    for handler in original_config_handlers:
        config_logger.addHandler(handler)
    config_logger.setLevel(original_config_level)
    config_logger.propagate = original_config_propagate
    # print(f"[Cleanup Post] Logging state restored.")


# --- Test Functions ---

# test_setup_logging_basic remains the same

def test_setup_logging_custom_levels(db_path: str) -> None:
    """Ensure custom log levels apply to logger and handlers."""
    console_h, db_h = setup_logging(
        log_level_main=logging.WARNING,
        log_level_console=logging.ERROR,
        log_level_db=logging.CRITICAL,
        db_path=db_path,
    )

    root_logger = logging.getLogger()

    assert root_logger.level == logging.WARNING
    assert console_h.level == logging.ERROR
    assert db_h.level == logging.CRITICAL


def test_setup_logging_clears_existing_handlers(db_path: str) -> None:
    """Ensure repeated setup does not accumulate handlers."""
    first_console, first_db = setup_logging(db_path=db_path)
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 2

    second_console, second_db = setup_logging(db_path=db_path)

    assert len(root_logger.handlers) == 2
    assert second_console is not first_console
    assert second_db is not first_db

@patch('lumberjack.logging_config.os.makedirs')
@patch('lumberjack.logging_config.logging.basicConfig') # Mock basicConfig
def test_setup_logging_handles_makedirs_error_fallback(mock_basic_config, mock_makedirs, db_path, caplog):
    """
    Tests that setup_logging falls back to basicConfig when makedirs fails
    and logs a critical error.
    """
    mock_makedirs.side_effect = OSError("Permission denied")

    # Use caplog to capture the critical error logged *before* fallback
    with caplog.at_level(logging.CRITICAL, logger='lumberjack.logging_config'):
        # Call the function, expecting it to handle the error internally
        console_h, db_h = setup_logging(db_path=db_path)

    # 1. Check that handlers were NOT successfully returned (or are None)
    #    Based on the current code, it returns None, None on critical failure
    assert console_h is None
    assert db_h is None

    # 2. Check that the critical error was logged by config_logger
    assert "Critical error during logging setup" in caplog.text
    assert "Permission denied" in caplog.text

    # 3. Check that logging.basicConfig was called as a fallback
    mock_basic_config.assert_called_once()
    # Optionally check the arguments passed to basicConfig
    # args, kwargs = mock_basic_config.call_args
    # assert kwargs.get('level') == logging.WARNING


# test_shutdown_logging_closes_db_handler remains the same
# test_shutdown_logging_handles_no_handler remains the same
# test_shutdown_logging_handles_close_error remains the same

# (Include the unchanged test functions here if providing the full file)

