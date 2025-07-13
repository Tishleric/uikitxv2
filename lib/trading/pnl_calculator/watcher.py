"""File watcher component for monitoring trade and market price CSV files.

Uses watchdog library for efficient file system monitoring.
"""

import logging
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from datetime import datetime
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

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


class CSVFileHandler(FileSystemEventHandler):
    """Handler for CSV file changes."""
    
    def __init__(self, file_type: str, callback: Callable[[str, str], None]):
        """Initialize handler.
        
        Args:
            file_type: Type of files to monitor ('trades' or 'market_prices')
            callback: Function to call when file changes, receives (file_path, file_type)
        """
        self.file_type = file_type
        self.callback = callback
        self._last_modified: Dict[str, float] = {}
        self._debounce_seconds = 1.0  # Prevent multiple rapid events
        
    def _should_process(self, file_path: str) -> bool:
        """Check if file should be processed based on debouncing."""
        current_time = time.time()
        last_time = self._last_modified.get(file_path, 0)
        
        if current_time - last_time < self._debounce_seconds:
            return False
            
        self._last_modified[file_path] = current_time
        return True
        
    @monitor()
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if it's a CSV file
        if file_path.suffix.lower() != '.csv':
            return
            
        # Check if we should process (debounce)
        if not self._should_process(str(file_path)):
            return
            
        logger.info(f"New {self.file_type} file detected: {file_path}")
        
        # Wait a moment for file to be fully written
        time.sleep(0.5)
        
        try:
            self.callback(str(file_path), self.file_type)
        except Exception as e:
            logger.error(f"Error processing new file {file_path}: {e}")
            
    @monitor()
    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification event."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if it's a CSV file
        if file_path.suffix.lower() != '.csv':
            return
            
        # Check if we should process (debounce)
        if not self._should_process(str(file_path)):
            return
            
        logger.info(f"{self.file_type} file modified: {file_path}")
        
        # Wait a moment for file write to complete
        time.sleep(0.5)
        
        try:
            self.callback(str(file_path), self.file_type)
        except Exception as e:
            logger.error(f"Error processing modified file {file_path}: {e}")


class PnLFileWatcher:
    """Main file watcher for P&L system."""
    
    def __init__(self, trade_callback: Callable[[str, str], None],
                 price_callback: Callable[[str, str], None]):
        """Initialize the file watcher.
        
        Args:
            trade_callback: Callback for trade file changes
            price_callback: Callback for market price file changes
        """
        self.trade_dir = Path("data/input/trade_ledger")
        self.price_dir = Path("data/input/market_prices")
        
        # Ensure directories exist
        self.trade_dir.mkdir(parents=True, exist_ok=True)
        self.price_dir.mkdir(parents=True, exist_ok=True)
        
        # Create handlers
        self.trade_handler = CSVFileHandler('trades', trade_callback)
        self.price_handler = CSVFileHandler('market_prices', price_callback)
        
        # Create observers
        self.trade_observer = Observer()
        self.price_observer = Observer()
        
        self._running = False
        
    @monitor()
    def start(self):
        """Start watching for file changes."""
        if self._running:
            logger.warning("File watcher already running")
            return
            
        # Schedule observers
        self.trade_observer.schedule(
            self.trade_handler,
            str(self.trade_dir),
            recursive=False
        )
        
        self.price_observer.schedule(
            self.price_handler,
            str(self.price_dir),
            recursive=False
        )
        
        # Start observers
        self.trade_observer.start()
        self.price_observer.start()
        
        self._running = True
        logger.info(f"Started watching directories:")
        logger.info(f"  - Trades: {self.trade_dir}")
        logger.info(f"  - Prices: {self.price_dir}")
        
    @monitor()
    def stop(self):
        """Stop watching for file changes."""
        if not self._running:
            return
            
        self.trade_observer.stop()
        self.price_observer.stop()
        
        self.trade_observer.join()
        self.price_observer.join()
        
        self._running = False
        logger.info("File watcher stopped")
        
    def process_existing_files(self):
        """Process any existing files in the directories.
        
        This is useful on startup to catch up with files that were
        added while the system was down.
        """
        # Process existing trade files
        trade_files = sorted(self.trade_dir.glob("trades_*.csv"))
        for file_path in trade_files:
            logger.info(f"Processing existing trade file: {file_path}")
            try:
                self.trade_handler.callback(str(file_path), 'trades')
            except Exception as e:
                logger.error(f"Error processing existing trade file {file_path}: {e}")
                
        # Process existing market price files
        price_files = sorted(self.price_dir.glob("market_prices_*.csv"))
        for file_path in price_files:
            logger.info(f"Processing existing price file: {file_path}")
            try:
                self.price_handler.callback(str(file_path), 'market_prices')
            except Exception as e:
                logger.error(f"Error processing existing price file {file_path}: {e}")
                
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        
        
def example_usage():
    """Example of how to use the file watcher."""
    
    def on_trade_file_change(file_path: str, file_type: str):
        print(f"Trade file changed: {file_path}")
        
    def on_price_file_change(file_path: str, file_type: str):
        print(f"Price file changed: {file_path}")
        
    # Create and start watcher
    watcher = PnLFileWatcher(on_trade_file_change, on_price_file_change)
    
    # Process existing files first
    watcher.process_existing_files()
    
    # Start watching
    with watcher:
        print("Watching for file changes... Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            
            
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    example_usage() 