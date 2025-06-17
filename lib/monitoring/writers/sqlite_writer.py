"""SQLite writer for observability data - Phase 5"""

import sqlite3
import threading
import time
import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from lib.monitoring.queues import ObservabilityQueue, ObservabilityRecord


class SQLiteWriter:
    """
    Writes observability data to SQLite database with WAL mode.
    
    Features:
    - Automatic schema creation
    - WAL mode for concurrent access
    - Transaction-based batch writes
    - Error handling and retries
    - Graceful shutdown
    """
    
    def __init__(self, db_path: str = "logs/observability.db"):
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
    
    def write_batch(self, records: List[ObservabilityRecord]) -> None:
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
                            record.start_ts_us
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
                        "INSERT OR REPLACE INTO process_trace VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
    Background thread that continuously drains the queue and writes to SQLite.
    
    Features:
    - 10Hz drain cycle (100ms)
    - Batch size up to 100 records
    - Graceful shutdown
    - Error recovery
    - Performance metrics
    """
    
    def __init__(self, 
                 queue: ObservabilityQueue,
                 db_path: str = "logs/observability.db",
                 batch_size: int = 100,
                 drain_interval: float = 0.1):  # 10Hz
        super().__init__(daemon=True)
        self.queue = queue
        self.writer = SQLiteWriter(db_path)
        self.batch_size = batch_size
        self.drain_interval = drain_interval
        
        # Control flags
        self._stop_event = threading.Event()
        self._error_count = 0
        self._total_written = 0
        self._start_time = time.time()
        
        # Metrics
        self.metrics = {
            'batches_written': 0,
            'records_written': 0,
            'errors': 0,
            'last_error': None,
            'last_write_time': None,
            'uptime_seconds': 0
        }
        self._metrics_lock = threading.Lock()
    
    def run(self) -> None:
        """Main writer loop"""
        print(f"[BatchWriter] Starting writer thread (batch_size={self.batch_size}, interval={self.drain_interval}s)")
        
        while not self._stop_event.is_set():
            try:
                # Drain records from queue
                records = self.queue.drain(max_items=self.batch_size)
                
                if records:
                    # Write batch to database
                    start_write = time.time()
                    self.writer.write_batch(records)
                    write_duration = time.time() - start_write
                    
                    # Update metrics
                    with self._metrics_lock:
                        self.metrics['batches_written'] += 1
                        self.metrics['records_written'] += len(records)
                        self.metrics['last_write_time'] = datetime.now().isoformat()
                        self._total_written += len(records)
                    
                    # Log if write was slow
                    if write_duration > 0.05:  # 50ms warning threshold
                        print(f"[BatchWriter] Slow write: {len(records)} records in {write_duration:.3f}s")
                
                # Sleep for drain interval
                time.sleep(self.drain_interval)
                
            except Exception as e:
                # Handle errors gracefully
                with self._metrics_lock:
                    self.metrics['errors'] += 1
                    self.metrics['last_error'] = str(e)
                    self._error_count += 1
                
                print(f"[BatchWriter] Error in writer loop: {e}")
                
                # Exponential backoff on errors
                sleep_time = min(2 ** self._error_count, 30)  # Max 30 seconds
                time.sleep(sleep_time)
        
        print(f"[BatchWriter] Writer thread stopped. Total written: {self._total_written}")
    
    def stop(self, timeout: float = 5.0) -> None:
        """Stop the writer thread gracefully"""
        print("[BatchWriter] Stopping writer thread...")
        self._stop_event.set()
        
        # Wait for thread to finish with timeout
        self.join(timeout)
        
        if self.is_alive():
            print("[BatchWriter] Warning: Writer thread did not stop gracefully")
        else:
            # Final drain to ensure no data loss
            final_records = self.queue.drain(max_items=1000)
            if final_records:
                print(f"[BatchWriter] Final drain: writing {len(final_records)} records")
                self.writer.write_batch(final_records)
        
        # Close writer
        self.writer.close()
        print("[BatchWriter] Writer thread stopped")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get writer metrics"""
        with self._metrics_lock:
            metrics = self.metrics.copy()
            metrics['uptime_seconds'] = time.time() - self._start_time
            metrics['records_per_second'] = (
                self._total_written / metrics['uptime_seconds'] 
                if metrics['uptime_seconds'] > 0 else 0
            )
            
            # Add database stats
            try:
                metrics['database'] = self.writer.get_stats()
            except Exception as e:
                metrics['database'] = {'error': str(e)}
            
            # Add queue stats
            metrics['queue'] = self.queue.get_queue_stats()
            
            return metrics 