#!/usr/bin/env python3
"""Extract unique broker symbols and test translations to all formats."""

import pandas as pd
import glob
import os
import sys
sys.path.insert(0, '.')
from lib.trading.market_prices.rosetta_stone import RosettaStone, SymbolFormat

def main():
    # Initialize RosettaStone
    rs = RosettaStone()
    
    # Find all broker trade files
    broker_files = glob.glob('data/reference/BrokerTrades/DASONLY.*.csv')
    
    # Collect unique descriptions
    unique_descriptions = set()
    
    for file_path in broker_files:
        try:
            # Read CSV with explicit quote handling
            df = pd.read_csv(file_path, quotechar='"')
            if 'DESCRIPTION' in df.columns:
                # Filter out empty/null descriptions
                descriptions = df['DESCRIPTION'].dropna()
                # Strip quotes from descriptions - both single and double, leading and trailing
                descriptions = descriptions.str.strip('"').str.strip("'").str.strip()
                unique_descriptions.update(descriptions)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    # Remove empty strings
    unique_descriptions = {desc for desc in unique_descriptions if desc.strip()}
    
    print(f"Found {len(unique_descriptions)} unique broker descriptions")
    
    # Debug: show first few raw descriptions
    print("\nFirst few raw descriptions:")
    for i, desc in enumerate(sorted(unique_descriptions)[:3]):
        print(f"  {i}: '{desc}'")
    
    # Prepare results
    results = []
    
    for broker_symbol in sorted(unique_descriptions):
        # Extra cleanup - remove any remaining quotes
        cleaned_symbol = broker_symbol.strip('"').strip("'").strip()
        row = {'broker': cleaned_symbol}
        
        # Try to translate to each format
        for target_format in ['bloomberg', 'cme', 'actantrisk', 'actanttrades', 'actanttime']:
            try:
                translated = rs.translate(cleaned_symbol, 
                                        from_format='broker',
                                        to_format=target_format)
                row[target_format] = translated if translated else 'TRANSLATION_FAILED'
            except Exception as e:
                row[target_format] = f'ERROR: {str(e)}'
        
        results.append(row)
    
    # Create DataFrame and save
    results_df = pd.DataFrame(results)
    output_file = 'data/output/broker_translation_test.csv'
    results_df.to_csv(output_file, index=False)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Total rows: {len(results_df)}")
    
    # Show first few rows
    print("\nFirst 5 translations:")
    print(results_df.head().to_string())

if __name__ == '__main__':
    main()