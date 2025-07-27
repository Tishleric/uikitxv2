"""
Database utilities for thread-safe operations

Purpose: Provide thread-safe database operations to prevent race conditions
when multiple watchers access the same database
"""

import sqlite3
import threading
import time
import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

# Global lock for database operations
_db_lock = threading.Lock()

# Retry configuration
MAX_RETRIES = 5
RETRY_DELAY = 0.1  # seconds


@contextmanager
def get_db_connection(db_path: str, timeout: float = 30.0):
    """
    Thread-safe context manager for database connections.
    
    Args:
        db_path: Path to the database
        timeout: Maximum time to wait for database lock
        
    Yields:
        sqlite3.Connection: Database connection
    """
    conn = None
    try:
        # Set a longer timeout to handle concurrent access
        conn = sqlite3.connect(db_path, timeout=timeout)
        # Enable Write-Ahead Logging for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        # Set synchronous to NORMAL for better performance
        conn.execute("PRAGMA synchronous=NORMAL")
        yield conn
    finally:
        if conn:
            conn.close()


def execute_with_retry(conn: sqlite3.Connection, query: str, params: tuple = None, 
                      max_retries: int = MAX_RETRIES) -> Optional[sqlite3.Cursor]:
    """
    Execute a query with retry logic for handling database locks.
    
    Args:
        conn: Database connection
        query: SQL query to execute
        params: Query parameters
        max_retries: Maximum number of retry attempts
        
    Returns:
        Cursor object or None if failed
    """
    for attempt in range(max_retries):
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"Database operation failed: {e}")
                raise
    return None


def is_file_processed_safe(db_path: str, file_path: str, last_modified: float) -> bool:
    """
    Thread-safe check if a file has been processed.
    
    Args:
        db_path: Path to database
        file_path: Path to the file
        last_modified: File's last modified timestamp
        
    Returns:
        True if file has been processed, False otherwise
    """
    with _db_lock:
        try:
            with get_db_connection(db_path) as conn:
                cursor = execute_with_retry(
                    conn,
                    "SELECT 1 FROM processed_files WHERE file_path = ? AND last_modified = ?",
                    (file_path, last_modified)
                )
                return cursor.fetchone() is not None if cursor else False
        except Exception as e:
            logger.error(f"Error checking processed file: {e}")
            return False


def mark_file_processed_safe(db_path: str, file_path: str, processed_at: str, 
                           count: int, last_modified: float) -> bool:
    """
    Thread-safe marking of a file as processed.
    
    Args:
        db_path: Path to database
        file_path: Path to the file
        processed_at: Timestamp when processed
        count: Number of items processed
        last_modified: File's last modified timestamp
        
    Returns:
        True if successful, False otherwise
    """
    with _db_lock:
        try:
            with get_db_connection(db_path) as conn:
                cursor = execute_with_retry(
                    conn,
                    """
                    INSERT OR REPLACE INTO processed_files 
                    (file_path, processed_at, trade_count, last_modified)
                    VALUES (?, ?, ?, ?)
                    """,
                    (file_path, processed_at, count, last_modified)
                )
                if cursor:
                    conn.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error marking file as processed: {e}")
            return False


def update_price_safe(db_path: str, symbol: str, price: float, timestamp: str) -> bool:
    """
    Thread-safe price update.
    
    Args:
        db_path: Path to database
        symbol: Symbol to update
        price: New price value
        timestamp: Price timestamp
        
    Returns:
        True if successful, False otherwise
    """
    with _db_lock:
        try:
            with get_db_connection(db_path) as conn:
                cursor = execute_with_retry(
                    conn,
                    """
                    INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
                    VALUES (?, 'now', ?, ?)
                    """,
                    (symbol, price, timestamp)
                )
                if cursor:
                    conn.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating price for {symbol}: {e}")
            return False 