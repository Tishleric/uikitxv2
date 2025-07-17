"""
Add vtexp column to spot_risk_raw table for storing time to expiry values.
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_vtexp_column():
    """Add vtexp column to spot_risk_raw table."""
    
    db_path = Path("data/output/spot_risk/spot_risk.db")
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(spot_risk_raw)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'vtexp' in columns:
            logger.info("vtexp column already exists in spot_risk_raw")
            return
            
        # Add vtexp column
        logger.info("Adding vtexp column to spot_risk_raw table...")
        cursor.execute("ALTER TABLE spot_risk_raw ADD COLUMN vtexp REAL")
        
        # Create index on vtexp for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_vtexp ON spot_risk_raw(vtexp)")
        
        conn.commit()
        logger.info("Successfully added vtexp column and index")
        
        # Update the schema.sql file content for reference
        schema_update = """
-- Added to spot_risk_raw table:
-- vtexp REAL,  -- Time to expiry in years from vtexp CSV mapping
"""
        logger.info("Schema update note:")
        print(schema_update)
        
    except Exception as e:
        logger.error(f"Error adding vtexp column: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_vtexp_column() 