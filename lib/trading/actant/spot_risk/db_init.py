"""
Database initialization for Spot Risk data storage.

This module creates and initializes the SQLite database for storing
spot risk raw data and calculated Greeks.
"""

import sqlite3
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports when running directly
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from lib.monitoring.decorators import monitor


@monitor()
def initialize_database(db_path: Optional[str] = None) -> str:
    """
    Initialize the spot risk database with schema.
    
    Args:
        db_path: Optional path to database file. 
                 Defaults to data/output/spot_risk/spot_risk.db
    
    Returns:
        str: Path to created database
    """
    # Determine database path
    if db_path is None:
        # Use project structure
        project_root = Path(__file__).parent.parent.parent.parent.parent  # Up to project root
        db_dir = project_root / "data" / "output" / "spot_risk"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(db_dir / "spot_risk.db")
    
    # Read schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Create database and execute schema
    conn = sqlite3.connect(db_path)
    try:
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Execute schema
        conn.executescript(schema_sql)
        
        # Verify tables were created
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Database initialized at: {db_path}")
        print(f"Created tables: {', '.join(tables)}")
        
        conn.commit()
    finally:
        conn.close()
    
    return db_path


@monitor()
def verify_schema(db_path: str) -> dict:
    """
    Verify the database schema is correctly set up.
    
    Args:
        db_path: Path to database file
        
    Returns:
        dict: Schema information
    """
    conn = sqlite3.connect(db_path)
    try:
        # Get table info
        tables = {}
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        for (table_name,) in cursor.fetchall():
            # Get column info for each table
            col_cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for row in col_cursor:
                columns.append({
                    'name': row[1],
                    'type': row[2],
                    'nullable': not row[3],
                    'primary_key': bool(row[5])
                })
            tables[table_name] = columns
        
        # Get indexes
        index_cursor = conn.execute("""
            SELECT name, tbl_name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        indexes = list(index_cursor.fetchall())
        
        return {
            'tables': tables,
            'indexes': indexes,
            'table_count': len(tables),
            'index_count': len(indexes)
        }
    finally:
        conn.close()


if __name__ == "__main__":
    # Initialize database
    db_path = initialize_database()
    
    # Verify schema
    schema_info = verify_schema(db_path)
    
    print("\n=== Schema Verification ===")
    print(f"Tables: {schema_info['table_count']}")
    print(f"Indexes: {schema_info['index_count']}")
    
    print("\nTable Details:")
    for table, columns in schema_info['tables'].items():
        print(f"\n{table}:")
        for col in columns:
            pk = " (PK)" if col['primary_key'] else ""
            nullable = " NULL" if col['nullable'] else " NOT NULL"
            print(f"  - {col['name']}: {col['type']}{nullable}{pk}") 