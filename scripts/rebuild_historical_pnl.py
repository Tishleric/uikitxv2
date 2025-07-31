"""
Standalone script to perform a complete historical P&L rebuild.

This script wipes the database, processes all historical trades with symbol
translation, applies historical close prices, and correctly calculates and
stores daily (non-cumulative) P&L values.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import sys
import os
import glob

# Add project root to path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.trading.pnl_fifo_lifo import config
from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade, calculate_historical_unrealized_pnl
from lib.trading.pnl_fifo_lifo.data_manager import (
    create_all_tables,
    view_unrealized_positions,
    load_pricing_dictionaries,
    setup_pricing_as_of,
    get_trading_day,
    update_daily_position,
    view_daily_positions
)
from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator
from lib.trading.market_prices.rosetta_stone import RosettaStone

def main():
    """Main execution function."""
    print("--- Starting Historical P&L Rebuild ---")

    # --- Phase 1: Setup and Data Loading ---
    print("\n[Phase 1/4] Initializing and loading data...")

    # Define the historical close prices as provided
    symbol_futures = 'TYU5 Comdty' # The expected bloomberg symbol for the futures
    close_prices = {
        datetime(2025, 7, 21).date(): {symbol_futures: 111.1875},
        datetime(2025, 7, 22).date(): {symbol_futures: 111.40625},
        datetime(2025, 7, 23).date(): {symbol_futures: 111.015625},
        datetime(2025, 7, 24).date(): {symbol_futures: 110.828125},
        datetime(2025, 7, 25).date(): {symbol_futures: 110.984375},
        datetime(2025, 7, 28).date(): {symbol_futures: 110.765625},
        datetime(2025, 7, 29).date(): {
            symbol_futures: 111.359375,
            '1MQ5P 111.75 Comdty': 1.03125  # Added new option closing price
        },
        datetime(2025, 7, 30).date(): {
            symbol_futures: 111.0,  # TYU5 close
            '1MQ5C 111.75 Comdty': 0.00100000016391277  # Option close price
        },
    }

    # Wipe and recreate all database tables
    conn = sqlite3.connect(config.DB_NAME)
    print("  - Wiping and recreating database tables...")
    create_all_tables(conn)

    # Load all trade CSVs from the trade_ledger directory
    trade_folder = 'data/input/trade_ledger'
    all_trade_files = sorted(glob.glob(os.path.join(trade_folder, 'trades_*.csv')))
    if not all_trade_files:
        print(f"  - ERROR: No trade CSVs found in {trade_folder}")
        conn.close()
        return
    
    print(f"  - Loading {len(all_trade_files)} trade files...")
    
    # Load each CSV file with error handling
    trade_dfs = []
    for file_path in all_trade_files:
        try:
            df = pd.read_csv(file_path)
            trade_dfs.append(df)
            print(f"    Loaded {len(df)} trades from {os.path.basename(file_path)}")
        except pd.errors.ParserError as e:
            print(f"    WARNING: Error parsing {os.path.basename(file_path)}: {e}")
            # Try loading with error handling
            try:
                df = pd.read_csv(file_path, on_bad_lines='skip')
                trade_dfs.append(df)
                print(f"    Loaded {len(df)} trades from {os.path.basename(file_path)} (skipped bad lines)")
            except Exception as e2:
                print(f"    ERROR: Could not load {os.path.basename(file_path)}: {e2}")
                continue
    
    if not trade_dfs:
        print("  - ERROR: No trades loaded successfully")
        conn.close()
        return
        
    trades_df = pd.concat(trade_dfs, ignore_index=True)

    # Translate symbols using RosettaStone
    print("  - Translating symbols from 'actanttrades' to 'bloomberg'...")
    translator = RosettaStone()
    def translate_symbol(symbol):
        translated = translator.translate(symbol, 'actanttrades', 'bloomberg')
        if not translated:
            print(f"    WARNING: Failed to translate symbol: {symbol}")
            return symbol  # Fallback to original
        return translated
    
    trades_df['bloomberg_symbol'] = trades_df['instrumentName'].apply(translate_symbol)
    
    # Debug: Show symbol translation for options
    option_trades = trades_df[trades_df['instrumentName'].str.contains('OCAD|OPAD')]
    if not option_trades.empty:
        print(f"  - Option symbol translations:")
        for _, row in option_trades.iterrows():
            print(f"    {row['instrumentName']} -> {row['bloomberg_symbol']}")

    # Prepare and sort the master DataFrame
    # Handle mixed datetime formats (some with microseconds, some without)
    try:
        # Try format='mixed' first (newer pandas versions)
        trades_df['marketTradeTime'] = pd.to_datetime(trades_df['marketTradeTime'], format='mixed')
    except (ValueError, TypeError):
        # Fallback: Standardize timestamps by adding .000000 to those without microseconds
        def standardize_timestamp(ts):
            ts_str = str(ts)
            if '.' not in ts_str and len(ts_str) == 19:  # Format: YYYY-MM-DD HH:MM:SS
                return ts_str + '.000000'
            return ts_str
        
        trades_df['marketTradeTime'] = trades_df['marketTradeTime'].apply(standardize_timestamp)
        trades_df['marketTradeTime'] = pd.to_datetime(trades_df['marketTradeTime'])
    trades_df.sort_values('marketTradeTime', inplace=True)
    trades_df.reset_index(drop=True, inplace=True)
    trades_df['trading_day'] = trades_df['marketTradeTime'].apply(get_trading_day)
    trades_df['date_str'] = trades_df['trading_day'].apply(lambda d: d.strftime('%Y%m%d'))
    trades_df['sequenceId'] = [f"{trades_df.iloc[i]['date_str']}-{i+1}" for i in range(len(trades_df))]
    print(f"  - Loaded and sorted a total of {len(trades_df)} trades.")

    # --- Phase 2: Chronological P&L Calculation ---
    print("\n[Phase 2/4] Processing trades chronologically and calculating daily P&L...")
    
    last_processed_date = None
    
    # Track daily closed positions separately (not cumulative)
    daily_closed_positions = {'fifo': {}, 'lifo': {}}
    
    # Get a cursor for EOD updates
    cursor = conn.cursor()

    for idx, row in trades_df.iterrows():
        trading_day = row['trading_day']
        
        # EOD Process: When the trading day changes, process the day that just ended.
        if last_processed_date and trading_day != last_processed_date:
            print(f"  - Running EOD process for {last_processed_date}...")
            
            # Reset daily closed positions for the new day
            for method in ['fifo', 'lifo']:
                daily_closed_positions[method][trading_day] = {'quantity': 0, 'pnl': 0}
            if last_processed_date in close_prices:
                unique_symbols = pd.read_sql_query("SELECT DISTINCT symbol FROM trades_fifo WHERE quantity > 0", conn)['symbol'].tolist()

                for symbol in unique_symbols:
                    settle_price = close_prices.get(last_processed_date, {}).get(symbol)
                    if not settle_price:
                        continue

                    for method in ['fifo', 'lifo']:
                        # Calculate total unrealized P&L using current cost basis
                        positions = view_unrealized_positions(conn, method, symbol=symbol)
                        total_unrealized_pnl = 0
                        
                        if not positions.empty:
                            for _, pos in positions.iterrows():
                                # Simple P&L: (settle - cost_basis) * qty * 1000
                                pnl = (settle_price - pos['price']) * pos['quantity'] * 1000
                                if pos['buySell'] == 'S':  # Short positions have inverted P&L
                                    pnl = -pnl
                                total_unrealized_pnl += pnl
                        
                        # Get current open position at end of day
                        open_query = f"""
                            SELECT 
                                SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END) as net_position
                            FROM trades_{method}
                            WHERE symbol = ? AND quantity > 0
                        """
                        result = cursor.execute(open_query, (symbol,)).fetchone()
                        open_position = result[0] if result[0] else 0
                        
                        # Store the TOTAL unrealized P&L (not the change)
                        cursor.execute("""
                            UPDATE daily_positions 
                            SET unrealized_pnl = ?, open_position = ?, timestamp = ?
                            WHERE date = ? AND symbol = ? AND method = ?
                        """, (total_unrealized_pnl, open_position, 
                              last_processed_date.strftime('%Y-%m-%d') + ' 16:00:00',
                              last_processed_date.strftime('%Y-%m-%d'), symbol, method))
                        
                        # Mark-to-market: Update all open positions to settle price
                        cursor.execute(f"""
                            UPDATE trades_{method}
                            SET price = ?, time = ?
                            WHERE symbol = ? AND quantity > 0
                        """, (settle_price, last_processed_date.strftime('%Y-%m-%d') + ' 16:00:00', symbol))
                        
                conn.commit()

        # Initialize daily tracking for this trading day if not exists
        for method in ['fifo', 'lifo']:
            if trading_day not in daily_closed_positions[method]:
                daily_closed_positions[method][trading_day] = {'quantity': 0, 'pnl': 0}
        
        # Process the current trade
        trade = {
            'transactionId': row['tradeId'], 'symbol': row['bloomberg_symbol'],
            'price': row['price'], 'quantity': row['quantity'],
            'buySell': row['buySell'], 'sequenceId': row['sequenceId'],
            'time': row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'fullPartial': 'full'
        }
        
        for method in ['fifo', 'lifo']:
            realized_trades = process_new_trade(conn, trade, method, row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S'))
            if realized_trades:
                realized_qty = sum(r['quantity'] for r in realized_trades)
                realized_pnl_delta = sum(r['realizedPnL'] for r in realized_trades)
                
                # Track daily closed positions (not cumulative)
                daily_closed_positions[method][trading_day]['quantity'] += realized_qty
                daily_closed_positions[method][trading_day]['pnl'] += realized_pnl_delta
                
                # Update with daily values, not cumulative
                update_daily_position(conn, trading_day.strftime('%Y-%m-%d'), trade['symbol'], method, 
                                    daily_closed_positions[method][trading_day]['quantity'], 
                                    daily_closed_positions[method][trading_day]['pnl'])
        
        last_processed_date = trading_day

    # Final EOD process for the very last day of trades
    print(f"  - Running final EOD process for {last_processed_date}...")
    if last_processed_date in close_prices:
        unique_symbols = pd.read_sql_query("SELECT DISTINCT symbol FROM trades_fifo WHERE quantity > 0", conn)['symbol'].tolist()
        for symbol in unique_symbols:
            settle_price = close_prices.get(last_processed_date, {}).get(symbol)
            if not settle_price:
                continue
                
            for method in ['fifo', 'lifo']:
                # Calculate total unrealized P&L using current cost basis
                positions = view_unrealized_positions(conn, method, symbol=symbol)
                total_unrealized_pnl = 0
                
                if not positions.empty:
                    for _, pos in positions.iterrows():
                        # Simple P&L: (settle - cost_basis) * qty * 1000
                        pnl = (settle_price - pos['price']) * pos['quantity'] * 1000
                        if pos['buySell'] == 'S':  # Short positions have inverted P&L
                            pnl = -pnl
                        total_unrealized_pnl += pnl
                
                # Get current open position at end of day
                open_query = f"""
                    SELECT 
                        SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END) as net_position
                    FROM trades_{method}
                    WHERE symbol = ? AND quantity > 0
                """
                result = cursor.execute(open_query, (symbol,)).fetchone()
                open_position = result[0] if result[0] else 0
                
                # Store the TOTAL unrealized P&L (not the change)
                cursor.execute("""
                    UPDATE daily_positions 
                    SET unrealized_pnl = ?, open_position = ?, timestamp = ?
                    WHERE date = ? AND symbol = ? AND method = ?
                """, (total_unrealized_pnl, open_position,
                      last_processed_date.strftime('%Y-%m-%d') + ' 16:00:00',
                      last_processed_date.strftime('%Y-%m-%d'), symbol, method))
                
                # Mark-to-market: Update all open positions to settle price
                cursor.execute(f"""
                    UPDATE trades_{method}
                    SET price = ?, time = ?
                    WHERE symbol = ? AND quantity > 0
                """, (settle_price, last_processed_date.strftime('%Y-%m-%d') + ' 16:00:00', symbol))
                
        conn.commit()

    # --- Phase 3: Final Aggregation ---
    print("\n[Phase 3/4] Aggregating final positions...")
    aggregator = PositionsAggregator(trades_db_path=config.DB_NAME)
    aggregator._load_positions_from_db()
    aggregator._write_positions_to_db()
    print("  - Final `positions` table has been populated.")

    # --- Phase 4: Verification ---
    print("\n[Phase 4/4] Verification...")
    print("\n--- Final 'daily_positions' Table ---")
    daily_df = view_daily_positions(conn)
    print(daily_df.to_string())

    print("\n--- Final 'positions' Table (Summary) ---")
    pos_df = pd.read_sql_query("SELECT symbol, open_position, closed_position, fifo_realized_pnl, fifo_unrealized_pnl FROM positions", conn)
    print(pos_df.to_string())
    
    conn.close()
    print("\n--- Historical P&L Rebuild Complete ---")

if __name__ == '__main__':
    main()
