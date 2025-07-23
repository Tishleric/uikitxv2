"""
EOD P&L Snapshot Service

This service monitors for 4pm market price updates and calculates end-of-day
P&L snapshots with settlement-aware logic. P&L is calculated for the 2pm-to-2pm
period that ended at 2pm today (calculated at 4pm when settlement prices arrive).
"""

import logging
import sqlite3
import asyncio
from datetime import datetime, date, timedelta, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from lib.monitoring.decorators import monitor
from .settlement_constants import (
    CHICAGO_TZ, SETTLEMENT_TIME, EOD_TIME,
    get_pnl_period_boundaries, get_eod_boundary,
    get_pnl_date_for_trade, format_pnl_period,
    split_position_at_settlement, localize_to_chicago
)
from .tyu5_service import TYU5Service
from .tyu5_runner import TYU5Runner
from .market_price_monitor import MarketPriceMonitor

logger = logging.getLogger(__name__)


class EODSnapshotService:
    """Service for calculating and storing EOD P&L snapshots."""
    
    def __init__(self, 
                 market_prices_db: str = "data/output/market_prices/market_prices.db",
                 pnl_tracker_db: str = "data/output/pnl/pnl_tracker.db"):
        """
        Initialize the EOD snapshot service.
        
        Args:
            market_prices_db: Path to market prices database
            pnl_tracker_db: Path to P&L tracker database
        """
        self.market_prices_db = market_prices_db
        self.pnl_tracker_db = pnl_tracker_db
        self.last_processed_date = None
        self._running = False
        self.price_monitor = MarketPriceMonitor(market_prices_db)
        
    @monitor()
    async def monitor_for_eod(self, check_interval: int = 60):
        """
        Main monitoring loop that checks for 4pm price updates.
        
        Args:
            check_interval: Seconds between checks
        """
        self._running = True
        logger.info("Starting EOD snapshot monitoring")
        
        while self._running:
            try:
                # Check if 4pm batch has started
                if self.price_monitor.detect_4pm_batch_start():
                    # Track symbol updates
                    self.price_monitor.track_symbol_updates()
                    
                    # Check if batch is complete
                    if self.price_monitor.is_batch_complete():
                        trade_date = self._get_latest_price_date()
                        
                        if trade_date and trade_date != self.last_processed_date:
                            # At 4pm on trade_date, we calculate P&L for the period
                            # that ended at 2pm today
                            logger.info(f"4pm price batch complete for {trade_date}")
                            logger.info(f"Calculating P&L for period: {format_pnl_period(trade_date)}")
                            
                            # Log completion stats
                            stats = self.price_monitor.get_completion_stats()
                            logger.info(f"Completion stats: {stats['updated_symbols']}/{stats['total_symbols']} "
                                      f"symbols ({stats['completion_ratio']:.1%})")
                            
                            # Trigger EOD snapshot for the P&L period ending at 2pm today
                            success = await self.trigger_eod_snapshot(trade_date)
                            
                            if success:
                                self.last_processed_date = trade_date
                                self.price_monitor.reset_tracking()
                                logger.info(f"EOD snapshot completed for P&L date {trade_date}")
                            else:
                                logger.error(f"EOD snapshot failed for P&L date {trade_date}")
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in EOD monitoring loop: {e}")
                await asyncio.sleep(check_interval)
    
    def stop_monitoring(self):
        """Stop the monitoring loop."""
        self._running = False
        logger.info("Stopping EOD snapshot monitoring")
    
    def _get_latest_price_date(self) -> Optional[date]:
        """Get the trade date for the latest price updates."""
        try:
            conn = sqlite3.connect(self.market_prices_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(trade_date) 
                FROM futures_prices
                WHERE prior_close IS NOT NULL
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return datetime.strptime(result[0], '%Y-%m-%d').date()
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest price date: {e}")
            return None
    
    @monitor()
    async def trigger_eod_snapshot(self, pnl_date: date) -> bool:
        """
        Main EOD processing logic for the P&L period ending at 2pm on pnl_date.
        
        At 4pm on Tuesday, this calculates P&L for Monday 2pm to Tuesday 2pm.
        Uses SQL aggregation of P&L components instead of recalculation.
        
        Args:
            pnl_date: The P&L date (period ends at 2pm on this date)
            
        Returns:
            True if successful
        """
        try:
            # Get P&L period boundaries
            period_start, period_end = get_pnl_period_boundaries(pnl_date)
            logger.info(f"Starting EOD snapshot for P&L date {pnl_date}")
            logger.info(f"P&L Period: {period_start} to {period_end}")
            
            # Calculate P&L for the period using SQL aggregation
            eod_results = self.calculate_settlement_aware_pnl_with_fifo(pnl_date)
            
            if eod_results.empty:
                logger.warning("No P&L data found for period")
                return self._write_empty_snapshot(pnl_date)
            
            # Write to EOD history
            success = self.write_snapshot_to_history(eod_results, pnl_date)
            
            return success
            
        except Exception as e:
            logger.error(f"Error in EOD snapshot: {e}")
            return False
    
    def _run_tyu5_for_period(self, pnl_date: date, period_start: datetime, period_end: datetime) -> bool:
        """
        Run TYU5 calculation for trades within the P&L period.
        
        TODO: Currently TYU5 doesn't support period filtering. 
        For now, we run for all trades and filter results.
        In Phase 3, we'll enhance TYU5 to accept period boundaries.
        """
        try:
            # TYU5Service will use latest prices which include settlement prices
            service = TYU5Service()
            
            # Run calculation for the trade date
            # TODO: Pass period boundaries to TYU5
            result = service.calculate_pnl(trade_date=pnl_date)
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error running TYU5: {e}")
            return False
    
    def _get_tyu5_results(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get the latest TYU5 calculation results."""
        try:
            conn = sqlite3.connect(self.pnl_tracker_db)
            
            # Get positions with P&L
            positions_df = pd.read_sql_query("""
                SELECT * FROM tyu5_positions
                WHERE Net_Quantity != 0
            """, conn)
            
            # Get FIFO breakdown
            breakdown_df = pd.read_sql_query("""
                SELECT * FROM tyu5_position_breakdown
            """, conn)
            
            conn.close()
            
            return positions_df, breakdown_df
            
        except Exception as e:
            logger.error(f"Error getting TYU5 results: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def _get_settlement_prices_for_period(self, pnl_date: date) -> Dict[str, Dict[str, float]]:
        """
        Get settlement prices for P&L calculation.
        
        For P&L date T (covering T-1 2pm to T 2pm):
        - Previous settlement: px_settle from T-1 (for positions opened before period)
        - Current settlement: px_settle from T (for period-end valuation)
        
        Returns:
            Dict mapping symbol to {'prev_settle': float, 'curr_settle': float}
        """
        prices = {}
        
        try:
            conn = sqlite3.connect(self.market_prices_db)
            
            # Get previous trading day (TODO: handle weekends/holidays properly)
            prev_date = pnl_date - timedelta(days=1)
            
            # Query both days' settlement prices
            query = """
            WITH combined_prices AS (
                SELECT 
                    symbol,
                    trade_date,
                    prior_close as px_settle
                FROM futures_prices
                WHERE trade_date IN (?, ?) AND prior_close IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    symbol,
                    trade_date,
                    prior_close as px_settle
                FROM options_prices
                WHERE trade_date IN (?, ?) AND prior_close IS NOT NULL
            )
            SELECT 
                symbol,
                MAX(CASE WHEN trade_date = ? THEN px_settle END) as prev_settle,
                MAX(CASE WHEN trade_date = ? THEN px_settle END) as curr_settle
            FROM combined_prices
            GROUP BY symbol
            """
            
            df = pd.read_sql_query(query, conn, params=(
                prev_date.isoformat(),
                pnl_date.isoformat(),
                prev_date.isoformat(),
                pnl_date.isoformat(),
                prev_date.isoformat(),
                pnl_date.isoformat()
            ))
            
            conn.close()
            
            # Format results
            for _, row in df.iterrows():
                symbol = row['symbol']
                prices[symbol] = {
                    'prev_settle': float(row['prev_settle']) if pd.notna(row['prev_settle']) else None,
                    'curr_settle': float(row['curr_settle']) if pd.notna(row['curr_settle']) else None
                }
            
            logger.info(f"Loaded settlement prices for {len(prices)} symbols")
            logger.debug(f"Date range: {prev_date} to {pnl_date}")
            
            return prices
            
        except Exception as e:
            logger.error(f"Error getting settlement prices: {e}")
            return {}
    
    @monitor()
    def calculate_settlement_aware_pnl_with_fifo(self, 
                                                pnl_date: datetime.date) -> pd.DataFrame:
        """
        Calculate P&L for the 2pm-to-2pm period using SQL aggregation.
        
        Args:
            pnl_date: The P&L date (e.g., Tuesday for Monday 2pm to Tuesday 2pm)
            
        Returns:
            DataFrame with EOD P&L by symbol
        """
        # Generate settlement keys for the period
        yesterday = pnl_date - timedelta(days=1)
        start_key = yesterday.strftime("%Y%m%d_1400")
        end_key = pnl_date.strftime("%Y%m%d_1400")
        
        logger.info(f"Calculating P&L for period {start_key} to {end_key}")
        
        conn = sqlite3.connect(self.pnl_tracker_db) # Changed from self.pnl_db_path to self.pnl_tracker_db
        
        try:
            # Query P&L components for the period
            query = """
                SELECT 
                    symbol,
                    SUM(pnl_amount) as period_pnl,
                    COUNT(*) as component_count,
                    GROUP_CONCAT(DISTINCT component_type) as component_types
                FROM tyu5_pnl_components
                WHERE start_settlement_key = ? 
                  AND end_settlement_key = ?
                GROUP BY symbol
            """
            
            results_df = pd.read_sql_query(query, conn, params=(start_key, end_key))
            
            if results_df.empty:
                logger.warning(f"No P&L components found for period {start_key} to {end_key}")
                return pd.DataFrame()
            
            # Get open positions from snapshots for unrealized P&L
            snapshot_query = """
                SELECT 
                    symbol,
                    SUM(quantity_remaining) as open_quantity,
                    SUM(quantity_remaining * entry_price) / SUM(quantity_remaining) as avg_entry_price
                FROM tyu5_open_lot_snapshots
                WHERE settlement_key = ?
                GROUP BY symbol
            """
            
            open_positions = pd.read_sql_query(snapshot_query, conn, params=(end_key,))
            
            # Merge with settlement prices
            settlement_prices = self._get_settlement_prices_for_period(
                yesterday, pnl_date, results_df['symbol'].unique().tolist()
            )
            
            # Build final result
            final_results = []
            for _, row in results_df.iterrows():
                symbol = row['symbol']
                realized_pnl = row['period_pnl']
                
                # Get unrealized P&L if position is still open
                unrealized_pnl = 0
                position_quantity = 0
                
                if symbol in open_positions.set_index('symbol').index:
                    open_pos = open_positions[open_positions['symbol'] == symbol].iloc[0]
                    position_quantity = open_pos['open_quantity']
                    avg_entry = open_pos['avg_entry_price']
                    
                    # Use settlement price for unrealized calculation
                    curr_settle = settlement_prices.get(pnl_date, {}).get(symbol)
                    if curr_settle:
                        unrealized_pnl = position_quantity * (curr_settle - avg_entry) * 1000 # Changed multiplier to 1000
                
                final_results.append({
                    'snapshot_date': pnl_date,
                    'symbol': symbol,
                    'position_quantity': position_quantity,
                    'realized_pnl': realized_pnl,
                    'unrealized_pnl_settle': unrealized_pnl,
                    'unrealized_pnl_current': unrealized_pnl,  # Same for now
                    'total_daily_pnl': realized_pnl + unrealized_pnl,
                    'settlement_price': settlement_prices.get(pnl_date, {}).get(symbol),
                    'current_price': settlement_prices.get(pnl_date, {}).get(symbol),
                    'pnl_period_start': f"{yesterday} 14:00:00",
                    'pnl_period_end': f"{pnl_date} 14:00:00",
                    'trades_in_period': row['component_count']
                })
            
            return pd.DataFrame(final_results)
            
        except Exception as e:
            logger.error(f"Error calculating settlement-aware P&L: {e}")
            raise
        finally:
            conn.close()
    
    @monitor()
    def write_snapshot_to_history(self, 
                                snapshot_df: pd.DataFrame, 
                                pnl_date: date) -> bool:
        """
        Write EOD snapshot to history table and update TOTAL row.
        
        Args:
            snapshot_df: DataFrame with position snapshots
            pnl_date: The P&L date (period ended at 2pm on this date)
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.pnl_tracker_db)
            cursor = conn.cursor()
            
            # Get period boundaries for logging
            period_start, period_end = get_pnl_period_boundaries(pnl_date)
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Delete existing snapshots for this P&L date
            cursor.execute("""
                DELETE FROM tyu5_eod_pnl_history 
                WHERE snapshot_date = ?
            """, (pnl_date.isoformat(),))
            
            # Insert individual position snapshots
            for _, snapshot in snapshot_df.iterrows():
                cursor.execute("""
                    INSERT INTO tyu5_eod_pnl_history
                    (snapshot_date, symbol, position_quantity, realized_pnl,
                     unrealized_pnl_settle, unrealized_pnl_current, total_daily_pnl,
                     settlement_price, current_price, pnl_period_start, pnl_period_end,
                     trades_in_period)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pnl_date.isoformat(),
                    snapshot['symbol'],
                    snapshot.get('position_quantity', 0),
                    snapshot.get('realized_pnl', 0),
                    snapshot.get('unrealized_pnl_settle', 0),
                    snapshot.get('unrealized_pnl_current', 0),
                    snapshot.get('total_daily_pnl', 0),
                    snapshot.get('settlement_price'),
                    snapshot.get('current_price'),
                    snapshot.get('pnl_period_start'),
                    snapshot.get('pnl_period_end'),
                    snapshot.get('trades_in_period')
                ))
            
            # Calculate and insert TOTAL row
            total_realized = sum(s['realized_pnl'] for s in snapshot_df.to_dict('records'))
            total_unrealized_settle = sum(s['unrealized_pnl_settle'] for s in snapshot_df.to_dict('records'))
            total_unrealized_current = sum(s['unrealized_pnl_current'] for s in snapshot_df.to_dict('records'))
            total_pnl = sum(s['total_daily_pnl'] for s in snapshot_df.to_dict('records'))
            
            cursor.execute("""
                INSERT INTO tyu5_eod_pnl_history
                (snapshot_date, symbol, position_quantity, realized_pnl,
                 unrealized_pnl_settle, unrealized_pnl_current, total_daily_pnl,
                 settlement_price, current_price, pnl_period_start, pnl_period_end,
                 trades_in_period)
                VALUES (?, 'TOTAL', 0, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)
            """, (
                pnl_date.isoformat(),
                total_realized,
                total_unrealized_settle,
                total_unrealized_current,
                total_pnl,
                period_start.isoformat(),
                period_end.isoformat(),
                snapshot_df['trades_in_period'].sum() if 'trades_in_period' in snapshot_df.columns else 0
            ))
            
            # Commit transaction
            cursor.execute("COMMIT")
            conn.close()
            
            logger.info(f"Wrote {len(snapshot_df)} position snapshots plus TOTAL row")
            logger.info(f"P&L Period: {period_start} to {period_end}")
            logger.info(f"Total P&L for period: ${total_pnl:,.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing EOD snapshot: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def _write_empty_snapshot(self, pnl_date: date) -> bool:
        """Write an empty snapshot with just a TOTAL row showing zero P&L."""
        try:
            conn = sqlite3.connect(self.pnl_tracker_db)
            cursor = conn.cursor()
            
            # Delete any existing records for this date
            cursor.execute("""
                DELETE FROM tyu5_eod_pnl_history 
                WHERE snapshot_date = ?
            """, (pnl_date.isoformat(),))
            
            # Insert TOTAL row with zeros
            cursor.execute("""
                INSERT INTO tyu5_eod_pnl_history
                (snapshot_date, symbol, position_quantity, realized_pnl,
                 unrealized_pnl_settle, unrealized_pnl_current, total_daily_pnl,
                 settlement_price, current_price)
                VALUES (?, 'TOTAL', 0, 0, 0, 0, 0, NULL, NULL)
            """, (pnl_date.isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Wrote empty snapshot for {pnl_date} (no positions)")
            return True
            
        except Exception as e:
            logger.error(f"Error writing empty snapshot: {e}")
            return False


async def main():
    """Example usage of EOD snapshot service."""
    service = EODSnapshotService()
    
    # Run monitoring loop
    await service.monitor_for_eod(check_interval=30)


if __name__ == "__main__":
    asyncio.run(main()) 