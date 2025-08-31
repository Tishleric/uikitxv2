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

def main(preserve_processed_files=False):
    """Main execution function.
    
    Args:
        preserve_processed_files: If True, skip dropping the processed_files table
    """
    print("--- Starting Historical P&L Rebuild ---")

    # --- Phase 1: Setup and Data Loading ---
    print("\n[Phase 1/6] Initializing and loading data...")

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
            '1MQ5C 111.75 Comdty': 0.0625  # Placeholder from 7/30
        },
        datetime(2025, 7, 30).date(): {
            symbol_futures: 111.0,  # TYU5 close
            '1MQ5C 111.75 Comdty': 0.171875  # Option close price
        },
        datetime(2025, 7, 31).date(): {
            symbol_futures: 111.0625,
            '1MQ5C 111.75 Comdty': 0.03125,
            'TJPQ25P1 110.5 Comdty': 0.09375
        },
        datetime(2025, 8, 1).date(): {
            symbol_futures: 112.203125,  # TYU5 close
            'USU5 Comdty': 115.687500,  # USU5 close
            '1MQ5C 111.75 Comdty': 0.453125,
            'TJPQ25P1 110.75 Comdty': 0.001,
            'TYWQ25C1 112.75 Comdty': 0.078125,
            'TYWQ25C1 112.5 Comdty': 0.140625,
            'TYWQ25C1 112.25 Comdty': 0.234375,
            'TJWQ25C1 112.5 Comdty': 0.171875  # This is XCMEOCADPS20250807Q0HY1/112.5
        },
        datetime(2025, 8, 4).date(): {
            symbol_futures: 112.375,  # TYU5 close
            'USU5 Comdty': 115.9063,  # USU5 close
            '2MQ5C 112.5 Comdty': 0.25,
            '2MQ5C 112.75 Comdty': 0.15625,
            'TJPQ25P1 110.5 Comdty': 0.00100000016391277,
            'TJWQ25C1 112.5 Comdty': 0.203125,
            'TYWQ25C1 112.75 Comdty': 0.09375,
            'TYWQ25C1 112.5 Comdty': 0.171875,
            'TYWQ25C1 112.25 Comdty': 0.296875
        },
        datetime(2025, 8, 5).date(): {
            symbol_futures: 112.296875,  # TYU5 close
            'USU5 Comdty': 116.125,  # USU5 close
            '2MQ5C 112.5 Comdty': 0.125,
            '2MQ5C 112.75 Comdty': 0.0625,
            'TJPQ25P1 110.5 Comdty': 0.006999999,
            'TJWQ25C1 112.5 Comdty': 0.09375,
            'TJWQ25C1 113.25 Comdty': 0.0156,
            'TYWQ25C1 112.25 Comdty': 0.140625,
            'TYWQ25C1 112.5 Comdty': 0.046875,
            'TYWQ25C1 112.75 Comdty': 0.015625
        },
        datetime(2025, 8, 6).date(): {
            symbol_futures: 112.234375,  # TYU5 close
            'USU5 Comdty': 115.5625,  # USU5 close
            '2MQ5C 112.5 Comdty': 0.0625,
            '2MQ5C 112.75 Comdty': 0.03125,
            'TJWQ25C1 112.5 Comdty': 0.03125,
            'TJWQ25C1 113.25 Comdty': 0,
            'TYWQ25C1 112.75 Comdty': 0.006999999
        },
        datetime(2025, 8, 7).date(): {
            symbol_futures: 112.09375,  # TYU5 close
            'USU5 Comdty': 115.53125,  # USU5 close
            '2MQ5C 112.75 Comdty': 0.001,
            '2MQ5C 112.25 Comdty': 0.03125,
            'TJWQ25C1 112.5 Comdty': 0,
            'TJWQ25C1 113.25 Comdty': 0
        },
        datetime(2025, 8, 8).date(): {
            symbol_futures: 111.828125,  # TYU5 close
            'USU5 Comdty': 115.0,       # USU5 close
            '2MQ5C 112.25 Comdty': 0,
            '2MQ5C 112.75 Comdty': 0
        },
        datetime(2025, 8, 11).date(): {
            symbol_futures: 111.890625,  
            'USU5 Comdty': 115.15625,       
        },
        datetime(2025, 8, 12).date(): {
            symbol_futures: 111.8125,  
            'USU5 Comdty': 114.65625,       
        },
        datetime(2025, 8, 13).date(): {
            symbol_futures: 112.171875,  
            'USU5 Comdty': 115.5,       
        },
        datetime(2025, 8, 14).date(): {
            symbol_futures: 111.796875,  
            'USU5 Comdty': 114.65625,
            'FVU5 Comdty': 108.7734375,
            'TUU5 Comdty': 103.8671875,
        },
        datetime(2025, 8, 15).date(): {
            symbol_futures: 111.59375,  
            'USU5 Comdty': 114,
            'FVU5 Comdty': 108.6796875,
            'TUU5 Comdty': 103.8203125,
        },
        datetime(2025, 8, 18).date(): {
            symbol_futures: 111.515625,  
            'USU5 Comdty': 113.78125,
            'FVU5 Comdty': 108.625,
            'TUU5 Comdty': 103.7890625,
        },
        datetime(2025, 8, 19).date(): {
            symbol_futures: 111.765625,  
            'USU5 Comdty': 114.34375,
            'FVU5 Comdty': 108.75,
            'TUU5 Comdty': 103.8203125,
        },
        datetime(2025, 8, 20).date(): {
            symbol_futures: 111.859375,  
            'USU5 Comdty': 114.40625,
            'FVU5 Comdty': 108.8125,
            'TUU5 Comdty': 103.839843375,
        },
        datetime(2025, 8, 21).date(): {
            symbol_futures: 111.53125,
        },
        datetime(2025, 8, 22).date(): {
            symbol_futures: 112.140625,  
            'USU5 Comdty': 114.84375,
            'FVU5 Comdty': 109.046875,
            'TUU5 Comdty': 103.94140625,
        },
        datetime(2025, 8, 25).date(): {
            symbol_futures: 111.96875,  
            'USU5 Comdty': 114.71875,
            'FVU5 Comdty': 108.90625,
            'TUU5 Comdty': 103.85546875,
        },
        datetime(2025, 8, 26).date(): {
            symbol_futures: 112.203125,  
            'USU5 Comdty': 114.59375,
            'FVU5 Comdty': 109.125,
        },
        datetime(2025, 8, 27).date(): {
            symbol_futures: 112.40625,  
            'USU5 Comdty': 114.625,
            'TYZ5 Comdty': 112.4375,
            'USZ5 Comdty': 114.25,
        },
        datetime(2025, 8, 28).date(): {  
            'USZ5 Comdty': 114.8125,
            'TYZ5 Comdty': 112.59375,
            'FVZ5 Comdty': 109.4765625,
        },
        datetime(2025, 8, 29).date(): {  
            'USZ5 Comdty': 114.25,
            'TYZ5 Comdty': 112.5,
            'FVZ5 Comdty': 109.46875,
            'TUZ5 Comdty': 104.26953125,
        },
    }

    # Wipe and recreate all database tables
    conn = sqlite3.connect(config.DB_NAME, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")  # Ensure WAL mode for better concurrency
    print("  - Wiping and recreating database tables...")
    create_all_tables(conn, preserve_processed_files=preserve_processed_files)

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
        # Handle NaN or non-string values
        if pd.isna(symbol) or not isinstance(symbol, str):
            return symbol
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

    # All trades will be treated as historical.
    historical_df = trades_df.copy()
    print(f"  - Processing all {len(historical_df)} trades as historical.")
    
    # --- Phase 2: Chronological P&L Calculation for Historical Data ---
    print("\n[Phase 2/6] Processing historical trades chronologically and calculating daily P&L...")
    
    last_processed_date = None
    
    # Track daily closed positions per-symbol (not cumulative across symbols)
    daily_closed_positions = {'fifo': {}, 'lifo': {}}
    
    # Get a cursor for EOD updates
    cursor = conn.cursor()

    for idx, row in historical_df.iterrows():
        trading_day = row['trading_day']
        
        # EOD Process: When the trading day changes, process the day that just ended.
        if last_processed_date and trading_day != last_processed_date:
            print(f"  - Running EOD process for {last_processed_date}...")
            
            # Initialize per-symbol tracking for the new day
            for method in ['fifo', 'lifo']:
                daily_closed_positions[method][trading_day] = {}
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
                                # Simple P&L: (settle - cost_basis) * qty
                                pnl = (settle_price - pos['price']) * pos['quantity'] * config.get_pnl_multiplier(symbol)
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
                        # Use INSERT OR REPLACE to handle both existing and new records
                        cursor.execute("""
                            INSERT OR REPLACE INTO daily_positions 
                            (date, symbol, method, open_position, closed_position, realized_pnl, unrealized_pnl, timestamp)
                            VALUES (?, ?, ?, ?, 
                                COALESCE((SELECT closed_position FROM daily_positions WHERE date = ? AND symbol = ? AND method = ?), 0),
                                COALESCE((SELECT realized_pnl FROM daily_positions WHERE date = ? AND symbol = ? AND method = ?), 0),
                                ?, ?)
                        """, (last_processed_date.strftime('%Y-%m-%d'), symbol, method, open_position,
                              last_processed_date.strftime('%Y-%m-%d'), symbol, method,
                              last_processed_date.strftime('%Y-%m-%d'), symbol, method,
                              total_unrealized_pnl, last_processed_date.strftime('%Y-%m-%d') + ' 16:00:00'))
                        
                        # Mark-to-market: Update all open positions to settle price
                        cursor.execute(f"""
                            UPDATE trades_{method}
                            SET price = ?, time = ?
                            WHERE symbol = ? AND quantity > 0
                        """, (settle_price, last_processed_date.strftime('%Y-%m-%d') + ' 16:00:00.000', symbol))
                        
                conn.commit()

        # Initialize daily tracking for this trading day if not exists
        for method in ['fifo', 'lifo']:
            if trading_day not in daily_closed_positions[method]:
                daily_closed_positions[method][trading_day] = {}
        
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
                
                # Track daily closed positions per-symbol
                symbol = trade['symbol']
                if symbol not in daily_closed_positions[method][trading_day]:
                    daily_closed_positions[method][trading_day][symbol] = {'quantity': 0, 'pnl': 0}
                
                daily_closed_positions[method][trading_day][symbol]['quantity'] += realized_qty
                daily_closed_positions[method][trading_day][symbol]['pnl'] += realized_pnl_delta
                
                # Update with per-symbol values
                # Only update if we have realized trades (don't create empty records)
                if realized_trades:
                    update_daily_position(conn, trading_day.strftime('%Y-%m-%d'), symbol, method, 
                                        daily_closed_positions[method][trading_day][symbol]['quantity'], 
                                        daily_closed_positions[method][trading_day][symbol]['pnl'], 
                                        accumulate=False)
        
        last_processed_date = trading_day

    # Final EOD process for the very last day of trades
    print(f"  - Running final EOD process for {last_processed_date}...")
    if last_processed_date in close_prices:
        unique_symbols = pd.read_sql_query("SELECT DISTINCT symbol FROM trades_fifo WHERE quantity > 0", conn)['symbol'].tolist()
        print(f"    DEBUG: Open positions found for symbols: {unique_symbols}")
        print(f"    DEBUG: Close prices available for {last_processed_date}: {list(close_prices[last_processed_date].keys())}")
        for symbol in unique_symbols:
            settle_price = close_prices.get(last_processed_date, {}).get(symbol)
            if not settle_price:
                print(f"    DEBUG: No settle price found for symbol '{symbol}' on {last_processed_date}")
                continue
            print(f"    DEBUG: Processing {symbol} with settle price {settle_price}")
                
            for method in ['fifo', 'lifo']:
                # Calculate total unrealized P&L using current cost basis
                positions = view_unrealized_positions(conn, method, symbol=symbol)
                total_unrealized_pnl = 0
                
                if not positions.empty:
                    print(f"      DEBUG {method}: Found {len(positions)} open positions for {symbol}")
                    for _, pos in positions.iterrows():
                        # Simple P&L: (settle - cost_basis) * qty
                        pnl = (settle_price - pos['price']) * pos['quantity'] * config.get_pnl_multiplier(symbol)
                        if pos['buySell'] == 'S':  # Short positions have inverted P&L
                            pnl = -pnl
                        total_unrealized_pnl += pnl
                        print(f"        Position: qty={pos['quantity']}, price={pos['price']}, settle={settle_price}, pnl={pnl}")
                else:
                    print(f"      DEBUG {method}: No open positions found for {symbol}")
                
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
                # First check if a record exists
                existing = cursor.execute("""
                    SELECT 1 FROM daily_positions 
                    WHERE date = ? AND symbol = ? AND method = ?
                """, (last_processed_date.strftime('%Y-%m-%d'), symbol, method)).fetchone()
                
                if existing:
                    # Update existing record - this ensures we overwrite any records created during trade processing
                    cursor.execute("""
                        UPDATE daily_positions 
                        SET unrealized_pnl = ?, open_position = ?, timestamp = ?
                        WHERE date = ? AND symbol = ? AND method = ?
                    """, (total_unrealized_pnl, open_position,
                          last_processed_date.strftime('%Y-%m-%d') + ' 16:00:00',
                          last_processed_date.strftime('%Y-%m-%d'), symbol, method))
                else:
                    # Insert new record if none exists
                    cursor.execute("""
                        INSERT INTO daily_positions 
                        (date, symbol, method, open_position, closed_position, realized_pnl, unrealized_pnl, timestamp)
                        VALUES (?, ?, ?, ?, 0, 0, ?, ?)
                    """, (last_processed_date.strftime('%Y-%m-%d'), symbol, method, open_position,
                          total_unrealized_pnl, last_processed_date.strftime('%Y-%m-%d') + ' 16:00:00'))
                
                # Mark-to-market: Update all open positions to settle price
                cursor.execute(f"""
                    UPDATE trades_{method}
                    SET price = ?, time = ?
                    WHERE symbol = ? AND quantity > 0
                """, (settle_price, last_processed_date.strftime('%Y-%m-%d') + ' 16:00:00.000', symbol))
                
        conn.commit()
    
    # Populate pricing table with all close prices before running aggregator
    print("\n  - Populating pricing table with close prices...")
    for date, prices in close_prices.items():
        for symbol, price in prices.items():
            cursor.execute("""
                INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
                VALUES (?, 'close', ?, ?)
            """, (symbol, price, date.strftime('%Y-%m-%d') + ' 16:00:00'))
    conn.commit()
    print(f"  - Inserted {sum(len(prices) for prices in close_prices.values())} close prices into pricing table")
    
    # Add last day's close prices as sodTod prices
    print("\n  - Adding last day's close prices as sodTod...")
    last_trading_date = max(close_prices.keys())
    last_day_prices = close_prices[last_trading_date]
    sodtod_count = 0
    
    for symbol, price in last_day_prices.items():
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'sodTod', ?, ?)
        """, (symbol, price, last_trading_date.strftime('%Y-%m-%d') + ' 06:00:00'))
        sodtod_count += 1
    
    conn.commit()
    print(f"  - Inserted {sodtod_count} sodTod prices from {last_trading_date.strftime('%Y-%m-%d')}")
        
    # Close connection before aggregator runs to avoid lock
    conn.close()

    # --- Phase 5: Final Aggregation ---
    print("\n[Phase 5/6] Aggregating final positions...")
    aggregator = PositionsAggregator(trades_db_path=config.DB_NAME)
    aggregator._load_positions_from_db()
    # Pass the loaded positions cache to the write method
    aggregator._write_positions_to_db(aggregator.positions_cache)
    print("  - Final `positions` table has been populated.")

    # --- Phase 6: Verification ---
    print("\n[Phase 6/6] Verification...")
    # Reopen connection for verification
    conn = sqlite3.connect(config.DB_NAME)
    print("\n--- Final 'daily_positions' Table ---")
    daily_df = view_daily_positions(conn)
    print(daily_df.to_string())

    print("\n--- Final 'positions' Table (Summary) ---")
    pos_df = pd.read_sql_query("SELECT symbol, open_position, closed_position, fifo_realized_pnl, fifo_unrealized_pnl FROM positions", conn)
    print(pos_df.to_string())
    
    conn.close()
    print("\n--- Historical P&L Rebuild Complete ---")

if __name__ == '__main__':
    # For production: preserve the processed_files table
    main(preserve_processed_files=True)
