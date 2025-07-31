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
    from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade, calculate_historical_unrealized_pnl
    from lib.trading.pnl_fifo_lifo.data_manager import (
        create_all_tables,
        view_unrealized_positions, view_realized_trades, 
        load_pricing_dictionaries, setup_pricing_as_of,
        view_daily_positions, get_trading_day
    )
    from lib.trading.pnl_fifo_lifo.main import process_multiple_csvs
else:
    # Module execution - use relative imports
    from . import config
    from .pnl_engine import process_new_trade, calculate_historical_unrealized_pnl
    from .data_manager import (
        create_all_tables,
        view_unrealized_positions, view_realized_trades, 
        load_pricing_dictionaries, setup_pricing_as_of,
        view_daily_positions, get_trading_day
    )
    from .main import process_multiple_csvs

# Enable verbose mode for testing
config.VERBOSE = True

def print_separator(title=""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("="*60)

def run_comprehensive_daily_breakdown(close_prices=None):
    """
    Replicate the comprehensive daily P&L breakdown.
    """
    print_separator("COMPREHENSIVE DAILY P&L BREAKDOWN")
    
    if close_prices is None:
        print("ERROR: No close prices provided for the simulation.")
        return

    conn = sqlite3.connect(config.DB_NAME)
    print("\nCreating fresh database tables...")
    create_all_tables(conn)
    
    print("\nProcessing trades from data/input/trade_ledger folder...")
    trades_df = process_multiple_csvs('data/input/trade_ledger', conn, close_prices)
    
    if trades_df is None:
        print("ERROR: No trades loaded!")
        conn.close()
        return
    
    trades_csv = trades_df.copy()
    trades_csv['marketTradeTime'] = pd.to_datetime(trades_csv['marketTradeTime'])
    trades_csv['trading_day'] = trades_csv['marketTradeTime'].apply(get_trading_day)
    trades_csv['date'] = trades_csv['trading_day']
    trades_csv = trades_csv.sort_values('marketTradeTime').reset_index(drop=True)
    
    trades_csv['date_str'] = trades_csv['trading_day'].apply(lambda d: d.strftime('%Y%m%d'))
    trades_csv['sequenceId'] = [f"{trades_csv.iloc[i]['date_str']}-{i+1}" for i in range(len(trades_csv))]
    
    realized_trades = {}
    for method in ['fifo', 'lifo']:
        df = view_realized_trades(conn, method)
        if not df.empty:
            realized_trades[method] = df.set_index('sequenceIdDoingOffsetting')['realizedPnL'].to_dict()
    
    daily_unrealized = {'fifo': {}, 'lifo': {}}
    prev_day_unrealized = {'fifo': {}, 'lifo': {}}
    cursor = conn.cursor()
    
    last_processed_date = None
    
    # Create a temporary in-memory representation of trades to process
    temp_conn = sqlite3.connect(':memory:')
    create_all_tables(temp_conn)
    
    for idx, row in trades_csv.iterrows():
        trading_day = row['trading_day']
        
        if last_processed_date and trading_day != last_processed_date:
            if last_processed_date in close_prices:
                unique_symbols = set()
                for method in ['fifo', 'lifo']:
                    positions = view_unrealized_positions(temp_conn, method)
                    if not positions.empty:
                        unique_symbols.update(positions['symbol'].unique())

                for symbol in unique_symbols:
                    if symbol not in close_prices[last_processed_date]:
                        continue
                    
                    valuation_dt = datetime.combine(last_processed_date, datetime.min.time()).replace(hour=16, minute=0)
                    setup_pricing_as_of(temp_conn, valuation_dt, close_prices, symbol)
                    price_dicts = load_pricing_dictionaries(temp_conn)
                    
                    for method in ['fifo', 'lifo']:
                        positions = view_unrealized_positions(temp_conn, method, symbol=symbol)
                        unrealized_pnl_cumulative = 0
                        if not positions.empty:
                            unrealized_list = calculate_historical_unrealized_pnl(positions, price_dicts, valuation_dt)
                            unrealized_pnl_cumulative = sum(u['unrealizedPnL'] for u in unrealized_list)
                        
                        if last_processed_date not in daily_unrealized[method]:
                            daily_unrealized[method][last_processed_date] = {}
                        daily_unrealized[method][last_processed_date][symbol] = unrealized_pnl_cumulative
                        
                        prev_unrealized = prev_day_unrealized[method].get(symbol, 0)
                        unrealized_pnl_change = unrealized_pnl_cumulative - prev_unrealized
                        
                        cursor.execute("""
                            UPDATE daily_positions SET unrealized_pnl = ?
                            WHERE date = ? AND symbol = ? AND method = ?
                        """, (unrealized_pnl_change, last_processed_date.strftime('%Y-%m-%d'), symbol, method))

                        prev_day_unrealized[method][symbol] = unrealized_pnl_cumulative
                conn.commit()
        
        trade = {
            'transactionId': row['tradeId'], 'symbol': row['instrumentName'],
            'price': row['price'], 'quantity': row['quantity'],
            'buySell': row['buySell'], 'sequenceId': row['sequenceId'],
            'time': row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'fullPartial': 'full'
        }
        
        for method in ['fifo', 'lifo']:
            process_new_trade(temp_conn, trade, method, row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S'))
        
        last_processed_date = trading_day

    if last_processed_date in close_prices:
        unique_symbols = set()
        for method in ['fifo', 'lifo']:
            positions = view_unrealized_positions(temp_conn, method)
            if not positions.empty:
                unique_symbols.update(positions['symbol'].unique())
        
        for symbol in unique_symbols:
            if symbol not in close_prices[last_processed_date]:
                continue
            
            valuation_dt = datetime.combine(last_processed_date, datetime.min.time()).replace(hour=16, minute=0)
            setup_pricing_as_of(temp_conn, valuation_dt, close_prices, symbol)
            price_dicts = load_pricing_dictionaries(temp_conn)
            
            for method in ['fifo', 'lifo']:
                positions = view_unrealized_positions(temp_conn, method, symbol=symbol)
                unrealized_pnl_cumulative = 0
                if not positions.empty:
                    unrealized_list = calculate_historical_unrealized_pnl(positions, price_dicts, valuation_dt)
                    unrealized_pnl_cumulative = sum(u['unrealizedPnL'] for u in unrealized_list)

                if last_processed_date not in daily_unrealized[method]:
                    daily_unrealized[method][last_processed_date] = {}
                daily_unrealized[method][last_processed_date][symbol] = unrealized_pnl_cumulative
                
                prev_unrealized = prev_day_unrealized[method].get(symbol, 0)
                unrealized_pnl_change = unrealized_pnl_cumulative - prev_unrealized

                cursor.execute("""
                    UPDATE daily_positions SET unrealized_pnl = ?
                    WHERE date = ? AND symbol = ? AND method = ?
                """, (unrealized_pnl_change, last_processed_date.strftime('%Y-%m-%d'), symbol, method))
        conn.commit()

    for method in ['fifo', 'lifo']:
        print_separator(f"{method.upper()} Method")
        prev_day_unrealized_pnl = 0
        
        for date, day_trades in trades_csv.groupby('date'):
            print(f"\n--- {date} ---")
            print(f"{'Time':<15} {'ID':>3} {'Symbol':<25} {'Side':<5} {'Qty':>8} {'Price':>11} {'Real P&L':>10} {'Day Real':>10} {'Unreal EOD':>11} {'Day Total':>11}")
            print("-" * 118)
            
            daily_running_realized = 0
            day_unrealized_data = daily_unrealized.get(method, {}).get(date, {})
            current_day_unrealized_pnl = sum(day_unrealized_data.values()) if isinstance(day_unrealized_data, dict) else 0

            for _, trade in day_trades.iterrows():
                realized_pnl_for_trade = realized_trades.get(method, {}).get(trade['sequenceId'], 0)
                daily_running_realized += realized_pnl_for_trade
                day_total_pnl = daily_running_realized + current_day_unrealized_pnl

                print(f"{trade['marketTradeTime'].strftime('%H:%M:%S'):<15} {trade['tradeId']:>3} {trade['instrumentName']:<25} "
                      f"{trade['buySell']:<5} {trade['quantity']:>8.g} {trade['price']:>11.6g} "
                      f"${realized_pnl_for_trade:>9.6g} ${daily_running_realized:>9.6g} "
                      f"${current_day_unrealized_pnl:>10.6g} ${day_total_pnl:>10.6g}")
            
            day_realized_total = daily_running_realized
            unrealized_pnl_change = current_day_unrealized_pnl - prev_day_unrealized_pnl
            total_daily_pnl = day_realized_total + unrealized_pnl_change
            
            print(f"\nEnd of day: Daily Realized=${day_realized_total:.6g}, Daily Unrealized=${unrealized_pnl_change:.6g}, Total Daily P&L=${total_daily_pnl:.6g}")
            prev_day_unrealized_pnl = current_day_unrealized_pnl
    
    print_separator("FINAL SUMMARY")
    print("\n=== Daily Position Summary ===")
    daily_pos = view_daily_positions(conn)
    if not daily_pos.empty:
        print(daily_pos.to_string())
    else:
        print("No daily positions found")
    
    conn.close()
    temp_conn.close()

def main():
    """Run all tests"""
    print("PnL Calculation System - Test Simulation")
    print("========================================")
    
    symbol = 'XCMEFFDPSX20250919U0ZN'
    close_prices = {
        datetime(2025, 7, 21).date(): {symbol: 111.1875},
        datetime(2025, 7, 22).date(): {symbol: 111.40625},
        datetime(2025, 7, 23).date(): {symbol: 111.015625},
        datetime(2025, 7, 24).date(): {symbol: 110.828125},
        datetime(2025, 7, 25).date(): {symbol: 110.984375},
        datetime(2025, 7, 28).date(): {symbol: 110.765625},
        datetime(2025, 7, 29).date(): {symbol: 111.359375},
    }

    run_comprehensive_daily_breakdown(close_prices=close_prices)
    
    print("\n" + "="*60)
    print("Test simulation complete!")

if __name__ == '__main__':
    main()
