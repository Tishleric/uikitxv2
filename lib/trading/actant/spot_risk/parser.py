"""Parser for Actant spot risk CSV files."""

import re
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, Any
import logging

logger = logging.getLogger(__name__)


def extract_datetime_from_filename(filename: Union[str, Path]) -> datetime:
    """
    Extract datetime from filename format: bav_analysis_YYYYMMDD_HHMMSS.csv
    
    Args:
        filename: Path or string of the CSV filename
        
    Returns:
        datetime object parsed from filename
        
    Raises:
        ValueError: If datetime cannot be parsed from filename
    """
    try:
        # Convert to string if Path object
        filename_str = str(filename)
        
        # Extract just the filename without path
        if '/' in filename_str or '\\' in filename_str:
            filename_str = Path(filename_str).name
            
        # Pattern: bav_analysis_YYYYMMDD_HHMMSS.csv
        pattern = r'bav_analysis_(\d{8})_(\d{6})\.csv'
        match = re.search(pattern, filename_str)
        
        if not match:
            raise ValueError(f"Could not extract datetime from filename: {filename_str}")
            
        date_str = match.group(1)  # YYYYMMDD
        time_str = match.group(2)  # HHMMSS
        
        # Parse datetime
        dt = datetime.strptime(date_str + time_str, '%Y%m%d%H%M%S')
        return dt
        
    except Exception as e:
        logger.error(f"Error parsing datetime from filename {filename}: {e}")
        raise ValueError(f"Failed to parse datetime from filename: {filename}") from e


def parse_expiry_from_key(key: Any) -> Optional[str]:
    """
    Extract expiry information from instrument key.
    
    Args:
        key: Instrument key (any type, but expects string)
        
    Returns:
        Expiry string (e.g., 'SEP25', '16JUL25') or None if not parseable
    """
    try:
        if not key or not isinstance(key, str):
            return None
            
        parts = key.split('.')
        
        # Future format: XCME.ZN.SEP25
        if len(parts) == 3:
            return parts[2]  # Return month-year (e.g., 'SEP25')
            
        # Option format: XCME.WY3.16JUL25.111.C or similar
        if len(parts) >= 4:
            # The expiry is typically the third part
            return parts[2]  # Return date-month-year (e.g., '16JUL25')
            
        logger.debug(f"Could not parse expiry from key: {key}")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing expiry from key {key}: {e}")
        return None


def parse_spot_risk_csv(filepath: Union[str, Path], calculate_time_to_expiry: bool = False) -> pd.DataFrame:
    """
    Parse Actant spot risk CSV file and prepare DataFrame.
    
    Args:
        filepath: Path to the CSV file
        calculate_time_to_expiry: Whether to calculate vtexp column
        
    Returns:
        Sorted DataFrame with added columns:
        - midpoint_price: (bid + ask) / 2
        - expiry_date: Parsed from instrument key
        - vtexp: Time to expiry in years (if calculate_time_to_expiry=True)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
            
        logger.info(f"Reading CSV file: {filepath}")
        
        # Read CSV, skip the type row (second row)
        df = pd.read_csv(filepath, skiprows=[1])
        
        # Normalize column names to lowercase for consistent access
        df.columns = df.columns.str.lower()
        
        # Clean numeric columns - convert to numeric, handling errors
        numeric_columns = ['strike', 'bid', 'ask']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate midpoint price
        if 'bid' in df.columns and 'ask' in df.columns:
            df['midpoint_price'] = (df['bid'] + df['ask']) / 2
        else:
            logger.warning("bid or ask columns not found, cannot calculate midpoint_price")
            
        # Extract expiry dates
        if 'key' in df.columns:
            df['expiry_date'] = df['key'].apply(parse_expiry_from_key)
        else:
            logger.warning("key column not found, cannot extract expiry_date")
            
        # Sort DataFrame
        # Priority: instrument type (futures first), then expiry, then strike (for options)
        sort_columns = []
        
        if 'itype' in df.columns:
            # Create a custom sort key for itype to ensure futures come first
            # Handle both full names and abbreviations
            itype_sort_map = {
                'future': 0, 'f': 0,  # Future variations
                'call': 1, 'c': 1,    # Call variations
                'put': 2, 'p': 2      # Put variations
            }
            df['_sort_itype'] = df['itype'].str.lower().map(lambda x: itype_sort_map.get(x, 3))
            sort_columns.append('_sort_itype')
        if 'expiry_date' in df.columns:
            sort_columns.append('expiry_date')
        if 'strike' in df.columns:
            sort_columns.append('strike')
            
        if sort_columns:
            df = df.sort_values(by=sort_columns)
            # Drop the temporary sort column
            if '_sort_itype' in df.columns:
                df = df.drop(columns=['_sort_itype'])
            
        # Reset index after sorting
        df = df.reset_index(drop=True)
        
        # Calculate time to expiry if requested
        if calculate_time_to_expiry:
            from .time_calculator import calculate_vtexp_for_dataframe
            
            # Extract timestamp from filename
            csv_timestamp = extract_datetime_from_filename(filepath)
            
            # Calculate vtexp
            df = calculate_vtexp_for_dataframe(df, csv_timestamp)
            logger.info(f"Calculated vtexp for {df['vtexp'].notna().sum()} options")
        
        logger.info(f"Successfully parsed {len(df)} rows from {filepath.name}")
        
        return df
        
    except pd.errors.EmptyDataError:
        logger.error(f"Empty CSV file: {filepath}")
        raise ValueError(f"CSV file is empty: {filepath}")
    except Exception as e:
        logger.error(f"Error parsing CSV file {filepath}: {e}")
        raise 