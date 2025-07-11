"""File watcher for automatic Spot Risk CSV processing.

This module monitors the input directory for new CSV files and automatically
processes them through the Greek calculation pipeline.
"""

import os
import time
import logging
from pathlib import Path
from typing import Set, Optional
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from lib.monitoring.decorators import monitor
from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator

logger = logging.getLogger(__name__)


class SpotRiskFileHandler(FileSystemEventHandler):
    """Handles file system events for Spot Risk CSV files."""
    
    def __init__(self, input_dir: str, output_dir: str, processed_files: Optional[Set[str]] = None):
        """Initialize the file handler.
        
        Args:
            input_dir: Directory to watch for new CSV files
            output_dir: Directory to save processed files
            processed_files: Set of already processed filenames (for restart recovery)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.processed_files = processed_files or set()
        self.calculator = SpotRiskGreekCalculator()
        
        # Create output directory if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Pattern for valid files: bav_analysis_YYYYMMDD_HHMMSS.csv
        self.file_pattern = r'bav_analysis_\d{8}_\d{6}\.csv'
        
        logger.info(f"SpotRiskFileHandler initialized: watching {input_dir}")
    
    @monitor()
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        if isinstance(event, FileCreatedEvent):
            self._process_file_event(event.src_path)
    
    @monitor()
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        # Also process on modify in case file was created empty and then written
        self._process_file_event(event.src_path)
    
    def _process_file_event(self, filepath: str):
        """Process a file event with debouncing and validation."""
        try:
            path = Path(filepath)
            
            # Check if it's a CSV file matching our pattern
            if not path.suffix.lower() == '.csv':
                return
                
            if not path.name.startswith('bav_analysis_'):
                return
            
            # Skip if already processed
            if path.name in self.processed_files:
                logger.debug(f"Skipping already processed file: {path.name}")
                return
            
            # Wait for file to be fully written (simple debounce)
            if not self._wait_for_file_ready(path):
                logger.warning(f"File not ready after timeout: {path.name}")
                return
            
            logger.info(f"Processing new file: {path.name}")
            self._process_csv_file(path)
            
        except Exception as e:
            logger.error(f"Error handling file event for {filepath}: {e}", exc_info=True)
    
    def _wait_for_file_ready(self, filepath: Path, timeout: int = 10) -> bool:
        """Wait for file to be fully written by checking size stability.
        
        Args:
            filepath: Path to the file
            timeout: Maximum seconds to wait
            
        Returns:
            bool: True if file is ready, False if timeout
        """
        last_size = -1
        stable_count = 0
        
        for _ in range(timeout):
            try:
                current_size = filepath.stat().st_size
                
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= 2:  # Size stable for 2 seconds
                        return True
                else:
                    stable_count = 0
                    
                last_size = current_size
                time.sleep(1)
                
            except OSError:
                # File might be locked or deleted
                time.sleep(1)
                
        return False
    
    @monitor()
    def _process_csv_file(self, input_path: Path):
        """Process a single CSV file through the Greek calculation pipeline.
        
        Args:
            input_path: Path to the input CSV file
        """
        try:
            # Generate output filename with timestamp preserved
            filename_parts = input_path.stem.split('_')
            if len(filename_parts) >= 4:
                timestamp = f"{filename_parts[2]}_{filename_parts[3]}"
                output_filename = f"bav_analysis_processed_{timestamp}.csv"
            else:
                # Fallback
                output_filename = f"{input_path.stem}_processed.csv"
            
            output_path = self.output_dir / output_filename
            
            # Parse CSV
            logger.info(f"Parsing CSV file: {input_path}")
            df = parse_spot_risk_csv(input_path, calculate_time_to_expiry=True)
            
            if df is None or df.empty:
                logger.error(f"Failed to parse CSV file: {input_path}")
                return
            
            logger.info(f"Parsed {len(df)} rows, calculating Greeks...")
            
            # Calculate Greeks
            df_with_greeks, results = self.calculator.calculate_greeks(df)
            
            # Log summary
            success_count = sum(1 for r in results if r.success)
            logger.info(f"Greek calculations: {success_count} successful, {len(results) - success_count} failed")
            
            # Save output (preserving sorting from parser)
            df_with_greeks.to_csv(output_path, index=False)
            logger.info(f"Saved processed file: {output_path}")
            
            # Mark as processed
            self.processed_files.add(input_path.name)
            
        except Exception as e:
            logger.error(f"Error processing CSV file {input_path}: {e}", exc_info=True)
            # Don't mark as processed on error - allow retry on next run


class SpotRiskWatcher:
    """Main watcher service for Spot Risk CSV files."""
    
    def __init__(self, input_dir: str, output_dir: str):
        """Initialize the watcher service.
        
        Args:
            input_dir: Directory to watch for new CSV files
            output_dir: Directory to save processed files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.observer = Observer()
        self.handler = SpotRiskFileHandler(input_dir, output_dir)
        
    @monitor()
    def start(self):
        """Start watching for files."""
        logger.info(f"Starting SpotRiskWatcher on {self.input_dir}")
        
        # Process any existing files first
        self._process_existing_files()
        
        # Start watching for new files
        self.observer.schedule(self.handler, str(self.input_dir), recursive=False)
        self.observer.start()
        
        logger.info("SpotRiskWatcher started successfully")
    
    def stop(self):
        """Stop watching for files."""
        logger.info("Stopping SpotRiskWatcher...")
        self.observer.stop()
        self.observer.join()
        logger.info("SpotRiskWatcher stopped")
    
    def _process_existing_files(self):
        """Process any existing unprocessed files in the input directory."""
        logger.info("Checking for existing unprocessed files...")
        
        # Get list of already processed files
        processed_files = set()
        for f in self.output_dir.glob("bav_analysis_processed_*.csv"):
            # Extract original filename from processed name
            # bav_analysis_processed_YYYYMMDD_HHMMSS.csv -> bav_analysis_YYYYMMDD_HHMMSS.csv
            parts = f.stem.split('_')
            if len(parts) >= 4:
                original_name = f"bav_analysis_{parts[2]}_{parts[3]}.csv"
                processed_files.add(original_name)
        
        self.handler.processed_files = processed_files
        logger.info(f"Found {len(processed_files)} already processed files")
        
        # Process any unprocessed files
        for csv_file in self.input_dir.glob("bav_analysis_*.csv"):
            if csv_file.name not in processed_files:
                logger.info(f"Processing existing file: {csv_file.name}")
                self.handler._process_csv_file(csv_file) 