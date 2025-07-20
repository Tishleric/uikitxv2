"""
Spot Risk File Handler for market price monitoring.

Handles spot risk CSV files and processes them for Current_Price updates.
"""

import logging
from pathlib import Path
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import time
import threading

from lib.monitoring.decorators import monitor
from .spot_risk_price_processor import SpotRiskPriceProcessor
from .storage import MarketPriceStorage

logger = logging.getLogger(__name__)


class SpotRiskFileHandler(FileSystemEventHandler):
    """Handle new spot risk files."""
    
    def __init__(self, storage: MarketPriceStorage):
        """
        Initialize file handler with storage.
        
        Args:
            storage: MarketPriceStorage instance
        """
        self.storage = storage
        self.processor = SpotRiskPriceProcessor(storage)
        
        # Track processed files to avoid duplicates
        self._processed_files = set()
        self._lock = threading.Lock()
        
    @monitor()
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation events."""
        filepath = Path(event.src_path)
        
        # If it's a new directory, we'll catch files via on_modified
        if event.is_directory:
            return
            
        # Only process bav_analysis files
        if filepath.name.startswith('bav_analysis_') and filepath.suffix == '.csv':
            self._process_file(filepath)
    
    @monitor()
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        filepath = Path(event.src_path)
        
        # Only process if file hasn't been processed yet
        with self._lock:
            if filepath.name not in self._processed_files and \
               filepath.name.startswith('bav_analysis_') and filepath.suffix == '.csv':
                self._process_file(filepath)
    
    def _process_file(self, filepath: Path):
        """Process a spot risk file."""
        logger.info(f"Detected spot risk file: {filepath.name}")
        
        try:
            # Wait a bit to ensure file is fully written
            time.sleep(2)
            
            # Process the file
            result = self.processor.process_file(filepath)
            
            if result:
                logger.info(f"Successfully processed spot risk file: {filepath.name}")
                
                # Mark as processed
                with self._lock:
                    self._processed_files.add(filepath.name)
            else:
                logger.warning(f"Failed to process spot risk file: {filepath.name}")
                
        except Exception as e:
            logger.error(f"Error processing spot risk file {filepath}: {e}") 