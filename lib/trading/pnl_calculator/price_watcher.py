"""Price file watcher for real-time price monitoring."""

import logging
import os
import time as time_module
from pathlib import Path
from datetime import datetime, time
from typing import Dict, Set, Optional, Callable
import pytz
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

logger = logging.getLogger(__name__)


class PriceFileHandler(FileSystemEventHandler):
    """Handles file system events for price files."""
    
    def __init__(self, 
                 processor_callback: Callable[[Path], None],
                 chicago_tz):
        """
        Initialize the handler.
        
        Args:
            processor_callback: Function to call when a price file is detected
            chicago_tz: Chicago timezone for time window checks
        """
        self.processor_callback = processor_callback
        self.chicago_tz = chicago_tz
        self.processed_files: Set[str] = set()
        
    def _is_price_file(self, file_path: Path) -> bool:
        """Check if file is a price file based on name pattern."""
        # Price files have patterns: Futures_YYYYMMDD_HHMM.csv or Options_YYYYMMDD_HHMM.csv
        name = file_path.name.lower()
        return ((name.startswith('futures_') or name.startswith('options_') or name.startswith('market_prices_')) and 
                name.endswith('.csv') and
                file_path.exists() and
                file_path.stat().st_size > 0)
    
    def _get_file_time(self, file_path: Path) -> Optional[datetime]:
        """Extract timestamp from filename."""
        # Expected formats: 
        # - Futures_YYYYMMDD_HHMM.csv
        # - Options_YYYYMMDD_HHMM.csv
        # - market_prices_YYYYMMDD_HHMM.csv
        try:
            parts = file_path.stem.split('_')
            if len(parts) >= 3:
                # For Futures_ or Options_ files, date is at index 1
                if parts[0].lower() in ['futures', 'options']:
                    date_str = parts[1]  # YYYYMMDD
                    time_str = parts[2]  # HHMM
                # For market_prices_ files, date is at index 2
                elif parts[0].lower() == 'market' and len(parts) >= 4:
                    date_str = parts[2]  # YYYYMMDD
                    time_str = parts[3]  # HHMM
                else:
                    return None
                
                # Parse date and time
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                hour = int(time_str[:2])
                minute = int(time_str[2:4])
                
                # Create datetime in Chicago timezone
                dt = self.chicago_tz.localize(
                    datetime(year, month, day, hour, minute)
                )
                return dt
        except (ValueError, IndexError) as e:
            logger.debug(f"Could not parse time from {file_path.name}: {e}")
        return None
    
    def _is_in_valid_window(self, file_time: datetime) -> bool:
        """Check if file time is within 2pm or 4pm window."""
        # Define windows in Chicago time
        windows = [
            (time(13, 45), time(14, 30)),  # 1:45-2:30 PM (2pm window)
            (time(15, 45), time(16, 30)),  # 3:45-4:30 PM (4pm window)
        ]
        
        file_time_only = file_time.time()
        
        for start, end in windows:
            if start <= file_time_only <= end:
                return True
        return False
    
    def _should_process_file(self, file_path: Path, check_time_window: bool = True) -> bool:
        """Determine if file should be processed.
        
        Args:
            file_path: Path to the file
            check_time_window: Whether to enforce time window check (default True)
        """
        if not self._is_price_file(file_path):
            return False
            
        # Check if already processed
        file_key = f"{file_path.name}:{file_path.stat().st_mtime}"
        if file_key in self.processed_files:
            logger.debug(f"File already processed: {file_path.name}")
            return False
            
        # Check time window for real-time processing
        # Only process files within valid time windows for accurate price selection
        if check_time_window:
            file_time = self._get_file_time(file_path)
            if file_time and not self._is_in_valid_window(file_time):
                logger.debug(f"File outside valid time windows: {file_path.name}")
                return False
            
        return True
    
    def on_created(self, event):
        """Handle file creation events."""
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            file_path = Path(event.src_path)
            if self._should_process_file(file_path):
                logger.info(f"New price file detected: {file_path.name}")
                try:
                    self.processor_callback(file_path)
                    # Mark as processed
                    file_key = f"{file_path.name}:{file_path.stat().st_mtime}"
                    self.processed_files.add(file_key)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
    
    def on_modified(self, event):
        """Handle file modification events."""
        if isinstance(event, FileModifiedEvent) and not event.is_directory:
            file_path = Path(event.src_path)
            if self._should_process_file(file_path):
                logger.info(f"Price file modified: {file_path.name}")
                try:
                    self.processor_callback(file_path)
                    # Mark as processed
                    file_key = f"{file_path.name}:{file_path.stat().st_mtime}"
                    self.processed_files.add(file_key)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")


class PriceFileWatcher:
    """Watches directories for new price files."""
    
    def __init__(self, watch_directories: list[str], processor_callback: Callable[[Path], None]):
        """
        Initialize the price file watcher.
        
        Args:
            watch_directories: List of directories to monitor
            processor_callback: Function to call when a price file is detected
        """
        self.watch_directories = [Path(d) for d in watch_directories]
        self.processor_callback = processor_callback
        self.chicago_tz = pytz.timezone('America/Chicago')
        self.observer = Observer()
        self.is_running = False
        
        # Create handler
        self.handler = PriceFileHandler(processor_callback, self.chicago_tz)
        
        # Validate directories
        for directory in self.watch_directories:
            if not directory.exists():
                logger.warning(f"Watch directory does not exist: {directory}")
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created watch directory: {directory}")
    
    def start(self):
        """Start watching for price files."""
        if self.is_running:
            logger.warning("Price file watcher already running")
            return
            
        # Schedule observers for each directory
        for directory in self.watch_directories:
            if directory.exists():
                self.observer.schedule(self.handler, str(directory), recursive=False)
                logger.info(f"Watching directory: {directory}")
        
        # Start observer
        self.observer.start()
        self.is_running = True
        logger.info("Price file watcher started")
        
        # Wait a moment before processing existing files
        time_module.sleep(0.5)
        
        # Process any existing files on startup
        self._process_existing_files()
    
    def stop(self):
        """Stop watching for price files."""
        if not self.is_running:
            return
            
        self.observer.stop()
        self.observer.join()
        self.is_running = False
        logger.info("Price file watcher stopped")
    
    def _process_existing_files(self):
        """Process any existing files in watched directories on startup."""
        logger.info("Checking for existing price files...")
        
        for directory in self.watch_directories:
            if not directory.exists():
                continue
                
            # Find all price CSV files (Futures_*, Options_*, or market_prices_*)
            for pattern in ["Futures_*.csv", "Options_*.csv", "market_prices_*.csv"]:
                for file_path in directory.glob(pattern):
                    # Skip time window check for initial loading of existing files
                    if self.handler._should_process_file(file_path, check_time_window=False):
                        logger.info(f"Processing existing file: {file_path.name}")
                        try:
                            self.processor_callback(file_path)
                            # Mark as processed
                            file_key = f"{file_path.name}:{file_path.stat().st_mtime}"
                            self.handler.processed_files.add(file_key)
                        except Exception as e:
                            logger.error(f"Error processing existing file {file_path}: {e}") 