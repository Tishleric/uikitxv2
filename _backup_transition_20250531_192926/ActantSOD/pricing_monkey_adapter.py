"""
Pricing Monkey to Actant adapter module.

This module transforms Pricing Monkey DataFrame output into the format
expected by actant.py, including price conversions and contract mapping.
"""

import pandas as pd
import logging
import datetime

logger = logging.getLogger(__name__)


def parse_pm_expiry_date(date_input):
    """
    Parse Pricing Monkey expiry date into MM/DD/YYYY format.
    
    Handles various PM date formats including "21-May-2025 14:00 Chicago".
    
    Args:
        date_input: A date representation (datetime, string, etc.).
        
    Returns:
        str: Formatted date string (MM/DD/YYYY) or empty string if invalid.
    """
    if pd.isna(date_input) or date_input == "":
        return ""
    
    try:
        # Convert to datetime if it's a string
        if isinstance(date_input, str):
            date_input = date_input.strip()
            
            # Handle PM format like "21-May-2025 14:00 Chicago"
            if "Chicago" in date_input:
                parts = date_input.split()
                if len(parts) >= 2:
                    date_part = parts[0]  # Extract just the date part
                    try:
                        # Try to parse with explicit format
                        date_obj = datetime.datetime.strptime(date_part, "%d-%b-%Y").date()
                        return date_obj.strftime('%m/%d/%Y')
                    except ValueError:
                        pass
            
            # Try different formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%d %b %Y']:
                try:
                    date_obj = datetime.datetime.strptime(date_input, fmt).date()
                    return date_obj.strftime('%m/%d/%Y')
                except ValueError:
                    continue
            
            # If none of the above formats worked, try pandas as fallback
            try:
                date_obj = pd.to_datetime(date_input, errors='coerce')
                if not pd.isna(date_obj):
                    return date_obj.strftime('%m/%d/%Y')
            except:
                pass
            
            logger.warning(f"Failed to parse expiry date: '{date_input}'")
            return ""
            
        # If it's already a datetime or pandas Timestamp
        elif isinstance(date_input, (datetime.date, datetime.datetime, pd.Timestamp)):
            return date_input.strftime('%m/%d/%Y')
        
        return ""
    except Exception as e:
        logger.warning(f"Error parsing expiry date {date_input}: {str(e)}")
        return ""


def interpret_pm_ordinal_to_index(pm_ordinal: str, pm_shift_needed: bool = False) -> int:
    """
    Convert PM ordinal to actual expiry index accounting for PM lag.
    
    Args:
        pm_ordinal: "1st", "2nd", "3rd", etc. from PM
        pm_shift_needed: Whether PM is lagging (post-3PM on expiry day)
        
    Returns:
        int: Actual expiry index (0, 1, 2 for 1st, 2nd, 3rd real expiry)
             Returns -1 if ordinal is invalid/out of range
    """
    # Extract numeric part from ordinal
    ordinal_map = {'1st': 0, '2nd': 1, '3rd': 2, '4th': 3, '5th': 4, '6th': 5, '7th': 6}
    
    if pm_ordinal not in ordinal_map:
        logger.warning(f"Invalid PM ordinal: '{pm_ordinal}'")
        return -1
    
    pm_index = ordinal_map[pm_ordinal]
    
    # If PM is lagging (post-3PM), their "2nd" is actually our "1st"
    if pm_shift_needed:
        actual_index = pm_index - 1
    else:
        actual_index = pm_index
    
    # Validate range (we only support 3 expiries: 0, 1, 2)
    if actual_index < 0 or actual_index > 2:
        logger.warning(f"PM ordinal '{pm_ordinal}' maps to out-of-range index {actual_index}")
        return -1
    
    return actual_index


def convert_handle_tick_to_decimal(price_str: str, instrument_type: str = "future") -> float:
    """
    Convert handle-tick price format to decimal.
    
    Examples:
        Futures (32nds): "110-04.25" → 110 + 4.25/32 = 110.1328125
        Options (64ths): "0-06.1" → 0 + 6.1/64 = 0.095625
        Decimal: "129.61" → 129.61 (already decimal)
    
    Args:
        price_str (str): Price in handle-tick or decimal format
        instrument_type (str): "future" (32nds) or "option" (64ths)
        
    Returns:
        float: Decimal price
    """
    if pd.isna(price_str) or price_str == "":
        return None
    
    price_str = str(price_str).strip()
    
    # If it's already a decimal number, return it
    try:
        return float(price_str)
    except ValueError:
        pass
    
    # Handle-tick format (110-04.25 or 0-00.5)
    if '-' in price_str:
        try:
            parts = price_str.split('-')
            handle = float(parts[0])
            
            # Handle the tick part which may have decimals
            tick_part = parts[1]
            if '.' in tick_part:
                tick_whole, tick_frac = tick_part.split('.')
                ticks = float(tick_whole) + float('0.' + tick_frac)
            else:
                ticks = float(tick_part)
            
            # Convert to decimal: 32nds for futures, 64ths for options
            divisor = 32.0 if instrument_type == "future" else 64.0
            return handle + ticks / divisor
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing handle-tick price '{price_str}': {e}")
            return None
    
    logger.warning(f"Unrecognized price format: '{price_str}'")
    return None


