"""
Common price parsing and formatting utilities for trading systems.

This module provides functions for converting between different price formats
used in treasury and bond trading, including:
- TT bond format (e.g., "110'005" for 110 and 1/64)
- Decimal format (e.g., 110.015625)
- Percentage format
- Display formatting for shocks
"""

import re
from typing import Optional, Union


def decimal_to_tt_bond_format(decimal_price: float) -> str:
    """
    Converts a decimal price to the TT bond style string format.
    
    This format represents prices in terms of whole points and 32nds, with a final digit
    indicating a half of a 32nd (i.e., 64ths of a point).
    
    Examples:
        110.015625 -> "110'005" (110 and 1/64)
        110.03125 -> "110'010" (110 and 1/32)
        110.046875 -> "110'015" (110 and 3/64)
    
    Args:
        decimal_price: The price as a decimal number.
        
    Returns:
        The price formatted as a TT bond style string.
        
    Raises:
        TypeError: If input price is not a number.
    """
    if not isinstance(decimal_price, (int, float)):
        raise TypeError("Input price must be a number.")

    whole_part = int(decimal_price)
    
    # Calculate total sixty-fourths for the fractional part
    fractional_value = decimal_price - whole_part
    
    # Total number of 1/64ths in the fractional part of the price
    num_sixty_fourths = round(fractional_value * 64.0)

    # Number of full 32nds
    num_full_32nds = int(num_sixty_fourths // 2)
    
    # Check if there is an extra half of a 32nd (i.e., an odd number of 64ths)
    has_half_32nd_extra = int(num_sixty_fourths % 2)
    
    # Format: WHOLE'XXY where XX is num_full_32nds (0-padded) and Y is 0 or 5
    return f"{whole_part}'{num_full_32nds:02d}{5 if has_half_32nd_extra else 0}"


def tt_bond_format_to_decimal(price_str: str) -> Optional[float]:
    """
    Convert a TT special string format price to decimal.
    
    Examples:
        "110'065" -> 110.203125 (110 and 6.5/32)
        "110'0875" -> 110.2734375 (110 and 8.75/32)
        "110'08" -> 110.25 (110 and 8/32)
    
    Args:
        price_str: Price string in TT format
        
    Returns:
        Decimal price value, or None if parsing fails
    """
    if not price_str:
        return None
        
    # Handle TT special format (e.g. "110'065")
    parts = price_str.split("'")
    if len(parts) != 2:
        return None
        
    try:
        whole_points = int(parts[0])
        fractional_str = parts[1]
        
        # Parse the fractional part based on length
        if len(fractional_str) == 2:  # Just 32nds, no fraction
            thirty_seconds = int(fractional_str)
            thirty_seconds_decimal = 0
        elif len(fractional_str) == 3:  # 32nds with single-digit fraction
            thirty_seconds = int(fractional_str[:2])
            thirty_seconds_decimal = int(fractional_str[2]) / 10.0
        elif len(fractional_str) == 4:  # 32nds with two-digit fraction
            thirty_seconds = int(fractional_str[:2])
            thirty_seconds_decimal = int(fractional_str[2:]) / 100.0
        else:
            return None
            
        # Convert to decimal price
        decimal_price = whole_points + (thirty_seconds + thirty_seconds_decimal) / 32.0
        return decimal_price
        
    except (ValueError, IndexError):
        return None


def parse_treasury_price(price_str: str) -> Optional[float]:
    """
    Parse treasury price from various formats.
    
    Handles formats like:
    - "110-08.5" (110 and 8.5/32)
    - "110-08.75" (110 and 8.75/32)
    - "110-08" (110 and 8/32)
    
    Args:
        price_str: Price string to parse
        
    Returns:
        Decimal price value, or None if parsing fails
    """
    if not price_str:
        return None
        
    # Remove any whitespace
    price_str = price_str.strip()
    
    # Try to match the treasury format (e.g., "110-08.5")
    match = re.match(r'^(\d+)-(\d+)(?:\.(\d+))?$', price_str)
    if not match:
        return None
        
    try:
        whole_points = int(match.group(1))
        thirty_seconds_part = int(match.group(2))
        fraction_str = match.group(3) or "0"
        
        # Convert fractional part to its decimal value
        if len(fraction_str) == 1:
            fraction_as_decimal = int(fraction_str) / 10.0
        elif len(fraction_str) == 2:
            fraction_as_decimal = int(fraction_str) / 100.0
        else:
            fraction_as_decimal = int(fraction_str) / (10 ** len(fraction_str))
            
        # Convert to decimal price
        decimal_price = whole_points + (thirty_seconds_part + fraction_as_decimal) / 32.0
        return decimal_price
        
    except (ValueError, AttributeError):
        return None


def format_treasury_price(decimal_price: float) -> str:
    """
    Format decimal price as treasury format string.
    
    Converts decimal price to format like "110-08.5" or "110-08.75".
    
    Args:
        decimal_price: Price as decimal number
        
    Returns:
        Formatted treasury price string
    """
    whole_part = int(decimal_price)
    fractional_part = decimal_price - whole_part
    
    # Convert to 32nds
    thirty_seconds_total = fractional_part * 32.0
    thirty_seconds_whole = int(thirty_seconds_total)
    thirty_seconds_fraction = thirty_seconds_total - thirty_seconds_whole
    
    # Format the fractional part
    if abs(thirty_seconds_fraction) < 0.001:
        return f"{whole_part}-{thirty_seconds_whole:02d}"
    elif abs(thirty_seconds_fraction - 0.5) < 0.001:
        return f"{whole_part}-{thirty_seconds_whole:02d}.5"
    elif abs(thirty_seconds_fraction - 0.25) < 0.001:
        return f"{whole_part}-{thirty_seconds_whole:02d}.25"
    elif abs(thirty_seconds_fraction - 0.75) < 0.001:
        return f"{whole_part}-{thirty_seconds_whole:02d}.75"
    else:
        # For other fractions, use two decimal places
        fraction_str = f"{thirty_seconds_fraction:.2f}".lstrip('0.')
        return f"{whole_part}-{thirty_seconds_whole:02d}.{fraction_str}"


def parse_and_convert_pm_price(price_str: str) -> Optional[dict]:
    """
    Parse a PricingMonkey price string and convert to decimal and special formats.
    
    Handles formats like "110-08.5" and converts to both decimal (110.265625)
    and TT special format ("110'085").
    
    Args:
        price_str: Price string from PricingMonkey
        
    Returns:
        Dictionary with 'decimal' and 'special_format' keys, or None if parsing fails
    """
    decimal_price = parse_treasury_price(price_str)
    if decimal_price is None:
        return None
        
    special_format = decimal_to_tt_bond_format(decimal_price)
    
    return {
        'decimal': decimal_price,
        'special_format': special_format
    }


def format_shock_value_for_display(value: float, shock_type: str) -> str:
    """
    Format shock value for display based on shock type.
    
    Args:
        value: The shock value to format
        shock_type: Type of shock - "percentage" or "absolute_usd"
        
    Returns:
        Formatted string for display
    """
    if shock_type == "percentage":
        # Convert decimal to percentage and format
        percentage_value = value * 100
        return f"{percentage_value:g}%"
    elif shock_type == "absolute_usd":
        # Format as currency
        if value >= 0:
            return f"${value:.2f}"
        else:
            return f"-${abs(value):.2f}"
    else:
        # Default formatting
        return f"{value:g}"


def convert_percentage_to_decimal(value: Union[str, float]) -> float:
    """
    Convert percentage value to decimal format.
    
    Handles both string percentages (e.g., "25%") and numeric values.
    
    Args:
        value: Percentage value as string or float
        
    Returns:
        Decimal representation of the percentage
    """
    if isinstance(value, str):
        # Remove percentage sign and convert
        clean_value = value.strip().rstrip('%')
        return float(clean_value) / 100.0
    elif isinstance(value, (int, float)):
        # Assume already in percentage form
        return float(value) / 100.0
    else:
        raise ValueError(f"Cannot convert {type(value)} to percentage decimal") 