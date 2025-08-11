"""
Test Price Updater Comparison
============================
Compare current vs optimized implementation side-by-side.
"""

import time
import pickle
import sqlite3
import shutil
from pathlib import Path
import sys
import logging
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import both implementations
from lib.trading.market_prices.price_updater_service import PriceUpdaterService
from tests.diagnostics.price_updater_service_optimized import PriceUpdaterServiceOptimized

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceUpdaterComparison:
    """Compare current and optimized implementations"""
    
    def __init__(self):
        self.test_db_current = "test_trades_current.db"
        self.test_db_optimized = "test_trades_optimized.db"
        self.captured_messages_dir = Path("tests/diagnostics/tests/diagnostics/captured_messages")
        
    def setup_test_databases(self):
        """Create test databases from production schema"""
        logger.info("Setting up test databases...")
        
        # Copy production database structure
        if Path("trades.db").exists():
            shutil.copy("trades.db", self.test_db_current)
            shutil.copy("trades.db", self.test_db_optimized)
        else:
            # Create minimal schema if no production DB
            self._create_minimal_schema(self.test_db_current)
            self._create_minimal_schema(self.test_db_optimized)
        
        # Clear pricing tables
        for db in [self.test_db_current, self.test_db_optimized]:
            conn = sqlite3.connect(db)
            conn.execute("DELETE FROM pricing WHERE price_type='now'")
            conn.commit()
            conn.close()
            
        logger.info("Test databases ready")
    
    def _create_minimal_schema(self, db_path):
        """Create minimal pricing table for testing"""
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pricing (
                symbol TEXT NOT NULL,
                price_type TEXT NOT NULL,
                price REAL,
                timestamp TEXT,
                PRIMARY KEY (symbol, price_type)
            )
        """)
        conn.commit()
        conn.close()
    
    def load_captured_messages(self):
        """Load captured messages from files"""
        messages = []
        
        # Try multiple locations
        possible_dirs = [
            self.captured_messages_dir,
            Path("tests/diagnostics/captured_messages"),
            Path("captured_messages")
        ]
        
        msg_dir = None
        for dir_path in possible_dirs:
            if dir_path.exists():
                msg_dir = dir_path
                break
        
        if not msg_dir:
            logger.error("No captured messages found!")
            return messages
        
        # Load all pickle files
        for pkl_file in sorted(msg_dir.glob("message_*.pkl")):
            with open(pkl_file, 'rb') as f:
                messages.append(pickle.load(f))
                
        logger.info(f"Loaded {len(messages)} captured messages")
        return messages
    
    def process_with_current(self, message_data):
        """Process message with current implementation"""
        # Create current implementation
        current = PriceUpdaterService(self.test_db_current)
        
        # Time the processing
        start_time = time.perf_counter()
        
        # Process message (we need to extract the logic since run() is a loop)
        payload = pickle.loads(message_data)
        buffer = payload['data']
        
        import pyarrow as pa
        reader = pa.ipc.open_stream(buffer)
        arrow_table = reader.read_all()
        df = arrow_table.to_pandas()
        
        timestamp = payload.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        prices_to_update = current._extract_prices(df)
        
        if prices_to_update:
            with sqlite3.connect(self.test_db_current) as conn:
                from lib.trading.pnl_fifo_lifo.data_manager import update_current_price
                for symbol, price_data in prices_to_update.items():
                    update_current_price(conn, symbol, price_data['price'], timestamp)
        
        end_time = time.perf_counter()
        
        return {
            'time': end_time - start_time,
            'num_updates': len(prices_to_update),
            'rows_processed': len(df)
        }
    
    def process_with_optimized(self, message_data):
        """Process message with optimized implementation"""
        # Create optimized implementation
        optimized = PriceUpdaterServiceOptimized(self.test_db_optimized)
        
        # Use the test method that returns timing
        timing, prices = optimized.process_message_for_testing(message_data)
        
        return {
            'time': timing['total'],
            'num_updates': timing['unique_prices'],
            'rows_processed': timing['rows_in'],
            'timing_breakdown': timing
        }
    
    def get_prices_from_db(self, db_path):
        """Extract all prices from database"""
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT symbol, price, timestamp FROM pricing WHERE price_type='now' ORDER BY symbol",
            conn
        )
        conn.close()
        return df
    
    def compare_results(self):
        """Compare prices in both databases"""
        current_prices = self.get_prices_from_db(self.test_db_current)
        optimized_prices = self.get_prices_from_db(self.test_db_optimized)
        
        # Check if same symbols
        current_symbols = set(current_prices['symbol'])
        optimized_symbols = set(optimized_prices['symbol'])
        
        if current_symbols != optimized_symbols:
            logger.error("Symbol mismatch!")
            logger.error(f"Current only: {current_symbols - optimized_symbols}")
            logger.error(f"Optimized only: {optimized_symbols - current_symbols}")
            return False
        
        # Check if same prices
        merged = pd.merge(current_prices, optimized_prices, on='symbol', suffixes=('_current', '_optimized'))
        price_diffs = merged[merged['price_current'] != merged['price_optimized']]
        
        if not price_diffs.empty:
            logger.error("Price mismatches found:")
            logger.error(price_diffs)
            return False
        
        logger.info(f"✓ All {len(current_prices)} prices match exactly!")
        return True
    
    def run_comparison(self):
        """Run full comparison test"""
        # Setup
        self.setup_test_databases()
        messages = self.load_captured_messages()
        
        if not messages:
            logger.error("No messages to test!")
            return
        
        # Results storage
        results = {
            'current': [],
            'optimized': []
        }
        
        # Process each message
        logger.info("\n" + "="*60)
        logger.info("PROCESSING MESSAGES")
        logger.info("="*60)
        
        for i, message in enumerate(messages):
            logger.info(f"\nMessage {i+1}/{len(messages)}:")
            
            # Process with current
            logger.info("  Processing with CURRENT implementation...")
            current_result = self.process_with_current(message)
            results['current'].append(current_result)
            logger.info(f"    Time: {current_result['time']:.3f}s")
            logger.info(f"    Updates: {current_result['num_updates']}")
            
            # Process with optimized
            logger.info("  Processing with OPTIMIZED implementation...")
            optimized_result = self.process_with_optimized(message)
            results['optimized'].append(optimized_result)
            logger.info(f"    Time: {optimized_result['time']:.3f}s")
            logger.info(f"    Updates: {optimized_result['num_updates']} (from {optimized_result['rows_processed']} rows)")
            
            # Show timing breakdown
            if 'timing_breakdown' in optimized_result:
                timing = optimized_result['timing_breakdown']
                logger.info(f"    Breakdown:")
                logger.info(f"      - Deserialize: {(timing['pickle_loads'] + timing['arrow_deserialize'])*1000:.1f}ms")
                logger.info(f"      - Extract/Dedup: {timing['extract_deduplicate']*1000:.1f}ms")
                logger.info(f"      - Batch Update: {timing['batch_update']*1000:.1f}ms")
                logger.info(f"      - Dedup savings: {timing['dedup_ratio']*100:.1f}%")
            
            # Show speedup
            speedup = current_result['time'] / optimized_result['time'] if optimized_result['time'] > 0 else 0
            logger.info(f"    SPEEDUP: {speedup:.1f}x faster")
        
        # Verify correctness
        logger.info("\n" + "="*60)
        logger.info("VERIFYING CORRECTNESS")
        logger.info("="*60)
        
        if self.compare_results():
            logger.info("✓ CORRECTNESS VERIFIED - All prices match!")
        else:
            logger.error("✗ CORRECTNESS FAILED - Price mismatch detected!")
            return
        
        # Summary statistics
        logger.info("\n" + "="*60)
        logger.info("SUMMARY STATISTICS")
        logger.info("="*60)
        
        current_times = [r['time'] for r in results['current']]
        optimized_times = [r['time'] for r in results['optimized']]
        
        logger.info(f"\nCurrent Implementation:")
        logger.info(f"  Total time: {sum(current_times):.3f}s")
        logger.info(f"  Avg per message: {sum(current_times)/len(current_times):.3f}s")
        logger.info(f"  Total updates: {sum(r['num_updates'] for r in results['current'])}")
        
        logger.info(f"\nOptimized Implementation:")
        logger.info(f"  Total time: {sum(optimized_times):.3f}s")
        logger.info(f"  Avg per message: {sum(optimized_times)/len(optimized_times):.3f}s")
        logger.info(f"  Total updates: {sum(r['num_updates'] for r in results['optimized'])}")
        
        avg_speedup = sum(current_times) / sum(optimized_times) if sum(optimized_times) > 0 else 0
        logger.info(f"\nOVERALL SPEEDUP: {avg_speedup:.1f}x faster")
        
        # Cleanup test databases
        logger.info("\nCleaning up test databases...")
        Path(self.test_db_current).unlink(missing_ok=True)
        Path(self.test_db_optimized).unlink(missing_ok=True)


def main():
    """Run the comparison test"""
    comparison = PriceUpdaterComparison()
    comparison.run_comparison()


if __name__ == "__main__":
    main()