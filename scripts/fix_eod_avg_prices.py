#!/usr/bin/env python
"""Fix EOD Average Prices

This script recalculates and updates the avg_buy_price and avg_sell_price
fields in the eod_pnl table using the PnLCalculator to get correct
weighted average costs.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.calculator import PnLCalculator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def recalculate_avg_prices_for_date(storage: PnLStorage, trade_date: str):
    """Recalculate average prices for all instruments on a given date."""
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    # Get all trades for this date
    cursor.execute("""
        SELECT 
            trade_id,
            instrument_name,
            trade_timestamp,
            quantity,
            price,
            side
        FROM processed_trades
        WHERE trade_date = ?
        ORDER BY trade_timestamp
    """, (trade_date,))
    
    trades = cursor.fetchall()
    
    if not trades:
        logger.info(f"No trades found for {trade_date}")
        return 0
    
    # Create calculator and process trades
    calc = PnLCalculator()
    
    for trade in trades:
        timestamp = pd.to_datetime(trade['trade_timestamp'])
        symbol = trade['instrument_name']
        quantity = float(trade['quantity'])
        if trade['side'] == 'S':
            quantity = -quantity
        price = float(trade['price'])
        trade_id = str(trade['trade_id'])
        
        calc.add_trade(timestamp, symbol, quantity, price, trade_id)
    
    # Add dummy market closes to trigger P&L calculation
    trade_date_obj = pd.to_datetime(trade_date).date()
    for symbol in set(t['instrument_name'] for t in trades):
        # Use last trade price as market close
        last_price = next(t['price'] for t in reversed(trades) if t['instrument_name'] == symbol)
        calc.add_market_close(symbol, trade_date_obj, last_price)
    
    # Calculate P&L to get positions and average costs
    pnl_df = calc.calculate_daily_pnl()
    
    if pnl_df.empty:
        logger.warning(f"No P&L data calculated for {trade_date}")
        return 0
    
    # Update EOD records
    updates = []
    for symbol in pnl_df['symbol'].unique():
        symbol_data = pnl_df[pnl_df['symbol'] == symbol].iloc[-1]
        
        position = float(symbol_data['position'])
        avg_cost = float(symbol_data['avg_cost']) if pd.notna(symbol_data['avg_cost']) else 0.0
        
        # Determine avg_buy or avg_sell based on position
        if position > 0 and avg_cost > 0:
            avg_buy = avg_cost
            avg_sell = None
        elif position < 0 and avg_cost > 0:
            avg_buy = None
            avg_sell = avg_cost
        else:
            avg_buy = None
            avg_sell = None
        
        updates.append((avg_buy, avg_sell, trade_date, symbol))
    
    # Update database
    update_query = """
    UPDATE eod_pnl 
    SET avg_buy_price = ?, avg_sell_price = ?
    WHERE trade_date = ? AND instrument_name = ?
    """
    
    cursor.executemany(update_query, updates)
    conn.commit()
    conn.close()
    
    return len(updates)


def main():
    """Main function to fix average prices."""
    storage = PnLStorage()
    
    # Get all unique trade dates
    conn = storage._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT trade_date FROM eod_pnl ORDER BY trade_date")
    trade_dates = [row['trade_date'] for row in cursor.fetchall()]
    conn.close()
    
    logger.info(f"Found {len(trade_dates)} trade dates to process")
    
    total_updated = 0
    for trade_date in trade_dates:
        logger.info(f"Processing {trade_date}...")
        updated = recalculate_avg_prices_for_date(storage, trade_date)
        total_updated += updated
        logger.info(f"  Updated {updated} records")
    
    logger.info(f"Total records updated: {total_updated}")
    
    # Show sample results
    conn = storage._get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            trade_date,
            instrument_name,
            closing_position,
            avg_buy_price,
            avg_sell_price,
            realized_pnl,
            unrealized_pnl
        FROM eod_pnl
        WHERE avg_buy_price IS NOT NULL OR avg_sell_price IS NOT NULL
        ORDER BY trade_date DESC, instrument_name
        LIMIT 10
    """)
    
    print("\nSample Updated Records:")
    print("-" * 120)
    print(f"{'Date':<12} {'Instrument':<35} {'Position':>10} {'Avg Buy':>10} {'Avg Sell':>10} {'Real P&L':>10} {'Unreal P&L':>12}")
    print("-" * 120)
    
    for row in cursor.fetchall():
        instrument = row['instrument_name']
        if len(instrument) > 35:
            instrument = instrument[:32] + "..."
        print(f"{row['trade_date']:<12} {instrument:<35} {row['closing_position']:>10} "
              f"{row['avg_buy_price'] or 0:>10.4f} {row['avg_sell_price'] or 0:>10.4f} "
              f"{row['realized_pnl']:>10.2f} {row['unrealized_pnl']:>12.2f}")
    
    conn.close()


if __name__ == "__main__":
    main() 