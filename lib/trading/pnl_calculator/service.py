"""P&L Service orchestrating calculations, storage, and real-time updates.

This service acts as the central coordinator for the P&L tracking system,
handling trade processing, market price updates, and P&L calculations.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import pandas as pd
import pytz

from .calculator import PnLCalculator
from .storage import PnLStorage
from .models import Trade

# Set up module logger
logger = logging.getLogger(__name__)

# Import monitor decorator if available
try:
    from lib.monitoring.decorators import monitor
except ImportError:
    # Fallback if monitoring is not available
    def monitor():
        def decorator(func):
            return func
        return decorator


class PnLService:
    """Central service for P&L calculation and tracking."""
    
    def __init__(self, storage: Optional[PnLStorage] = None):
        """Initialize the P&L service.
        
        Args:
            storage: Storage instance (creates default if not provided)
        """
        self.storage = storage or PnLStorage()
        self.calculators: Dict[date, PnLCalculator] = {}  # Calculator per trade date
        self._processed_files: Set[str] = set()
        
        # Time zones
        self.chicago_tz = pytz.timezone('America/Chicago')
        self.est_tz = pytz.timezone('America/New_York')
        
    def _get_calculator_for_date(self, trade_date: date) -> PnLCalculator:
        """Get or create calculator for a specific trade date.
        
        Args:
            trade_date: Date to get calculator for
            
        Returns:
            PnLCalculator instance for that date
        """
        if trade_date not in self.calculators:
            self.calculators[trade_date] = PnLCalculator()
            logger.info(f"Created new calculator for trade date {trade_date}")
            
        return self.calculators[trade_date]
        
    @monitor()
    def process_trade_file(self, file_path: str) -> None:
        """Process a trade CSV file.
        
        Args:
            file_path: Path to the trade CSV file
        """
        try:
            # Check if already processed
            if file_path in self._processed_files:
                logger.info(f"File already processed: {file_path}")
                return
                
            logger.info(f"Processing trade file: {file_path}")
            
            # Extract date from filename (trades_YYYYMMDD.csv)
            # IMPORTANT: The trade_date is determined from the FILENAME, not the actual
            # marketTradeTime in the CSV. This means all trades in a file will be
            # assigned to the date in the filename, regardless of their actual timestamps.
            # This is by design to group trades by the intended trading day.
            filename = Path(file_path).name
            if filename.startswith('trades_') and filename.endswith('.csv'):
                date_str = filename[7:15]  # Extract YYYYMMDD
                trade_date = datetime.strptime(date_str, '%Y%m%d').date()
            else:
                logger.warning(f"Unexpected filename format: {filename}, using today's date")
                trade_date = date.today()
                
            # Read trades from CSV
            trades_df = pd.read_csv(file_path)
            
            # Save trades to storage with the trading day date
            rows_saved = self.storage.save_processed_trades(trades_df, filename, trade_date)
            logger.info(f"Saved {rows_saved} trades to storage")
            
            # Get calculator for this date
            calc = self._get_calculator_for_date(trade_date)
            
            # Load trades into calculator
            calc.load_trades_from_csv(file_path)
            
            # Get current time in EST for price selection
            now_est = datetime.now(self.est_tz)
            
            # Calculate P&L for each unique instrument
            instruments = trades_df['instrumentName'].unique()
            
            for instrument in instruments:
                # Get market price
                price, price_source = self.storage.get_market_price(instrument, now_est)
                
                if price is None:
                    logger.warning(f"No market price found for {instrument}, using last known or trade price")
                    # Use last trade price as fallback
                    instrument_trades = trades_df[trades_df['instrumentName'] == instrument]
                    if not instrument_trades.empty:
                        price = instrument_trades.iloc[-1]['price']
                        price_source = 'trade_price'
                    else:
                        logger.error(f"No price available for {instrument}")
                        continue
                        
                # Add market close to calculator
                calc.add_market_close(instrument, trade_date, price)
                
            # Calculate daily P&L
            pnl_df = calc.calculate_daily_pnl()
            
            # Save P&L snapshots
            self._save_pnl_snapshots(pnl_df, trade_date, now_est)
            
            # Check if it's EOD (5pm EST or later)
            if now_est.hour >= 17:
                self._save_eod_pnl(pnl_df, trade_date)
                
            # Mark file as processed
            self._processed_files.add(file_path)
            
            # Log file processing
            self.storage.log_file_processing(
                file_path, 'trades', 'completed', 
                rows_processed=len(trades_df)
            )
            
        except Exception as e:
            logger.error(f"Error processing trade file {file_path}: {e}")
            self.storage.log_file_processing(
                file_path, 'trades', 'error',
                error_message=str(e)
            )
            raise
            
    @monitor()
    def process_market_price_file(self, file_path: str) -> None:
        """Process a market price CSV file.
        
        Args:
            file_path: Path to the market price CSV file
        """
        try:
            logger.info(f"Processing market price file: {file_path}")
            
            # Extract timestamp from filename (market_prices_YYYYMMDD_HHMM.csv)
            filename = Path(file_path).name
            if filename.startswith('market_prices_') and filename.endswith('.csv'):
                date_str = filename[14:22]  # YYYYMMDD
                time_str = filename[23:27]  # HHMM
                
                # Create timestamp in EST
                upload_time = datetime.strptime(f"{date_str} {time_str}", '%Y%m%d %H%M')
                upload_time = self.est_tz.localize(upload_time)
            else:
                logger.warning(f"Unexpected filename format: {filename}, using current time")
                upload_time = datetime.now(self.est_tz)
                
            # Read prices
            prices_df = pd.read_csv(file_path)
            
            # Save to storage
            rows_saved = self.storage.save_market_prices(
                prices_df, upload_time, filename
            )
            logger.info(f"Saved {rows_saved} market prices to storage")
            
            # Recalculate P&L for all active dates with new prices
            self._recalculate_all_pnl(upload_time)
            
            # Log file processing
            self.storage.log_file_processing(
                file_path, 'market_prices', 'completed',
                rows_processed=len(prices_df)
            )
            
        except Exception as e:
            logger.error(f"Error processing market price file {file_path}: {e}")
            self.storage.log_file_processing(
                file_path, 'market_prices', 'error',
                error_message=str(e)
            )
            raise
            
    def _recalculate_all_pnl(self, as_of: datetime) -> None:
        """Recalculate P&L for all active trade dates with new market prices.
        
        Args:
            as_of: Timestamp to use for price selection
        """
        for trade_date, calc in self.calculators.items():
            # Skip if no trades
            if not calc.trades:
                continue
                
            # Get all unique instruments
            instruments = set(trade.symbol for trade in calc.trades)
            
            # Update market prices
            for instrument in instruments:
                price, price_source = self.storage.get_market_price(instrument, as_of)
                if price is not None:
                    calc.add_market_close(instrument, trade_date, price)
                    
            # Recalculate P&L
            pnl_df = calc.calculate_daily_pnl()
            
            # Save updated snapshots
            self._save_pnl_snapshots(pnl_df, trade_date, as_of)
            
            # Check if EOD
            if as_of.hour >= 17:
                self._save_eod_pnl(pnl_df, trade_date)
                
    def _save_pnl_snapshots(self, pnl_df: pd.DataFrame, trade_date: date, 
                           snapshot_time: datetime) -> None:
        """Save P&L snapshots to storage.
        
        Args:
            pnl_df: DataFrame with P&L data
            trade_date: Trade date
            snapshot_time: Time of snapshot
        """
        if pnl_df.empty:
            return
            
        # Group by symbol to get latest position
        for symbol in pnl_df['symbol'].unique():
            symbol_data = pnl_df[pnl_df['symbol'] == symbol].iloc[-1]
            
            snapshot = {
                'snapshot_timestamp': snapshot_time,
                'instrument_name': symbol,
                'position': int(symbol_data['position']),
                'avg_cost': float(symbol_data['avg_cost']) if pd.notna(symbol_data['avg_cost']) else 0.0,
                'market_price': float(symbol_data['market_close']) if pd.notna(symbol_data['market_close']) else 0.0,
                'price_source': 'px_settle',  # Will be updated based on time logic
                'price_upload_time': snapshot_time,
                'realized_pnl': float(symbol_data['realized_pnl']),
                'unrealized_pnl': float(symbol_data['unrealized_pnl']),
                'total_pnl': float(symbol_data['total_daily_pnl'])
            }
            
            self.storage.save_pnl_snapshot(snapshot)
            
    def _save_eod_pnl(self, pnl_df: pd.DataFrame, trade_date: date) -> None:
        """Save end-of-day P&L summary.
        
        Args:
            pnl_df: DataFrame with P&L data
            trade_date: Trade date (from filename)
        """
        if pnl_df.empty:
            return
            
        eod_data = []
        
        # Get unique dates from the P&L data
        unique_dates = pnl_df['date'].unique() if 'date' in pnl_df.columns else []
        
        for calc_date in unique_dates:
            # Filter data for this specific date
            date_df = pnl_df[pnl_df['date'] == calc_date]
            
            # Group by symbol for this date
            for symbol in date_df['symbol'].unique():
                symbol_df = date_df[date_df['symbol'] == symbol]
                
                # Get opening and closing positions
                opening_pos = 0  # Will be loaded from previous day in production
                closing_pos = int(symbol_df.iloc[-1]['position'])
                
                # Get average cost from the calculator
                # The avg_cost from PnLCalculator is the weighted average price
                avg_cost = float(symbol_df.iloc[-1]['avg_cost']) if pd.notna(symbol_df.iloc[-1]['avg_cost']) else 0.0
                
                # For long positions, avg_cost is the average buy price
                # For short positions, avg_cost is the average sell price
                avg_buy = avg_cost if closing_pos > 0 and avg_cost > 0 else None
                avg_sell = avg_cost if closing_pos < 0 and avg_cost > 0 else None
                    
                # Get actual trade count from the database
                conn = self.storage._get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as trade_count 
                    FROM processed_trades 
                    WHERE instrument_name = ? AND DATE(trade_timestamp) = ?
                """, (symbol, str(calc_date)))
                result = cursor.fetchone()
                actual_trade_count = result['trade_count'] if result else 0
                conn.close()
                    
                eod_record = {
                    'trade_date': calc_date,  # Use the actual calculation date
                    'instrument_name': symbol,
                    'opening_position': opening_pos,
                    'closing_position': closing_pos,
                    'trades_count': actual_trade_count,  # Use actual trade count from DB
                    'realized_pnl': float(symbol_df['realized_pnl'].sum()),
                    'unrealized_pnl': float(symbol_df.iloc[-1]['unrealized_pnl']),
                    'total_pnl': float(symbol_df['total_daily_pnl'].sum()),
                    'avg_buy_price': avg_buy,
                    'avg_sell_price': avg_sell
                }
                
                eod_data.append(eod_record)
        
        if eod_data:
            self.storage.save_eod_pnl(eod_data)
        logger.info(f"Saved EOD P&L for {len(eod_data)} instruments on {trade_date}")
        
    @monitor()
    def get_live_pnl(self, trade_date: Optional[date] = None) -> pd.DataFrame:
        """Get current live P&L.
        
        Args:
            trade_date: Date to get P&L for (defaults to today)
            
        Returns:
            DataFrame with current P&L data
        """
        if trade_date is None:
            trade_date = date.today()
            
        calc = self._get_calculator_for_date(trade_date)
        
        if not calc.trades:
            return pd.DataFrame()
            
        return calc.calculate_daily_pnl()
        
    @monitor()
    def get_position_summary(self, trade_date: Optional[date] = None) -> pd.DataFrame:
        """Get current position summary.
        
        Args:
            trade_date: Date to get positions for (defaults to today)
            
        Returns:
            DataFrame with position summary
        """
        if trade_date is None:
            trade_date = date.today()
            
        calc = self._get_calculator_for_date(trade_date)
        
        if not calc.trades:
            return pd.DataFrame()
            
        return calc.get_position_summary(as_of_date=trade_date) 