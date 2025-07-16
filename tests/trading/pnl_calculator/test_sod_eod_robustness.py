"""Comprehensive test suite for SOD/EOD P&L calculation robustness."""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta, time
from decimal import Decimal
import pytz

from lib.trading.pnl_calculator.storage import PnLStorage
from lib.trading.pnl_calculator.position_manager import PositionManager


class TestSODEODRobustness(unittest.TestCase):
    """Test SOD/EOD P&L calculations for robustness and accuracy."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_sod_eod.db"
        self.storage = PnLStorage(str(self.db_path))
        self.position_manager = PositionManager(self.storage)
        self.chicago_tz = pytz.timezone('America/Chicago')
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def _create_position(self, symbol: str, qty: float, avg_cost: float, 
                        realized_pnl: float = 0.0):
        """Helper to create a position in the database."""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO positions (
                instrument_name, position_quantity, avg_cost,
                total_realized_pnl, unrealized_pnl, last_updated,
                is_option
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, qty, avg_cost, realized_pnl, 0.0, datetime.now(), 
              1 if symbol.startswith('O') else 0))
        
        conn.commit()
        conn.close()
        
    def test_sod_snapshot_accuracy(self):
        """Test that SOD snapshots capture exact position state."""
        # Create positions at various times during the day
        positions = [
            ('TYH5', 10, 110.5, 50.0),      # Long futures with realized P&L
            ('TUM5', -5, 105.25, -25.0),    # Short futures with loss
            ('OTYH5 C11000', 20, 1.5, 10.0), # Options with profit
            ('TYZ5', 0, 110.0, 100.0),      # Flat position with P&L
        ]
        
        for symbol, qty, avg_cost, realized_pnl in positions:
            if qty != 0:  # Only create non-zero positions
                self._create_position(symbol, qty, avg_cost, realized_pnl)
        
        # Take SOD snapshot at 5pm Chicago time
        sod_time = datetime.now(self.chicago_tz).replace(hour=17, minute=0, second=0)
        self.position_manager.take_snapshot('SOD', sod_time)
        
        # Verify snapshot accuracy
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT instrument_name, position_quantity, avg_cost, 
                   total_realized_pnl, unrealized_pnl
            FROM position_snapshots
            WHERE snapshot_type = 'SOD'
            ORDER BY instrument_name
        """)
        
        snapshots = cursor.fetchall()
        conn.close()
        
        # Should have 3 snapshots (excluding flat position)
        self.assertEqual(len(snapshots), 3)
        
        # Verify each snapshot
        expected = {
            'OTYH5 C11000': (20, 1.5, 10.0),
            'TYH5': (10, 110.5, 50.0),
            'TUM5': (-5, 105.25, -25.0),
        }
        
        for snapshot in snapshots:
            symbol = snapshot[0]
            self.assertIn(symbol, expected)
            exp_qty, exp_avg, exp_real = expected[symbol]
            
            self.assertEqual(snapshot[1], exp_qty)  # position_quantity
            self.assertEqual(snapshot[2], exp_avg)  # avg_cost
            self.assertEqual(snapshot[3], exp_real) # realized_pnl
            
    def test_eod_snapshot_with_intraday_changes(self):
        """Test EOD snapshot after intraday trading activity."""
        # Morning positions
        self._create_position('TYH5', 10, 110.0)
        self._create_position('TUM5', -5, 105.0)
        
        # Take SOD snapshot
        sod_time = datetime.now(self.chicago_tz).replace(hour=17, minute=0, second=0)
        sod_time = sod_time - timedelta(days=1)  # Previous day 5pm
        self.position_manager.take_snapshot('SOD', sod_time)
        
        # Simulate intraday trades (would normally come through position updates)
        # Close half of TYH5 position with profit
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE positions
            SET position_quantity = 5,
                total_realized_pnl = 2.5,  -- 5 * (110.5 - 110.0)
                last_updated = ?
            WHERE instrument_name = 'TYH5'
        """, (datetime.now(),))
        
        # Add to short position
        cursor.execute("""
            UPDATE positions
            SET position_quantity = -8,
                avg_cost = 105.1875,  -- Weighted average
                last_updated = ?
            WHERE instrument_name = 'TUM5'
        """, (datetime.now(),))
        
        conn.commit()
        conn.close()
        
        # Take EOD snapshot at 4pm
        eod_time = datetime.now(self.chicago_tz).replace(hour=16, minute=0, second=0)
        self.position_manager.take_snapshot('EOD', eod_time)
        
        # Verify both snapshots exist with correct data
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        # Check SOD
        cursor.execute("""
            SELECT COUNT(*) FROM position_snapshots
            WHERE snapshot_type = 'SOD'
        """)
        self.assertEqual(cursor.fetchone()[0], 2)  # TYH5 and TUM5
        
        # Check EOD
        cursor.execute("""
            SELECT instrument_name, position_quantity, total_realized_pnl
            FROM position_snapshots
            WHERE snapshot_type = 'EOD'
            ORDER BY instrument_name
        """)
        
        eod_snapshots = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(eod_snapshots), 2)
        
        # Verify EOD reflects intraday changes
        eod_data = {row[0]: (row[1], row[2]) for row in eod_snapshots}
        
        self.assertEqual(eod_data['TYH5'][0], 5)    # Reduced position
        self.assertEqual(eod_data['TYH5'][1], 2.5)  # Realized P&L
        self.assertEqual(eod_data['TUM5'][0], -8)   # Increased short
        
    def test_precision_in_snapshots(self):
        """Test that snapshots maintain proper decimal precision."""
        # Create positions with problematic values
        test_positions = [
            ('TYU5', 7, 110.03125, 4.8125),     # Would cause 4.75000000001
            ('TYH5', 3, 99.99999, 1.23456),     # Many decimals
            ('OTYM5 C11000', 11, 0.54321, 0.1), # Option with decimals
        ]
        
        for symbol, qty, avg_cost, realized_pnl in test_positions:
            self._create_position(symbol, qty, avg_cost, realized_pnl)
            
        # Update market prices to trigger unrealized P&L calculations
        market_prices = {
            'TYU5': 110.71875,
            'TYH5': 100.12345,
            'OTYM5 C11000': 0.6789,
        }
        
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        for symbol, mkt_price in market_prices.items():
            cursor.execute("""
                UPDATE positions
                SET last_market_price = ?,
                    unrealized_pnl = ROUND((? - avg_cost) * position_quantity, ?)
                WHERE instrument_name = ?
            """, (mkt_price, mkt_price, 4 if symbol.startswith('O') else 5, symbol))
            
        conn.commit()
        
        # Take snapshot
        snapshot_time = datetime.now()
        self.position_manager.take_snapshot('TEST', snapshot_time)
        
        # Verify precision in snapshots
        cursor.execute("""
            SELECT instrument_name, unrealized_pnl, total_realized_pnl
            FROM position_snapshots
            WHERE snapshot_type = 'TEST'
        """)
        
        for row in cursor.fetchall():
            symbol, unreal_pnl, real_pnl = row
            
            # Check decimal places
            for value in [unreal_pnl, real_pnl]:
                if value and '.' in str(value):
                    decimals = len(str(value).rstrip('0').split('.')[1])
                    self.assertLessEqual(
                        decimals, 5,
                        f"{symbol} has {decimals} decimal places in P&L"
                    )
                    
        conn.close()
        
    def test_boundary_conditions(self):
        """Test P&L calculations at day boundaries."""
        # Position opened right before SOD (4:59pm)
        pre_sod = datetime.now(self.chicago_tz).replace(hour=16, minute=59, second=0)
        self._create_position('TYH5', 10, 110.0)
        
        # SOD snapshot at 5:00pm
        sod_time = pre_sod + timedelta(minutes=1)
        self.position_manager.take_snapshot('SOD', sod_time)
        
        # Trade at midnight (SOD marker)
        midnight = sod_time.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        
        # Trade right before EOD (3:59pm)
        pre_eod = midnight.replace(hour=15, minute=59, second=0)
        
        # EOD snapshot at 4:00pm
        eod_time = pre_eod + timedelta(minutes=1)
        self.position_manager.take_snapshot('EOD', eod_time)
        
        # Verify both snapshots captured correctly
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*), snapshot_type
            FROM position_snapshots
            GROUP BY snapshot_type
        """)
        
        results = {row[1]: row[0] for row in cursor.fetchall()}
        conn.close()
        
        self.assertEqual(results.get('SOD', 0), 1)
        self.assertEqual(results.get('EOD', 0), 1)
        
    def test_zero_position_handling(self):
        """Test that zero positions are not included in snapshots."""
        # Create mix of zero and non-zero positions
        positions = [
            ('TYH5', 10, 110.0, 0.0),    # Active position
            ('TUM5', 0, 105.0, 50.0),     # Flat with P&L
            ('TYZ5', 0, 0.0, 0.0),        # Completely flat
            ('TYF6', -5, 111.0, -10.0),   # Active short
        ]
        
        for symbol, qty, avg_cost, realized_pnl in positions:
            if qty != 0 or realized_pnl != 0:
                # Only create if non-zero position or has realized P&L
                self._create_position(symbol, qty, avg_cost, realized_pnl)
        
        # Take snapshot
        snapshot_time = datetime.now()
        self.position_manager.take_snapshot('TEST', snapshot_time)
        
        # Verify only non-zero positions are in snapshot
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT instrument_name, position_quantity
            FROM position_snapshots
            WHERE snapshot_type = 'TEST'
            ORDER BY instrument_name
        """)
        
        snapshots = cursor.fetchall()
        conn.close()
        
        # Should only have TYH5 and TYF6
        self.assertEqual(len(snapshots), 2)
        
        symbols_in_snapshot = [row[0] for row in snapshots]
        self.assertIn('TYH5', symbols_in_snapshot)
        self.assertIn('TYF6', symbols_in_snapshot)
        self.assertNotIn('TUM5', symbols_in_snapshot)  # Flat position
        self.assertNotIn('TYZ5', symbols_in_snapshot)  # Never created
        

class TestIntraDayPnLAccuracy(unittest.TestCase):
    """Test intraday P&L tracking accuracy."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_intraday.db"
        self.storage = PnLStorage(str(self.db_path))
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_continuous_pnl_tracking(self):
        """Test that P&L is tracked accurately throughout the day."""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        # Simulate a trading day
        trades = [
            # (time, symbol, qty, price, expected_realized_pnl)
            ('08:00', 'TYH5', 10, 110.0, 0.0),       # Open long
            ('10:00', 'TYH5', 5, 110.25, 0.0),       # Add to long
            ('12:00', 'TYH5', -7, 110.5, 3.5),       # Partial close with profit
            ('14:00', 'TYH5', -8, 110.375, 3.0),     # Close position
            ('15:00', 'TYH5', -5, 110.4, 0.0),       # Open short
        ]
        
        position_qty = 0
        total_cost = 0.0
        cumulative_realized = 0.0
        
        for time_str, symbol, trade_qty, price, expected_real in trades:
            # Update position tracking
            if trade_qty > 0:
                # Buy
                position_qty += trade_qty
                total_cost += trade_qty * price
            else:
                # Sell
                if position_qty > 0:
                    # Closing long
                    qty_to_close = min(position_qty, abs(trade_qty))
                    avg_cost = total_cost / position_qty if position_qty > 0 else 0
                    realized = qty_to_close * (price - avg_cost)
                    realized = round(realized, 5)
                    cumulative_realized += realized
                    
                    # Update position
                    position_qty -= qty_to_close
                    total_cost = avg_cost * position_qty if position_qty > 0 else 0
                    
                    # Check if we're going short
                    remaining = abs(trade_qty) - qty_to_close
                    if remaining > 0:
                        position_qty = -remaining
                        total_cost = remaining * price
                else:
                    # Already short, adding to short
                    position_qty += trade_qty  # trade_qty is negative
                    total_cost += abs(trade_qty) * price
            
            # Verify expected realized P&L
            if expected_real > 0:
                self.assertAlmostEqual(
                    cumulative_realized, 
                    sum(t[4] for t in trades[:trades.index((time_str, symbol, trade_qty, price, expected_real)) + 1]),
                    places=5,
                    msg=f"Realized P&L mismatch at {time_str}"
                )
        
        conn.close()


if __name__ == '__main__':
    unittest.main() 