"""
Business Day Utilities

Handles calculation of next business day for settlement price storage.
Specifically handles Friday -> Sunday mapping for CME markets.
"""

from datetime import date, timedelta
from typing import Optional


def get_next_business_day(current_date: date) -> date:
    """
    Get the next business day for settlement price storage.
    
    For CME markets:
    - Monday-Thursday: Next day
    - Friday: Skip Saturday, return Sunday
    - Saturday: Return Sunday  
    - Sunday: Return Monday
    
    Args:
        current_date: Current date
        
    Returns:
        Next business day for price storage
    """
    weekday = current_date.weekday()
    
    if weekday < 4:  # Monday (0) through Thursday (3)
        # Next day is a regular business day
        return current_date + timedelta(days=1)
    elif weekday == 4:  # Friday
        # Skip Saturday, go to Sunday
        return current_date + timedelta(days=2)
    elif weekday == 5:  # Saturday
        # Go to Sunday
        return current_date + timedelta(days=1)
    else:  # Sunday (6)
        # Go to Monday
        return current_date + timedelta(days=1)


def is_business_day(check_date: date) -> bool:
    """
    Check if a date is a business day for CME markets.
    
    Note: CME markets trade Sunday-Friday (closed Saturday only)
    
    Args:
        check_date: Date to check
        
    Returns:
        True if business day, False if not
    """
    # Saturday is not a business day
    return check_date.weekday() != 5


def get_previous_business_day(current_date: date) -> date:
    """
    Get the previous business day.
    
    Args:
        current_date: Current date
        
    Returns:
        Previous business day
    """
    weekday = current_date.weekday()
    
    if weekday == 0:  # Monday
        # Previous day is Sunday
        return current_date - timedelta(days=1)
    elif weekday == 6:  # Sunday
        # Previous day is Friday
        return current_date - timedelta(days=2)
    else:  # Tuesday-Saturday
        # Previous day
        return current_date - timedelta(days=1) 