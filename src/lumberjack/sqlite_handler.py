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
    - Aggregates performance metrics into the 'AveragePerformance' table.
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
            # Use Row factory for easier access in emit
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

            # --- Create flowTrace table ---
            create_flow_trace_table_sql = """
            CREATE TABLE IF NOT EXISTS flowTrace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                machine TEXT NOT NULL,
                user TEXT NOT NULL,
                level TEXT NOT NULL,
                function TEXT NOT NULL,
                message TEXT NOT NULL
            );
            """
            create_flow_trace_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_flowTrace_timestamp ON flowTrace (timestamp);
            """
            self.cursor.execute(create_flow_trace_table_sql)
            self.cursor.execute(create_flow_trace_index_sql)

            # --- Create AveragePerformance table (Revised Schema) ---
            create_avg_perf_table_sql = """
            CREATE TABLE IF NOT EXISTS AveragePerformance (
                function_name TEXT PRIMARY KEY,
                call_count INTEGER NOT NULL DEFAULT 0,
                error_count INTEGER NOT NULL DEFAULT 0,
                avg_duration_s REAL NOT NULL DEFAULT 0.0,
                avg_cpu_delta REAL NOT NULL DEFAULT 0.0,
                avg_memory_delta_mb REAL NOT NULL DEFAULT 0.0,
                last_updated TEXT NOT NULL
            );
            """
            create_avg_perf_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_AvgPerf_last_updated ON AveragePerformance (last_updated);
            """
            self.cursor.execute(create_avg_perf_table_sql)
            self.cursor.execute(create_avg_perf_index_sql)
            # --- End Create AveragePerformance ---

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
        Processes FLOW_TRACE log records, writes them to the flowTrace table,
        and updates the AveragePerformance table.
        Ignores all other messages.
        """
        if record.levelno < self.level or self.cursor is None or self.conn is None:
            return

        flow_trace_prefix = "FLOW_TRACE:"
        msg = record.getMessage()

        if not msg.startswith(flow_trace_prefix):
            return # Ignore messages not matching the prefix

        try:
            json_str = msg[len(flow_trace_prefix):]
            log_data = json.loads(json_str)

            # --- Extract common data ---
            display_timestamp = log_data.get('timestamp') # For flowTrace table
            iso_timestamp = log_data.get('timestamp_iso') # For AveragePerformance update
            machine = log_data.get('machine', 'N/A')
            user = log_data.get('user', 'N/A')
            level = log_data.get('level')
            function_name = log_data.get('function')
            message = log_data.get('message')

            # Basic validation
            if not all([display_timestamp, iso_timestamp, level, function_name, message]):
                 print(f"Warning: Missing required common data in FLOW_TRACE record: {log_data}")
                 return

            # --- Insert into flowTrace table ---
            insert_flow_sql = """
            INSERT INTO flowTrace (timestamp, machine, user, level, function, message)
            VALUES (?, ?, ?, ?, ?, ?);
            """
            self.cursor.execute(insert_flow_sql, (
                display_timestamp, machine, user, level, function_name, message
            ))

            # --- Update AveragePerformance table ---
            self._update_average_performance(function_name, level, iso_timestamp, log_data)

            self.conn.commit() # Commit both inserts/updates

        except json.JSONDecodeError:
            print(f"Error decoding JSON from log message: {msg}")
            if self.conn: self.conn.rollback() # Rollback if JSON fails
        except sqlite3.Error as e:
            if self.conn and "Cannot operate on a closed database" not in str(e):
                 print(f"Error during database operation for log: {e}")
            try:
                if self.conn: self.conn.rollback()
            except sqlite3.Error:
                pass
        except Exception as e:
            print(f"Unexpected error in SQLiteHandler.emit: {e}")
            try:
                if self.conn: self.conn.rollback()
            except sqlite3.Error:
                pass

    def _update_average_performance(self, function_name: str, level: str, iso_timestamp: str, log_data: dict):
        """
        Helper method to update the AveragePerformance table with function metrics.
        
        This method maintains running averages of performance metrics for each function.
        For INFO level logs, it updates call count and calculates new averages for 
        duration, CPU usage, and memory usage. For ERROR level logs, it increments
        the error counter.
        
        Args:
            function_name (str): Name of the function being logged.
            level (str): Log level ('INFO' or 'ERROR').
            iso_timestamp (str): ISO 8601 timestamp of the log event.
            log_data (dict): Dictionary containing metrics extracted from the log record.
                Expected keys for INFO level:
                - metric_duration_s: Execution time in seconds
                - metric_cpu_delta: CPU usage percentage delta
                - metric_memory_delta_mb: Memory usage delta in MB
                
        Note:
            - For the first call to a function, initial averages are set to the current metrics.
            - For subsequent calls, a weighted average formula is used:
              new_avg = (old_avg * old_count + new_value) / new_count
        """
        if self.cursor is None or self.conn is None:
             return

        # Fetch existing record
        self.cursor.execute("SELECT * FROM AveragePerformance WHERE function_name = ?", (function_name,))
        existing_row = self.cursor.fetchone()

        if level == "INFO":
            # Extract metrics for INFO level
            metric_duration = log_data.get('metric_duration_s')
            metric_cpu = log_data.get('metric_cpu_delta')
            metric_memory = log_data.get('metric_memory_delta_mb')

            # Convert None metrics to 0.0 for calculation
            current_duration = float(metric_duration) if metric_duration is not None else 0.0
            current_cpu = float(metric_cpu) if metric_cpu is not None else 0.0
            current_memory = float(metric_memory) if metric_memory is not None else 0.0

            if existing_row:
                # Update existing row
                old_count = existing_row['call_count']
                new_count = old_count + 1

                # Calculate new averages using the formula: new_avg = (old_avg * old_count + new_value) / new_count
                new_avg_duration = (existing_row['avg_duration_s'] * old_count + current_duration) / new_count
                new_avg_cpu = (existing_row['avg_cpu_delta'] * old_count + current_cpu) / new_count
                new_avg_memory = (existing_row['avg_memory_delta_mb'] * old_count + current_memory) / new_count

                update_sql = """
                UPDATE AveragePerformance SET
                    call_count = ?,
                    avg_duration_s = ?,
                    avg_cpu_delta = ?,
                    avg_memory_delta_mb = ?,
                    last_updated = ?
                WHERE function_name = ?;
                """
                self.cursor.execute(update_sql, (
                    new_count,
                    new_avg_duration,
                    new_avg_cpu,
                    new_avg_memory,
                    iso_timestamp,
                    function_name
                ))
            else:
                # Insert new row
                insert_sql = """
                INSERT INTO AveragePerformance (
                    function_name, call_count, error_count,
                    avg_duration_s, avg_cpu_delta, avg_memory_delta_mb,
                    last_updated
                ) VALUES (?, 1, 0, ?, ?, ?, ?);
                """
                self.cursor.execute(insert_sql, (
                    function_name,
                    current_duration, # First call, average is just the current value
                    current_cpu,
                    current_memory,
                    iso_timestamp
                ))

        elif level == "ERROR":
            if existing_row:
                # Update existing row
                new_error_count = existing_row['error_count'] + 1
                update_sql = """
                UPDATE AveragePerformance SET
                    error_count = ?,
                    last_updated = ?
                WHERE function_name = ?;
                """
                self.cursor.execute(update_sql, (new_error_count, iso_timestamp, function_name))
            else:
                # Insert new row
                insert_sql = """
                INSERT INTO AveragePerformance (
                    function_name, call_count, error_count,
                    avg_duration_s, avg_cpu_delta, avg_memory_delta_mb,
                    last_updated
                ) VALUES (?, 0, 1, 0.0, 0.0, 0.0, ?);
                """
                self.cursor.execute(insert_sql, (function_name, iso_timestamp))

        # else: level is neither INFO nor ERROR - do nothing for AveragePerformance


    def close(self):
        """Safely closes the database connection."""
        if self.conn:
            try:
                # Check if connection is usable before trying to close cursor/connection
                self.conn.execute("SELECT 1") # Simple check
                if self.cursor:
                    self.cursor.close()
                    self.cursor = None
                self.conn.close()
                self.conn = None
            except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
                 # Handle cases where connection might already be closed or unusable
                 # print(f"Info: Connection already closed or unusable during close(): {e}")
                 self.conn = None
                 self.cursor = None
            except Exception as e:
                print(f"Error closing SQLite connection: {e}")
                self.conn = None
                self.cursor = None
        super().close()