"""
Checkpoint SQLite database to merge WAL file changes into main database.

This ensures all changes are written to the main .db file before copying.
"""

import sqlite3
import sys
from pathlib import Path

def checkpoint_database(db_path: str):
    """
    Checkpoint the database to merge WAL changes into main file.
    
    Args:
        db_path: Path to the SQLite database
    """
    db_path = Path(db_path)
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return False
        
    try:
        conn = sqlite3.connect(str(db_path))
        
        # Perform a full checkpoint
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.commit()
        conn.close()
        
        print(f"✓ Database checkpointed: {db_path}")
        
        # Check if WAL/SHM files still exist
        wal_path = db_path.with_suffix('.db-wal')
        shm_path = db_path.with_suffix('.db-shm')
        
        if wal_path.exists() and wal_path.stat().st_size == 0:
            print("  - WAL file is now empty")
        if not wal_path.exists():
            print("  - WAL file removed")
            
        return True
        
    except Exception as e:
        print(f"Error checkpointing database: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python checkpoint_database.py <database_path>")
        print("Example: python checkpoint_database.py data/trades.db")
        sys.exit(1)
        
    db_path = sys.argv[1]
    checkpoint_database(db_path)