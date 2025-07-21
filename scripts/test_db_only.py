"""Test TYU5 Database Only - Verify database functionality"""

import sys
sys.path.append('.')

from lib.trading.pnl_integration.tyu5_history_db import TYU5HistoryDB
import pandas as pd
from datetime import datetime


def test_database_only():
    """Test database functionality with dummy data"""
    
    print("Testing TYU5 History Database...")
    
    # Create dummy data matching TYU5 output format
    trades_df = pd.DataFrame([
        {
            'Trade_ID': 'TEST_001',
            'DateTime': '2025-07-20 10:00:00',
            'Symbol': 'TYU5',
            'Action': 'BUY',
            'Quantity': 1000,
            'Price_Decimal': 110.5,
            'Price_32nds': '110-16',
            'Fees': 0,
            'Type': 'FUT',
            'Realized_PNL': 0,
            'Counterparty': 'TEST'
        }
    ])
    
    positions_df = pd.DataFrame([
        {
            'Symbol': 'TYU5',
            'Type': 'FUT',
            'Net_Quantity': 1000,
            'Avg_Entry_Price': 110.5,
            'Avg_Entry_Price_32nds': '110-16',
            'Prior_Close': 110.625,
            'Current_Price': 110.625,
            'Prior_Present_Value': 110500000,
            'Current_Present_Value': 110625000,
            'Unrealized_PNL': 125000,
            'Unrealized_PNL_Current': 125000,
            'Unrealized_PNL_Flash': 125000,
            'Unrealized_PNL_Close': 125000,
            'Realized_PNL': 0,
            'Daily_PNL': 0,
            'Total_PNL': 125000,
            'attribution_error': None
        }
    ])
    
    # Initialize database
    db = TYU5HistoryDB()
    
    # Save run
    timestamp = datetime.now()
    db.save_run(
        run_timestamp=timestamp,
        trades_df=trades_df,
        positions_df=positions_df,
        trade_ledger_file='test_file.csv',
        excel_file='test_output.xlsx'
    )
    
    print("✓ Data saved to database")
    
    # Query back
    runs = db.get_run_summary()
    print(f"\nDatabase contains {len(runs)} runs")
    print(runs[['run_timestamp', 'total_positions', 'total_trades', 'total_pnl']].head())
    
    positions = db.get_latest_positions()
    print(f"\nLatest positions:")
    print(positions[['symbol', 'net_quantity', 'total_pnl']].head())
    
    print("\n✓ Database test successful!")


if __name__ == "__main__":
    test_database_only() 