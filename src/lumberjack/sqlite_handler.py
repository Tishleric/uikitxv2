# src/lumberjack/sqlite_handler.py

import logging
import sqlite3
import time
import json
import os
import datetime # Keep for potential internal logging

class SQLiteHandler(logging.Handler):
    """
    Custom logging handler that writes log records to an SQLite database.

    - Writes final summary/error messages (INFO/ERROR level, FLOW_TRACE: prefix)
      from the TraceCloser decorator to the 'flowTrace' table.
    - Ignores other log messages.
    """
    def __init__(self, db_filename='function_logs.db'):
        super().__init__()
        self.db_filename = db_filename
        self.conn = None
        self.cursor = None
        self._connect_and_initialize()

    def _connect_and_initialize(self):
        """Connects to the database and creates the flowTrace table if needed."""
        try:
            db_dir = os.path.dirname(self.db_filename)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            self.conn = sqlite3.connect(self.db_filename, check_same_thread=False)
            self.cursor = self.conn.cursor()

            # --- MODIFIED: Create flowTrace table with new column order/names ---
            # Desired order: timestamp, machine, user, level, function, message
            create_flow_trace_table_sql = """
            CREATE TABLE IF NOT EXISTS flowTrace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                machine TEXT NOT NULL,          -- Renamed from machine_id
                user TEXT NOT NULL,             -- Renamed from user_id
                level TEXT NOT NULL,
                function TEXT NOT NULL, -- Renamed from function_name
                message TEXT NOT NULL
            );
            """
            # Index on timestamp (still valid)
            create_flow_trace_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_flowTrace_timestamp ON flowTrace (timestamp);
            """

            self.cursor.execute(create_flow_trace_table_sql)
            self.cursor.execute(create_flow_trace_index_sql)
            # --- End Modified Table ---

            self.conn.commit()

        except sqlite3.Error as e:
            print(f"Error connecting to or initializing database {self.db_filename}: {e}")
            self.conn = None
            self.cursor = None
        except Exception as e:
             print(f"Unexpected error during SQLiteHandler initialization: {e}")
             self.conn = None
             self.cursor = None


    def emit(self, record):
        """
        Processes FLOW_TRACE log records and writes them to the flowTrace table
        using the new column order/names.
        Ignores all other messages.
        """
        if record.levelno < self.level or self.cursor is None or self.conn is None:
            return

        flow_trace_prefix = "FLOW_TRACE:"

        msg = record.getMessage()

        try:
            if msg.startswith(flow_trace_prefix):
                json_str = msg[len(flow_trace_prefix):]
                log_data = json.loads(json_str)

                # Extract data using the NEW keys expected from TraceCloser
                timestamp = log_data.get('timestamp')
                machine = log_data.get('machine', 'N/A') # Use new key 'machine'
                user = log_data.get('user', 'N/A')       # Use new key 'user'
                level = log_data.get('level')
                function = log_data.get('function')     # Use new key 'function'
                message = log_data.get('message')

                # Basic validation (using new keys)
                if not all([timestamp, level, function, message]):
                     print(f"Warning: Missing required data in FLOW_TRACE record: {log_data}")
                     return

                # --- MODIFIED Insert SQL and Parameters (new order/names) ---
                insert_flow_sql = """
                INSERT INTO flowTrace (timestamp, machine, user, level, function, message)
                VALUES (?, ?, ?, ?, ?, ?);
                """
                self.cursor.execute(insert_flow_sql, (
                    timestamp,
                    machine,
                    user,
                    level,
                    function,
                    message
                ))
                # --- End Modified ---
                self.conn.commit()
                return # Handled this record

        except json.JSONDecodeError:
            print(f"Error decoding JSON from log message: {msg}")
        except sqlite3.Error as e:
            if self.conn and "Cannot operate on a closed database" not in str(e):
                 print(f"Error during database operation for log: {e}")
            try:
                if self.conn: self.conn.rollback()
            except sqlite3.Error:
                pass
        except Exception as e:
            print(f"Unexpected error in SQLiteHandler.emit: {e}")


    def close(self):
        """Safely closes the database connection."""
        if self.conn:
            try:
                _ = self.conn.total_changes
                if self.cursor:
                    self.cursor.close()
                    self.cursor = None
                self.conn.close()
                self.conn = None
            except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                self.conn = None
                self.cursor = None
            except Exception as e:
                print(f"Error closing SQLite connection: {e}")
                self.conn = None
                self.cursor = None
        super().close()
