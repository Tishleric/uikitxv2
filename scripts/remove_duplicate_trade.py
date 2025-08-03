#!/usr/bin/env python3
"""Script to remove duplicate option trade with price 0.00100000016391277"""

import sqlite3
from datetime import datetime

def remove_duplicate_trade():
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    
    try:
        # First, find the duplicate trades in trades_fifo
        cursor.execute("""
            SELECT sequenceId, symbol, price, original_price, quantity, buySell, time 
            FROM trades_fifo 
            WHERE price = 0.00100000016391277
        """)
        
        duplicate_trades_fifo = cursor.fetchall()
        
        if not duplicate_trades_fifo:
            print("No trades found with price 0.00100000016391277 in trades_fifo")
            return
        
        print(f"Found {len(duplicate_trades_fifo)} trade(s) to remove from trades_fifo:")
        for trade in duplicate_trades_fifo:
            print(f"  SequenceId: {trade[0]}, Symbol: {trade[1]}, Price: {trade[2]}, OriginalPrice: {trade[3]}, Qty: {trade[4]}, Side: {trade[5]}, Time: {trade[6]}")
        
        # Get the sequenceIds to remove
        sequence_ids = [trade[0] for trade in duplicate_trades_fifo]
        
        # Remove from trades_fifo table
        placeholders = ','.join('?' * len(sequence_ids))
        cursor.execute(f"DELETE FROM trades_fifo WHERE sequenceId IN ({placeholders})", sequence_ids)
        print(f"Removed {cursor.rowcount} rows from trades_fifo table")
        
        # Remove from trades_lifo table
        cursor.execute(f"DELETE FROM trades_lifo WHERE sequenceId IN ({placeholders})", sequence_ids)
        print(f"Removed {cursor.rowcount} rows from trades_lifo table")
        
        # Note: daily_positions doesn't store individual trades, it stores aggregated positions by date
        # So we don't need to remove anything from there
        
        print("\nVerifying the remaining trade exists:")
        
        # Verify the remaining trade exists in trades_fifo
        cursor.execute("""
            SELECT sequenceId, symbol, price, original_price, quantity, buySell, time 
            FROM trades_fifo 
            WHERE price = 111.171875
        """)
        
        remaining_trades = cursor.fetchall()
        print(f"\nRemaining trade(s) with price 111.171875 in trades_fifo:")
        for trade in remaining_trades:
            print(f"  SequenceId: {trade[0]}, Symbol: {trade[1]}, Price: {trade[2]}, OriginalPrice: {trade[3]}, Qty: {trade[4]}, Side: {trade[5]}, Time: {trade[6]}")
        
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
    remove_duplicate_trade()