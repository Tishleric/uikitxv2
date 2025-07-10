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
        
        # Read CSV, skip the type row (second row) only for original files
        # For processed files (already have headers), don't skip any rows
        if 'processed' in str(filepath):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_csv(filepath, skiprows=[1])
        
        # Normalize column names to lowercase for consistent access
        df.columns = df.columns.str.lower()
        
        # Clean numeric columns - convert to numeric, handling errors
        numeric_columns = ['strike', 'bid', 'ask', 'adjtheor']  # Added adjtheor
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate midpoint price with validation and track source
        # Initialize price_source column
        df['price_source'] = 'unknown'
        
        # Priority 1: Use adjtheor if available
        if 'adjtheor' in df.columns:
            logger.info("Using adjtheor column as primary price source")
            df['midpoint_price'] = pd.to_numeric(df['adjtheor'], errors='coerce')
            
            # Mark rows where adjtheor is valid
            adjtheor_valid_mask = df['midpoint_price'].notna()
            df.loc[adjtheor_valid_mask, 'price_source'] = 'adjtheor'
            
            # Count how many valid adjtheor prices we have
            adjtheor_valid = adjtheor_valid_mask.sum()
            logger.info(f"Found {adjtheor_valid} valid adjtheor prices out of {len(df)} rows")
            
            # For rows where adjtheor is missing, calculate midpoint from bid/ask
            adjtheor_missing = df['midpoint_price'].isna()
            if adjtheor_missing.any() == True and 'bid' in df.columns and 'ask' in df.columns:
                logger.info(f"Calculating midpoint for {adjtheor_missing.sum()} rows with missing adjtheor")
                calculated_midpoint = (df.loc[adjtheor_missing, 'bid'] + df.loc[adjtheor_missing, 'ask']) / 2
                valid_calc = calculated_midpoint.notna()
                df.loc[adjtheor_missing & valid_calc, 'midpoint_price'] = calculated_midpoint[valid_calc]
                df.loc[adjtheor_missing & valid_calc, 'price_source'] = 'calculated'
        
        # Priority 2: Calculate from bid/ask if adjtheor not available
        elif 'bid' in df.columns and 'ask' in df.columns:
            # Calculate midpoint where both bid and ask are valid
            df['midpoint_price'] = (df['bid'] + df['ask']) / 2
            
            # Mark rows where calculation worked
            calculated_mask = df['midpoint_price'].notna()
            df.loc[calculated_mask, 'price_source'] = 'calculated'
            
            # Count rows with missing midpoint prices
            missing_midpoint = df['midpoint_price'].isna()
            if bool(missing_midpoint.any()):
                missing_count = missing_midpoint.sum()
                logger.warning(f"Found {missing_count} rows with missing midpoint prices")
                
                # For rows with missing midpoint, try alternative sources
                # 1. If only bid is missing, use ask
                bid_missing = df['bid'].isna()
                ask_valid = df['ask'].notna()
                use_ask_mask = missing_midpoint & bid_missing & ask_valid
                df.loc[use_ask_mask, 'midpoint_price'] = df.loc[use_ask_mask, 'ask']
                df.loc[use_ask_mask, 'price_source'] = 'ask_only'
                
                # 2. If only ask is missing, use bid
                ask_missing = df['ask'].isna()
                bid_valid = df['bid'].notna()
                use_bid_mask = missing_midpoint & ask_missing & bid_valid
                df.loc[use_bid_mask, 'midpoint_price'] = df.loc[use_bid_mask, 'bid']
                df.loc[use_bid_mask, 'price_source'] = 'bid_only'
                
                # 3. Check if there's a 'price' or 'last' column as fallback
                fallback_columns = ['price', 'last', 'settle', 'close']
                for fallback_col in fallback_columns:
                    if fallback_col in df.columns:
                        # Use fallback where midpoint is still missing
                        still_missing = df['midpoint_price'].isna()
                        fallback_values = pd.to_numeric(df.loc[still_missing, fallback_col], errors='coerce')
                        # Check if we got valid values from the fallback column
                        if isinstance(fallback_values, pd.Series):
                            valid_fallback_mask = fallback_values.notna()
                            df.loc[still_missing & valid_fallback_mask, 'midpoint_price'] = fallback_values[valid_fallback_mask]
                            df.loc[still_missing & valid_fallback_mask, 'price_source'] = f'fallback_{fallback_col}'
                            filled_count = (still_missing & valid_fallback_mask).sum()
                        else:
                            filled_count = 0
                        
                        if filled_count > 0:
                            logger.info(f"Used {fallback_col} column to fill {filled_count} missing midpoint prices")
                
                # Log final status
                final_missing = df['midpoint_price'].isna().sum()
                if final_missing > 0:
                    logger.error(f"Still have {final_missing} rows with no valid price data")
                    # Log sample of problematic rows for debugging
                    sample_missing = df[df['midpoint_price'].isna()].head(5)
                    if not sample_missing.empty:
                        debug_cols = [col for col in ['key', 'bid', 'ask'] if col in sample_missing.columns]
                        if debug_cols:
                            logger.debug(f"Sample rows with missing prices:\n{sample_missing[debug_cols]}")
        else:
            logger.warning("bid or ask columns not found, looking for alternative price columns")
            # Try to find any price column
            price_columns = ['price', 'last', 'midpoint', 'settle', 'close']
            for col in price_columns:
                if col in df.columns:
                    df['midpoint_price'] = pd.to_numeric(df[col], errors='coerce')
                    valid_prices = df['midpoint_price'].notna()
                    df.loc[valid_prices, 'price_source'] = f'fallback_{col}'
                    logger.info(f"Using {col} column as midpoint_price for {valid_prices.sum()} rows")
                    break
            else:
                logger.error("No valid price columns found in CSV")
                
        # Mark any remaining rows without prices as 'missing'
        missing_prices = df['midpoint_price'].isna()
        df.loc[missing_prices, 'price_source'] = 'missing'
            
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