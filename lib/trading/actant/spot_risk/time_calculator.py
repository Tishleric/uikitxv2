"""Time to expiry calculator for spot risk options."""

import re
import os
import csv
import logging
from datetime import datetime
from typing import Dict, Optional
import pandas as pd
import pytz

from lib.trading.bond_future_options.bachelier import time_to_expiry_years

logger = logging.getLogger(__name__)

# CME expiry time conventions
SERIES_TIME_MAP = {
    'VY': (14, 0),  # Monday 2:00 PM
    'WY': (14, 0),  # Wednesday 2:00 PM
    'ZN': (16, 30)  # Friday 4:30 PM
}

# Month name to number mapping
MONTH_MAP = {
    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
}

CT_ZONE = pytz.timezone("America/Chicago")


def parse_series_from_key(key: str) -> Optional[str]:
    """
    Extract series code from instrument key.
    
    Args:
        key: Instrument key (e.g., "XCME.WY3.16JUL25.111.C")
        
    Returns:
        Series code (VY, WY, ZN) or None
    """
    parts = key.split('.')
    if len(parts) >= 2:
        # Extract first two letters of second part
        series_part = parts[1]
        if len(series_part) >= 2:
            return series_part[:2]
    return None


def parse_expiry_date_full(expiry_str: str) -> Optional[datetime]:
    """
    Parse expiry date string to datetime (date only).
    
    Args:
        expiry_str: Expiry string (e.g., "16JUL25")
        
    Returns:
        datetime object or None
    """
    if not expiry_str:
        return None
        
    try:
        # Pattern: DDMMMYY (e.g., "16JUL25")
        pattern = r'^(\d{1,2})([A-Z]{3})(\d{2})$'
        match = re.match(pattern, expiry_str)
        
        if match:
            day = int(match.group(1))
            month_str = match.group(2)
            year = int(match.group(3)) + 2000  # Convert YY to YYYY
            
            if month_str in MONTH_MAP:
                month = MONTH_MAP[month_str]
                return datetime(year, month, day)
    except:
        pass
        
    return None


def build_expiry_datetime(expiry_str: str, series_code: str) -> Optional[datetime]:
    """
    Build full expiry datetime with CME time conventions.
    
    Args:
        expiry_str: Expiry date string (e.g., "16JUL25")
        series_code: Series code (VY, WY, ZN)
        
    Returns:
        Full datetime with appropriate expiry time in CT
    """
    date = parse_expiry_date_full(expiry_str)
    if not date or series_code not in SERIES_TIME_MAP:
        return None
        
    hour, minute = SERIES_TIME_MAP[series_code]
    
    # Create datetime with Chicago timezone
    expiry_dt = CT_ZONE.localize(datetime(
        date.year, date.month, date.day, hour, minute
    ))
    
    return expiry_dt


def calculate_vtexp_for_dataframe(df: pd.DataFrame, csv_timestamp: datetime) -> pd.DataFrame:
    """
    Calculate vtexp (time to expiry in years) for all options in dataframe.
    
    Args:
        df: DataFrame with 'key' and 'expiry_date' columns
        csv_timestamp: Evaluation datetime from CSV filename
        
    Returns:
        DataFrame with added 'vtexp' column
    """
    # Ensure CSV timestamp is timezone aware
    if csv_timestamp.tzinfo is None:
        csv_timestamp = CT_ZONE.localize(csv_timestamp)
    
    # Build map of unique expiry -> vtexp
    vtexp_map = {}
    
    # Process each unique expiry
    for idx, row in df.iterrows():
        key = str(row['key'])
        expiry_str = str(row['expiry_date'])
        itype = str(row['itype'])
        
        # Skip futures and non-tradeable
        if itype not in ['C', 'P'] or not expiry_str or expiry_str == 'nan':
            continue
            
        # Use expiry_str as cache key
        if expiry_str not in vtexp_map:
            series_code = parse_series_from_key(key)
            if series_code:
                expiry_dt = build_expiry_datetime(expiry_str, series_code)
                if expiry_dt:
                    # Format for bachelier: "YYYYMMDD HH:MM"
                    expiry_formatted = expiry_dt.strftime("%Y%m%d %H:%M")
                    vtexp = time_to_expiry_years(expiry_formatted, csv_timestamp)
                    vtexp_map[expiry_str] = vtexp
    
    # Map vtexp to dataframe
    df['vtexp'] = df.apply(
        lambda row: vtexp_map.get(row['expiry_date']) if row['itype'] in ['C', 'P'] else None,
        axis=1
    )
    
    return df


