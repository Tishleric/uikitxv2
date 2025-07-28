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
from datetime import datetime, time as dt_time
from typing import Dict, Optional, Tuple, Set
import pytz
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from .data_manager import roll_2pm_prices, roll_4pm_prices
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
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.daily_tracker = DailyCSVTracker()
        self.processed_files = set()  # Track processed files to avoid duplicates
        self._start_4pm_monitor()
        
    def on_created(self, event):
        """Handle new file creation - skip existing files"""
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
                file_type = 'futures'
            elif 'Options' in str(filepath):
                prices = self._process_options_file(filepath)
                file_type = 'options'
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
        """Parse futures CSV with new format"""
        prices = {}
        
        try:
            df = pd.read_csv(filepath)
            
            # Map column positions (A=0, B=1, C=2, H=7)
            col_A = 0  # Symbol
            col_B = 1  # Settle price
            col_C = 2  # Flash close
            col_H = 7  # Status
            
            # Process rows 2-6 (0-indexed: 1-5)
            for idx in range(1, min(6, len(df))):
                row = df.iloc[idx]
                
                # Check status in column H
                status = str(row.iloc[col_H]).strip().upper() if col_H < len(row) else ''
                if status not in ['Y', 'N']:
                    continue
                
                # Get symbol from column A
                symbol_base = str(row.iloc[col_A]).strip().upper() if col_A < len(row) else ''
                if symbol_base not in FUTURES_SYMBOLS:
                    logger.warning(f"Unknown futures symbol: {symbol_base}")
                    continue
                
                bloomberg_symbol = FUTURES_SYMBOLS[symbol_base]
                
                # Get price based on status
                if status == 'Y':
                    # Use settle price from column B
                    price_val = row.iloc[col_B] if col_B < len(row) else None
                    price_type = 'settle'
                else:
                    # Use flash close from column C
                    price_val = row.iloc[col_C] if col_C < len(row) else None
                    price_type = 'flash'
                
                if pd.notna(price_val) and price_val != '#NAME?':
                    try:
                        prices[bloomberg_symbol] = float(price_val)
                        logger.debug(f"Futures {price_type}: {bloomberg_symbol} = {price_val}")
                    except (ValueError, TypeError):
                        logger.error(f"Invalid price for {bloomberg_symbol}: {price_val}")
                        
        except Exception as e:
            logger.error(f"Error parsing futures file {filepath}: {e}")
            
        return prices
    
    def _process_options_file(self, filepath: Path) -> Dict[str, float]:
        """Parse options CSV with new format"""
        prices = {}
        
        try:
            df = pd.read_csv(filepath)
            
            # Map column positions (G=6, I=8, J=9, K=10)
            col_G = 6   # Status
            col_I = 8   # Symbol
            col_J = 9   # Flash price
            col_K = 10  # Settle price
            
            # Check G2 for status (row index 1)
            if len(df) < 2:
                return prices
            
            status = str(df.iloc[1, col_G]).strip().upper() if col_G < len(df.columns) else ''
            if status not in ['Y', 'N']:
                logger.error(f"Invalid status in G2: {status}")
                return prices
            
            # Determine price column
            if status == 'Y':
                price_col = col_K  # Settle prices
                price_type = 'settle'
            else:
                price_col = col_J  # Flash prices
                price_type = 'flash'
            
            # Process rows 2-433 (0-indexed: 1-432)
            for idx in range(1, min(433, len(df))):
                row = df.iloc[idx]
                
                # Get symbol from column I (already Bloomberg format)
                symbol = str(row.iloc[col_I]).strip() if col_I < len(row) else ''
                if not symbol or symbol == 'nan':
                    continue
                
                # Get price
                price_val = row.iloc[price_col] if price_col < len(row) else None
                if pd.notna(price_val) and str(price_val) != '#NAME?':
                    try:
                        prices[symbol] = float(price_val)
                    except (ValueError, TypeError):
                        logger.error(f"Invalid price for {symbol}: {price_val}")
                        
        except Exception as e:
            logger.error(f"Error parsing options file {filepath}: {e}")
            
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
        """Trigger 4pm roll for all symbols that have prices for this date"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            
            # Get all unique symbols from pricing table
            cursor.execute("SELECT DISTINCT symbol FROM pricing WHERE symbol LIKE '% Comdty'")
            symbols = [row[0] for row in cursor.fetchall()]
            
            # Roll prices for each symbol
            for symbol in symbols:
                logger.info(f"Rolling 4pm prices for {symbol}")
                roll_4pm_prices(conn, symbol)
                
            conn.commit()
            logger.info(f"Successfully completed 4pm roll for {len(symbols)} symbols")
            
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
        self.handler = ClosePriceFileHandler(self.db_path)
        
    def start(self):
        """Start watching directories"""
        # Create observers for futures and options
        futures_dir = Path(self.config['futures_dir'])
        options_dir = Path(self.config['options_dir'])
        
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