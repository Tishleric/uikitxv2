import datetime
from dateutil.relativedelta import relativedelta
from workalendar.usa import UnitedStates
import pandas as pd
pd.set_option('display.max_rows', 100)      # Show up to 100 rows
pd.set_option('display.max_columns', 100)    # Show up to 100 columns
pd.set_option('display.width', 1000)       # Set the display width to 1000 characters
pd.set_option('display.max_colwidth', 100)  # Set the max column width to 100 characters

# Define Bloomberg Monthly Symbols
def get_optiondate_list():
    """
    Generate next 3 option expiry dates and corresponding asset codes.
    
    This function maintains backward compatibility while using the new clean logic.
    
    Returns:
        tuple: (list_of_dates, symbols) - same format as original function
    """
    dates, assets, _ = get_clean_option_dates_and_assets()
    return dates, assets


def get_clean_option_dates_and_assets(current_datetime=None):
    """
    Generate next 3 option expiry dates and corresponding asset codes with clean logic.
    
    Args:
        current_datetime: Override for testing (defaults to datetime.now())
    
    Returns:
        tuple: (dates_list, asset_codes_list, pm_shift_needed)
               - dates_list: ['2025-05-27', '2025-05-28', '2025-05-30'] 
               - asset_codes_list: ['VY4', 'WY4', 'ZN5']
               - pm_shift_needed: True if PM ordinals need shifting due to post-3PM
    """
    if current_datetime is None:
        current_datetime = datetime.datetime.now()
    
    # Asset code mapping
    expiry_days = {'Monday': 'VY', 'Wednesday': 'WY', 'Friday': 'ZN'}
    
    # Get holidays for current year
    cal = UnitedStates()
    holidays = {holiday[0] for holiday in cal.holidays(current_datetime.year)}
    
    # Determine if we need to shift PM ordinals (post-3PM on expiry day)
    current_weekday_name = current_datetime.strftime("%A")
    is_expiry_day = current_weekday_name in expiry_days
    is_post_3pm = current_datetime.hour >= 15
    pm_shift_needed = is_expiry_day and is_post_3pm
    
    # Find next 3 valid expiry dates
    list_of_dates = []
    symbols = []
    
    # Start from tomorrow if we're post-3PM on expiry day, otherwise today
    start_date = current_datetime.date()
    if pm_shift_needed:
        start_date += datetime.timedelta(days=1)
    
    check_date = start_date
    max_days_ahead = 30  # Safety limit
    
    for _ in range(max_days_ahead):
        weekday_name = check_date.strftime("%A")
        
        # Check if this is an expiry day
        if weekday_name in expiry_days:
            # Handle holiday shifts
            actual_expiry_date = check_date
            while actual_expiry_date in holidays or actual_expiry_date.weekday() in {5, 6}:
                actual_expiry_date += datetime.timedelta(days=1)
            
            # Generate asset code: base + occurrence number
            base_code = expiry_days[weekday_name]  # Original intended day
            occurrence_num = _calculate_occurrence_in_month(check_date, check_date.weekday())
            asset_code = base_code + str(occurrence_num)
            
            symbols.append(asset_code)
            list_of_dates.append(actual_expiry_date.strftime("%Y-%m-%d"))
            
            # Stop when we have 3 expiries
            if len(list_of_dates) >= 3:
                break
        
        check_date += datetime.timedelta(days=1)
    
    return list_of_dates, symbols, pm_shift_needed


def _calculate_occurrence_in_month(target_date, target_weekday):
    """
    Calculate which occurrence of the weekday this date represents in the month.
    
    Args:
        target_date (datetime.date): The date to check
        target_weekday (int): Weekday number (0=Monday, 6=Sunday)
        
    Returns:
        int: Occurrence number (1, 2, 3, 4, etc.)
    """
    count = 0
    for day in range(1, target_date.day + 1):
        check_date = datetime.date(target_date.year, target_date.month, day)
        if check_date.weekday() == target_weekday:
            count += 1
    return count


def closest_weekly_treasury_strike(price):
    increment = 0.25  # Weekly options move in 0.25 increments
    return round(price / increment) * increment


def main():
    # Example usage:
    current_price = 110.39  # Example current price in decimal
    closest_strike = closest_weekly_treasury_strike(current_price)

    print(f"Closest strike price: {closest_strike}")
    print(get_optiondate_list())