def read_vtexp_from_csv(vtexp_dir: str = "data/input/vtexp") -> Dict[str, float]:
    """
    Read vtexp values from the most recent CSV file in the vtexp directory.
    
    Args:
        vtexp_dir: Directory containing vtexp CSV files
        
    Returns:
        Dictionary mapping symbol to vtexp value
    """
    # Find all vtexp CSV files
    vtexp_files = []
    if os.path.exists(vtexp_dir):
        for filename in os.listdir(vtexp_dir):
            if filename.startswith("vtexp_") and filename.endswith(".csv"):
                vtexp_files.append(os.path.join(vtexp_dir, filename))
    
    if not vtexp_files:
        raise FileNotFoundError(f"No vtexp CSV files found in {vtexp_dir}")
    
    # Sort by filename to get most recent (files are named vtexp_YYYYMMDD_HHMMSS.csv)
    vtexp_files.sort()
    most_recent_file = vtexp_files[-1]
    logger.info(f"Reading vtexp values from: {most_recent_file}")
    
    # Read the CSV file
    vtexp_map = {}
    with open(most_recent_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row['symbol']
            # Convert from days to years (252 trading days per year)
            vtexp = float(row['vtexp']) / 252
            vtexp_map[symbol] = vtexp
    
    logger.info(f"Loaded {len(vtexp_map)} vtexp values from CSV")
    return vtexp_map


def load_vtexp_for_dataframe(df: pd.DataFrame, 
                              csv_timestamp: datetime, 
                              vtexp_data: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """
    Load vtexp values and map to dataframe.
    Uses pre-loaded vtexp_data if provided, otherwise reads from CSV.
    
    Args:
        df: DataFrame with 'key' column containing instrument symbols
        csv_timestamp: Evaluation datetime (kept for API compatibility)
        vtexp_data: Pre-loaded dictionary of {expiry_code: vtexp_value}
        
    Returns:
        DataFrame with added 'vtexp' column
    """
    if vtexp_data:
        logger.info("Using pre-loaded vtexp data from cache.")
        vtexp_base_map = vtexp_data
    else:
        logger.warning("No vtexp cache provided. Falling back to reading from CSV.")
        vtexp_base_map = read_vtexp_from_csv()
    
    # Import the mapper
    from .vtexp_mapper import VtexpSymbolMapper
    mapper = VtexpSymbolMapper()
    
    # Get option symbols from dataframe
    option_mask = df['itype'].isin(['C', 'P'])
    option_symbols = df.loc[option_mask, 'key'].tolist()
    
    # Create mapping from spot risk symbols to vtexp values
    vtexp_map = mapper.create_mapping_dict(option_symbols, vtexp_base_map)
    
    # Log sample of keys for debugging
    if len(option_symbols) > 0:
        sample_keys = option_symbols[:3]
        logger.debug(f"Sample option keys from dataframe: {sample_keys}")
    sample_vtexp_keys = list(vtexp_base_map.keys())[:3]
    logger.debug(f"Sample keys from vtexp CSV: {sample_vtexp_keys}")
    
    # Map vtexp to dataframe based on converted symbols
    df['vtexp'] = df.apply(
        lambda row: vtexp_map.get(row['key']) if row['itype'] in ['C', 'P'] else None,
        axis=1
    )
    
    # Log how many matches we found
    matched_count = df['vtexp'].notna().sum()
    options_count = df[df['itype'].isin(['C', 'P'])].shape[0]
    logger.info(f"Matched vtexp values for {matched_count} out of {options_count} options")
    
    return df 