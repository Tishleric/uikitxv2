# demo/query_runner.py

# No logging import needed here anymore unless for specific low-level debug
# import logging
import os
import sys
import yaml
import sqlite3
import datetime
import time # For potential delays or session expiry check

# --- Adjust Python path to find 'src' ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    # Path adjustment logging removed
    sys.path.insert(0, src_path)
# --- End Path Adjustment ---

# --- Import Decorators ---
try:
    from decorators.trace_closer import TraceCloser
    from decorators.trace_time import TraceTime
    # TraceCpu/TraceMemory could also be added if desired
except ImportError as e:
    # If imports fail, print is the only reliable option before logging is set up
    print(f"[Import Error] Failed to import decorators: {e}", file=sys.stderr)
    sys.exit(1)
# --- End Imports ---

# --- Constants ---
QUERIES_FILE = os.path.join(current_dir, 'queries.yaml')
# --- Use a file-based DB for demo data persistence ---
# Ensure logs directory exists (usually done by logging setup, but good practice)
LOG_DB_DIR = os.path.join(project_root, 'logs')
os.makedirs(LOG_DB_DIR, exist_ok=True)
DB_PATH = os.path.join(LOG_DB_DIR, 'query_runner_demo_data.db')
# --- End DB Path Change ---

# --- Load Queries ---
QUERIES = {} # Initialize as empty dict
try:
    # YAML loading logging removed
    with open(QUERIES_FILE, 'r') as f:
        QUERIES = yaml.safe_load(f)
    if not QUERIES:
        # Error logging removed - rely on potential downstream errors if needed
        QUERIES = {}
except FileNotFoundError:
    # Error logging removed
    pass # Let it proceed, _execute_query will fail if key not found
except yaml.YAMLError as e:
    # Error logging removed
    print(f"[Error] Failed to parse YAML file '{QUERIES_FILE}': {e}", file=sys.stderr) # Keep critical print
    # Keep QUERIES as {}
except Exception as e:
    # Error logging removed
    print(f"[Error] An unexpected error occurred loading '{QUERIES_FILE}': {e}", file=sys.stderr) # Keep critical print
    # Keep QUERIES as {}

# --- End Load Queries ---

# --- Database Setup ---
def setup_demo_db():
    """Creates/resets the file-based SQLite DB and populates with demo data."""
    # Delete existing DB file to ensure clean state for demo
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError as e:
             print(f"Warning: Could not remove existing demo DB {DB_PATH}: {e}", file=sys.stderr)

    conn = None # Initialize conn
    try:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            email TEXT,
            creation_date TIMESTAMP
        )""")
        cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            status TEXT,
            last_updated TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )""")
        cursor.execute("""
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            login_time TIMESTAMP,
            expiry_time TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )""")

        # Insert sample data
        now = datetime.datetime.now()
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (1, 'alice', 'alice@example.com', now - datetime.timedelta(days=10)))
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (2, 'bob', 'bob@example.com', now - datetime.timedelta(days=5)))
        cursor.execute("INSERT INTO orders (user_id, status, last_updated) VALUES (?, ?, ?)", (1, 'Pending', now - datetime.timedelta(hours=1)))
        cursor.execute("INSERT INTO orders (user_id, status, last_updated) VALUES (?, ?, ?)", (2, 'Shipped', now - datetime.timedelta(minutes=30)))
        cursor.execute("INSERT INTO orders (user_id, status, last_updated) VALUES (?, ?, ?)", (1, 'Delivered', now))
        cursor.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", ('abc', 1, now - datetime.timedelta(minutes=60), now + datetime.timedelta(minutes=60))) # Active
        cursor.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", ('def', 2, now - datetime.timedelta(minutes=120), now - datetime.timedelta(minutes=60))) # Expired

        conn.commit()
        # Setup logging removed
    except sqlite3.Error as db_err:
        # Error logging removed, print critical setup failure
        print(f"[Critical Error] Failed to set up demo database '{DB_PATH}': {db_err}", file=sys.stderr)
        # Depending on severity, might want to exit
        sys.exit(1)
    except Exception as e:
        # Error logging removed, print critical setup failure
        print(f"[Critical Error] An unexpected error occurred during demo DB setup: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()


# Call setup when module loads
setup_demo_db()
# --- End Database Setup ---

# --- Decorated Query Functions ---

def _execute_query(query_key: str, params=(), fetch_one=False, fetch_all=False, commit=False):
    """Helper to execute a query from the loaded dictionary."""
    sql = QUERIES.get(query_key)
    if not sql:
        # Error logging removed
        raise ValueError(f"Query key '{query_key}' not found in queries file.")

    conn = None
    try:
        # Use the file-based DB path
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cursor = conn.cursor()
        # Execution logging removed (decorators handle start/end)
        cursor.execute(sql, params)

        result = None
        if fetch_one:
            result = cursor.fetchone()
            # Result logging removed (decorators handle return value)
        elif fetch_all:
            result = cursor.fetchall()
            # Result logging removed

        if commit:
            conn.commit()
            result = cursor.rowcount # Return number of affected rows for commits
            # Commit logging removed

        return result
    except sqlite3.Error as db_err:
        # Specific DB error logging removed
        # Re-raise the exception so TraceCloser can catch it and log the final error state
        raise
    except Exception as e:
        # Specific unexpected error logging removed
        raise # Re-raise for TraceCloser
    finally:
        if conn:
            conn.close()
            # Connection close logging removed


@TraceCloser()
@TraceTime(log_args=True, log_return=True)
def get_user_by_id(user_id: int):
    """Fetches a user record by ID."""
    return _execute_query('getUserById', params=(user_id,), fetch_one=True)

@TraceCloser()
@TraceTime(log_args=True, log_return=False) # Don't log return (rowcount)
def update_order_status(new_status: str, order_id: int):
    """Updates the status of a specific order."""
    return _execute_query('updateOrderStatus', params=(new_status, order_id), commit=True)

@TraceCloser()
@TraceTime(log_args=False, log_return=True) # Log results, hide args (timestamp)
def get_active_sessions():
    """Fetches all sessions that haven't expired."""
    # Pass the current time to the query
    return _execute_query('getActiveSessions', params=(datetime.datetime.now(),), fetch_all=True)

@TraceCloser()
@TraceTime(log_args=True, log_return=False) # Designed to fail
def get_non_existent_data(item_id: int):
    """Attempts to query a table that doesn't exist."""
    return _execute_query('getNonExistentTableData', params=(item_id,), fetch_one=True)

# --- End Decorated Query Functions ---
