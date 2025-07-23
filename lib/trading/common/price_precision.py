"""
Price Precision Utilities

Handles rounding of price data to exactly 6 decimal places for FULLPNL table.
All other tables maintain original precision from source data.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union, Optional
import pandas as pd
import numpy as np


def round_price_to_6dp(value: Union[float, int, str, None]) -> Optional[float]:
    """
    Round a price value to exactly 6 decimal places.
    
    Only rounds values that need it - if source has more precision, it's preserved
    elsewhere in the system. This function is ONLY for FULLPNL table insertion.
    
    Args:
        value: Price value to round (can be float, int, string, or None)
        
    Returns:
        Rounded float value with 6 decimal places, or None if input is None/NaN
    """
    if value is None:
        return None
        
    # Handle pandas/numpy NaN
    if isinstance(value, (float, np.floating)) and (pd.isna(value) or np.isnan(value)):
        return None
        
    # Handle string values like "awaiting data"
    if isinstance(value, str):
        try:
            value = float(value)
        except (ValueError, TypeError):
            return None
    
    try:
        # Use Decimal for precise rounding
        decimal_value = Decimal(str(value))
        # Round to 6 decimal places using banker's rounding
        rounded = decimal_value.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        return float(rounded)
    except (ValueError, TypeError, InvalidOperation):
        return None


def round_dataframe_prices(df: pd.DataFrame, price_columns: list) -> pd.DataFrame:
    """
    Round specified price columns in a DataFrame to 6 decimal places.
    
    This creates a copy of the DataFrame and only modifies the specified columns.
    Used specifically for FULLPNL table preparation.
    
    Args:
        df: Input DataFrame
        price_columns: List of column names containing price data
        
    Returns:
        New DataFrame with rounded price columns
    """
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    for col in price_columns:
        if col in result_df.columns:
            # Apply rounding to each value in the column
            result_df[col] = result_df[col].apply(round_price_to_6dp)
        else:
            # Log warning if column doesn't exist
            import logging
            logging.warning(f"Price column '{col}' not found in DataFrame")
    
    return result_df


# List of price columns in FULLPNL table that should be rounded
FULLPNL_PRICE_COLUMNS = [
    'avg_entry_price',
    'current_price', 
    'flash_close',
    'prior_close',
    'current_present_value',
    'prior_present_value',
    'unrealized_pnl_current',
    'unrealized_pnl_flash',
    'unrealized_pnl_close',
    'realized_pnl',
    'daily_pnl',
    'total_pnl',
    # Greeks that are price-related
    'vtexp',
    'delta_f',
    'gamma_f', 
    'speed_f',
    'theta_f',
    'vega_f',
    'dv01_y',
    'delta_y',
    'gamma_y',
    'speed_y',
    'theta_y',
    'vega_y'
] 