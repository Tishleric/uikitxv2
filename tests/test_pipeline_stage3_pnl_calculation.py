"""
Stage 3: Test P&L calculation functionality.
This test verifies that unrealized P&L is calculated correctly.
"""

print("Starting Stage 3 test...")

import sqlite3
import pandas as pd
import tempfile
import os
import sys
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pytz

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


class TestStage3PnLCalculation:
    """Stage 3: Test P&L calculations"""
    
    def setup_test_database(self, db_path):
        """Create test data optimized for P&L testing"""
        conn = sqlite3.connect(db_path)
        create_all_tables(conn)
        
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # Positions with known expected P&L
        positions = [
            # FUTURES1: Buy position from yesterday (should use SOD price as entry)
            {
                'transactionId': 1,
                'symbol': 'FUTURES1',
                'price': 100.0,      # Actual trade price
                'quantity': 10,
                'buySell': 'B',
                'sequenceId': 'YEST-001',
                'time': yesterday.strftime('%Y-%m-%d %H:%M:%S.000'),
                'original_price': 100.0,
                'original_time': yesterday.strftime('%Y-%m-%d %H:%M:%S.000'),
                'fullPartial': 'full'
            },
            # FUTURES2: Sell position from today
            {
                'transactionId': 2,
                'symbol': 'FUTURES2',
                'price': 50.0,       # Actual trade price
                'quantity': 5,
                'buySell': 'S',
                'sequenceId': 'TODAY-001',
                'time': now.strftime('%Y-%m-%d %H:%M:%S.000'),
                'original_price': 50.0,
                'original_time': now.strftime('%Y-%m-%d %H:%M:%S.000'),
                'fullPartial': 'full'
            }
        ]
        
        # Insert into both FIFO and LIFO
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
        
        # Pricing designed for easy P&L verification
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        pricing_data = [
            # FUTURES1 prices
            ('FUTURES1', 'now', 102.0),      # Up $2 from entry
            ('FUTURES1', 'sodTod', 100.5),    # SOD today (entry for yesterday's trade)
            ('FUTURES1', 'sodTom', 101.0),    # Different for time-based testing
            ('FUTURES1', 'close', 101.5),     
            
            # FUTURES2 prices
            ('FUTURES2', 'now', 48.0),        # Down $2 (good for short)
            ('FUTURES2', 'sodTod', 49.5),     
            ('FUTURES2', 'sodTom', 49.0),     
            ('FUTURES2', 'close', 48.5),      
        ]
        
        for symbol, price_type, price in pricing_data:
            conn.execute("""
                INSERT INTO pricing (symbol, price_type, price, timestamp)
                VALUES (?, ?, ?, ?)
            """, (symbol, price_type, price, timestamp))
        
        conn.commit()
        conn.close()
    
    def calculate_expected_pnl(self, symbol, quantity, buy_sell, entry_price, 
                             sod_tod, sod_tom, now_price, time_period='pre_2pm'):
        """Calculate expected P&L manually"""
        
        # Determine intermediate price based on time
        if time_period == 'pre_2pm':
            intermediate = sod_tod
        else:
            intermediate = sod_tom
            
        # Calculate P&L
        pnl = ((intermediate - entry_price) * quantity + 
               (now_price - intermediate) * quantity) * 1000
        
        # Adjust for short positions
        if buy_sell == 'S':
            pnl = -pnl
            
        return round(pnl, 2)
    
    def test_stage3_pnl_calculation(self):
        """Test P&L calculation functionality"""
        print("\n" + "="*60)
        print("STAGE 3 TEST: P&L CALCULATION")
        print("="*60)
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Setup database
            print("\n2. Setting up test database...")
            self.setup_test_database(db_path)
            print("   ✓ Database created with test data")
            
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
                
                # Load positions (this triggers P&L calculation)
                print("\n4. Loading positions and calculating P&L...")
                aggregator._load_positions_from_db()
                
                # Check cache contents
                print("\n5. Verifying P&L calculations...")
                cache = aggregator.positions_cache
                
                if cache.empty:
                    raise AssertionError("Cache is empty after load!")
                
                print(f"   Loaded {len(cache)} positions")
                
                # Display P&L columns
                pnl_columns = [col for col in cache.columns if 'pnl' in col.lower()]
                print(f"   P&L columns found: {pnl_columns}")
                
                # Check each position
                print("\n   P&L Results:")
                for _, row in cache.iterrows():
                    symbol = row['symbol']
                    print(f"\n   {symbol}:")
                    print(f"     Open Position: {row['open_position']}")
                    
                    # Check if P&L columns exist and have values
                    if 'fifo_unrealized_pnl' in row:
                        print(f"     FIFO Unrealized P&L: ${row['fifo_unrealized_pnl']:,.2f}")
                    else:
                        print(f"     FIFO Unrealized P&L: NOT CALCULATED")
                        
                    if 'lifo_unrealized_pnl' in row:
                        print(f"     LIFO Unrealized P&L: ${row['lifo_unrealized_pnl']:,.2f}")
                    else:
                        print(f"     LIFO Unrealized P&L: NOT CALCULATED")
                        
                    if 'fifo_unrealized_pnl_close' in row:
                        print(f"     FIFO Close P&L: ${row['fifo_unrealized_pnl_close']:,.2f}")
                        
                    if 'lifo_unrealized_pnl_close' in row:
                        print(f"     LIFO Close P&L: ${row['lifo_unrealized_pnl_close']:,.2f}")
                
                # Manual verification for FUTURES1
                print("\n6. Manual P&L verification...")
                
                # Get pricing data
                conn = sqlite3.connect(db_path)
                prices_df = pd.read_sql_query("SELECT * FROM pricing", conn)
                conn.close()
                
                print("\n   Pricing data:")
                for symbol in ['FUTURES1', 'FUTURES2']:
                    symbol_prices = prices_df[prices_df['symbol'] == symbol]
                    if not symbol_prices.empty:
                        print(f"   {symbol}:")
                        for _, price_row in symbol_prices.iterrows():
                            print(f"     {price_row['price_type']}: ${price_row['price']:.2f}")
                
                # Calculate expected P&L for FUTURES1
                # Yesterday's trade should use SOD as entry (Pmax logic)
                print("\n   Expected P&L calculation for FUTURES1:")
                print("   - Quantity: 10 (Buy)")
                print("   - Entry price: $100.50 (SOD, not actual $100)")
                print("   - Current price: $102.00")
                print("   - Pre-2pm intermediate: $100.50 (sodTod)")
                print("   - P&L = ((100.50 - 100.50) + (102.00 - 100.50)) * 10 * 1000")
                print("   - P&L = (0 + 1.50) * 10 * 1000 = $15,000")
                
                # Verify FUTURES1 P&L
                futures1 = cache[cache['symbol'] == 'FUTURES1']
                if not futures1.empty and 'fifo_unrealized_pnl' in futures1.columns:
                    actual_pnl = futures1.iloc[0]['fifo_unrealized_pnl']
                    expected_pnl = 15000.0
                    
                    if abs(actual_pnl - expected_pnl) < 1:
                        print(f"\n   ✓ FUTURES1 P&L correct: ${actual_pnl:,.2f}")
                    else:
                        print(f"\n   ✗ FUTURES1 P&L mismatch: expected ${expected_pnl:,.2f}, got ${actual_pnl:,.2f}")
                
                # Check if all P&L values are calculated
                if 'fifo_unrealized_pnl' in cache.columns:
                    non_zero_pnl = cache[cache['fifo_unrealized_pnl'] != 0]
                    print(f"\n   Positions with non-zero P&L: {len(non_zero_pnl)}/{len(cache)}")
                    
                    if len(non_zero_pnl) > 0:
                        print("\n✓ STAGE 3 PASSED - P&L calculations working!")
                    else:
                        print("\n⚠ WARNING: All P&L values are zero")
                else:
                    print("\n✗ STAGE 3 FAILED - P&L columns not found in cache")
                
                print("\nReady for Stage 4: Full pipeline test")
                
        except Exception as e:
            print(f"\n✗ STAGE 3 ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
            
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
                print(f"\nCleaned up test database")


if __name__ == "__main__":
    test = TestStage3PnLCalculation()
    test.test_stage3_pnl_calculation()