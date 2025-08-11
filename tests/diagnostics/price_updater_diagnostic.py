"""
Price Updater Diagnostic Tool
============================
Simulates live environment to diagnose the 14-second latency issue.
"""

import time
import sqlite3
import redis
import pandas as pd
import numpy as np
import pickle
import pyarrow as pa
from datetime import datetime
from pathlib import Path
import logging
import threading
import json
from typing import Dict, List, Optional
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.trading.market_prices.rosetta_stone import RosettaStone

# Configure logging with microsecond precision
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class TimingContext:
    """Context manager for timing operations"""
    def __init__(self, name: str, logger=None):
        self.name = name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        self.logger.info(f"{self.name}: {self.duration:.3f}s")


class SpotRiskSimulator:
    """Simulates spot risk data generation"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379)
        self.channel = "spot_risk:results_channel"
        
    def generate_sample_data(self, num_symbols: int = 10) -> pd.DataFrame:
        """Generate sample spot risk data similar to production"""
        symbols = [f"TYZ{i%10} INDEX" for i in range(num_symbols)]
        
        data = {
            'key': symbols,
            'adjtheor': np.random.uniform(95.0, 105.0, num_symbols),
            'bid': np.random.uniform(94.5, 104.5, num_symbols),
            'ask': np.random.uniform(95.5, 105.5, num_symbols),
            'timestamp': [datetime.now().isoformat()] * num_symbols
        }
        
        return pd.DataFrame(data)
    
    def publish_batch(self, batch_id: str, num_symbols: int = 10):
        """Publish a batch of data to Redis, mimicking spot risk watcher"""
        df = self.generate_sample_data(num_symbols)
        
        with TimingContext("Arrow serialization"):
            # Convert to Arrow format
            arrow_table = pa.Table.from_pandas(df)
            sink = pa.BufferOutputStream()
            with pa.ipc.new_stream(sink, arrow_table.schema) as writer:
                writer.write_table(arrow_table)
            buffer = sink.getvalue()
        
        # Create payload
        payload = {
            'batch_id': batch_id,
            'publish_timestamp': time.time(),
            'format': 'arrow',
            'data': buffer,
            'timestamp': datetime.now().isoformat()
        }
        
        with TimingContext("Pickle + Redis publish"):
            pickled_payload = pickle.dumps(payload)
            self.redis_client.publish(self.channel, pickled_payload)
            
        logger.info(f"Published batch {batch_id} with {num_symbols} symbols")
        return df


class PriceUpdaterDiagnostic:
    """Diagnostic version of price updater with detailed timing"""
    
    def __init__(self, trades_db_path: str = "trades.db"):
        self.trades_db_path = trades_db_path
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379)
        self.channel = "spot_risk:results_channel"
        self.symbol_translator = RosettaStone()
        self.timing_results = []
        
    def process_one_message(self, message_data: bytes) -> Dict[str, float]:
        """Process a single message with detailed timing"""
        timing = {}
        overall_start = time.perf_counter()
        
        # 1. Pickle deserialization
        with TimingContext("Pickle loads") as t:
            payload = pickle.loads(message_data)
        timing['pickle_loads'] = t.duration
        
        # 2. Arrow deserialization
        with TimingContext("Arrow deserialize") as t:
            buffer = payload['data']
            reader = pa.ipc.open_stream(buffer)
            arrow_table = reader.read_all()
            df = arrow_table.to_pandas()
        timing['arrow_deserialize'] = t.duration
        
        # 3. Extract prices
        with TimingContext("Extract prices") as t:
            prices_to_update = self._extract_prices(df)
        timing['extract_prices'] = t.duration
        timing['num_symbols'] = len(prices_to_update)
        
        # 4. Database updates
        db_start = time.perf_counter()
        
        with TimingContext("DB connection") as t:
            conn = sqlite3.connect(self.trades_db_path)
        timing['db_connect'] = t.duration
        
        try:
            update_times = []
            for symbol, price_data in prices_to_update.items():
                with TimingContext(f"Update {symbol}", logger=None) as t:
                    self._update_price(conn, symbol, price_data['price'], 
                                     payload.get('timestamp', datetime.now().isoformat()))
                update_times.append(t.duration)
            
            timing['db_updates_total'] = sum(update_times)
            timing['db_updates_avg'] = np.mean(update_times) if update_times else 0
            timing['db_updates_max'] = max(update_times) if update_times else 0
            
            with TimingContext("DB commit") as t:
                conn.commit()
            timing['db_commit'] = t.duration
            
        finally:
            conn.close()
            
        timing['db_total'] = time.perf_counter() - db_start
        timing['overall'] = time.perf_counter() - overall_start
        
        # Log detailed breakdown
        logger.info(f"""
Message processing breakdown:
- Pickle deserialize: {timing['pickle_loads']:.3f}s
- Arrow deserialize: {timing['arrow_deserialize']:.3f}s  
- Extract prices ({timing['num_symbols']} symbols): {timing['extract_prices']:.3f}s
- DB operations:
  - Connection: {timing['db_connect']:.3f}s
  - Updates (avg): {timing['db_updates_avg']:.3f}s
  - Updates (max): {timing['db_updates_max']:.3f}s
  - Updates (total): {timing['db_updates_total']:.3f}s
  - Commit: {timing['db_commit']:.3f}s
  - DB Total: {timing['db_total']:.3f}s
