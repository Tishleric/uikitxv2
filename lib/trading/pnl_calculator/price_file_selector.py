"""
Price File Selector for P&L Calculator

Implements intelligent time-based selection of price files and price columns.
Only considers files exported around 2pm and 4pm CDT, ignoring 3pm exports.
"""

import re
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Optional, Tuple, List
import pytz

# Chicago timezone for all time comparisons
CHICAGO_TZ = pytz.timezone('America/Chicago')

# Valid export time windows (in CDT)
EXPORT_WINDOWS = {
    '2pm': {
        'target': time(14, 0),      # 2:00 PM
        'start': time(13, 45),      # 1:45 PM  
        'end': time(14, 30),        # 2:30 PM
        'price_column': 'PX_LAST'
    },
    '4pm': {
        'target': time(16, 0),      # 4:00 PM
        'start': time(15, 45),      # 3:45 PM
        'end': time(16, 30),        # 4:30 PM
        'price_column': 'PX_SETTLE'
    }
}


class PriceFileSelector:
    """Selects appropriate price files based on time windows."""
    
    def __init__(self):
        self.chicago_tz = CHICAGO_TZ
        
    def parse_price_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract datetime from price filename.
        
        Expected formats:
        - Options_YYYYMMDD_HHMM.csv
        - Futures_YYYYMMDD_HHMM.csv
        - market_prices_YYYYMMDD_HHMM.csv
        
        Returns:
            Datetime object in Chicago timezone, or None if parsing fails
        """
        # Try different patterns
        patterns = [
            r'(\d{8})_(\d{4})\.csv$',  # YYYYMMDD_HHMM.csv
            r'(\d{8})_(\d{2})(\d{2})\.csv$',  # YYYYMMDD_HHMM.csv (grouped differently)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                if len(match.groups()) == 2:
                    date_str, time_str = match.groups()
                else:
                    date_str = match.group(1)
                    time_str = match.group(2) + match.group(3)
                
                try:
                    # Parse date and time
                    dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M")
                    # Assume times in filenames are in Chicago time
                    dt_chicago = self.chicago_tz.localize(dt)
                    return dt_chicago
                except ValueError:
                    continue
                    
        return None
    
    def classify_export_time(self, dt: datetime) -> Optional[str]:
        """
        Classify a datetime into export window (2pm, 4pm, or None).
        
        Args:
            dt: Datetime to classify (should be timezone-aware)
            
        Returns:
            '2pm', '4pm', or None if not in a valid window
        """
        # Convert to Chicago time if needed
        if dt.tzinfo is None:
            dt = self.chicago_tz.localize(dt)
        else:
            dt = dt.astimezone(self.chicago_tz)
            
        # Get time component
        dt_time = dt.time()
        
        # Check each window
        for window_name, window_config in EXPORT_WINDOWS.items():
            start = window_config['start']
            end = window_config['end']
            
            # Handle boundary cases (inclusive)
            if start <= dt_time <= end:
                return window_name
                
        return None
    
    def get_latest_valid_price_file(
        self, 
        directory: Path, 
        current_time: Optional[datetime] = None
    ) -> Tuple[Optional[Path], str]:
        """
        Get the latest valid price file and corresponding price column.
        
        Args:
            directory: Directory containing price files
            current_time: Current time for selection logic (defaults to now)
            
        Returns:
            Tuple of (file_path, price_column) or (None, '') if no valid files
            
        Raises:
            ValueError: If no valid price files found
        """
        if current_time is None:
            current_time = datetime.now(self.chicago_tz)
        elif current_time.tzinfo is None:
            current_time = self.chicago_tz.localize(current_time)
        else:
            current_time = current_time.astimezone(self.chicago_tz)
            
        # Get all CSV files
        csv_files = list(directory.glob("*.csv"))
        
        if not csv_files:
            raise ValueError(f"No CSV files found in {directory}")
            
        # Parse and classify files
        valid_files = []
        for file_path in csv_files:
            dt = self.parse_price_filename(file_path.name)
            if dt:
                window = self.classify_export_time(dt)
                if window:
                    valid_files.append((file_path, dt, window))
        
        if not valid_files:
            raise ValueError(f"No valid price files (2pm or 4pm) found in {directory}")
            
        # Sort by timestamp (newest first)
        valid_files.sort(key=lambda x: x[1], reverse=True)
        
        # Selection logic based on current time
        current_hour = current_time.hour
        
        # After 4:30pm, prefer 4pm file if available
        if current_hour >= 16 and current_time.minute >= 30:
            # Look for today's 4pm file first
            today = current_time.date()
            for file_path, dt, window in valid_files:
                if dt.date() == today and window == '4pm':
                    return file_path, EXPORT_WINDOWS[window]['price_column']
                    
        # Otherwise, use most recent valid file
        file_path, dt, window = valid_files[0]
        return file_path, EXPORT_WINDOWS[window]['price_column']
    
    def select_price_files(
        self, 
        base_directory: Path,
        current_time: Optional[datetime] = None
    ) -> dict:
        """
        Select price files for both futures and options.
        
        Args:
            base_directory: Base directory containing futures/ and options/ subdirs
            current_time: Current time for selection logic
            
        Returns:
            Dictionary with 'futures' and 'options' keys containing file info
        """
        results = {}
        
        # Select futures file
        futures_dir = base_directory / "futures"
        if futures_dir.exists():
            try:
                futures_file, futures_col = self.get_latest_valid_price_file(
                    futures_dir, current_time
                )
                results['futures'] = {
                    'file': futures_file,
                    'price_column': futures_col,
                    'timestamp': self.parse_price_filename(futures_file.name)
                }
            except ValueError as e:
                results['futures'] = {'error': str(e)}
                
        # Select options file
        options_dir = base_directory / "options"
        if options_dir.exists():
            try:
                options_file, options_col = self.get_latest_valid_price_file(
                    options_dir, current_time
                )
                results['options'] = {
                    'file': options_file,
                    'price_column': options_col,
                    'timestamp': self.parse_price_filename(options_file.name)
                }
            except ValueError as e:
                results['options'] = {'error': str(e)}
                
        return results 