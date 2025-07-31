"""
Data Management Module

Purpose: Database operations, CSV loading, pricing management, and data queries
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import os
import re
from glob import glob
from .config import DEFAULT_SYMBOL, ALL_TABLES, METHODS

def create_all_tables(conn):
    """Create all required tables for PnL tracking"""
    cursor = conn.cursor()
    
    # Schema for unrealized trades (FIFO and LIFO versions)
    trades_schema = """(
        transactionId INTEGER,
        symbol TEXT,
        price REAL,
        original_price REAL,
        quantity REAL,
        buySell TEXT,
        sequenceId TEXT PRIMARY KEY,
        time TEXT,
        original_time TEXT,
        fullPartial TEXT DEFAULT 'full'
    )"""
    
    # Schema for realized positions
    realized_schema = """(
        symbol TEXT,
        sequenceIdBeingOffset TEXT,
        sequenceIdDoingOffsetting TEXT,
        partialFull TEXT,
        quantity REAL,
        entryPrice REAL,
        exitPrice REAL,
        realizedPnL REAL,
        timestamp TEXT
    )"""
    
    # Create unrealized trade tables
    for suffix in ['fifo', 'lifo']:
        cursor.execute(f"DROP TABLE IF EXISTS trades_{suffix}")
        cursor.execute(f"CREATE TABLE trades_{suffix} {trades_schema}")
        
    # Create realized position tables  
    for suffix in ['fifo', 'lifo']:
        cursor.execute(f"DROP TABLE IF EXISTS realized_{suffix}")
        cursor.execute(f"CREATE TABLE realized_{suffix} {realized_schema}")
    
    # Create pricing table
    cursor.execute("DROP TABLE IF EXISTS pricing")
    pricing_schema = """
    CREATE TABLE pricing (
        symbol TEXT,
        price_type TEXT,
        price REAL,
        timestamp TEXT,
        PRIMARY KEY (symbol, price_type)
    )
    """
    cursor.execute(pricing_schema)
    
    # Create daily positions table
    cursor.execute("DROP TABLE IF EXISTS daily_positions")
    daily_positions_schema = """
    CREATE TABLE daily_positions (
        date DATE,
        symbol TEXT,
        method TEXT,
        open_position REAL,
        closed_position INTEGER,
        realized_pnl REAL,
        unrealized_pnl REAL,
        timestamp TEXT,
        PRIMARY KEY (date, symbol, method)
    )
    """
    cursor.execute(daily_positions_schema)
    
    # Create processed files tracking table
    cursor.execute("DROP TABLE IF EXISTS processed_files")
    processed_files_schema = """
    CREATE TABLE processed_files (
        file_path TEXT PRIMARY KEY,
        processed_at TEXT,
        trade_count INTEGER,
        last_modified REAL
    )
    """
    cursor.execute(processed_files_schema)
    
    # Create positions master table
    positions_schema = """
    CREATE TABLE IF NOT EXISTS positions (
        symbol TEXT PRIMARY KEY,
        open_position REAL DEFAULT 0,
        closed_position REAL DEFAULT 0,
        delta_y REAL,
        gamma_y REAL,
        speed_y REAL,
        theta REAL,
        vega REAL,
        fifo_realized_pnl REAL DEFAULT 0,
        fifo_unrealized_pnl REAL DEFAULT 0,
        lifo_realized_pnl REAL DEFAULT 0,
        lifo_unrealized_pnl REAL DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_trade_update TIMESTAMP,
        last_greek_update TIMESTAMP,
        has_greeks BOOLEAN DEFAULT 0,
        instrument_type TEXT
    )
    """
    cursor.execute(positions_schema)
    
    # Create indexes for positions table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_updated ON positions(last_updated)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_type ON positions(instrument_type)")
    
    conn.commit()


def get_trading_day(timestamp):
    """
    Get the trading day for a given timestamp.
    Trading day runs from 5pm to 4pm CDT.
    A trade at 5:01pm on July 20 belongs to July 21 trading day.
    A trade at 3:59pm on July 21 belongs to July 21 trading day.
    """
    if isinstance(timestamp, str):
        dt = pd.to_datetime(timestamp)
    else:
        dt = timestamp
    
    # If time is >= 17:00 (5pm), it belongs to next day
    if dt.hour >= 17:
        trading_day = (dt + pd.Timedelta(days=1)).date()
    else:
        trading_day = dt.date()
    
    return trading_day


def load_csv_to_database(csv_file, conn, process_trade_func):
    """Load trades from CSV and process through FIFO/LIFO offsetting"""
    
    # Read CSV
    df = pd.read_csv(csv_file)
    
    # Parse datetime and create sequenceId
    df['marketTradeTime'] = pd.to_datetime(df['marketTradeTime'])
    # Use trading day (5pm-4pm) instead of calendar day
    df['trading_day'] = df['marketTradeTime'].apply(get_trading_day)
    df['date'] = df['trading_day'].apply(lambda d: d.strftime('%Y%m%d'))
    df['sequenceId'] = [f"{df.iloc[i]['date']}-{i+1}" for i in range(len(df))]
    
    # Process each trade through offsetting logic
    realized_summary = {'fifo': [], 'lifo': []}
    
    for _, row in df.iterrows():
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
            realized = process_trade_func(conn, trade, method)
            realized_summary[method].extend(realized)
    
    return df, realized_summary


def update_daily_positions_unrealized_pnl(conn):
    """
    Update unrealized P&L for all symbols in daily_positions using simplified calculation
    Formula: (Settle Price - Entry Price) × Quantity × 1000
    """
    from .pnl_engine import calculate_daily_simple_unrealized_pnl
    
    cursor = conn.cursor()
    today = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    # Get settle prices (close price type)
    settle_query = "SELECT symbol, price FROM pricing WHERE price_type = 'close'"
    settle_df = pd.read_sql_query(settle_query, conn)
    settle_prices = dict(zip(settle_df['symbol'], settle_df['price']))
    
    # Get all symbols with daily positions today
    symbols_query = "SELECT DISTINCT symbol FROM daily_positions WHERE date = ?"
    symbols = [row[0] for row in cursor.execute(symbols_query, (today,)).fetchall()]
    
    for symbol in symbols:
        for method in ['fifo', 'lifo']:
            # Get unrealized positions for this symbol/method
            positions = view_unrealized_positions(conn, method, symbol)
            if positions.empty:
                continue
            
            # Calculate using simplified formula
            unrealized_list = calculate_daily_simple_unrealized_pnl(positions, settle_prices)
            total_unrealized = sum(u['unrealizedPnL'] for u in unrealized_list)
            
            # Update daily position
            update_query = """
                UPDATE daily_positions 
                SET unrealized_pnl = ?, timestamp = ?
                WHERE date = ? AND symbol = ? AND method = ?
            """
            cursor.execute(update_query, (
                total_unrealized, 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                today, symbol, method
            ))
    
    conn.commit()


def view_unrealized_positions(conn, method='fifo', symbol=None):
    """View current unrealized positions"""
    if symbol:
        query = f"SELECT * FROM trades_{method} WHERE quantity > 0 AND symbol = ? ORDER BY sequenceId"
        df = pd.read_sql_query(query, conn, params=[symbol])
    else:
        query = f"SELECT * FROM trades_{method} WHERE quantity > 0 ORDER BY sequenceId"
        df = pd.read_sql_query(query, conn)
    return df


def view_realized_trades(conn, method='fifo'):
    """View realized trades"""
    query = f"SELECT * FROM realized_{method} ORDER BY timestamp DESC"
    df = pd.read_sql_query(query, conn)
    return df


def load_pricing_dictionaries(conn):
    """Load pricing data from database into separate dictionaries"""
    
    # Query all pricing data
    query = "SELECT symbol, price_type, price FROM pricing"
    df = pd.read_sql_query(query, conn)
    
    # Create dictionaries for each price type
    price_dicts = {
        'now': {},
        'close': {},
        'sodTod': {},
        'sodTom': {}
    }
    
    # Populate dictionaries
    for _, row in df.iterrows():
        price_type = row['price_type']
        if price_type in price_dicts:
            price_dicts[price_type][row['symbol']] = row['price']
    
    return price_dicts


def setup_pricing_as_of(conn, valuation_datetime, close_prices, symbol):
    """
    Set up pricing table to represent state at a specific point in time.
    valuation_datetime: datetime object in Chicago
    close_prices: dict of date -> dict of symbol -> close price
    """
    cursor = conn.cursor()
    
    # Clear existing pricing
    cursor.execute("DELETE FROM pricing WHERE symbol = ?", (symbol,))
    
    # Determine valuation date and time
    val_date = valuation_datetime.date()
    val_hour = valuation_datetime.hour
    
    # Sort dates to find relevant prices
    sorted_dates = sorted(close_prices.keys())
    
    # Find dates with prices for this symbol
    dates_with_symbol = [d for d in sorted_dates if symbol in close_prices.get(d, {})]
    
    if not dates_with_symbol:
        raise ValueError(f"No price data found for symbol {symbol}")
    
    # Find the most recent close price (today or previous day)
    close_date = val_date if val_date in dates_with_symbol else max(d for d in dates_with_symbol if d < val_date)
    close_price = close_prices[close_date][symbol]
    close_timestamp = f"{close_date} 14:00:00"  # 2pm
    
    # Use close price as current price for historical simulation
    current_price = close_price
    
    # Determine sodTod and sodTom based on time
    if val_hour >= 16:  # After 4pm
        # sodTod = yesterday's close, sodTom = NULL
        if close_date in dates_with_symbol:
            idx = dates_with_symbol.index(close_date)
            if idx > 0:
                sodtod_date = dates_with_symbol[idx - 1]
                sodtod_price = close_prices[sodtod_date][symbol]
                sodtod_timestamp = f"{sodtod_date} 14:00:00"
                
                cursor.execute("""
                    INSERT INTO pricing (symbol, price_type, price, timestamp)
                    VALUES (?, 'sodTod', ?, ?)
                """, (symbol, sodtod_price, sodtod_timestamp))
        # sodTom is NULL (don't insert)
        
    elif val_hour >= 14:  # 2pm-4pm
        # sodTod = yesterday's close, sodTom = today's close
        if close_date in dates_with_symbol:
            idx = dates_with_symbol.index(close_date)
            if idx > 0:
                sodtod_date = dates_with_symbol[idx - 1]
                sodtod_price = close_prices[sodtod_date][symbol]
                sodtod_timestamp = f"{sodtod_date} 14:00:00"
                
                cursor.execute("""
                    INSERT INTO pricing (symbol, price_type, price, timestamp)
                    VALUES (?, 'sodTod', ?, ?)
                """, (symbol, sodtod_price, sodtod_timestamp))
            
            # sodTom = today's close
            cursor.execute("""
                INSERT INTO pricing (symbol, price_type, price, timestamp)
                VALUES (?, 'sodTom', ?, ?)
            """, (symbol, close_price, close_timestamp))
    
    else:  # Before 2pm
        # sodTod = yesterday's close, sodTom = NULL
        if close_date in dates_with_symbol:
            idx = dates_with_symbol.index(close_date)
            if idx > 0:
                sodtod_date = dates_with_symbol[idx - 1]
                sodtod_price = close_prices[sodtod_date][symbol]
                sodtod_timestamp = f"{sodtod_date} 14:00:00"
                
                cursor.execute("""
                    INSERT INTO pricing (symbol, price_type, price, timestamp)
                    VALUES (?, 'sodTod', ?, ?)
                """, (symbol, sodtod_price, sodtod_timestamp))
    
    # Always insert close and now prices
    cursor.execute("""
        INSERT INTO pricing (symbol, price_type, price, timestamp)
        VALUES (?, 'close', ?, ?)
    """, (symbol, close_price, close_timestamp))
    
    cursor.execute("""
        INSERT INTO pricing (symbol, price_type, price, timestamp)
        VALUES (?, 'now', ?, ?)
    """, (symbol, current_price, valuation_datetime.strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    
    # Return pricing setup
    pricing_df = pd.read_sql_query("SELECT * FROM pricing WHERE symbol = ? ORDER BY price_type", conn, params=[symbol])
    return pricing_df


def roll_2pm_prices(conn, new_close_price, symbol):
    """At 2pm: update close price and copy to sodTom"""
    cursor = conn.cursor()
    
    # Use 2pm timestamp for the price
    now = datetime.now()
    today_2pm = now.replace(hour=14, minute=0, second=0, microsecond=0)
    timestamp = today_2pm.strftime('%Y-%m-%d %H:%M:%S')
    
    # Update both close and sodTom with new price
    for price_type in ['close', 'sodTom']:
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, ?, ?, ?)
        """, (symbol, price_type, new_close_price, timestamp))
    
    conn.commit()


