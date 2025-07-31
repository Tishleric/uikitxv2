"""
PnL Calculation System - Main Application

Purpose: Command-line interface and orchestration for P&L calculations
"""

import sqlite3
import argparse
from datetime import datetime
import pandas as pd
from .config import DB_NAME, DEFAULT_SYMBOL, METHODS
from .pnl_engine import process_new_trade, calculate_unrealized_pnl
from .data_manager import (
    create_all_tables, load_csv_to_database, load_multiple_csvs,
    view_unrealized_positions, view_realized_trades, 
    load_pricing_dictionaries, setup_pricing_as_of,
    roll_2pm_prices, roll_4pm_prices, view_daily_positions,
    update_daily_position, get_trading_day
)


def calculate_live_unrealized(conn, price_dicts):
    """Calculate real-time unrealized PnL for both FIFO and LIFO"""
    results = {}
    
    for method in METHODS:
        positions = view_unrealized_positions(conn, method)
        if not positions.empty:
            pnl_list = calculate_unrealized_pnl(positions, price_dicts, 'live')
            results[method] = pd.DataFrame(pnl_list)
        else:
            results[method] = pd.DataFrame()
    
    return results


def calculate_2pm_unrealized(conn, price_dicts):
    """Calculate 2pm close unrealized PnL"""
    results = {}
    
    for method in METHODS:
        positions = view_unrealized_positions(conn, method)
        if not positions.empty:
            pnl_list = calculate_unrealized_pnl(positions, price_dicts, '2pm_close')
            results[method] = pd.DataFrame(pnl_list)
        else:
            results[method] = pd.DataFrame()
    
    return results


def calculate_4pm_unrealized(conn, price_dicts):
    """Calculate 4pm EOD unrealized PnL"""
    results = {}
    
    for method in METHODS:
        positions = view_unrealized_positions(conn, method)
        if not positions.empty:
            pnl_list = calculate_unrealized_pnl(positions, price_dicts, '4pm_close')
            results[method] = pd.DataFrame(pnl_list)
        else:
            results[method] = pd.DataFrame()
    
    return results


def update_daily_unrealized_pnl(conn, date, price_dicts, symbol):
    """Update unrealized PnL in daily positions table"""
    cursor = conn.cursor()
    
    for method in METHODS:
        # Get unrealized positions
        positions = view_unrealized_positions(conn, method)
        if positions.empty:
            continue
        
        # Calculate unrealized PnL using existing function
        unrealized_list = calculate_unrealized_pnl(positions, price_dicts, '4pm_close')
        unrealized_df = pd.DataFrame(unrealized_list)
        total_unrealized = unrealized_df['unrealizedPnL'].sum() if not unrealized_df.empty else 0
        
        # Update daily position
        update_query = """
            UPDATE daily_positions 
            SET unrealized_pnl = ?
            WHERE date = ? AND symbol = ? AND method = ?
        """
        cursor.execute(update_query, (total_unrealized, date, symbol, method))
    
    conn.commit()


def process_single_csv(csv_file, conn):
    """Process a single CSV file through the calculation engine"""
    # Create fresh tables
    create_all_tables(conn)
    
    # Load and process trades
    df, realized_summary = load_csv_to_database(csv_file, conn, process_new_trade)
    
    print(f"Loaded {len(df)} trades from {csv_file}")
    for method in METHODS:
        print(f"{method.upper()}: {len(realized_summary[method])} realizations")
    
    return df, realized_summary


