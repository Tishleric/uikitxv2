"""
Parse Actant JSON export for ATM option data
"""

import json
import pandas as pd
import os
import glob

def find_latest_json():
    """Find most recent Actant JSON file - optimized for current day"""
    from datetime import datetime
    
    # Try optimized approach first - today's files only
    today = datetime.now().strftime("%Y%m%d")
    todays_pattern = f"Z:/ActantEOD/*_{today}_*.json"
    todays_files = glob.glob(todays_pattern)
    
    if todays_files:
        # Found today's files - much faster
        return max(todays_files, key=os.path.getmtime)
    
    # Fallback to original method (slow but comprehensive)
    json_files = glob.glob("Z:/ActantEOD/*.json")
    if not json_files:
        json_files = glob.glob("*.json")
    
    if json_files:
        return max(json_files, key=os.path.getmtime)
    return None

def parse_json(filepath):
    """Extract F, K, T, Vol for ATM options from JSON"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    results = []
    
    # Navigate JSON structure - look for totals array
    if 'totals' in data:
        for total in data['totals']:
            scenario = total.get('header', 'Unknown')
            
            # Skip certain scenarios if needed
            if scenario == "w/o first":
                continue
                
            if 'points' in total:
                # Find the 0 shock point (ATM)
                for point in total['points']:
                    if point.get('header') == '0':
                        values = point.get('values', {})
                        
                        # Extract values, removing 'ab_' prefix
                        F = float(values.get('ab_F', 0))
                        K = float(values.get('ab_K', 0))
                        T = float(values.get('ab_T', 0))  # Days
                        Vol = float(values.get('ab_Vol', 0))  # Percentage
                        
                        # Only add if we have valid data
                        if F > 0 and K > 0 and T > 0 and Vol > 0:
                            results.append({
                                'scenario': scenario,
                                'F': F,
                                'K': K,
                                'T': T / 365.0,  # Convert days to years
                                'Vol': Vol  # Keep as percentage for now
                            })
                        break  # Found the 0 shock point, move to next scenario
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    json_file = find_latest_json()
    if json_file:
        print(f"Parsing {json_file}...")
        df = parse_json(json_file)
        
        if not df.empty:
            df.to_csv('actant_data.csv', index=False)
            print(f"Saved {len(df)} records to actant_data.csv")
            print("\nExtracted data:")
            print(df)
        else:
            print("ERROR: No ATM option data found in JSON file")
            print("Make sure the JSON contains 'totals' array with shock points")
    else:
        print("ERROR: No JSON file found in Z:/ActantEOD/ or current directory") 