"""
Integration tests for FIFO P&L calculations with positions aggregator.

This test suite validates the complete flow:
1. Trade processing → Realized P&L → Position updates
2. Price updates → Unrealized P&L recalculation → Positions table update
3. Live vs Close P&L calculations
"""

import unittest
import sqlite3
import tempfile
import os
import sys
import time
from datetime import datetime, timedelta
import pandas as pd
import threading

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade
from lib.trading.pnl_fifo_lifo.data_manager import (
    initialize_database, 
    update_current_price,
    update_daily_position
)
from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator


class TestFIFOPnLIntegration(unittest.TestCase):
    """Integration tests for complete FIFO P&L flow"""
    
    def setUp(self):
        """Set up test environment with database and aggregator"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.test_db_path)
        initialize_database(self.conn)
        
        # Initialize positions aggregator
        self.aggregator = PositionsAggregator(self.test_db_path)
        
        # Create positions table
        self.conn.execute("""
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
                fifo_unrealized_pnl_close REAL DEFAULT 0,
                lifo_realized_pnl REAL DEFAULT 0,
                lifo_unrealized_pnl REAL DEFAULT 0,
                lifo_unrealized_pnl_close REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                has_greeks BOOLEAN DEFAULT 0,
                instrument_type TEXT
            )
        """)
        self.conn.commit()
        
    def tearDown(self):
        """Clean up test environment"""
        self.conn.close()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_full_trade_to_positions_flow(self):
        """Test complete flow from trade entry to positions table update"""
        symbol = 'TYU5 Comdty'
        
        # Step 1: Enter initial trades
        # Buy 10 @ 112.50
        trade1 = {
            'sequenceId': 1,
            'transactionId': 'TXN001',
            'symbol': symbol,
            'quantity': 10,
            'price': 112.50,
            'buySell': 'B',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fullPartial': 'full'
        }
        process_new_trade(self.conn, trade1, 'fifo')
        
        # Buy 5 @ 112.25
        trade2 = {
            'sequenceId': 2,
            'transactionId': 'TXN002',
            'symbol': symbol,
            'quantity': 5,
            'price': 112.25,
            'buySell': 'B',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fullPartial': 'full'
        }
        process_new_trade(self.conn, trade2, 'fifo')
        self.conn.commit()
        
        # Step 2: Set initial prices and trigger aggregator
        update_current_price(self.conn, symbol, 112.60, datetime.now())
        
        # Load positions into aggregator
        self.aggregator._load_positions_from_db()
        
        # Step 3: Process a closing trade
        # Sell 12 @ 112.75
        trade3 = {
            'sequenceId': 3,
            'transactionId': 'TXN003',
            'symbol': symbol,
            'quantity': 12,
            'price': 112.75,
            'buySell': 'S',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fullPartial': 'full'
        }
        realized_trades = process_new_trade(self.conn, trade3, 'fifo')
        self.conn.commit()
        
        # Update daily position
        today = datetime.now().strftime('%Y-%m-%d')
        realized_pnl = sum(r['realizedPnL'] for r in realized_trades)
        update_daily_position(self.conn, today, symbol, 'fifo', 12, realized_pnl)
        
        # Step 4: Update price and trigger unrealized P&L calculation
        # Set SOD and current prices
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'sodTod', ?, ?)
        """, (symbol, 112.30, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
        
        update_current_price(self.conn, symbol, 112.80, datetime.now())
        
        # Reload positions to calculate unrealized P&L
        self.aggregator._load_positions_from_db()
        
        # Step 5: Write aggregated data to positions table
        if not self.aggregator.positions_cache.empty:
            self.aggregator._write_positions_to_db(self.aggregator.positions_cache)
        
        # Step 6: Verify positions table
        positions_df = pd.read_sql_query(
            "SELECT * FROM positions WHERE symbol = ?", 
            self.conn, 
            params=(symbol,)
        )
        
        self.assertEqual(len(positions_df), 1)
        position = positions_df.iloc[0]
        
        # Verify position quantities
        self.assertEqual(position['open_position'], 3)  # 15 bought - 12 sold
        self.assertEqual(position['closed_position'], 12)
        
        # Verify realized P&L
        # First 10: (112.75 - 112.50) * 10 * 1000 = 2500
        # Next 2: (112.75 - 112.25) * 2 * 1000 = 1000
        # Total: 3500
        self.assertEqual(position['fifo_realized_pnl'], 3500)
        
        # Verify unrealized P&L exists (3 @ 112.25 with current price 112.80)
        self.assertGreater(position['fifo_unrealized_pnl'], 0)
    
    def test_live_vs_close_pnl(self):
        """Test Live P&L vs Close P&L calculations"""
        symbol = 'TYU5 Comdty'
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create a position
        trade = {
            'sequenceId': 1,
            'transactionId': 'TXN001',
            'symbol': symbol,
            'quantity': 10,
            'price': 112.50,
            'buySell': 'B',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fullPartial': 'full'
        }
        process_new_trade(self.conn, trade, 'fifo')
        self.conn.commit()
        
        # Set prices
        cursor = self.conn.cursor()
        # SOD price
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'sodTod', ?, ?)
        """, (symbol, 112.55, f"{today} 08:00:00"))
        
        # Current price
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'now', ?, ?)
        """, (symbol, 112.70, f"{today} 10:00:00"))
        
        # Close price (today)
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'close', ?, ?)
        """, (symbol, 112.65, f"{today} 16:00:00"))
        self.conn.commit()
        
        # Load and calculate P&L
        self.aggregator._load_positions_from_db()
        self.aggregator._write_positions_to_db(self.aggregator.positions_cache)
        
        # Query positions
        positions_df = pd.read_sql_query(
            "SELECT * FROM positions WHERE symbol = ?", 
            self.conn, 
            params=(symbol,)
        )
        
        position = positions_df.iloc[0]
        
        # Live P&L should use current price (112.70)
        # Close P&L should use close price (112.65)
        # Both should be positive but close P&L should be less
        self.assertGreater(position['fifo_unrealized_pnl'], 0)
        self.assertGreater(position['fifo_unrealized_pnl_close'], 0)
        self.assertGreater(position['fifo_unrealized_pnl'], position['fifo_unrealized_pnl_close'])
    
    def test_price_update_triggers_recalculation(self):
        """Test that price updates trigger P&L recalculation"""
        symbol = 'TYU5 Comdty'
        
        # Create a position
        trade = {
            'sequenceId': 1,
            'transactionId': 'TXN001',
            'symbol': symbol,
            'quantity': 10,
            'price': 112.50,
            'buySell': 'B',
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fullPartial': 'full'
        }
        process_new_trade(self.conn, trade, 'fifo')
        self.conn.commit()
        
        # Set initial price
        update_current_price(self.conn, symbol, 112.60, datetime.now())
        self.aggregator._load_positions_from_db()
        self.aggregator._write_positions_to_db(self.aggregator.positions_cache)
        
        # Get initial unrealized P&L
        initial_positions = pd.read_sql_query(
            "SELECT fifo_unrealized_pnl FROM positions WHERE symbol = ?", 
            self.conn, 
            params=(symbol,)
        )
        initial_unrealized = initial_positions.iloc[0]['fifo_unrealized_pnl']
        
        # Update price
        update_current_price(self.conn, symbol, 112.80, datetime.now())
        self.aggregator._load_positions_from_db()
        self.aggregator._write_positions_to_db(self.aggregator.positions_cache)
        
        # Get updated unrealized P&L
        updated_positions = pd.read_sql_query(
            "SELECT fifo_unrealized_pnl FROM positions WHERE symbol = ?", 
            self.conn, 
            params=(symbol,)
        )
        updated_unrealized = updated_positions.iloc[0]['fifo_unrealized_pnl']
        
        # Unrealized P&L should have increased with price increase
        self.assertGreater(updated_unrealized, initial_unrealized)
    
    def test_multiple_symbols_isolation(self):
        """Test that P&L calculations are properly isolated by symbol"""
        # Create positions in two different symbols
        symbols = ['TYU5 Comdty', 'ZNU5 Comdty']
        
        for i, symbol in enumerate(symbols):
            trade = {
                'sequenceId': i + 1,
                'transactionId': f'TXN00{i+1}',
                'symbol': symbol,
                'quantity': 10,
                'price': 112.50 + i,  # Different prices
                'buySell': 'B',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'fullPartial': 'full'
            }
            process_new_trade(self.conn, trade, 'fifo')
        self.conn.commit()
        
        # Set different current prices
        update_current_price(self.conn, symbols[0], 112.70, datetime.now())
        update_current_price(self.conn, symbols[1], 113.20, datetime.now())
        
        # Calculate P&L
        self.aggregator._load_positions_from_db()
        self.aggregator._write_positions_to_db(self.aggregator.positions_cache)
        
        # Verify each symbol has its own P&L
        positions_df = pd.read_sql_query(
            "SELECT * FROM positions ORDER BY symbol", 
            self.conn
        )
        
        self.assertEqual(len(positions_df), 2)
        
        # Each should have different unrealized P&L based on their prices
        pnl_values = positions_df['fifo_unrealized_pnl'].values
        self.assertNotEqual(pnl_values[0], pnl_values[1])


if __name__ == '__main__':
    unittest.main()