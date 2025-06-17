"""Simple, robust retention management for observability data.

This module implements a dead-simple retention strategy:
- Delete records older than retention period
- Let SQLite handle fragmentation naturally
- Use WAL mode for better concurrency
- No VACUUM operations (avoid spikes)
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Tuple


class RetentionManager:
    """Manages data retention for observability database.
    
    Philosophy: Keep it simple. Delete old data, let SQLite handle the rest.
    After 6 hours, the database reaches steady state where deletions = insertions.
    
    Attributes:
        db_path: Path to SQLite database
        retention_hours: Hours of data to retain (default: 6)
    """
    
    def __init__(self, db_path: str, retention_hours: int = 6):
        """Initialize retention manager.
        
        Args:
            db_path: Path to SQLite database file
            retention_hours: Number of hours of data to keep
        """
        self.db_path = db_path
        self.retention_hours = retention_hours
        self._ensure_wal_mode()
    
    def _ensure_wal_mode(self) -> None:
        """Ensure database is in WAL mode for better concurrency.
        
        WAL mode benefits:
        - Readers don't block writers
        - Writers don't block readers  
        - Better crash recovery
        - Automatic checkpointing
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
        except Exception as e:
            # Non-critical - database works fine without WAL
            print(f"[RETENTION] Warning: Could not enable WAL mode: {e}")
    
    def cleanup_old_records(self) -> Tuple[int, int]:
        """Delete records older than retention period.
        
        This is the core retention logic. Simply deletes old records
        and returns counts. SQLite handles free page management.
        
        Returns:
            Tuple of (process_records_deleted, data_records_deleted)
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        cutoff_str = cutoff.isoformat()
        
        process_deleted = 0
        data_deleted = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete old process traces
                cursor = conn.execute(
                    "DELETE FROM process_trace WHERE ts < ?",
                    (cutoff_str,)
                )
                process_deleted = cursor.rowcount
                
                # Delete old data traces  
                cursor = conn.execute(
                    "DELETE FROM data_trace WHERE ts < ?", 
                    (cutoff_str,)
                )
                data_deleted = cursor.rowcount
                
                # Commit is automatic with context manager
                
        except sqlite3.OperationalError as e:
            # Common in high-load scenarios
            if "database is locked" in str(e):
                # This is expected occasionally - let caller retry
                raise
            else:
                # Unexpected operational error
                print(f"[RETENTION] Operational error: {e}")
                raise
                
        except sqlite3.Error as e:
            # Any other database error
            print(f"[RETENTION] Database error: {e}")
            raise
            
        return process_deleted, data_deleted
    
    def get_retention_stats(self) -> dict:
        """Get statistics about current retention state.
        
        Returns:
            Dict with:
            - total_process_records: Total records in process_trace
            - total_data_records: Total records in data_trace
            - oldest_process_ts: Oldest timestamp in process_trace
            - oldest_data_ts: Oldest timestamp in data_trace
            - retention_hours: Configured retention period
            - database_size_mb: Current database file size in MB
        """
        stats = {
            "total_process_records": 0,
            "total_data_records": 0,
            "oldest_process_ts": None,
            "oldest_data_ts": None,
            "retention_hours": self.retention_hours,
            "database_size_mb": 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get record counts
                stats["total_process_records"] = conn.execute(
                    "SELECT COUNT(*) FROM process_trace"
                ).fetchone()[0]
                
                stats["total_data_records"] = conn.execute(
                    "SELECT COUNT(*) FROM data_trace"
                ).fetchone()[0]
                
                # Get oldest timestamps
                oldest_process = conn.execute(
                    "SELECT MIN(ts) FROM process_trace"
                ).fetchone()[0]
                if oldest_process:
                    stats["oldest_process_ts"] = oldest_process
                
                oldest_data = conn.execute(
                    "SELECT MIN(ts) FROM data_trace"
                ).fetchone()[0]
                if oldest_data:
                    stats["oldest_data_ts"] = oldest_data
                
                # Get database size
                page_count = conn.execute("PRAGMA page_count").fetchone()[0]
                page_size = conn.execute("PRAGMA page_size").fetchone()[0]
                stats["database_size_mb"] = (page_count * page_size) / (1024 * 1024)
                
        except sqlite3.Error as e:
            print(f"[RETENTION] Error getting stats: {e}")
            # Return partial stats rather than failing
            
        return stats
    
    def estimate_steady_state_size(self) -> float:
        """Estimate database size at steady state.
        
        Based on current insertion rate and retention period,
        estimate the steady-state database size.
        
        Returns:
            Estimated size in MB
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get recent insertion rate (last 5 minutes)
                five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
                
                recent_count = conn.execute(
                    "SELECT COUNT(*) FROM process_trace WHERE ts > ?",
                    (five_min_ago,)
                ).fetchone()[0]
                
                # Calculate rate per hour
                rate_per_hour = recent_count * 12  # 5 min * 12 = 1 hour
                
                # Estimate total records at steady state
                total_records = rate_per_hour * self.retention_hours
                
                # Estimate size (rough: 500 bytes per record)
                estimated_mb = (total_records * 500) / (1024 * 1024)
                
                # Add 15% overhead for SQLite structures and fragmentation
                return estimated_mb * 1.15
                
        except sqlite3.Error:
            return 0.0 