#!/usr/bin/env python
"""Test market price integration with positions."""

import sys
from pathlib import Path
from datetime import datetime
import pytz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.position_manager import PositionManager

def test_market_price_integration():
    """Test that market prices work with position updates."""
    
    # Initialize components
    storage = PnLStorage("data/output/pnl/pnl_tracker.db")
    position_manager = PositionManager(storage)
    
    print("Testing Market Price Integration")
    print("=" * 60)
    
    # Check market prices in database
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT bloomberg, px_last, px_settle, upload_timestamp 
        FROM market_prices 
        ORDER BY upload_timestamp DESC 
        LIMIT 10
    """)
    
    print("\nLatest market prices in database:")
    for row in cursor.fetchall():
        print(f"  {row['bloomberg']}: last={row['px_last']}, settle={row['px_settle']}, time={row['upload_timestamp']}")
    
    # Test getting a market price
    chicago_tz = pytz.timezone('America/Chicago')
    test_time = datetime.now(chicago_tz)
    
    test_instruments = ['TY', 'FV', 'TU']  # Futures
    
    print(f"\nTesting get_market_price at {test_time}:")
    for instrument in test_instruments:
        price, source = storage.get_market_price(instrument, test_time)
        print(f"  {instrument}: price={price}, source={source}")
    
    # Update market prices for positions
    print("\nUpdating market prices for all positions...")
    try:
        position_manager.update_market_prices()
        print("  SUCCESS: Market prices updated")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Check updated positions
    positions = position_manager.get_positions()
    
    print(f"\nPositions with market prices ({len(positions)} total):")
    for pos in positions[:5]:  # Show first 5
        print(f"  {pos['instrument_name']}: qty={pos['position_quantity']}, " +
              f"avg_cost={pos['avg_cost']}, market_price={pos.get('last_market_price', 'N/A')}, " +
              f"unrealized_pnl={pos.get('unrealized_pnl', 0)}")
    
    conn.close()

if __name__ == "__main__":
    test_market_price_integration() 