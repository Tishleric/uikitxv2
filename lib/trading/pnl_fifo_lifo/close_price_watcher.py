"""
Close Price File Watcher for PnL System

Purpose: Monitor Trade Control directories for close price CSV files and update trades.db
Handles both futures and options files with new format
"""

import sqlite3
import pandas as pd
import logging
import time
import re
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
import pytz
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from .data_manager import roll_2pm_prices, roll_4pm_prices, perform_eod_settlement
from .config import CLOSE_PRICE_WATCHER, FUTURES_SYMBOLS

logger = logging.getLogger(__name__)

# Chicago timezone for all time operations
CHICAGO_TZ = pytz.timezone('America/Chicago')


class DailyCSVTracker:
    """Tracks CSV files received per trading day"""
    
    def __init__(self):
        self.daily_files = {}  # {date: {14: True, 15: True, 16: True}}
        self.expected_hours = [14, 15, 16]  # 2pm, 3pm, 4pm
        self.roll_4pm_triggered = set()  # Track dates where 4pm roll was triggered
        self._lock = threading.Lock()
        
    def add_file(self, date_str: str, hour: int) -> dict:
        """Add a file and return status"""
        with self._lock:
            if date_str not in self.daily_files:
                self.daily_files[date_str] = {}
            
            self.daily_files[date_str][hour] = True
            
            return {
                'received_count': len(self.daily_files[date_str]),
                'is_complete': self._is_day_complete(date_str),
                'missing_hours': self._get_missing_hours(date_str)
            }
    
    def _is_day_complete(self, date_str: str) -> bool:
        """Check if we've received all expected files"""
        if date_str not in self.daily_files:
            return False
        
        received = self.daily_files[date_str]
        return all(hour in received for hour in self.expected_hours)
    
    def _get_missing_hours(self, date_str: str) -> list:
        """Get list of missing hours"""
        if date_str not in self.daily_files:
            return self.expected_hours
        
        received = self.daily_files[date_str]
        return [h for h in self.expected_hours if h not in received]
    
    def should_trigger_4pm_roll(self, date_str: str) -> Tuple[bool, str]:
        """Determine if we should trigger 4pm roll"""
        with self._lock:
            # Don't trigger if already done
            if date_str in self.roll_4pm_triggered:
                return False, "already_triggered"
            
            now_chicago = datetime.now(CHICAGO_TZ)
            current_hour = now_chicago.hour + now_chicago.minute / 60.0
            
            # Option 1: All files received AND it's 4pm CDT or later
            if self._is_day_complete(date_str) and current_hour >= 16.0:
                return True, "all_files_at_4pm"
            
            # Option 2: It's past 4:30pm CDT and we have at least the 4pm file
            if current_hour >= 16.5:  # 4:30pm
                received = self.daily_files.get(date_str, {})
                if 16 in received:  # Have 4pm file
                    return True, "fallback_at_430pm"
            
            return False, "not_ready"
    
    def mark_4pm_roll_complete(self, date_str: str):
        """Mark that 4pm roll was triggered for this date"""
        with self._lock:
            self.roll_4pm_triggered.add(date_str)


