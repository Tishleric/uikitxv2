#!/usr/bin/env python3
"""
Migration script to add closed_quantity column to positions table.
This column tracks the quantity that was closed (reduced to zero) today.
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_closed_quantity_column(db_path: str):
    """Add closed_quantity column to positions table if it doesn't exist."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(positions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'closed_quantity' in column_names:
            logger.info(f"Column 'closed_quantity' already exists in {db_path}")
            return
        
        # Add the column
        cursor.execute("""
            ALTER TABLE positions 
            ADD COLUMN closed_quantity REAL NOT NULL DEFAULT 0
        """)
        
        conn.commit()
        logger.info(f"Successfully added 'closed_quantity' column to {db_path}")
        
    except Exception as e:
        logger.error(f"Error adding column to {db_path}: {e}")
        raise
    finally:
        conn.close()

def main():
    """Run migration on all P&L tracking databases."""
    db_paths = [
        "data/output/pnl/pnl_tracker.db",
        # Add any other database paths here
    ]
    
    for db_path in db_paths:
        if Path(db_path).exists():
            logger.info(f"Processing database: {db_path}")
            add_closed_quantity_column(db_path)
        else:
            logger.warning(f"Database not found: {db_path}")

if __name__ == "__main__":
    main() 