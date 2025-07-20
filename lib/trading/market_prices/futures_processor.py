"""
Futures price file processor.

Handles processing of futures price CSV files, adding Bloomberg U5 suffix
and updating the database based on time windows.
"""

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import re

from lib.monitoring.decorators import monitor
from .storage import MarketPriceStorage
from .constants import CHICAGO_TZ, TIME_WINDOWS, FILE_PATTERNS, FUTURES_SUFFIX

logger = logging.getLogger(__name__)


class FuturesProcessor:
    """Processes futures price files and updates database."""
    
    def __init__(self, storage: MarketPriceStorage):
        """
        Initialize processor with storage instance.
        
        Args:
            storage: MarketPriceStorage instance for database operations
        """
        self.storage = storage
        self.file_pattern = re.compile(FILE_PATTERNS['futures'])
        
    @monitor()
    def process_file(self, file_path: Path) -> bool:
        """
        Process a single futures price file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            True if successfully processed, False otherwise
        """
        try:
            # Extract timestamp and validate window
            file_timestamp, window_type = self._parse_filename(file_path.name)
            if not file_timestamp or not window_type:
                logger.warning(f"Skipping file {file_path.name} - invalid timestamp or window")
                return False
                
            # Check if already processed
            if self.storage.is_file_processed(file_path.name):
                logger.info(f"File {file_path.name} already processed, skipping")
                return True
                
            # Skip 3pm files
            if window_type == '3pm':
                logger.info(f"Skipping 3pm file: {file_path.name}")
                return True
                
            logger.info(f"{'='*60}")
            logger.info(f"FUTURES FILE PROCESSING: {file_path.name}")
            logger.info(f"{'='*60}")
            logger.info(f"File timestamp: {file_timestamp}")
            logger.info(f"Window type: {window_type}")
            logger.info(f"Action: {TIME_WINDOWS[window_type]['action']}")
            
            # Read CSV file
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from CSV")
            
            # Validate required columns - futures use decimal columns
            price_column = TIME_WINDOWS[window_type].get('futures_column', TIME_WINDOWS[window_type]['column'])
            required_columns = ['SYMBOL', price_column]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
                
            # Record file processing start
            tracker_id = self.storage.record_file_processing(
                filename=file_path.name,
                file_type='futures',
                file_timestamp=file_timestamp,
                window_type=window_type,
                total_rows=len(df)
            )
            
            # Process rows based on window type
            if window_type == '2pm':
                success = self._process_2pm_file(df, file_timestamp.date(), tracker_id)
            else:  # 4pm
                success = self._process_4pm_file(df, file_timestamp.date(), tracker_id)
                
            if success:
                self.storage.complete_file_processing(tracker_id)
                logger.info(f"Successfully processed {file_path.name}")
            else:
                logger.error(f"Failed to process {file_path.name}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing futures file {file_path}: {e}", exc_info=True)
            return False
    
    def _parse_filename(self, filename: str) -> Tuple[Optional[datetime], Optional[str]]:
        """
        Parse filename to extract timestamp and determine time window.
        
        Args:
            filename: Name of the file (e.g., "Futures_20250712_1400.csv")
            
        Returns:
            Tuple of (timestamp, window_type) or (None, None) if parsing fails
        """
        match = self.file_pattern.match(filename)
        if not match:
            return None, None
            
        date_str, time_str = match.groups()
        
        try:
            # Parse datetime
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M")
            # Localize to Chicago time
            dt_chicago = CHICAGO_TZ.localize(dt)
            
            # Determine window type
            file_time = dt.time()
            for window_name, window_config in TIME_WINDOWS.items():
                if window_config['start'] <= file_time <= window_config['end']:
                    return dt_chicago, window_name
                    
            # Not in any valid window
            return dt_chicago, None
            
        except ValueError as e:
            logger.error(f"Failed to parse timestamp from {filename}: {e}")
            return None, None
    
    @monitor()
    def _process_2pm_file(self, df: pd.DataFrame, trade_date: date, tracker_id: int) -> bool:
        """
        Process 2pm file - update current prices.
        
        Args:
            df: DataFrame with price data
            trade_date: Trading date from filename
            tracker_id: File tracker record ID
            
        Returns:
            True if successful
        """
        price_column = TIME_WINDOWS['2pm'].get('futures_column', TIME_WINDOWS['2pm']['column'])  # PX_LAST_DEC
        processed_count = 0
        error_count = 0
        
        logger.info(f"Processing 2pm file: Updating current prices for {trade_date}")
        
        for idx, row in df.iterrows():
            try:
                # Get symbol and add U5 suffix
                symbol = str(row['SYMBOL']).strip()
                if not symbol:
                    continue
                    
                # Add Bloomberg suffix and Comdty
                bloomberg_symbol = f"{symbol}{FUTURES_SUFFIX} Comdty"
                
                # Get price
                price_value = row.get(price_column)
                if pd.isna(price_value):
                    logger.debug(f"Skipping {symbol} - no {price_column} value")
                    continue
                    
                try:
                    price = float(price_value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid price for {symbol}: {price_value}")
                    error_count += 1
                    continue
                
                # Update Flash_Close price
                self.storage.update_futures_flash_close(trade_date, bloomberg_symbol, price)
                processed_count += 1
                
                if processed_count % 10 == 0:
                    logger.debug(f"Processed {processed_count} prices...")
                    
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                error_count += 1
                
            # Update progress
            if (idx + 1) % 10 == 0:
                self.storage.update_file_processing_progress(tracker_id, idx + 1)
        
        # Final progress update
        self.storage.update_file_processing_progress(tracker_id, len(df))
        
        logger.info(f"2pm processing complete: {processed_count} prices updated, {error_count} errors")
        return error_count == 0 or processed_count > 0
    
    @monitor()
    def _process_4pm_file(self, df: pd.DataFrame, file_date: date, tracker_id: int) -> bool:
        """
        Process 4pm file - insert prior closes for next trading day.
        
        Args:
            df: DataFrame with price data
            file_date: Date from filename
            tracker_id: File tracker record ID
            
        Returns:
            True if successful
        """
        price_column = TIME_WINDOWS['4pm'].get('futures_column', TIME_WINDOWS['4pm']['column'])  # PX_SETTLE_DEC
        processed_count = 0
        error_count = 0
        
        # Calculate next trading day (simplified - just add 1 day)
        # In production, you'd use a proper trading calendar
        next_trade_date = file_date + timedelta(days=1)
        
        logger.info(f"Processing 4pm file: Inserting prior closes for {next_trade_date}")
        
        for idx, row in df.iterrows():
            try:
                # Get symbol and add U5 suffix
                symbol = str(row['SYMBOL']).strip()
                if not symbol:
                    continue
                    
                # Add Bloomberg suffix and Comdty
                bloomberg_symbol = f"{symbol}{FUTURES_SUFFIX} Comdty"
                
                # Get price
                price_value = row.get(price_column)
                if pd.isna(price_value):
                    logger.debug(f"Skipping {symbol} - no {price_column} value")
                    continue
                    
                try:
                    price = float(price_value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid price for {symbol}: {price_value}")
                    error_count += 1
                    continue
                
                # Insert prior close for next day
                self.storage.insert_futures_prior_close(next_trade_date, bloomberg_symbol, price)
                processed_count += 1
                
                if processed_count % 10 == 0:
                    logger.debug(f"Processed {processed_count} prices...")
                    
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                error_count += 1
                
            # Update progress
            if (idx + 1) % 10 == 0:
                self.storage.update_file_processing_progress(tracker_id, idx + 1)
        
        # Final progress update
        self.storage.update_file_processing_progress(tracker_id, len(df))
        
        logger.info(f"4pm processing complete: {processed_count} prior closes inserted, {error_count} errors")
        return error_count == 0 or processed_count > 0
    
    @monitor()
    def get_processing_stats(self) -> dict:
        """Get processing statistics."""
        return {
            'file_pattern': FILE_PATTERNS['futures'],
            'suffix_added': FUTURES_SUFFIX,
            'supported_windows': ['2pm', '4pm']
        } 