def process_multiple_csvs(folder_path, conn, close_prices=None):
    """Process multiple CSV files with daily tracking"""
    # Create fresh tables
    create_all_tables(conn)
    
    # For simple loading without day-by-day processing
    if close_prices is None:
        trades_df = load_multiple_csvs(folder_path, conn, process_new_trade, 
                                      use_daily_tracking=True, close_prices=close_prices)
        if trades_df is not None:
            print(f"Processed {len(trades_df)} total trades")
        return trades_df
    
    # Day-by-day processing when close prices are provided
    # First, read all trades to get the full picture
    all_trades = []
    symbol = DEFAULT_SYMBOL
    
    # Read all CSV files
    import os
    import re
    from glob import glob
    pattern = os.path.join(folder_path, 'trades_*.csv')
    csv_files = glob(pattern)
    
    # Extract dates and sort
    file_info = []
    date_pattern = re.compile(r'trades_(\d{8})\.csv')
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        match = date_pattern.match(filename)
        if match:
            date_str = match.group(1)
            file_info.append((date_str, file_path))
    
    file_info.sort(key=lambda x: x[0])
    
    # Read all trades first
    for date_str, file_path in file_info:
        df = pd.read_csv(file_path)
        if not df.empty:
            symbol = df['instrumentName'].iloc[0]
        all_trades.append(df)
    
    if not all_trades:
        return None
    
    all_trades_df = pd.concat(all_trades, ignore_index=True)
    all_trades_df['marketTradeTime'] = pd.to_datetime(all_trades_df['marketTradeTime'])
    all_trades_df = all_trades_df.sort_values('marketTradeTime')
    
    # Process all trades sequentially
    last_processed_date = None
    
    for idx, row in all_trades_df.iterrows():
        trading_day = get_trading_day(row['marketTradeTime'])
        trade_date = trading_day
        
        # When we transition to a new day, calculate unrealized for previous day
        if last_processed_date and trade_date != last_processed_date:
            if last_processed_date in close_prices:
                # Set up pricing and calculate unrealized for the completed day
                valuation_dt = datetime.combine(last_processed_date, datetime.min.time()).replace(hour=16, minute=0)
                setup_pricing_as_of(conn, valuation_dt, close_prices, symbol)
                price_dicts = load_pricing_dictionaries(conn)
                update_daily_unrealized_pnl(conn, last_processed_date.strftime('%Y-%m-%d'), price_dicts, symbol)
        
        # Process the trade
        trade = {
            'transactionId': row['tradeId'],
            'symbol': row['instrumentName'],
            'price': row['price'],
            'quantity': row['quantity'],
            'buySell': row['buySell'],
            'sequenceId': f"{trading_day.strftime('%Y%m%d')}-{idx + 1}",
            'time': row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'fullPartial': 'full'
        }
        
        # Process through both FIFO and LIFO
        for method in METHODS:
            realized = process_new_trade(conn, trade, method, 
                                       row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S'))
            
            # Update daily tracking (this now works correctly!)
            realized_qty = sum(r['quantity'] for r in realized)
            realized_pnl_delta = sum(r['realizedPnL'] for r in realized)
            trade_date_str = trading_day.strftime('%Y-%m-%d')
            update_daily_position(conn, trade_date_str, trade['symbol'], method, 
                                realized_qty, realized_pnl_delta)
        
        last_processed_date = trade_date
    
    # Don't forget the last day
    if last_processed_date and last_processed_date in close_prices:
        valuation_dt = datetime.combine(last_processed_date, datetime.min.time()).replace(hour=16, minute=0)
        setup_pricing_as_of(conn, valuation_dt, close_prices, close_prices[last_processed_date], symbol)
        price_dicts = load_pricing_dictionaries(conn)
        update_daily_unrealized_pnl(conn, last_processed_date.strftime('%Y-%m-%d'), price_dicts, symbol)
    
    print(f"Processed {len(all_trades_df)} total trades with day-by-day tracking")
    
    return all_trades_df


def generate_pnl_report(conn, date=None):
    """Generate comprehensive P&L report"""
    results = {}
    
    # Get daily positions
    daily_pos = view_daily_positions(conn, date=date)
    
    for method in METHODS:
        method_pos = daily_pos[daily_pos['method'] == method] if not daily_pos.empty else pd.DataFrame()
        
        # Get realized trades
        realized = view_realized_trades(conn, method)
        
        # Get unrealized positions
        unrealized = view_unrealized_positions(conn, method)
        
        results[method] = {
            'daily_positions': method_pos,
            'realized_trades': realized,
            'unrealized_positions': unrealized,
            'total_realized': realized['realizedPnL'].sum() if not realized.empty else 0,
            'position_count': len(unrealized) if not unrealized.empty else 0
        }
    
    return results


def main():
    """Main entry point for command-line usage"""
    parser = argparse.ArgumentParser(description='PnL Calculation System')
    parser.add_argument('command', choices=['single', 'multi', 'report'], 
                       help='Command to execute')
    parser.add_argument('--csv', help='CSV file path (for single command)')
    parser.add_argument('--folder', help='Folder path containing CSV files (for multi command)')
    parser.add_argument('--date', help='Date for report (YYYY-MM-DD format)')
    parser.add_argument('--db', default=DB_NAME, help='Database file name')
    
    args = parser.parse_args()
    
    # Connect to database
    conn = sqlite3.connect(args.db)
    
    try:
        if args.command == 'single':
            if not args.csv:
                print("Error: --csv required for single command")
                return
            process_single_csv(args.csv, conn)
            
        elif args.command == 'multi':
            if not args.folder:
                print("Error: --folder required for multi command")
                return
            # You can add close prices here or load from a config file
            process_multiple_csvs(args.folder, conn)
            
        elif args.command == 'report':
            report_date = datetime.strptime(args.date, '%Y-%m-%d').date() if args.date else None
            report = generate_pnl_report(conn, date=report_date)
            
            for method, data in report.items():
                print(f"\n=== {method.upper()} Method ===")
                print(f"Total Realized P&L: ${data['total_realized']:.2f}")
                print(f"Open Positions: {data['position_count']}")
                
                if not data['daily_positions'].empty:
                    print("\nDaily Summary:")
                    print(data['daily_positions'])
    
    finally:
        conn.close()


if __name__ == '__main__':
    main() 