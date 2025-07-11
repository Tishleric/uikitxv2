"""File watcher for automatic Spot Risk CSV processing.

This module monitors the input directory for new CSV files and automatically
processes them through the Greek calculation pipeline.
"""

import os
import time
import logging
import json
from pathlib import Path
from typing import Set, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import pytz

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from lib.monitoring.decorators import monitor
from lib.trading.actant.spot_risk.parser import parse_spot_risk_csv
from lib.trading.actant.spot_risk.calculator import SpotRiskGreekCalculator

logger = logging.getLogger(__name__)


def get_spot_risk_date_folder(timestamp: Optional[datetime] = None) -> str:
    """Get the date folder name for a given timestamp using 3pm EST boundaries.
    
    The trading day runs from 3pm EST to 3pm EST the next day.
    Files created between 3pm EST Monday and 3pm EST Tuesday belong to Tuesday's folder.
    
    Args:
        timestamp: The timestamp to check. If None, uses current time.
        
    Returns:
        str: Date folder name in YYYY-MM-DD format
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # Ensure we have timezone info
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    # Convert to EST
    est = pytz.timezone('US/Eastern')
    est_time = timestamp.astimezone(est)
    
    # If before 3pm EST, use previous day
    if est_time.hour < 15:
        folder_date = est_time.date() - timedelta(days=1)
    else:
        folder_date = est_time.date()
    
    return folder_date.strftime('%Y-%m-%d')


def ensure_date_folder(base_path: Path, date_folder: str) -> Path:
    """Ensure a date folder exists and return its path.
    
    Args:
        base_path: Base directory path
        date_folder: Date folder name (YYYY-MM-DD format)
        
    Returns:
        Path: Full path to the date folder
    """
    date_path = base_path / date_folder
    date_path.mkdir(parents=True, exist_ok=True)
    return date_path


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
        
        # State tracking
        self.state_file = self.output_dir / '.file_watcher_state.json'
        self.state = self._load_state()
        
        logger.info(f"SpotRiskFileHandler initialized: watching {input_dir}")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from JSON file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state file: {e}")
        return {}
    
    def _save_state(self):
        """Save state to JSON file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state file: {e}")
    
    def _get_file_key(self, filepath: Path) -> str:
        """Get a unique key for a file based on path, mtime, and size."""
        try:
            stat = filepath.stat()
            return f"{filepath}|{stat.st_mtime}|{stat.st_size}"
        except Exception:
            return str(filepath)
    
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
            
            # Get relative path from input directory
            try:
                relative_path = path.relative_to(self.input_dir)
            except ValueError:
                # File is not in our input directory
                return
            
            # Get relative path string for logging
            relative_path_str = str(relative_path)
            
            # Skip if already processed (check state first)
            file_key = self._get_file_key(path)
            if file_key in self.state:
                logger.debug(f"Skipping already processed file (from state): {relative_path_str}")
                return
            
            # Also check legacy tracking for backward compatibility
            if relative_path_str in self.processed_files:
                logger.debug(f"Skipping already processed file: {relative_path_str}")
                return
            
            # Wait for file to be fully written (simple debounce)
            if not self._wait_for_file_ready(path):
                logger.warning(f"File not ready after timeout: {path.name}")
                return
            
            logger.info(f"Processing new file: {relative_path_str}")
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
            # Start timing
            start_time = time.time()
            
            # Determine relative path and output structure
            try:
                relative_path = input_path.relative_to(self.input_dir)
            except ValueError:
                logger.error(f"File not in input directory: {input_path}")
                return
            
            # Check if file is in a date subfolder or root
            parts = relative_path.parts
            if len(parts) > 1:
                # File is in a subfolder - maintain structure
                date_folder = parts[0]
                output_base_path = ensure_date_folder(self.output_dir, date_folder)
            else:
                # File is in root - determine date folder based on current time
                date_folder = get_spot_risk_date_folder()
                output_base_path = ensure_date_folder(self.output_dir, date_folder)
                logger.info(f"File in root directory, using date folder: {date_folder}")
            
            # Generate output filename with timestamp preserved
            filename_parts = input_path.stem.split('_')
            if len(filename_parts) >= 4:
                timestamp = f"{filename_parts[2]}_{filename_parts[3]}"
                output_filename = f"bav_analysis_processed_{timestamp}.csv"
            else:
                # Fallback
                output_filename = f"{input_path.stem}_processed.csv"
            
            output_path = output_base_path / output_filename
            
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
            
            # Calculate aggregates
            df_with_aggregates = self.calculator.calculate_aggregates(df_with_greeks)
            logger.info("Added aggregate rows")
            
            # Save output (preserving sorting from parser)
            df_with_aggregates.to_csv(output_path, index=False)
            logger.info(f"Saved processed file: {output_path}")
            
            # Calculate and log total processing time
            elapsed_time = time.time() - start_time
            logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
            
            # Mark as processed using relative path
            self.processed_files.add(str(relative_path))
            
            # Save to persistent state
            file_key = self._get_file_key(input_path)
            self.state[file_key] = {
                'processed_at': datetime.now().isoformat(),
                'output_file': str(output_path),
                'relative_path': str(relative_path)
            }
            self._save_state()
            
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
        
        # Start watching for new files (recursive=True to watch subfolders)
        self.observer.schedule(self.handler, str(self.input_dir), recursive=True)
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
        
        # Load state to get already processed files
        state_processed = set()
        for file_info in self.handler.state.values():
            if 'relative_path' in file_info:
                state_processed.add(file_info['relative_path'])
        
        # Get list of already processed files (check all subfolders)
        processed_files = set(state_processed)  # Start with state-tracked files
        
        # Look for processed files in root and all date subfolders
        for processed_file in self.output_dir.rglob("bav_analysis_processed_*.csv"):
            # Extract original filename from processed name
            # bav_analysis_processed_YYYYMMDD_HHMMSS.csv -> bav_analysis_YYYYMMDD_HHMMSS.csv
            parts = processed_file.stem.split('_')
            if len(parts) >= 4:
                original_name = f"bav_analysis_{parts[2]}_{parts[3]}.csv"
                
                # Determine relative path based on where the processed file is
                try:
                    relative_output_path = processed_file.relative_to(self.output_dir)
                    if len(relative_output_path.parts) > 1:
                        # File is in a date subfolder
                        date_folder = relative_output_path.parts[0]
                        original_relative_path = f"{date_folder}/{original_name}"
                    else:
                        # File is in root (legacy)
                        original_relative_path = original_name
                    processed_files.add(original_relative_path)
                except ValueError:
                    logger.warning(f"Could not determine relative path for: {processed_file}")
        
        self.handler.processed_files = processed_files
        logger.info(f"Found {len(processed_files)} already processed files")
        
        # Process any unprocessed files in root and subfolders
        for csv_file in self.input_dir.rglob("bav_analysis_*.csv"):
            try:
                relative_path = csv_file.relative_to(self.input_dir)
                relative_path_str = str(relative_path)
                
                # Check state first for efficiency
                file_key = self.handler._get_file_key(csv_file)
                if file_key in self.handler.state:
                    continue
                
                if relative_path_str not in processed_files:
                    logger.info(f"Processing existing file: {relative_path_str}")
                    self.handler._process_csv_file(csv_file)
            except ValueError:
                logger.warning(f"File not in input directory: {csv_file}") 