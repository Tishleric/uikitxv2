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

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.monitoring.decorators import monitor
# Import the specific, correct DB function instead of the whole storage class
from lib.trading.pnl_fifo_lifo.data_manager import update_current_price
from lib.trading.market_prices.rosetta_stone import RosettaStone
import sqlite3 # Import sqlite3 for the connection

logger = logging.getLogger(__name__)

class PriceUpdaterService:
    """
    Subscribes to Redis for new spot risk data and updates the pricing table.
    """

    def __init__(self, trades_db_path: str = "trades.db"):
        """Initializes the service with a connection to Redis."""
        self.redis_client = redis.Redis(decode_responses=True)
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
                payload = json.loads(message['data'])
                publish_timestamp = payload.get('publish_timestamp', start_time)
                latency = start_time - publish_timestamp
                # --- End Instrumentation ---

                logger.info(f"Received new data package from Redis for price update (Latency: {latency:.3f}s).")
                df = pd.read_json(payload['data'], orient='records')
                timestamp = payload.get('timestamp', datetime.now().isoformat())

                if df.empty:
                    logger.warning("Received an empty DataFrame. Skipping price update.")
                    continue
                
                prices_to_update = self._extract_prices(df)
                
                if prices_to_update:
                    logger.info(f"Extracted {len(prices_to_update)} prices to update in 'pricing' table.")
                    with sqlite3.connect(self.trades_db_path) as conn:
                        for symbol, price_data in prices_to_update.items():
                            update_current_price(conn, symbol, price_data['price'], timestamp)
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
                prices[bloomberg_symbol] = {'price': price}
        
        return prices 