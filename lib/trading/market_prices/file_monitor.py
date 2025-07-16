"""
File monitoring system for market price data.

Monitors directories for new futures and options price files and triggers
processing based on time windows.
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Set, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import threading
import time

from lib.monitoring.decorators import monitor
from .storage import MarketPriceStorage
from .futures_processor import FuturesProcessor
from .options_processor import OptionsProcessor
from .constants import CHICAGO_TZ, FILE_PATTERNS, DATA_ROOT
import re

logger = logging.getLogger(__name__)


class MarketPriceFileHandler(FileSystemEventHandler):
    """Handle new market price files."""
    
    def __init__(self, storage: MarketPriceStorage, 
                 futures_callback: Optional[Callable] = None,
                 options_callback: Optional[Callable] = None):
        """
        Initialize file handler with storage and optional callbacks.
        
        Args:
            storage: MarketPriceStorage instance
            futures_callback: Optional callback for futures processing
            options_callback: Optional callback for options processing
        """
        self.storage = storage
        self.futures_processor = FuturesProcessor(storage)
        self.options_processor = OptionsProcessor(storage)
        self.futures_callback = futures_callback
        self.options_callback = options_callback
        
        # Compile regex patterns
        self.futures_pattern = re.compile(FILE_PATTERNS['futures'])
        self.options_pattern = re.compile(FILE_PATTERNS['options'])
        
        # Track processed files to avoid duplicates
        self._processed_files: Set[str] = set()
        self._lock = threading.Lock()
        
    @monitor()
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        filepath = Path(event.src_path)
        self._process_file(filepath)
    
    @monitor()
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        filepath = Path(event.src_path)
        
        # Only process if file hasn't been processed yet
        with self._lock:
            if filepath.name not in self._processed_files:
                self._process_file(filepath)
    
    def _process_file(self, filepath: Path):
        """Process a potential market price file."""
        filename = filepath.name
        
        # Check if it's a futures file
        if self.futures_pattern.match(filename):
            logger.info(f"Detected futures price file: {filename}")
            self._process_futures_file(filepath)
        
        # Check if it's an options file
        elif self.options_pattern.match(filename):
            logger.info(f"Detected options price file: {filename}")
            self._process_options_file(filepath)
        
        else:
            logger.debug(f"Ignoring non-price file: {filename}")
    
    @monitor()
    def _process_futures_file(self, filepath: Path):
        """Process a futures price file."""
        try:
            # Wait a bit to ensure file is fully written
            time.sleep(1)
            
            # Process the file
            result = self.futures_processor.process_file(filepath)
            
            if result:
                logger.info(f"Successfully processed futures file: {filepath.name}")
                
                # Mark as processed
                with self._lock:
                    self._processed_files.add(filepath.name)
                
                # Call callback if provided
                if self.futures_callback:
                    self.futures_callback(filepath, 'processed')
            else:
                logger.warning(f"Failed to process futures file: {filepath.name}")
                
                # Call callback with error status if provided
                if self.futures_callback:
                    self.futures_callback(filepath, 'error')
                    
        except Exception as e:
            logger.error(f"Error processing futures file {filepath}: {e}")
    
    @monitor()
    def _process_options_file(self, filepath: Path):
        """Process an options price file."""
        try:
            # Wait a bit to ensure file is fully written
            time.sleep(1)
            
            # Process the file
            result = self.options_processor.process_file(filepath)
            
            if result:
                logger.info(f"Successfully processed options file: {filepath.name}")
                
                # Mark as processed
                with self._lock:
                    self._processed_files.add(filepath.name)
                
                # Call callback if provided
                if self.options_callback:
                    self.options_callback(filepath, 'processed')
            else:
                logger.warning(f"Failed to process options file: {filepath.name}")
                
                # Call callback with error status if provided
                if self.options_callback:
                    self.options_callback(filepath, 'error')
                    
        except Exception as e:
            logger.error(f"Error processing options file {filepath}: {e}")


class MarketPriceFileMonitor:
    """Monitor directories for new market price files."""
    
    def __init__(self, storage: Optional[MarketPriceStorage] = None,
                 futures_callback: Optional[Callable] = None,
                 options_callback: Optional[Callable] = None):
        """
        Initialize file monitor.
        
        Args:
            storage: MarketPriceStorage instance (creates new if None)
            futures_callback: Optional callback for futures processing
            options_callback: Optional callback for options processing
        """
        self.storage = storage or MarketPriceStorage()
        self.futures_callback = futures_callback
        self.options_callback = options_callback
        
        # Set up directories to monitor
        self.futures_dir = DATA_ROOT / "input" / "market_prices" / "futures"
        self.options_dir = DATA_ROOT / "input" / "market_prices" / "options"
        
        # Create directories if they don't exist
        self.futures_dir.mkdir(parents=True, exist_ok=True)
        self.options_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler and observer
        self.handler = MarketPriceFileHandler(
            self.storage,
            futures_callback=futures_callback,
            options_callback=options_callback
        )
        self.observer = Observer()
        self._monitoring = False
        
    @monitor()
    def start(self):
        """Start monitoring for new files."""
        if self._monitoring:
            logger.warning("Market price monitor already running")
            return
            
        try:
            # Schedule monitoring for both directories
            self.observer.schedule(self.handler, str(self.futures_dir), recursive=False)
            self.observer.schedule(self.handler, str(self.options_dir), recursive=False)
            
            # Start observer
            self.observer.start()
            self._monitoring = True
            
            logger.info(f"Started monitoring market price directories:")
            logger.info(f"  Futures: {self.futures_dir}")
            logger.info(f"  Options: {self.options_dir}")
            
        except Exception as e:
            logger.error(f"Error starting market price monitor: {e}")
            raise
    
    @monitor()
    def stop(self):
        """Stop monitoring."""
        if not self._monitoring:
            return
            
        try:
            self.observer.stop()
            self.observer.join(timeout=5)
            self._monitoring = False
            
            logger.info("Stopped monitoring market price directories")
            
        except Exception as e:
            logger.error(f"Error stopping market price monitor: {e}")
    
    @monitor()
    def process_existing_files(self):
        """Process any existing files in the monitored directories."""
        logger.info("Processing existing market price files...")
        
        # Process existing futures files
        futures_files = list(self.futures_dir.glob("*.csv"))
        for filepath in sorted(futures_files):
            if self.handler.futures_pattern.match(filepath.name):
                logger.info(f"Processing existing futures file: {filepath.name}")
                self.handler._process_futures_file(filepath)
        
        # Process existing options files
        options_files = list(self.options_dir.glob("*.csv"))
        for filepath in sorted(options_files):
            if self.handler.options_pattern.match(filepath.name):
                logger.info(f"Processing existing options file: {filepath.name}")
                self.handler._process_options_file(filepath)
        
        logger.info(f"Processed {len(futures_files)} futures and {len(options_files)} options files")
    
    def is_monitoring(self) -> bool:
        """Check if monitor is currently running."""
        return self._monitoring 