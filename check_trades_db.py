import sqlite3
import os

if os.path.exists('trades.db'):
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    
    # Get all tables
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"Tables in trades.db: {[t[0] for t in tables]}")
    
    # Check trades_fifo
    if any('trades_fifo' in t for t in tables):
        count = cursor.execute("SELECT COUNT(*) FROM trades_fifo").fetchone()[0]
        print(f"Total trades in FIFO: {count}")
        
        # Show recent trades
        recent = cursor.execute("SELECT * FROM trades_fifo ORDER BY time DESC LIMIT 5").fetchall()
        if recent:
            print("\nRecent trades:")
            for trade in recent:
                print(trade)
    else:
        print("No trades_fifo table found!")
        
    conn.close()
else:
    print("trades.db does not exist!") 