import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from Brent_Bisection import *

option_strikes = {110.0, 110.25, 110.5, 110.75, 111.0, 111.25, 111.5, 111.75, 112.0, 112.25, 112.5, 112.75, 113.0, 113.25, 113.5, 113.75, 114.0}

def closest_strike(underlying_future_price, option_strikes):
    return min(option_strikes, key=lambda x: abs(x - underlying_future_price))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob

option_strikes = {110.0, 110.25, 110.5, 110.75, 111.0, 111.25, 111.5, 111.75, 112.0, 112.25, 112.5, 112.75, 113.0, 113.25, 113.5, 113.75, 114.0}

def closest_strike(underlying_future_price, option_strikes):
    return min(option_strikes, key=lambda x: abs(x - underlying_future_price))

def extract_atm_calls(expiry, type_of_option):
    """Extract ATM call options from all CSV files and save to ATM_C_21AUG25.csv"""
    
    # Get the current script directory
    script_dir = os.path.dirname(__file__)
    data_validation_dir = os.path.join(script_dir, 'data_validation')
    
    # Find all CSV files in both date folders
    csv_files = []
    for date_folder in ['2025-08-18', '2025-08-19', '2025-08-20', '2025-08-21', '2025-08-22', '2025-08-25', '2025-08-26']:
        folder_path = os.path.join(data_validation_dir, date_folder)
        if os.path.exists(folder_path):
            pattern = os.path.join(folder_path, '*.csv')
            csv_files.extend(glob.glob(pattern))
    
    # Sort files by filename for consistent ordering
    csv_files.sort()
    
    print(f"Found {len(csv_files)} CSV files")
    
    # Extract ATM call rows
    atm_rows = []
    
    for csv_file in csv_files:
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            
            # Get underlying future price from first row
            if len(df) > 0:
                underlying_price = df.iloc[0]['underlying_future_price']
                
                # Find closest strike
                closest_strike_val = closest_strike(underlying_price, option_strikes)
                
                # Find row matching criteria
                mask = (
                    (df['expiry'] == expiry) & 
                    (df['strike'] == closest_strike_val) & 
                    (df['itype'] == type_of_option)
                )
                
                matching_rows = df[mask]
                
                if len(matching_rows) > 0:
                    # Take first match and add timestamp info
                    row = matching_rows.iloc[0].copy()
                    row['source_file'] = os.path.basename(csv_file)
                    row['underlying_price'] = underlying_price
                    row['closest_strike'] = closest_strike_val
                    atm_rows.append(row)
                    
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    # Create output DataFrame
    if atm_rows:
        output_df = pd.DataFrame(atm_rows)
        
        # Save to CSV
        output_path = os.path.join(data_validation_dir, f'ATM_{type_of_option}_{expiry}.csv')
        output_df.to_csv(output_path, index=False)
        
        print(f"Extracted {len(atm_rows)} ATM {type_of_option} rows")
        print(f"Output saved to: {output_path}")
        
        return output_df
    else:
        print("No ATM call rows found!")
        return None


def vol(df2, expiry, type_of_option):
    df2["IV_binary_search"] = df2['implied_vol']
    df2 = df2.drop_duplicates(subset=['vtexp'])
    for i in range(len(df2)):
        #print(i, "of", len(df2)-1)
        S, K, T = df2['underlying_future_price'].iloc[i], df2['strike'].iloc[i], df2['vtexp'].iloc[i]
        C_mkt = df2['adjtheor'].iloc[i]
        #print(S, K, T, C_mkt)
        # Root function in sigma: f(sig) = model - market
        def f_sigma(sig): return bachelier_call(S, K, sig, T) - C_mkt
        # Bracket [0, hi] by geometric expansion
        lo, hi = 0.0, 1e-4
        while f_sigma(hi) < 0: hi *= 2.0

        df2['IV_binary_search'].iloc[i] = bisection(f_sigma, lo, hi, xtol=1e-16, ftol=1e-16)[0]
    
    df2.to_csv(f'lib/trading/bond_future_options/data_validation/ATM_{type_of_option}_{expiry}_vols.csv')
    return df2

if __name__ == "__main__":
    # Run the extraction
    for expiry in ['21AUG25', '25AUG25', '26AUG25', '27AUG25']:
        result = extract_atm_calls(expiry, 'C')
        result = vol(result, expiry, 'C')
        if result is not None:
            print(f"\nFirst few rows:")
            print(result.head())








