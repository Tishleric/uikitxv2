"""
Test Data Setup for Close PnL Testing
Creates isolated test database with known values for validation
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Chicago timezone for consistency
CHICAGO_TZ = pytz.timezone('America/Chicago')

def create_test_database(db_path='test_close_pnl.db'):
    """Create test database with modified schema for close PnL testing"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing tables for clean slate
    cursor.execute("DROP TABLE IF EXISTS positions")
    cursor.execute("DROP TABLE IF EXISTS pricing")
    cursor.execute("DROP TABLE IF EXISTS trades_fifo")
    cursor.execute("DROP TABLE IF EXISTS trades_lifo")
    cursor.execute("DROP TABLE IF EXISTS daily_positions")
    
    # Create positions table with new columns for close PnL
    positions_schema = """
    CREATE TABLE positions (
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
        -- NEW COLUMNS FOR CLOSE PNL
        fifo_unrealized_pnl_close REAL DEFAULT 0,
        lifo_unrealized_pnl_close REAL DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_trade_update TIMESTAMP,
        last_greek_update TIMESTAMP,
        has_greeks BOOLEAN DEFAULT 0,
        instrument_type TEXT
    )
    """
    cursor.execute(positions_schema)
    
    # Create pricing table
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
    
    # Create trades tables (simplified)
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
    
    cursor.execute(f"CREATE TABLE trades_fifo {trades_schema}")
    cursor.execute(f"CREATE TABLE trades_lifo {trades_schema}")
    
    # Create daily positions table
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
    
    conn.commit()
    return conn


def insert_test_data(conn):
    """Insert test data with known values"""
    
    cursor = conn.cursor()
    now = datetime.now(CHICAGO_TZ)
    today_str = now.strftime('%Y-%m-%d')
    yesterday = now - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    # Test symbols
    symbols = ['TYU5 Comdty', 'ZNU5 Comdty', 'ZFU5 Comdty']
    
    # Insert test trades for FIFO (open positions)
    test_trades = [
        # TYU5: Long 10 @ 111.5
        (1, 'TYU5 Comdty', 111.5, 111.5, 10, 'B', 'SEQ001', f'{today_str} 09:00:00.000', f'{today_str} 09:00:00.000'),
        # ZNU5: Short 5 @ 108.25
        (2, 'ZNU5 Comdty', 108.25, 108.25, 5, 'S', 'SEQ002', f'{today_str} 10:00:00.000', f'{today_str} 10:00:00.000'),
        # ZFU5: Long 20 @ 109.75
        (3, 'ZFU5 Comdty', 109.75, 109.75, 20, 'B', 'SEQ003', f'{today_str} 11:00:00.000', f'{today_str} 11:00:00.000'),
    ]
    
    for trade in test_trades:
        cursor.execute("""
            INSERT INTO trades_fifo (transactionId, symbol, price, original_price, 
                                   quantity, buySell, sequenceId, time, original_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, trade)
    
    # Insert pricing data
    pricing_data = [
        # Current prices (now)
        ('TYU5 Comdty', 'now', 111.75, f'{today_str} 14:30:00'),
        ('ZNU5 Comdty', 'now', 108.00, f'{today_str} 14:30:00'),
        ('ZFU5 Comdty', 'now', 110.00, f'{today_str} 14:30:00'),
        
        # Today's close prices (for TYU5 and ZNU5 only - testing mixed availability)
        ('TYU5 Comdty', 'close', 111.625, f'{today_str} 16:00:00'),
        ('ZNU5 Comdty', 'close', 108.125, f'{today_str} 16:00:00'),
        # ZFU5 has yesterday's close only
        ('ZFU5 Comdty', 'close', 109.50, f'{yesterday_str} 16:00:00'),
        
        # SOD prices
        ('TYU5 Comdty', 'sodTod', 111.50, f'{today_str} 07:00:00'),
        ('ZNU5 Comdty', 'sodTod', 108.25, f'{today_str} 07:00:00'),
        ('ZFU5 Comdty', 'sodTod', 109.75, f'{today_str} 07:00:00'),
    ]
    
    for price_row in pricing_data:
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, ?, ?, ?)
        """, price_row)
    
    # Insert daily positions data (realized PnL)
    daily_data = [
        (today_str, 'TYU5 Comdty', 'fifo', 10, 5, 1250.0, 0, f'{today_str} 14:00:00'),
        (today_str, 'ZNU5 Comdty', 'fifo', -5, 10, 2500.0, 0, f'{today_str} 14:00:00'),
        (today_str, 'ZFU5 Comdty', 'fifo', 20, 0, 0.0, 0, f'{today_str} 14:00:00'),
    ]
    
    for row in daily_data:
        cursor.execute("""
            INSERT INTO daily_positions (date, symbol, method, open_position, 
                                       closed_position, realized_pnl, unrealized_pnl, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, row)
    
    conn.commit()
    
    # Calculate expected values for validation
    expected_values = {
        'TYU5 Comdty': {
            'open_position': 10,
            'entry_price': 111.5,
            'now_price': 111.75,
            'close_price': 111.625,
            'realized_pnl': 1250.0,
            # Unrealized PnL = (now - entry) * qty * 1000 = (111.75 - 111.5) * 10 * 1000 = 2500
            'expected_unrealized_live': 2500.0,
            # Unrealized Close = (close - entry) * qty * 1000 = (111.625 - 111.5) * 10 * 1000 = 1250
            'expected_unrealized_close': 1250.0,
            'expected_pnl_live': 3750.0,  # 1250 + 2500
            'expected_pnl_close': 2500.0   # 1250 + 1250
        },
        'ZNU5 Comdty': {
            'open_position': -5,
            'entry_price': 108.25,
            'now_price': 108.00,
            'close_price': 108.125,
            'realized_pnl': 2500.0,
            # Short position: Unrealized = -(now - entry) * qty * 1000 = -(108.00 - 108.25) * 5 * 1000 = 1250
            'expected_unrealized_live': 1250.0,
            # Short close: -(108.125 - 108.25) * 5 * 1000 = 625
            'expected_unrealized_close': 625.0,
            'expected_pnl_live': 3750.0,  # 2500 + 1250
            'expected_pnl_close': 3125.0  # 2500 + 625
        },
        'ZFU5 Comdty': {
            'open_position': 20,
            'entry_price': 109.75,
            'now_price': 110.00,
            'close_price': None,  # Only yesterday's close available
            'realized_pnl': 0.0,
            # Unrealized = (110.00 - 109.75) * 20 * 1000 = 5000
            'expected_unrealized_live': 5000.0,
            'expected_unrealized_close': None,  # Should be NULL
            'expected_pnl_live': 5000.0,
            'expected_pnl_close': None  # Should be NULL
        }
    }
    
    return expected_values


if __name__ == "__main__":
    # Create and populate test database
    conn = create_test_database()
    expected_values = insert_test_data(conn)
    
    print("Test database created successfully!")
    print("\nExpected values:")
    for symbol, values in expected_values.items():
        print(f"\n{symbol}:")
        print(f"  Live PnL: ${values['expected_pnl_live']:,.2f}")
        if values['expected_pnl_close'] is not None:
            print(f"  Close PnL: ${values['expected_pnl_close']:,.2f}")
        else:
            print(f"  Close PnL: NULL (no today's close price)")
    
    conn.close()