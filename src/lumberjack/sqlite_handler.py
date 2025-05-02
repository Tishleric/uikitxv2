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

    - Writes structured function execution summaries (INFO level, specific prefixes like
      FUNC_EXEC_LOG:, CPU_TRACE_LOG:, MEMORY_TRACE_LOG:) to the 'function_log' table.
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
        """Connects to the database and creates tables if needed."""
        try:
            db_dir = os.path.dirname(self.db_filename)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            self.conn = sqlite3.connect(self.db_filename, check_same_thread=False)
            self.cursor = self.conn.cursor()

            # --- Create function_log table (Existing) ---
            create_function_log_table_sql = """
            CREATE TABLE IF NOT EXISTS function_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_uuid TEXT NOT NULL UNIQUE,
                timestamp TEXT NOT NULL,
                function_name TEXT NOT NULL,
                execution_time_s REAL NOT NULL,
                cpu_usage_delta REAL NULL,
                memory_usage_delta_mb REAL NULL
            );
            """
            create_function_log_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_log_uuid ON function_log (log_uuid);
            """
            self.cursor.execute(create_function_log_table_sql)
            self.cursor.execute(create_function_log_index_sql)

            # --- NEW: Create flowTrace table ---
            create_flow_trace_table_sql = """
            CREATE TABLE IF NOT EXISTS flowTrace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_uuid TEXT NOT NULL,
                level TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                function_name TEXT NOT NULL,
                message TEXT NOT NULL
            );
            """
            # Optional: Index on log_uuid or timestamp for faster querying
            create_flow_trace_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_flowTrace_log_uuid ON flowTrace (log_uuid);
            """
            self.cursor.execute(create_flow_trace_table_sql)
            self.cursor.execute(create_flow_trace_index_sql)
            # --- End New Table ---

            self.conn.commit()
            # print(f"SQLiteHandler initialized with DB: {self.db_filename}")

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
        Processes specific log records based on prefixes and writes them to
        either function_log or flowTrace table.
        """
        # Don't process if handler level is higher than record level, or if DB connection failed
        # Note: We rely on setup_logging setting the handler level appropriately (e.g., INFO)
        if record.levelno < self.level or self.cursor is None or self.conn is None:
            return

        # Prefixes for routing
        func_log_prefix = "FUNC_EXEC_LOG:"
        cpu_log_prefix = "CPU_TRACE_LOG:"
        mem_log_prefix = "MEMORY_TRACE_LOG:"
        flow_trace_prefix = "FLOW_TRACE:" # New prefix for the summary/error log

        msg = record.getMessage() # Get the raw message

        try:
            log_uuid = None # Keep track of uuid for potential error reporting

            # --- Route to function_log table ---
            if msg.startswith(func_log_prefix):
                json_str = msg[len(func_log_prefix):]
                log_data = json.loads(json_str)
                log_uuid = log_data.get('log_uuid')
                if log_uuid is None: return

                timestamp_str = log_data.get('timestamp')
                func_name = log_data.get('name')
                duration_s = log_data.get('duration_s')
                if timestamp_str is None or func_name is None or duration_s is None:
                    print(f"Warning: Missing data in FUNC_EXEC_LOG record: {log_data}")
                    return

                insert_sql = """
                INSERT INTO function_log (log_uuid, timestamp, function_name, execution_time_s)
                VALUES (?, ?, ?, ?);
                """
                self.cursor.execute(insert_sql, (log_uuid, timestamp_str, func_name, duration_s))
                self.conn.commit()
                return # Handled this record

            elif msg.startswith(cpu_log_prefix):
                json_str = msg[len(cpu_log_prefix):]
                log_data = json.loads(json_str)
                log_uuid = log_data.get('log_uuid')
                if log_uuid is None: return

                cpu_delta = log_data.get('cpu_delta')
                if cpu_delta is None:
                    print(f"Warning: Missing data in CPU_TRACE_LOG record: {log_data}")
                    return

                update_sql = """
                UPDATE function_log SET cpu_usage_delta = ? WHERE log_uuid = ?;
                """
                self.cursor.execute(update_sql, (cpu_delta, log_uuid))
                if self.cursor.rowcount == 0:
                     print(f"Warning: CPU_TRACE_LOG received, but no matching row found for log_uuid: {log_uuid}")
                self.conn.commit()
                return # Handled this record

            elif msg.startswith(mem_log_prefix):
                json_str = msg[len(mem_log_prefix):]
                log_data = json.loads(json_str)
                log_uuid = log_data.get('log_uuid')
                if log_uuid is None: return

                mem_delta = log_data.get('memory_delta_mb')
                if mem_delta is None:
                    print(f"Warning: Missing data in MEMORY_TRACE_LOG record: {log_data}")
                    return

                update_sql = """
                UPDATE function_log SET memory_usage_delta_mb = ? WHERE log_uuid = ?;
                """
                self.cursor.execute(update_sql, (mem_delta, log_uuid))
                if self.cursor.rowcount == 0:
                     print(f"Warning: MEMORY_TRACE_LOG received, but no matching row found for log_uuid: {log_uuid}")
                self.conn.commit()
                return # Handled this record

            # --- NEW: Route to flowTrace table ---
            elif msg.startswith(flow_trace_prefix):
                json_str = msg[len(flow_trace_prefix):]
                log_data = json.loads(json_str)

                # Extract data for flowTrace
                log_uuid = log_data.get('log_uuid')
                level = log_data.get('level') # Should be 'INFO' or 'ERROR'
                timestamp = log_data.get('timestamp')
                function_name = log_data.get('function_name')
                message = log_data.get('message')

                # Basic validation
                if not all([log_uuid, level, timestamp, function_name, message]):
                     print(f"Warning: Missing data in FLOW_TRACE record: {log_data}")
                     return

                insert_flow_sql = """
                INSERT INTO flowTrace (log_uuid, level, timestamp, function_name, message)
                VALUES (?, ?, ?, ?, ?);
                """
                self.cursor.execute(insert_flow_sql, (
                    log_uuid,
                    level,
                    timestamp,
                    function_name,
                    message
                ))
                self.conn.commit()
                return # Handled this record

            # --- End New Routing ---

            # If message didn't match any prefix, it's ignored by this handler

        except json.JSONDecodeError:
            print(f"Error decoding JSON from log message: {msg}")
        except sqlite3.IntegrityError as e:
             # This might happen if function_log gets a duplicate UUID somehow
             print(f"Database integrity error (likely duplicate log_uuid '{log_uuid}' for function_log): {e}")
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
                # print("SQLiteHandler connection closed.")
            except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                self.conn = None
                self.cursor = None
            except Exception as e:
                print(f"Error closing SQLite connection: {e}")
                self.conn = None
                self.cursor = None
        super().close()
