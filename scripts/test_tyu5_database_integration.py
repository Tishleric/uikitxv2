"""Test TYU5 Database Integration - Direct DataFrame capture"""

import sys
sys.path.append('.')

from lib.trading.pnl_integration.trade_ledger_adapter import TradeLedgerAdapter
from lib.trading.pnl_integration.tyu5_history_db import TYU5HistoryDB
import pandas as pd
from datetime import datetime


def test_database_integration():
    """Test the complete flow: Trade Ledger → TYU5 → Database"""
    
    print("=" * 80)
    print("TYU5 DATABASE INTEGRATION TEST")
    print("=" * 80)
    
    # Initialize adapter
    adapter = TradeLedgerAdapter()
    
    # Run TYU5 with database capture
    print("\n1. Running TYU5 with database capture...")
    result = adapter.prepare_and_run_tyu5(save_to_db=True)
    
    if result['status'] == 'SUCCESS':
        print(f"   ✓ TYU5 calculation completed")
        print(f"   ✓ Excel saved to: {result['excel_file']}")
        print(f"   ✓ Positions: {len(result['positions_df'])}")
        print(f"   ✓ Trades: {len(result['trades_df'])}")
        
        # Display sample data
        print("\n2. Sample Positions:")
        print(result['positions_df'][['Symbol', 'Type', 'Net_Quantity', 'Total_PNL']].head())
        
        print("\n3. Sample Trades:")
        print(result['trades_df'][['Symbol', 'Action', 'Quantity', 'Price_Decimal']].head())
        
    else:
        print(f"   ✗ TYU5 failed: {result.get('error')}")
        return
    
    # Query database
    print("\n4. Querying Database...")
    db = TYU5HistoryDB()
    
    # Get run summary
    runs = db.get_run_summary()
    print(f"\n   Database contains {len(runs)} runs:")
    if not runs.empty:
        print(runs[['run_timestamp', 'total_positions', 'total_trades', 'total_pnl']].head())
    
    # Get latest positions
    positions = db.get_latest_positions()
    print(f"\n   Latest positions snapshot:")
    if not positions.empty:
        print(positions[['symbol', 'type', 'net_quantity', 'total_pnl']].head())
    
    # Get position history for TYU5
    if not positions.empty and 'TYU5' in positions['symbol'].values:
        history = db.get_position_history('TYU5')
        print(f"\n   TYU5 position history ({len(history)} records):")
        print(history[['run_timestamp', 'net_quantity', 'avg_entry_price', 'total_pnl']].head())
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE - Database integration successful!")
    print("=" * 80)


if __name__ == "__main__":
    test_database_integration() 