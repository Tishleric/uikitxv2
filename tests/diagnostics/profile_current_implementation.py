"""
Profile Current Price Updater Implementation
===========================================
Profiles the exact current implementation to find the 14-second bottleneck.
NO MODIFICATIONS to production code - only observation.
"""

import cProfile
import pstats
import pickle
import time
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.trading.market_prices.price_updater_service import PriceUpdaterService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfiledPriceUpdaterService(PriceUpdaterService):
    """
    Wrapper around PriceUpdaterService that adds profiling.
    NO CHANGES to business logic - only adds timing.
    """
    
    def __init__(self, trades_db_path: str = "trades.db"):
        super().__init__(trades_db_path)
        self.timing_results = []
        
    def run(self):
        """Override run() to add profiling around message processing"""
        logger.info(f"Starting PROFILED Price Updater service...")
        
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.redis_channel)
        
        messages_processed = 0
        
        for message in pubsub.listen():
            if message['type'] != 'message':
                continue
            
            # Profile this single message
            profiler = cProfile.Profile()
            
            # Start profiling
            profiler.enable()
            overall_start = time.perf_counter()
            
            try:
                # Call the parent's actual processing logic
                # This is where we spend 14 seconds
                self._process_message_with_timing(message)
                
            finally:
                overall_end = time.perf_counter()
                profiler.disable()
                
                # Save profiling results
                messages_processed += 1
                self._save_profile(profiler, messages_processed)
                
                logger.info(f"Message {messages_processed} took {overall_end - overall_start:.3f}s")
                
                # Stop after 3 messages for safety
                if messages_processed >= 3:
                    logger.info("Profiling complete after 3 messages")
                    break
    
    def _process_message_with_timing(self, message):
        """Process message with detailed timing - wraps parent method"""
        import pyarrow as pa
        import sqlite3
        
        # Time each major operation
        t0 = time.perf_counter()
        
        # 1. Deserialize pickle
        payload = pickle.loads(message['data'])
        t1 = time.perf_counter()
        
        # 2. Deserialize Arrow
        buffer = payload['data']
        reader = pa.ipc.open_stream(buffer)
        arrow_table = reader.read_all()
        df = arrow_table.to_pandas()
        t2 = time.perf_counter()
        
        # 3. Extract prices
        prices_to_update = self._extract_prices(df)
        t3 = time.perf_counter()
        
        # 4. Database updates
        timestamp = payload.get('timestamp', datetime.now().isoformat())
        
        if prices_to_update:
            with sqlite3.connect(self.trades_db_path) as conn:
                t_db_start = time.perf_counter()
                
                for i, (symbol, price_data) in enumerate(prices_to_update.items()):
                    t_symbol_start = time.perf_counter()
                    
                    # Call parent's update method (from data_manager)
                    from lib.trading.pnl_fifo_lifo.data_manager import update_current_price
                    update_current_price(conn, symbol, price_data['price'], timestamp)
                    
                    t_symbol_end = time.perf_counter()
                    
                    if i < 3:  # Log first 3 symbols
                        logger.info(f"  Symbol {symbol}: {t_symbol_end - t_symbol_start:.3f}s")
                
                t_db_end = time.perf_counter()
        
        t4 = time.perf_counter()
        
        # Log timing breakdown
        timing = {
            'pickle_loads': t1 - t0,
            'arrow_deserialize': t2 - t1,
            'extract_prices': t3 - t2,
            'database_updates': t4 - t3,
            'total': t4 - t0,
            'num_symbols': len(prices_to_update)
        }
        
        logger.info(f"""
Timing Breakdown:
- Pickle loads: {timing['pickle_loads']:.3f}s
- Arrow deserialize: {timing['arrow_deserialize']:.3f}s
- Extract prices ({timing['num_symbols']} symbols): {timing['extract_prices']:.3f}s
- Database updates: {timing['database_updates']:.3f}s
- TOTAL: {timing['total']:.3f}s
""")
        
        self.timing_results.append(timing)
    
    def _save_profile(self, profiler, message_num):
        """Save profiling results"""
        # Create profile output directory
        profile_dir = Path("tests/diagnostics/profiles")
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Save stats
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_file = profile_dir / f"profile_msg{message_num}_{timestamp}.stats"
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        
        # Save to file
        with open(stats_file, 'w') as f:
            stats = pstats.Stats(profiler, stream=f)
            stats.sort_stats('cumulative')
            stats.print_stats(50)  # Top 50 functions
        
        # Also print top 20 to console
        logger.info(f"\n=== TOP 20 FUNCTIONS BY CUMULATIVE TIME (Message {message_num}) ===")
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(20)


def profile_from_captured_message():
    """Profile using a captured message (offline testing)"""
    # Find captured messages
    msg_dir = Path("tests/diagnostics/captured_messages")
    if not msg_dir.exists():
        logger.error(f"No captured messages found. Run capture_redis_messages.py first!")
        return
        
    # Get first message file
    msg_files = list(msg_dir.glob("message_*.pkl"))
    if not msg_files:
        logger.error("No message files found!")
        return
        
    msg_file = msg_files[0]
    logger.info(f"Using captured message: {msg_file}")
    
    # Load message
    with open(msg_file, 'rb') as f:
        message_data = pickle.load(f)
    
    # Create profiler
    updater = ProfiledPriceUpdaterService()
    
    # Profile the message processing
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Create fake message structure
    fake_message = {
        'type': 'message',
        'channel': 'spot_risk:results_channel',
        'data': message_data
    }
    
    updater._process_message_with_timing(fake_message)
    
    profiler.disable()
    
    # Show results
    logger.info("\n=== PROFILING RESULTS ===")
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(30)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', 
                       help='Profile live messages from Redis (requires running spot risk watcher)')
    parser.add_argument('--offline', action='store_true',
                       help='Profile from captured message file')
    
    args = parser.parse_args()
    
    if args.offline:
        profile_from_captured_message()
    else:
        # Default to live profiling
        logger.info("Starting live profiling...")
        logger.info("Make sure spot risk watcher is running!")
        updater = ProfiledPriceUpdaterService()
        updater.run()


if __name__ == "__main__":
    main()