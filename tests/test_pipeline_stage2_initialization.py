"""
Stage 2: Test module import and PositionsAggregator initialization.
This test ensures we can import and initialize the aggregator properly.
"""

print("Starting Stage 2 test...")

import sqlite3
import pandas as pd
import tempfile
import os
import sys
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

print("Adding project path...")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dependencies one by one to identify issues
print("\n1. Importing dependencies...")

try:
    from lib.trading.pnl_fifo_lifo.data_manager import create_all_tables
    print("   ✓ data_manager imported")
except Exception as e:
    print(f"   ✗ Failed to import data_manager: {e}")
    raise

try:
    # Mock SpotRiskDatabaseService before importing PositionsAggregator
    sys.modules['lib.trading.actant.spot_risk.database'] = Mock()
    sys.modules['lib.trading.actant.spot_risk.database'].SpotRiskDatabaseService = Mock
    
    from lib.trading.pnl_fifo_lifo.positions_aggregator import PositionsAggregator
    print("   ✓ PositionsAggregator imported")
except Exception as e:
    print(f"   ✗ Failed to import PositionsAggregator: {e}")
    raise

try:
    import redis
    print("   ✓ redis module imported")
except Exception as e:
    print(f"   ✗ Failed to import redis: {e}")
    raise


class TestStage2Initialization:
    """Stage 2: Test PositionsAggregator initialization"""
    
    def setup_test_database(self, db_path):
        """Recreate the same test data from Stage 1"""
        conn = sqlite3.connect(db_path)
        create_all_tables(conn)
        
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # Same positions as Stage 1
        fifo_positions = [
            {
                'transactionId': 1,
                'symbol': 'FUTURES1',
                'price': 100.0,
                'quantity': 10,
                'buySell': 'B',
                'sequenceId': 'YEST-001',
                'time': yesterday.strftime('%Y-%m-%d %H:%M:%S.000'),
                'original_price': 100.0,
                'original_time': yesterday.strftime('%Y-%m-%d %H:%M:%S.000'),
                'fullPartial': 'full'
            },
            {
                'transactionId': 2,
                'symbol': 'FUTURES1',
                'price': 101.5,
                'quantity': 5,
                'buySell': 'B',
                'sequenceId': 'TODAY-001',
                'time': now.strftime('%Y-%m-%d %H:%M:%S.000'),
                'original_price': 101.5,
                'original_time': now.strftime('%Y-%m-%d %H:%M:%S.000'),
                'fullPartial': 'full'
            },
            {
                'transactionId': 3,
                'symbol': 'FUTURES2',
                'price': 50.0,
                'quantity': 20,
                'buySell': 'S',
                'sequenceId': 'TODAY-002',
                'time': now.strftime('%Y-%m-%d %H:%M:%S.000'),
                'original_price': 50.0,
                'original_time': now.strftime('%Y-%m-%d %H:%M:%S.000'),
                'fullPartial': 'full'
            }
        ]
        
        # Insert into both FIFO and LIFO tables
        for pos in fifo_positions:
            for table in ['trades_fifo', 'trades_lifo']:
                conn.execute(f"""
                    INSERT INTO {table}
                    (transactionId, symbol, price, original_price, quantity, buySell, 
                     sequenceId, time, original_time, fullPartial)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pos['transactionId'], pos['symbol'], pos['price'], 
                      pos['original_price'], pos['quantity'], pos['buySell'],
                      pos['sequenceId'], pos['time'], pos['original_time'], 
                      pos['fullPartial']))
        
        # Same pricing as Stage 1
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        pricing_data = [
            ('FUTURES1', 'now', 102.5),
            ('FUTURES1', 'sodTod', 101.0),
            ('FUTURES1', 'sodTom', 101.5),
            ('FUTURES1', 'close', 102.0),
            ('FUTURES2', 'now', 49.0),
            ('FUTURES2', 'sodTod', 49.5),
            ('FUTURES2', 'sodTom', 49.25),
            ('FUTURES2', 'close', 49.1),
        ]
        
        for symbol, price_type, price in pricing_data:
            conn.execute("""
                INSERT INTO pricing (symbol, price_type, price, timestamp)
                VALUES (?, ?, ?, ?)
            """, (symbol, price_type, price, timestamp))
        
        conn.commit()
        conn.close()
    
    def test_stage2_initialization(self):
        """Test PositionsAggregator initialization"""
        print("\n" + "="*60)
        print("STAGE 2 TEST: MODULE IMPORT AND INITIALIZATION")
        print("="*60)
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        aggregator = None
        
        try:
            # Setup database
            print("\n2. Setting up test database...")
            self.setup_test_database(db_path)
            print("   ✓ Database created")
            
            # Mock Redis to prevent connection attempts
            print("\n3. Mocking Redis...")
            with patch('redis.Redis') as mock_redis_class:
                # Setup mock Redis behavior
                mock_redis = Mock()
                mock_pubsub = Mock()
                mock_pubsub.listen.return_value = []  # Empty iterator
                mock_redis.pubsub.return_value = mock_pubsub
                mock_redis_class.return_value = mock_redis
                
                print("   ✓ Redis mocked")
                
                # Initialize PositionsAggregator
                print("\n4. Creating PositionsAggregator instance...")
                aggregator = PositionsAggregator(
                    trades_db_path=db_path
                )
                print("   ✓ PositionsAggregator created")
                
                # Verify attributes
                print("\n5. Verifying aggregator attributes...")
                
                # Check database paths
                assert aggregator.trades_db_path == db_path, "trades_db_path not set correctly"
                print(f"   ✓ trades_db_path: {aggregator.trades_db_path}")
                
                # Check Redis client
                assert aggregator.redis_client is not None, "redis_client is None"
                print("   ✓ redis_client initialized")
                
                # Check positions cache
                assert hasattr(aggregator, 'positions_cache'), "positions_cache not created"
                print("   ✓ positions_cache exists")
                
                # Check if cache is a DataFrame
                assert isinstance(aggregator.positions_cache, pd.DataFrame), "positions_cache is not a DataFrame"
                print(f"   ✓ positions_cache is DataFrame (empty: {aggregator.positions_cache.empty})")
                
                # Check queue
                assert hasattr(aggregator, 'db_write_queue'), "db_write_queue not created"
                print("   ✓ db_write_queue exists")
                
                # Check symbol translator
                assert hasattr(aggregator, 'symbol_translator'), "symbol_translator not created"
                print("   ✓ symbol_translator exists")
                
                # Check that run_aggregation_service method exists
                assert hasattr(aggregator, 'run_aggregation_service'), "run_aggregation_service method not found"
                print("   ✓ run_aggregation_service method exists")
                
                # Test loading positions manually
                print("\n6. Testing _load_positions_from_db()...")
                aggregator._load_positions_from_db()
                
                # Check cache state after load
                print("\n7. Checking cache state after load...")
                print(f"   Cache shape: {aggregator.positions_cache.shape}")
                
                if not aggregator.positions_cache.empty:
                    print(f"   ✓ Cache loaded with {len(aggregator.positions_cache)} positions")
                    print(f"   Cache columns: {list(aggregator.positions_cache.columns)[:5]}...")  # Show first 5 columns
                    
                    # Show cache contents
                    print("\n   Cache contents:")
                    for _, row in aggregator.positions_cache.iterrows():
                        print(f"   - {row['symbol']}: open={row.get('open_position', 0)}, "
                              f"closed={row.get('closed_position', 0)}")
                else:
                    print("   ⚠ Cache is empty after load")
                
                # Test that we can write to database
                print("\n8. Testing database write (bypassing queue)...")
                if not aggregator.positions_cache.empty:
                    # Directly call write method to test
                    aggregator._write_positions_to_db(aggregator.positions_cache)
                    print("   ✓ Database write completed")
                else:
                    print("   ⚠ Skipping write test - no data in cache")
                
                print("\n✓ STAGE 2 PASSED - PositionsAggregator initialized successfully!")
                print("\nReady for Stage 3: P&L calculation test")
                
        except Exception as e:
            print(f"\n✗ STAGE 2 ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
            
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
                print(f"\nCleaned up test database")


if __name__ == "__main__":
    test = TestStage2Initialization()
    test.test_stage2_initialization()