def map_pm_description_to_underlying(description: str) -> str:
    """
    Map Pricing Monkey trade description to underlying contract symbol.
    
    Args:
        description (str): Trade description from Pricing Monkey
        
    Returns:
        str: Underlying contract symbol (ZB, ZN, ZF, ZT, FGBL) or None if not found
    """
    if not isinstance(description, str):
        return None
    
    desc_upper = description.upper()
    
    # Direct contract mappings
    if desc_upper.startswith("TY"):
        return "ZN"
    elif desc_upper.startswith("RX"):
        return "FGBL"
    elif desc_upper.startswith("TU"):
        return "ZT"
    elif desc_upper.startswith("FV"):
        return "ZF"
    elif desc_upper.startswith("US"):
        return "ZB"
    elif "10Y NOTE" in desc_upper:
        return "ZN"
    
    return None



def extract_trade_data_from_pm(pm_df: pd.DataFrame) -> list[dict]:
    """
    Transform Pricing Monkey DataFrame into actant.py trade_data format.
    
    Args:
        pm_df (pd.DataFrame): Pricing Monkey DataFrame with columns:
                              'Trade Amount', 'Trade Description', 'Strike', 'Expiry Date', 'Price'
        
    Returns:
        list[dict]: List of trade dictionaries in actant.py format with Strike and Price
    """
    trade_data = []
    
    if pm_df.empty:
        logger.warning("Empty Pricing Monkey DataFrame provided")
        return trade_data
    
    required_columns = ['Trade Amount', 'Trade Description']
    missing_columns = [col for col in required_columns if col not in pm_df.columns]
    if missing_columns:
        logger.error(f"Missing required columns in PM DataFrame: {missing_columns}")
        return trade_data
    
    skipped_count = 0
    for _, row in pm_df.iterrows():
        # Skip rows with missing essential data
        if pd.isna(row['Trade Amount']) or pd.isna(row['Trade Description']):
            logger.debug(f"Skipping row with missing data: {row.to_dict()}")
            skipped_count += 1
            continue
        
        # Keep original trade description - no more complex transformations
        trade_description = str(row['Trade Description']).strip()
        
        # ENHANCED: Include Strike, Price, and Expiry Date from PM data
        trade_dict = {
            "Trade Description": trade_description,
            "Trade Amount": int(row['Trade Amount']),
            "Strike": str(row.get('Strike', '')) if not pd.isna(row.get('Strike', '')) else '',
            "Price": str(row.get('Price', '')) if not pd.isna(row.get('Price', '')) else '',
            "Expiry Date": str(row.get('Expiry Date', '')) if not pd.isna(row.get('Expiry Date', '')) else ''
        }
        
        trade_data.append(trade_dict)
        logger.debug(f"Converted trade: {trade_dict}")
    
    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} trades due to missing data or out-of-range ordinals")
    
    logger.info(f"Extracted {len(trade_data)} trades from Pricing Monkey data")
    return trade_data


if __name__ == "__main__":
    # Test the adapter functions
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    # Test price conversion
    test_prices = ["110-04.25", "0-00.5", "129.61", "107-15"]
    print("Testing price conversions:")
    for price in test_prices:
        decimal = convert_handle_tick_to_decimal(price)
        print(f"  {price} → {decimal}")
    
    # Test description mapping
    test_descriptions = ["TYM5", "1st 10y note 25 out put", "RXM5"]
    print("\nTesting description mapping:")
    for desc in test_descriptions:
        underlying = map_pm_description_to_underlying(desc)
        print(f"  '{desc}' → {underlying}")
    
    # Test ordinal interpretation
    print("\nTesting ordinal interpretation:")
    test_ordinals = ["1st", "2nd", "3rd", "4th"]
    for ordinal in test_ordinals:
        index_normal = interpret_pm_ordinal_to_index(ordinal, False)
        index_shifted = interpret_pm_ordinal_to_index(ordinal, True)
        print(f"  '{ordinal}' → normal: {index_normal}, post-3PM: {index_shifted}")
    
    # Test expiry date parsing
    print("\nTesting expiry date parsing:")
    test_dates = ["18-Jun-2025 14:00 Chicago", "2025-06-18", "06/18/2025", "", "invalid-date"]
    for date_str in test_dates:
        parsed = parse_pm_expiry_date(date_str)
        print(f"  '{date_str}' → '{parsed}'") 