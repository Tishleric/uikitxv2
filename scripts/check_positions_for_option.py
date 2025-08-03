#!/usr/bin/env python3
"""Script to check and update positions for the option trade"""

import sqlite3
import pandas as pd

def check_positions():
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    
    try:
        # Check positions table for the option symbol
        print("Checking positions table for option symbol...")
        cursor.execute("""
            SELECT * FROM positions 
            WHERE symbol LIKE '%1MQ5C%' OR symbol LIKE '%111.75%'
        """)
        
        positions_rows = cursor.fetchall()
        
        if positions_rows:
            print("\nFound in positions table:")
            cursor.execute("PRAGMA table_info(positions)")
            columns = [col[1] for col in cursor.fetchall()]
            df = pd.DataFrame(positions_rows, columns=columns)
            print(df.to_string(index=False))
        else:
            print("\nNo matching positions found")
            
        # Check daily_positions for the option symbol
        print("\n\nChecking daily_positions table for option symbol...")
        cursor.execute("""
            SELECT * FROM daily_positions 
            WHERE symbol LIKE '%1MQ5C%' OR symbol LIKE '%111.75%'
            ORDER BY date DESC
        """)
        
        daily_positions_rows = cursor.fetchall()
        
        if daily_positions_rows:
            print("\nFound in daily_positions table:")
            cursor.execute("PRAGMA table_info(daily_positions)")
            columns = [col[1] for col in cursor.fetchall()]
            df = pd.DataFrame(daily_positions_rows, columns=columns)
            print(df.to_string(index=False))
        else:
            print("\nNo matching daily positions found")
            
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    check_positions()