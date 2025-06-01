# tests/lumberjack/test_sqlite_handler.py

import pytest
import logging
import sqlite3
import json
import time
import os
from pathlib import Path

# Assuming 'src' is accessible in the path for imports
from monitoring.logging.handlers import SQLiteHandler

# --- Fixtures ---

@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Provides a path to a temporary database file."""
    return str(tmp_path / "test_logs.db")

@pytest.fixture
def sqlite_handler(db_path: str) -> SQLiteHandler:
    """Creates an SQLiteHandler instance using the temporary db path."""
    handler = SQLiteHandler(db_filename=db_path)
    # Ensure tables are created before tests run
    assert handler.conn is not None
    assert handler.cursor is not None
    yield handler
    # Teardown: close the handler connection
    handler.close()

@pytest.fixture
def logger_with_handler(sqlite_handler: SQLiteHandler) -> logging.Logger:
    """Creates a logger and attaches the SQLite handler."""
    logger = logging.getLogger("test_sqlite_logger")
    # Clear handlers in case of reuse in test session
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.DEBUG) # Process all levels
    sqlite_handler.setLevel(logging.INFO) # Handler only processes INFO+
    logger.addHandler(sqlite_handler)
    yield logger
    # Teardown: remove handler
    logger.removeHandler(sqlite_handler)

def query_db(db_path: str, sql: str, params=()):
    """Helper function to query the test database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    return results

# --- Test Functions ---

def test_sqlite_handler_initialization(db_path: str):
    """Tests if the handler connects and creates tables."""
    # Check if file exists (handler creation should trigger connection)
    assert not os.path.exists(db_path)
    handler = SQLiteHandler(db_filename=db_path)
    assert os.path.exists(db_path)

    # Check if tables exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='function_log';")
        assert cursor.fetchone() is not None, "'function_log' table not created"
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flowTrace';")
        assert cursor.fetchone() is not None, "'flowTrace' table not created"
    finally:
        conn.close()
        handler.close()

def test_emit_function_log(logger_with_handler: logging.Logger, sqlite_handler: SQLiteHandler, db_path: str):
    """Tests emitting a FUNC_EXEC_LOG record."""
    log_uuid = "func-uuid-123"
    timestamp = "05/02/25 15:00:00"
    func_name = "test_function"
    duration = 0.12345

    log_data = {
        "log_uuid": log_uuid,
        "name": func_name,
        "timestamp": timestamp,
        "duration_s": duration
    }
    log_message = f"FUNC_EXEC_LOG:{json.dumps(log_data)}"

    # Log the message at INFO level (handler's level)
    logger_with_handler.info(log_message)

    # Verify data in function_log table
    results = query_db(db_path, "SELECT log_uuid, timestamp, function_name, execution_time_s FROM function_log WHERE log_uuid = ?", (log_uuid,))
    assert len(results) == 1
    row = results[0]
    assert row[0] == log_uuid
    assert row[1] == timestamp
    assert row[2] == func_name
    assert row[3] == pytest.approx(duration)

    # Verify flowTrace table is empty
    results_flow = query_db(db_path, "SELECT * FROM flowTrace WHERE log_uuid = ?", (log_uuid,))
    assert len(results_flow) == 0


def test_emit_cpu_log(logger_with_handler: logging.Logger, sqlite_handler: SQLiteHandler, db_path: str):
    """Tests emitting a CPU_TRACE_LOG record updates function_log."""
    log_uuid = "cpu-uuid-456"
    # First, insert a base record into function_log
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO function_log (log_uuid, timestamp, function_name, execution_time_s) VALUES (?, ?, ?, ?)",
                   (log_uuid, "05/02/25 15:01:00", "cpu_func", 0.5))
    conn.commit()
    conn.close()

    cpu_delta = 15.75
    log_data = {"log_uuid": log_uuid, "cpu_delta": cpu_delta}
    log_message = f"CPU_TRACE_LOG:{json.dumps(log_data)}"

    logger_with_handler.info(log_message)

    # Verify cpu_usage_delta is updated in function_log table
    results = query_db(db_path, "SELECT cpu_usage_delta FROM function_log WHERE log_uuid = ?", (log_uuid,))
    assert len(results) == 1
    assert results[0][0] == pytest.approx(cpu_delta)


