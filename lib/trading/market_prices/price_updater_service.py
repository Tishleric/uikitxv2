"""
Price Updater Service
---------------------
A lightweight, standalone service that subscribes to the spot risk results
channel on Redis and updates the `pricing` table in `trades.db`.
"""

import logging
import pandas as pd
import json
import redis
import time
from pathlib import Path
import sys
from datetime import datetime
import pyarrow as pa  # Import pyarrow for Arrow deserialization
import pickle  # Import pickle for envelope deserialization

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.monitoring.decorators import monitor
from lib.trading.market_prices.rosetta_stone import RosettaStone
import sqlite3 # Import sqlite3 for the connection

logger = logging.getLogger(__name__)

class PriceUpdaterService:
    """
    Subscribes to Redis for new spot risk data and updates the pricing table.
    """

    def __init__(self, trades_db_path: str = "trades.db"):
        """Initializes the service with a connection to Redis."""
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379)  # Changed to handle raw bytes for Arrow
        self.redis_channel = "spot_risk:results_channel"
        self.trades_db_path = trades_db_path
        self.symbol_translator = RosettaStone()
        logger.info("Initialized PriceUpdaterService.")

    @monitor()
    def run(self):
        """
        Runs as a persistent service, listening to the Redis channel.
        """
        logger.info(f"Starting Price Updater service, subscribing to Redis channel '{self.redis_channel}'...")
        
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.redis_channel)
        
        for message in pubsub.listen():
            if message['type'] != 'message':
                continue
            
            try:
                # --- Start Instrumentation ---
                start_time = time.time()
                
                # Deserialize the pickled envelope containing Arrow data
                payload = pickle.loads(message['data'])
                publish_timestamp = payload.get('publish_timestamp', start_time)
                latency = start_time - publish_timestamp
                # --- End Instrumentation ---

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
                
                prices_to_update = self._extract_prices(df)
                
                if prices_to_update:
                    logger.info(f"Extracted {len(prices_to_update)} prices to update in 'pricing' table.")
                    with sqlite3.connect(self.trades_db_path) as conn:
                        # Disable auto-commit for batch operation
                        conn.isolation_level = None
                        conn.execute("BEGIN")
                        
                        for symbol, price_data in prices_to_update.items():
                            # Update price without committing
                            conn.execute(
                                "INSERT OR REPLACE INTO pricing (symbol, price_type, price, timestamp) VALUES (?, 'now', ?, ?)",
                                (symbol, price_data['price'], timestamp)
                            )
                        
                        # Single commit for all updates
                        conn.commit()
                        
                        # Publish Redis notification after successful commit
                        self.redis_client.publish("positions:changed", "price_update")
                        
                    logger.info(f"Successfully updated {len(prices_to_update)} prices.")
                else:
                    logger.info("No relevant prices found in the data package for updating.")

            except redis.exceptions.ConnectionError as e:
                logger.error(f"Redis connection error: {e}. Retrying in 30 seconds...")
                time.sleep(30)
                pubsub.subscribe(self.redis_channel)
            except Exception as e:
                logger.error(f"An error occurred in the price updater service: {e}", exc_info=True)
                time.sleep(10)

    def _extract_prices(self, df: pd.DataFrame) -> dict:
        """
        Extracts prices from the DataFrame, preferring 'adjtheor' and
        falling back to the midpoint. Translates symbols to Bloomberg.
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
                # Track duplicates
                if bloomberg_symbol in prices:
                    symbol_count[bloomberg_symbol] = symbol_count.get(bloomberg_symbol, 1) + 1
                else:
                    symbol_count[bloomberg_symbol] = 1
                    
                prices[bloomberg_symbol] = {'price': price}
        
        # Log deduplication stats if any duplicates found
        duplicates = {sym: count for sym, count in symbol_count.items() if count > 1}
        if duplicates:
            total_removed = sum(count - 1 for count in duplicates.values())
            logger.info(f"Deduplicated symbols: {duplicates}")
            logger.info(f"Removed {total_removed} duplicate price updates")
        
        return prices 