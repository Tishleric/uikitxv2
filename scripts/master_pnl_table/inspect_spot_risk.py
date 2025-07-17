#!/usr/bin/env python3
"""
inspect_spot_risk.py

Inspect the spot_risk database to understand structure for bid/ask data.
"""

import sqlite3
import os
import json


def inspect_spot_risk_db():
    """Inspect spot_risk database structure and sample data."""
    
    # Database path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    db_path = os.path.join(project_root, "data", "output", "spot_risk", "spot_risk.db")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # List all tables
        print("Tables in spot_risk.db:")
        print("=" * 60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check spot_risk_raw structure
        print("\nspot_risk_raw table structure:")
        print("=" * 60)
        cursor.execute("PRAGMA table_info(spot_risk_raw)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]:<25} {col[2]:<15}")
        
        # Check if bloomberg_symbol exists
        bloomberg_col_exists = any(col[1] == 'bloomberg_symbol' for col in columns)
        print(f"\nbloomberg_symbol column exists: {bloomberg_col_exists}")
        
        # Get sample data
        print("\nSample spot_risk_raw data (first 3 rows):")
        print("=" * 60)
        cursor.execute("SELECT * FROM spot_risk_raw LIMIT 3")
        rows = cursor.fetchall()
        
        for i, row in enumerate(rows):
            print(f"\nRow {i+1}:")
            for j, (col, val) in enumerate(zip([c[1] for c in columns], row)):
                if col == 'raw_data' and val:
                    # Parse JSON for raw_data column
                    try:
                        json_data = json.loads(val)
                        print(f"  {col}: <JSON with keys: {', '.join(list(json_data.keys())[:5])}>")
                        if 'bid' in json_data:
                            print(f"    - bid: {json_data['bid']}")
                        if 'ask' in json_data:
                            print(f"    - ask: {json_data['ask']}")
                    except:
                        print(f"  {col}: <unable to parse JSON>")
                else:
                    print(f"  {col}: {val}")
        
        # Check latest session
        print("\nLatest spot risk session:")
        print("=" * 60)
        cursor.execute("""
            SELECT session_id, source_file, data_timestamp, row_count 
            FROM spot_risk_sessions 
            ORDER BY session_id DESC 
            LIMIT 1
        """)
        session = cursor.fetchone()
        if session:
            print(f"  Session ID: {session[0]}")
            print(f"  Source File: {session[1]}")
            print(f"  Data Timestamp: {session[2]}")
            print(f"  Row Count: {session[3]}")
        
        # Test JSON extraction
        print("\nTesting JSON extraction for bid/ask:")
        print("=" * 60)
        cursor.execute("""
            SELECT 
                instrument_key,
                bloomberg_symbol,
                json_extract(raw_data, '$.bid') as bid,
                json_extract(raw_data, '$.ask') as ask
            FROM spot_risk_raw
            WHERE bloomberg_symbol IS NOT NULL
            LIMIT 5
        """)
        results = cursor.fetchall()
        for row in results:
            bid_val = row[2] if row[2] is not None else "NULL"
            ask_val = row[3] if row[3] is not None else "NULL"
            symbol = row[1] if row[1] is not None else "NULL"
            print(f"  {symbol:<30} bid: {bid_val:<10} ask: {ask_val}")
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    inspect_spot_risk_db() 