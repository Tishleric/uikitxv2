"""
Trade File Watcher for P&L Calculator

Monitors trade ledger input directory and processes files using TradePreprocessor.
Handles the specific behavior where today's file grows throughout the day and
switches to next day's file at 4pm CDT.
"""

import logging
from pathlib import Path
from datetime import datetime, time, timedelta
import pytz
from typing import Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from .trade_preprocessor import TradePreprocessor

# Set up module logger
logger = logging.getLogger(__name__)


class TradeFileHandler(FileSystemEventHandler):
    """Handler for trade file changes with special logic for growing files."""
    
    def __init__(self, preprocessor: TradePreprocessor):
        """Initialize handler.
        
        Args:
            preprocessor: TradePreprocessor instance to use
        """
        self.preprocessor = preprocessor
        self.chicago_tz = pytz.timezone('America/Chicago')
        self._processing = set()  # Track files currently being processed
        
    def _is_trade_file(self, file_path: Path) -> bool:
        """Check if file is a trade ledger file."""
        return (file_path.suffix.lower() == '.csv' and 
                file_path.name.startswith('trades_'))
    
    def _get_current_trade_date(self) -> str:
        """Get the current trade date (switches at 4pm CDT)."""
        now = datetime.now(self.chicago_tz)
        cutover_time = datetime.strptime("16:00", "%H:%M").time()  # 4pm
        
        # If before 4pm, use today; if after 4pm, use tomorrow
        if now.time() < cutover_time:
            trade_date = now.date()
        else:
            trade_date = (now + timedelta(days=1)).date()
        
        return trade_date.strftime('%Y%m%d')
    
    def _is_active_file(self, file_path: Path) -> bool:
        """Check if this is the active trade file for today."""
        # Extract date from filename (trades_YYYYMMDD.csv)
        try:
            file_date = file_path.stem.split('_')[1]
            current_date = self._get_current_trade_date()
            return file_date == current_date
        except (IndexError, ValueError):
            return False
    
    def _handle_file_event(self, file_path: Path):
        """Process a file event."""
        # Skip if not a trade file
        if not self._is_trade_file(file_path):
            return
        
        # Skip if already processing
        if str(file_path) in self._processing:
            logger.debug(f"Already processing {file_path.name}, skipping")
            return
        
        try:
            # Mark as processing
            self._processing.add(str(file_path))
            
            # Check if this is the active file
            is_active = self._is_active_file(file_path)
            
            if is_active:
                logger.info(f"Processing active trade file: {file_path.name}")
            else:
                logger.info(f"Processing historical trade file: {file_path.name}")
            
            # Process the file
            self.preprocessor.process_trade_file(str(file_path))
            
        except Exception as e:
            logger.error(f"Error handling file event for {file_path}: {e}")
        finally:
            # Remove from processing set
            self._processing.discard(str(file_path))
    
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        logger.info(f"New file detected: {file_path.name}")
        self._handle_file_event(file_path)
    
    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification event."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only log if it's a trade file to reduce noise
        if self._is_trade_file(file_path):
            logger.debug(f"File modified: {file_path.name}")
            self._handle_file_event(file_path)


class TradeFileWatcher:
    """Main watcher for trade ledger files."""
    
    def __init__(self, input_dir: Optional[str] = None, output_dir: Optional[str] = None):
        """Initialize the trade file watcher.
        
        Args:
            input_dir: Directory to watch (default: data/input/trade_ledger)
            output_dir: Directory for processed files (default: data/output/trade_ledger_processed)
        """
        # Set directories
        self.input_dir = Path(input_dir) if input_dir else Path("data/input/trade_ledger")
        
        # Ensure input directory exists
        self.input_dir.mkdir(parents=True, exist_ok=True)
        
        # Create preprocessor
        self.preprocessor = TradePreprocessor(output_dir)
        
        # Create handler
        self.handler = TradeFileHandler(self.preprocessor)
        
        # Create observer
        self.observer = Observer()
        
        self._running = False
        
    def start(self):
        """Start watching for file changes."""
        if self._running:
            logger.warning("Trade file watcher already running")
            return
        
        # Process existing files first
        logger.info("Processing existing trade files...")
        self.preprocessor.process_all_files(str(self.input_dir))
        
        # Schedule observer
        self.observer.schedule(
            self.handler,
            str(self.input_dir),
            recursive=False
        )
        
        # Start observer
        self.observer.start()
        self._running = True
        
        logger.info(f"Trade file watcher started, monitoring {self.input_dir}")
    
    def stop(self):
        """Stop watching for file changes."""
        if not self._running:
            return
        
        self.observer.stop()
        self.observer.join()
        self._running = False
        
        logger.info("Trade file watcher stopped")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


if __name__ == "__main__":
    # Example usage
    import time
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start watcher
    watcher = TradeFileWatcher()
    
    try:
        watcher.start()
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        watcher.stop() 