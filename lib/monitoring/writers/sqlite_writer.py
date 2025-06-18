"""SQLite writer with batch processing for observatory data - Phase 5"""

import sqlite3
import os
import time
import threading
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

from ..queues import ObservatoryRecord
from ..circuit_breaker import CircuitBreaker, CircuitBreakerError


class SQLiteWriter:
    """
    Writes observatory data to SQLite database with WAL mode.
    
    Features:
    - Automatic schema creation
    - WAL mode for concurrent access
    - Transaction-based batch writes
    - Error handling and retries
    - Graceful shutdown
    """
    
    def __init__(self, db_path: str = "logs/observatory.db"):
        self.db_path = db_path
        self._ensure_directory()
        self._create_schema()
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        
    def _ensure_directory(self) -> None:
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
    def _create_schema(self) -> None:
        """Create database schema if not exists"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Create process_trace table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_trace (
                    ts           TEXT NOT NULL,      -- ISO format timestamp
                    process      TEXT NOT NULL,      -- module.function
                    status       TEXT NOT NULL,      -- OK|ERR
                    duration_ms  REAL NOT NULL,      -- Execution time in milliseconds
                    exception    TEXT,               -- Full traceback if ERR
                    thread_id    INTEGER NOT NULL DEFAULT 0,  -- Thread identifier
                    call_depth   INTEGER NOT NULL DEFAULT 0,  -- Stack depth  
                    start_ts_us  INTEGER NOT NULL DEFAULT 0,  -- Start timestamp in microseconds
                    cpu_delta    REAL,               -- CPU usage change in percentage
                    memory_delta_mb REAL,             -- Memory usage change in MB
                    PRIMARY KEY (ts, process)
                )
            """)
            
            # Create data_trace table for arguments and results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_trace (
                    ts          TEXT NOT NULL,       -- ISO format timestamp
                    process     TEXT NOT NULL,       -- module.function
                    data        TEXT NOT NULL,       -- Variable name (arg name or 'result')
                    data_type   TEXT NOT NULL,       -- INPUT|OUTPUT
                    data_value  TEXT NOT NULL,       -- Serialized value
                    status      TEXT NOT NULL,       -- Copied from process_trace
                    exception   TEXT,                -- Copied from process_trace
                    PRIMARY KEY (ts, process, data, data_type)
                )
            """)
            
            # Create optimized indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_process_ts ON process_trace(process, ts DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_process ON data_trace(process)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ts_window ON process_trace(ts)")
            
            # New indexes for parent-child relationship queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_thread_time ON process_trace(thread_id, start_ts_us)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_hierarchy ON process_trace(thread_id, call_depth, start_ts_us)")
            
            # Create view for parent-child relationships
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS parent_child_traces AS
                WITH potential_parents AS (
                    -- For each trace, find all potential parent traces
                    SELECT 
                        c.ts as child_ts,
                        c.process as child_process,
                        c.thread_id as child_thread,
                        c.call_depth as child_depth,
                        c.start_ts_us as child_start,
                        c.start_ts_us + (c.duration_ms * 1000) as child_end,
                        p.ts as parent_ts,
                        p.process as parent_process,
                        p.call_depth as parent_depth,
                        p.start_ts_us as parent_start,
                        p.start_ts_us + (p.duration_ms * 1000) as parent_end,
                        -- Rank by closest parent (deepest call depth that still contains child)
                        ROW_NUMBER() OVER (
                            PARTITION BY c.ts, c.process 
                            ORDER BY p.call_depth DESC
                        ) as parent_rank
                    FROM process_trace c
                    LEFT JOIN process_trace p ON (
                        c.thread_id = p.thread_id  -- Same thread
                        AND p.start_ts_us <= c.start_ts_us  -- Parent started before child
                        AND p.start_ts_us + (p.duration_ms * 1000) >= c.start_ts_us + (c.duration_ms * 1000)  -- Parent ended after child
                        AND p.call_depth < c.call_depth  -- Parent has lower call depth
                        AND NOT (c.ts = p.ts AND c.process = p.process)  -- Not the same trace
                    )
                )
                SELECT 
                    child_ts,
                    child_process,
                    parent_ts,
                    parent_process,
                    child_thread as thread_id,
                    child_depth - COALESCE(parent_depth, 0) as relative_depth
                FROM potential_parents 
                WHERE parent_rank = 1
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            # Set pragmas for performance
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY")
            yield conn
        finally:
            if conn:
                conn.close()
    
    def _ensure_json_string(self, value: Any) -> str:
        """Ensure value is a JSON string for SQLite storage"""
        if value is None:
            return "null"
        elif isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool)):
            return json.dumps(value)
        elif isinstance(value, (dict, list)):
            # This handles lazy serialized objects
            return json.dumps(value)
        else:
            # Fallback for any other type
            return json.dumps(str(value))
    
    def write_batch(self, records: List[ObservatoryRecord]) -> None:
        """
        Write a batch of records to the database.
        
        Uses a single transaction for efficiency.
        """
        if not records:
            return
            
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                try:
                    # Begin transaction
                    cursor.execute("BEGIN TRANSACTION")
                    
                    # Prepare process_trace data
                    process_data = []
                    data_trace_records = []
                    
                    for record in records:
                        # Process trace record
                        process_data.append((
                            record.ts,
                            record.process,
                            record.status,
                            record.duration_ms,
                            record.exception,
                            record.thread_id,
                            record.call_depth,
                            record.start_ts_us,
                            record.cpu_delta,
                            record.memory_delta_mb
                        ))
                        
                        # Data trace records for arguments
                        if record.args:
                            for i, arg_value in enumerate(record.args):
                                data_trace_records.append((
                                    record.ts,
                                    record.process,
                                    f"arg_{i}",
                                    "INPUT",
                                    self._ensure_json_string(arg_value),
                                    record.status,
                                    record.exception
                                ))
                        
                        # Data trace records for kwargs
                        if record.kwargs:
                            for key, value in record.kwargs.items():
                                data_trace_records.append((
                                    record.ts,
                                    record.process,
                                    key,
                                    "INPUT",
                                    self._ensure_json_string(value),
                                    record.status,
                                    record.exception
                                ))
                        
                        # Data trace record for result
                        if record.result is not None:
                            data_trace_records.append((
                                record.ts,
                                record.process,
                                "result",
                                "OUTPUT",
                                self._ensure_json_string(record.result),
                                record.status,
                                record.exception
                            ))
                    
                    # Bulk insert process traces
                    cursor.executemany(
                        "INSERT OR REPLACE INTO process_trace VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        process_data
                    )
                    
                    # Bulk insert data traces
                    if data_trace_records:
                        cursor.executemany(
                            "INSERT OR REPLACE INTO data_trace VALUES (?, ?, ?, ?, ?, ?, ?)",
                            data_trace_records
                        )
                    
                    # Commit transaction
                    conn.commit()
                    
                except Exception as e:
                    # Rollback on error
                    conn.rollback()
                    raise RuntimeError(f"Failed to write batch: {e}") from e
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get table sizes
            cursor.execute("SELECT COUNT(*) FROM process_trace")
            process_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM data_trace")
            data_count = cursor.fetchone()[0]
            
            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            # Get latest timestamp
            cursor.execute("SELECT MAX(ts) FROM process_trace")
            latest_ts = cursor.fetchone()[0]
            
            return {
                'process_trace_count': process_count,
                'data_trace_count': data_count,
                'db_size_bytes': db_size,
                'db_size_mb': round(db_size / (1024 * 1024), 2),
                'latest_timestamp': latest_ts,
                'db_path': self.db_path
            }
    
    def close(self) -> None:
        """Close any open connections"""
        # SQLite connections are closed after each operation
        # This method is here for API compatibility
        pass


class BatchWriter(threading.Thread):
    """
    Background thread that writes observatory records to SQLite.
    
    Features:
    - Batch writing for performance
    - WAL mode for concurrent reads
    - Automatic schema creation
    - Thread-safe operation
    - Circuit breaker for fault tolerance
    """
    
    def __init__(self, 
                 db_path: str,
                 queue,
                 batch_size: int = 100,
                 drain_interval: float = 0.1):
        super().__init__(daemon=True)
        self.db_path = db_path
        self.queue = queue
        self.batch_size = batch_size
        self.drain_interval = drain_interval
        self._stop_event = threading.Event()
        
        # Statistics
        self.total_written = 0
        self.total_errors = 0
        self.last_write_time = None
        self.last_error = None
        
        # Circuit breaker for database operations
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,  # Open after 3 failures
            timeout_seconds=30,   # Wait 30s before retry
            success_threshold=2   # Need 2 successes to close
        )
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with schema"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode
            
            # Create tables if they don't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS process_trace (
                    ts TEXT NOT NULL,
                    process TEXT NOT NULL,
                    process_group TEXT,
                    status TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    exception TEXT,
                    thread_id INTEGER NOT NULL DEFAULT 0,
                    call_depth INTEGER NOT NULL DEFAULT 0,
                    start_ts_us INTEGER NOT NULL DEFAULT 0,
                    cpu_delta REAL,
                    memory_delta_mb REAL,
                    PRIMARY KEY (ts, process, thread_id, start_ts_us)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_trace (
                    ts TEXT NOT NULL,
                    process TEXT NOT NULL,
                    data TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    data_value TEXT NOT NULL,
                    status TEXT NOT NULL,
                    exception TEXT,
                    thread_id INTEGER NOT NULL DEFAULT 0,
                    start_ts_us INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (ts, process, data, data_type, thread_id, start_ts_us)
                )
            """)
            
            # Create optimized indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_process_ts ON process_trace(process, ts DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ts_window ON process_trace(ts)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_data_process ON data_trace(process)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_thread_depth ON process_trace(thread_id, call_depth)")
            
            # Add view for parent-child relationships
            conn.execute("""
                CREATE VIEW IF NOT EXISTS parent_child_traces AS
                SELECT 
                    p1.ts as parent_ts,
                    p1.process as parent_process,
                    p2.ts as child_ts,
                    p2.process as child_process,
                    p2.call_depth - p1.call_depth as depth_diff,
                    (julianday(p2.ts) - julianday(p1.ts)) * 86400000 as time_diff_ms
                FROM process_trace p1
                JOIN process_trace p2 ON p1.thread_id = p2.thread_id
                WHERE p2.call_depth = p1.call_depth + 1
                  AND p2.start_ts_us > p1.start_ts_us
                  AND p2.start_ts_us < p1.start_ts_us + (p1.duration_ms * 1000)
                ORDER BY p1.ts DESC, p2.ts
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize database: {e}")
            self.last_error = str(e)
            raise
    
    def run(self):
        """Main writer loop"""
        print(f"[INFO] BatchWriter started for {self.db_path}")
        
        while not self._stop_event.is_set():
            try:
                # Drain queue
                batch = self.queue.drain(self.batch_size)
                
                if batch:
                    # Use circuit breaker for write operation
                    try:
                        self.circuit_breaker.call(self._write_batch, batch)
                    except CircuitBreakerError as e:
                        # Circuit is open, log and skip
                        print(f"[WARNING] {e}")
                        # Put records back in queue if possible
                        for record in batch:
                            try:
                                self.queue.put(record)
                            except:
                                pass  # Queue might be full
                    except Exception as e:
                        # Other errors are already handled by circuit breaker
                        self.last_error = str(e)
                        self.total_errors += 1
                
                # Sleep for drain interval
                time.sleep(self.drain_interval)
                
            except Exception as e:
                print(f"[ERROR] Writer thread error: {e}")
                self.last_error = str(e)
                self.total_errors += 1
                time.sleep(1)  # Back off on errors
        
        # Final flush on shutdown
        self._final_flush()
        print(f"[INFO] BatchWriter stopped. Total written: {self.total_written}")
    
    def _write_batch(self, batch: List[ObservatoryRecord]):
        """Write a batch of records to database (protected by circuit breaker)"""
        start = time.time()
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Start transaction
            conn.execute("BEGIN")
            
            # Process each record
            for record in batch:
                # Determine process_group (backwards compatibility)
                process_group = getattr(record, 'process_group', None)
                if not process_group:
                    # Auto-derive from module name
                    parts = record.process.split('.')
                    process_group = '.'.join(parts[:2]) if len(parts) > 1 else parts[0]
                
                # Insert process trace
                conn.execute("""
                    INSERT OR REPLACE INTO process_trace 
                    (ts, process, process_group, status, duration_ms, exception, 
                     thread_id, call_depth, start_ts_us, cpu_delta, memory_delta_mb)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.ts,
                    record.process,
                    process_group,
                    record.status,
                    record.duration_ms,
                    record.exception,
                    record.thread_id,
                    record.call_depth,
                    record.start_ts_us,
                    record.cpu_delta,
                    record.memory_delta_mb
                ))
                
                # Insert data traces for arguments
                if record.args:
                    for i, arg_value in enumerate(record.args):
                        # Handle lazy serialized objects
                        if isinstance(arg_value, dict) and arg_value.get('__lazy__'):
                            arg_str = json.dumps(arg_value)
                        else:
                            arg_str = str(arg_value)
                        
                        conn.execute("""
                            INSERT OR REPLACE INTO data_trace
                            (ts, process, data, data_type, data_value, status, exception,
                             thread_id, start_ts_us)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            record.ts,
                            record.process,
                            f"arg_{i}",  # Changed from arg{i} to arg_{i}
                            "INPUT",
                            arg_str,
                            record.status,
                            record.exception,
                            record.thread_id,
                            record.start_ts_us
                        ))
                
                # Insert data trace for kwargs
                if record.kwargs:
                    for key, value in record.kwargs.items():
                        # Handle lazy serialized objects
                        if isinstance(value, dict) and value.get('__lazy__'):
                            val_str = json.dumps(value)
                        else:
                            val_str = str(value)
                        
                        conn.execute("""
                            INSERT OR REPLACE INTO data_trace
                            (ts, process, data, data_type, data_value, status, exception,
                             thread_id, start_ts_us)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            record.ts,
                            record.process,
                            key,
                            "INPUT",
                            val_str,
                            record.status,
                            record.exception,
                            record.thread_id,
                            record.start_ts_us
                        ))
                
                # Insert data trace for result
                if record.result is not None:
                    # Handle lazy serialized objects
                    if isinstance(record.result, dict) and record.result.get('__lazy__'):
                        result_str = json.dumps(record.result)
                    else:
                        result_str = str(record.result)
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO data_trace
                        (ts, process, data, data_type, data_value, status, exception,
                         thread_id, start_ts_us)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.ts,
                        record.process,
                        "result",  # Changed from "return" to "result"
                        "OUTPUT",
                        result_str,
                        record.status,
                        record.exception,
                        record.thread_id,
                        record.start_ts_us
                    ))
            
            # Commit transaction
            conn.commit()
            
            # Update statistics
            self.total_written += len(batch)
            self.last_write_time = datetime.now()
            
            # Log slow writes
            duration = (time.time() - start) * 1000
            if duration > 50:  # More than 50ms is slow
                print(f"[WARNING] Slow write: {len(batch)} records in {duration:.1f}ms")
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise  # Let circuit breaker handle it
        finally:
            conn.close()
    
    def _final_flush(self):
        """Flush any remaining records on shutdown"""
        remaining = self.queue.drain(10000)  # Get everything
        if remaining:
            try:
                # Bypass circuit breaker for final flush
                self._write_batch(remaining)
                print(f"[INFO] Final flush wrote {len(remaining)} records")
            except Exception as e:
                print(f"[ERROR] Final flush failed: {e}")
    
    def stop(self):
        """Stop the writer thread gracefully"""
        self._stop_event.set()
        self.join(timeout=5)  # Wait up to 5 seconds
    
    def get_stats(self) -> Dict[str, Any]:
        """Get writer statistics"""
        try:
            # Get database size
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            
            # Get row counts
            conn = sqlite3.connect(self.db_path)
            process_count = conn.execute("SELECT COUNT(*) FROM process_trace").fetchone()[0]
            data_count = conn.execute("SELECT COUNT(*) FROM data_trace").fetchone()[0]
            conn.close()
            
        except Exception as e:
            db_size = 0
            process_count = 0
            data_count = 0
        
        return {
            'total_written': self.total_written,
            'total_errors': self.total_errors,
            'last_write_time': self.last_write_time.isoformat() if self.last_write_time else None,
            'last_error': self.last_error,
            'db_size_bytes': db_size,
            'process_trace_count': process_count,
            'data_trace_count': data_count,
            'circuit_breaker': self.circuit_breaker.get_stats()
        } 