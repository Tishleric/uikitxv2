"""
Migration: Add close PnL columns to positions table
Purpose: Support parallel calculation of close-based unrealized PnL
Date: 2025-08-03
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def migrate():
    """Add close PnL columns to positions table"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'trades.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(positions)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        columns_to_add = [
            ('fifo_unrealized_pnl_close', 'REAL DEFAULT 0'),
            ('lifo_unrealized_pnl_close', 'REAL DEFAULT 0')
        ]
        
        added_columns = []
        
        for col_name, col_def in columns_to_add:
            if col_name not in existing_columns:
                print(f"Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE positions ADD COLUMN {col_name} {col_def}")
                added_columns.append(col_name)
            else:
                print(f"Column {col_name} already exists, skipping")
        
        if added_columns:
            conn.commit()
            print(f"\nMigration completed successfully!")
            print(f"Added columns: {', '.join(added_columns)}")
            
            # Log migration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT INTO migration_history (migration_name, applied_at)
                VALUES (?, ?)
            """, ('010_add_close_pnl_columns', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
        else:
            print("\nNo changes needed - all columns already exist")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running migration: Add close PnL columns")
    print("-" * 50)
    
    success = migrate()
    
    if success:
        print("\n✓ Migration successful")
    else:
        print("\n✗ Migration failed")
        sys.exit(1)