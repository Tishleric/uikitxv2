"""
Test Simulation - Verbose P&L Calculation

Purpose: Replicate the full simulation from the notebook with verbose output
to verify the Python module conversion is perfect.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import sys
import os

# Handle direct execution vs module import
if __name__ == '__main__':
    # Direct execution - add parent directories to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    
    # Use absolute imports
    from lib.trading.pnl_fifo_lifo import config
    from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade, calculate_unrealized_pnl, calculate_historical_unrealized_pnl
    from lib.trading.pnl_fifo_lifo.data_manager import (
        create_all_tables, load_csv_to_database, load_multiple_csvs,
        view_unrealized_positions, view_realized_trades, 
        load_pricing_dictionaries, setup_pricing_as_of,
        view_daily_positions, update_daily_position, get_trading_day
    )
    from lib.trading.pnl_fifo_lifo.main import update_daily_unrealized_pnl, process_multiple_csvs
else:
    # Module execution - use relative imports
    from . import config
    from .pnl_engine import process_new_trade, calculate_unrealized_pnl, calculate_historical_unrealized_pnl
    from .data_manager import (
        create_all_tables, load_csv_to_database, load_multiple_csvs,
        view_unrealized_positions, view_realized_trades, 
        load_pricing_dictionaries, setup_pricing_as_of,
        view_daily_positions, update_daily_position, get_trading_day
    )
    from .main import update_daily_unrealized_pnl, process_multiple_csvs

# Enable verbose mode for testing
config.VERBOSE = True

def print_separator(title=""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("="*60)

def run_comprehensive_daily_breakdown():
    """
    Replicate the comprehensive daily P&L breakdown from Cell 23 of the notebook
    """
    print_separator("COMPREHENSIVE DAILY P&L BREAKDOWN")
    
    # Historical close prices (from notebook)
    close_prices = {
        datetime(2025, 7, 21).date(): 111.1875,
        datetime(2025, 7, 22).date(): 111.40625,
        datetime(2025, 7, 23).date(): 111.015625,
        datetime(2025, 7, 24).date(): 110.828125,
        datetime(2025, 7, 25).date(): 110.984375
    }
    
    # Connect to database
    conn = sqlite3.connect(config.DB_NAME)
    
    # Create fresh tables
    print("\nCreating fresh database tables...")
    create_all_tables(conn)
    
    # Process multiple CSVs with daily tracking
    print("\nProcessing trades from data/input/trade_ledger folder...")
    trades_df = process_multiple_csvs('data/input/trade_ledger', conn, close_prices)
    
    if trades_df is None:
        print("ERROR: No trades loaded!")
        conn.close()
        return
    
    # Use the trades DataFrame we already loaded
    trades_csv = trades_df.copy()
    trades_csv['marketTradeTime'] = pd.to_datetime(trades_csv['marketTradeTime'])
    trades_csv['trading_day'] = trades_csv['marketTradeTime'].apply(get_trading_day)
    trades_csv['date'] = trades_csv['trading_day']
    trades_csv = trades_csv.sort_values('marketTradeTime').reset_index(drop=True)
    
    # Generate sequence IDs to match what was stored in database
    trades_csv['date_str'] = trades_csv['trading_day'].apply(lambda d: d.strftime('%Y%m%d'))
    trades_csv['sequenceId'] = [f"{trades_csv.iloc[i]['date_str']}-{i+1}" for i in range(len(trades_csv))]
    
    # Get realized trades from database
    realized_trades = {}
    for method in ['fifo', 'lifo']:
        df = view_realized_trades(conn, method)
        if not df.empty:
            realized_trades[method] = df.set_index('sequenceIdDoingOffsetting')['realizedPnL'].to_dict()
    
    # Calculate daily unrealized P&L
    daily_unrealized = {'fifo': {}, 'lifo': {}}
    cursor = conn.cursor()
    
    # Process all trades sequentially
    last_processed_date = None
    
    for idx, row in trades_csv.iterrows():
        trading_day = row['trading_day']
        trade_date = trading_day
        
        # When we transition to a new day, calculate unrealized for previous day
        if last_processed_date and trade_date != last_processed_date:
            if last_processed_date in close_prices:
                # Set up pricing and calculate unrealized for the completed day
                valuation_dt = datetime.combine(last_processed_date, datetime.min.time()).replace(hour=16, minute=0)
                symbol = 'XCMEFFDPSX20250919U0ZN'
                setup_pricing_as_of(conn, valuation_dt, close_prices, close_prices[last_processed_date], symbol)
                price_dicts = load_pricing_dictionaries(conn)
                
                for method in ['fifo', 'lifo']:
                    # Get unrealized P&L
                    positions = view_unrealized_positions(conn, method)
                    if not positions.empty:
                        unrealized_list = calculate_historical_unrealized_pnl(positions, price_dicts, valuation_dt)
                        unrealized_pnl = sum(u['unrealizedPnL'] for u in unrealized_list)
                    else:
                        unrealized_pnl = 0
                    
                    daily_unrealized[method][last_processed_date] = unrealized_pnl
                    
                    # Update the daily_positions table with correct unrealized P&L
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE daily_positions 
                        SET unrealized_pnl = ?
                        WHERE date = ? AND symbol = ? AND method = ?
                    """, (unrealized_pnl, last_processed_date.strftime('%Y-%m-%d'), symbol, method))
                    conn.commit()
                
                print(f"Processed trades up to {last_processed_date}")
        
        trade = {
            'transactionId': row['tradeId'],
            'symbol': row['instrumentName'],
            'price': row['price'],
            'quantity': row['quantity'],
            'buySell': row['buySell'],
            'sequenceId': row['sequenceId'],
            'time': row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'fullPartial': 'full'
        }
        
        # Process through both FIFO and LIFO
        for method in ['fifo', 'lifo']:
            realized = process_new_trade(conn, trade, method, 
                                       row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S'))
        
        last_processed_date = trade_date
    
    # Don't forget the last day
    if last_processed_date and last_processed_date in close_prices:
        valuation_dt = datetime.combine(last_processed_date, datetime.min.time()).replace(hour=16, minute=0)
        symbol = 'XCMEFFDPSX20250919U0ZN'
        setup_pricing_as_of(conn, valuation_dt, close_prices, close_prices[last_processed_date], symbol)
        price_dicts = load_pricing_dictionaries(conn)
        
        for method in ['fifo', 'lifo']:
            # Get unrealized P&L
            positions = view_unrealized_positions(conn, method)
            if not positions.empty:
                unrealized_list = calculate_historical_unrealized_pnl(positions, price_dicts, valuation_dt)
                unrealized_pnl = sum(u['unrealizedPnL'] for u in unrealized_list)
            else:
                unrealized_pnl = 0
            
            daily_unrealized[method][last_processed_date] = unrealized_pnl
            
            # Update the daily_positions table
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE daily_positions 
                SET unrealized_pnl = ?
                WHERE date = ? AND symbol = ? AND method = ?
            """, (unrealized_pnl, last_processed_date.strftime('%Y-%m-%d'), symbol, method))
            conn.commit()
        
        print(f"Processed trades up to {last_processed_date}")
    
    # Display detailed breakdown by method
    cumulative_totals = {'fifo': 0, 'lifo': 0}  # Track cumulative P&L
    
    for method in ['fifo', 'lifo']:
        print_separator(f"{method.upper()} Method")
        
        running_realized = 0
        prev_total = 0  # Track previous day's total
        
        # Group trades by date
        for date, day_trades in trades_csv.groupby('date'):
            print(f"\n--- {date} ---")
            print(f"{'Time':<15} {'ID':>3} {'Symbol':<25} {'Side':<5} {'Qty':>8} {'Price':>11} {'Real P&L':>10} {'Run Real':>10} {'Unreal':>10} {'Total':>10}")
            print("-" * 105)
            
            # Process each trade
            for _, trade in day_trades.iterrows():
                trade_time = trade['marketTradeTime'].strftime('%H:%M:%S')
                seq_id = trade['sequenceId']
                
                # Get realized P&L for this trade
                realized_pnl = realized_trades.get(method, {}).get(seq_id, 0)
                running_realized += realized_pnl
                
                # Get unrealized P&L for the day
                unrealized_pnl = daily_unrealized.get(method, {}).get(date, 0)
                
                # Calculate total
                total_pnl = running_realized + unrealized_pnl
                
                print(f"{trade_time:<15} {trade['tradeId']:>3} {trade['instrumentName']:<25} "
                      f"{trade['buySell']:<5} {trade['quantity']:>8.6g} {trade['price']:>11.6g} "
                      f"${realized_pnl:>9.6g} ${running_realized:>9.6g} "
                      f"${unrealized_pnl:>9.6g} ${total_pnl:>9.6g}")
            
            # Day summary
            day_realized = sum(realized_trades.get(method, {}).get(
                trade['sequenceId'], 0) 
                for _, trade in day_trades.iterrows())
            day_unrealized = daily_unrealized.get(method, {}).get(date, 0)
            
            # Calculate daily change
            current_total = running_realized + day_unrealized
            daily_change = current_total - prev_total
            prev_total = current_total
            
            print(f"\nEnd of day: Realized=${day_realized:.6g} (day only), Unrealized=${day_unrealized:.6g}, "
                  f"Daily Change=${daily_change:.6g}, Cumulative Total=${current_total:.6g}")
    
    # Final summary
    print_separator("FINAL SUMMARY")
    
    # View final daily positions (already calculated and stored)
    print("\n=== Daily Position Summary ===")
    daily_pos = view_daily_positions(conn)
    if not daily_pos.empty:
        print(daily_pos.to_string())
    else:
        print("No daily positions found")
    
    # Show summary by method
    print("\n=== Daily Summary by Method ===")
    for method in ['fifo', 'lifo']:
        print(f"\n{method.upper()}:")
        method_df = daily_pos[daily_pos['method'] == method][['date', 'open_position', 'closed_position', 'realized_pnl', 'unrealized_pnl']] if not daily_pos.empty else pd.DataFrame()
        if not method_df.empty:
            print(method_df.to_string())
        else:
            print("No data")
    
    conn.close()

def test_single_csv_processing():
    """Test processing a single CSV file"""
    print_separator("SINGLE CSV PROCESSING TEST")
    
    conn = sqlite3.connect(config.DB_NAME)
    create_all_tables(conn)
    
    # Load single CSV
    df, realized_summary = load_csv_to_database('samplestrades.csv', conn, process_new_trade)
    
    print(f"\nLoaded {len(df)} trades")
    print(f"FIFO: {len(realized_summary['fifo'])} realizations")
    print(f"LIFO: {len(realized_summary['lifo'])} realizations")
    
    # Show unrealized positions
    print("\n=== Unrealized Positions ===")
    for method in ['fifo', 'lifo']:
        print(f"\n{method.upper()}:")
        positions = view_unrealized_positions(conn, method)
        if not positions.empty:
            print(positions[['sequenceId', 'symbol', 'buySell', 'quantity', 'price']].to_string())
        else:
            print("No open positions")
    
    # Show realized trades
    print("\n=== Realized Trades (first 10) ===")
    for method in ['fifo', 'lifo']:
        print(f"\n{method.upper()}:")
        realized = view_realized_trades(conn, method)
        if not realized.empty:
            print(realized.head(10)[['sequenceIdDoingOffsetting', 'quantity', 'entryPrice', 'exitPrice', 'realizedPnL']].to_string())
        else:
            print("No realized trades")
    
    conn.close()

def test_pricing_setup():
    """Test pricing setup functionality"""
    print_separator("PRICING SETUP TEST")
    
    conn = sqlite3.connect(config.DB_NAME)
    create_all_tables(conn)
    
    close_prices = {
        datetime(2025, 7, 23).date(): 111.015625,
        datetime(2025, 7, 24).date(): 110.828125,
    }
    
    # Test pricing at different times
    test_times = [
        (datetime(2025, 7, 24, 10, 0, 0), "10:00 AM - Before 2pm"),
        (datetime(2025, 7, 24, 15, 0, 0), "3:00 PM - Between 2-4pm"),
        (datetime(2025, 7, 24, 18, 35, 0), "6:35 PM - After 4pm"),
    ]
    
    for valuation_dt, desc in test_times:
        print(f"\n{desc}:")
        pricing_df = setup_pricing_as_of(conn, valuation_dt, close_prices, 110.828125, 'XCMEFFDPSX20250919U0ZN')
        print(pricing_df.to_string())
    
    conn.close()

def main():
    """Run all tests"""
    print("PnL Calculation System - Test Simulation")
    print("========================================")
    print("This will run the same calculations as the notebook to verify the conversion")
    
    # Test 1: Single CSV processing - COMMENTED OUT (requires samplestrades.csv)
    # test_single_csv_processing()
    
    # Test 2: Pricing setup
    test_pricing_setup()
    
    # Test 3: Comprehensive daily breakdown (main test)
    run_comprehensive_daily_breakdown()
    
    print("\n" + "="*60)
    print("Test simulation complete!")
    print("Compare the output above with the notebook results to verify accuracy.")

if __name__ == '__main__':
    main() 