#!/usr/bin/env python3
"""Script to update option positions to reflect the removal of duplicate trade"""

import sqlite3
from datetime import datetime

def update_positions():
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    
    try:
        # Update positions table - change open_position from 2.0 to 1.0
        print("Updating positions table...")
        cursor.execute("""
            UPDATE positions 
            SET open_position = 1.0,
                last_updated = ?
            WHERE symbol = '1MQ5C 111.75 Comdty'
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        
        print(f"Updated {cursor.rowcount} row(s) in positions table")
        
        # Update daily_positions table - change open_position from 2.0 to 1.0
        print("\nUpdating daily_positions table...")
        cursor.execute("""
            UPDATE daily_positions 
            SET open_position = 1.0
            WHERE symbol = '1MQ5C 111.75 Comdty' AND date = '2025-07-29'
        """)
        
        print(f"Updated {cursor.rowcount} row(s) in daily_positions table")
        
        # Verify the updates
        print("\nVerifying updates...")
        
        # Check positions table
        cursor.execute("""
            SELECT symbol, open_position, closed_position, last_updated 
            FROM positions 
            WHERE symbol = '1MQ5C 111.75 Comdty'
        """)
        
        position_row = cursor.fetchone()
        if position_row:
            print(f"\nPositions table:")
            print(f"  Symbol: {position_row[0]}")
            print(f"  Open Position: {position_row[1]}")
            print(f"  Closed Position: {position_row[2]}")
            print(f"  Last Updated: {position_row[3]}")
        
        # Check daily_positions table
        cursor.execute("""
            SELECT date, symbol, method, open_position 
            FROM daily_positions 
            WHERE symbol = '1MQ5C 111.75 Comdty'
            ORDER BY date DESC, method
        """)
        
        daily_rows = cursor.fetchall()
        if daily_rows:
            print(f"\nDaily positions table:")
            for row in daily_rows:
                print(f"  Date: {row[0]}, Symbol: {row[1]}, Method: {row[2]}, Open Position: {row[3]}")
        
        # Commit the changes
        conn.commit()
        print("\nChanges committed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_positions()