class ClosePriceFileHandler(FileSystemEventHandler):
    """Handle close price CSV files from Trade Control directories"""
    
    def __init__(self, db_path: str, startup_time: float):
        self.db_path = db_path
        self.startup_time = startup_time
        self.daily_tracker = DailyCSVTracker()
        self.processed_files = set()  # Track processed files to avoid duplicates
        self._start_4pm_monitor()
        
    def _ignore_old_file(self, event_path: str) -> bool:
        """Return True if the file existed before the watcher started."""
        try:
            if Path(event_path).stat().st_mtime < self.startup_time:
                logger.debug(f"Ignoring pre-existing file: {Path(event_path).name}")
                return True
        except FileNotFoundError:
            return True # File deleted before we could check, ignore.
        return False
        
    def on_created(self, event):
        """Handle new file creation - skip existing files"""
        if self._ignore_old_file(event.src_path):
            return

        if isinstance(event, FileCreatedEvent) and event.src_path.endswith('.csv'):
            filepath = Path(event.src_path)
            
            # Skip if already processed
            if str(filepath) in self.processed_files:
                return
                
            logger.info(f"New close price file detected: {filepath.name}")
            self._process_file(filepath)
    
    def _start_4pm_monitor(self):
        """Start background thread to monitor for 4pm roll trigger"""
        def monitor_loop():
            while True:
                try:
                    # Check each tracked date
                    now_chicago = datetime.now(CHICAGO_TZ)
                    today_str = now_chicago.strftime('%Y%m%d')
                    
                    should_roll, reason = self.daily_tracker.should_trigger_4pm_roll(today_str)
                    if should_roll:
                        logger.info(f"Triggering 4pm roll for {today_str} - reason: {reason}")
                        self._trigger_4pm_roll_for_date(today_str)
                        self.daily_tracker.mark_4pm_roll_complete(today_str)
                        
                except Exception as e:
                    logger.error(f"Error in 4pm monitor: {e}")
                    
                time.sleep(30)  # Check every 30 seconds
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("Started 4pm roll monitor thread")
    
    def _process_file(self, filepath: Path):
        """Process futures or options file"""
        try:
            # Wait for file to be fully written
            if not self._wait_for_file_ready(filepath):
                logger.warning(f"File not ready after timeout: {filepath.name}")
                return
            
            # Extract date and time from filename
            date_str, hour = self._extract_datetime_from_filename(filepath.name)
            if not date_str or hour is None:
                logger.error(f"Could not extract date/time from filename: {filepath.name}")
                return
            
            # Determine file type and process
            if 'Futures' in str(filepath):
                prices = self._process_futures_file(filepath)
            elif 'Options' in str(filepath):
                prices = self._process_options_file(filepath)
            else:
                logger.warning(f"Unknown file type: {filepath}")
                return
            
            if not prices:
                logger.warning(f"No prices extracted from {filepath.name}")
                return
            
            # Update prices in database
            self._update_prices(prices, date_str, hour)
            
            # Track file
            status = self.daily_tracker.add_file(date_str, hour)
            logger.info(f"Daily status for {date_str}: {status}")
            
            # Mark as processed
            self.processed_files.add(str(filepath))
            
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {e}", exc_info=True)
    
    def _wait_for_file_ready(self, filepath: Path, timeout: int = 10) -> bool:
        """Wait for file to be fully written"""
        last_size = -1
        stable_count = 0
        
        for _ in range(timeout):
            try:
                current_size = filepath.stat().st_size
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= 2:
                        return True
                else:
                    stable_count = 0
                last_size = current_size
                time.sleep(1)
            except OSError:
                time.sleep(1)
                
        return False
    
    def _extract_datetime_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract date string and hour from filename"""
        # Pattern: Futures_YYYYMMDD_HHMM.csv or Options_YYYYMMDD_HHMM.csv
        pattern = r'(?:Futures|Options)_(\d{8})_(\d{2})(\d{2})\.csv'
        match = re.match(pattern, filename)
        
        if match:
            date_str = match.group(1)
            hour = int(match.group(2))
            return date_str, hour
        
        return None, None
    
    def _process_futures_file(self, filepath: Path) -> Dict[str, float]:
        """Parse futures CSV with new format
        
        Expected columns:
        - SYMBOL: Base symbol (e.g., 'TU', 'FV', 'TY')
        - PX_SETTLE_DEC: Settle price in decimal format
        - PX_300_DEC: Flash price (3pm close) in decimal format
        - Settle Price = Today: Status indicator ('Y' for settle, else flash)
        """
        prices = {}
        
        try:
            df = pd.read_csv(filepath)
            
            # Validate required columns exist
            required_columns = ['SYMBOL', 'PX_SETTLE_DEC', 'PX_300_DEC', 'Settle Price = Today']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in futures file: {missing_columns}")
                return prices
            
            # Process all data rows (skip header)
            for idx in range(len(df)):
                row = df.iloc[idx]
                
                # Get symbol from SYMBOL column
                symbol_base = str(row['SYMBOL']).strip().upper()
                
                # Skip empty or invalid symbols
                if not symbol_base or symbol_base == 'NAN':
                    continue
                    
                if symbol_base not in FUTURES_SYMBOLS:
                    logger.warning(f"Unknown futures symbol: {symbol_base}")
                    continue
                
                bloomberg_symbol = FUTURES_SYMBOLS[symbol_base]
                
                # Check status to determine which price to use
                status = str(row['Settle Price = Today']).strip().upper()
                
                if status == 'Y':
                    # Use settle price
                    price_val = row['PX_SETTLE_DEC']
                    price_type = 'settle'
                elif status == 'N':
                    # Use flash price only if status is explicitly 'N'
                    price_val = row['PX_300_DEC']
                    price_type = 'flash'
                else:
                    # For empty/NaN status, try settle price first, then flash
                    settle_val = row['PX_SETTLE_DEC']
                    flash_val = row['PX_300_DEC']
                    
                    if pd.notna(settle_val) and str(settle_val) not in ['#NAME?', '#N/A N/A', 'nan']:
                        price_val = settle_val
                        price_type = 'settle (default)'
                    elif pd.notna(flash_val) and str(flash_val) not in ['#NAME?', '#N/A N/A', 'nan']:
                        price_val = flash_val
                        price_type = 'flash (default)'
                    else:
                        # Skip if both are invalid
                        logger.debug(f"Skipping {bloomberg_symbol}: no valid price available")
                        continue
                
                # Validate and convert price
                if pd.notna(price_val) and str(price_val) not in ['#NAME?', '#N/A N/A', 'nan']:
                    try:
                        prices[bloomberg_symbol] = float(price_val)
                        logger.debug(f"Futures {price_type}: {bloomberg_symbol} = {price_val}")
                    except (ValueError, TypeError):
                        logger.error(f"Invalid price for {bloomberg_symbol}: {price_val}")
                else:
                    logger.debug(f"Skipping {bloomberg_symbol}: price_val={price_val}, isna={pd.isna(price_val)}")
                        
        except Exception as e:
            logger.error(f"Error parsing futures file {filepath}: {e}", exc_info=True)
            
        return prices
    
    def _process_options_file(self, filepath: Path) -> Dict[str, float]:
        """Parse options CSV with new format
        
        Expected columns:
        - SYMBOL: Bloomberg format symbol (e.g., 'TJPN25P5 114.25 Comdty')
        - LAST_PRICE: Flash price
        - PX_SETTLE: Settle price
        - Settle Price = Today: Status indicator ('Y' for settle, else flash)
        """
        prices = {}
        
        try:
            df = pd.read_csv(filepath)
            
            # Validate required columns exist
            required_columns = ['SYMBOL', 'LAST_PRICE', 'PX_SETTLE', 'Settle Price = Today']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns in options file: {missing_columns}")
                return prices
            
            # Process all data rows
            # Stop at empty rows or error rows
            for idx in range(len(df)):
                row = df.iloc[idx]
                
                # Get symbol - already in Bloomberg format
                symbol = str(row['SYMBOL']).strip()
                
                # Skip invalid or empty symbols
                if not symbol or symbol == 'nan' or symbol == '0.0':
                    continue
                
                # Remove 'COMB' if present (normalize symbol format)
                if ' COMB ' in symbol:
                    symbol = symbol.replace(' COMB ', ' ')
                    
                # Check status for this specific row
                status = str(row['Settle Price = Today']).strip().upper()
                
                if status == 'Y':
                    # Use settle price
                    price_val = row['PX_SETTLE']
                    price_type = 'settle'
                else:
                    # Use flash price (LAST_PRICE) for any other status
                    price_val = row['LAST_PRICE']
                    price_type = 'flash'
                
                # Validate and convert price
                # Skip invalid values like -2146826238, #NAME?, etc.
                if (pd.notna(price_val) and 
                    str(price_val) not in ['#NAME?', '#N/A Mandatory parameter [SECURITY] cannot be empty']):
                    try:
                        price_float = float(price_val)
                        # Skip obviously invalid prices (like -2146826238)
                        if price_float > -1000000 and price_float < 1000000:
                            prices[symbol] = price_float
                            logger.debug(f"Options {price_type}: {symbol} = {price_float}")
                    except (ValueError, TypeError):
                        logger.error(f"Invalid price for {symbol}: {price_val}")
                        
        except Exception as e:
            logger.error(f"Error parsing options file {filepath}: {e}", exc_info=True)
            
        return prices
    
    def _update_prices(self, prices: Dict[str, float], date_str: str, hour: int):
        """Update prices in database and call roll_2pm_prices"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Update each price and call roll_2pm
            for symbol, price in prices.items():
                logger.info(f"Updating {symbol}: ${price} and calling roll_2pm_prices")
                roll_2pm_prices(conn, price, symbol)
                
            conn.commit()
            logger.info(f"Successfully updated {len(prices)} prices for {date_str} {hour:02d}:00")
            
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _trigger_4pm_roll_for_date(self, date_str: str):
        """Trigger 4pm roll and EOD settlement for all symbols"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            
            # Get all unique symbols from pricing table
            cursor.execute("SELECT DISTINCT symbol FROM pricing WHERE symbol LIKE '% Comdty'")
            symbols = [row[0] for row in cursor.fetchall()]
            
            # Build close prices dict for EOD settlement
            close_prices = {}
            for symbol in symbols:
                cursor.execute("SELECT price FROM pricing WHERE symbol = ? AND price_type = 'close'", (symbol,))
                result = cursor.fetchone()
                if result:
                    close_prices[symbol] = result[0]
            
            # Roll prices for each symbol
            for symbol in symbols:
                logger.info(f"Rolling 4pm prices for {symbol}")
                roll_4pm_prices(conn, symbol)
                
            # Perform EOD settlement (mark-to-market)
            from datetime import datetime
            settlement_date = datetime.strptime(date_str, '%Y%m%d').date()
            logger.info(f"Performing EOD settlement for {settlement_date}")
            perform_eod_settlement(conn, settlement_date, close_prices)
            
            conn.commit()
            logger.info(f"Successfully completed 4pm roll and EOD settlement for {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error in 4pm roll: {e}")
            conn.rollback()
        finally:
            conn.close()


class ClosePriceWatcher:
    """Main watcher for close price files"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or 'trades.db'
        self.config = CLOSE_PRICE_WATCHER
        self.observers = []
        self.startup_time = time.time()
        self.handler = ClosePriceFileHandler(self.db_path, self.startup_time)
        
    def start(self):
        """Start watching directories"""
        # Create observers for futures and options
        futures_dir = Path(self.config['futures_dir'])
        options_dir = Path(self.config['options_dir'])
        
        logger.info("Ignoring pre-existing files. Only new files will be processed.")
        
        for directory, name in [(futures_dir, 'futures'), (options_dir, 'options')]:
            if directory.exists():
                observer = Observer()
                observer.schedule(self.handler, str(directory), recursive=False)
                observer.start()
                self.observers.append(observer)
                logger.info(f"Started watching {name} directory: {directory}")
            else:
                logger.warning(f"{name} directory does not exist: {directory}")
                
        if not self.observers:
            raise ValueError("No directories available to watch")
    
    def stop(self):
        """Stop all observers"""
        for observer in self.observers:
            if observer.is_alive():
                observer.stop()
                observer.join()
        logger.info("Close price watcher stopped")
    
    def run_forever(self):
        """Run continuously"""
        try:
            self.start()
            logger.info("Close price watcher running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.stop()


def main():
    """Main entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Close Price Watcher')
    parser.add_argument('--db', default='trades.db', help='Path to trades database')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    watcher = ClosePriceWatcher(db_path=args.db)
    watcher.run_forever()


if __name__ == '__main__':
    main() 