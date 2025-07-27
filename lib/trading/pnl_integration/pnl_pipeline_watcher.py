#!/usr/bin/env python3
"""
Minimal Pipeline Watcher Skeleton

Monitors for file changes and triggers callbacks.
All PnL calculation logic has been removed for clean integration
with a new PnL module.
"""

import logging
import time
from pathlib import Path
from typing import Set, Optional, Callable, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

logger = logging.getLogger(__name__)


class FileChangeHandler(FileSystemEventHandler):
    """Generic file change handler."""
    
    def __init__(self, file_pattern: str, callback: Callable):
        """
        Initialize the handler.
        
        Args:
            file_pattern: File extension or pattern to watch (e.g., '.csv')
            callback: Function to call when matching files change
        """
        self.file_pattern = file_pattern
        self.callback = callback
        self.processed_files: Set[str] = set()
        self.debounce_time = 10  # seconds
        self.last_event_time = 0
        
    def on_created(self, event):
        """Handle file creation events."""
        if isinstance(event, FileCreatedEvent) and event.src_path.endswith(self.file_pattern):
            self._handle_file_event(event.src_path, "created")
            
    def on_modified(self, event):
        """Handle file modification events."""
        if isinstance(event, FileModifiedEvent) and event.src_path.endswith(self.file_pattern):
            self._handle_file_event(event.src_path, "modified")
            
    def _handle_file_event(self, file_path: str, event_type: str):
        """Handle file events with debouncing."""
        current_time = time.time()
        
        # Debounce rapid events
        if current_time - self.last_event_time < self.debounce_time:
            logger.debug(f"Debouncing {event_type} event for {file_path}")
            return
            
        self.last_event_time = current_time
        
        # Check if file is ready (not being written)
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return
            
        try:
            # Wait a bit to ensure file write is complete
            time.sleep(2)
            
            # Check file can be read
            with open(file_path, 'rb') as f:
                f.read(1)
                
            logger.info(f"File {event_type}: {file_path}")
            
            # Call the callback
            if self.callback:
                self.callback(file_path, event_type)
                
        except Exception as e:
            logger.error(f"Error handling file event: {e}")


class PipelineWatcher:
    """Minimal pipeline watcher for monitoring file changes."""
    
    def __init__(self):
        """Initialize the watcher."""
        self.observer = Observer()
        self.watched_paths: List[Path] = []
        
    def add_watch(self, directory: str, file_pattern: str, callback: Callable):
        """
        Add a directory to watch for file changes.
        
        Args:
            directory: Directory path to watch
            file_pattern: File extension or pattern (e.g., '.csv')
            callback: Function to call when files change
        """
        watch_path = Path(directory)
        
        if not watch_path.exists():
            logger.warning(f"Watch directory does not exist: {directory}")
            watch_path.mkdir(parents=True, exist_ok=True)
            
        handler = FileChangeHandler(file_pattern, callback)
        self.observer.schedule(handler, str(watch_path), recursive=False)
        self.watched_paths.append(watch_path)
        
        logger.info(f"Watching {directory} for {file_pattern} files")
        
    def start(self):
        """Start the file watcher."""
        if not self.watched_paths:
            logger.warning("No paths configured for watching")
            return
            
        self.observer.start()
        logger.info("Pipeline watcher started")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        """Stop the file watcher."""
        self.observer.stop()
        self.observer.join()
        logger.info("Pipeline watcher stopped")


def create_minimal_watcher() -> PipelineWatcher:
    """
    Create a minimal file watcher.
    
    This is a template - configure with your specific directories
    and callbacks as needed.
    
    Returns:
        Configured PipelineWatcher instance
    """
    watcher = PipelineWatcher()
    
    # Example configurations - modify as needed:
    
    # Watch for trade files
    def on_trade_file(file_path: str, event_type: str):
        logger.info(f"Trade file {event_type}: {file_path}")
        # TODO: Integrate with new PnL module
        
    watcher.add_watch(
        directory="data/input/trade_ledger",
        file_pattern=".csv",
        callback=on_trade_file
    )
    
    # Watch for price files
    def on_price_file(file_path: str, event_type: str):
        logger.info(f"Price file {event_type}: {file_path}")
        # TODO: Integrate with new PnL module
        
    watcher.add_watch(
        directory="data/input/market_prices",
        file_pattern=".csv",
        callback=on_price_file
    )
    
    return watcher


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start watcher
    watcher = create_minimal_watcher()
    watcher.start() 