#!/usr/bin/env python3
"""
Test spot risk symbol translation coverage to see which symbols aren't being translated.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path
from collections import defaultdict

from lib.trading.market_prices.spot_risk_symbol_adapter import SpotRiskSymbolAdapter

def main():
    """Analyze symbol translation coverage."""
    
    print("="*60)
    print("SPOT RISK SYMBOL TRANSLATION COVERAGE ANALYSIS")
    print("="*60)
    
    # Load a spot risk file
    test_file = Path("data/input/actant_spot_risk/2025-07-18/bav_analysis_20250717_145100.csv")
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return
        
    # Read CSV
    df = pd.read_csv(test_file)
    df = df.iloc[1:].reset_index(drop=True)  # Skip type row
    
    # Get unique symbols
    symbols = df['Key'].dropna().unique()
    print(f"\nTotal unique symbols: {len(symbols)}")
    
    # Test translation
    adapter = SpotRiskSymbolAdapter()
    
    translated = []
    not_translated = []
    by_type = defaultdict(list)
    
    for symbol in symbols:
        if 'INVALID' in str(symbol) or symbol == 'XCME.ZN':
            continue
            
        bloomberg = adapter.translate(symbol)
        
        if bloomberg:
            translated.append((symbol, bloomberg))
            # Categorize by type
            if ' ' in bloomberg:
                by_type['options'].append((symbol, bloomberg))
            else:
                by_type['futures'].append((symbol, bloomberg))
        else:
            not_translated.append(symbol)
            # Categorize failed translations
            if '.' in symbol and symbol.count('.') >= 4:
                by_type['failed_options'].append(symbol)
            else:
                by_type['failed_futures'].append(symbol)
    
    # Report results
    print(f"\nTranslation Results:")
    print(f"  Successfully translated: {len(translated)}")
    print(f"  Failed to translate: {len(not_translated)}")
    print(f"  Success rate: {len(translated)/(len(translated)+len(not_translated))*100:.1f}%")
    
    print(f"\nBy Type:")
    print(f"  Futures translated: {len(by_type['futures'])}")
    print(f"  Options translated: {len(by_type['options'])}")
    print(f"  Futures failed: {len(by_type['failed_futures'])}")
    print(f"  Options failed: {len(by_type['failed_options'])}")
    
    # Show failed translations
    if not_translated:
        print(f"\nFailed Translations:")
        for symbol in sorted(not_translated)[:20]:  # Show first 20
            print(f"  {symbol}")
        if len(not_translated) > 20:
            print(f"  ... and {len(not_translated)-20} more")
    
    # Analyze patterns in failed translations
    print(f"\nAnalyzing Failed Patterns:")
    patterns = defaultdict(int)
    for symbol in not_translated:
        parts = symbol.split('.')
        if len(parts) >= 2:
            series = parts[1]  # e.g., VY3, WY3, etc.
            patterns[series] += 1
    
    for series, count in sorted(patterns.items(), key=lambda x: -x[1]):
        print(f"  {series}: {count} symbols")
    
    # Show some successful translations for comparison
    print(f"\nSample Successful Translations:")
    for spot, bloom in translated[:10]:
        print(f"  {spot} → {bloom}")


if __name__ == "__main__":
    main() 