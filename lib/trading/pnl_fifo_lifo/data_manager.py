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
        quantity REAL,
        buySell TEXT,
        sequenceId TEXT PRIMARY KEY,
        time TEXT,
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


def view_unrealized_positions(conn, method='fifo'):
    """View current unrealized positions"""
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


def setup_pricing_as_of(conn, valuation_datetime, close_prices, current_price, symbol):
    """
    Set up pricing table to represent state at a specific point in time.
    valuation_datetime: datetime object in Chicago
    close_prices: dict of date -> close price
    """
    cursor = conn.cursor()
    
    # Clear existing pricing
    cursor.execute("DELETE FROM pricing WHERE symbol = ?", (symbol,))
    
    # Determine valuation date and time
    val_date = valuation_datetime.date()
    val_hour = valuation_datetime.hour
    
    # Sort dates to find relevant prices
    sorted_dates = sorted(close_prices.keys())
    
    # Find the most recent close price (today or previous day)
    close_date = val_date if val_date in close_prices else max(d for d in sorted_dates if d < val_date)
    close_price = close_prices[close_date]
    close_timestamp = f"{close_date} 14:00:00"  # 2pm
    
    # Determine sodTod and sodTom based on time
    if val_hour >= 16:  # After 4pm
        # sodTod = yesterday's close, sodTom = NULL
        if close_date in sorted_dates:
            idx = sorted_dates.index(close_date)
            if idx > 0:
                sodtod_date = sorted_dates[idx - 1]
                sodtod_price = close_prices[sodtod_date]
                sodtod_timestamp = f"{sodtod_date} 14:00:00"
                
                cursor.execute("""
                    INSERT INTO pricing (symbol, price_type, price, timestamp)
                    VALUES (?, 'sodTod', ?, ?)
                """, (symbol, sodtod_price, sodtod_timestamp))
        # sodTom is NULL (don't insert)
        
    elif val_hour >= 14:  # 2pm-4pm
        # sodTod = yesterday's close, sodTom = today's close
        if close_date in sorted_dates:
            idx = sorted_dates.index(close_date)
            if idx > 0:
                sodtod_date = sorted_dates[idx - 1]
                sodtod_price = close_prices[sodtod_date]
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
        if close_date in sorted_dates:
            idx = sorted_dates.index(close_date)
            if idx > 0:
                sodtod_date = sorted_dates[idx - 1]
                sodtod_price = close_prices[sodtod_date]
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
    
    if existing:
        # Increment existing values
        closed_position = existing[0] + realized_qty
        realized_pnl = existing[1] + realized_pnl_delta
        # Unrealized will be updated separately
    else:
        # New day - start fresh
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