def test_emit_memory_log(logger_with_handler: logging.Logger, sqlite_handler: SQLiteHandler, db_path: str):
    """Tests emitting a MEMORY_TRACE_LOG record updates function_log."""
    log_uuid = "mem-uuid-789"
    # Insert base record
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO function_log (log_uuid, timestamp, function_name, execution_time_s) VALUES (?, ?, ?, ?)",
                   (log_uuid, "05/02/25 15:02:00", "mem_func", 0.8))
    conn.commit()
    conn.close()

    mem_delta = 25.123
    log_data = {"log_uuid": log_uuid, "memory_delta_mb": mem_delta}
    log_message = f"MEMORY_TRACE_LOG:{json.dumps(log_data)}"

    logger_with_handler.info(log_message)

    # Verify memory_usage_delta_mb is updated
    results = query_db(db_path, "SELECT memory_usage_delta_mb FROM function_log WHERE log_uuid = ?", (log_uuid,))
    assert len(results) == 1
    assert results[0][0] == pytest.approx(mem_delta, abs=1e-3)


def test_emit_flow_trace_log_info(logger_with_handler: logging.Logger, sqlite_handler: SQLiteHandler, db_path: str):
    """Tests emitting a FLOW_TRACE: log at INFO level."""
    log_uuid = "flow-info-111"
    timestamp = "05/02/25 15:03:00"
    func_name = "flow_info_func"
    message = "Executed successfully with metrics."

    log_data = {
        "log_uuid": log_uuid,
        "level": "INFO",
        "timestamp": timestamp,
        "function_name": func_name,
        "message": message
    }
    log_message = f"FLOW_TRACE:{json.dumps(log_data)}"

    logger_with_handler.info(log_message)

    # Verify data in flowTrace table
    results = query_db(db_path, "SELECT log_uuid, level, timestamp, function_name, message FROM flowTrace WHERE log_uuid = ?", (log_uuid,))
    assert len(results) == 1
    row = results[0]
    assert row[0] == log_uuid
    assert row[1] == "INFO"
    assert row[2] == timestamp
    assert row[3] == func_name
    assert row[4] == message

    # Verify function_log table is empty for this UUID
    results_func = query_db(db_path, "SELECT * FROM function_log WHERE log_uuid = ?", (log_uuid,))
    assert len(results_func) == 0


def test_emit_flow_trace_log_error(logger_with_handler: logging.Logger, sqlite_handler: SQLiteHandler, db_path: str):
    """Tests emitting a FLOW_TRACE: log at ERROR level."""
    log_uuid = "flow-error-222"
    timestamp = "05/02/25 15:04:00"
    func_name = "flow_error_func"
    error_message = "Something failed."

    log_data = {
        "log_uuid": log_uuid,
        "level": "ERROR",
        "timestamp": timestamp,
        "function_name": func_name,
        "message": f"Error: {error_message}"
    }
    log_message = f"FLOW_TRACE:{json.dumps(log_data)}"

    # Log at ERROR level (should still be handled by INFO level handler)
    logger_with_handler.error(log_message)

    # Verify data in flowTrace table
    results = query_db(db_path, "SELECT log_uuid, level, timestamp, function_name, message FROM flowTrace WHERE log_uuid = ?", (log_uuid,))
    assert len(results) == 1
    row = results[0]
    assert row[0] == log_uuid
    assert row[1] == "ERROR" # Check level
    assert row[2] == timestamp
    assert row[3] == func_name
    assert row[4] == f"Error: {error_message}"


def test_emit_ignores_other_messages(logger_with_handler: logging.Logger, sqlite_handler: SQLiteHandler, db_path: str):
    """Tests that messages without the specific prefixes are ignored."""
    logger_with_handler.info("This is a standard info message.")
    logger_with_handler.debug("This is a debug message.") # Below handler level
    logger_with_handler.warning("This is a warning message.") # No prefix

    # Verify both tables are empty
    results_func = query_db(db_path, "SELECT * FROM function_log")
    assert len(results_func) == 0
    results_flow = query_db(db_path, "SELECT * FROM flowTrace")
    assert len(results_flow) == 0


