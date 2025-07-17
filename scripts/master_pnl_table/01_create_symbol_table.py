#!/usr/bin/env python3
"""
01_create_symbol_table.py

Creates the FULLPNL table with just the symbol column from positions table.
This is the first step in building the master P&L table incrementally.
"""

import sqlite3
import os
from datetime import datetime


def create_fullpnl_table():
    """Create FULLPNL table with symbols from positions table."""
    
    # Database path - go up two levels from scripts/master_pnl_table/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    db_path = os.path.join(project_root, "data", "output", "pnl", "pnl_tracker.db")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, check if positions table has any data
        cursor.execute("SELECT COUNT(*) FROM positions")
        position_count = cursor.fetchone()[0]
        print(f"\nPositions table has {position_count} records")
        
        if position_count == 0:
            print("WARNING: Positions table is empty!")
            print("\nTrying to populate from cto_trades if available...")
            
            # Check cto_trades
            cursor.execute("SELECT COUNT(DISTINCT Symbol) FROM cto_trades")
            unique_symbols = cursor.fetchone()[0]
            print(f"Found {unique_symbols} unique symbols in cto_trades")
        
        # Drop FULLPNL table if it exists
        cursor.execute("DROP TABLE IF EXISTS FULLPNL")
        print("\nDropped existing FULLPNL table (if any)")
        
        # Create FULLPNL table with just symbol column
        cursor.execute("""
            CREATE TABLE FULLPNL (
                symbol TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created new FULLPNL table")
        
        # Populate from positions table
        if position_count > 0:
            cursor.execute("""
                INSERT INTO FULLPNL (symbol)
                SELECT DISTINCT instrument_name
                FROM positions
                WHERE instrument_name IS NOT NULL
                ORDER BY instrument_name
            """)
            inserted = cursor.rowcount
            print(f"Inserted {inserted} symbols from positions table")
        else:
            # If positions empty, try getting unique symbols from cto_trades
            cursor.execute("""
                INSERT INTO FULLPNL (symbol)
                SELECT DISTINCT Symbol
                FROM cto_trades
                WHERE Symbol IS NOT NULL
                ORDER BY Symbol
            """)
            inserted = cursor.rowcount
            print(f"Inserted {inserted} symbols from cto_trades table")
        
        # Commit changes
        conn.commit()
        
        # Show sample of data
        print("\nSample of FULLPNL table:")
        print("-" * 60)
        cursor.execute("SELECT symbol FROM FULLPNL LIMIT 10")
        for row in cursor.fetchall():
            print(f"  {row[0]}")
        
        # Show total count
        cursor.execute("SELECT COUNT(*) FROM FULLPNL")
        total = cursor.fetchone()[0]
        print(f"\nTotal symbols in FULLPNL: {total}")
        
        # Show symbol format examples
        print("\nSymbol format check (first 5 with different patterns):")
        cursor.execute("""
            SELECT symbol 
            FROM FULLPNL 
            WHERE symbol LIKE '%Comdty%'
            LIMIT 5
        """)
        comdty_symbols = cursor.fetchall()
        if comdty_symbols:
            print("Bloomberg format symbols found:")
            for sym in comdty_symbols:
                print(f"  {sym[0]}")
        else:
            print("WARNING: No Bloomberg format symbols (ending in 'Comdty') found!")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\nDatabase connection closed")


if __name__ == "__main__":
    print("Creating FULLPNL table with symbol column")
    print("=" * 60)
    create_fullpnl_table() 