def roll_4pm_prices(conn, symbol):
    """At 4pm: move sodTom to sodTod, clear sodTom"""
    cursor = conn.cursor()
    
    # Get current sodTom value AND its timestamp
    sodTom_data = cursor.execute(
        "SELECT price, timestamp FROM pricing WHERE symbol = ? AND price_type = 'sodTom'", 
        (symbol,)
    ).fetchone()
    
    if sodTom_data:
        price, original_timestamp = sodTom_data
        
        # Move sodTom to sodTod, preserving the original timestamp
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, ?, ?, ?)
        """, (symbol, 'sodTod', price, original_timestamp))
        
        # Clear sodTom
        cursor.execute("""
            DELETE FROM pricing WHERE symbol = ? AND price_type = 'sodTom'
        """, (symbol,))
        
        conn.commit()


def update_daily_position(conn, trade_date, symbol, method, realized_qty=0, realized_pnl_delta=0):
    """Update daily position tracking after a trade"""
    cursor = conn.cursor()
    
    # Calculate current open position (net quantity)
    open_query = f"""
        SELECT 
            SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END) as net_position
        FROM trades_{method}
        WHERE symbol = ? AND quantity > 0
    """
    result = cursor.execute(open_query, (symbol,)).fetchone()
    open_position = result[0] if result[0] else 0
    
    # Get existing daily position values
    existing_query = """
        SELECT closed_position, realized_pnl, unrealized_pnl
        FROM daily_positions
        WHERE date = ? AND symbol = ? AND method = ?
    """
    existing = cursor.execute(existing_query, (trade_date, symbol, method)).fetchone()
    
    # Don't accumulate - use the values passed in directly
    # The caller is responsible for tracking daily totals
    closed_position = realized_qty
    realized_pnl = realized_pnl_delta
    
    # Update or insert daily position (unrealized_pnl will be updated separately)
    upsert_query = """
        INSERT OR REPLACE INTO daily_positions 
        (date, symbol, method, open_position, closed_position, realized_pnl, unrealized_pnl, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, 
            COALESCE((SELECT unrealized_pnl FROM daily_positions 
                      WHERE date = ? AND symbol = ? AND method = ?), 0), ?)
    """
    cursor.execute(upsert_query, (
        trade_date, symbol, method, open_position, closed_position, 
        realized_pnl, trade_date, symbol, method,
        trade_date + ' 16:00:00'  # Use trade date at 4pm instead of current time
    ))
    
    conn.commit()


def view_daily_positions(conn, date=None, method=None):
    """View daily position tracking data"""
    query = "SELECT * FROM daily_positions WHERE 1=1"
    params = []
    
    if date:
        query += " AND date = ?"
        params.append(date)
    
    if method:
        query += " AND method = ?"
        params.append(method)
    
    query += " ORDER BY date, method"
    
    df = pd.read_sql_query(query, conn, params=params)
    return df


def load_multiple_csvs(folder_path, conn, process_trade_func, use_daily_tracking=True, close_prices=None):
    """
    Load multiple CSV files from a folder, processing them in chronological order.
    CSV files should be named: trades_YYYYMMDD.csv
    """
    # Find all matching CSV files
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
    
    # Sort by date
    file_info.sort(key=lambda x: x[0])
    
    if not file_info:
        return None
    
    # Process each file
    all_trades = []
    
    for date_str, file_path in file_info:
        # Read CSV
        df = pd.read_csv(file_path)
        
        # Parse datetime and create sequenceId
        df['marketTradeTime'] = pd.to_datetime(df['marketTradeTime'])
        df['trading_day'] = df['marketTradeTime'].apply(get_trading_day)
        df['date'] = df['trading_day'].apply(lambda d: d.strftime('%Y%m%d'))
        
        # Create unique sequenceId across all files
        start_idx = len(all_trades)
        df['sequenceId'] = [f"{df.iloc[i]['date']}-{start_idx + i + 1}" for i in range(len(df))]
        
        # Get trading day for this CSV
        trading_day = df['trading_day'].iloc[0] if not df.empty else None
        
        # Process each trade
        realized_summary = {'fifo': [], 'lifo': []}
        
        for _, row in df.iterrows():
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
                realized = process_trade_func(conn, trade, method, trade['time'][:19])
                realized_summary[method].extend(realized)
                
                # Update daily tracking if enabled
                if use_daily_tracking:
                    realized_qty = sum(r['quantity'] for r in realized)
                    realized_pnl_delta = sum(r['realizedPnL'] for r in realized)
                    trade_date = get_trading_day(row['marketTradeTime']).strftime('%Y-%m-%d')
                    update_daily_position(conn, trade_date, trade['symbol'], method, 
                                        realized_qty, realized_pnl_delta)
        
        all_trades.extend(df.to_dict('records'))
    
    return pd.DataFrame(all_trades) if all_trades else None 


def update_current_price(conn, symbol, price, timestamp):
    """
    Update or insert current price for a symbol in the pricing table.
    
    Args:
        conn: Database connection
        symbol: Bloomberg format symbol (e.g., 'TYU5 Comdty')
        price: Current price value
        timestamp: Timestamp when price was observed
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        
        # Ensure timestamp is a string
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_str = str(timestamp)
        
        # Insert or replace the 'now' price for this symbol
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'now', ?, ?)
        """, (symbol, price, timestamp_str))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error updating current price for {symbol}: {e}")
        conn.rollback()
        return False


def perform_eod_settlement(conn, settlement_date, close_prices):
    """
    Perform end-of-day settlement: calculate total unrealized P&L and mark positions to market.
    
    Args:
        conn: Database connection
        settlement_date: Date object for the trading day being settled
        close_prices: Dict of symbol -> settlement price for the day
        
    This function:
    1. Calculates total unrealized P&L for each symbol/method
    2. Updates daily_positions with the total (not change)
    3. Updates all open positions' prices to the settlement price (mark-to-market)
    """
    cursor = conn.cursor()
    
    # Get all symbols with open positions
    unique_symbols = pd.read_sql_query(
        "SELECT DISTINCT symbol FROM trades_fifo WHERE quantity > 0", conn
    )['symbol'].tolist()
    
    for symbol in unique_symbols:
        settle_price = close_prices.get(symbol)
        if not settle_price:
            continue
            
        for method in METHODS:
            # Calculate total unrealized P&L using current cost basis
            positions = view_unrealized_positions(conn, method, symbol=symbol)
            total_unrealized_pnl = 0
            
            if not positions.empty:
                for _, pos in positions.iterrows():
                    # Simple P&L: (settle - cost_basis) * qty * 1000
                    pnl = (settle_price - pos['price']) * pos['quantity'] * PNL_MULTIPLIER
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
            date_str = settlement_date.strftime('%Y-%m-%d')
            cursor.execute("""
                UPDATE daily_positions 
                SET unrealized_pnl = ?, open_position = ?, timestamp = ?
                WHERE date = ? AND symbol = ? AND method = ?
            """, (total_unrealized_pnl, open_position, 
                  date_str + ' 16:00:00',
                  date_str, symbol, method))
            
            # Mark-to-market: Update all open positions to settle price
            cursor.execute(f"""
                UPDATE trades_{method}
                SET price = ?, time = ?
                WHERE symbol = ? AND quantity > 0
            """, (settle_price, date_str + ' 16:00:00', symbol))
    
    conn.commit() 