"""
Price Updater Service - OPTIMIZED VERSION
----------------------------------------
Optimized with deduplication and batch commits for testing.
This is a TEST VERSION - not for production use yet.
"""

import logging
import pandas as pd
import json
import redis
import time
from pathlib import Path
import sys
from datetime import datetime
import pyarrow as pa
import pickle
import sqlite3

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.monitoring.decorators import monitor
from lib.trading.market_prices.rosetta_stone import RosettaStone

logger = logging.getLogger(__name__)

class PriceUpdaterServiceOptimized:
    """
    Optimized version with deduplication and batch commits.
    """

    def __init__(self, trades_db_path: str = "trades.db"):
        """Initializes the service with a connection to Redis."""
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379)
        self.redis_channel = "spot_risk:results_channel"
        self.trades_db_path = trades_db_path
        self.symbol_translator = RosettaStone()
        logger.info("Initialized PriceUpdaterService (OPTIMIZED).")

    @monitor()
    def run(self):
        """
        Runs as a persistent service, listening to the Redis channel.
        """
        logger.info(f"Starting OPTIMIZED Price Updater service...")
        
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.redis_channel)
        
        for message in pubsub.listen():
            if message['type'] != 'message':
                continue
            
            try:
                start_time = time.time()
                
                # Deserialize the pickled envelope containing Arrow data
                payload = pickle.loads(message['data'])
                publish_timestamp = payload.get('publish_timestamp', start_time)
                latency = start_time - publish_timestamp

                logger.info(f"Received new data package from Redis for price update (Latency: {latency:.3f}s).")
                
                # Deserialize Arrow data to DataFrame
                buffer = payload['data']
                reader = pa.ipc.open_stream(buffer)
                arrow_table = reader.read_all()
                df = arrow_table.to_pandas()
                
                timestamp = payload.get('timestamp', datetime.now().isoformat())

                if df.empty:
                    logger.warning("Received an empty DataFrame. Skipping price update.")
                    continue
                
                # OPTIMIZATION 1: Extract and deduplicate prices
                prices_to_update = self._extract_prices_deduplicated(df)
                
                if prices_to_update:
                    logger.info(f"Extracted {len(prices_to_update)} UNIQUE prices to update (from {len(df)} rows).")
                    
                    # OPTIMIZATION 2: Batch all updates in a single transaction
                    self._batch_update_prices(prices_to_update, timestamp)
                    
                    logger.info(f"Successfully updated {len(prices_to_update)} prices with SINGLE commit.")
                else:
                    logger.info("No relevant prices found in the data package for updating.")

            except redis.exceptions.ConnectionError as e:
                logger.error(f"Redis connection error: {e}. Retrying in 30 seconds...")
                time.sleep(30)
                pubsub.subscribe(self.redis_channel)
            except Exception as e:
                logger.error(f"An error occurred in the price updater service: {e}", exc_info=True)
                time.sleep(10)

    def _extract_prices_deduplicated(self, df: pd.DataFrame) -> dict:
        """
        Extracts prices from the DataFrame with DEDUPLICATION.
        For duplicate symbols, keeps the last occurrence (most recent).
        """
        df.columns = [col.lower() for col in df.columns]
        prices = {}
        
        # Track duplicates for logging
        symbol_count = {}

        for _, row in df.iterrows():
            actant_symbol = row.get('key')
            if not actant_symbol or pd.isna(actant_symbol):
                continue

            bloomberg_symbol = self.symbol_translator.translate(actant_symbol, 'actantrisk', 'bloomberg')
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
                # DEDUPLICATION: Simply overwrite any previous price for this symbol
                # This keeps the last occurrence, which should be the most recent
                if bloomberg_symbol in prices:
                    symbol_count[bloomberg_symbol] = symbol_count.get(bloomberg_symbol, 1) + 1
                else:
                    symbol_count[bloomberg_symbol] = 1
                    
                prices[bloomberg_symbol] = {'price': price}
        
        # Log deduplication stats
        duplicates = {sym: count for sym, count in symbol_count.items() if count > 1}
        if duplicates:
            logger.info(f"Deduplicated symbols: {duplicates}")
            total_removed = sum(count - 1 for count in duplicates.values())
            logger.info(f"Removed {total_removed} duplicate price updates")
        
        return prices

    def _batch_update_prices(self, prices_to_update: dict, timestamp: str):
        """
        Update all prices in a SINGLE database transaction with ONE commit.
        """
        with sqlite3.connect(self.trades_db_path) as conn:
            cursor = conn.cursor()
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Batch all updates
                for symbol, price_data in prices_to_update.items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp)
                        VALUES (?, 'now', ?, ?)
                    """, (symbol, price_data['price'], timestamp))
                
                # SINGLE COMMIT for all updates
                conn.commit()
                
                # Publish Redis signal for positions update
                try:
                    self.redis_client.publish("positions:changed", "price_update")
                    logger.debug(f"Published positions:changed signal after batch update")
                except Exception as redis_err:
                    logger.warning(f"Failed to publish Redis signal: {redis_err}")
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to update prices: {e}")
                raise

    def process_message_for_testing(self, message_data):
        """
        Process a single message for testing purposes.
        Returns timing information.
        """
        timing = {}
        
        t0 = time.perf_counter()
        
        # Deserialize
        payload = pickle.loads(message_data)
        t1 = time.perf_counter()
        timing['pickle_loads'] = t1 - t0
        
        # Arrow deserialize
        buffer = payload['data']
        reader = pa.ipc.open_stream(buffer)
        arrow_table = reader.read_all()
        df = arrow_table.to_pandas()
        t2 = time.perf_counter()
        timing['arrow_deserialize'] = t2 - t1
        
        # Extract and deduplicate
        prices_to_update = self._extract_prices_deduplicated(df)
        t3 = time.perf_counter()
        timing['extract_deduplicate'] = t3 - t2
        
        timing['rows_in'] = len(df)
        timing['unique_prices'] = len(prices_to_update)
        timing['dedup_ratio'] = 1 - (len(prices_to_update) / len(df)) if len(df) > 0 else 0
        
        # Batch update
        timestamp = payload.get('timestamp', datetime.now().isoformat())
        if prices_to_update:
            self._batch_update_prices(prices_to_update, timestamp)
        t4 = time.perf_counter()
        timing['batch_update'] = t4 - t3
        
        timing['total'] = t4 - t0
        
        return timing, prices_to_update

# For backwards compatibility in testing
PriceUpdaterService = PriceUpdaterServiceOptimized