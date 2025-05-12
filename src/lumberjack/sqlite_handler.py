# src/lumberjack/sqlite_handler.py

import logging
import sqlite3
import time
import json
import os
import datetime

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
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

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
            return

        try:
            json_str = msg[len(flow_trace_prefix):]
            log_data = json.loads(json_str)

            display_timestamp = log_data.get('timestamp')
            iso_timestamp = log_data.get('timestamp_iso')
            machine = log_data.get('machine', 'N/A')
            user = log_data.get('user', 'N/A')
            level = log_data.get('level')
            function_name = log_data.get('function')
            message = log_data.get('message')

            if not all([display_timestamp, iso_timestamp, level, function_name, message]):
                 print(f"Warning: Missing required common data in FLOW_TRACE record: {log_data}")
                 return

            insert_flow_sql = """
            INSERT INTO flowTrace (timestamp, machine, user, level, function, message)
            VALUES (?, ?, ?, ?, ?, ?);
            """
            self.cursor.execute(insert_flow_sql, (
                display_timestamp, machine, user, level, function_name, message
            ))

            self._update_average_performance(function_name, level, iso_timestamp, log_data)

            self.conn.commit()

        except json.JSONDecodeError:
            print(f"Error decoding JSON from log message: {msg}")
            if self.conn: self.conn.rollback()
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
        """Helper method to handle updates to the AveragePerformance table."""
        if self.cursor is None or self.conn is None:
             return

        self.cursor.execute("SELECT * FROM AveragePerformance WHERE function_name = ?", (function_name,))
        existing_row = self.cursor.fetchone()

        if level == "INFO":
            metric_duration = log_data.get('metric_duration_s')
            metric_cpu = log_data.get('metric_cpu_delta')
            metric_memory = log_data.get('metric_memory_delta_mb')

            current_duration = float(metric_duration) if metric_duration is not None else 0.0
            current_cpu = float(metric_cpu) if metric_cpu is not None else 0.0
            current_memory = float(metric_memory) if metric_memory is not None else 0.0

            if existing_row:
                old_count = existing_row['call_count']
                new_count = old_count + 1

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
                insert_sql = """
                INSERT INTO AveragePerformance (
                    function_name, call_count, error_count,
                    avg_duration_s, avg_cpu_delta, avg_memory_delta_mb,
                    last_updated
                ) VALUES (?, 1, 0, ?, ?, ?, ?);
                """
                self.cursor.execute(insert_sql, (
                    function_name,
                    current_duration,
                    current_cpu,
                    current_memory,
                    iso_timestamp
                ))

        elif level == "ERROR":
            if existing_row:
                new_error_count = existing_row['error_count'] + 1
                update_sql = """
                UPDATE AveragePerformance SET
                    error_count = ?,
                    last_updated = ?
                WHERE function_name = ?;
                """
                self.cursor.execute(update_sql, (new_error_count, iso_timestamp, function_name))
            else:
                insert_sql = """
                INSERT INTO AveragePerformance (
                    function_name, call_count, error_count,
                    avg_duration_s, avg_cpu_delta, avg_memory_delta_mb,
                    last_updated
                ) VALUES (?, 0, 1, 0.0, 0.0, 0.0, ?);
                """
                self.cursor.execute(insert_sql, (function_name, iso_timestamp))


    def close(self):
        """Safely closes the database connection."""
        if self.conn:
            try:
                self.conn.execute("SELECT 1")
                if self.cursor:
                    self.cursor.close()
                    self.cursor = None
                self.conn.close()
                self.conn = None
            except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
                 self.conn = None
                 self.cursor = None
            except Exception as e:
                print(f"Error closing SQLite connection: {e}")
                self.conn = None
                self.cursor = None
        super().close()