"""Spot Risk Dashboard Controller

This module handles the business logic for the Spot Risk dashboard.
Follows the Controller layer of MVC pattern - coordinates between data and views.
"""

import os
import glob
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import datetime

from lib.monitoring.decorators import monitor
from lib.trading.actant.spot_risk import parse_spot_risk_csv, SpotRiskGreekCalculator


class SpotRiskController:
    """Controller for Spot Risk dashboard business logic
    
    Handles data loading, processing, and state management.
    """
    
    def __init__(self):
        """Initialize the controller with calculator instance"""
        self.calculator = SpotRiskGreekCalculator()
        self.current_data: Optional[pd.DataFrame] = None
        self.data_timestamp: Optional[datetime] = None
        # Keep csv_directory for backward compatibility
        self.csv_directory = self._get_csv_directory()
        
    def _get_csv_directory(self) -> Path:
        """Get the directory where spot risk CSV files are stored
        
        Returns:
            Path: Directory path for CSV files
        """
        # Navigate from controller location to data directory
        project_root = Path(__file__).parent.parent.parent.parent
        csv_dir = project_root / "data" / "input" / "actant_spot_risk"
        
        # Create directory if it doesn't exist
        csv_dir.mkdir(parents=True, exist_ok=True)
        
        return csv_dir
    
    def _get_csv_directories(self) -> List[Path]:
        """Get all directories where spot risk CSV files might be stored
        
        Returns:
            List[Path]: List of directory paths, in priority order
        """
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Check output directory first (for processed files)
        output_dir = project_root / "data" / "output" / "spot_risk"
        input_dir = project_root / "data" / "input" / "actant_spot_risk"
        
        dirs = []
        if output_dir.exists():
            dirs.append(output_dir)
        if input_dir.exists():
            dirs.append(input_dir)
            
        # Create input directory if neither exists
        if not dirs:
            input_dir.mkdir(parents=True, exist_ok=True)
            dirs.append(input_dir)
            
        return dirs
    
    @monitor()
    def discover_csv_files(self) -> List[Dict[str, Any]]:
        """Discover available CSV files in the spot risk directory
        
        Returns:
            List[Dict]: List of file info dicts with keys:
                - filepath: Full path to file
                - filename: Just the filename
                - modified_time: Last modified datetime
                - size_mb: File size in MB
        """
        file_info = []
        
        # Check all directories
        for directory in self._get_csv_directories():
            # Pattern to match CSV files
            pattern = str(directory / "*.csv")
            csv_files = glob.glob(pattern)
            
            for filepath in csv_files:
                path = Path(filepath)
                stat = path.stat()
                
                # Prioritize processed files
                is_processed = "_processed" in path.name
                
                file_info.append({
                    'filepath': str(path),
                    'filename': path.name,
                    'modified_time': datetime.fromtimestamp(stat.st_mtime),
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'is_processed': is_processed
                })
        
        # Sort by: processed files first, then by modified time (newest first)
        file_info.sort(key=lambda x: (not x['is_processed'], -x['modified_time'].timestamp()))
        
        return file_info
    
    @monitor()
    def find_latest_csv(self) -> Optional[str]:
        """Find the most recently modified CSV file
        
        Returns:
            Optional[str]: Path to latest CSV file, or None if no files found
        """
        files = self.discover_csv_files()
        
        if files:
            return files[0]['filepath']
        
        return None
    
    @monitor()
    def load_csv_data(self, filepath: Optional[str] = None) -> bool:
        """Load CSV data and prepare for processing
        
        Args:
            filepath: Path to CSV file. If None, loads latest file.
            
        Returns:
            bool: True if data loaded successfully
        """
        try:
            # Use provided filepath or find latest
            if filepath is None:
                filepath = self.find_latest_csv()
                
            if filepath is None:
                print("No CSV files found in spot risk directory")
                return False
            
            # Parse the CSV file
            df = parse_spot_risk_csv(filepath)
            
            if df is None or df.empty:
                print(f"Failed to parse CSV file: {filepath}")
                return False
            
            # Store the data and metadata
            self.current_data = df
            self.data_timestamp = self._extract_timestamp(filepath, df)
            
            print(f"Loaded {len(df)} rows from {Path(filepath).name}")
            return True
            
        except Exception as e:
            print(f"Error loading CSV data: {e}")
            return False
    
    def _extract_timestamp(self, filepath: str, df: pd.DataFrame) -> datetime:
        """Extract timestamp from filename or data
        
        Args:
            filepath: Path to CSV file
            df: Parsed DataFrame
            
        Returns:
            datetime: Best guess at data timestamp
        """
        # Try to extract from filename first
        # Expected format: bav_analysis_YYYYMMDD_HHMMSS.csv
        filename = Path(filepath).stem
        parts = filename.split('_')
        
        if len(parts) >= 4:
            try:
                date_str = parts[-2]  # YYYYMMDD
                time_str = parts[-1]  # HHMMSS
                
                # Parse the timestamp
                timestamp_str = f"{date_str}_{time_str}"
                return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except:
                pass
        
        # Fallback to file modification time
        return datetime.fromtimestamp(Path(filepath).stat().st_mtime)
    
    @monitor()
    def process_greeks(self, model: str = "bachelier_v1") -> Optional[pd.DataFrame]:
        """Process Greeks for current data using specified model
        
        Args:
            model: Model version to use for calculations
            
        Returns:
            Optional[pd.DataFrame]: Processed data with Greeks, or None if failed
        """
        if self.current_data is None:
            print("No data loaded. Call load_csv_data() first.")
            return None
        
        try:
            # Calculate Greeks - returns tuple of (DataFrame, results_list)
            df_with_greeks, results = self.calculator.calculate_greeks(
                self.current_data.copy()
            )
            
            return df_with_greeks
            
        except Exception as e:
            print(f"Error processing Greeks: {e}")
            return None
    
    def get_unique_expiries(self) -> List[str]:
        """Get list of unique expiry dates in current data
        
        Returns:
            List[str]: Sorted list of unique expiry dates
        """
        if self.current_data is None:
            return []
        
        # Check both uppercase and lowercase column names
        expiry_col = None
        for col in ['expiry_date', 'EXPIRY_DATE', 'Expiry_Date']:
            if col in self.current_data.columns:
                expiry_col = col
                break
        
        if expiry_col:
            expiries = self.current_data[expiry_col].dropna().unique()
            return sorted(str(e) for e in expiries)
        
        return []
    
    def get_strike_range(self) -> tuple:
        """Get min and max strike prices in current data
        
        Returns:
            tuple: (min_strike, max_strike) or (100.0, 120.0) if no data
        """
        if self.current_data is None:
            return (100.0, 120.0)
        
        # Check both uppercase and lowercase column names
        strike_col = None
        for col in ['strike', 'STRIKE', 'Strike']:
            if col in self.current_data.columns:
                strike_col = col
                break
        
        if strike_col:
            # Convert to numeric, handling invalid values
            strikes = []
            for val in self.current_data[strike_col]:
                # Skip None, INVALID, and other non-numeric values
                if val is None or str(val).upper() == 'INVALID':
                    continue
                try:
                    strike_float = float(val)
                    strikes.append(strike_float)
                except (ValueError, TypeError):
                    continue
            
            if strikes:
                return (float(min(strikes)), float(max(strikes)))
        
        # Return sensible defaults for ZN futures if no valid strikes found
        return (100.0, 120.0)
    
    def filter_data(self, 
                    expiry: Optional[str] = None,
                    option_type: Optional[str] = None,
                    strike_range: Optional[tuple] = None) -> Optional[pd.DataFrame]:
        """Filter current data based on criteria
        
        Args:
            expiry: Filter by specific expiry date
            option_type: Filter by type (All, Calls, Puts, Futures)
            strike_range: Tuple of (min_strike, max_strike)
            
        Returns:
            Optional[pd.DataFrame]: Filtered data or None if no data
        """
        if self.current_data is None:
            return None
        
        df = self.current_data.copy()
        
        # Apply expiry filter
        if expiry and expiry != "All Expiries":
            expiry_col = None
            for col in ['expiry_date', 'EXPIRY_DATE', 'Expiry_Date']:
                if col in df.columns:
                    expiry_col = col
                    break
            
            if expiry_col:
                df = df[df[expiry_col] == expiry]
        
        # Apply type filter
        if option_type and option_type != "All":
            type_col = None
            for col in ['itype', 'ITYPE', 'Type', 'type']:
                if col in df.columns:
                    type_col = col
                    break
            
            if type_col:
                if option_type == "Calls":
                    df = df[df[type_col].str.upper() == 'C']
                elif option_type == "Puts":
                    df = df[df[type_col].str.upper() == 'P']
                elif option_type == "Futures":
                    df = df[df[type_col].str.upper().isin(['F', 'FUTURE'])]
        
        # Apply strike range filter
        if strike_range:
            strike_col = None
            for col in ['strike', 'STRIKE', 'Strike']:
                if col in df.columns:
                    strike_col = col
                    break
            
            if strike_col:
                strikes = pd.to_numeric(df[strike_col], errors='coerce')
                df = df[(strikes >= strike_range[0]) & (strikes <= strike_range[1])]
        
        return df 

    def get_timestamp(self) -> str:
        """Get formatted timestamp from currently loaded data
        
        Returns:
            str: Formatted timestamp string or empty if no data
        """
        if self.data_timestamp:
            return self.data_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return '' 