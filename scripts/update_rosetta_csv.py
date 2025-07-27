#!/usr/bin/env python3
"""
Update ExpirationCalendar_CLEANED.csv with new column names and formats.

Renames XCME -> ActantRisk and generates ActantTrades and ActantTime columns.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import re

# Month codes for futures contracts
MONTH_CODES = {
    1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
    7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
}

# Series to product mappings for ActantTrades format
SERIES_TO_PRODUCT = {
    'VY': 'VY',  # Monday
    'GY': 'GY',  # Tuesday (Globex)
    'WY': 'WY',  # Wednesday
    'HY': 'HY',  # Thursday (Globex)
    'ZN': 'ZN',  # Friday
    'OZN': 'OZN' # Quarterly
}


def parse_date(date_str):
    """Parse date from various formats."""
    try:
        # Try parsing "7/21/2025 14:00" format
        return datetime.strptime(date_str.split()[0], '%m/%d/%Y')
    except:
        return None


def generate_actant_trades_format(row):
    """
    Generate ActantTrades format from row data.
    Format: XCMEOCADPS20250728N0VY4 (no strike included in base)
    """
    try:
        # Parse expiry date
        expiry_date = parse_date(row['Option Expiration Date (CT)'])
        if not expiry_date:
            return None
            
        # Get CME symbol (e.g., VY3N5)
        cme_symbol = row['CME']
        
        # Extract series and number
        # Handle OZN (quarterly) differently
        if cme_symbol.startswith('OZN'):
            # OZNQ5 format
            match = re.match(r'^(OZN)([A-Z]\d)$', cme_symbol)
            if not match:
                return None
            series = match.group(1)  # OZN
            week_num = ''  # No week number for quarterly
            contract = match.group(2)  # Q5
        else:
            # Regular weekly format
            match = re.match(r'^([A-Z]+)(\d)([A-Z]\d)$', cme_symbol)
            if not match:
                return None
            series = match.group(1)  # VY, GY, WY, HY, ZN
            week_num = match.group(2)  # 3, 4, 5, etc.
            contract = match.group(3)  # N5, Q5, etc.
        
        # Get product code
        product = SERIES_TO_PRODUCT.get(series, series)
        
        # Format date as YYYYMMDD
        date_str = expiry_date.strftime('%Y%m%d')
        
        # Build ActantTrades format
        # XCMEOCADPS{date}{month_code}0{product}{week_num}
        month_code = contract[0]  # N, Q, U, etc.
        
        return f"XCMEOCADPS{date_str}{month_code}0{product}{week_num}"
        
    except Exception as e:
        print(f"Error generating ActantTrades for {row.get('CME', 'unknown')}: {e}")
        return None


def generate_actant_time_format(row):
    """
    Generate ActantTime format from row data.
    Format: XCME.ZN.N.G.21JUL25
    
    ASSUMPTION: The 'G' in the format represents the underlying contract type.
    For 10-Year notes, we'll use 'G' consistently.
    """
    try:
        # Parse expiry date
        expiry_date = parse_date(row['Option Expiration Date (CT)'])
        if not expiry_date:
            return None
            
        # Get underlying symbol (e.g., ZNU5)
        underlying = row['Underlying Symbol']
        if not underlying or len(underlying) < 3:
            return None
            
        # Extract month code from underlying
        month_code = underlying[2]  # N from ZNU5
        
        # Format date as DDBBBDD (e.g., 21JUL25)
        date_str = expiry_date.strftime('%d%b%y').upper()
        
        # ASSUMPTION: Using 'ZN' as the product and 'G' as the type
        # This may need adjustment based on actual product types
        return f"XCME.ZN.{month_code}.G.{date_str}"
        
    except Exception as e:
        print(f"Error generating ActantTime for {row.get('CME', 'unknown')}: {e}")
        return None


def main():
    """Update CSV with new column names and formats."""
    # Read the CSV
    csv_path = Path("data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} rows from {csv_path}")
    
    # Rename columns
    column_renames = {
        'XCME': 'ActantRisk',
        'XCME_Original': 'ActantRisk_Original'
    }
    
    df = df.rename(columns=column_renames)
    print("Renamed XCME columns to ActantRisk")
    
    # Generate ActantTrades column
    print("Generating ActantTrades format...")
    df['ActantTrades'] = df.apply(generate_actant_trades_format, axis=1)
    
    # Count successful generations
    trades_count = df['ActantTrades'].notna().sum()
    print(f"Generated {trades_count}/{len(df)} ActantTrades entries")
    
    # Generate ActantTime column
    print("Generating ActantTime format...")
    df['ActantTime'] = df.apply(generate_actant_time_format, axis=1)
    
    # Count successful generations
    time_count = df['ActantTime'].notna().sum()
    print(f"Generated {time_count}/{len(df)} ActantTime entries")
    
    # Save updated CSV
    output_path = csv_path.with_stem(csv_path.stem + "_updated")
    df.to_csv(output_path, index=False)
    print(f"\nSaved updated CSV to: {output_path}")
    
    # Show sample rows
    print("\nSample rows:")
    sample_cols = ['CME', 'ActantRisk', 'ActantTrades', 'ActantTime', 'Bloomberg_Call']
    print(df[sample_cols].head(10).to_string())
    
    # Check for any Friday options (ZN1-ZN5)
    friday_df = df[df['CME'].str.startswith('ZN')]
    if not friday_df.empty:
        print(f"\nFound {len(friday_df)} Friday options (special handling):")
        print(friday_df[sample_cols].head().to_string())
    
    # Note assumptions
    print("\n*** ASSUMPTIONS MADE ***")
    print("1. ActantTrades format uses XCMEOCADPS prefix for options")
    print("2. ActantTime format uses 'G' as a fixed type indicator")
    print("3. ActantTime uses 'ZN' as the product for all 10-Year options")
    print("4. Friday options (ZN1-ZN5) follow the same pattern")
    print("\nPlease verify these assumptions are correct!")


if __name__ == "__main__":
    main() 