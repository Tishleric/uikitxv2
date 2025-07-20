"""
Options price file processor.

Handles processing of options price CSV files with proper Bloomberg symbols
and updates the database based on time windows.
"""

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import re

from lib.monitoring.decorators import monitor
from .storage import MarketPriceStorage
from .constants import CHICAGO_TZ, TIME_WINDOWS, FILE_PATTERNS

logger = logging.getLogger(__name__)


class OptionsProcessor:
    """Processes options price files and updates database."""
    
    def __init__(self, storage: MarketPriceStorage):
        """
        Initialize processor with storage instance.
        
        Args:
            storage: MarketPriceStorage instance for database operations
        """
        self.storage = storage
        self.file_pattern = re.compile(FILE_PATTERNS['options'])
        
    @monitor()
    def process_file(self, file_path: Path) -> bool:
        """
        Process a single options price file.
        
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
            logger.info(f"OPTIONS FILE PROCESSING: {file_path.name}")
            logger.info(f"{'='*60}")
            logger.info(f"File timestamp: {file_timestamp}")
            logger.info(f"Window type: {window_type}")
            logger.info(f"Action: {TIME_WINDOWS[window_type]['action']}")
            
            # Read CSV file
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from CSV")
            
            # Validate required columns
            required_columns = ['SYMBOL', TIME_WINDOWS[window_type]['column']]
            optional_columns = ['EXPIRE_DT', 'MONEYNESS']
            
            missing_required = [col for col in required_columns if col not in df.columns]
            if missing_required:
                logger.error(f"Missing required columns: {missing_required}")
                return False
                
            # Check which optional columns are available
            available_optional = [col for col in optional_columns if col in df.columns]
            logger.info(f"Available optional columns: {available_optional}")
                
            # Record file processing start
            tracker_id = self.storage.record_file_processing(
                filename=file_path.name,
                file_type='options',
                file_timestamp=file_timestamp,
                window_type=window_type,
                total_rows=len(df)
            )
            
            # Process rows based on window type
            if window_type == '2pm':
                success = self._process_2pm_file(df, file_timestamp.date(), tracker_id, available_optional)
            else:  # 4pm
                success = self._process_4pm_file(df, file_timestamp.date(), tracker_id, available_optional)
                
            if success:
                self.storage.complete_file_processing(tracker_id)
                logger.info(f"Successfully processed {file_path.name}")
            else:
                logger.error(f"Failed to process {file_path.name}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing options file {file_path}: {e}", exc_info=True)
            return False
    
    def _parse_filename(self, filename: str) -> Tuple[Optional[datetime], Optional[str]]:
        """
        Parse filename to extract timestamp and determine time window.
        
        Args:
            filename: Name of the file (e.g., "Options_20250712_1400.csv")
            
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
    def _process_2pm_file(self, df: pd.DataFrame, trade_date: date, tracker_id: int, 
                         optional_columns: list) -> bool:
        """
        Process 2pm file - update current prices.
        
        Args:
            df: DataFrame with price data
            trade_date: Trading date from filename
            tracker_id: File tracker record ID
            optional_columns: List of available optional columns
            
        Returns:
            True if successful
        """
        price_column = TIME_WINDOWS['2pm']['column']  # PX_LAST
        processed_count = 0
        error_count = 0
        
        logger.info(f"Processing 2pm file: Updating current prices for {trade_date}")
        
        for idx, row in df.iterrows():
            try:
                # Get symbol (already in Bloomberg format)
                symbol = str(row['SYMBOL']).strip()
                if not symbol:
                    continue
                
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
                
                # Get optional fields
                expire_dt = None
                moneyness = None
                
                if 'EXPIRE_DT' in optional_columns:
                    expire_dt_value = row.get('EXPIRE_DT')
                    if pd.notna(expire_dt_value):
                        try:
                            # Try different date formats
                            date_str = str(expire_dt_value).strip()
                            # Try M/D/YYYY format first (e.g., "7/14/2025")
                            if '/' in date_str:
                                expire_dt = datetime.strptime(date_str, "%m/%d/%Y").date()
                            # Fall back to YYYYMMDD format
                            else:
                                expire_dt = datetime.strptime(date_str, "%Y%m%d").date()
                        except ValueError:
                            logger.debug(f"Invalid expire date for {symbol}: {expire_dt_value}")
                
                if 'MONEYNESS' in optional_columns:
                    moneyness_value = row.get('MONEYNESS')
                    if pd.notna(moneyness_value):
                        try:
                            # Handle text moneyness values
                            moneyness_str = str(moneyness_value).strip().upper()
                            if moneyness_str == 'ITM':
                                moneyness = 1.0  # In the money
                            elif moneyness_str == 'OTM':
                                moneyness = -1.0  # Out of the money
                            elif moneyness_str == 'ATM':
                                moneyness = 0.0  # At the money
                            else:
                                # Try to parse as float
                                moneyness = float(moneyness_value)
                        except (ValueError, TypeError):
                            logger.debug(f"Invalid moneyness for {symbol}: {moneyness_value}")
                
                # Update Flash_Close price
                self.storage.update_options_flash_close(
                    trade_date=trade_date,
                    symbol=symbol,
                    price=price,
                    expire_dt=expire_dt,
                    moneyness=moneyness
                )
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
        
        logger.info(f"2pm processing complete: {processed_count} prices updated, {error_count} errors out of {len(df)} total rows")
        # Only return success if we processed all valid rows (some rows might be legitimately skipped for no price)
        skipped_count = len(df) - processed_count - error_count
        return error_count == 0 and processed_count > 0
    
    @monitor()
    def _process_4pm_file(self, df: pd.DataFrame, file_date: date, tracker_id: int,
                         optional_columns: list) -> bool:
        """
        Process 4pm file - insert prior closes for next trading day.
        
        Args:
            df: DataFrame with price data
            file_date: Date from filename
            tracker_id: File tracker record ID
            optional_columns: List of available optional columns
            
        Returns:
            True if successful
        """
        price_column = TIME_WINDOWS['4pm']['column']  # PX_SETTLE
        processed_count = 0
        error_count = 0
        
        # Calculate next trading day (simplified - just add 1 day)
        # In production, you'd use a proper trading calendar
        next_trade_date = file_date + timedelta(days=1)
        
        logger.info(f"Processing 4pm file: Inserting prior closes for {next_trade_date}")
        
        for idx, row in df.iterrows():
            try:
                # Get symbol (already in Bloomberg format)
                symbol = str(row['SYMBOL']).strip()
                if not symbol:
                    continue
                
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
                
                # Get optional fields
                expire_dt = None
                moneyness = None
                
                if 'EXPIRE_DT' in optional_columns:
                    expire_dt_value = row.get('EXPIRE_DT')
                    if pd.notna(expire_dt_value):
                        try:
                            # Parse date - assuming YYYYMMDD format
                            expire_dt = datetime.strptime(str(expire_dt_value), "%Y%m%d").date()
                        except ValueError:
                            logger.debug(f"Invalid expire date for {symbol}: {expire_dt_value}")
                
                if 'MONEYNESS' in optional_columns:
                    moneyness_value = row.get('MONEYNESS')
                    if pd.notna(moneyness_value):
                        try:
                            moneyness = float(moneyness_value)
                        except (ValueError, TypeError):
                            logger.debug(f"Invalid moneyness for {symbol}: {moneyness_value}")
                
                # Insert prior close for next day
                self.storage.insert_options_prior_close(
                    trade_date=next_trade_date,
                    symbol=symbol,
                    prior_close=price,
                    expire_dt=expire_dt,
                    moneyness=moneyness
                )
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
        
        logger.info(f"4pm processing complete: {processed_count} prior closes inserted, {error_count} errors out of {len(df)} total rows")
        # Only return success if we processed all valid rows (some rows might be legitimately skipped for no price)
        skipped_count = len(df) - processed_count - error_count
        return error_count == 0 and processed_count > 0
    
    @monitor()
    def get_processing_stats(self) -> dict:
        """Get processing statistics."""
        return {
            'file_pattern': FILE_PATTERNS['options'],
            'symbol_format': 'Bloomberg (no suffix needed)',
            'supported_windows': ['2pm', '4pm'],
            'optional_fields': ['EXPIRE_DT', 'MONEYNESS']
        } 