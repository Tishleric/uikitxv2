#!/usr/bin/env python3
"""Show complete FULLPNL table."""
import sqlite3
from pathlib import Path

def show_fullpnl():
    project_root = Path(__file__).parent.parent.parent
    pnl_db_path = project_root / "data/output/pnl/pnl_tracker.db"
    
    conn = sqlite3.connect(pnl_db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT symbol, open_position, px_last, px_settle, bid, ask, price
        FROM FULLPNL
        ORDER BY symbol
    """)
    
    results = cursor.fetchall()
    
    print(f"{'Symbol':<30} {'Position':>10} {'px_last':>10} {'px_settle':>10} {'Bid':>10} {'Ask':>10} {'Price':>10}")
    print("-" * 100)
    
    for row in results:
        symbol, position, px_last, px_settle, bid, ask, price = row
        position_str = f"{position:.0f}" if position is not None else "NULL"
        px_last_str = f"{px_last:.6f}" if px_last is not None else "NULL"
        px_settle_str = f"{px_settle:.6f}" if px_settle is not None else "NULL"
        bid_str = f"{bid:.6f}" if bid is not None else "NULL"
        ask_str = f"{ask:.6f}" if ask is not None else "NULL"
        price_str = f"{price:.6f}" if price is not None else "NULL"
        
        print(f"{symbol:<30} {position_str:>10} {px_last_str:>10} {px_settle_str:>10} {bid_str:>10} {ask_str:>10} {price_str:>10}")
    
    conn.close()

if __name__ == "__main__":
    show_fullpnl() 