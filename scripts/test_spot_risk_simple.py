#!/usr/bin/env python3
"""
Simple test to check if spot risk prices can be added to market_prices.db
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from pathlib import Path
from datetime import datetime

def main():
    """Test adding a sample current price to the database."""
    
    db_path = Path("data/output/market_prices/market_prices.db")
    
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
        
    print(f"Testing database update: {db_path}")
    
    try:
        # Use a short timeout to avoid hanging on locks
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        cursor = conn.cursor()
        
        # Check if Current_Price column exists
        cursor.execute("PRAGMA table_info(options_prices)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Options table columns: {columns}")
        
        if 'Current_Price' not in columns:
            print("ERROR: Current_Price column not found!")
            return
            
        # Try to update a sample option price
        test_symbol = "TYN25C3 111.000"
        test_price = 0.5625
        test_date = "2025-07-17"
        
        print(f"\nTrying to update: {test_symbol} = ${test_price}")
        
        # First check if row exists
        cursor.execute("""
            SELECT symbol, Current_Price, Flash_Close 
            FROM options_prices 
            WHERE symbol = ? AND trade_date = ?
        """, (test_symbol, test_date))
        
        row = cursor.fetchone()
        if row:
            print(f"Found existing row: {row}")
            
            # Update it
            cursor.execute("""
                UPDATE options_prices
                SET Current_Price = ?
                WHERE symbol = ? AND trade_date = ?
            """, (test_price, test_symbol, test_date))
            
            print(f"Updated {cursor.rowcount} rows")
        else:
            print("No existing row found, inserting new one")
            
            cursor.execute("""
                INSERT INTO options_prices (trade_date, symbol, Current_Price)
                VALUES (?, ?, ?)
            """, (test_date, test_symbol, test_price))
            
            print(f"Inserted {cursor.rowcount} rows")
            
        conn.commit()
        
        # Verify the update
        cursor.execute("""
            SELECT symbol, Current_Price, Flash_Close, prior_close
            FROM options_prices
            WHERE symbol = ? AND trade_date = ?
        """, (test_symbol, test_date))
        
        row = cursor.fetchone()
        if row:
            print(f"\nVerification - Row after update:")
            print(f"  Symbol: {row[0]}")
            print(f"  Current_Price: {row[1]}")
            print(f"  Flash_Close: {row[2]}")
            print(f"  prior_close: {row[3]}")
        
        conn.close()
        print("\n✓ Database update successful!")
        
    except sqlite3.OperationalError as e:
        print(f"\n✗ Database error: {e}")
        print("The database might be locked by another process")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")


if __name__ == "__main__":
    main() 