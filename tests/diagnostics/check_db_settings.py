"""
Quick Database Settings Check
============================
Check current SQLite settings that might affect performance.
Read-only - no modifications.
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_settings(db_path="trades.db"):
    """Check database settings related to performance"""
    
    logger.info(f"Checking database settings for: {db_path}")
    logger.info("="*50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Important settings for performance
    settings = [
        ('journal_mode', 'Should be WAL for concurrent access'),
        ('synchronous', '2=FULL (slow), 1=NORMAL (faster), 0=OFF (unsafe)'),
        ('busy_timeout', 'Milliseconds to wait for locks'),
        ('cache_size', 'Number of pages in cache (negative = KB)'),
        ('page_size', 'Bytes per page (4096 or 8192 recommended)'),
        ('wal_autocheckpoint', 'Pages before auto-checkpoint (default 1000)'),
        ('temp_store', '0=DEFAULT, 1=FILE, 2=MEMORY'),
        ('mmap_size', 'Memory-mapped I/O size (0=disabled)'),
    ]
    
    for setting, description in settings:
        try:
            cursor.execute(f"PRAGMA {setting}")
            value = cursor.fetchone()
            value = value[0] if value else "N/A"
            logger.info(f"{setting:20s}: {value:15s} ({description})")
        except Exception as e:
            logger.error(f"Error checking {setting}: {e}")
    
    # Check table info for pricing
    logger.info("\nPricing table structure:")
    cursor.execute("PRAGMA table_info(pricing)")
    columns = cursor.fetchall()
    for col in columns:
        logger.info(f"  {col[1]:15s} {col[2]:10s} {'NOT NULL' if col[3] else 'NULL':8s} {'PK' if col[5] else ''}")
    
    # Check indexes
    logger.info("\nIndexes on pricing table:")
    cursor.execute("PRAGMA index_list(pricing)")
    indexes = cursor.fetchall()
    for idx in indexes:
        logger.info(f"  {idx[1]:30s} {'UNIQUE' if idx[2] else 'NON-UNIQUE'}")
        cursor.execute(f"PRAGMA index_info({idx[1]})")
        idx_cols = cursor.fetchall()
        for col in idx_cols:
            logger.info(f"    - Column: {col[2]}")
    
    # Check current size
    cursor.execute("SELECT COUNT(*) FROM pricing")
    count = cursor.fetchone()[0]
    logger.info(f"\nPricing table rows: {count}")
    
    # Performance recommendations
    logger.info("\n" + "="*50)
    logger.info("PERFORMANCE RECOMMENDATIONS:")
    
    cursor.execute("PRAGMA journal_mode")
    journal = cursor.fetchone()[0]
    if journal != 'wal':
        logger.warning("1. Enable WAL mode: PRAGMA journal_mode=WAL")
        logger.warning("   This allows concurrent readers during writes")
    
    cursor.execute("PRAGMA synchronous")
    sync = cursor.fetchone()[0]
    if sync == 2:
        logger.warning("2. Consider PRAGMA synchronous=NORMAL (currently FULL)")
        logger.warning("   This can significantly speed up commits")
    
    conn.close()

if __name__ == "__main__":
    check_database_settings()