#!/usr/bin/env python3
"""Script to examine schema and find duplicate option trade rows"""

import sqlite3
import pandas as pd

def examine_tables():
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\n" + "="*80 + "\n")
        
        # Check schema for each relevant table
        for table_name in ['trades_fifo', 'trades_lifo', 'daily_positions', 'positions']:
            print(f"\nTable: {table_name}")
            print("-" * 40)
            
            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema = cursor.fetchall()
            
            if not schema:
                print(f"  Table {table_name} does not exist")
                continue
                
            print("  Schema:")
            for col in schema:
                print(f"    {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else 'NULL':10} {'PRIMARY KEY' if col[5] else ''}")
            
            # Look for rows with the duplicate price
            try:
                # First get column names
                col_names = [col[1] for col in schema]
                
                # Check if price column exists
                if 'price' in col_names:
                    cursor.execute(f"SELECT * FROM {table_name} WHERE price = 0.00100000016391277")
                    rows = cursor.fetchall()
                    
                    if rows:
                        print(f"\n  Found {len(rows)} row(s) with price 0.00100000016391277:")
                        df = pd.DataFrame(rows, columns=col_names)
                        print(df.to_string(index=False))
                    else:
                        print("\n  No rows found with price 0.00100000016391277")
                        
                    # Also check for the good trade
                    cursor.execute(f"SELECT * FROM {table_name} WHERE price = 111.171875")
                    rows = cursor.fetchall()
                    
                    if rows:
                        print(f"\n  Found {len(rows)} row(s) with price 111.171875:")
                        df = pd.DataFrame(rows, columns=col_names)
                        print(df.to_string(index=False))
                else:
                    print(f"\n  Table {table_name} does not have a price column")
                    
                    # For daily_positions, let's check if there are any option-related entries
                    if table_name == 'daily_positions':
                        # Get all columns to understand the structure
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                        sample_rows = cursor.fetchall()
                        if sample_rows:
                            print(f"\n  Sample rows from {table_name}:")
                            df = pd.DataFrame(sample_rows, columns=col_names)
                            print(df.to_string(index=False))
                            
            except Exception as e:
                print(f"  Error querying table: {e}")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    examine_tables()