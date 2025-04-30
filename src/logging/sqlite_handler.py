import logging
import sqlite3
import time
import json
import os

class SQLiteHandler(logging.Handler):
    """
    Custom logging handler that writes specific log records (INFO level)
    containing function execution summaries to an SQLite database.
    Uses a log_uuid to correlate function start, CPU, and Memory trace logs.
    Stateless regarding log linking.
    """
    def __init__(self, db_filename='function_logs.db'):
        super().__init__()
        self.db_filename = db_filename
        self.conn = None
        self.cursor = None
        self._connect_and_initialize()

    def _connect_and_initialize(self):
        """Connects to the database and creates the table if needed."""
        try:
            db_dir = os.path.dirname(self.db_filename)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            self.conn = sqlite3.connect(self.db_filename, check_same_thread=False)
            self.cursor = self.conn.cursor()
            # Create table SQL statement - ADDED memory_usage_delta_mb column
            create_table_sql = """
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
            create_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_log_uuid ON function_log (log_uuid);
            """
            self.cursor.execute(create_table_sql)
            self.cursor.execute(create_index_sql)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error connecting to or initializing database {self.db_filename}: {e}")
            self.conn = None
            self.cursor = None

    def emit(self, record):
        """
        Processes a log record using log_uuid for correlation.
        - If FUNC_EXEC_LOG, inserts a new row.
        - If CPU_TRACE_LOG, updates the row matching the log_uuid with CPU delta.
        - If MEMORY_TRACE_LOG, updates the row matching the log_uuid with Memory delta.
        """
        if self.cursor is None or self.conn is None or record.levelno != logging.INFO:
            return

        func_log_prefix = "FUNC_EXEC_LOG:"
        cpu_log_prefix = "CPU_TRACE_LOG:"
        mem_log_prefix = "MEMORY_TRACE_LOG:" # New prefix
        msg = record.getMessage()

        try:
            log_uuid = None
            log_data = None

            # Extract log_uuid and data based on prefix
            if msg.startswith(func_log_prefix):
                # --- Handle Function Execution Log ---
                json_str = msg[len(func_log_prefix):]
                log_data = json.loads(json_str)
                log_uuid = log_data.get('log_uuid')
                # ... (rest of FUNC_EXEC_LOG handling as before) ...
                if log_uuid is None: return # Basic error check
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

            elif msg.startswith(cpu_log_prefix):
                 # --- Handle CPU Trace Log ---
                json_str = msg[len(cpu_log_prefix):]
                log_data = json.loads(json_str)
                log_uuid = log_data.get('log_uuid')
                # ... (rest of CPU_TRACE_LOG handling as before) ...
                if log_uuid is None: return # Basic error check
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

            elif msg.startswith(mem_log_prefix):
                 # --- Handle Memory Trace Log ---
                json_str = msg[len(mem_log_prefix):]
                log_data = json.loads(json_str)
                log_uuid = log_data.get('log_uuid')

                if log_uuid is None:
                    print(f"Warning: Missing log_uuid in MEMORY_TRACE_LOG record: {log_data}")
                    return

                mem_delta = log_data.get('memory_delta_mb')

                if mem_delta is None:
                    print(f"Warning: Missing data in MEMORY_TRACE_LOG record: {log_data}")
                    return

                # Update the row matching the log_uuid
                update_sql = """
                UPDATE function_log SET memory_usage_delta_mb = ? WHERE log_uuid = ?;
                """
                self.cursor.execute(update_sql, (mem_delta, log_uuid))
                # Check if the update actually affected a row
                if self.cursor.rowcount == 0:
                     print(f"Warning: MEMORY_TRACE_LOG received, but no matching row found for log_uuid: {log_uuid}")
                self.conn.commit() # Commit after update


        except json.JSONDecodeError:
            print(f"Error decoding JSON from log message: {msg}")
        except sqlite3.IntegrityError as e:
             print(f"Database integrity error (likely duplicate log_uuid '{log_uuid}'): {e}")
        except sqlite3.Error as e:
            if "Cannot operate on a closed database" not in str(e):
                 print(f"Error during database operation for log: {e}")
            try:
                if self.conn: self.conn.rollback()
            except sqlite3.Error:
                pass
        except Exception as e:
            print(f"Unexpected error in SQLiteHandler.emit: {e}")

    def close(self):
        """Safely closes the database connection."""
        # ... (close method remains the same) ...
        if self.conn:
            try:
                _ = self.conn.total_changes
                if self.cursor:
                    self.cursor.close()
                self.conn.close()
                self.conn = None
                self.cursor = None
            except sqlite3.ProgrammingError:
                self.conn = None
                self.cursor = None
            except Exception as e:
                print(f"Error closing SQLite connection: {e}")
                self.conn = None
                self.cursor = None
        super().close()

