#!/usr/bin/env python
"""
Create positions from trades using the proven tyu5_pnl FIFO logic.
This is a simplified version that avoids circular imports.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import logging
import sqlite3

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator.storage import PnLStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleTradeProcessor:
    """Simplified version of tyu5_pnl TradeProcessor without circular imports."""
    
    def __init__(self, multiplier: float = 1000):
        self.positions = {}
        self.current_prices = {}
        self.multiplier = multiplier
        
    def process_trades(self, trades_df: pd.DataFrame):
        """Process trades and build positions using FIFO logic."""
        trades_df = trades_df.sort_values(['Date', 'Time'])
        
        for _, trade in trades_df.iterrows():
            symbol = trade['Symbol']
            quantity = float(trade['Quantity'])
            price = float(trade['Price'])
            action = trade['Action'].upper()
            
            if symbol not in self.positions:
                self.positions[symbol] = []
                
            self.current_prices[symbol] = price
            
            remaining = abs(quantity)
            
            # SELL: match against open longs
            if action in ['SELL', 'SHORT']:
                # Match against open long positions
                for pos in self.positions[symbol]:
                    if remaining <= 0:
                        break
                    if pos['remaining'] > 0:
                        matched = min(remaining, pos['remaining'])
                        pos['remaining'] -= matched
                        remaining -= matched
                        
                # If unmatched quantity, open new short
                if remaining > 0:
                    self.positions[symbol].append({
                        'quantity': -remaining,
                        'price': price,
                        'remaining': -remaining,
                        'type': trade.get('Type', 'FUT')
                    })
                    
            # BUY: match against open shorts
            elif action in ['BUY', 'COVER']:
                # Match against open short positions
                for pos in self.positions[symbol]:
                    if remaining <= 0:
                        break
                    if pos['remaining'] < 0:
                        matched = min(remaining, -pos['remaining'])
                        pos['remaining'] += matched
                        remaining -= matched
                        
                # If unmatched quantity, open new long
                if remaining > 0:
                    self.positions[symbol].append({
                        'quantity': remaining,
                        'price': price,
                        'remaining': remaining,
                        'type': trade.get('Type', 'FUT')
                    })
    
    def calculate_positions(self):
        """Calculate net positions from the position lots."""
        result = []
        
        for symbol, pos_list in self.positions.items():
            # Filter out fully closed positions
            active_positions = [p for p in pos_list if p['remaining'] != 0]
            
            if not active_positions:
                continue
                
            # Calculate net position
            total_qty = sum(p['remaining'] for p in active_positions)
            
            if total_qty == 0:
                continue
                
            # Calculate weighted average price
            total_value = sum(p['remaining'] * p['price'] for p in active_positions)
            avg_price = total_value / total_qty if total_qty != 0 else 0
            
            # Get current price
            current_price = self.current_prices.get(symbol, avg_price)
            
            # Calculate unrealized P&L
            unrealized_pnl = total_qty * (current_price - avg_price) * self.multiplier
            
            result.append({
                'Symbol': symbol,
                'Type': active_positions[0]['type'],
                'Net_Quantity': total_qty,
                'Avg_Entry_Price': avg_price,
                'Current_Price': current_price,
                'Unrealized_PNL': unrealized_pnl
            })
            
        return pd.DataFrame(result)


def main():
    """Process trades and create positions in database."""
    
    # Initialize storage
    storage = PnLStorage("data/output/pnl/pnl_tracker.db")
    
    # Load trades
    conn = storage._get_connection()
    trades_df = pd.read_sql_query("""
        SELECT Date, Time, Symbol, Action, Quantity, Price, Type
        FROM cto_trades
        ORDER BY Date, Time
    """, conn)
    
    if trades_df.empty:
        logger.warning("No trades found in database")
        conn.close()
        return
        
    logger.info(f"Processing {len(trades_df)} trades")
    
    # Process trades
    processor = SimpleTradeProcessor()
    processor.process_trades(trades_df)
    
    # Calculate positions
    positions_df = processor.calculate_positions()
    
    if positions_df.empty:
        logger.warning("No positions calculated")
        conn.close()
        return
        
    logger.info(f"Calculated {len(positions_df)} positions")
    print("\nPositions Summary:")
    print(positions_df)
    
    # Clear existing positions
    cursor = conn.cursor()
    cursor.execute("DELETE FROM positions")
    
    # Insert new positions
    for _, pos in positions_df.iterrows():
        symbol = pos['Symbol']
        is_option = 'OCA' in symbol or 'OPA' in symbol
        
        cursor.execute("""
            INSERT INTO positions (
                instrument_name, position_quantity, avg_cost,
                total_realized_pnl, unrealized_pnl, last_market_price,
                last_trade_id, last_updated, is_option, closed_quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            pos['Net_Quantity'],
            pos['Avg_Entry_Price'],
            0.0,
            pos['Unrealized_PNL'],
            pos['Current_Price'],
            'FIFO_CALC',
            datetime.now(),
            is_option,
            0.0
        ))
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Saved {len(positions_df)} positions to database")
    
    # Verify by checking the database
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    verify_df = pd.read_sql_query("SELECT COUNT(*) as count FROM positions", conn)
    conn.close()
    
    print(f"\nDatabase verification: {verify_df['count'][0]} positions in database")


if __name__ == "__main__":
    main() 