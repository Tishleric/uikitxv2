"""
Positions Aggregator Module

Purpose: Aggregate data from trades.db and spot_risk.db into unified POSITIONS table
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import pandas as pd
import pytz
import redis
import json
import time
import threading
import queue
import pyarrow as pa  # Import pyarrow for Arrow deserialization
import pickle  # Import pickle for envelope deserialization

from .config import DEFAULT_SYMBOL, PNL_MULTIPLIER, REALIZED_PMAX_ENABLED
from .pnl_engine import calculate_unrealized_pnl
from .data_manager import view_unrealized_positions, load_pricing_dictionaries, get_trading_day
from lib.trading.market_prices.rosetta_stone import RosettaStone
from lib.trading.actant.spot_risk.database import SpotRiskDatabaseService
from lib.monitoring.decorators import monitor

logger = logging.getLogger(__name__)


class PositionsAggregator:
    """Aggregates position, P&L, and Greek data into master positions table."""
    
    def __init__(self, trades_db_path: str = "trades.db"):
        """
        Initialize aggregator with database paths.
        
        Args:
            trades_db_path: Path to trades.db
            spot_risk_db_path: Path to spot_risk.db (optional)
        """
        self.trades_db_path = trades_db_path
        self.symbol_translator = RosettaStone()
        self.redis_client = redis.Redis(host='127.0.0.1', port=6379)  # Changed to handle raw bytes for Arrow
        self.redis_channel = "spot_risk:results_channel"
        self.greek_data_cache = {}
        
        # In-memory cache for positions data
        self.positions_cache = pd.DataFrame()
        self.db_lock = threading.Lock()
        
        # Queue for decoupling database writes
        self.db_write_queue = queue.Queue()
        
        logger.info("Initialized PositionsAggregator with in-memory caching and writer queue")
    
    def _load_positions_from_db(self):
        """
        Load all positions data from database into memory.
        This includes data from trades_fifo, trades_lifo, daily_positions tables.
        """
        with self.db_lock:
            logger.info("Loading positions data from database into memory...")
            start_time = time.time()
            
            conn = sqlite3.connect(self.trades_db_path)
            
            try:
                # Get current trading day using Chicago-local time to avoid host timezone drift
                chicago_tz = pytz.timezone('America/Chicago')
                now_chicago = datetime.now(chicago_tz)
                current_trading_day = get_trading_day(now_chicago).strftime('%Y-%m-%d')
                
                # Query to get all position data we need
                # Pull directly from trades and realized tables for consistency
                if REALIZED_PMAX_ENABLED:
                    # Apply conditional SOD/Pmax adjustment to realized P&L at aggregation time
                    query = f"""
                    WITH all_symbols AS (
                        -- Get all unique symbols from both open and closed positions
                        SELECT DISTINCT symbol FROM trades_fifo WHERE quantity > 0
                        UNION
                        SELECT DISTINCT symbol FROM realized_fifo
                        WHERE 
                            -- Only include symbols with trades today
                            DATE(timestamp, 
                                 CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                                      THEN '+1 day' 
                                      ELSE '+0 day' 
                                 END) = ?
                        UNION  
                        SELECT DISTINCT symbol FROM realized_lifo
                        WHERE 
                            -- Only include symbols with trades today
                            DATE(timestamp, 
                                 CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                                      THEN '+1 day' 
                                      ELSE '+0 day' 
                                 END) = ?
                    ),
                    open_positions AS (
                        -- Get open positions from FIFO
                        SELECT 
                            symbol,
                            SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END) as open_position
                        FROM trades_fifo
                        WHERE quantity > 0
                        GROUP BY symbol
                    ),
                    closed_positions_fifo AS (
                        -- Pmax-adjusted realized for current trading day (FIFO)
                        -- Derive entry trading day from sequenceIdBeingOffset, and entry side from signs.
                        SELECT 
                            rf.symbol as symbol,
                            SUM(ABS(rf.quantity)) as closed_position,
                            SUM(
                                CASE 
                                    WHEN DATE(substr(rf.sequenceIdBeingOffset,1,4) || '-' || substr(rf.sequenceIdBeingOffset,5,2) || '-' || substr(rf.sequenceIdBeingOffset,7,2)) <> ?
                                         AND ABS(rf.exitPrice - rf.entryPrice) >= 1e-12
                                    THEN CASE 
                                             WHEN ((rf.exitPrice - rf.entryPrice) * rf.realizedPnL) > 0
                                             THEN (rf.exitPrice - COALESCE(sod.price, rf.entryPrice)) * rf.quantity * (CASE WHEN substr(rf.symbol,1,2) = 'TU' THEN 2000 ELSE {PNL_MULTIPLIER} END)
                                             ELSE (COALESCE(sod.price, rf.entryPrice) - rf.exitPrice) * rf.quantity * (CASE WHEN substr(rf.symbol,1,2) = 'TU' THEN 2000 ELSE {PNL_MULTIPLIER} END)
                                         END
                                    ELSE rf.realizedPnL
                                END
                            ) as fifo_realized_pnl
                        FROM realized_fifo rf
                        LEFT JOIN pricing sod ON sod.symbol = rf.symbol AND sod.price_type = 'sodTod'
                        WHERE 
                            -- Only realized rows for today's trading day
                            DATE(rf.timestamp, CASE WHEN CAST(strftime('%H', rf.timestamp) AS INTEGER) >= 17 THEN '+1 day' ELSE '+0 day' END) = ?
                        GROUP BY rf.symbol
                    ),
                    closed_positions_lifo AS (
                        -- Pmax-adjusted realized for current trading day (LIFO)
                        SELECT 
                            rl.symbol as symbol,
                            SUM(
                                CASE 
                                    WHEN DATE(substr(rl.sequenceIdBeingOffset,1,4) || '-' || substr(rl.sequenceIdBeingOffset,5,2) || '-' || substr(rl.sequenceIdBeingOffset,7,2)) <> ?
                                         AND ABS(rl.exitPrice - rl.entryPrice) >= 1e-12
                                    THEN CASE 
                                             WHEN ((rl.exitPrice - rl.entryPrice) * rl.realizedPnL) > 0
                                             THEN (rl.exitPrice - COALESCE(sodl.price, rl.entryPrice)) * rl.quantity * (CASE WHEN substr(rl.symbol,1,2) = 'TU' THEN 2000 ELSE {PNL_MULTIPLIER} END)
                                             ELSE (COALESCE(sodl.price, rl.entryPrice) - rl.exitPrice) * rl.quantity * (CASE WHEN substr(rl.symbol,1,2) = 'TU' THEN 2000 ELSE {PNL_MULTIPLIER} END)
                                         END
                                    ELSE rl.realizedPnL
                                END
                            ) as lifo_realized_pnl
                        FROM realized_lifo rl
                        LEFT JOIN pricing sodl ON sodl.symbol = rl.symbol AND sodl.price_type = 'sodTod'
                        WHERE 
                            DATE(rl.timestamp, CASE WHEN CAST(strftime('%H', rl.timestamp) AS INTEGER) >= 17 THEN '+1 day' ELSE '+0 day' END) = ?
                        GROUP BY rl.symbol
                    )
                    SELECT 
                        s.symbol,
                        COALESCE(o.open_position, 0) as open_position,
                        COALESCE(cf.closed_position, 0) as closed_position,
                        COALESCE(cf.fifo_realized_pnl, 0) as fifo_realized_pnl,
                        COALESCE(cl.lifo_realized_pnl, 0) as lifo_realized_pnl
                    FROM all_symbols s
                    LEFT JOIN open_positions o ON s.symbol = o.symbol
                    LEFT JOIN closed_positions_fifo cf ON s.symbol = cf.symbol
                    LEFT JOIN closed_positions_lifo cl ON s.symbol = cl.symbol
                    """
                else:
                    # Original behavior: sum raw realized PnL for today's trading day
                    query = """
                    WITH all_symbols AS (
                        -- Get all unique symbols from both open and closed positions
                        SELECT DISTINCT symbol FROM trades_fifo WHERE quantity > 0
                        UNION
                        SELECT DISTINCT symbol FROM realized_fifo
                        WHERE 
                            -- Only include symbols with trades today
                            DATE(timestamp, 
                                 CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                                      THEN '+1 day' 
                                      ELSE '+0 day' 
                                 END) = ?
                        UNION  
                        SELECT DISTINCT symbol FROM realized_lifo
                        WHERE 
                            -- Only include symbols with trades today
                            DATE(timestamp, 
                                 CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                                      THEN '+1 day' 
                                      ELSE '+0 day' 
                                 END) = ?
                    ),
                    open_positions AS (
                        -- Get open positions from FIFO
                        SELECT 
                            symbol,
                            SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END) as open_position
                        FROM trades_fifo
                        WHERE quantity > 0
                        GROUP BY symbol
                    ),
                    closed_positions_fifo AS (
                        -- Get closed positions and realized P&L from realized_fifo for current trading day
                        SELECT 
                            symbol,
                            SUM(ABS(quantity)) as closed_position,
                            SUM(realizedPnL) as fifo_realized_pnl
                        FROM realized_fifo
                        WHERE 
                            -- Calculate trading day: if hour >= 17 (5pm Chicago time), use next day
                            DATE(timestamp, 
                                 CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                                      THEN '+1 day' 
                                      ELSE '+0 day' 
                                 END) = ?
                        GROUP BY symbol
                    ),
                    closed_positions_lifo AS (
                        -- Get realized P&L from realized_lifo for current trading day
                        SELECT 
                            symbol,
                            SUM(realizedPnL) as lifo_realized_pnl
                        FROM realized_lifo
                        WHERE 
                            -- Calculate trading day: if hour >= 17 (5pm Chicago time), use next day
                            DATE(timestamp, 
                                 CASE WHEN CAST(strftime('%H', timestamp) AS INTEGER) >= 17 
                                      THEN '+1 day' 
                                      ELSE '+0 day' 
                                 END) = ?
                        GROUP BY symbol
                    )
                    SELECT 
                        s.symbol,
                        COALESCE(o.open_position, 0) as open_position,
                        COALESCE(cf.closed_position, 0) as closed_position,
                        COALESCE(cf.fifo_realized_pnl, 0) as fifo_realized_pnl,
                        COALESCE(cl.lifo_realized_pnl, 0) as lifo_realized_pnl
                    FROM all_symbols s
                    LEFT JOIN open_positions o ON s.symbol = o.symbol
                    LEFT JOIN closed_positions_fifo cf ON s.symbol = cf.symbol
                    LEFT JOIN closed_positions_lifo cl ON s.symbol = cl.symbol
                    """
                
                # Load the base position data
                if REALIZED_PMAX_ENABLED:
                    # Params mapping: all_symbols (fifo today), all_symbols (lifo today),
                    # closed_positions_fifo (entry day compare), closed_positions_fifo (today),
                    # closed_positions_lifo (entry day compare), closed_positions_lifo (today)
                    self.positions_cache = pd.read_sql_query(
                        query, conn,
                        params=[current_trading_day, current_trading_day, current_trading_day, current_trading_day, current_trading_day, current_trading_day]
                    )
                else:
                    self.positions_cache = pd.read_sql_query(
                        query, conn,
                        params=[current_trading_day, current_trading_day, current_trading_day, current_trading_day]
                    )
                
                # Add placeholder columns for unrealized P&L
                self.positions_cache['fifo_unrealized_pnl'] = 0.0
                self.positions_cache['lifo_unrealized_pnl'] = 0.0
                self.positions_cache['fifo_unrealized_pnl_close'] = 0.0
                self.positions_cache['lifo_unrealized_pnl_close'] = 0.0
                
                # Initialize Greek columns but preserve existing values from cache
                self.positions_cache['delta_y'] = None
                self.positions_cache['gamma_y'] = None
                self.positions_cache['speed_y'] = None
                self.positions_cache['theta'] = None
                self.positions_cache['vega'] = None
                self.positions_cache['has_greeks'] = False
                self.positions_cache['instrument_type'] = None
                
                # Restore Greeks from cache if available
                if hasattr(self, 'greek_data_cache') and self.greek_data_cache:
                    for symbol in self.positions_cache['symbol']:
                        if symbol in self.greek_data_cache:
                            greek_data = self.greek_data_cache[symbol]
                            open_position = self.positions_cache.loc[self.positions_cache['symbol'] == symbol, 'open_position'].values[0]
                            
                            # Restore position-weighted Greeks
                            idx = self.positions_cache['symbol'] == symbol
                            self.positions_cache.loc[idx, 'delta_y'] = self._safe_multiply(greek_data.get('delta_y'), open_position)
                            self.positions_cache.loc[idx, 'gamma_y'] = self._safe_multiply(greek_data.get('gamma_y'), open_position)
                            self.positions_cache.loc[idx, 'speed_y'] = self._safe_multiply(greek_data.get('speed_y'), open_position)
                            self.positions_cache.loc[idx, 'theta'] = self._safe_multiply(greek_data.get('theta_F'), open_position)
                            self.positions_cache.loc[idx, 'vega'] = self._safe_multiply(greek_data.get('vega_y'), open_position)
                            self.positions_cache.loc[idx, 'has_greeks'] = True
                            self.positions_cache.loc[idx, 'instrument_type'] = greek_data.get('instrument_type')
                
                # Calculate unrealized P&L for all positions
                price_dicts = load_pricing_dictionaries(conn)
                
                for method in ['fifo', 'lifo']:
                    positions_df = view_unrealized_positions(conn, method)
                    if not positions_df.empty:
                        # Group by symbol and calculate total unrealized P&L
                        for symbol in positions_df['symbol'].unique():
                            symbol_positions = positions_df[positions_df['symbol'] == symbol]
                            
                            # Calculate LIVE unrealized P&L
                            unrealized_list = calculate_unrealized_pnl(symbol_positions, price_dicts, 'live')
                            total_unrealized = sum(u['unrealizedPnL'] for u in unrealized_list)
                            
                            # Calculate CLOSE unrealized P&L
                            total_unrealized_close = 0.0
                            # Check if we have today's close price
                            today = datetime.now().strftime('%Y-%m-%d')
                            close_query = """
                            SELECT price, timestamp 
                            FROM pricing 
                            WHERE symbol = ? AND price_type = 'close'
                            """
                            close_result = conn.execute(close_query, (symbol,)).fetchone()
                            
                            if close_result and close_result[1] and close_result[1].startswith(today):
                                # Create modified price dict with close price as 'now'
                                close_price_dicts = price_dicts.copy()
                                close_price_dicts['now'] = price_dicts.get('close', {}).copy()
                                
                                # Calculate unrealized with close prices
                                unrealized_close_list = calculate_unrealized_pnl(symbol_positions, close_price_dicts, 'live')
                                total_unrealized_close = sum(u['unrealizedPnL'] for u in unrealized_close_list)
                            
                            # Update the cache
                            mask = self.positions_cache['symbol'] == symbol
                            if mask.any():
                                self.positions_cache.loc[mask, f'{method}_unrealized_pnl'] = total_unrealized
                                self.positions_cache.loc[mask, f'{method}_unrealized_pnl_close'] = total_unrealized_close
                
                load_time = time.time() - start_time
                logger.info(f"Loaded {len(self.positions_cache)} positions into memory in {load_time:.2f}s")
                
            finally:
                conn.close()
    
    def _listen_for_redis_messages(self):
        """
        Listen for messages from both Redis channels:
        - spot_risk:results_channel: New Greek data
        - positions:changed: Signal to refresh positions from DB
        """
        logger.info("Starting Redis listener thread for dual-channel subscription...")
        
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.redis_channel, "positions:changed")
        
        for message in pubsub.listen():
            if message['type'] != 'message':
                continue
            
            # Note: channel comes as bytes when decode_responses=False
            channel = message['channel'].decode('utf-8') if isinstance(message['channel'], bytes) else message['channel']
            
            try:
                if channel == "positions:changed":
                    # Refresh signal received - reload positions from database
                    # This channel still sends simple string messages
                    logger.info("Received positions:changed signal. Refreshing cache from database...")
                    self._load_positions_from_db()
                    
                    # Queue the updated positions for writing to database
                    if not self.positions_cache.empty:
                        logger.debug("Queueing updated positions for database write after price change")
                        self.db_write_queue.put(self.positions_cache.copy())
                    
                    # Also update daily positions with new prices
                    conn = sqlite3.connect(self.trades_db_path)
                    try:
                        from .data_manager import update_daily_positions_unrealized_pnl
                        update_daily_positions_unrealized_pnl(conn)
                        logger.debug("Updated daily positions unrealized P&L after positions change")
                    finally:
                        conn.close()
                    
                elif channel == self.redis_channel:
                    # Greek data received - process with in-memory cache
                    start_time = time.time()
                    
                    # Deserialize the pickled envelope containing Arrow data
                    payload = pickle.loads(message['data'])
                    publish_timestamp = payload.get('publish_timestamp', start_time)
                    latency = start_time - publish_timestamp
                    
                    logger.info(f"Received new Greek data package from Redis (Latency: {latency:.3f}s).")
                    
                    # Deserialize Arrow data to DataFrame
                    buffer = payload['data']
                    reader = pa.ipc.open_stream(buffer)
                    arrow_table = reader.read_all()
                    greeks_df = arrow_table.to_pandas()
                    logger.info(f"--- DIAGNOSTIC: Received Greeks DataFrame from Redis ---\n{greeks_df.to_string()}")
                    
                    if greeks_df.empty:
                        logger.warning("Received an empty DataFrame in the payload. Skipping.")
                        continue
                    
                    # Process Greek data
                    if 'key' not in greeks_df.columns:
                        logger.error("Incoming Greek data is missing the 'key' column for symbol translation.")
                        continue
                    
                    # Create the bloomberg_symbol column using the Rosetta Stone translator
                    greeks_df['bloomberg_symbol'] = greeks_df['key'].apply(
                        lambda x: self.symbol_translator.translate(x, 'actantrisk', 'bloomberg') if x else None
                    )
                    
                    # Drop rows where translation failed
                    greeks_df.dropna(subset=['bloomberg_symbol'], inplace=True)
                    
                    # Keep only the last entry for each symbol
                    greeks_df.drop_duplicates(subset=['bloomberg_symbol'], keep='last', inplace=True)
                    
                    # Update Greek cache
                    self.greek_data_cache = greeks_df.set_index('bloomberg_symbol').to_dict('index')
                    logger.info(f"Greek cache updated with {len(self.greek_data_cache)} unique symbols from batch '{payload['batch_id']}'.")
                    
                    # Update positions with new Greeks
                    self._update_positions_with_greeks()
                    
                    execution_time = time.time() - start_time
                    logger.info(f"Finished processing batch '{payload['batch_id']}'. (Execution: {execution_time:.3f}s)")
                    
            except redis.exceptions.ConnectionError as e:
                logger.error(f"Redis connection error: {e}. Retrying in 30 seconds...")
                time.sleep(30)
                pubsub = self.redis_client.pubsub()
                pubsub.subscribe(self.redis_channel, "positions:changed")
            except Exception as e:
                logger.error(f"Error in Redis listener: {e}", exc_info=True)
    
    def _update_positions_with_greeks(self):
        """
        Update the in-memory positions cache with new Greek data.
        This performs a fast in-memory merge and then writes to database.
        """
        with self.db_lock:
            if self.positions_cache.empty:
                logger.warning("Positions cache is empty. Loading from database...")
                self._load_positions_from_db()
                return
            
            # Reset Greek columns before updating
            self.positions_cache['delta_y'] = None
            self.positions_cache['gamma_y'] = None
            self.positions_cache['speed_y'] = None
            self.positions_cache['theta'] = None
            self.positions_cache['vega'] = None
            self.positions_cache['has_greeks'] = False
            self.positions_cache['instrument_type'] = None
            
            # Update Greeks for each symbol in cache
            for symbol in self.positions_cache['symbol']:
                if symbol in self.greek_data_cache:
                    greek_data = self.greek_data_cache[symbol]
                    open_position = self.positions_cache.loc[self.positions_cache['symbol'] == symbol, 'open_position'].values[0]
                    
                    # Calculate position-weighted Greeks
                    idx = self.positions_cache['symbol'] == symbol
                    self.positions_cache.loc[idx, 'delta_y'] = self._safe_multiply(greek_data.get('delta_y'), open_position)
                    self.positions_cache.loc[idx, 'gamma_y'] = self._safe_multiply(greek_data.get('gamma_y'), open_position)
                    self.positions_cache.loc[idx, 'speed_y'] = self._safe_multiply(greek_data.get('speed_y'), open_position)
                    self.positions_cache.loc[idx, 'theta'] = self._safe_multiply(greek_data.get('theta_F'), open_position)
                    self.positions_cache.loc[idx, 'vega'] = self._safe_multiply(greek_data.get('vega_y'), open_position)
                    self.positions_cache.loc[idx, 'has_greeks'] = True
                    self.positions_cache.loc[idx, 'instrument_type'] = greek_data.get('instrument_type')
            
            # Write updated positions to the queue for the writer thread
            if not self.positions_cache.empty:
                self.db_write_queue.put(self.positions_cache.copy())
    
    def _safe_multiply(self, value, position):
        """Safely multiply Greek value by position, handling None values."""
        if value is None or position is None:
            return None
        return value * position
    
    def _write_positions_to_db(self, positions_df):
        """Write a DataFrame of positions to the database."""
        # This function now runs in its own thread with its own short-lived connection
        conn = sqlite3.connect(self.trades_db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Write all positions to database
            for _, row in positions_df.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO positions (
                        symbol, open_position, closed_position,
                        delta_y, gamma_y, speed_y, theta, vega,
                        fifo_realized_pnl, fifo_unrealized_pnl,
                        lifo_realized_pnl, lifo_unrealized_pnl,
                        fifo_unrealized_pnl_close, lifo_unrealized_pnl_close,
                        last_updated, last_trade_update, last_greek_update,
                        has_greeks, instrument_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['symbol'],
                    row['open_position'],
                    row['closed_position'],
                    row['delta_y'],
                    row['gamma_y'],
                    row['speed_y'],
                    row['theta'],
                    row['vega'],
                    row['fifo_realized_pnl'],
                    row['fifo_unrealized_pnl'],
                    row['lifo_realized_pnl'],
                    row['lifo_unrealized_pnl'],
                    row.get('fifo_unrealized_pnl_close', 0),
                    row.get('lifo_unrealized_pnl_close', 0),
                    now,
                    now,  # last_trade_update
                    now if row['has_greeks'] else None,  # last_greek_update
                    1 if row['has_greeks'] else 0,
                    row['instrument_type']
                ))
            
            conn.commit()
            logger.debug(f"Writer thread: successfully wrote {len(positions_df)} positions to database.")
            
            # This part still uses a direct connection but it's a read-heavy operation
            # and should be fast. Keeping it here for simplicity for now.
            from .data_manager import update_daily_positions_unrealized_pnl
            update_daily_positions_unrealized_pnl(conn)
            logger.debug("Writer thread: updated daily positions unrealized P&L.")
            
        finally:
            conn.close()

    def _db_writer_thread(self):
        """Dedicated thread to write positions from the queue to the database."""
        logger.info("Database writer thread started.")
        while True:
            try:
                # Block until an item is available in the queue
                positions_df_to_write = self.db_write_queue.get()
                
                if positions_df_to_write is None:  # Sentinel value to stop the thread
                    logger.info("Writer thread received stop signal. Exiting.")
                    break
                
                self._write_positions_to_db(positions_df_to_write)
                self.db_write_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in DB writer thread: {e}", exc_info=True)

    @monitor()
    def run_aggregation_service(self):
        """
        Runs as a persistent service with in-memory caching.
        Subscribes to two Redis channels:
        - spot_risk:results_channel: For new Greek data
        - positions:changed: For signals to refresh positions from DB
        """
        logger.info("Starting Positions Aggregator service with in-memory caching...")
        
        # Load initial positions into memory and push to writer queue
        self._load_positions_from_db()
        if not self.positions_cache.empty:
            self.db_write_queue.put(self.positions_cache.copy())
            
        # Start the database writer thread
        writer_thread = threading.Thread(target=self._db_writer_thread, daemon=True)
        writer_thread.start()
        
        # Start the Redis listener in a separate thread
        listener_thread = threading.Thread(target=self._listen_for_redis_messages, daemon=True)
        listener_thread.start()
        
        logger.info("Positions Aggregator service started successfully with writer and listener threads.")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)  # Sleep for 0.5 seconds
                # Could add periodic health checks here
        except KeyboardInterrupt:
            logger.info("Positions Aggregator service shutting down...")

    # Note: Old methods removed - all operations now happen via in-memory cache
    # The following methods have been removed as they're no longer needed:
    # - update_position() 
    # - _get_trade_data()
    # - _get_greek_data() 
    # - _update_positions_table()
    # - _get_all_symbols()
    # All functionality is now handled through the in-memory cache operations 