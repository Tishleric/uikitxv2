#!/usr/bin/env python
"""Check the current state of the P&L system."""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.market_prices.storage import MarketPriceStorage


def check_pnl_state():
    """Check current state of P&L system."""
    print("\n" + "="*60)
    print("P&L SYSTEM STATE CHECK")
    print("="*60 + "\n")
    
    # Check trade files
    trade_dir = Path("data/input/trade_ledger")
    print(f"1. Trade files in {trade_dir}:")
    if trade_dir.exists():
        csv_files = list(trade_dir.glob("trades_*.csv"))
        print(f"   Found {len(csv_files)} trade files")
        for f in sorted(csv_files)[-5:]:  # Show last 5
            print(f"   - {f.name} ({f.stat().st_size} bytes)")
    else:
        print("   Directory not found!")
    
    # Check database state
    print("\n2. Database state:")
    try:
        pnl_storage = PnLStorage()
        with pnl_storage._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM cto_trades")
            trade_count = cursor.fetchone()[0]
            print(f"   - cto_trades table: {trade_count} records")
            
            # Show last few trades
            cursor = conn.execute("""
                SELECT Date, Time, Symbol, Type, Action, Quantity, Price, source_file
                FROM cto_trades 
                ORDER BY Date DESC, Time DESC 
                LIMIT 3
            """)
            recent_trades = cursor.fetchall()
            if recent_trades:
                print("   - Recent trades:")
                for trade in recent_trades:
                    print(f"     {trade['Date']} {trade['Time']}: {trade['Symbol']} {trade['Type']} {trade['Action']} {trade['Quantity']} @ {trade['Price']}")
    except Exception as e:
        print(f"   Error accessing P&L database: {e}")
    
    # Check market prices
    print("\n3. Market prices:")
    try:
        market_storage = MarketPriceStorage()
        with market_storage._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM futures_prices")
            futures_count = cursor.fetchone()[0]
            print(f"   - futures_prices: {futures_count} records")
            
            cursor = conn.execute("SELECT COUNT(*) FROM options_prices")
            options_count = cursor.fetchone()[0]
            print(f"   - options_prices: {options_count} records")
    except Exception as e:
        print(f"   Error accessing market price database: {e}")
    
    # Check Excel output
    print("\n4. TYU5 Excel output:")
    excel_dir = Path("data/output/pnl")
    if excel_dir.exists():
        excel_files = list(excel_dir.glob("tyu5_pnl_all_*.xlsx"))
        print(f"   Found {len(excel_files)} Excel files")
        if excel_files:
            latest = max(excel_files, key=lambda x: x.stat().st_mtime)
            mod_time = datetime.fromtimestamp(latest.stat().st_mtime)
            print(f"   - Latest: {latest.name}")
            print(f"   - Modified: {mod_time}")
            print(f"   - Size: {latest.stat().st_size:,} bytes")
    else:
        print("   Output directory not found!")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    check_pnl_state() 