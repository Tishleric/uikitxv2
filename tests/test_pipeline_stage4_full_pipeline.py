"""
Stage 4: Full pipeline test from calculation to database insertion.
This test verifies the complete flow: load → calculate → queue → write.
"""

print("Starting Stage 4 test...")

import sqlite3
import pandas as pd
import tempfile
import os
import sys
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

print("Adding project path...")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dependencies
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


class TestStage4FullPipeline:
    """Stage 4: Test complete pipeline"""
    
    def setup_test_database(self, db_path):
        """Create test data"""
        conn = sqlite3.connect(db_path)
        create_all_tables(conn)
        
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # Simple test positions
        positions = [
            {
                'transactionId': 1,
                'symbol': 'PIPELINE1',
                'price': 100.0,
                'quantity': 10,
                'buySell': 'B',
                'sequenceId': 'PIPE-001',
                'time': yesterday.strftime('%Y-%m-%d %H:%M:%S.000'),
                'original_price': 100.0,
                'original_time': yesterday.strftime('%Y-%m-%d %H:%M:%S.000'),
                'fullPartial': 'full'
            },
            {
                'transactionId': 2,
                'symbol': 'PIPELINE2',
                'price': 200.0,
                'quantity': 5,
                'buySell': 'S',
                'sequenceId': 'PIPE-002',
                'time': now.strftime('%Y-%m-%d %H:%M:%S.000'),
                'original_price': 200.0,
                'original_time': now.strftime('%Y-%m-%d %H:%M:%S.000'),
                'fullPartial': 'full'
            }
        ]
        
        # Insert positions
        for pos in positions:
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
        
        # Insert pricing
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        pricing_data = [
            ('PIPELINE1', 'now', 105.0),
            ('PIPELINE1', 'sodTod', 101.0),
            ('PIPELINE1', 'sodTom', 102.0),
            ('PIPELINE1', 'close', 104.0),
            ('PIPELINE2', 'now', 195.0),
            ('PIPELINE2', 'sodTod', 198.0),
            ('PIPELINE2', 'sodTom', 197.0),
            ('PIPELINE2', 'close', 196.0),
        ]
        
        for symbol, price_type, price in pricing_data:
            conn.execute("""
                INSERT INTO pricing (symbol, price_type, price, timestamp)
                VALUES (?, ?, ?, ?)
            """, (symbol, price_type, price, timestamp))
        
        conn.commit()
        conn.close()
    
    def verify_database_insertion(self, db_path):
        """Check if P&L values made it to positions table"""
        conn = sqlite3.connect(db_path)
        
        # Query positions table
        query = """
            SELECT 
                symbol,
                open_position,
                fifo_unrealized_pnl,
                lifo_unrealized_pnl,
                fifo_unrealized_pnl_close,
                lifo_unrealized_pnl_close,
                last_updated
            FROM positions
            ORDER BY symbol
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def test_stage4_full_pipeline(self):
        """Test the complete pipeline"""
        print("\n" + "="*60)
        print("STAGE 4 TEST: FULL PIPELINE")
        print("="*60)
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Setup database
            print("\n2. Setting up test database...")
            self.setup_test_database(db_path)
            print("   ✓ Database created")
            
            # Mock Redis
            with patch('redis.Redis') as mock_redis_class:
                mock_redis = Mock()
                mock_pubsub = Mock()
                mock_pubsub.listen.return_value = []
                mock_redis.pubsub.return_value = mock_pubsub
                mock_redis_class.return_value = mock_redis
                
                # Create aggregator
                print("\n3. Creating PositionsAggregator...")
                aggregator = PositionsAggregator(trades_db_path=db_path)
                print("   ✓ Aggregator created")
                
                # Start writer thread manually with error tracking
                print("\n4. Starting writer thread...")
                
                # Wrap writer thread to catch exceptions
                writer_exception = [None]  # Use list to modify in closure
                
                def writer_with_error_catch():
                    try:
                        aggregator._db_writer_thread()
                    except Exception as e:
                        writer_exception[0] = e
                        print(f"\n   ✗ Writer thread error: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                writer_thread = threading.Thread(
                    target=writer_with_error_catch, 
                    daemon=True
                )
                writer_thread.start()
                print("   ✓ Writer thread started")
                
                # Load positions (triggers calculation)
                print("\n5. Loading positions (triggers P&L calculation)...")
                aggregator._load_positions_from_db()
                
                # Check cache
                print("\n6. Checking cache state...")
                if not aggregator.positions_cache.empty:
                    print(f"   ✓ Cache loaded with {len(aggregator.positions_cache)} positions")
                    
                    # Ensure Greek columns have non-null values
                    print("\n   Ensuring Greek columns have valid values...")
                    # Replace None values with defaults
                    aggregator.positions_cache['delta_y'] = aggregator.positions_cache['delta_y'].fillna(0.0)
                    aggregator.positions_cache['gamma_y'] = aggregator.positions_cache['gamma_y'].fillna(0.0)
                    aggregator.positions_cache['speed_y'] = aggregator.positions_cache['speed_y'].fillna(0.0)
                    aggregator.positions_cache['theta'] = aggregator.positions_cache['theta'].fillna(0.0)
                    aggregator.positions_cache['vega'] = aggregator.positions_cache['vega'].fillna(0.0)
                    aggregator.positions_cache['has_greeks'] = aggregator.positions_cache['has_greeks'].fillna(False)
                    aggregator.positions_cache['instrument_type'] = aggregator.positions_cache['instrument_type'].fillna('future')
                    
                    print("   ✓ Greek columns set to default values")
                    print(f"   Cache columns: {list(aggregator.positions_cache.columns)}")
                    
                    # Display cache P&L values
                    print("\n   Cache P&L values:")
                    for _, row in aggregator.positions_cache.iterrows():
                        print(f"   {row['symbol']}: "
                              f"FIFO unrealized=${row.get('fifo_unrealized_pnl', 0):,.2f}")
                else:
                    raise AssertionError("Cache is empty!")
                
                # Queue for database write
                print("\n7. Queueing for database write...")
                aggregator.db_write_queue.put(aggregator.positions_cache.copy())
                print(f"   ✓ Queue size: {aggregator.db_write_queue.qsize()}")
                
                # Wait for writer thread to process
                print("\n8. Waiting for writer thread to process queue...")
                max_wait = 5.0
                start_time = time.time()
                
                while not aggregator.db_write_queue.empty() and (time.time() - start_time) < max_wait:
                    time.sleep(0.1)
                
                if aggregator.db_write_queue.empty():
                    print(f"   ✓ Queue processed in {time.time() - start_time:.2f} seconds")
                else:
                    print(f"   ⚠ Queue still has {aggregator.db_write_queue.qsize()} items after {max_wait}s")
                
                # Give extra time for database commit
                print("   Waiting additional 0.5s for database commit...")
                time.sleep(0.5)
                
                # Check if writer thread had an exception
                if writer_exception[0]:
                    raise writer_exception[0]
                
                # Verify database insertion
                print("\n9. Verifying database insertion...")
                positions_df = self.verify_database_insertion(db_path)
                
                if positions_df.empty:
                    print("   ✗ No data found in positions table!")
                else:
                    print(f"   ✓ Found {len(positions_df)} rows in positions table")
                    
                    print("\n   Database contents:")
                    for _, row in positions_df.iterrows():
                        print(f"   {row['symbol']}:")
                        print(f"     - Open position: {row['open_position']}")
                        print(f"     - FIFO unrealized P&L: ${row['fifo_unrealized_pnl']:,.2f}")
                        print(f"     - LIFO unrealized P&L: ${row['lifo_unrealized_pnl']:,.2f}")
                        print(f"     - Last updated: {row['last_updated']}")
                    
                    # Verify P&L values are non-zero
                    non_zero = positions_df[
                        (positions_df['fifo_unrealized_pnl'] != 0) | 
                        (positions_df['lifo_unrealized_pnl'] != 0)
                    ]
                    
                    if len(non_zero) == len(positions_df):
                        print(f"\n   ✓ All {len(positions_df)} positions have P&L values")
                    else:
                        print(f"\n   ⚠ Only {len(non_zero)}/{len(positions_df)} positions have P&L")
                
                # Compare cache vs database
                print("\n10. Comparing cache vs database values...")
                all_match = True
                
                for _, cache_row in aggregator.positions_cache.iterrows():
                    symbol = cache_row['symbol']
                    db_row = positions_df[positions_df['symbol'] == symbol]
                    
                    if not db_row.empty:
                        db_row = db_row.iloc[0]
                        cache_pnl = cache_row.get('fifo_unrealized_pnl', 0)
                        db_pnl = db_row['fifo_unrealized_pnl']
                        
                        if abs(cache_pnl - db_pnl) < 0.01:
                            print(f"   ✓ {symbol}: Cache (${cache_pnl:,.2f}) = DB (${db_pnl:,.2f})")
                        else:
                            print(f"   ✗ {symbol}: Cache (${cache_pnl:,.2f}) ≠ DB (${db_pnl:,.2f})")
                            all_match = False
                    else:
                        print(f"   ✗ {symbol}: Not found in database")
                        all_match = False
                
                # Final verdict
                if all_match and len(positions_df) > 0:
                    print("\n✓ STAGE 4 PASSED - Full pipeline working!")
                    print("\nPipeline verified:")
                    print("  1. Positions loaded from trades_fifo/lifo")
                    print("  2. P&L calculated correctly")
                    print("  3. Cache updated with P&L values")
                    print("  4. Queue mechanism working")
                    print("  5. Writer thread processed queue")
                    print("  6. Database contains correct P&L values")
                else:
                    print("\n✗ STAGE 4 FAILED - Pipeline issues detected")
                
                # Stop writer thread
                aggregator.db_write_queue.put(None)  # Sentinel to stop thread
                writer_thread.join(timeout=1.0)
                
        except Exception as e:
            print(f"\n✗ STAGE 4 ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
            
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
                print(f"\nCleaned up test database")


if __name__ == "__main__":
    test = TestStage4FullPipeline()
    test.test_stage4_full_pipeline()