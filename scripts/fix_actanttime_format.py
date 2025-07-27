#!/usr/bin/env python3
"""
Fix ActantTime format in ExpirationCalendar_CLEANED.csv
Changes from month-varying format (e.g., XCME.ZN.U.G.24JUL25) 
to fixed format (XCME.ZN.N.G.24JUL25)
"""

import pandas as pd
import re
from pathlib import Path

def fix_actanttime_format():
    """Fix ActantTime column to use consistent N.G pattern."""
    
    csv_path = Path("data/reference/symbol_translation/ExpirationCalendar_CLEANED.csv")
    
    print(f"Loading CSV from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Check if ActantTime column exists
    if 'ActantTime' not in df.columns:
        print("ERROR: ActantTime column not found!")
        return False
    
    # Count current formats
    print("\nCurrent ActantTime formats:")
    pattern_counts = {}
    for value in df['ActantTime'].dropna():
        # Extract the pattern (e.g., ZN.U.G, ZN.Z.G)
        match = re.search(r'ZN\.[A-Z]\.G', str(value))
        if match:
            pattern = match.group()
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    for pattern, count in sorted(pattern_counts.items()):
        print(f"  {pattern}: {count} occurrences")
    
    # Fix the format
    print("\nFixing ActantTime format to use ZN.N.G pattern...")
    original_values = df['ActantTime'].copy()
    
    # Replace any ZN.[A-Z].G pattern with ZN.N.G
    df['ActantTime'] = df['ActantTime'].apply(
        lambda x: re.sub(r'ZN\.[A-Z]\.G', 'ZN.N.G', str(x)) if pd.notna(x) else x
    )
    
    # Count changes
    changes = (original_values != df['ActantTime']).sum()
    print(f"Modified {changes} entries")
    
    # Show sample changes
    if changes > 0:
        print("\nSample changes (first 5):")
        changed_mask = original_values != df['ActantTime']
        sample_changes = df[changed_mask].head()
        for idx in sample_changes.index:
            print(f"  Row {idx}: {original_values[idx]} → {df.loc[idx, 'ActantTime']}")
    
    # Verify new format
    print("\nVerifying new format:")
    new_pattern_counts = {}
    for value in df['ActantTime'].dropna():
        match = re.search(r'ZN\.[A-Z]\.G', str(value))
        if match:
            pattern = match.group()
            new_pattern_counts[pattern] = new_pattern_counts.get(pattern, 0) + 1
    
    for pattern, count in sorted(new_pattern_counts.items()):
        print(f"  {pattern}: {count} occurrences")
    
    # Save the updated CSV
    output_path = csv_path
    df.to_csv(output_path, index=False)
    print(f"\nSaved updated CSV to {output_path}")
    
    return True

if __name__ == "__main__":
    success = fix_actanttime_format()
    if success:
        print("\n✅ ActantTime format fix completed successfully!")
    else:
        print("\n❌ ActantTime format fix failed!")
        exit(1) 