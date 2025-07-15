"""Fix EOD unrealized P&L values by recalculating from trades and market prices.

This script:
1. Loads all trades and recalculates P&L using the core calculator
2. Updates EOD P&L table with correct unrealized values
3. Fixes the bad price data for XCMEOCADPS20250714N0VY2/109
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import pytz

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator import PnLCalculator, PnLStorage


def fix_bad_trade_price():
    """Fix the incorrect price for XCMEOCADPS20250714N0VY2/109."""
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    
    # Check current data
    check_query = """
    SELECT trade_id, instrument_name, price, quantity 
    FROM processed_trades 
    WHERE instrument_name = 'XCMEOCADPS20250714N0VY2/109'
    """
    
    cursor = conn.cursor()
    cursor.execute(check_query)
    trades = cursor.fetchall()
    
    print("\nCurrent trades for XCMEOCADPS20250714N0VY2/109:")
    for trade in trades:
        print(f"  Trade {trade[0]}: Price={trade[2]}, Quantity={trade[3]}")
    
    # Fix the bad price (1234.0 should be 1.234)
    update_query = """
    UPDATE processed_trades 
    SET price = 1.234 
    WHERE instrument_name = 'XCMEOCADPS20250714N0VY2/109' 
      AND price = 1234.0
    """
    
    cursor.execute(update_query)
    rows_updated = cursor.rowcount
    conn.commit()
    
    print(f"\nFixed {rows_updated} trade(s) with incorrect price")
    
    conn.close()


def recalculate_all_eod_pnl():
    """Recalculate all EOD P&L with correct unrealized values."""
    print("\n" + "="*80)
    print("RECALCULATING EOD P&L")
    print("="*80)
    
    # Initialize storage
    storage = PnLStorage("data/output/pnl/pnl_tracker.db")
    est_tz = pytz.timezone('US/Eastern')
    
    # Get all unique trade dates
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT DATE(trade_timestamp) as trade_date 
        FROM processed_trades 
        ORDER BY trade_date
    """)
    
    trade_dates = [row['trade_date'] for row in cursor.fetchall()]
    print(f"\nTrade dates to process: {', '.join(trade_dates)}")
    
    # Process each date
    for process_date_str in trade_dates:
        process_date = datetime.strptime(process_date_str, '%Y-%m-%d').date()
        print(f"\n{'='*60}")
        print(f"Processing {process_date}")
        print(f"{'='*60}")
        
        # Load trades up to and including this date
        query = """
        SELECT * FROM processed_trades 
        WHERE DATE(trade_timestamp) <= ? 
        ORDER BY trade_timestamp
        """
        
        trades_df = pd.read_sql_query(query, conn, params=(process_date_str,))
        
        if trades_df.empty:
            print("No trades to process")
            continue
            
        # Initialize calculator
        calc = PnLCalculator()
        
        # Add all trades
        for _, trade in trades_df.iterrows():
            timestamp = pd.to_datetime(trade['trade_timestamp'])
            quantity = float(trade['quantity'])
            if trade['side'] == 'S':
                quantity = -quantity
                
            calc.add_trade(
                timestamp=timestamp,
                symbol=trade['instrument_name'],
                quantity=quantity,
                price=float(trade['price']),
                trade_id=str(trade['trade_id'])
            )
        
        # Get all instruments traded up to this date
        instruments = trades_df['instrument_name'].unique()
        
        # Add market prices for EOD (5pm) on process date
        eod_time = est_tz.localize(datetime.combine(process_date, datetime.min.time().replace(hour=17)))
        
        for instrument in instruments:
            price, price_source = storage.get_market_price(instrument, eod_time)
            if price:
                calc.add_market_close(instrument, process_date, price)
                print(f"  {instrument}: Market price = {price} ({price_source})")
        
        # Calculate P&L
        pnl_df = calc.calculate_daily_pnl()
        
        if pnl_df.empty:
            print("No P&L data calculated")
            continue
        
        # Filter for current date
        date_pnl = pnl_df[pnl_df['date'] == process_date]
        
        # Update EOD P&L for each instrument
        for symbol in date_pnl['symbol'].unique():
            symbol_data = date_pnl[date_pnl['symbol'] == symbol].iloc[-1]
            
            # Get trade count for this specific date
            trade_count_query = """
            SELECT COUNT(*) as count 
            FROM processed_trades 
            WHERE instrument_name = ? AND DATE(trade_timestamp) = ?
            """
            cursor.execute(trade_count_query, (symbol, process_date_str))
            trade_count = cursor.fetchone()['count']
            
            # Calculate cumulative realized P&L up to this date
            cumulative_realized = pnl_df[
                (pnl_df['symbol'] == symbol) & 
                (pnl_df['date'] <= process_date)
            ]['realized_pnl'].sum()
            
            # Update EOD P&L
            update_query = """
            UPDATE eod_pnl 
            SET unrealized_pnl = ?,
                total_pnl = ?,
                realized_pnl = ?,
                trades_count = ?
            WHERE trade_date = ? AND instrument_name = ?
            """
            
            unrealized = float(symbol_data['unrealized_pnl'])
            total = cumulative_realized + unrealized
            
            cursor.execute(update_query, (
                unrealized,
                total,
                cumulative_realized,
                trade_count,
                process_date_str,
                symbol
            ))
            
            if cursor.rowcount > 0:
                print(f"  Updated {symbol}:")
                print(f"    Position: {int(symbol_data['position'])}")
                print(f"    Realized P&L: ${cumulative_realized:.2f}")
                print(f"    Unrealized P&L: ${unrealized:.2f}")
                print(f"    Total P&L: ${total:.2f}")
    
    conn.commit()
    conn.close()
    print("\nEOD P&L recalculation complete!")


def verify_daily_summary():
    """Verify the daily P&L summary after fixes."""
    print("\n" + "="*80)
    print("DAILY P&L SUMMARY (AFTER FIXES)")
    print("="*80)
    
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    conn.row_factory = sqlite3.Row
    
    query = """
    SELECT 
        trade_date,
        SUM(trades_count) as total_trades,
        SUM(realized_pnl) as total_realized,
        SUM(unrealized_pnl) as total_unrealized,
        SUM(total_pnl) as total_pnl
    FROM eod_pnl
    GROUP BY trade_date
    ORDER BY trade_date
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    
    data = []
    for row in cursor.fetchall():
        data.append({
            'Date': row['trade_date'],
            'Trades': row['total_trades'],
            'Realized P&L': f"${row['total_realized']:.2f}",
            'Unrealized P&L': f"${row['total_unrealized']:.2f}",
            'Total P&L': f"${row['total_pnl']:.2f}"
        })
    
    if data:
        df = pd.DataFrame(data)
        print(df.to_string(index=False))
    
    conn.close()


if __name__ == "__main__":
    # First fix the bad trade price
    fix_bad_trade_price()
    
    # Then recalculate all EOD P&L
    recalculate_all_eod_pnl()
    
    # Finally verify the results
    verify_daily_summary() 