- Overall: {timing['overall']:.3f}s
""")
        
        return timing
    
    def _extract_prices(self, df: pd.DataFrame) -> dict:
        """Extract prices with timing for symbol translation"""
        df.columns = [col.lower() for col in df.columns]
        prices = {}
        
        translation_times = []
        
        for _, row in df.iterrows():
            actant_symbol = row.get('key')
            if not actant_symbol or pd.isna(actant_symbol):
                continue
            
            trans_start = time.perf_counter()
            bloomberg_symbol = self.symbol_translator.translate(actant_symbol, 'actantrisk', 'bloomberg')
            translation_times.append(time.perf_counter() - trans_start)
            
            if not bloomberg_symbol:
                continue
            
            price = row.get('adjtheor')
            if not isinstance(price, (int, float)) or pd.isna(price):
                bid = row.get('bid')
                ask = row.get('ask')
                if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
                    price = (bid + ask) / 2
                else:
                    price = None
            
            if price is not None:
                prices[bloomberg_symbol] = {'price': price}
        
        if translation_times:
            logger.info(f"Symbol translation avg: {np.mean(translation_times)*1000:.1f}ms, "
                       f"max: {max(translation_times)*1000:.1f}ms")
        
        return prices
    
    def _update_price(self, conn, symbol: str, price: float, timestamp: str):
        """Update price in database"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
            VALUES (?, 'now', ?, ?)
        """, (symbol, price, timestamp))
    
    def run_diagnostic(self, num_messages: int = 5):
        """Run diagnostic on a number of messages"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.channel)
        
        messages_processed = 0
        
        logger.info(f"Starting diagnostic for {num_messages} messages...")
        
        for message in pubsub.listen():
            if message['type'] != 'message':
                continue
                
            timing = self.process_one_message(message['data'])
            self.timing_results.append(timing)
            
            messages_processed += 1
            if messages_processed >= num_messages:
                break
        
        self._print_summary()
    
    def _print_summary(self):
        """Print summary statistics"""
        if not self.timing_results:
            logger.info("No messages processed")
            return
            
        df = pd.DataFrame(self.timing_results)
        
        logger.info("\n" + "="*60)
        logger.info("TIMING SUMMARY")
        logger.info("="*60)
        
        for col in ['pickle_loads', 'arrow_deserialize', 'extract_prices', 
                    'db_connect', 'db_updates_avg', 'db_commit', 'db_total', 'overall']:
            if col in df.columns:
                logger.info(f"{col:20s}: avg={df[col].mean():.3f}s, "
                           f"max={df[col].max():.3f}s, min={df[col].min():.3f}s")


class DatabaseDiagnostic:
    """Diagnose database-specific issues"""
    
    def __init__(self, db_path: str = "trades.db"):
        self.db_path = db_path
    
    def check_configuration(self):
        """Check database configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        configs = {}
        for pragma in ['journal_mode', 'synchronous', 'temp_store', 'busy_timeout', 
                      'cache_size', 'page_size', 'wal_autocheckpoint']:
            cursor.execute(f"PRAGMA {pragma}")
            result = cursor.fetchone()
            configs[pragma] = result[0] if result else None
        
        logger.info("\nDatabase Configuration:")
        for key, value in configs.items():
            logger.info(f"  {key}: {value}")
        
        conn.close()
        return configs
    
    def test_concurrent_access(self, num_threads: int = 5):
        """Test concurrent database access"""
        logger.info(f"\nTesting concurrent access with {num_threads} threads...")
        
        def update_worker(thread_id: int, num_updates: int = 10):
            conn = sqlite3.connect(self.db_path)
            times = []
            
            for i in range(num_updates):
                symbol = f"TEST_SYMBOL_{thread_id}_{i}"
                start = time.perf_counter()
                
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
                        VALUES (?, 'now', ?, ?)
                    """, (symbol, 100.0 + i, datetime.now().isoformat()))
                    conn.commit()
                    
                    duration = time.perf_counter() - start
                    times.append(duration)
                    
                except sqlite3.OperationalError as e:
                    logger.warning(f"Thread {thread_id} got database lock: {e}")
                    
            conn.close()
            return times
        
        threads = []
        results = {}
        
        overall_start = time.perf_counter()
        
        for i in range(num_threads):
            t = threading.Thread(target=lambda: results.update({i: update_worker(i)}))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
            
        overall_duration = time.perf_counter() - overall_start
        
        # Analyze results
        all_times = []
        for thread_times in results.values():
            all_times.extend(thread_times)
        
        if all_times:
            logger.info(f"Concurrent update stats:")
            logger.info(f"  Total time: {overall_duration:.3f}s")
            logger.info(f"  Avg update: {np.mean(all_times):.3f}s")
            logger.info(f"  Max update: {max(all_times):.3f}s")
            logger.info(f"  Min update: {min(all_times):.3f}s")
            logger.info(f"  Updates/sec: {len(all_times)/overall_duration:.1f}")


def main():
    """Run full diagnostic suite"""
    logger.info("Starting Price Updater Diagnostic")
    logger.info("="*60)
    
    # 1. Check database configuration
    db_diag = DatabaseDiagnostic()
    db_diag.check_configuration()
    
    # 2. Test concurrent database access
    db_diag.test_concurrent_access()
    
    # 3. Set up simulator and diagnostic
    simulator = SpotRiskSimulator()
    diagnostic = PriceUpdaterDiagnostic()
    
    # 4. Publish test messages
    logger.info("\nPublishing test messages...")
    for i in range(5):
        simulator.publish_batch(f"test_batch_{i}", num_symbols=10)
        time.sleep(0.5)  # Small delay between batches
    
    # 5. Run diagnostic
    diagnostic.run_diagnostic(num_messages=5)
    
    logger.info("\nDiagnostic complete!")


if __name__ == "__main__":
    main()