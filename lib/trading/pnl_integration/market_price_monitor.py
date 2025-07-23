"""
Market Price Monitor for EOD P&L

This module monitors the market_prices.db for 4pm settlement price updates
and determines when the batch is complete enough to trigger EOD calculations.
"""

import logging
import sqlite3
from datetime import datetime, timedelta, time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd

from lib.monitoring.decorators import monitor
from .settlement_constants import CHICAGO_TZ, SETTLE_WINDOW_START, SETTLE_WINDOW_END

logger = logging.getLogger(__name__)


class MarketPriceMonitor:
    """Monitor market prices database for 4pm settlement price updates."""
    
    def __init__(self, 
                 market_prices_db: str = "data/output/market_prices/market_prices.db",
                 completion_threshold: float = 0.95):
        """
        Initialize the market price monitor.
        
        Args:
            market_prices_db: Path to market prices database
            completion_threshold: Percentage of symbols that must be updated (0.95 = 95%)
        """
        self.market_prices_db = market_prices_db
        self.completion_threshold = completion_threshold
        self.last_check_time = None
        self.pending_symbols: Set[str] = set()
        self.updated_symbols: Set[str] = set()
        self._baseline_symbols: Set[str] = set()
        
    @monitor()
    def detect_4pm_batch_start(self) -> bool:
        """
        Detect when 4pm price updates begin arriving.
        
        Returns:
            True if 4pm updates have started
        """
        try:
            current_time = datetime.now(CHICAGO_TZ)
            current_hour = current_time.hour
            
            # Only check during/after 4pm window
            if current_hour < 15:  # Before 3pm
                return False
            
            conn = sqlite3.connect(self.market_prices_db)
            cursor = conn.cursor()
            
            # Look for recent prior_close updates (4pm prices)
            window_start = current_time - timedelta(minutes=30)
            
            # Check futures
            cursor.execute("""
                SELECT COUNT(*) as update_count
                FROM futures_prices
                WHERE prior_close IS NOT NULL
                  AND last_updated > ?
            """, (window_start,))
            
            futures_count = cursor.fetchone()[0]
            
            # Check options
            cursor.execute("""
                SELECT COUNT(*) as update_count
                FROM options_prices
                WHERE prior_close IS NOT NULL
                  AND last_updated > ?
            """, (window_start,))
            
            options_count = cursor.fetchone()[0]
            
            conn.close()
            
            # If we see any updates, batch has started
            batch_started = (futures_count + options_count) > 0
            
            if batch_started and not self.pending_symbols:
                # Initialize tracking on first detection
                self._initialize_symbol_tracking()
                logger.info(f"Detected 4pm batch start with {futures_count} futures, {options_count} options")
            
            return batch_started
            
        except Exception as e:
            logger.error(f"Error detecting 4pm batch start: {e}")
            return False
    
    def _initialize_symbol_tracking(self):
        """Initialize the set of symbols we're tracking for updates."""
        try:
            conn = sqlite3.connect(self.market_prices_db)
            
            # Get all active symbols (those with Flash_Close from 2pm)
            futures_df = pd.read_sql_query("""
                SELECT DISTINCT symbol 
                FROM futures_prices
                WHERE Flash_Close IS NOT NULL
                  AND trade_date = (SELECT MAX(trade_date) FROM futures_prices)
            """, conn)
            
            options_df = pd.read_sql_query("""
                SELECT DISTINCT symbol
                FROM options_prices
                WHERE Flash_Close IS NOT NULL
                  AND trade_date = (SELECT MAX(trade_date) FROM options_prices)
            """, conn)
            
            conn.close()
            
            # Combine all symbols
            all_symbols = set(futures_df['symbol'].tolist() + options_df['symbol'].tolist())
            
            self._baseline_symbols = all_symbols
            self.pending_symbols = all_symbols.copy()
            self.updated_symbols = set()
            
            logger.info(f"Tracking {len(self.pending_symbols)} symbols for 4pm updates")
            
        except Exception as e:
            logger.error(f"Error initializing symbol tracking: {e}")
    
    @monitor()
    def track_symbol_updates(self) -> Dict[str, bool]:
        """
        Track which symbols have received 4pm prices.
        
        Returns:
            Dict mapping symbol to update status
        """
        if not self.pending_symbols:
            return {}
        
        try:
            conn = sqlite3.connect(self.market_prices_db)
            current_time = datetime.now()
            
            # Check for updates since last check
            check_window = self.last_check_time or (current_time - timedelta(minutes=30))
            
            # Get recently updated futures
            futures_df = pd.read_sql_query("""
                SELECT symbol, prior_close, last_updated
                FROM futures_prices
                WHERE prior_close IS NOT NULL
                  AND last_updated > ?
                  AND trade_date = (SELECT MAX(trade_date) FROM futures_prices)
            """, conn, params=(check_window,))
            
            # Get recently updated options
            options_df = pd.read_sql_query("""
                SELECT symbol, prior_close, last_updated
                FROM options_prices
                WHERE prior_close IS NOT NULL
                  AND last_updated > ?
                  AND trade_date = (SELECT MAX(trade_date) FROM options_prices)
            """, conn, params=(check_window,))
            
            conn.close()
            
            # Track updates
            newly_updated = set()
            
            for _, row in pd.concat([futures_df, options_df]).iterrows():
                symbol = row['symbol']
                if symbol in self.pending_symbols:
                    self.pending_symbols.remove(symbol)
                    self.updated_symbols.add(symbol)
                    newly_updated.add(symbol)
            
            self.last_check_time = current_time
            
            # Return status for all baseline symbols
            status = {}
            for symbol in self._baseline_symbols:
                status[symbol] = symbol in self.updated_symbols
            
            if newly_updated:
                logger.info(f"Detected {len(newly_updated)} new symbol updates. "
                          f"Total: {len(self.updated_symbols)}/{len(self._baseline_symbols)}")
            
            return status
            
        except Exception as e:
            logger.error(f"Error tracking symbol updates: {e}")
            return {}
    
    @monitor()
    def is_batch_complete(self, use_threshold: bool = True) -> bool:
        """
        Determine if enough symbols have been updated to proceed with EOD.
        
        Args:
            use_threshold: If True, use completion threshold. If False, require 100%.
            
        Returns:
            True if batch is sufficiently complete
        """
        if not self._baseline_symbols:
            return False
        
        completion_ratio = len(self.updated_symbols) / len(self._baseline_symbols)
        
        if use_threshold:
            is_complete = completion_ratio >= self.completion_threshold
        else:
            is_complete = completion_ratio >= 1.0
        
        if is_complete:
            logger.info(f"Batch complete: {len(self.updated_symbols)}/{len(self._baseline_symbols)} "
                      f"symbols updated ({completion_ratio:.1%})")
        
        return is_complete
    
    def get_missing_symbols(self) -> List[str]:
        """Get list of symbols still awaiting 4pm prices."""
        return sorted(list(self.pending_symbols))
    
    def get_completion_stats(self) -> Dict[str, any]:
        """Get detailed statistics about the current update batch."""
        total = len(self._baseline_symbols)
        updated = len(self.updated_symbols)
        pending = len(self.pending_symbols)
        
        return {
            'total_symbols': total,
            'updated_symbols': updated,
            'pending_symbols': pending,
            'completion_ratio': updated / total if total > 0 else 0,
            'missing_symbols': self.get_missing_symbols()[:10],  # First 10 missing
            'is_complete': self.is_batch_complete()
        }
    
    def reset_tracking(self):
        """Reset tracking state for next day."""
        self.pending_symbols.clear()
        self.updated_symbols.clear()
        self._baseline_symbols.clear()
        self.last_check_time = None
        logger.info("Reset symbol tracking for next trading day") 