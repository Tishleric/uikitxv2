"""Time to expiry calculator for spot risk options."""

import re
from datetime import datetime
from typing import Dict, Optional
import pandas as pd
import pytz

from lib.trading.bond_future_options.bachelier import time_to_expiry_years

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
        key = row['key']
        expiry_str = row['expiry_date']
        itype = row['itype']
        
        # Skip futures and non-tradeable
        if itype not in ['C', 'P'] or not expiry_str:
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