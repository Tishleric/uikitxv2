"""
Test the exact production pipeline for P&L calculation and insertion.
This test verifies that calculated unrealized P&L values correctly flow
from calculation through to database insertion.
"""

import sqlite3
import time
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch
import pandas as pd

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Importing modules...")
try:
    from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator
    print("✓ PositionsAggregator imported")
except Exception as e:
    print(f"✗ Failed to import PositionsAggregator: {e}")
    raise

try:
    from lib.trading.pnl_fifo_lifo.data_manager import create_all_tables
    print("✓ create_all_tables imported")
except Exception as e:
    print(f"✗ Failed to import create_all_tables: {e}")
    raise


class TestPnLInsertionPipeline:
    """Test the complete pipeline from P&L calculation to database insertion"""
    
    def setup_test_database(self, db_path):
        """Create test database with positions and prices"""
        conn = sqlite3.connect(db_path)
        
        # Create all required tables
        create_all_tables(conn)
        
        # Insert test positions in trades_fifo
        test_positions = [
            {
                'transactionId': 1,
                'symbol': 'TEST1',
                'price': 100.0,
                'quantity': 10,
                'buySell': 'B',
                'sequenceId': 'TEST-001',
                'time': '2025-01-21 10:00:00.000',
                'original_price': 100.0,
                'original_time': '2025-01-21 10:00:00.000',
                'fullPartial': 'full'
            },
            {
                'transactionId': 2,
                'symbol': 'TEST2',
                'price': 50.0,
                'quantity': 5,
                'buySell': 'S',
                'sequenceId': 'TEST-002',
                'time': '2025-01-21 11:00:00.000',
                'original_price': 50.0,
                'original_time': '2025-01-21 11:00:00.000',
                'fullPartial': 'full'
            }
        ]
        
        for pos in test_positions:
            conn.execute("""
                INSERT INTO trades_fifo 
                (transactionId, symbol, price, original_price, quantity, buySell, 
                 sequenceId, time, original_time, fullPartial)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pos['transactionId'], pos['symbol'], pos['price'], 
                  pos['original_price'], pos['quantity'], pos['buySell'],
                  pos['sequenceId'], pos['time'], pos['original_time'], 
                  pos['fullPartial']))
        
        # Insert test positions in trades_lifo (same data)
        for pos in test_positions:
            conn.execute("""
                INSERT INTO trades_lifo 
                (transactionId, symbol, price, original_price, quantity, buySell, 
                 sequenceId, time, original_time, fullPartial)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pos['transactionId'], pos['symbol'], pos['price'], 
                  pos['original_price'], pos['quantity'], pos['buySell'],
                  pos['sequenceId'], pos['time'], pos['original_time'], 
                  pos['fullPartial']))
        
        # Insert pricing data
        price_data = [
            # TEST1 prices
            ('TEST1', 'now', 102.0),      # Current price up $2
            ('TEST1', 'sodTod', 100.5),    # SOD today
            ('TEST1', 'sodTom', 101.0),    # SOD tomorrow
            ('TEST1', 'close', 101.5),     # Today's close
            # TEST2 prices  
            ('TEST2', 'now', 49.0),        # Current price down $1
            ('TEST2', 'sodTod', 49.5),     # SOD today
            ('TEST2', 'sodTom', 49.0),     # SOD tomorrow
            ('TEST2', 'close', 49.25),     # Today's close
        ]
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for symbol, price_type, price in price_data:
            conn.execute("""
                INSERT INTO pricing (symbol, price_type, price, timestamp)
                VALUES (?, ?, ?, ?)
            """, (symbol, price_type, price, timestamp))
        
        # Insert some realized P&L data for completeness
        conn.execute("""
            INSERT INTO realized_fifo (symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting,
                                     partialFull, quantity, entryPrice, exitPrice, realizedPnL, timestamp)
            VALUES ('TEST1', 'OLD-001', 'TEST-001', 'full', 5, 99.0, 100.0, 5000.0, ?)
        """, (timestamp,))
        
        conn.execute("""
            INSERT INTO realized_lifo (symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting,
                                     partialFull, quantity, entryPrice, exitPrice, realizedPnL, timestamp)
            VALUES ('TEST1', 'OLD-001', 'TEST-001', 'full', 5, 99.0, 100.0, 5000.0, ?)
        """, (timestamp,))
        
        conn.commit()
        conn.close()
        
    def verify_database_values(self, db_path):
        """Verify P&L values were correctly inserted"""
        conn = sqlite3.connect(db_path)
        
        # Query the positions table
        query = """
            SELECT 
                symbol,
                open_position,
                closed_position,
                fifo_realized_pnl,
                fifo_unrealized_pnl,
                lifo_realized_pnl,
                lifo_unrealized_pnl,
                fifo_unrealized_pnl_close,
                lifo_unrealized_pnl_close,
                last_updated
            FROM positions
            ORDER BY symbol
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print("\n=== DATABASE VERIFICATION ===")
        print(f"Rows in positions table: {len(df)}")
        
        if df.empty:
            raise AssertionError("No data found in positions table!")
        
        print("\nPositions table contents:")
        print(df.to_string(index=False))
        
        # Verify TEST1 (Buy position, should have positive unrealized P&L)
        test1 = df[df['symbol'] == 'TEST1']
        if not test1.empty:
            test1_row = test1.iloc[0]
            print(f"\nTEST1 Verification:")
            print(f"  Open Position: {test1_row['open_position']}")
            print(f"  FIFO Unrealized P&L: ${test1_row['fifo_unrealized_pnl']:.2f}")
            print(f"  LIFO Unrealized P&L: ${test1_row['lifo_unrealized_pnl']:.2f}")
            print(f"  FIFO Close P&L: ${test1_row['fifo_unrealized_pnl_close']:.2f}")
            print(f"  LIFO Close P&L: ${test1_row['lifo_unrealized_pnl_close']:.2f}")
            
            # Manual calculation check for TEST1
            # Buy 10 @ 100, now price 102
            # For simplicity, assuming pre-2pm and using sodTod as intermediate
            # P&L = ((sodTod - entry) + (now - sodTod)) * qty * 1000
            # P&L = ((100.5 - 100) + (102 - 100.5)) * 10 * 1000 = 20,000
            expected_pnl = 20000.0
            
            assert test1_row['fifo_unrealized_pnl'] > 0, "Buy position should have positive P&L when price rises"
            assert abs(test1_row['fifo_unrealized_pnl'] - expected_pnl) < 1, f"Expected ~${expected_pnl}, got ${test1_row['fifo_unrealized_pnl']}"
        
        # Verify TEST2 (Sell position, should have positive unrealized P&L when price falls)
        test2 = df[df['symbol'] == 'TEST2']
        if not test2.empty:
            test2_row = test2.iloc[0]
            print(f"\nTEST2 Verification:")
            print(f"  Open Position: {test2_row['open_position']}")
            print(f"  FIFO Unrealized P&L: ${test2_row['fifo_unrealized_pnl']:.2f}")
            print(f"  LIFO Unrealized P&L: ${test2_row['lifo_unrealized_pnl']:.2f}")
            
            # Sell positions have inverted P&L
            assert test2_row['fifo_unrealized_pnl'] > 0, "Sell position should have positive P&L when price falls"
        
        # Verify all required columns are populated
        assert len(df) == 2, f"Expected 2 rows, got {len(df)}"
        assert all(df['fifo_unrealized_pnl'].notna()), "FIFO unrealized P&L should not be null"
        assert all(df['lifo_unrealized_pnl'].notna()), "LIFO unrealized P&L should not be null"
        
        return df
        
    def test_pnl_insertion_pipeline(self):
        """Test the complete pipeline from calculation to database insertion"""
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            print("\n=== TESTING P&L INSERTION PIPELINE ===")
            
            # 1. Setup test database
            print("1. Setting up test database...")
            self.setup_test_database(db_path)
            
            # 2. Mock Redis to prevent connection attempts
            with patch('redis.Redis') as mock_redis_class:
                mock_redis = Mock()
                mock_redis.pubsub.return_value.listen.return_value = []
                mock_redis_class.return_value = mock_redis
                
                # 3. Start PositionsAggregator (real instance with real threads)
                print("2. Starting PositionsAggregator...")
                aggregator = PositionsAggregator(
                    trades_db_path=db_path,
                    spot_risk_db_path=db_path
                )
                aggregator.start()
                
                # Give threads time to start
                time.sleep(0.1)
                
                # 4. Trigger the exact same flow as Redis signal would
                print("3. Triggering _load_positions_from_db() (simulating Redis signal)...")
                aggregator._load_positions_from_db()
                
                # 5. Wait for writer thread to process (production behavior)
                print("4. Waiting for writer thread to process queue...")
                time.sleep(1.0)  # Give writer thread time to process
                
                # 6. Verify database insertion
                print("5. Verifying database values...")
                df = self.verify_database_values(db_path)
                
                # 7. Additional verification - check cache state
                print("\n=== CACHE STATE ===")
                if not aggregator.positions_cache.empty:
                    print(f"Positions in cache: {len(aggregator.positions_cache)}")
                    for _, row in aggregator.positions_cache.iterrows():
                        print(f"  {row['symbol']}: FIFO P&L=${row['fifo_unrealized_pnl']:.2f}")
                
                # 8. Stop aggregator
                print("\n6. Stopping aggregator...")
                aggregator.stop()
                
                print("\n✓ TEST PASSED - P&L values successfully flowed from calculation to database!")
                
        except Exception as e:
            print(f"\n✗ TEST FAILED: {str(e)}")
            raise
            
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == "__main__":
    test = TestPnLInsertionPipeline()
    test.test_pnl_insertion_pipeline()