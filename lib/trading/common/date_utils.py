"""
Trading calendar and date utilities.

This module provides functions for working with trading dates, expiry dates,
and market calendars.
"""

from datetime import datetime, timedelta
from typing import Optional, List
import calendar


def get_monthly_expiry_code(month: int) -> str:
    """
    Get the single-letter code for a futures expiry month.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Single letter code (F=Jan, G=Feb, H=Mar, J=Apr, K=May, M=Jun,
                          N=Jul, Q=Aug, U=Sep, V=Oct, X=Nov, Z=Dec)
    """
    month_codes = {
        1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
        7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
    }
    return month_codes.get(month, '')


def get_third_friday(year: int, month: int) -> datetime:
    """
    Get the third Friday of a given month (common expiry date).
    
    Args:
        year: Year as integer
        month: Month as integer (1-12)
        
    Returns:
        datetime object for the third Friday
    """
    # Find first day of month
    first_day = datetime(year, month, 1)
    
    # Find first Friday
    days_until_friday = (4 - first_day.weekday()) % 7
    if days_until_friday == 0 and first_day.weekday() != 4:
        days_until_friday = 7
    first_friday = first_day + timedelta(days=days_until_friday)
    
    # Third Friday is 14 days after first Friday
    third_friday = first_friday + timedelta(days=14)
    return third_friday


def get_futures_expiry_date(year: int, month: int, contract_type: str = "ZN") -> datetime:
    """
    Get the expiry date for a futures contract.
    
    Different contracts have different expiry rules. This function
    encapsulates the logic for common contract types.
    
    Args:
        year: Year as integer
        month: Month as integer (1-12)
        contract_type: Type of futures contract (e.g., "ZN" for 10-year note)
        
    Returns:
        datetime object for the expiry date
    """
    if contract_type in ["ZN", "ZF", "ZT"]:  # Treasury futures
        # Last business day of the month preceding the delivery month
        if month == 1:
            expiry_month = 12
            expiry_year = year - 1
        else:
            expiry_month = month - 1
            expiry_year = year
            
        # Get last day of the expiry month
        last_day = calendar.monthrange(expiry_year, expiry_month)[1]
        expiry_date = datetime(expiry_year, expiry_month, last_day)
        
        # If last day is weekend, move to Friday
        if expiry_date.weekday() == 5:  # Saturday
            expiry_date -= timedelta(days=1)
        elif expiry_date.weekday() == 6:  # Sunday
            expiry_date -= timedelta(days=2)
            
        return expiry_date
    else:
        # Default to third Friday for other contracts
        return get_third_friday(year, month)


def parse_expiry_date(date_str: str) -> Optional[datetime]:
    """
    Parse an expiry date string in various formats.
    
    Handles formats like:
    - "MM/DD/YYYY"
    - "YYYY-MM-DD"
    - "DD-MMM-YY" (e.g., "21-MAR-25")
    
    Args:
        date_str: Date string to parse
        
    Returns:
        datetime object or None if parsing fails
    """
    # Common date formats in trading systems
    formats = [
        "%m/%d/%Y",    # MM/DD/YYYY
        "%Y-%m-%d",    # YYYY-MM-DD
        "%d-%b-%y",    # DD-MMM-YY
        "%d-%b-%Y",    # DD-MMM-YYYY
        "%m/%d/%y",    # MM/DD/YY
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def get_trading_days_between(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate the number of trading days between two dates.
    
    This is a simplified version that excludes weekends but not holidays.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of trading days
    """
    days = 0
    current = start_date
    
    while current <= end_date:
        if current.weekday() < 5:  # Monday to Friday
            days += 1
        current += timedelta(days=1)
    
    return days


def is_trading_day(date: datetime) -> bool:
    """
    Check if a given date is a trading day.
    
    Simplified version that only checks for weekends.
    
    Args:
        date: Date to check
        
    Returns:
        True if trading day, False otherwise
    """
    return date.weekday() < 5  # Monday to Friday 