"""Validate P&L calculations by directly using the PnLCalculator.

This script loads trades and market prices, runs calculations through
the core PnLCalculator, and compares with dashboard values.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, date
import pandas as pd
from tabulate import tabulate

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.trading.pnl_calculator import PnLCalculator, PnLStorage


def load_all_trades():
    """Load all trades from CSV files."""
    trade_files = sorted(Path("data/input/trade_ledger").glob("trades_*.csv"))
    all_trades = []
    
    for file in trade_files:
        df = pd.read_csv(file)
        df['source_file'] = file.name
        all_trades.append(df)
    
    if all_trades:
        return pd.concat(all_trades, ignore_index=True)
    return pd.DataFrame()


def get_market_prices_for_date(storage, instrument, as_of_date):
    """Get market price for an instrument on a specific date."""
    conn = storage._get_connection()
    cursor = conn.cursor()
    
    # Try to get 5pm price for that date
    query = """
    SELECT px_settle, px_last, upload_hour
    FROM market_prices
    WHERE bloomberg = ? 
      AND upload_date = ?
      AND upload_hour = 17
    ORDER BY upload_timestamp DESC
    LIMIT 1
    """
    
    cursor.execute(query, (instrument, as_of_date))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result['px_settle']
    return None


def validate_position_pnl():
    """Validate position P&L calculations."""
    print("\n" + "="*80)
    print("VALIDATING POSITION P&L CALCULATIONS")
    print("="*80)
    
    # Initialize storage
    storage = PnLStorage("data/output/pnl/pnl_tracker.db")
    
    # Load all trades
    trades_df = load_all_trades()
    print(f"\nLoaded {len(trades_df)} trades from {trades_df['source_file'].nunique()} files")
    
    # Initialize calculator
    calc = PnLCalculator()
    
    # Add all trades to calculator
    for _, trade in trades_df.iterrows():
        timestamp = datetime.strptime(str(trade['marketTradeTime']).split('.')[0], '%Y-%m-%d %H:%M:%S')
        quantity = float(trade['quantity'])
        if trade['buySell'] == 'S':
            quantity = -quantity
            
        calc.add_trade(
            timestamp=timestamp,
            symbol=trade['instrumentName'],
            quantity=quantity,
            price=float(trade['price']),
            trade_id=str(trade['tradeId'])
        )
    
    # Get unique trading dates
    trades_df['trade_date'] = pd.to_datetime(trades_df['marketTradeTime']).dt.date
    unique_dates = sorted(trades_df['trade_date'].unique())
    
    print(f"\nTrading dates: {', '.join(str(d) for d in unique_dates)}")
    
    # Add market prices for all instruments and dates
    instruments = trades_df['instrumentName'].unique()
    for trade_date in unique_dates:
        for instrument in instruments:
            price = get_market_prices_for_date(storage, instrument, trade_date)
            if price:
                calc.add_market_close(instrument, trade_date, price)
                print(f"Added market close: {instrument} @ {price} on {trade_date}")
    
    # Calculate P&L
    pnl_df = calc.calculate_daily_pnl()
    
    # Print detailed results by date
    for current_date in unique_dates:
        print(f"\n{'='*60}")
        print(f"DATE: {current_date}")
        print(f"{'='*60}")
        
        date_data = pnl_df[pnl_df['date'] == current_date]
        
        if date_data.empty:
            print("No data for this date")
            continue
            
        # Group by symbol and show details
        for symbol in date_data['symbol'].unique():
            symbol_data = date_data[date_data['symbol'] == symbol].iloc[-1]
            
            if symbol_data['position'] == 0 and symbol_data['realized_pnl'] == 0:
                continue
                
            print(f"\n{symbol}:")
            print(f"  Position: {symbol_data['position']}")
            print(f"  Avg Cost: {symbol_data['avg_cost']:.4f}")
            print(f"  Market Price: {symbol_data['market_close']:.4f}")
            print(f"  Realized P&L: ${symbol_data['realized_pnl']:.2f}")
            print(f"  Unrealized P&L: ${symbol_data['unrealized_pnl']:.2f}")
            print(f"  Total Daily P&L: ${symbol_data['total_daily_pnl']:.2f}")
    
    # Summary by instrument (latest position)
    print(f"\n{'='*60}")
    print("FINAL POSITIONS SUMMARY")
    print(f"{'='*60}")
    
    latest_date = max(unique_dates)
    latest_data = pnl_df[pnl_df['date'] == latest_date]
    
    summary_data = []
    total_realized = 0
    total_unrealized = 0
    
    for symbol in instruments:
        # Get all realized P&L for this symbol
        symbol_pnl = pnl_df[pnl_df['symbol'] == symbol]
        if symbol_pnl.empty:
            continue
            
        realized_sum = symbol_pnl['realized_pnl'].sum()
        latest = symbol_pnl.iloc[-1]
        
        if latest['position'] != 0 or realized_sum != 0:
            summary_data.append({
                'Instrument': symbol,
                'Position': int(latest['position']),
                'Avg Cost': f"{latest['avg_cost']:.4f}",
                'Realized P&L': f"${realized_sum:.2f}",
                'Unrealized P&L': f"${latest['unrealized_pnl']:.2f}",
                'Total P&L': f"${realized_sum + latest['unrealized_pnl']:.2f}"
            })
            
            total_realized += realized_sum
            total_unrealized += latest['unrealized_pnl']
    
    # Print summary table
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        print(tabulate(df_summary, headers='keys', tablefmt='grid', showindex=False))
    
    print(f"\nTOTALS:")
    print(f"  Total Realized P&L: ${total_realized:.2f}")
    print(f"  Total Unrealized P&L: ${total_unrealized:.2f}")
    print(f"  Total P&L: ${total_realized + total_unrealized:.2f}")


def check_eod_pnl_data():
    """Check what's stored in the EOD P&L table."""
    print("\n" + "="*80)
    print("EOD P&L TABLE DATA")
    print("="*80)
    
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    conn.row_factory = sqlite3.Row
    
    query = """
    SELECT 
        trade_date,
        instrument_name,
        closing_position,
        trades_count,
        realized_pnl,
        unrealized_pnl,
        total_pnl,
        avg_buy_price,
        avg_sell_price
    FROM eod_pnl
    ORDER BY trade_date, instrument_name
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Group by date
    by_date = {}
    for row in rows:
        date = row['trade_date']
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(dict(row))
    
    for date, instruments in by_date.items():
        print(f"\n{date}:")
        print("-" * 60)
        
        date_realized = 0
        date_unrealized = 0
        
        for inst in instruments:
            if inst['closing_position'] != 0 or inst['realized_pnl'] != 0:
                print(f"  {inst['instrument_name']}:")
                print(f"    Position: {inst['closing_position']}")
                print(f"    Trades: {inst['trades_count']}")
                print(f"    Realized: ${inst['realized_pnl']:.2f}")
                print(f"    Unrealized: ${inst['unrealized_pnl']:.2f}")
                print(f"    Total: ${inst['total_pnl']:.2f}")
                
                date_realized += inst['realized_pnl']
                date_unrealized += inst['unrealized_pnl']
        
        print(f"\n  Date Totals - Realized: ${date_realized:.2f}, Unrealized: ${date_unrealized:.2f}")
    
    conn.close()


def check_daily_pnl_aggregation():
    """Check how daily P&L is being aggregated."""
    print("\n" + "="*80)
    print("DAILY P&L AGGREGATION CHECK")
    print("="*80)
    
    conn = sqlite3.connect("data/output/pnl/pnl_tracker.db")
    conn.row_factory = sqlite3.Row
    
    # Same query as controller uses
    query = """
    SELECT 
        trade_date,
        COUNT(DISTINCT instrument_name) as instrument_count,
        SUM(trades_count) as total_trades_count,
        SUM(realized_pnl) as total_realized_pnl,
        SUM(unrealized_pnl) as total_unrealized_pnl,
        SUM(realized_pnl + unrealized_pnl) as total_pnl
    FROM eod_pnl
    GROUP BY trade_date
    ORDER BY trade_date DESC
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print("\nDaily P&L Summary (as shown in dashboard):")
    print("-" * 80)
    
    data = []
    for row in rows:
        data.append({
            'Date': row['trade_date'],
            'Trades': row['total_trades_count'],
            'Realized P&L': f"${row['total_realized_pnl']:.2f}",
            'Unrealized P&L': f"${row['total_unrealized_pnl']:.2f}",
            'Total P&L': f"${row['total_pnl']:.2f}"
        })
    
    if data:
        df = pd.DataFrame(data)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    
    conn.close()


if __name__ == "__main__":
    # Run all validations
    validate_position_pnl()
    check_eod_pnl_data()
    check_daily_pnl_aggregation() 