"""
Settlement Time Constants and Utilities

This module provides constants and utilities for handling CME settlement times
in the P&L calculation system. All times are in Chicago time (CDT/CST).

CRITICAL: P&L days run from 2pm to 2pm (settlement to settlement).
At 4pm, we calculate P&L for the period that ended at 2pm today.
"""

import pytz
from datetime import time, datetime, timedelta
from typing import Tuple, Optional, Union


# Chicago timezone (CME trading hours)
CHICAGO_TZ = pytz.timezone('America/Chicago')

# Key trading times (in Chicago time)
SETTLEMENT_TIME = time(14, 0)  # 2:00 PM CDT - CME settlement & P&L day boundary
EOD_TIME = time(16, 0)  # 4:00 PM CDT - End of day P&L calculation
SOD_TIME = time(17, 0)  # 5:00 PM CDT - Start of day for next trading day

# Settlement price windows
FLASH_WINDOW_START = time(13, 45)  # 1:45 PM CDT
FLASH_WINDOW_END = time(14, 15)    # 2:15 PM CDT
SETTLE_WINDOW_START = time(15, 45)  # 3:45 PM CDT
SETTLE_WINDOW_END = time(16, 15)    # 4:15 PM CDT


def localize_to_chicago(dt: datetime) -> datetime:
    """Convert a naive datetime to Chicago timezone."""
    if dt.tzinfo is None:
        return CHICAGO_TZ.localize(dt)
    else:
        return dt.astimezone(CHICAGO_TZ)


def get_pnl_date_for_trade(trade_timestamp: datetime) -> datetime.date:
    """
    Determine which P&L date a trade belongs to.
    
    Rules:
    - Trades before 2pm belong to current calendar day's P&L
    - Trades at/after 2pm belong to next calendar day's P&L
    
    Args:
        trade_timestamp: The trade timestamp (will be converted to Chicago time)
        
    Returns:
        The P&L date this trade belongs to
    """
    # Ensure Chicago timezone
    trade_dt = localize_to_chicago(trade_timestamp)
    
    # Get 2pm cutoff for that day
    cutoff = trade_dt.replace(hour=14, minute=0, second=0, microsecond=0)
    
    if trade_dt < cutoff:
        return trade_dt.date()
    else:
        return trade_dt.date() + timedelta(days=1)


def get_pnl_period_boundaries(pnl_date: datetime.date) -> Tuple[datetime, datetime]:
    """
    Get the start and end times for a P&L date.
    
    P&L date T covers the period from 2pm on day T-1 to 2pm on day T.
    
    Args:
        pnl_date: The P&L date (e.g., Tuesday)
        
    Returns:
        Tuple of (period_start, period_end) in Chicago time
        For Tuesday: (Monday 2pm, Tuesday 2pm)
    """
    # End is 2pm on the P&L date
    period_end = CHICAGO_TZ.localize(
        datetime.combine(pnl_date, SETTLEMENT_TIME)
    )
    
    # Start is 2pm on the previous day
    # TODO: Handle weekends/holidays
    period_start = period_end - timedelta(days=1)
    
    return period_start, period_end


def get_settlement_boundaries(date: datetime.date) -> Tuple[datetime, datetime]:
    """
    Get the settlement time boundaries for a given date.
    
    DEPRECATED: Use get_pnl_period_boundaries instead.
    This function name is misleading as it suggests within-day boundaries.
    """
    # For backward compatibility, return P&L period boundaries
    return get_pnl_period_boundaries(date)


def get_eod_boundary(date: datetime.date) -> datetime:
    """Get the 4pm EOD calculation time for a given date."""
    return CHICAGO_TZ.localize(datetime.combine(date, EOD_TIME))


def is_before_settlement(dt: datetime, settlement_date: datetime.date) -> bool:
    """
    Check if a datetime is before the settlement time on a given date.
    
    Note: This determines if a trade belongs to the current or next P&L day.
    """
    dt_chicago = localize_to_chicago(dt)
    settlement_time = CHICAGO_TZ.localize(
        datetime.combine(settlement_date, SETTLEMENT_TIME)
    )
    return dt_chicago < settlement_time


def is_in_settlement_window(timestamp: datetime) -> bool:
    """
    Check if timestamp falls within the 2pm settlement price window (1:45-2:15 PM).
    
    Args:
        timestamp: The timestamp to check
        
    Returns:
        True if within settlement window
    """
    timestamp = localize_to_chicago(timestamp)
    timestamp_time = timestamp.time()
    
    return FLASH_WINDOW_START <= timestamp_time <= FLASH_WINDOW_END


def get_applicable_price_type(timestamp: datetime) -> str:
    """
    Determine which price type to use based on timestamp.
    
    Args:
        timestamp: The timestamp to check
        
    Returns:
        'px_last' for 2pm window, 'px_settle' for 4pm window, 'current' otherwise
    """
    timestamp = localize_to_chicago(timestamp)
    timestamp_time = timestamp.time()
    
    if FLASH_WINDOW_START <= timestamp_time <= FLASH_WINDOW_END:
        return 'px_last'  # Flash close (2pm price)
    elif SETTLE_WINDOW_START <= timestamp_time <= SETTLE_WINDOW_END:
        return 'px_settle'  # Settlement (4pm price)
    else:
        return 'current'  # Use current market price


def split_position_at_settlement(
    entry_time: datetime,
    exit_time: Optional[datetime],
    settlement_time: datetime
) -> Tuple[bool, Optional[datetime], Optional[datetime]]:
    """
    Determine if a position crosses settlement boundary.
    
    This is used for precise P&L attribution when a position
    spans multiple P&L periods.
    
    Args:
        entry_time: When position was opened
        exit_time: When position was closed (None if still open)
        settlement_time: The settlement boundary to check
        
    Returns:
        Tuple of (crosses_settlement, pre_settlement_exit, post_settlement_entry)
    """
    entry_chicago = localize_to_chicago(entry_time)
    exit_chicago = localize_to_chicago(exit_time) if exit_time else None
    settle_chicago = localize_to_chicago(settlement_time)
    
    # If closed before settlement, no split
    if exit_chicago and exit_chicago <= settle_chicago:
        return False, None, None
        
    # If opened after settlement, no split
    if entry_chicago >= settle_chicago:
        return False, None, None
        
    # Position crosses settlement
    return True, settle_chicago, settle_chicago


def format_chicago_time(dt: datetime) -> str:
    """Format datetime in Chicago timezone for display."""
    dt = localize_to_chicago(dt)
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z') 


def format_pnl_period(pnl_date: datetime.date) -> str:
    """
    Format a P&L period for display.
    
    Args:
        pnl_date: The P&L date
        
    Returns:
        Human-readable period description
    """
    period_start, period_end = get_pnl_period_boundaries(pnl_date)
    return (f"{period_start.strftime('%Y-%m-%d %I:%M %p')} to "
            f"{period_end.strftime('%Y-%m-%d %I:%M %p')} CT") 