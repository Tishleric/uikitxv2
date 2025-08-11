#!/usr/bin/env python3
"""
Add Broker column to ExpirationCalendar_CLEANED.csv - Version 2.
Generates broker-format symbols for each row while preserving all existing data.
For options, generates combined CALL/PUT format.
"""

import pandas as pd
from datetime import datetime
import re

# Product mappings - corrected based on user feedback
PRODUCT_MAP = {
    'ZN': '10YR TNOTE',    # 10-Year Note
    'ZT': '2YR TNOTE',     # 2-Year Note  
    'ZF': '5YR TNOTE',     # 5-Year Note
    'ZB': '30YR TBOND',    # 30-Year Bond (was mislabeled as 20-year)
}

def get_week_number_in_month(date):
    """Calculate which occurrence of this weekday in the month (1st Monday = 1, etc.)"""
    day = date.day
    weekday = date.weekday()
    
    # Find all days in month with same weekday
    first_day = date.replace(day=1)
    days_with_same_weekday = []
    
    for d in range(1, 32):
        try:
            test_date = date.replace(day=d)
            if test_date.weekday() == weekday:
                days_with_same_weekday.append(d)
        except ValueError:
            break
    
    # Find which occurrence this is
    return days_with_same_weekday.index(day) + 1 if day in days_with_same_weekday else None


def extract_strike_from_original(original_str):
    """Extract strike from Original column format like 'VY3N5 C11100'"""
    if pd.isna(original_str):
        return None
        
    # Match pattern like "C11100" or "P11100"
    match = re.search(r'[CP](\d+)', str(original_str))
    if match:
        strike_str = match.group(1)
        # Convert to decimal format (11100 -> 111.00)
        try:
            strike_val = float(strike_str) / 100
            return f"{strike_val:.2f}"
        except:
            pass
    return None


def generate_broker_symbol(row):
    """Generate broker-format symbol for a calendar row."""
    try:
        # Parse expiration date
        exp_date = pd.to_datetime(row['Option Expiration Date (CT)'])
        month = exp_date.strftime('%b').upper()  # JAN, FEB, etc.
        year = exp_date.strftime('%y')  # 25, 26, etc.
        
        # Get product info
        product_desc = row['Option Product']
        underlying = row['Underlying Symbol']
        
        # Handle missing values
        if pd.isna(product_desc):
            return None
            
        # Extract base product (ZN, ZT, ZF, ZB)
        base_product = None
        for key in PRODUCT_MAP:
            if key in underlying:
                base_product = key
                break
        
        if not base_product:
            return None
            
        broker_product = PRODUCT_MAP.get(base_product)
        if not broker_product:
            return None
        
        # Check if this is a future
        if 'Future' in product_desc and 'Option' not in product_desc:
            # Simple futures format: MON YY CBT PRODUCT
            return f'"{month} {year} CBT {broker_product}"'
        
        # Handle options - need to extract strike
        strike = extract_strike_from_original(row.get('Original'))
        if not strike:
            # Try CME_Original
            strike = extract_strike_from_original(row.get('CME_Original'))
        
        if not strike:
            # Can't generate option without strike
            return None
        
        # Determine week info based on product description
        week_info = ""
        weekday = exp_date.strftime('%A')
        week_num = get_week_number_in_month(exp_date)
        
        if 'Weekly' in product_desc or 'Wk' in product_desc:
            if weekday == 'Friday':
                # Friday weeklies use "WKLY WK{N}" format
                if week_num:
                    week_info = f"WKLY WK{week_num}"
            elif weekday == 'Monday':
                # Monday options don't have special week info in broker format
                # But let's check if it's actually a Tuesday (like Sep 2, 2025)
                # due to Labor Day
                pass
            elif weekday == 'Tuesday':
                # Tuesday uses "W{N} TUES OPT" format
                if week_num:
                    week_info = f"W{week_num} TUES OPT"
            elif weekday == 'Wednesday':
                # Wednesday uses "WED WK{N}" format
                if week_num:
                    week_info = f"WED WK{week_num}"
            elif weekday == 'Thursday':
                # Thursday uses "W{N} THURS OPT" format
                if week_num:
                    week_info = f"W{week_num} THURS OPT"
        
        # For options in the calendar, we'll store in a format that indicates
        # this row represents both CALL and PUT
        # The actual broker format would be split into two separate entries
        # But to maintain calendar structure, we'll use a placeholder format
        parts = [month, year, 'CBT', broker_product]
        if week_info:
            parts.append(week_info)
        parts.append(strike)
        
        # Return a format that indicates both option types are available
        return f'"CALL/PUT {" ".join(parts)}"'
        
    except Exception as e:
        print(f"Error processing row: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Add Broker column to the expiration calendar."""
    # Read the calendar
    input_file = 'data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv'
    df = pd.read_csv(input_file)
    
    print(f"Loaded calendar with {len(df)} rows")
    
    # Generate broker symbols
    df['Broker'] = df.apply(generate_broker_symbol, axis=1)
    
    # Count successful generations
    generated = df['Broker'].notna().sum()
    print(f"Generated {generated} broker symbols out of {len(df)} rows")
    
    # Show examples by type
    print("\nFutures examples:")
    futures = df[(df['Broker'].notna()) & (df['Option Product'].str.contains('Future', na=False))]
    for idx, row in futures.head(5).iterrows():
        print(f"  {row['Option Product']}: {row['Broker']}")
    
    print("\nOptions examples:")
    options = df[(df['Broker'].notna()) & (df['Option Product'].str.contains('Option', na=False))]
    for idx, row in options.head(10).iterrows():
        print(f"  {row['Option Product']}: {row['Broker']}")
    
    # Check for missing broker symbols in options
    missing_options = df[(df['Broker'].isna()) & (df['Option Product'].str.contains('Option', na=False))]
    if len(missing_options) > 0:
        print(f"\nWarning: {len(missing_options)} option rows without broker symbols")
        print("Sample missing:")
        for idx, row in missing_options.head(3).iterrows():
            print(f"  {row['Option Product']} - Original: {row.get('Original', 'N/A')}")
    
    # Save the updated calendar
    output_file = input_file  # Overwrite the original
    df.to_csv(output_file, index=False)
    print(f"\nSaved updated calendar to {output_file}")


if __name__ == "__main__":
    main()