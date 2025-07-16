#!/usr/bin/env python
"""Process existing trades through the position manager to populate positions."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.position_manager import PositionManager
import sqlite3

def process_existing_trades():
    """Process trades already in the database through the position manager."""
    
    # Initialize storage and position manager
    db_path = "data/output/pnl/pnl_tracker.db"
    storage = PnLStorage(db_path)
    position_manager = PositionManager(storage)
    
    print("Processing existing trades to create positions...")
    
    # Get all trades from the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get trades ordered by timestamp
    cursor.execute("""
        SELECT * FROM processed_trades 
        ORDER BY trade_timestamp ASC
    """)
    
    trades = cursor.fetchall()
    print(f"Found {len(trades)} trades to process")
    
    # Process each trade through the position manager
    position_updates = []
    
    for trade in trades:
        # Convert side to signed quantity
        quantity = float(trade['quantity'])
        if trade['side'] == 'S':
            quantity = -quantity
        
        # Create trade data for position manager
        trade_data = {
            'instrumentName': trade['instrument_name'],
            'marketTradeTime': trade['trade_timestamp'],
            'quantity': quantity,
            'price': float(trade['price']),
            'tradeId': trade['trade_id']
        }
        
        try:
            # Process trade and update position
            update = position_manager.process_trade(trade_data)
            position_updates.append({
                'instrument': update.instrument_name,
                'action': update.trade_action,
                'new_qty': update.new_quantity,
                'realized_pnl': update.realized_pnl
            })
            
            print(f"Processed {trade['instrument_name']}: {update.trade_action} -> qty={update.new_quantity}")
            
        except Exception as e:
            print(f"Error processing trade {trade['trade_id']}: {e}")
    
    # Update market prices for all positions
    print("\nUpdating market prices...")
    try:
        position_manager.update_market_prices()
        print("Market prices updated successfully")
    except Exception as e:
        print(f"Error updating market prices: {e}")
    
    # Get final positions
    positions = position_manager.get_positions()
    print(f"\nCreated {len(positions)} positions:")
    
    for pos in positions:
        print(f"  {pos['instrument_name']}: {pos['position_quantity']} @ ${pos['avg_cost']:.4f}")
        print(f"    Realized P&L: ${pos['total_realized_pnl']:.2f}")
        print(f"    Unrealized P&L: ${pos.get('unrealized_pnl', 0):.2f}")
    
    # Summary
    if position_updates:
        opens = sum(1 for u in position_updates if u['action'] == 'OPEN')
        closes = sum(1 for u in position_updates if u['action'] == 'CLOSE')
        amends = sum(1 for u in position_updates if u['action'] == 'AMEND')
        total_realized = sum(u['realized_pnl'] for u in position_updates)
        
        print(f"\nPosition update summary:")
        print(f"  Opens: {opens}")
        print(f"  Closes: {closes}")
        print(f"  Amends: {amends}")
        print(f"  Total realized P&L: ${total_realized:.2f}")
    
    conn.close()
    print("\nPosition population complete!")

if __name__ == "__main__":
    process_existing_trades() 