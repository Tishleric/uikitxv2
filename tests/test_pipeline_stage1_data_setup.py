"""
Stage 1: Test data setup and verification for P&L pipeline.
This test ensures all required data is correctly set up before testing the pipeline.
"""

print("Starting Stage 1 test...")

import sqlite3
import pandas as pd
import tempfile
import os
import sys
from datetime import datetime, timedelta

print("Adding project path...")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Importing create_all_tables...")
try:
    from lib.trading.pnl_fifo_lifo.data_manager import create_all_tables
    print("✓ Successfully imported create_all_tables")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    raise


class TestStage1DataSetup:
    """Stage 1: Verify test data setup"""
    
    def create_test_database(self, db_path):
        """Create comprehensive test data"""
        conn = sqlite3.connect(db_path)
        
        # Create all tables
        create_all_tables(conn)
        
        # Get current time and yesterday
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # 1. Insert test positions in trades_fifo
        print("\n1. Creating trades_fifo positions...")
        fifo_positions = [
            # Position from yesterday (should use SOD price in Pmax logic)
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
            # Position from today (should use actual price)
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
            # Short position
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
        
        for pos in fifo_positions:
            conn.execute("""
                INSERT INTO trades_fifo 
                (transactionId, symbol, price, original_price, quantity, buySell, 
                 sequenceId, time, original_time, fullPartial)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pos['transactionId'], pos['symbol'], pos['price'], 
                  pos['original_price'], pos['quantity'], pos['buySell'],
                  pos['sequenceId'], pos['time'], pos['original_time'], 
                  pos['fullPartial']))
        
        # 2. Insert same positions in trades_lifo
        print("2. Creating trades_lifo positions...")
        for pos in fifo_positions:
            conn.execute("""
                INSERT INTO trades_lifo 
                (transactionId, symbol, price, original_price, quantity, buySell, 
                 sequenceId, time, original_time, fullPartial)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pos['transactionId'], pos['symbol'], pos['price'], 
                  pos['original_price'], pos['quantity'], pos['buySell'],
                  pos['sequenceId'], pos['time'], pos['original_time'], 
                  pos['fullPartial']))
        
        # 3. Insert comprehensive pricing data
        print("3. Creating pricing data...")
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        pricing_data = [
            # FUTURES1 - all prices slightly different
            ('FUTURES1', 'now', 102.5),      # Current price (up from entry)
            ('FUTURES1', 'sodTod', 101.0),    # Start of day today
            ('FUTURES1', 'sodTom', 101.5),    # Start of day tomorrow (different!)
            ('FUTURES1', 'close', 102.0),     # Today's close price
            
            # FUTURES2 - prices for short position
            ('FUTURES2', 'now', 49.0),        # Current price (down = good for short)
            ('FUTURES2', 'sodTod', 49.5),     
            ('FUTURES2', 'sodTom', 49.25),    # Different from sodTod
            ('FUTURES2', 'close', 49.1),      
        ]
        
        for symbol, price_type, price in pricing_data:
            conn.execute("""
                INSERT INTO pricing (symbol, price_type, price, timestamp)
                VALUES (?, ?, ?, ?)
            """, (symbol, price_type, price, timestamp))
        
        # 4. Insert some realized P&L for context
        print("4. Creating realized P&L data...")
        conn.execute("""
            INSERT INTO realized_fifo (symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting,
                                     partialFull, quantity, entryPrice, exitPrice, realizedPnL, timestamp)
            VALUES ('FUTURES1', 'OLD-001', 'YEST-001', 'partial', 5, 99.0, 100.0, 5000.0, ?)
        """, (timestamp,))
        
        conn.execute("""
            INSERT INTO realized_lifo (symbol, sequenceIdBeingOffset, sequenceIdDoingOffsetting,
                                     partialFull, quantity, entryPrice, exitPrice, realizedPnL, timestamp)
            VALUES ('FUTURES1', 'OLD-001', 'YEST-001', 'partial', 5, 99.0, 100.0, 5000.0, ?)
        """, (timestamp,))
        
        conn.commit()
        conn.close()
        
    def verify_test_data(self, db_path):
        """Verify all test data was created correctly"""
        conn = sqlite3.connect(db_path)
        
        print("\n=== STAGE 1: DATA VERIFICATION ===")
        
        # 1. Verify trades_fifo
        print("\n1. Checking trades_fifo positions:")
        fifo_query = "SELECT * FROM trades_fifo WHERE quantity > 0 ORDER BY symbol, sequenceId"
        fifo_df = pd.read_sql_query(fifo_query, conn)
        print(f"   Found {len(fifo_df)} positions in trades_fifo")
        
        if not fifo_df.empty:
            print("\n   trades_fifo contents:")
            for _, row in fifo_df.iterrows():
                print(f"   - {row['sequenceId']}: {row['buySell']} {row['quantity']} "
                      f"{row['symbol']} @ ${row['price']:.2f} on {row['time']}")
        
        # 2. Verify trades_lifo
        print("\n2. Checking trades_lifo positions:")
        lifo_query = "SELECT COUNT(*) as count FROM trades_lifo WHERE quantity > 0"
        lifo_count = pd.read_sql_query(lifo_query, conn)['count'].iloc[0]
        print(f"   Found {lifo_count} positions in trades_lifo")
        
        # 3. Verify pricing data
        print("\n3. Checking pricing data:")
        pricing_query = """
            SELECT symbol, 
                   MAX(CASE WHEN price_type = 'now' THEN price END) as now_price,
                   MAX(CASE WHEN price_type = 'sodTod' THEN price END) as sodTod,
                   MAX(CASE WHEN price_type = 'sodTom' THEN price END) as sodTom,
                   MAX(CASE WHEN price_type = 'close' THEN price END) as close_price
            FROM pricing
            GROUP BY symbol
            ORDER BY symbol
        """
        pricing_df = pd.read_sql_query(pricing_query, conn)
        
        print(f"   Found pricing for {len(pricing_df)} symbols")
        if not pricing_df.empty:
            print("\n   Pricing data:")
            for _, row in pricing_df.iterrows():
                print(f"   {row['symbol']}:")
                print(f"     - now:    ${row['now_price']:.2f}")
                print(f"     - sodTod: ${row['sodTod']:.2f}")
                print(f"     - sodTom: ${row['sodTom']:.2f}")
                print(f"     - close:  ${row['close_price']:.2f}")
                
                # Verify sodTod != sodTom (important for time-based logic)
                if row['sodTod'] == row['sodTom']:
                    print(f"     ⚠ WARNING: sodTod == sodTom for {row['symbol']}")
                else:
                    print(f"     ✓ sodTod != sodTom (good for testing)")
        
        # 4. Verify realized P&L
        print("\n4. Checking realized P&L:")
        realized_query = "SELECT COUNT(*) as fifo_count FROM realized_fifo"
        realized_count = pd.read_sql_query(realized_query, conn)['fifo_count'].iloc[0]
        print(f"   Found {realized_count} realized FIFO trades")
        
        # 5. Summary verification
        print("\n=== VERIFICATION SUMMARY ===")
        
        all_good = True
        
        # Check FIFO positions exist
        if len(fifo_df) == 0:
            print("✗ No positions in trades_fifo")
            all_good = False
        else:
            print(f"✓ {len(fifo_df)} positions in trades_fifo")
        
        # Check LIFO positions exist  
        if lifo_count == 0:
            print("✗ No positions in trades_lifo")
            all_good = False
        else:
            print(f"✓ {lifo_count} positions in trades_lifo")
        
        # Check pricing exists for all symbols
        symbols_with_positions = set(fifo_df['symbol'].unique())
        symbols_with_prices = set(pricing_df['symbol'].unique())
        
        if symbols_with_positions != symbols_with_prices:
            print(f"✗ Price/position mismatch: positions={symbols_with_positions}, prices={symbols_with_prices}")
            all_good = False
        else:
            print(f"✓ Pricing data exists for all {len(symbols_with_prices)} symbols")
        
        # Check all price types exist
        for _, row in pricing_df.iterrows():
            if pd.isna(row['now_price']) or pd.isna(row['sodTod']) or pd.isna(row['sodTom']):
                print(f"✗ Missing price types for {row['symbol']}")
                all_good = False
        
        if all_good:
            print("\n✓ All price types present for all symbols")
        
        # Check for sodTod != sodTom
        different_sod = all(row['sodTod'] != row['sodTom'] for _, row in pricing_df.iterrows())
        if different_sod:
            print("✓ sodTod differs from sodTom (good for time-based testing)")
        else:
            print("⚠ Some symbols have sodTod == sodTom")
        
        conn.close()
        
        return all_good
    
    def test_stage1_data_setup(self):
        """Run Stage 1 test"""
        print("\n" + "="*60)
        print("STAGE 1 TEST: DATA SETUP AND VERIFICATION")
        print("="*60)
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create test data
            self.create_test_database(db_path)
            
            # Verify test data
            success = self.verify_test_data(db_path)
            
            if success:
                print("\n✓ STAGE 1 PASSED - Test data is correctly set up!")
                print(f"\nDatabase location: {db_path}")
                print("Ready for Stage 2: Module import and initialization")
            else:
                print("\n✗ STAGE 1 FAILED - Test data setup has issues")
                raise AssertionError("Test data verification failed")
                
        except Exception as e:
            print(f"\n✗ STAGE 1 ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
            
        finally:
            # For testing, keep the database for inspection
            print(f"\nTest database kept at: {db_path}")
            # Normally we would: os.unlink(db_path)


if __name__ == "__main__":
    test = TestStage1DataSetup()
    test.test_stage1_data_setup()