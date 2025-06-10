"""
CSV Parser Module for Actant Option Data

This module handles parsing of Actant CSV files containing option greeks
and prices across multiple expirations and strike offsets.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass

from pnl_calculations import OptionGreeks


@dataclass
class ActantDataFile:
    """Metadata for an Actant data file."""
    filepath: Path
    symbol: str
    timestamp: datetime
    
    @classmethod
    def from_filename(cls, filepath: Path) -> 'ActantDataFile':
        """
        Parse filename format: GE_XCME.ZN_20250610_103938.csv
        """
        pattern = r'GE_(.+)_(\d{8})_(\d{6})\.csv'
        match = re.match(pattern, filepath.name)
        
        if not match:
            raise ValueError(f"Invalid filename format: {filepath.name}")
            
        symbol = match.group(1)
        date_str = match.group(2)
        time_str = match.group(3)
        
        # Parse timestamp
        timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        
        return cls(filepath=filepath, symbol=symbol, timestamp=timestamp)


class ActantCSVParser:
    """Parse Actant CSV files containing option data."""
    
    # Expected value types (rows) in the CSV
    EXPECTED_VALUES = [
        'ab_sDeltaPathCallPct',
        'ab_sDeltaPathPutPct',
        'ab_sDeltaPathDV01Call',
        'ab_sDeltaPathDV01Put',
        'ab_sGammaPathDV01',
        'ab_VegaDV01',
        'ab_Theta',
        'ab_F',
        'ab_K',
        'ab_R',
        'ab_T',
        'ab_Vol',
        'ab_sCall',
        'ab_sPut'
    ]
    
    def __init__(self, shock_multiplier: float = 16.0):
        """
        Initialize parser.
        
        Args:
            shock_multiplier: Multiplier to convert shock units to basis points
                             (default: 1 shock unit = 16 bp)
        """
        self.shock_multiplier = shock_multiplier
    
    def parse_file(self, filepath: Path) -> pd.DataFrame:
        """
        Read and validate CSV file.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            DataFrame with parsed data
        """
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")
            
        # Read CSV
        df = pd.read_csv(filepath)
        
        # Validate structure
        self._validate_dataframe(df)
        
        return df
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate DataFrame structure."""
        # Check required columns exist
        required_cols = ['Expiration', 'Value', 'UPrice']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Check that we have shock columns
        shock_cols = [col for col in df.columns if col not in required_cols]
        if len(shock_cols) < 5:
            raise ValueError("Insufficient shock columns in data")
    
    def get_expirations(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of unique expirations in the data.
        
        Args:
            df: Parsed DataFrame
            
        Returns:
            List of expiration identifiers
        """
        expirations = df['Expiration'].unique()
        # Filter out 'w/o first' and keep only valid expirations
        valid_expirations = []
        for exp in expirations:
            if exp == 'w/o first':
                continue
            # Check if this expiration has actual data (non-zero values)
            exp_data = df[df['Expiration'] == exp]
            if not exp_data.empty:
                # Check if we have call prices (look for 'ab_sCall' in Value column)
                has_call_data = 'ab_sCall' in exp_data['Value'].values
                if has_call_data:
                    # Get the call price row and check if it has non-zero values
                    call_row = exp_data[exp_data['Value'] == 'ab_sCall'].iloc[0, 3:]
                    if not call_row.isna().all() and (call_row != 0).any():
                        valid_expirations.append(exp)
        
        return valid_expirations
    
    def extract_shock_values(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract shock values from column headers.
        
        Args:
            df: Parsed DataFrame
            
        Returns:
            Array of shock values in basis points
        """
        # Get shock columns (skip first 3: Expiration, Value, UPrice)
        shock_columns = df.columns[3:]
        shocks = np.array([float(col) for col in shock_columns])
        
        # Convert to basis points
        return shocks * self.shock_multiplier
    
    def parse_to_greeks(self, df: pd.DataFrame, expiration: str) -> OptionGreeks:
        """
        Parse DataFrame into OptionGreeks object for specific expiration.
        
        Args:
            df: Parsed DataFrame
            expiration: Expiration identifier
            
        Returns:
            OptionGreeks object
        """
        # Filter for specific expiration
        exp_data = df[df['Expiration'] == expiration].copy()
        
        if exp_data.empty:
            raise ValueError(f"No data found for expiration: {expiration}")
        
        # Extract shock values
        shocks = self.extract_shock_values(df)
        
        # Helper to get row values
        def get_row_values(value_name: str) -> np.ndarray:
            row = exp_data[exp_data['Value'] == value_name]
            if row.empty:
                raise ValueError(f"Value '{value_name}' not found for expiration '{expiration}'")
            # Get values starting from column 3 (skip Expiration, Value, UPrice)
            return row.iloc[0, 3:].values.astype(float)
        
        # Extract underlying price
        underlying_price = float(exp_data.iloc[0]['UPrice'])
        
        # Create OptionGreeks object
        greeks = OptionGreeks(
            shocks=shocks,
            call_prices=get_row_values('ab_sCall'),
            put_prices=get_row_values('ab_sPut'),
            call_delta_dv01=get_row_values('ab_sDeltaPathDV01Call'),
            put_delta_dv01=get_row_values('ab_sDeltaPathDV01Put'),
            gamma_dv01=get_row_values('ab_sGammaPathDV01'),
            vega_dv01=get_row_values('ab_VegaDV01'),
            theta=get_row_values('ab_Theta'),
            forward=get_row_values('ab_F')[0],
            strike=get_row_values('ab_K')[0],
            time_to_expiry=get_row_values('ab_T')[0],
            underlying_price=underlying_price
        )
        
        return greeks
    
    def parse_all_expirations(self, df: pd.DataFrame) -> Dict[str, OptionGreeks]:
        """
        Parse all expirations into dictionary of OptionGreeks.
        
        Args:
            df: Parsed DataFrame
            
        Returns:
            Dictionary mapping expiration to OptionGreeks
        """
        results = {}
        expirations = self.get_expirations(df)
        
        for exp in expirations:
            try:
                results[exp] = self.parse_to_greeks(df, exp)
            except ValueError as e:
                print(f"Warning: Skipping expiration {exp}: {e}")
                
        return results


class ActantFileMonitor:
    """Monitor directory for latest Actant CSV files."""
    
    def __init__(self, watch_dir: Path):
        """
        Initialize file monitor.
        
        Args:
            watch_dir: Directory to monitor for CSV files
        """
        self.watch_dir = Path(watch_dir)
        if not self.watch_dir.exists():
            raise ValueError(f"Watch directory does not exist: {watch_dir}")
    
    def get_latest_file(self, symbol: Optional[str] = None) -> Optional[ActantDataFile]:
        """
        Get the most recent CSV file.
        
        Args:
            symbol: Optional symbol filter (e.g., 'XCME.ZN')
            
        Returns:
            ActantDataFile object or None if no files found
        """
        # Find all CSV files
        csv_files = list(self.watch_dir.glob("GE_*.csv"))
        
        if not csv_files:
            return None
        
        # Parse filenames
        data_files = []
        for filepath in csv_files:
            try:
                data_file = ActantDataFile.from_filename(filepath)
                if symbol is None or data_file.symbol == symbol:
                    data_files.append(data_file)
            except ValueError:
                continue
        
        if not data_files:
            return None
        
        # Return most recent
        return max(data_files, key=lambda f: f.timestamp)
    
    def get_files_since(self, since_timestamp: datetime, 
                       symbol: Optional[str] = None) -> List[ActantDataFile]:
        """
        Get all files since a given timestamp.
        
        Args:
            since_timestamp: Timestamp cutoff
            symbol: Optional symbol filter
            
        Returns:
            List of ActantDataFile objects
        """
        csv_files = list(self.watch_dir.glob("GE_*.csv"))
        
        data_files = []
        for filepath in csv_files:
            try:
                data_file = ActantDataFile.from_filename(filepath)
                if (data_file.timestamp > since_timestamp and 
                    (symbol is None or data_file.symbol == symbol)):
                    data_files.append(data_file)
            except ValueError:
                continue
        
        return sorted(data_files, key=lambda f: f.timestamp)


# Convenience function
def load_latest_data(watch_dir: Path, symbol: Optional[str] = None,
                    expiration: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, OptionGreeks]]:
    """
    Load latest data file and parse into OptionGreeks.
    
    Args:
        watch_dir: Directory containing CSV files
        symbol: Optional symbol filter
        expiration: Optional specific expiration to parse
        
    Returns:
        Tuple of (raw DataFrame, dictionary of OptionGreeks by expiration)
    """
    monitor = ActantFileMonitor(watch_dir)
    latest_file = monitor.get_latest_file(symbol)
    
    if not latest_file:
        raise FileNotFoundError(f"No Actant CSV files found in {watch_dir}")
    
    parser = ActantCSVParser()
    df = parser.parse_file(latest_file.filepath)
    
    if expiration:
        # Parse only specific expiration
        greeks = parser.parse_to_greeks(df, expiration)
        return df, {expiration: greeks}
    else:
        # Parse all expirations
        all_greeks = parser.parse_all_expirations(df)
        return df, all_greeks 