"""Data models and services for Observatory Dashboard"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import pandas as pd

from .constants import OBSERVATORY_DB_PATH, DEFAULT_PAGE_SIZE


class ObservatoryDataService:
    """Service for querying observatory data from SQLite database"""
    
    def __init__(self, db_path: str = OBSERVATORY_DB_PATH):
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure the database file exists"""
        if not os.path.exists(self.db_path):
            # Create empty database with schema if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_trace (
                    ts           TEXT NOT NULL,
                    process      TEXT NOT NULL,
                    status       TEXT NOT NULL,
                    duration_ms  REAL NOT NULL,
                    exception    TEXT,
                    thread_id    TEXT,
                    call_depth   INTEGER,
                    start_ts_us  INTEGER,
                    PRIMARY KEY (ts, process)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_trace (
                    ts          TEXT NOT NULL,
                    process     TEXT NOT NULL,
                    data        TEXT NOT NULL,
                    data_type   TEXT NOT NULL,
                    data_value  TEXT NOT NULL,
                    status      TEXT NOT NULL,
                    exception   TEXT,
                    PRIMARY KEY (ts, process, data, data_type)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_process_ts ON process_trace(process, ts DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_process ON data_trace(process)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ts_window ON process_trace(ts)")
            
            conn.commit()
            conn.close()
        else:
            # Ensure schema exists even if database file exists
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if tables exist
                tables = cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                table_names = [t[0] for t in tables]
                
                if 'process_trace' not in table_names or 'data_trace' not in table_names:
                    # Create missing tables
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS process_trace (
                            ts           TEXT NOT NULL,
                            process      TEXT NOT NULL,
                            status       TEXT NOT NULL,
                            duration_ms  REAL NOT NULL,
                            exception    TEXT,
                            thread_id    TEXT,
                            call_depth   INTEGER,
                            start_ts_us  INTEGER,
                            PRIMARY KEY (ts, process)
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS data_trace (
                            ts          TEXT NOT NULL,
                            process     TEXT NOT NULL,
                            data        TEXT NOT NULL,
                            data_type   TEXT NOT NULL,
                            data_value  TEXT NOT NULL,
                            status      TEXT NOT NULL,
                            exception   TEXT,
                            PRIMARY KEY (ts, process, data, data_type)
                        )
                    """)
                    
                    # Create indexes
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_process_ts ON process_trace(process, ts DESC)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_process ON data_trace(process)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ts_window ON process_trace(ts)")
                    
                    conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        finally:
            if conn:
                conn.close()
    
    def get_trace_data(self, page: int = 1, page_size: int = 100) -> pd.DataFrame:
        """Get trace data with pagination"""
        with self._get_connection() as conn:
            offset = (page - 1) * page_size
            
            # Join data_trace with process_trace to get process_group and duration_ms
            query = """
                SELECT 
                    dt.ts,
                    CASE 
                        WHEN pt.process_group LIKE '%.%' AND 
                             SUBSTR(pt.process_group, INSTR(pt.process_group, '.') + 1) GLOB '[a-z]*'
                        THEN SUBSTR(pt.process_group, 1, INSTR(pt.process_group, '.') - 1)
                        ELSE pt.process_group
                    END as process_group,
                    CASE 
                        WHEN pt.process_group IS NOT NULL AND pt.process != pt.process_group
                        THEN 
                            CASE 
                                WHEN pt.process = pt.process_group || '.' || SUBSTR(pt.process, LENGTH(pt.process_group) + 2)
                                THEN SUBSTR(pt.process, LENGTH(pt.process_group) + 2)
                                ELSE pt.process
                            END
                        ELSE pt.process
                    END as process,
                    dt.data,
                    dt.data_type,
                    dt.data_value,
                    pt.duration_ms,
                    dt.status,
                    dt.exception
                FROM data_trace dt
                INNER JOIN process_trace pt ON dt.ts = pt.ts AND dt.process = pt.process
                ORDER BY dt.ts DESC
                LIMIT ? OFFSET ?
            """
            
            df = pd.read_sql_query(query, conn, params=(page_size, offset))
            
            if df.empty:
                return df
                
            # Format timestamp
            df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%Y-%m-%d %H:%M:%S.%f').str[:-3]
            
            # Format duration_ms to show as milliseconds with 1 decimal place
            if 'duration_ms' in df.columns:
                df['duration_ms'] = df['duration_ms'].apply(lambda x: f"{x:.1f} ms" if pd.notna(x) else "")
            
            return df
    
    def get_process_metrics(self, hours: int = 1) -> pd.DataFrame:
        """Get aggregated metrics by process for the last N hours"""
        with self._get_connection() as conn:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            query = """
                SELECT 
                    process,
                    COUNT(*) as call_count,
                    AVG(duration_ms) as avg_duration_ms,
                    MIN(duration_ms) as min_duration_ms,
                    MAX(duration_ms) as max_duration_ms,
                    SUM(CASE WHEN status = 'ERR' THEN 1 ELSE 0 END) as error_count,
                    ROUND(100.0 * SUM(CASE WHEN status = 'ERR' THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate
                FROM process_trace
                WHERE ts >= ?
                GROUP BY process
                ORDER BY call_count DESC
            """
            
            return pd.read_sql_query(query, conn, params=[cutoff_time])
    
    def get_recent_errors(self, limit: int = 50) -> pd.DataFrame:
        """Get recent error traces"""
        with self._get_connection() as conn:
            query = """
                SELECT 
                    ts as timestamp,
                    process,
                    duration_ms,
                    exception
                FROM process_trace
                WHERE status = 'ERR'
                ORDER BY ts DESC
                LIMIT ?
            """
            
            return pd.read_sql_query(query, conn, params=[limit])
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        with self._get_connection() as conn:
            stats = {}
            
            # Total traces
            stats["total_traces"] = conn.execute(
                "SELECT COUNT(*) FROM process_trace"
            ).fetchone()[0]
            
            # Total data points
            stats["total_data_points"] = conn.execute(
                "SELECT COUNT(*) FROM data_trace"
            ).fetchone()[0]
            
            # Recent activity (last 5 minutes)
            recent_cutoff = (datetime.now() - timedelta(minutes=5)).isoformat()
            stats["recent_traces"] = conn.execute(
                "SELECT COUNT(*) FROM process_trace WHERE ts >= ?",
                [recent_cutoff]
            ).fetchone()[0]
            
            # Error rate (last hour)
            hour_cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'ERR' THEN 1 ELSE 0 END) as errors
                FROM process_trace
                WHERE ts >= ?
                """,
                [hour_cutoff]
            )
            row = cursor.fetchone()
            total = row[0] or 1  # Avoid division by zero
            errors = row[1] or 0
            stats["error_rate"] = round(100.0 * errors / total, 2)
            
            # Database size
            if os.path.exists(self.db_path):
                stats["db_size_mb"] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            else:
                stats["db_size_mb"] = 0
            
            return stats
    
    def get_unique_process_groups(self) -> List[str]:
        """Get unique process groups from the data"""
        with self._get_connection() as conn:
            # Extract the proper process group from potentially incorrect values
            query = """
                SELECT DISTINCT 
                    CASE 
                        WHEN process_group LIKE '%.%' AND 
                             SUBSTR(process_group, INSTR(process_group, '.') + 1) GLOB '[a-z]*'
                        THEN SUBSTR(process_group, 1, INSTR(process_group, '.') - 1)
                        ELSE process_group
                    END as clean_process_group
                FROM process_trace
                WHERE process_group IS NOT NULL
                ORDER BY clean_process_group
            """
            
            result = conn.execute(query).fetchall()
            return [row[0] for row in result if row[0]]
    
    def filter_by_group(self, group: str) -> pd.DataFrame:
        """Filter data by process group"""
        with self._get_connection() as conn:
            if group == "all":
                # Show all data
                query = """
                    SELECT 
                        dt.ts,
                        CASE 
                            WHEN pt.process_group LIKE '%.%' AND 
                                 SUBSTR(pt.process_group, INSTR(pt.process_group, '.') + 1) GLOB '[a-z]*'
                            THEN SUBSTR(pt.process_group, 1, INSTR(pt.process_group, '.') - 1)
                            ELSE pt.process_group
                        END as process_group,
                        CASE 
                            WHEN pt.process_group IS NOT NULL AND pt.process != pt.process_group
                            THEN 
                                CASE 
                                    WHEN pt.process = pt.process_group || '.' || SUBSTR(pt.process, LENGTH(pt.process_group) + 2)
                                    THEN SUBSTR(pt.process, LENGTH(pt.process_group) + 2)
                                    ELSE pt.process
                                END
                            ELSE pt.process
                        END as process,
                        dt.data,
                        dt.data_type,
                        dt.data_value,
                        pt.duration_ms,
                        dt.status,
                        dt.exception
                    FROM data_trace dt
                    INNER JOIN process_trace pt ON dt.ts = pt.ts AND dt.process = pt.process
                    ORDER BY dt.ts DESC
                    LIMIT 1000
                """
                df = pd.read_sql_query(query, conn)
            else:
                # Filter by specific process group
                query = """
                    SELECT 
                        dt.ts,
                        CASE 
                            WHEN pt.process_group LIKE '%.%' AND 
                                 SUBSTR(pt.process_group, INSTR(pt.process_group, '.') + 1) GLOB '[a-z]*'
                            THEN SUBSTR(pt.process_group, 1, INSTR(pt.process_group, '.') - 1)
                            ELSE pt.process_group
                        END as process_group,
                        CASE 
                            WHEN pt.process_group IS NOT NULL AND pt.process != pt.process_group
                            THEN 
                                CASE 
                                    WHEN pt.process = pt.process_group || '.' || SUBSTR(pt.process, LENGTH(pt.process_group) + 2)
                                    THEN SUBSTR(pt.process, LENGTH(pt.process_group) + 2)
                                    ELSE pt.process
                                END
                            ELSE pt.process
                        END as process,
                        dt.data,
                        dt.data_type,
                        dt.data_value,
                        pt.duration_ms,
                        dt.status,
                        dt.exception
                    FROM data_trace dt
                    INNER JOIN process_trace pt ON dt.ts = pt.ts AND dt.process = pt.process
                    WHERE CASE 
                        WHEN pt.process_group LIKE '%.%' AND 
                             SUBSTR(pt.process_group, INSTR(pt.process_group, '.') + 1) GLOB '[a-z]*'
                        THEN SUBSTR(pt.process_group, 1, INSTR(pt.process_group, '.') - 1)
                        ELSE pt.process_group
                    END = ?
                    ORDER BY dt.ts DESC
                    LIMIT 1000
                """
                df = pd.read_sql_query(query, conn, params=(group,))
            
            if df.empty:
                return df
                
            # Format timestamp
            df['ts'] = pd.to_datetime(df['ts']).dt.strftime('%Y-%m-%d %H:%M:%S.%f').str[:-3]
            
            # Format duration_ms to show as milliseconds with 1 decimal place
            if 'duration_ms' in df.columns:
                df['duration_ms'] = df['duration_ms'].apply(lambda x: f"{x:.1f} ms" if pd.notna(x) else "")
            
            return df


class MetricsAggregator:
    """Aggregates metrics for dashboard visualizations"""
    
    def __init__(self, data_service: ObservatoryDataService):
        self.data_service = data_service
    
    def get_performance_timeline(self, process: str, hours: int = 1) -> pd.DataFrame:
        """Get performance metrics over time for a specific process"""
        with self.data_service._get_connection() as conn:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            query = """
                SELECT 
                    datetime(ts, 'unixepoch', 'localtime', 'start of minute') as minute,
                    COUNT(*) as calls,
                    AVG(duration_ms) as avg_duration,
                    MAX(duration_ms) as max_duration,
                    SUM(CASE WHEN status = 'ERR' THEN 1 ELSE 0 END) as errors
                FROM process_trace
                WHERE process = ? AND ts >= ?
                GROUP BY minute
                ORDER BY minute
            """
            
            return pd.read_sql_query(query, conn, params=[process, cutoff_time])
    
    def get_top_slow_functions(self, limit: int = 10) -> pd.DataFrame:
        """Get slowest functions by average duration"""
        with self.data_service._get_connection() as conn:
            query = """
                SELECT 
                    process,
                    COUNT(*) as call_count,
                    AVG(duration_ms) as avg_duration_ms,
                    MAX(duration_ms) as max_duration_ms
                FROM process_trace
                WHERE ts >= datetime('now', '-1 hour')
                GROUP BY process
                HAVING call_count > 10  -- Only show functions called more than 10 times
                ORDER BY avg_duration_ms DESC
                LIMIT ?
            """
            
            return pd.read_sql_query(query, conn, params=[limit])


class TraceAnalyzer:
    """Analyzes traces for patterns and relationships"""
    
    def __init__(self, data_service: ObservatoryDataService):
        self.data_service = data_service
    
    def get_parent_child_traces(self, parent_process: str) -> pd.DataFrame:
        """Get child traces for a given parent process"""
        with self.data_service._get_connection() as conn:
            query = """
                SELECT 
                    parent_ts,
                    parent_process,
                    child_ts,
                    child_process,
                    depth_diff,
                    time_diff_ms
                FROM parent_child_traces
                WHERE parent_process = ?
                ORDER BY child_ts
            """
            
            return pd.read_sql_query(query, conn, params=[parent_process])
    
    def detect_stale_processes(self, expected_interval_seconds: int = 60) -> List[Dict[str, Any]]:
        """Detect processes that haven't run within expected interval"""
        with self.data_service._get_connection() as conn:
            # Get last execution time for each process
            query = """
                SELECT 
                    process,
                    MAX(ts) as last_execution,
                    julianday('now') - julianday(MAX(ts)) as days_since_last
                FROM process_trace
                GROUP BY process
                HAVING days_since_last * 86400 > ?
                ORDER BY days_since_last DESC
            """
            
            cursor = conn.execute(query, [expected_interval_seconds])
            
            stale_processes = []
            for row in cursor:
                stale_processes.append({
                    "process": row[0],
                    "last_execution": row[1],
                    "seconds_since_last": int(row[2] * 86400)
                })
            
            return stale_processes 