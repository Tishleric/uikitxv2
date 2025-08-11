"""
Unit tests for FIFO realized and unrealized P&L calculations.

This test suite validates:
1. FIFO matching logic for realized P&L
2. Unrealized P&L calculations with Pmax logic
3. Time-based unrealized P&L (before/after 2pm)
4. Partial fills and complex scenarios
"""

import unittest
import sqlite3
from datetime import datetime, timedelta
import tempfile
import os
import sys
import pytz

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.trading.pnl_fifo_lifo.pnl_engine import (
    process_new_trade, 
    calculate_unrealized_pnl,
    get_effective_entry_price,
    PNL_MULTIPLIER
)
from lib.trading.pnl_fifo_lifo.data_manager import (
    initialize_database,
    view_unrealized_positions
)


class TestFIFOPnLCalculations(unittest.TestCase):
    """Test suite for FIFO P&L calculations"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.test_db_path)
        initialize_database(self.conn)
        self.chicago_tz = pytz.timezone('America/Chicago')
        
    def tearDown(self):
        """Clean up test database"""
        self.conn.close()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def _create_trade(self, sequence_id, symbol, quantity, price, buy_sell, 
                      transaction_id=None, timestamp=None):
        """Helper to create a trade dictionary"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if transaction_id is None:
            transaction_id = f"TXN{sequence_id}"
            
        return {
            'sequenceId': sequence_id,
            'transactionId': transaction_id,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'buySell': buy_sell,
            'time': timestamp,
            'fullPartial': 'full'
        }
    
    def _insert_price(self, symbol, price_type, price, timestamp=None):
        """Helper to insert a price into the pricing table"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, ?, ?, ?)
        """, (symbol, price_type, price, timestamp))
        self.conn.commit()
    
    # ==================== REALIZED P&L TESTS ====================
    
    def test_basic_long_realized_pnl(self):
        """Test basic long position: Buy then Sell"""
        # Buy 10 @ 112.50
        buy_trade = self._create_trade(1, 'TYU5 Comdty', 10, 112.50, 'B')
        process_new_trade(self.conn, buy_trade, 'fifo')
        self.conn.commit()
        
        # Sell 10 @ 112.75 - should realize profit
        sell_trade = self._create_trade(2, 'TYU5 Comdty', 10, 112.75, 'S')
        realized_trades = process_new_trade(self.conn, sell_trade, 'fifo')
        self.conn.commit()
        
        # Expected P&L: (112.75 - 112.50) * 10 * 1000 = $2,500
        self.assertEqual(len(realized_trades), 1)
        self.assertEqual(realized_trades[0]['realizedPnL'], 2500)
        self.assertEqual(realized_trades[0]['entryPrice'], 112.50)
        self.assertEqual(realized_trades[0]['exitPrice'], 112.75)
    
    def test_basic_short_realized_pnl(self):
        """Test basic short position: Sell then Buy"""
        # Sell 5 @ 112.50
        sell_trade = self._create_trade(1, 'TYU5 Comdty', 5, 112.50, 'S')
        process_new_trade(self.conn, sell_trade, 'fifo')
        self.conn.commit()
        
        # Buy 5 @ 112.25 - should realize profit
        buy_trade = self._create_trade(2, 'TYU5 Comdty', 5, 112.25, 'B')
        realized_trades = process_new_trade(self.conn, buy_trade, 'fifo')
        self.conn.commit()
        
        # Expected P&L: (112.50 - 112.25) * 5 * 1000 = $1,250
        self.assertEqual(len(realized_trades), 1)
        self.assertEqual(realized_trades[0]['realizedPnL'], 1250)
        self.assertEqual(realized_trades[0]['entryPrice'], 112.50)
        self.assertEqual(realized_trades[0]['exitPrice'], 112.25)
    
    def test_partial_fill_realized_pnl(self):
        """Test partial fill scenario"""
        # Buy 10 @ 112.50
        buy_trade = self._create_trade(1, 'TYU5 Comdty', 10, 112.50, 'B')
        process_new_trade(self.conn, buy_trade, 'fifo')
        self.conn.commit()
        
        # Sell 6 @ 112.75 - partial fill
        sell_trade = self._create_trade(2, 'TYU5 Comdty', 6, 112.75, 'S')
        realized_trades = process_new_trade(self.conn, sell_trade, 'fifo')
        self.conn.commit()
        
        # Expected P&L: (112.75 - 112.50) * 6 * 1000 = $1,500
        self.assertEqual(len(realized_trades), 1)
        self.assertEqual(realized_trades[0]['realizedPnL'], 1500)
        self.assertEqual(realized_trades[0]['quantity'], 6)
        self.assertEqual(realized_trades[0]['partialFull'], 'partial')
        
        # Check remaining position
        positions = view_unrealized_positions(self.conn, 'fifo')
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions.iloc[0]['quantity'], 4)
    
    def test_fifo_ordering(self):
        """Test FIFO ordering matches oldest positions first"""
        # Buy 5 @ 112.50 (oldest)
        buy1 = self._create_trade(1, 'TYU5 Comdty', 5, 112.50, 'B')
        process_new_trade(self.conn, buy1, 'fifo')
        
        # Buy 5 @ 112.25 (newer)
        buy2 = self._create_trade(2, 'TYU5 Comdty', 5, 112.25, 'B')
        process_new_trade(self.conn, buy2, 'fifo')
        
        # Buy 5 @ 112.00 (newest)
        buy3 = self._create_trade(3, 'TYU5 Comdty', 5, 112.00, 'B')
        process_new_trade(self.conn, buy3, 'fifo')
        self.conn.commit()
        
        # Sell 12 @ 112.75 - should match first two buys
        sell = self._create_trade(4, 'TYU5 Comdty', 12, 112.75, 'S')
        realized_trades = process_new_trade(self.conn, sell, 'fifo')
        self.conn.commit()
        
        # Should have 2 realizations
        self.assertEqual(len(realized_trades), 2)
        
        # First realization: 5 @ 112.50
        self.assertEqual(realized_trades[0]['quantity'], 5)
        self.assertEqual(realized_trades[0]['entryPrice'], 112.50)
        self.assertEqual(realized_trades[0]['realizedPnL'], 1250)  # (112.75-112.50)*5*1000
        
        # Second realization: 5 @ 112.25
        self.assertEqual(realized_trades[1]['quantity'], 5)
        self.assertEqual(realized_trades[1]['entryPrice'], 112.25)
        self.assertEqual(realized_trades[1]['realizedPnL'], 2500)  # (112.75-112.25)*5*1000
        
        # Remaining should be 3 @ 112.00
        positions = view_unrealized_positions(self.conn, 'fifo')
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions.iloc[0]['quantity'], 3)
        self.assertEqual(positions.iloc[0]['price'], 112.00)
    
    # ==================== UNREALIZED P&L TESTS ====================
    
    def test_pmax_logic_today_trade(self):
        """Test Pmax logic uses actual price for today's trades"""
        now = datetime.now()
        trade_time = now.strftime('%Y-%m-%d %H:%M:%S.000')
        
        # Today's trade should use actual price
        entry_price = get_effective_entry_price(
            actual_entry_price=112.50,
            sod_price=112.30,
            trade_time=trade_time
        )
        
        self.assertEqual(entry_price, 112.50)
    
    def test_pmax_logic_yesterday_trade(self):
        """Test Pmax logic uses SOD price for yesterday's trades"""
        # Yesterday at 3pm
        yesterday = datetime.now() - timedelta(days=1)
        trade_time = yesterday.replace(hour=15).strftime('%Y-%m-%d %H:%M:%S.000')
        
        # Yesterday's trade should use SOD price
        entry_price = get_effective_entry_price(
            actual_entry_price=112.50,
            sod_price=112.30,
            trade_time=trade_time
        )
        
        self.assertEqual(entry_price, 112.30)
    
    def test_unrealized_pnl_before_2pm(self):
        """Test unrealized P&L calculation before 2pm Chicago"""
        # Insert a long position
        buy_trade = self._create_trade(1, 'TYU5 Comdty', 10, 112.50, 'B')
        process_new_trade(self.conn, buy_trade, 'fifo')
        self.conn.commit()
        
        # Set up prices
        self._insert_price('TYU5 Comdty', 'sodTod', 112.55)
        self._insert_price('TYU5 Comdty', 'sodTom', 112.60)
        self._insert_price('TYU5 Comdty', 'now', 112.70)
        
        # Get positions and calculate unrealized P&L
        positions = view_unrealized_positions(self.conn, 'fifo')
        price_dicts = {
            'sodTod': {'TYU5 Comdty': 112.55},
            'sodTom': {'TYU5 Comdty': 112.60},
            'now': {'TYU5 Comdty': 112.70},
            'close': {}
        }
        
        # Mock time to before 2pm
        import unittest.mock
        with unittest.mock.patch('lib.trading.pnl_fifo_lifo.pnl_engine.get_current_time_period') as mock_time:
            mock_time.return_value = 'pre_2pm'
            
            unrealized = calculate_unrealized_pnl(positions, price_dicts, 'live')
            
            # Before 2pm formula: ((sodTod - entry) + (now - sodTod)) * qty * 1000
            # Entry = 112.50 (today's trade uses actual price)
            # ((112.55 - 112.50) + (112.70 - 112.55)) * 10 * 1000
            # (0.05 + 0.15) * 10 * 1000 = 2000
            self.assertEqual(len(unrealized), 1)
            self.assertEqual(unrealized[0]['unrealizedPnL'], 2000)
    
    def test_unrealized_pnl_after_2pm(self):
        """Test unrealized P&L calculation after 2pm Chicago"""
        # Insert a long position
        buy_trade = self._create_trade(1, 'TYU5 Comdty', 10, 112.50, 'B')
        process_new_trade(self.conn, buy_trade, 'fifo')
        self.conn.commit()
        
        # Set up prices
        self._insert_price('TYU5 Comdty', 'sodTod', 112.55)
        self._insert_price('TYU5 Comdty', 'sodTom', 112.60)
        self._insert_price('TYU5 Comdty', 'now', 112.70)
        
        # Get positions and calculate unrealized P&L
        positions = view_unrealized_positions(self.conn, 'fifo')
        price_dicts = {
            'sodTod': {'TYU5 Comdty': 112.55},
            'sodTom': {'TYU5 Comdty': 112.60},
            'now': {'TYU5 Comdty': 112.70},
            'close': {}
        }
        
        # Mock time to after 2pm
        import unittest.mock
        with unittest.mock.patch('lib.trading.pnl_fifo_lifo.pnl_engine.get_current_time_period') as mock_time:
            mock_time.return_value = '2pm_to_4pm'
            
            unrealized = calculate_unrealized_pnl(positions, price_dicts, 'live')
            
            # After 2pm formula: ((sodTom - entry) + (now - sodTom)) * qty * 1000
            # Entry = 112.50 (today's trade uses actual price)
            # ((112.60 - 112.50) + (112.70 - 112.60)) * 10 * 1000
            # (0.10 + 0.10) * 10 * 1000 = 2000
            self.assertEqual(len(unrealized), 1)
            self.assertEqual(unrealized[0]['unrealizedPnL'], 2000)
    
    def test_short_position_unrealized_pnl(self):
        """Test unrealized P&L for short positions (inverted)"""
        # Insert a short position
        sell_trade = self._create_trade(1, 'TYU5 Comdty', 5, 112.50, 'S')
        process_new_trade(self.conn, sell_trade, 'fifo')
        self.conn.commit()
        
        # Set up prices (market moved against us)
        self._insert_price('TYU5 Comdty', 'sodTod', 112.55)
        self._insert_price('TYU5 Comdty', 'now', 112.70)
        
        positions = view_unrealized_positions(self.conn, 'fifo')
        price_dicts = {
            'sodTod': {'TYU5 Comdty': 112.55},
            'sodTom': {'TYU5 Comdty': 112.60},
            'now': {'TYU5 Comdty': 112.70},
            'close': {}
        }
        
        # Mock time to before 2pm
        import unittest.mock
        with unittest.mock.patch('lib.trading.pnl_fifo_lifo.pnl_engine.get_current_time_period') as mock_time:
            mock_time.return_value = 'pre_2pm'
            
            unrealized = calculate_unrealized_pnl(positions, price_dicts, 'live')
            
            # For shorts, P&L is inverted
            # Base calc: ((112.55 - 112.50) + (112.70 - 112.55)) * 5 * 1000 = 1000
            # Inverted for short: -1000
            self.assertEqual(len(unrealized), 1)
            self.assertEqual(unrealized[0]['unrealizedPnL'], -1000)
    
    # ==================== COMPLEX SCENARIOS ====================
    
    def test_mixed_positions_realized_unrealized(self):
        """Test complex scenario with multiple trades and mixed P&L"""
        # Trade 1: Buy 10 @ 112.50
        trade1 = self._create_trade(1, 'TYU5 Comdty', 10, 112.50, 'B')
        process_new_trade(self.conn, trade1, 'fifo')
        
        # Trade 2: Buy 5 @ 112.25
        trade2 = self._create_trade(2, 'TYU5 Comdty', 5, 112.25, 'B')
        process_new_trade(self.conn, trade2, 'fifo')
        
        # Trade 3: Sell 12 @ 112.75
        trade3 = self._create_trade(3, 'TYU5 Comdty', 12, 112.75, 'S')
        realized = process_new_trade(self.conn, trade3, 'fifo')
        self.conn.commit()
        
        # Check realized P&L
        total_realized = sum(r['realizedPnL'] for r in realized)
        # First 10: (112.75 - 112.50) * 10 * 1000 = 2500
        # Next 2: (112.75 - 112.25) * 2 * 1000 = 1000
        # Total: 3500
        self.assertEqual(total_realized, 3500)
        
        # Check unrealized position (3 remaining @ 112.25)
        self._insert_price('TYU5 Comdty', 'sodTod', 112.30)
        self._insert_price('TYU5 Comdty', 'now', 112.40)
        
        positions = view_unrealized_positions(self.conn, 'fifo')
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions.iloc[0]['quantity'], 3)
        self.assertEqual(positions.iloc[0]['price'], 112.25)
        
        # Calculate unrealized P&L
        price_dicts = {
            'sodTod': {'TYU5 Comdty': 112.30},
            'sodTom': {'TYU5 Comdty': 112.35},
            'now': {'TYU5 Comdty': 112.40},
            'close': {}
        }
        
        import unittest.mock
        with unittest.mock.patch('lib.trading.pnl_fifo_lifo.pnl_engine.get_current_time_period') as mock_time:
            mock_time.return_value = 'pre_2pm'
            
            unrealized = calculate_unrealized_pnl(positions, price_dicts, 'live')
            # ((112.30 - 112.25) + (112.40 - 112.30)) * 3 * 1000 = 450
            self.assertEqual(unrealized[0]['unrealizedPnL'], 450)
    
    def test_close_pnl_calculation(self):
        """Test close P&L calculation using close prices"""
        # Insert a position
        buy_trade = self._create_trade(1, 'TYU5 Comdty', 10, 112.50, 'B')
        process_new_trade(self.conn, buy_trade, 'fifo')
        self.conn.commit()
        
        # Set up prices including close
        self._insert_price('TYU5 Comdty', 'sodTod', 112.55)
        self._insert_price('TYU5 Comdty', 'close', 112.65)
        
        positions = view_unrealized_positions(self.conn, 'fifo')
        price_dicts = {
            'sodTod': {'TYU5 Comdty': 112.55},
            'sodTom': {'TYU5 Comdty': 112.60},
            'now': {'TYU5 Comdty': 112.70},
            'close': {'TYU5 Comdty': 112.65}
        }
        
        # Calculate using 4pm_close method
        unrealized = calculate_unrealized_pnl(positions, price_dicts, '4pm_close')
        
        # 4pm close formula: ((sodTod - entry) + (close - sodTod)) * qty * 1000
        # ((112.55 - 112.50) + (112.65 - 112.55)) * 10 * 1000
        # (0.05 + 0.10) * 10 * 1000 = 1500
        self.assertEqual(len(unrealized), 1)
        self.assertEqual(unrealized[0]['unrealizedPnL'], 1500)


if __name__ == '__main__':
    unittest.main()