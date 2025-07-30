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
import redis
import json
import time

from .config import DEFAULT_SYMBOL
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
        self.redis_client = redis.Redis(decode_responses=True)
        self.redis_channel = "spot_risk:results_channel"
        self.greek_data_cache = {}
        logger.info("Initialized PositionsAggregator")

    @monitor()
    def run_aggregation_service(self):
        """
        Runs as a persistent service, subscribing to a Redis channel for new
        Greek data and updating the positions table in trades.db accordingly.
        """
        logger.info(f"Starting Positions Aggregator service, subscribing to Redis channel '{self.redis_channel}'...")
        
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.redis_channel)
        
        for message in pubsub.listen():
            # Filter out subscribe confirmation messages
            if message['type'] != 'message':
                continue
            
            try:
                # --- Start Instrumentation ---
                start_time = time.time()
                payload = json.loads(message['data'])
                publish_timestamp = payload.get('publish_timestamp', start_time)
                latency = start_time - publish_timestamp
                # --- End Instrumentation ---

                logger.info(f"Received new Greek data package from Redis (Latency: {latency:.3f}s).")
                
                greeks_df = pd.read_json(payload['data'], orient='records')
                if greeks_df.empty:
                    logger.warning("Received an empty DataFrame in the payload. Skipping.")
                    continue

                # The symbol translator expects ActantRisk format. Our DataFrame from the spot risk
                # pipeline uses 'key' as the column for this. We need to ensure that column exists.
                if 'key' not in greeks_df.columns:
                    logger.error("Incoming Greek data is missing the 'key' column for symbol translation.")
                    continue
                
                # Create the bloomberg_symbol column using the Rosetta Stone translator
                greeks_df['bloomberg_symbol'] = greeks_df['key'].apply(
                    lambda x: self.symbol_translator.translate(x, 'actantrisk', 'bloomberg') if x else None
                )

                # Drop rows where translation failed, as they cannot be indexed
                greeks_df.dropna(subset=['bloomberg_symbol'], inplace=True)

                # There can be multiple entries for the same instrument (e.g., from NET_FUTURES aggregates
                # in each chunk). We must keep only the last, most complete entry.
                greeks_df.drop_duplicates(subset=['bloomberg_symbol'], keep='last', inplace=True)

                self.greek_data_cache = greeks_df.set_index('bloomberg_symbol').to_dict('index')
                logger.info(f"Greek cache updated with {len(self.greek_data_cache)} unique symbols from batch '{payload['batch_id']}'.")

                self.update_all_positions()
                
                execution_time = time.time() - start_time
                logger.info(f"Finished processing batch '{payload['batch_id']}'. (Execution: {execution_time:.3f}s)")

            except redis.exceptions.ConnectionError as e:
                logger.error(f"Redis connection error: {e}. Retrying in 30 seconds...")
                time.sleep(30)
                # Re-subscribe after connection loss
                pubsub.subscribe(self.redis_channel)
            except Exception as e:
                logger.error(f"An unexpected error occurred in the aggregation service: {e}", exc_info=True)
                time.sleep(10)

    @monitor()
    def update_all_positions(self) -> Tuple[int, int]:
        """
        Update all positions in the POSITIONS table.
        
        Returns:
            Tuple of (successful_updates, failed_updates)
        """
        success_count = 0
        fail_count = 0
        
        # Get all unique symbols from trades
        symbols = self._get_all_symbols()
        
        for symbol in symbols:
            if self.update_position(symbol):
                success_count += 1
            else:
                fail_count += 1
                
        logger.info(f"Updated {success_count} positions, {fail_count} failures")
        return success_count, fail_count
    
    def update_position(self, symbol: str) -> bool:
        """
        Update a single position in the POSITIONS table.
        
        Args:
            symbol: Bloomberg format symbol to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Gather data from both sources
            trade_data = self._get_trade_data(symbol)
            # Use the in-memory cache, which was just updated.
            greek_data = self._get_greek_data(symbol)
            
            # Update positions table
            self._update_positions_table(symbol, trade_data, greek_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating position for {symbol}: {e}")
            return False
    
    def _get_trade_data(self, symbol: str) -> Dict:
        """Get position and P&L data from trades.db."""
        conn = sqlite3.connect(self.trades_db_path)
        cursor = conn.cursor()
        
        data = {
            'open_position': 0,
            'closed_position': 0,
            'fifo_realized_pnl': 0,
            'fifo_unrealized_pnl': 0,
            'lifo_realized_pnl': 0,
            'lifo_unrealized_pnl': 0
        }
        
        try:
            # Get current trading day
            current_trading_day = get_trading_day(datetime.now()).strftime('%Y-%m-%d')
            
            # Get open positions (net quantity)
            for method in ['fifo', 'lifo']:
                cursor.execute(f"""
                    SELECT SUM(CASE WHEN buySell = 'B' THEN quantity ELSE -quantity END)
                    FROM trades_{method}
                    WHERE symbol = ? AND quantity > 0
                """, (symbol,))
                result = cursor.fetchone()
                if method == 'fifo':  # Use FIFO as primary position
                    data['open_position'] = result[0] if result[0] else 0
            
            # Get realized P&L for current trading day only
            for method in ['fifo', 'lifo']:
                cursor.execute("""
                    SELECT realized_pnl
                    FROM daily_positions
                    WHERE symbol = ? AND method = ? AND date = ?
                """, (symbol, method, current_trading_day))
                result = cursor.fetchone()
                data[f'{method}_realized_pnl'] = result[0] if result and result[0] else 0
            
            # Get closed positions from daily_positions for current trading day only
            cursor.execute("""
                SELECT closed_position
                FROM daily_positions
                WHERE symbol = ? AND method = 'fifo' AND date = ?
            """, (symbol, current_trading_day))
            result = cursor.fetchone()
            data['closed_position'] = result[0] if result and result[0] else 0
            
            # Calculate unrealized P&L
            price_dicts = load_pricing_dictionaries(conn)
            
            for method in ['fifo', 'lifo']:
                positions_df = view_unrealized_positions(conn, method)
                positions_df = positions_df[positions_df['symbol'] == symbol]
                
                if not positions_df.empty:
                    unrealized_list = calculate_unrealized_pnl(positions_df, price_dicts, 'live')
                    total_unrealized = sum(u['unrealizedPnL'] for u in unrealized_list)
                    data[f'{method}_unrealized_pnl'] = total_unrealized
                    
        finally:
            conn.close()
            
        return data
    
    def _get_greek_data(self, symbol: str) -> Dict:
        """
        Get Greek data for a symbol from the in-memory cache.
        The cache is populated by the Redis listener.
        """
        if not self.greek_data_cache:
            return {'has_greeks': False}

        # The symbol is expected to be a Bloomberg symbol here
        greek_row = self.greek_data_cache.get(symbol)

        if greek_row:
            # Map the DataFrame columns to the expected dictionary keys
            return {
                'has_greeks': True,
                'delta_y': greek_row.get('delta_y'),
                'gamma_y': greek_row.get('gamma_y'),
                'speed_y': greek_row.get('speed_y'),
                'theta': greek_row.get('theta_F'), # Note: Mapping theta_F to theta
                'vega': greek_row.get('vega_y'),
                'instrument_type': greek_row.get('instrument_type')
            }
        else:
            return {'has_greeks': False}
    
    def _update_positions_table(self, symbol: str, trade_data: Dict, greek_data: Dict):
        """Update the positions table with aggregated data."""
        conn = sqlite3.connect(self.trades_db_path)
        cursor = conn.cursor()
        
        try:
            # Prepare the update
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get open position for Greek multiplication
            open_position = trade_data.get('open_position', 0)
            
            # Helper function to multiply Greek by position safely
            def position_weighted_greek(greek_value, position):
                """Calculate position-weighted Greek, handling None and edge cases."""
                if greek_value is None or position is None:
                    return None
                # If position is 0, the weighted Greek is 0
                return greek_value * position
            
            # Calculate position-weighted Greeks
            weighted_delta_y = position_weighted_greek(greek_data.get('delta_y'), open_position)
            weighted_gamma_y = position_weighted_greek(greek_data.get('gamma_y'), open_position)
            weighted_speed_y = position_weighted_greek(greek_data.get('speed_y'), open_position)
            weighted_theta = position_weighted_greek(greek_data.get('theta'), open_position)
            weighted_vega = position_weighted_greek(greek_data.get('vega'), open_position)
            
            # Log if we're applying position weighting
            if greek_data.get('has_greeks') and open_position != 0:
                logger.debug(f"Applied position weighting to Greeks for {symbol} (position={open_position})")
            
            cursor.execute("""
                INSERT OR REPLACE INTO positions (
                    symbol, open_position, closed_position,
                    delta_y, gamma_y, speed_y, theta, vega,
                    fifo_realized_pnl, fifo_unrealized_pnl,
                    lifo_realized_pnl, lifo_unrealized_pnl,
                    last_updated, last_trade_update, last_greek_update,
                    has_greeks, instrument_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                trade_data['open_position'],
                trade_data['closed_position'],
                weighted_delta_y,
                weighted_gamma_y,
                weighted_speed_y,
                weighted_theta,
                weighted_vega,
                trade_data['fifo_realized_pnl'],
                trade_data['fifo_unrealized_pnl'],
                trade_data['lifo_realized_pnl'],
                trade_data['lifo_unrealized_pnl'],
                now,
                now,  # last_trade_update
                now if greek_data.get('has_greeks') else None,  # last_greek_update
                1 if greek_data.get('has_greeks') else 0,
                greek_data.get('instrument_type')
            ))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def _get_all_symbols(self) -> List[str]:
        """Get all unique symbols from trades database."""
        conn = sqlite3.connect(self.trades_db_path)
        cursor = conn.cursor()
        
        symbols = set()
        
        try:
            # Get symbols from trades tables
            for table in ['trades_fifo', 'trades_lifo', 'realized_fifo', 'realized_lifo']:
                cursor.execute(f"SELECT DISTINCT symbol FROM {table}")
                symbols.update(row[0] for row in cursor.fetchall())
                
        finally:
            conn.close()
            
        return list(symbols) 