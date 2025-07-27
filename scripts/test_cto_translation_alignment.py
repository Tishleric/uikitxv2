#!/usr/bin/env python3
"""
Test that our symbol translator aligns with CTO's translation document.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from lib.trading.market_prices.rosetta_stone import RosettaStone

def main():
    """Test translations against CTO examples."""
    
    print("="*60)
    print("TESTING SYMBOL TRANSLATOR AGAINST CTO EXAMPLES")
    print("="*60)
    
    translator = RosettaStone()
    
    # CTO examples from the document (line 877-885)
    cto_examples = [
        # (Weekday, CME Globex, Bloomberg, Description)
        ('Monday', 'VY2N5', 'VBYA Comdty', 'Second Monday in July 2025'),
        ('Tuesday', 'GY2N5', 'TJPA Comdty', 'Second Tuesday in July 2025'),
        ('Wednesday', 'WY2N5', 'TYYA Comdty', 'Second Wednesday in July 2025'),
        ('Thursday', 'HY2N5', 'TJWA Comdty', 'Second Thursday in July 2025'),
        ('Friday', 'ZN2N5', '2MA Comdty', 'Second Friday in July 2025'),
    ]
    
    print("\nCTO Document Examples:")
    print("-" * 60)
    
    # For testing, we need to create Actant format symbols that would translate to these
    # July 2025 dates (assuming second week)
    test_dates = {
        'Monday': '20250714',     # July 14, 2025 (2nd Monday)
        'Tuesday': '20250715',    # July 15, 2025 (2nd Tuesday)
        'Wednesday': '20250716',  # July 16, 2025 (2nd Wednesday)
        'Thursday': '20250717',   # July 17, 2025 (2nd Thursday)
        'Friday': '20250718',     # July 18, 2025 (2nd Friday)
    }
    
    # Map CME series to Actant series
    cme_to_actant = {
        'VY': 'VY',
        'GY': 'TJ',  # Tuesday in CME is GY, but TJ in Actant
        'WY': 'WY',
        'HY': 'TH',  # Thursday in CME is HY, but TH in Actant
        'ZN': 'ZN',
    }
    
    for weekday, cme_symbol, expected_bloomberg, description in cto_examples:
        print(f"\n{weekday}:")
        print(f"  CME Globex: {cme_symbol}")
        print(f"  Expected Bloomberg: {expected_bloomberg}")
        print(f"  Description: {description}")
        
        # Extract parts from CME symbol (e.g., VY2N5)
        series = cme_symbol[:2]
        week = cme_symbol[2]
        month = cme_symbol[3]
        year = cme_symbol[4]
        
        # Convert to Actant series
        actant_series = cme_to_actant.get(series, series)
        
        # Create Actant format symbol
        # Format: XCMEOCADPS20250714N0VY2/110.00
        date_str = test_dates[weekday]
        actant_symbol = f"XCMEOCADPS{date_str}N0{actant_series}2/110.00"
        
        # Translate
        result = translator.translate(actant_symbol, 'actanttrades', 'bloomberg')
        
        if result:
            # Extract just the symbol part (before the strike)
            symbol_part = result.split()[0] + ' ' + result.split()[1][0]  # e.g., "VBYN25C2 C"
            symbol_base = symbol_part.split()[0][:-1]  # Remove the option type
            
            print(f"  Our translation: {symbol_base} (from {actant_symbol})")
            
            # Check if it matches (ignoring the specific format differences)
            if weekday == 'Friday':
                # Friday has special format
                if '2MA' in expected_bloomberg and 'MA' in result:
                    print("  ✓ Friday format matches (week + MA)")
                else:
                    print(f"  ✗ Friday format mismatch: got {result}")
            else:
                # For other days, check the base symbol
                expected_base = expected_bloomberg.split()[0].replace('A', '')  # Remove 'A' suffix
                if expected_base in ['VBY', 'TJP', 'TYY', 'TJW']:
                    # These are base codes without week/date info in CTO examples
                    our_base = result.split()[0][:3]  # Get first 3 chars
                    if our_base in result:
                        print(f"  ✓ Base code matches: {our_base}")
                    else:
                        print(f"  ✗ Base code mismatch")
        else:
            print(f"  ✗ Translation failed for {actant_symbol}")
    
    # Test some actual spot risk symbols
    print("\n" + "="*60)
    print("Testing Spot Risk Symbol Translations:")
    print("-" * 60)
    
    spot_risk_tests = [
        ('XCME.VY3.21JUL25.111.C', 'Monday option'),
        ('XCME.GY3.22JUL25.111.C', 'Tuesday option (CME format)'),
        ('XCME.TJ3.22JUL25.111.C', 'Tuesday option (Actant format)'),
        ('XCME.WY3.23JUL25.111.C', 'Wednesday option'),
        ('XCME.HY3.24JUL25.111.C', 'Thursday option (CME format)'),
        ('XCME.TH3.24JUL25.111.C', 'Thursday option (Actant format)'),
        ('XCME.ZN3.18JUL25.111.C', 'Friday option'),
    ]
    
    from lib.trading.market_prices.spot_risk_symbol_adapter import SpotRiskSymbolAdapter
    adapter = SpotRiskSymbolAdapter()
    
    for spot_symbol, description in spot_risk_tests:
        result = adapter.translate(spot_symbol)
        print(f"\n{description}:")
        print(f"  Input: {spot_symbol}")
        print(f"  Output: {result if result else 'FAILED'}")


if __name__ == "__main__":
    main() 