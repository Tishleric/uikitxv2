"""
End-to-end test simulating the complete flow from trade entry to dashboard display.

Flow:
1. Trade Entry (CSV file creation)
2. Trade Ledger Watcher detection
3. Trade processing (FIFO/LIFO)
4. Positions aggregation
5. Dashboard query
"""

import sqlite3
import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
import os

# Add parent directories to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade
from lib.trading.pnl_fifo_lifo.data_manager import create_all_tables, get_trading_day, update_daily_position
from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator


class TestEndToEndFlow:
    """Test the complete flow from trade entry to dashboard display."""
    
    @pytest.fixture
    def test_directory(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_database(self, test_directory):
        """Create a test database with required tables."""
        db_path = os.path.join(test_directory, "test_trades.db")
        conn = sqlite3.connect(db_path)
        create_all_tables(conn)
        
        # Also create the positions and pricing tables
        conn.execute("""
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
                fifo_unrealized_pnl_close REAL DEFAULT 0,
                lifo_unrealized_pnl_close REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_trade_update TIMESTAMP,
                last_greek_update TIMESTAMP,
                has_greeks BOOLEAN DEFAULT 0,
                instrument_type TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pricing (
                symbol TEXT,
                price_type TEXT,
                price REAL,
                timestamp TEXT,
                PRIMARY KEY (symbol, price_type)
            )
        """)
        
        conn.commit()
        conn.close()
        
        return db_path
    
    def simulate_trade_processing(self, db_path, trades):
        """Simulate what the trade ledger watcher does."""
        conn = sqlite3.connect(db_path)
        
        # Get max sequence number (simulating trade_ledger_watcher logic)
        cursor = conn.cursor()
        max_seq_query = """
            SELECT MAX(CAST(SUBSTR(sequenceId, INSTR(sequenceId, '-') + 1) AS INTEGER))
            FROM (
                SELECT sequenceId FROM trades_fifo
                UNION ALL
                SELECT sequenceId FROM trades_lifo
            )
        """
        result = cursor.execute(max_seq_query).fetchone()
        start_seq = (result[0] or 0) + 1
        
        # Process each trade
        for idx, trade in enumerate(trades):
            # Add sequenceId if not provided
            if 'sequenceId' not in trade:
                trade['sequenceId'] = f"{trade['time'][:10].replace('-', '')}-{start_seq + idx}"
            
            # Process through both FIFO and LIFO
            for method in ['fifo', 'lifo']:
                process_new_trade(conn, trade, method, trade['time'][:19])
                
                # Update daily position tracking (simulating trade_ledger_watcher)
                realized = pd.read_sql_query(
                    f"SELECT SUM(realizedPnL) as pnl, SUM(quantity) as qty "
                    f"FROM realized_{method} WHERE sequenceIdDoingOffsetting = ?", 
                    conn, params=(trade['sequenceId'],)
                )
                realized_qty = abs(realized['qty'].iloc[0] or 0)
                realized_pnl_delta = realized['pnl'].iloc[0] or 0
                
                trade_date_str = get_trading_day(
                    datetime.strptime(trade['time'], '%Y-%m-%d %H:%M:%S.%f')
                ).strftime('%Y-%m-%d')
                
                update_daily_position(conn, trade_date_str, trade['symbol'], method, 
                                    realized_qty, realized_pnl_delta)
        
        conn.commit()
        conn.close()
    
    def test_complete_flow(self, test_database):
        """Test the complete flow from trade entry to dashboard display."""
        # Step 1: Define test trades
        trades = [
            {
                'transactionId': 1001,
                'symbol': 'TYH5 Comdty',
                'price': 110.25,
                'quantity': 10,
                'buySell': 'B',
                'time': '2024-01-15 09:30:00.000',
                'fullPartial': 'full'
            },
            {
                'transactionId': 1002,
                'symbol': 'ESH5 Comdty',
                'price': 4000.00,
                'quantity': 5,
                'buySell': 'B',
                'time': '2024-01-15 10:00:00.000',
                'fullPartial': 'full'
            },
            {
                'transactionId': 1003,
                'symbol': 'TYH5 Comdty',
                'price': 110.50,
                'quantity': 4,
                'buySell': 'S',  # Partial offset
                'time': '2024-01-15 11:00:00.000',
                'fullPartial': 'full'
            },
            {
                'transactionId': 1004,
                'symbol': 'CLH5 Comdty',
                'price': 75.00,
                'quantity': 20,
                'buySell': 'B',
                'time': '2024-01-15 12:00:00.000',
                'fullPartial': 'full'
            },
            {
                'transactionId': 1005,
                'symbol': 'CLH5 Comdty',
                'price': 76.00,
                'quantity': 20,
                'buySell': 'S',  # Full offset
                'time': '2024-01-15 13:00:00.000',
                'fullPartial': 'full'
            }
        ]
        
        # Step 2: Simulate trade processing (what trade_ledger_watcher does)
        self.simulate_trade_processing(test_database, trades)
        
        # Step 3: Run positions aggregator (simulating the service)
        aggregator = PositionsAggregator(trades_db_path=test_database)
        aggregator._load_positions_from_db()
        
        # Add some dummy prices for unrealized P&L calculation
        conn = sqlite3.connect(test_database)
        conn.execute("INSERT INTO pricing VALUES ('TYH5 Comdty', 'now', 110.75, '2024-01-15 14:00:00')")
        conn.execute("INSERT INTO pricing VALUES ('ESH5 Comdty', 'now', 4010.00, '2024-01-15 14:00:00')")
        conn.commit()
        conn.close()
        
        # Re-load to calculate unrealized P&L
        aggregator._load_positions_from_db()
        aggregator._write_positions_to_db(aggregator.positions_cache)
        
        # Step 4: Simulate dashboard query
        conn = sqlite3.connect(test_database)
        dashboard_query = """
        SELECT 
            p.symbol,
            p.instrument_type,
            p.open_position,
            p.closed_position,
            p.fifo_realized_pnl,
            p.fifo_unrealized_pnl,
            (p.fifo_realized_pnl + p.fifo_unrealized_pnl) as pnl_live,
            p.last_updated
        FROM positions p
        WHERE p.open_position != 0 OR p.closed_position != 0
        ORDER BY p.symbol
        """
        
        df = pd.read_sql_query(dashboard_query, conn)
        conn.close()
        
        # Step 5: Verify results
        assert len(df) == 3  # Three symbols
        
        # Check CLH5 (fully closed)
        clh5 = df[df['symbol'] == 'CLH5 Comdty'].iloc[0]
        assert clh5['open_position'] == 0
        assert clh5['closed_position'] == 20
        assert clh5['fifo_realized_pnl'] == 20000  # (76-75) * 20 * 1000
        assert clh5['fifo_unrealized_pnl'] == 0
        assert clh5['pnl_live'] == 20000
        
        # Check ESH5 (open position)
        esh5 = df[df['symbol'] == 'ESH5 Comdty'].iloc[0]
        assert esh5['open_position'] == 5
        assert esh5['closed_position'] == 0
        assert esh5['fifo_realized_pnl'] == 0
        assert esh5['fifo_unrealized_pnl'] == 50000  # (4010-4000) * 5 * 1000
        assert esh5['pnl_live'] == 50000
        
        # Check TYH5 (partially closed)
        tyh5 = df[df['symbol'] == 'TYH5 Comdty'].iloc[0]
        assert tyh5['open_position'] == 6  # 10 - 4
        assert tyh5['closed_position'] == 4
        assert tyh5['fifo_realized_pnl'] == 1000  # (110.50-110.25) * 4 * 1000
        assert tyh5['fifo_unrealized_pnl'] == 3000  # (110.75-110.25) * 6 * 1000
        assert tyh5['pnl_live'] == 4000
        
        print("\n=== Dashboard Display Results ===")
        print(df.to_string())
        print("\nAll assertions passed! End-to-end flow working correctly.")
    
    def test_aggregator_query_matches_implementation(self, test_database):
        """Verify that our test query matches the actual implementation."""
        # Insert test data
        trades = [
            {
                'transactionId': 2001,
                'symbol': 'NGH5 Comdty',
                'price': 3.50,
                'quantity': 100,
                'buySell': 'B',
                'time': '2024-01-15 09:00:00.000',
                'fullPartial': 'full'
            },
            {
                'transactionId': 2002,
                'symbol': 'NGH5 Comdty',
                'price': 3.60,
                'quantity': 40,
                'buySell': 'S',
                'time': '2024-01-15 10:00:00.000',
                'fullPartial': 'full'
            }
        ]
        
        self.simulate_trade_processing(test_database, trades)
        
        # Run the actual aggregator
        aggregator = PositionsAggregator(trades_db_path=test_database)
        aggregator._load_positions_from_db()
        
        # Verify the loaded data
        assert len(aggregator.positions_cache) == 1
        ngh5 = aggregator.positions_cache.iloc[0]
        assert ngh5['symbol'] == 'NGH5 Comdty'
        assert ngh5['open_position'] == 60  # 100 - 40
        assert ngh5['closed_position'] == 40
        assert abs(ngh5['fifo_realized_pnl'] - 4000) < 0.01  # (3.60-3.50) * 40 * 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])