def test_emit_handles_malformed_json(logger_with_handler: logging.Logger, sqlite_handler: SQLiteHandler, db_path: str, capsys):
    """Tests that malformed JSON in prefixed messages is handled gracefully."""
    log_message = "FUNC_EXEC_LOG:{\"log_uuid\": \"bad-json-1\", \"name\": \"test\"" # Missing closing brace

    logger_with_handler.info(log_message)

    # Verify tables are empty
    results_func = query_db(db_path, "SELECT * FROM function_log")
    assert len(results_func) == 0
    results_flow = query_db(db_path, "SELECT * FROM flowTrace")
    assert len(results_flow) == 0

    # Check for error message printed to stderr (or stdout depending on logging config)
    captured = capsys.readouterr()
    assert "Error decoding JSON" in captured.out or "Error decoding JSON" in captured.err


def test_emit_flow_trace_malformed_json(
    logger_with_handler: logging.Logger,
    sqlite_handler: SQLiteHandler,
    db_path: str,
    capsys,
):
    """Ensures FLOW_TRACE messages with bad JSON do not crash the handler."""
    log_message = "FLOW_TRACE:{\"log_uuid\": \"bad-json-2\""  # Missing closing brace

    logger_with_handler.info(log_message)

    results = query_db(db_path, "SELECT * FROM flowTrace")
    assert len(results) == 0

    captured = capsys.readouterr()
    assert "Error decoding JSON" in captured.out or "Error decoding JSON" in captured.err


def test_emit_handles_missing_data(logger_with_handler: logging.Logger, sqlite_handler: SQLiteHandler, db_path: str, capsys):
    """Tests handling of records with missing required fields."""
    # Missing 'duration_s' in FUNC_EXEC_LOG
    log_data_func = {"log_uuid": "missing-data-1", "name": "func1", "timestamp": "05/02/25 15:05:00"}
    log_message_func = f"FUNC_EXEC_LOG:{json.dumps(log_data_func)}"

    # Missing 'level' in FLOW_TRACE
    log_data_flow = {"log_uuid": "missing-data-2", "timestamp": "05/02/25 15:06:00", "function_name": "func2", "message": "msg"}
    log_message_flow = f"FLOW_TRACE:{json.dumps(log_data_flow)}"

    logger_with_handler.info(log_message_func)
    logger_with_handler.info(log_message_flow)

    # Verify tables are empty
    results_func = query_db(db_path, "SELECT * FROM function_log")
    assert len(results_func) == 0
    results_flow = query_db(db_path, "SELECT * FROM flowTrace")
    assert len(results_flow) == 0

    # Check for warning messages printed
    captured = capsys.readouterr()
    assert "Warning: Missing data in FUNC_EXEC_LOG" in captured.out or "Warning: Missing data in FUNC_EXEC_LOG" in captured.err
    assert "Warning: Missing data in FLOW_TRACE" in captured.out or "Warning: Missing data in FLOW_TRACE" in captured.err


def test_sqlite_handler_close(db_path: str):
    """Tests the close method."""
    handler = SQLiteHandler(db_filename=db_path)
    assert handler.conn is not None
    assert handler.cursor is not None

    handler.close()

    assert handler.conn is None
    assert handler.cursor is None

    # Try closing again (should not raise error)
    try:
        handler.close()
    except Exception as e:
        pytest.fail(f"Closing handler second time raised exception: {e}")


def test_close_idempotent(db_path: str):
    """Calling close multiple times should not raise and leaves state cleared."""
    handler = SQLiteHandler(db_filename=db_path)
    handler.close()
    handler.close()
    handler.close()

    assert handler.conn is None
    assert handler.cursor is None


def test_initialization_schema_error(monkeypatch, db_path: str):
    """Handler sets connection to None when table creation fails."""

    class DummyCursor:
        def execute(self, sql, params=None):
            raise sqlite3.OperationalError("create fail")

    class DummyConn:
        def __init__(self):
            self.row_factory = None

        def cursor(self):
            return DummyCursor()

        def commit(self):
            pass

        def close(self):
            pass

    def failing_connect(*args, **kwargs):
        return DummyConn()

    monkeypatch.setattr(sqlite3, "connect", failing_connect)

    handler = SQLiteHandler(db_filename=db_path)

    assert handler.conn is None
    assert handler.cursor is None

