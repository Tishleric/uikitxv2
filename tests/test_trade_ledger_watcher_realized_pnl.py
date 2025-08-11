"""
Unit test that mimics the exact process used by TradeLedgerWatcher
for calculating FIFO realized P&L from trade CSV files.

This test replicates the actual production flow:
1. Read trades from CSV
2. Translate symbols using RosettaStone
3. Process trades through FIFO engine
4. Calculate and store realized P&L
"""

import unittest
import sqlite3
import pandas as pd
import tempfile
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.trading.pnl_fifo_lifo.pnl_engine import process_new_trade
from lib.trading.pnl_fifo_lifo.data_manager import (
    create_all_tables, 
    get_trading_day,
    update_daily_position
)
from lib.trading.market_prices.rosetta_stone import RosettaStone


class TestTradeLedgerWatcherRealizedPnL(unittest.TestCase):
    """Test FIFO realized P&L calculation mimicking TradeLedgerWatcher process"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.test_db_path)
        create_all_tables(self.conn)
        
        # Create temporary directory for CSV files
        self.csv_dir = tempfile.mkdtemp()
        
        # Initialize symbol translator
        self.translator = RosettaStone()
        
    def tearDown(self):
        """Clean up test environment"""
        self.conn.close()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
        
        # Clean up CSV directory
        for file in Path(self.csv_dir).glob('*.csv'):
            file.unlink()
        os.rmdir(self.csv_dir)
    
    def _create_trade_csv(self, filename, trades_data):
        """Create a CSV file mimicking the trade ledger format"""
        df = pd.DataFrame(trades_data)
        csv_path = Path(self.csv_dir) / filename
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def _process_trade_file_like_watcher(self, csv_path):
        """Process a trade file exactly like TradeLedgerWatcher does"""
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Parse datetime and create sequenceId
        df['marketTradeTime'] = pd.to_datetime(df['marketTradeTime'])
        df['trading_day'] = df['marketTradeTime'].apply(get_trading_day)
        df['date'] = df['trading_day'].apply(lambda d: d.strftime('%Y%m%d'))
        
        # Get the max sequence number for proper sequencing
        cursor = self.conn.cursor()
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
        trade_count = 0
        all_realized_pnl = []
        
        for idx, row in df.iterrows():
            # Translate symbol to Bloomberg format
            bloomberg_symbol = self.translator.translate(
                row['instrumentName'], 
                'actanttrades', 
                'bloomberg'
            )
            if not bloomberg_symbol:
                bloomberg_symbol = row['instrumentName']  # Fallback
            
            trade = {
                'transactionId': row['tradeId'],
                'symbol': bloomberg_symbol,
                'price': row['price'],
                'quantity': row['quantity'],
                'buySell': row['buySell'],
                'sequenceId': f"{row['date']}-{start_seq + trade_count}",
                'time': row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'fullPartial': 'full'
            }
            
            # Process through FIFO (mimicking the watcher)
            realized_trades = process_new_trade(
                self.conn, 
                trade, 
                'fifo',
                row['marketTradeTime'].strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # Update daily position tracking (realized only)
            if realized_trades:
                realized_query = pd.read_sql_query(
                    f"SELECT SUM(realizedPnL) as pnl, SUM(quantity) as qty FROM realized_fifo WHERE sequenceIdDoingOffsetting = ?", 
                    self.conn, 
                    params=(trade['sequenceId'],)
                )
                realized_qty = realized_query['qty'].iloc[0] or 0
                realized_pnl_delta = realized_query['pnl'].iloc[0] or 0
                
                trade_date_str = get_trading_day(row['marketTradeTime']).strftime('%Y-%m-%d')
                
                update_daily_position(
                    self.conn, 
                    trade_date_str, 
                    bloomberg_symbol, 
                    'fifo',
                    realized_qty, 
                    realized_pnl_delta
                )
                
                all_realized_pnl.extend(realized_trades)
            
            trade_count += 1
        
        # Commit all changes
        self.conn.commit()
        
        return all_realized_pnl, trade_count
    
    def test_basic_realized_pnl_from_csv(self):
        """Test basic realized P&L calculation from CSV trades"""
        # Create trade data mimicking actual CSV format
        # Using Bloomberg format directly since translation will fallback to original
        trades_data = [
            {
                'tradeId': 'T001',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 09:30:00.000',
                'price': 112.50,
                'quantity': 10,
                'buySell': 'B'
            },
            {
                'tradeId': 'T002',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 10:30:00.000',
                'price': 112.75,
                'quantity': 10,
                'buySell': 'S'
            }
        ]
        
        # Create CSV and process
        csv_path = self._create_trade_csv('trades_20240115.csv', trades_data)
        realized_pnl, trade_count = self._process_trade_file_like_watcher(csv_path)
        
        # Verify results
        self.assertEqual(trade_count, 2)
        self.assertEqual(len(realized_pnl), 1)
        
        # Expected P&L: (112.75 - 112.50) * 10 * 1000 = $2,500
        self.assertEqual(realized_pnl[0]['realizedPnL'], 2500)
        self.assertEqual(realized_pnl[0]['entryPrice'], 112.50)
        self.assertEqual(realized_pnl[0]['exitPrice'], 112.75)
        
        # Verify database state
        realized_df = pd.read_sql_query(
            "SELECT * FROM realized_fifo",
            self.conn
        )
        self.assertEqual(len(realized_df), 1)
        self.assertEqual(realized_df.iloc[0]['realizedPnL'], 2500)
    
    def test_partial_fill_realized_pnl(self):
        """Test partial fill scenario as processed by watcher"""
        trades_data = [
            {
                'tradeId': 'T001',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 09:00:00.000',
                'price': 112.50,
                'quantity': 10,
                'buySell': 'B'
            },
            {
                'tradeId': 'T002',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 10:00:00.000',
                'price': 112.25,
                'quantity': 5,
                'buySell': 'B'
            },
            {
                'tradeId': 'T003',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 11:00:00.000',
                'price': 112.75,
                'quantity': 12,
                'buySell': 'S'
            }
        ]
        
        csv_path = self._create_trade_csv('trades_20240115.csv', trades_data)
        realized_pnl, trade_count = self._process_trade_file_like_watcher(csv_path)
        
        # Should have 2 realizations (10 full, 2 partial)
        self.assertEqual(len(realized_pnl), 2)
        
        # First realization: 10 @ 112.50
        self.assertEqual(realized_pnl[0]['quantity'], 10)
        self.assertEqual(realized_pnl[0]['realizedPnL'], 2500)  # (112.75-112.50)*10*1000
        
        # Second realization: 2 @ 112.25
        self.assertEqual(realized_pnl[1]['quantity'], 2)
        self.assertEqual(realized_pnl[1]['realizedPnL'], 1000)  # (112.75-112.25)*2*1000
        
        # Verify remaining position
        trades_df = pd.read_sql_query(
            "SELECT * FROM trades_fifo WHERE quantity > 0",
            self.conn
        )
        self.assertEqual(len(trades_df), 1)
        self.assertEqual(trades_df.iloc[0]['quantity'], 3)  # 5 - 2 = 3 remaining
    
    def test_multiple_symbols_realized_pnl(self):
        """Test multiple symbols processed in same file"""
        trades_data = [
            # TYU5 trades
            {
                'tradeId': 'T001',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 09:00:00.000',
                'price': 112.50,
                'quantity': 10,
                'buySell': 'B'
            },
            # ZNU5 trades
            {
                'tradeId': 'T002',
                'instrumentName': 'ZNU5 Comdty',
                'marketTradeTime': '2024-01-15 09:30:00.000',
                'price': 120.00,
                'quantity': 5,
                'buySell': 'S'
            },
            # Close TYU5
            {
                'tradeId': 'T003',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 10:00:00.000',
                'price': 112.75,
                'quantity': 10,
                'buySell': 'S'
            },
            # Close ZNU5
            {
                'tradeId': 'T004',
                'instrumentName': 'ZNU5 Comdty',
                'marketTradeTime': '2024-01-15 10:30:00.000',
                'price': 119.75,
                'quantity': 5,
                'buySell': 'B'
            }
        ]
        
        csv_path = self._create_trade_csv('trades_20240115.csv', trades_data)
        realized_pnl, trade_count = self._process_trade_file_like_watcher(csv_path)
        
        self.assertEqual(trade_count, 4)
        self.assertEqual(len(realized_pnl), 2)
        
        # Find P&L for each symbol
        tyu5_pnl = [r for r in realized_pnl if 'TYU5' in r['symbol']][0]
        znu5_pnl = [r for r in realized_pnl if 'ZNU5' in r['symbol']][0]
        
        # TYU5: Long position closed with profit
        self.assertEqual(tyu5_pnl['realizedPnL'], 2500)  # (112.75-112.50)*10*1000
        
        # ZNU5: Short position closed with profit
        self.assertEqual(znu5_pnl['realizedPnL'], 1250)  # (120.00-119.75)*5*1000
    
    def test_daily_position_updates(self):
        """Test that daily positions are updated correctly"""
        trades_data = [
            {
                'tradeId': 'T001',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 09:00:00.000',
                'price': 112.50,
                'quantity': 10,
                'buySell': 'B'
            },
            {
                'tradeId': 'T002',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 14:00:00.000',
                'price': 112.75,
                'quantity': 6,
                'buySell': 'S'
            }
        ]
        
        csv_path = self._create_trade_csv('trades_20240115.csv', trades_data)
        realized_pnl, trade_count = self._process_trade_file_like_watcher(csv_path)
        
        # Check daily positions table
        daily_positions = pd.read_sql_query(
            "SELECT * FROM daily_positions WHERE symbol LIKE '%TYU5%' AND method = 'fifo'",
            self.conn
        )
        
        self.assertEqual(len(daily_positions), 1)
        position = daily_positions.iloc[0]
        
        # Verify daily position values
        self.assertEqual(position['closed_position'], 6)
        self.assertEqual(position['realized_pnl'], 1500)  # (112.75-112.50)*6*1000
        self.assertEqual(position['open_position'], 4)  # 10 - 6 = 4 remaining
    
    def test_sequence_id_generation(self):
        """Test that sequence IDs are generated correctly"""
        # First batch of trades
        trades_data1 = [
            {
                'tradeId': 'T001',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 09:00:00.000',
                'price': 112.50,
                'quantity': 10,
                'buySell': 'B'
            }
        ]
        
        csv_path1 = self._create_trade_csv('trades_20240115_1.csv', trades_data1)
        self._process_trade_file_like_watcher(csv_path1)
        
        # Second batch of trades - Buy more instead of sell to ensure it stays in trades_fifo
        trades_data2 = [
            {
                'tradeId': 'T002',
                'instrumentName': 'TYU5 Comdty',
                'marketTradeTime': '2024-01-15 10:00:00.000',
                'price': 112.45,
                'quantity': 5,
                'buySell': 'B'
            }
        ]
        
        csv_path2 = self._create_trade_csv('trades_20240115_2.csv', trades_data2)
        self._process_trade_file_like_watcher(csv_path2)
        
        # Check sequence IDs are properly incremented
        trades = pd.read_sql_query(
            "SELECT sequenceId FROM trades_fifo WHERE quantity > 0 ORDER BY sequenceId",
            self.conn
        )
        
        # Should have format: YYYYMMDD-N where N increments
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades.iloc[0]['sequenceId'], '20240115-1')
        self.assertEqual(trades.iloc[1]['sequenceId'], '20240115-2')


if __name__ == '__main__':
    unittest.main()