#!/usr/bin/env python3
"""Reset px_settle column to NULL."""
import sqlite3
from pathlib import Path

def reset_px_settle():
    project_root = Path(__file__).parent.parent.parent
    pnl_db_path = project_root / "data/output/pnl/pnl_tracker.db"
    
    conn = sqlite3.connect(pnl_db_path)
    cursor = conn.cursor()
    
    print("Resetting px_settle column to NULL...")
    cursor.execute("UPDATE FULLPNL SET px_settle = NULL")
    conn.commit()
    
    print(f"Reset {cursor.rowcount} rows")
    conn.close()

if __name__ == "__main__":
    reset_px_settle() 