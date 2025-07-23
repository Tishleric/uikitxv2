"""
Settlement Price Loader

Loads settlement prices (px_settle) from market_prices.db for use in 
settlement-aware P&L calculations. Handles missing prices explicitly.
"""

import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import pandas as pd

from .settlement_constants import CHICAGO_TZ

logger = logging.getLogger(__name__)


class SettlementPriceLoader:
    """Loads settlement prices from market database."""
    
    def __init__(self, market_db_path: str = "data/output/market_prices/market_prices.db"):
        """
        Initialize the settlement price loader.
        
        Args:
            market_db_path: Path to market prices database
        """
        self.market_db_path = market_db_path
        self._price_cache = {}
        
    def load_settlement_prices_for_period(self, 
                                        period_start: datetime,
                                        period_end: datetime,
                                        symbols: List[str]) -> Dict[date, Dict[str, float]]:
        """
        Load all settlement prices needed for P&L calculation over a period.
        
        Args:
            period_start: Start of P&L period (typically 2pm yesterday)
            period_end: End of P&L period (typically 2pm today)
            symbols: List of symbols to get prices for
            
        Returns:
            Dict mapping settlement date to symbol prices
            Missing prices are NOT included - caller must handle
        """
        # Determine which settlement dates we need
        dates_needed = self._get_settlement_dates_needed(period_start, period_end)
        
        logger.info(f"Loading settlement prices for {len(symbols)} symbols, "
                   f"dates: {[d.isoformat() for d in dates_needed]}")
        
        settlement_prices = {}
        missing_prices = []
        
        for settle_date in dates_needed:
            date_prices, date_missing = self._load_prices_for_date(settle_date, symbols)
            if date_prices:
                settlement_prices[settle_date] = date_prices
            missing_prices.extend(date_missing)
        
        # Report missing prices
        if missing_prices:
            self._report_missing_prices(missing_prices)
        
        return settlement_prices
    
    def _get_settlement_dates_needed(self, 
                                   period_start: datetime, 
                                   period_end: datetime) -> List[date]:
        """
        Determine which settlement dates are needed for the period.
        
        For positions spanning multiple days, we need settlement prices
        for each day the position crosses 2pm.
        """
        dates = []
        
        # Start date settlement (if period starts before 2pm on that day)
        start_date = period_start.date()
        if period_start.hour < 14:  # Before 2pm
            dates.append(start_date)
        
        # All intermediate dates
        current_date = start_date + timedelta(days=1)
        end_date = period_end.date()
        
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        
        return dates
    
    def _load_prices_for_date(self, 
                            settle_date: date, 
                            symbols: List[str]) -> tuple[Dict[str, float], List[Dict]]:
        """
        Load settlement prices for a specific date.
        
        Returns:
            Tuple of (prices dict, missing prices list)
        """
        if not Path(self.market_db_path).exists():
            logger.error(f"Market prices database not found: {self.market_db_path}")
            return {}, [{'date': settle_date, 'symbols': symbols, 
                        'reason': 'Database not found'}]
        
        prices = {}
        missing = []
        
        try:
            conn = sqlite3.connect(self.market_db_path)
            
            # Query both futures and options tables
            # Settlement price is stored as 'prior_close' 
            for symbol in symbols:
                # Handle Bloomberg suffix - TYU5 might be stored as "TYU5 Comdty"
                bloomberg_symbol = f"{symbol} Comdty" if len(symbol) <= 5 else symbol
                # Try futures first
                cursor = conn.execute("""
                    SELECT prior_close 
                    FROM futures_prices 
                    WHERE symbol = ? AND trade_date = ?
                """, (bloomberg_symbol, settle_date.isoformat()))
                
                result = cursor.fetchone()
                if result and result[0] is not None:
                    prices[symbol] = float(result[0])
                    continue
                
                # Try options if not found in futures
                cursor = conn.execute("""
                    SELECT prior_close 
                    FROM options_prices 
                    WHERE symbol = ? AND trade_date = ?
                """, (symbol, settle_date.isoformat()))
                
                result = cursor.fetchone()
                if result and result[0] is not None:
                    prices[symbol] = float(result[0])
                else:
                    # Price not found
                    missing.append({
                        'date': settle_date,
                        'symbol': symbol,
                        'reason': 'No settlement price in database'
                    })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error loading settlement prices: {e}")
            missing.append({
                'date': settle_date,
                'symbols': symbols,
                'reason': f'Database error: {str(e)}'
            })
        
        return prices, missing
    
    def _report_missing_prices(self, missing_prices: List[Dict]):
        """
        Report missing settlement prices.
        
        This is critical for reconciliation - we do NOT want to silently
        use default values or skip calculations.
        """
        logger.error(f"MISSING SETTLEMENT PRICES: {len(missing_prices)} issues found")
        
        # Group by date for clearer reporting
        by_date = {}
        for miss in missing_prices:
            date_key = miss['date']
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(miss)
        
        for date_key, issues in by_date.items():
            logger.error(f"  Date {date_key}:")
            for issue in issues:
                if 'symbol' in issue:
                    logger.error(f"    - {issue['symbol']}: {issue['reason']}")
                else:
                    logger.error(f"    - Multiple symbols: {issue['reason']}")
    
    def get_latest_settlement_price(self, symbol: str) -> Optional[float]:
        """
        Get the most recent settlement price for a symbol.
        
        Useful for current position valuation.
        """
        if not Path(self.market_db_path).exists():
            logger.error(f"Market prices database not found: {self.market_db_path}")
            return None
        
        try:
            conn = sqlite3.connect(self.market_db_path)
            
            # Try futures
            # Handle Bloomberg suffix
            bloomberg_symbol = f"{symbol} Comdty" if len(symbol) <= 5 else symbol
            
            cursor = conn.execute("""
                SELECT prior_close, trade_date 
                FROM futures_prices 
                WHERE symbol = ? AND prior_close IS NOT NULL
                ORDER BY trade_date DESC 
                LIMIT 1
            """, (bloomberg_symbol,))
            
            result = cursor.fetchone()
            if result:
                price, price_date = result
                logger.debug(f"Latest settlement for {symbol}: ${price} on {price_date}")
                conn.close()
                return float(price)
            
            # Try options
            cursor = conn.execute("""
                SELECT prior_close, trade_date 
                FROM options_prices 
                WHERE symbol = ? AND prior_close IS NOT NULL
                ORDER BY trade_date DESC 
                LIMIT 1
            """, (symbol,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                price, price_date = result
                logger.debug(f"Latest settlement for {symbol}: ${price} on {price_date}")
                return float(price)
            
            logger.warning(f"No settlement price found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest settlement price: {e}")
            return None 